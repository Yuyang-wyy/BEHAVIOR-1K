#!/usr/bin/env bash
# Assemble the lb_v1 submission package directory: results JSONs, videos, code snapshot, routing, README, summary.
set -e
P=/home/ywang/Behavior/local_eval/submission_lb_v1; B=/home/ywang/Behavior
rm -rf $P; mkdir -p $P/results $P/videos $P/code $P/checkpoints
cp -r $B/local_eval/eval_out/lb_v1_all/* $P/results/
for root in $B/local_eval/eval_out/lb_v1 $B/local_eval/eval_out/lb_v1_videos/remote $B/local_eval/eval_out/lb_v1_videos/sulab1; do
  for d in $root/*/videos; do t=$(basename $(dirname $d)); mkdir -p $P/videos/$t; cp -n $d/*.mp4 $P/videos/$t/ 2>/dev/null || true; done
done
cp $B/BEHAVIOR-1K/research/lb_v1/openpi-comet_lb_v1.patch $B/BEHAVIOR-1K/research/lb_v1/openpi-comet_websocket_b1k_server.py $B/BEHAVIOR-1K/research/lb_v1/openpi-comet_BASE.txt $P/code/
cp $B/local_eval/serve_comet.sh $B/local_eval/run_eval.sh $P/code/
cd $B/BEHAVIOR-1K && git diff OmniGibson/omnigibson/eval/eval.py OmniGibson/omnigibson/eval/evaluator.py > $P/code/evaluator_goal_history_logging.patch
cp $B/local_eval/lb/zs_tasks.txt $P/routing.txt
cp $B/planner_runs/lb_v1/SUBMISSION_README.md $P/README.md
cp $B/local_eval/exports/step-00040000/EXPORT_RECEIPT.json $P/checkpoints/ft40k_EXPORT_RECEIPT.json
echo "ft40k: local_eval/exports/step-00040000 (upload); zero-shot: openpi_comet/pi05-b1kpt50-cs32 (upload)" > $P/checkpoints/LINKS.txt
mv $P/results/summary.json $P/summary.json
echo "jsons: $(find $P/results -name '*.json' | wc -l)  videos: $(find $P/videos -name '*.mp4' | wc -l)  size: $(du -sh $P | cut -f1)"
