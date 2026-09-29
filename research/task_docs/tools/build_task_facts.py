"""Extract per-task facts for the 100 BEHAVIOR-1K 2026 challenge tasks.

Run with the `behavior` conda env (needs bddl, yaml, numpy):

    /home/ywang/miniconda3/envs/behavior/bin/python task_docs/tools/build_task_facts.py

Writes task_docs/facts/<NN>_<task>.json and task_docs/facts/all.json.

Sources (all offline, no simulator):
* goal/init: BEHAVIOR-1K/bddl3 knowledge base, compiled with the same wildcard
  expansion the evaluator uses (room layout counted from the scene template);
* scope, rooms, poses: datasets/2026-challenge-task-instances (template + the 20
  public instance files 301-320);
* step limit: metadata/task.jsonl (human mean length) x EVAL_TIMEOUT_MULTIPLIER 1.5;
* skill plans: data/2026-challenge-metadata-git/annotations (200 demos per task),
  rendered with the same templates Comet was trained on (build_comet_prompts.py);
* results: local_eval/eval_out and task_docs/data/eval_sulab1.json.

Initial truth of goal literals is INFERRED from the BDDL :init block (a literal
is initially true if it appears there; a negated literal is initially true when
its positive form does not). The simulator can differ (e.g. an articulated
object sampled half-open); verify with scripts/aspire_radio/task_feasibility_probe.py.
"""
from __future__ import annotations

import collections
import glob
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path("/home/ywang/Behavior")
B1K = ROOT / "BEHAVIOR-1K"
INST = B1K / "datasets/2026-challenge-task-instances"
ANN = ROOT / "data/2026-challenge-metadata-git/annotations"
OUT = ROOT / "task_docs/facts"
sys.path.insert(0, str(ROOT / "reproductions/winner_2025_task40/scripts"))
import build_comet_prompts as bcp  # noqa: E402

bcp.load_categories(str(ROOT / "reproductions/winner_2025_task40/configs/bddl_category_mapping.csv"))

FPS = 30
TIMEOUT_MULT = 1.5


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def parse_literal_str(terms):
    """terms from HEAD.terms, e.g. ['not', ['open', 'cabinet.n.01_1']] or ['inside', 'a', 'b']."""
    if terms and terms[0] == "not":
        if isinstance(terms[1], (list, tuple)):
            inner = terms[1]
            return True, inner[0], tuple(inner[1:])
        return True, terms[1], tuple(terms[2:])
    return False, terms[0], tuple(terms[1:])


def init_facts(parsed_init):
    facts = set()
    for cond in parsed_init:
        if cond[0] == "not":
            continue
        facts.add((cond[0], tuple(cond[1:])))
    return facts


def height_band(z):
    if z is None:
        return None
    if z < 0.25:
        return "floor"
    if z < 0.6:
        return "low (0.25-0.6 m)"
    if z < 1.1:
        return "table/counter (0.6-1.1 m)"
    if z < 1.6:
        return "high (1.1-1.6 m)"
    return "very high (>1.6 m)"


