"""Render task_docs/tasks/<NN>_<task>.md from facts/*.json plus notes/*.md.

    python3 task_docs/tools/render_task_docs.py

facts/ is generated (build_task_facts.py); notes/ holds the hand-written
planner notes for each task and is never overwritten by this script.
"""
import json
from pathlib import Path

ROOT = Path("/home/ywang/Behavior/task_docs")
OVERRIDES = json.loads((ROOT / "data/q_ceiling_overrides.json").read_text())


def fmt_range(r, unit=""):
    if not r:
        return "?"
    if r["min"] == r["max"]:
        return f"{r['median']}{unit}"
    return f"{r['median']}{unit} (range {r['min']}-{r['max']})"


def results_line(res):
    order = ["zs_pt50@sulab1", "ft24k@sulab1", "ft40k@sulab1", "ft40k@local"]
    parts = []
    for key in order + sorted(k for k in res if k not in order):
        if key in res:
            r = res[key]
            parts.append(f"{key} Q={r['q']:.2f}{' (success)' if r['success'] else ''}")
    return "; ".join(parts) if parts else "not evaluated yet"


def goal_top_level_forms(definition):
    """Count s-expressions directly inside (:goal ...). BDDL parsing keeps only the first."""
    i = definition.find("(:goal")
    if i < 0:
        return 0
    depth, forms, j = 0, 0, i
    while j < len(definition):
        c = definition[j]
        if c == "(":
            depth += 1
            if depth == 2:
                forms += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return forms


