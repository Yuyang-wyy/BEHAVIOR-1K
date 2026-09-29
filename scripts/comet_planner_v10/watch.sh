#!/usr/bin/env bash
# watch.sh SESSION [N] : 'continue' up to N checkpoints; stop early on a jaw event, hover > 6 s, base idle > 8 s, or episode end
S=$1; N=${2:-8}; X=$(dirname "$0")/sup.sh
for i in $(seq 1 $N); do
  out=$($X $S continue); echo "$out" | head -1
  line=$(echo "$out" | head -1)
  if echo "$line" | grep -q "OVER\|ev \['\|None"; then echo "$out" | sed -n 2p; exit; fi
  h=$(echo "$line" | sed -E 's/.*hoverL ([0-9.]+) R ([0-9.]+) idle ([0-9.]+).*/\1 \2 \3/')
  if python3 -c "import sys; l,r,i=map(float,'$h'.split()); sys.exit(0 if (((l>4 or r>4) and i>2) or i>6) else 1)"; then echo "$out" | sed -n 2p; exit; fi
done
echo "$out" | sed -n 2p