def summarize(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return {"min": round(min(values), 2), "median": round(statistics.median(values), 2), "max": round(max(values), 2)}


_KB = None


def KB():
    global _KB
    if _KB is None:
        from bddl.knowledge_base import KnowledgeBase
        _KB = KnowledgeBase(verbose=False)
    return _KB


def og_categories(inst, kb_synset_cache={}):
    syn = inst.rsplit("_", 1)[0]
    if syn not in kb_synset_cache:
        s = KB().get_synset(syn)
        if s is None:
            kb_synset_cache[syn] = ([], False)
        else:
            chain = [s] + sorted(s.descendants, key=lambda x: x.name)
            if s.is_substance:
                kb_synset_cache[syn] = ([ps.name for x in chain for ps in x.particle_systems], True)
            else:
                kb_synset_cache[syn] = ([c.name for x in chain if x.is_leaf for c in x.categories], False)
    return kb_synset_cache[syn]


def find_instance_files(task):
    tpl = sorted(glob.glob(str(INST / "scene_test/public/*/json" / f"*_task_{task}_0_0_template.json")))
    if not tpl:
        return None, None, []
    scene = Path(tpl[0]).parts[-3]
    inst_dir = Path(tpl[0]).parent / f"{scene}_task_{task}_instances"
    insts = sorted(inst_dir.glob("*-tro_state.json"))
    return scene, Path(tpl[0]), insts


def room_instance_of(obj_info, room_type):
    rooms = (obj_info or {}).get("args", {}).get("in_rooms") or []
    for r in rooms:
        if r.rsplit("_", 1)[0] == room_type:
            return r
    return rooms[0] if rooms else None


def build_scene_layout(template, base_inroom, inst_to_name):
    init_info = template["objects_info"]["init_info"]
    room_instances = {}
    for inst, room_type in base_inroom.items():
        name = inst_to_name.get(inst)
        info = init_info.get(name) if isinstance(name, str) else None
        ri = room_instance_of(info, room_type)
        if ri:
            room_instances.setdefault(room_type, ri)
    for room_type in set(base_inroom.values()):
        if room_type not in room_instances:
            room_instances[room_type] = f"{room_type}_0"
    layout = {}
    for room_type, ri in room_instances.items():
        counts = collections.Counter()
        for name, info in init_info.items():
            if ri in ((info.get("args") or {}).get("in_rooms") or []):
                counts[info["args"].get("category")] += 1
        layout[room_type] = dict(counts)
    return layout, room_instances


def annotation_summary(task_index):
    files = sorted(glob.glob(str(ANN / f"task-{task_index:04d}" / "episode_*.json")))
    verb_seqs = collections.Counter()
    prompt_counts = collections.Counter()
    verb_durations = collections.defaultdict(list)
    episodes = []
    for f in files:
        a = json.load(open(f))
        segs = sorted(a.get("skill_annotation") or [], key=lambda s: bcp.frame_span(s)[0])
        length = int((a.get("meta_data") or {}).get("task_duration") or 0)
        verbs, prompts = [], []
        seen_spans = set()
        for s in segs:
            key = (bcp.skill_prompt(s), tuple(bcp.frame_span(s)))
            if key in seen_spans:  # same skill annotated once per hand
                continue
            seen_spans.add(key)
            v = " + ".join(s.get("skill_description") or [])
            p = bcp.skill_prompt(s)
            st, en = bcp.frame_span(s)
            verbs.append(v)
            prompts.append((p, st, en))
            prompt_counts[p] += 1
            verb_durations[v].append((en - st) / FPS)
        verb_seqs[tuple(verbs)] += 1
        episodes.append({"file": Path(f).name, "length": length, "verbs": tuple(verbs), "prompts": prompts})
    if not episodes:
        return None
    top_seq, top_n = verb_seqs.most_common(1)[0]
    cands = [e for e in episodes if e["verbs"] == top_seq]
    cands.sort(key=lambda e: e["length"])
    rep = cands[len(cands) // 2]
    nseg = [len(e["verbs"]) for e in episodes]
    lengths = [e["length"] / FPS for e in episodes if e["length"]]
    # verb-level multiset per episode (order-free), to show how many of each skill a demo needs
    verb_count_mode = collections.Counter()
    for e in episodes:
        verb_count_mode[tuple(sorted(collections.Counter(e["verbs"]).items()))] += 1
    vc, vc_n = verb_count_mode.most_common(1)[0]
    return {
        "n_episodes": len(episodes),
        "segments_per_episode": summarize(nseg),
        "demo_seconds": summarize(lengths),
        "distinct_verb_sequences": len(verb_seqs),
        "modal_verb_sequence": list(top_seq),
        "modal_verb_sequence_share": round(top_n / len(episodes), 3),
        "modal_verb_counts": dict(vc),
        "modal_verb_counts_share": round(vc_n / len(episodes), 3),
        "representative_episode": {
            "file": rep["file"],
            "seconds": round(rep["length"] / FPS, 1),
            "steps": [{"prompt": p, "start_s": round(st / FPS, 1), "end_s": round(en / FPS, 1)} for p, st, en in rep["prompts"]],
        },
        "verb_mean_seconds": {v: round(statistics.mean(d), 1) for v, d in sorted(verb_durations.items())},
        "verb_counts_total": {v: len(d) for v, d in sorted(verb_durations.items(), key=lambda kv: -len(kv[1]))},
        "top_prompts": prompt_counts.most_common(25),
    }


def load_results():
    res = collections.defaultdict(dict)
    sul = json.load(open(ROOT / "task_docs/data/eval_sulab1.json"))
    for tag, tasks in sul.items():
        for t, r in tasks.items():
            res[t][f"{tag}@sulab1"] = r
    for j in glob.glob(str(ROOT / "local_eval/eval_out/*/*/json/*.json")):
        r = json.load(open(j))
        tag = Path(j).parts[-4]
        res[r["task"]][f"{tag}@local"] = {"instance": r.get("instance_id"), "q": r["q_score"]["final"],
                                           "success": r["success"], "steps": r.get("steps")}
    return res


def task_facts(row, taskdata, human, misc_rooms, custom, comet_map, results):
    name = row["task_name"]
    idx = row["task_index"]
    facts = {"index": idx, "name": name, "instruction": row["task"]}
    td = taskdata.get(name, {})
    facts.update({"title": td.get("name"), "rooms_listed": td.get("rooms"), "video": td.get("video"),
                  "scene_model": td.get("scene_model")})
    if name in comet_map:
        facts["comet_pretrain_sentence"] = comet_map[name]["task"]
    h = human[name]
    facts["human"] = {"mean_steps": h["length"], "mean_seconds": round(h["length"] / FPS, 1),
                      "step_limit": int(h["length"] * TIMEOUT_MULT),
                      "time_limit_seconds": round(h["length"] * TIMEOUT_MULT / FPS, 1),
                      "base_distance_m": h["distance_traveled"],
                      "eef_displacement_m": {"left": h["left_eef_displacement"], "right": h["right_eef_displacement"]}}
    facts["rooms_loaded"] = misc_rooms.get(name)
    facts["custom_lists"] = custom.get(name)

    # --- BDDL
    kb = KB().get_task(f"{name}-0")
    facts["bddl_definition"] = kb.definition
    base_conds, base_scope, base_inroom = kb.parse_base_scope()

    scene, tpl_path, inst_files = find_instance_files(name)
    facts["scene"] = scene
    facts["n_public_instances"] = len(inst_files)
    template = json.load(open(tpl_path)) if tpl_path else None
    inst_to_name = (template or {}).get("metadata", {}).get("task", {}).get("inst_to_name", {}) if template else {}
    layout, room_instances = build_scene_layout(template, base_inroom, inst_to_name) if template else ({}, {})
    facts["room_instances"] = room_instances
    compiled = kb.compile(scene_layout=layout)
    facts["has_wildcards"] = bool(kb.has_wildcards)
    parsed_objects = compiled.parsed_objects
    facts["objects"] = {syn: insts for syn, insts in parsed_objects.items()}

    init = init_facts(compiled.conditions.parsed_initial_conditions)
    future = {a[0] for p_, a in init if p_ == "future"}
    # `real` is implicit: every object that is not declared (future ...) exists at reset.
    for insts in compiled.parsed_objects.values():
        for inst in insts:
            if inst not in future and "agent" not in inst:
                init.add(("real", (inst,)))
    facts["future_objects"] = sorted(future)
    # ontop requires contact, so it implies touching in both directions.
    for p_, a in list(init):
        if p_ == "ontop" and len(a) == 2:
            init.add(("touching", (a[0], a[1])))
            init.add(("touching", (a[1], a[0])))
    # Articulated objects: read recorded joint positions (template + 20 instances).
    tpl_reg = (template or {}).get("state", {}).get("registry", {}).get("object_registry", {})
    open_counts = {}
    inst_states = [json.load(open(p__)) for p__ in inst_files]
    for insts_ in compiled.parsed_objects.values():
        for inst in insts_:
            if "agent" in inst:
                continue
            so = inst_to_name.get(inst)
            samples = []
            for d_ in inst_states:
                st = d_.get(inst)
                if isinstance(st, dict) and "joint_pos" in st:
                    samples.append(st["joint_pos"])
            if not samples and isinstance(so, str) and "joint_pos" in (tpl_reg.get(so) or {}):
                samples = [tpl_reg[so]["joint_pos"]]
            if samples:
                n_open = sum(1 for jp in samples if jp and max(abs(x) for x in jp) > 0.02)
                open_counts[inst] = {"instances_checked": len(samples), "instances_starting_open": n_open,
                                     "max_abs_joint_pos": round(max(max((abs(x) for x in jp), default=0) for jp in samples), 3)}
                if n_open * 2 > len(samples):
                    init.add(("open", (inst,)))
    facts["articulated_start_state"] = {k: v for k, v in open_counts.items()}
    facts["init_literals"] = sorted("(" + " ".join([p, *a]) + ")" for p, a in init if p != "real")

    options = compiled.ground_goal_state_options
    opt_summ = []
    for opt in options:
        lits = []
        for head in opt:
            neg, pred, args = parse_literal_str(head.terms)
            init_true = ((pred, args) in init) != neg
            lits.append({"literal": ("(not " if neg else "(") + " ".join([pred, *args]) + (")" if not neg else "))"),
                         "negated": neg, "predicate": pred, "args": list(args), "initially_true_inferred": init_true})
        n = len(lits)
        k = sum(l["initially_true_inferred"] for l in lits)
        opt_summ.append({"n_literals": n, "n_initially_true": k, "max_partial_q": round((n - k) / n, 3) if n else None,
                         "literals": lits})
    facts["n_ground_options"] = len(options)
    def self_paired(o):
        return any(len(l["args"]) == 2 and l["args"][0] == l["args"][1] and not l["negated"] for l in o["literals"])
    pool = [o for o in opt_summ if not self_paired(o)] or opt_summ
    facts["n_self_paired_options"] = len(opt_summ) - len([o for o in opt_summ if not self_paired(o)])
    best = max(pool, key=lambda o: (o["max_partial_q"] or 0, -o["n_literals"]))
    facts["ground_option_example"] = best
    facts["ground_option_sizes"] = collections.Counter(o["n_literals"] for o in opt_summ).most_common()
    facts["goal_predicates"] = collections.Counter(
        ("not " if l["negated"] else "") + l["predicate"] for l in best["literals"]).most_common()

    # --- scope objects and geometry
    init_info = (template or {}).get("objects_info", {}).get("init_info", {})
    registry = (template or {}).get("state", {}).get("registry", {}).get("object_registry", {})
    scope = []
    for syn, insts in parsed_objects.items():
        for inst in insts:
            name_ = inst_to_name.get(inst)
            cats, substance = og_categories(inst)
            entry = {"inst": inst, "scene_object": name_, "substance": substance}
            info = init_info.get(name_) if isinstance(name_, str) else None
            if info:
                args = info.get("args", {})
                entry.update({"category": args.get("category"), "model": args.get("model"),
                              "in_rooms": args.get("in_rooms"), "fixed": bool(args.get("fixed_base")),
                              "scale": args.get("scale")})
            elif not substance and "agent" not in inst:
                entry["category_candidates"] = cats[:8]
                entry["note"] = "wildcard/unassigned in template: resolved at runtime to a scene object of these categories"
            if substance:
                entry["systems"] = cats
            scope.append(entry)
    # per-instance poses
    robots, poses = [], collections.defaultdict(list)
    for f in inst_files:
        d = json.load(open(f))
        rp = (d.get("robot_poses") or {}).get("robot") or []
        rpos = rp[0]["position"] if rp else None
        robots.append(rpos)
        for inst, st in d.items():
            if inst == "robot_poses" or not isinstance(st, dict) or "root_link" not in st:
                continue
            pos = st["root_link"]["pos"]
            dist = math.hypot(pos[0] - rpos[0], pos[1] - rpos[1]) if rpos else None
            poses[inst].append((pos, dist))
    for e in scope:
        inst = e["inst"]
        pl = poses.get(inst)
        if not pl and isinstance(e.get("scene_object"), str) and e["scene_object"] in registry:
            rl = (registry[e["scene_object"]] or {}).get("root_link") or {}
            if "pos" in rl:
                pl = [(rl["pos"], None)]
        if pl:
            zs = [p[0][2] for p in pl]
            xs = [p[0][0] for p in pl]
            ys = [p[0][1] for p in pl]
            e["z"] = summarize(zs)
            e["height_band"] = height_band(statistics.median(zs))
            e["dist_from_robot_start_m"] = summarize([p[1] for p in pl])
            e["xy_spread_m"] = round(math.hypot(max(xs) - min(xs), max(ys) - min(ys)), 2)
            e["n_poses"] = len(pl)
    facts["scope"] = scope
    facts["robot_start_xy"] = [[round(r[0], 2), round(r[1], 2)] for r in robots if r]

    # --- demos, results
    facts["demos"] = annotation_summary(idx)
    if name in comet_map:
        facts["comet_skill_vocab"] = comet_map[name].get("skill")
    facts["results"] = results.get(name, {})
    return facts


def run():
    rows = load_jsonl(ROOT / "data/2026-challenge-demos/meta/tasks.jsonl")
    taskdata = {t["id"]: t for t in json.load(open(B1K / "docs/challenge/task_data.json"))["tasks"]}
    human = {r["task_name"]: r for r in load_jsonl(INST / "metadata/task.jsonl")}
    misc_rooms = {}
    import csv
    with open(INST / "metadata/B100_task_misc.csv") as f:
        for r in csv.DictReader(f):
            misc_rooms[r["Task"]] = [x.strip() for x in r["Rooms to inlcude"].split("\n") if x.strip()]
    custom = json.load(open(INST / "metadata/task_custom_lists.json"))
    comet_map = json.load(open(ROOT / "local_eval/openpi-comet/scripts/task_mapping.json"))
    comet_pre = json.load(open(ROOT / "reproductions/winner_2025_task40/configs/comet_task_mapping.json"))
    for k, v in comet_pre.items():
        comet_map.setdefault(k, {}).update({"task": v["task"], "skill": v.get("skill", comet_map.get(k, {}).get("skill"))})
    results = load_results()
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    everything = []
    for row in rows:
        if only and row["task_name"] not in only:
            continue
        try:
            f = task_facts(row, taskdata, human, misc_rooms, custom, comet_map, results)
        except Exception as exc:  # keep going; record the failure
            import traceback
            f = {"index": row["task_index"], "name": row["task_name"], "error": traceback.format_exc()}
            print("ERROR", row["task_name"], exc, file=sys.stderr)
        (OUT / f"{row['task_index']:02d}_{row['task_name']}.json").write_text(json.dumps(f, indent=1, default=str))
        everything.append(f)
        print(row["task_index"], row["task_name"], "ok" if "error" not in f else "ERROR", flush=True)
    if not only:
        (OUT / "all.json").write_text(json.dumps(everything, default=str))


if __name__ == "__main__":
    run()