def render(f, notes):
    L = []
    title = f.get("title") or f["name"].replace("_", " ")
    L.append(f"# {f['index']:02d} · {title}")
    L.append("")
    L.append(f"Task name `{f['name']}`, task index {f['index']}.")
    L.append("")
    L.append(f"> {f['instruction']}")
    if f.get("comet_pretrain_sentence") and f["comet_pretrain_sentence"] != f["instruction"]:
        L.append("")
        L.append(f"Comet pretraining used this sentence instead: \"{f['comet_pretrain_sentence']}\"")
    L.append("")
    if "error" in f:
        L.append("Fact extraction failed for this task:")
        L.append("```\n" + f["error"][-2000:] + "\n```")
        return "\n".join(L)

    h = f["human"]
    opt = f["ground_option_example"]
    L.append("## At a glance")
    L.append("")
    L.append("| item | value |")
    L.append("| --- | --- |")
    L.append(f"| scene | `{f.get('scene')}` |")
    L.append(f"| rooms in the goal | {', '.join(sorted(set((f.get('room_instances') or {}).keys()))) or '-'} |")
    L.append(f"| rooms loaded | {', '.join(f.get('rooms_loaded') or []) or '-'} |")
    L.append(f"| human demo length | {h['mean_seconds']} s mean ({int(h['mean_steps'])} steps) |")
    L.append(f"| episode time limit | {h['time_limit_seconds']} s ({h['step_limit']} steps at 30 Hz) |")
    L.append(f"| human base travel | {h['base_distance_m']} m |")
    L.append(f"| goal literals (best ground option) | {opt['n_literals']} |")
    L.append(f"| literals already true at start (inferred) | {opt['n_initially_true']} |")
    ov = OVERRIDES.get(f"{f['index']:02d}_{f['name']}")
    if ov:
        L.append(f"| max Q short of full success | **{ov['max_partial_q']}** realistic; {opt['max_partial_q']} from `:init` alone. {ov['reason']} |")
    else:
        L.append(f"| max Q short of full success | {opt['max_partial_q']} |")
    L.append(f"| ground goal options | {f['n_ground_options']} |")
    art = {k: v for k, v in (f.get("articulated_start_state") or {}).items() if v["instances_starting_open"]}
    if art:
        L.append("| starts open (joint_pos > 0.02) | " + "; ".join(
            f"`{k}` in {v['instances_starting_open']}/{v['instances_checked']} instances" for k, v in art.items()) + " |")
    L.append(f"| public test instances | {f['n_public_instances']} (ids 301-320) |")
    L.append(f"| closed-loop results, instance 311, n=1 | {results_line(f.get('results') or {})} |")
    if f.get("video"):
        L.append(f"| demo video | {f['video']} |")
    L.append("")

    if notes:
        L.append(notes.strip())
        L.append("")

    L.append("## Goal and Q scoring")
    L.append("")
    L.append("Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. "
             "A literal that is already true at reset sits in the denominator but can never earn credit. "
             "Full success scores 1.0 regardless.")
    L.append("")
    L.append("Ground literals of the best option (initial truth inferred from `:init`):")
    L.append("")
    L.append("| literal | true at start? | scores? |")
    L.append("| --- | --- | --- |")
    for lit in opt["literals"]:
        it = lit["initially_true_inferred"]
        L.append(f"| `{lit['literal']}` | {'yes' if it else 'no'} | {'never (already true)' if it else 'yes'} |")
    L.append("")
    if f["n_ground_options"] > 1:
        sizes = ", ".join(f"{n} literals x{c}" for n, c in f["ground_option_sizes"])
        L.append(f"The goal has {f['n_ground_options']} ground options ({sizes}); Q takes the best one, "
                 "so any valid choice of container or partner object counts.")
        L.append("")
    if f.get("n_self_paired_options"):
        L.append(f"{f['n_self_paired_options']} ground options pair an object with itself (for example `nextto can_1 can_1`). "
                 "Those can never hold, so the option shown above is the best one without them.")
        L.append("")
    goal = f["bddl_definition"]
    if goal_top_level_forms(goal) > 1:
        L.append("**Warning:** this goal has more than one top-level clause. The BDDL parser keeps only the first "
                 "(`bddl/parsing.py:281`), so the later clauses are ignored by the evaluator and are not in the literal table.")
        L.append("")
    g0 = goal.find("(:goal")
    L.append("BDDL goal:")
    L.append("")
    L.append("```lisp\n" + goal[g0:].rstrip() + "\n```")
    L.append("")

    L.append("## Objects and where they start")
    L.append("")
    L.append("Heights and distances come from the 20 public instances (301-320). "
             "Distance is horizontal, from the robot's start pose.")
    L.append("")
    L.append("| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for e in f["scope"]:
        if e["inst"].startswith("agent"):
            continue
        if e.get("substance"):
            L.append(f"| `{e['inst']}` | particle system | {', '.join(e.get('systems') or [])} | - | - | - | - |")
            continue
        cat = f"{e.get('category') or '/'.join(e.get('category_candidates', [])[:3])}" + (f" / {e['model']}" if e.get("model") else "")
        rooms = ", ".join(e.get("in_rooms") or []) or "-"
        z = e.get("z")
        height = f"{e.get('height_band')}, z {z['median']}" if z else "-"
        dist = fmt_range(e.get("dist_from_robot_start_m"), " m") if e.get("dist_from_robot_start_m") else "-"
        moves = "-" if e.get("xy_spread_m") is None else ("no" if e["xy_spread_m"] < 0.05 else f"yes, spread {e['xy_spread_m']} m")
        if e.get("fixed"):
            moves = "no (fixed)"
        if e["inst"] in (f.get("future_objects") or []):
            L.append(f"| `{e['inst']}` | does not exist at reset; created by a transition (slicing, cooking, etc.) | {'/'.join(e.get('category_candidates', [])[:3])} | - | - | - | - |")
            continue
        L.append(f"| `{e['inst']}` | {e.get('scene_object') or '(runtime)'} | {cat} | {rooms} | {height} | {dist} | {moves} |")
    L.append("")
    if f.get("custom_lists"):
        L.append("Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):")
        L.append("")
        L.append("```json\n" + json.dumps(f["custom_lists"], indent=1)[:3000] + "\n```")
        L.append("")
    L.append("Initial conditions from `:init`:")
    L.append("")
    L.append("```lisp\n" + "\n".join(f["init_literals"]) + "\n```")
    L.append("")

    d = f.get("demos")
    if d:
        L.append("## What the human demos did")
        L.append("")
        L.append(f"{d['n_episodes']} annotated demos. Length {fmt_range(d['demo_seconds'], ' s')}. "
                 f"Skills per demo {fmt_range(d['segments_per_episode'])}. "
                 f"{d['distinct_verb_sequences']} distinct skill orders; the most common one covers "
                 f"{round(100 * d['modal_verb_sequence_share'])}% of demos.")
        L.append("")
        counts = ", ".join(f"{v} x{n}" for v, n in sorted(d["modal_verb_counts"].items(), key=lambda kv: -kv[1]))
        L.append(f"Most common skill counts per demo ({round(100 * d['modal_verb_counts_share'])}% of demos): {counts}.")
        L.append("")
        rep = d["representative_episode"]
        L.append(f"Representative demo `{rep['file']}` ({rep['seconds']} s). The prompts are the exact skill sentences "
                 "Comet was fine-tuned on, so they are in-distribution prompts:")
        L.append("")
        for i, s in enumerate(rep["steps"], 1):
            L.append(f"{i}. `{s['prompt']}` ({s['start_s']}-{s['end_s']} s)")
        L.append("")
        L.append("Mean duration per skill in this task: " +
                 ", ".join(f"{v} {s} s" for v, s in d["verb_mean_seconds"].items()) + ".")
        L.append("")
        L.append("Most frequent skill sentences across all 200 demos:")
        L.append("")
        L.append("| skill sentence | count |")
        L.append("| --- | --- |")
        for p, n in d["top_prompts"][:15]:
            L.append(f"| `{p}` | {n} |")
        L.append("")
    L.append("## Sources")
    L.append("")
    L.append("Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the "
             "evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, "
             "`data/2026-challenge-metadata-git/annotations`, and the eval JSONs. "
             f"Raw facts: `task_docs/facts/{f['index']:02d}_{f['name']}.json`. "
             f"Planner notes: `task_docs/notes/{f['index']:02d}_{f['name']}.md`.")
    L.append("")
    return "\n".join(L)


def main():
    out = ROOT / "tasks"
    out.mkdir(exist_ok=True)
    index = []
    for p in sorted((ROOT / "facts").glob("[0-9][0-9]_*.json")):
        f = json.loads(p.read_text())
        note_path = ROOT / "notes" / (p.stem + ".md")
        notes = note_path.read_text() if note_path.exists() else ""
        (out / (p.stem + ".md")).write_text(render(f, notes))
        index.append(f)
    L = ["# BEHAVIOR-1K 2026: the 100 tasks", "",
         "One page per task for the high-level planner that prompts the Comet checkpoint. "
         "Read `README.md` for how Q is scored and how to prompt Comet.", "",
         "| # | task | scene | literals | max partial Q | limit (s) | demo skills | ft40k Q | zs Q | notes |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for f in index:
        if "error" in f:
            L.append(f"| {f['index']} | {f['name']} | extraction error | | | | | | | |")
            continue
        o = f["ground_option_example"]
        res = f.get("results") or {}
        ft = res.get("ft40k@local") or res.get("ft40k@sulab1")
        zs = res.get("zs_pt50@sulab1")
        segs = (f.get("demos") or {}).get("segments_per_episode") or {}
        has_notes = (ROOT / "notes" / f"{f['index']:02d}_{f['name']}.md").exists()
        ov = OVERRIDES.get(f"{f['index']:02d}_{f['name']}")
        if ov:
            o = dict(o, max_partial_q=f"{ov['max_partial_q']}*")
        L.append(f"| {f['index']} | [{f['name']}](tasks/{f['index']:02d}_{f['name']}.md) | {f.get('scene')} | {o['n_literals']} | "
                 f"{o['max_partial_q']} | {f['human']['time_limit_seconds']} | {segs.get('median', '?')} | "
                 f"{'' if ft is None else round(ft['q'], 2)} | {'' if zs is None else round(zs['q'], 2)} | {'yes' if has_notes else ''} |")
    L += ["", "\\* corrected by the planner notes; the `:init`-based value misses geometry that is already true at reset."]
    (ROOT / "INDEX.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
