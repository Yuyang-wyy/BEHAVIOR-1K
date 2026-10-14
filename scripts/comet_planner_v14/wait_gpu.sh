#!/usr/bin/env bash
# Block until no other job holds the GPU (ignores this harness's own policy servers on ports 81xx),
# for 3 consecutive checks 30 s apart. Other sessions share these GPUs; running alongside them crashes both.
ok=0
while [ $ok -lt 3 ]; do
  foreign=0
  for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do
    args=$(ps -o args= -p "$p" 2>/dev/null)
    [[ "$args" == *"--port=81"* ]] && continue
    foreign=1
  done
  if [ $foreign -eq 0 ]; then ok=$((ok+1)); else ok=0; fi
  [ $ok -lt 3 ] && sleep 30
done
