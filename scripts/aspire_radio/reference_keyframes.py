"""Read-only RGB reference extraction from training demos; never reads action columns."""

import argparse
import json
from pathlib import Path

import av
import pyarrow.parquet as pq


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-root", type=Path, default=Path(__file__).resolve().parents[3] / "data/2026-challenge-demos")
    parser.add_argument("--episode", type=int, default=31, help="Training episode index, NOT evaluation instance lookup")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    columns = ["episode_index", "tasks", "length", "raw_episode_id", "annotation_path"]
    for camera in ("zed_link_camera_0", "right_realsense_link_camera_0"):
        columns += [f"videos/observation.rgb.{camera}/{key}" for key in ("chunk_index", "file_index", "from_timestamp")]
    row = None
    for path in sorted((args.demo_root / "meta/episodes").glob("chunk-*/*.parquet")):
        for candidate in pq.read_table(path, columns=columns).to_pylist():
            if candidate["episode_index"] == args.episode:
                row = candidate
                break
        if row is not None:
            break
    if row is None or row["tasks"] != ["turning_on_radio"]:
        parser.error("Choose an existing radio training demonstration")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    annotation = json.loads((args.demo_root / row["annotation_path"]).read_text())
    skills = [{"description": item["skill_description"], "frames": item["frame_duration"]}
              for item in annotation["skill_annotation"]]
    frames = sorted({int(row["length"] * fraction) for fraction in (.25, .5, .7, .8, .9, .97)}
                    | {int(item["frames"][1]) - 1 for item in skills})
    for camera in ("zed_link_camera_0", "right_realsense_link_camera_0"):
        key = f"observation.rgb.{camera}"
        prefix = f"videos/{key}"
        path = args.demo_root / "videos" / key / f"chunk-{row[prefix + '/chunk_index']:03d}" / f"file-{row[prefix + '/file_index']:03d}.mp4"
        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            for index in frames:
                seconds = row[prefix + "/from_timestamp"] + index / 30
                container.seek(int(seconds / stream.time_base), stream=stream)
                for frame in container.decode(video=0):
                    if float(frame.pts * stream.time_base) >= seconds - 1 / 60:
                        frame.to_image().save(args.output_dir / f"{camera}_frame_{index:05d}.png")
                        break
    (args.output_dir / "provenance.json").write_text(json.dumps({"episode_index": args.episode,
        "raw_episode_id": row["raw_episode_id"], "training_reference_only": True,
        "action_columns_read": False, "skills": skills}, indent=2) + "\n")


if __name__ == "__main__":
    main()
