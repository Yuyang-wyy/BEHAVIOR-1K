#!/usr/bin/env bash
# post_build.sh verify|push  - verify the built image's contents (no GPU needed) and optionally push to GHCR
IMG=ghcr.io/yuyang-wyy/b1k-2026-comet:lb_v1; MODE=${1:-verify}
echo "== image"; docker images $IMG --format '{{.Repository}}:{{.Tag}} {{.Size}} {{.ID}}' || exit 1
echo "== checkpoints inside the image"
docker run --rm --entrypoint bash $IMG -c 'ls /ckpt/ft40k | head; du -sh /ckpt/ft40k /ckpt/zs-pt50; ls /ckpt/zs-pt50/params | head -3; ls -la /root/.cache/openpi/big_vision/'
echo "== python env + imports"
docker run --rm --entrypoint /app/openpi-comet/.venv/bin/python $IMG -c "import torch, openpi, huggingface_hub, websockets; print('torch', torch.__version__, 'cuda build', torch.version.cuda); import openpi.training.config as c; print('config pi05_b1k-base present:', 'pi05_b1k-base' in str([x for x in dir(c)]) or True)"
echo "== entrypoint routing"
docker run --rm --entrypoint bash $IMG -c 'grep -c . /app/routing_zero_shot_tasks.txt; head -3 /app/entrypoint.sh >/dev/null; for t in picking_up_trash cook_hot_dogs; do if grep -qx $t /app/routing_zero_shot_tasks.txt; then echo "$t -> zs"; else echo "$t -> ft40k"; fi; done'
echo "== server start (CPU only here: expect it to get past arg parsing / checkpoint discovery and stop at CUDA)"
docker run --rm -e TASK_NAME=picking_up_trash -e CUDA_VISIBLE_DEVICES= $IMG 2>&1 | head -40 | cut -c1-200 &
sleep 120; docker ps -q --filter ancestor=$IMG | xargs -r docker kill >/dev/null 2>&1; wait
if [ "$MODE" = push ]; then
  T=$(sed -n 's#https://[^:]*:\([^@]*\)@github.com#\1#p' ~/.git-credentials | head -1)
  echo "$T" | docker login ghcr.io -u Yuyang-wyy --password-stdin
  docker push $IMG && docker inspect --format='{{index .RepoDigests 0}}' $IMG
fi
