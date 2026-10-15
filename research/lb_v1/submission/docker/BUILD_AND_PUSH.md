# Build and push the policy image (needs a machine with Docker + NVIDIA runtime and ~60 GB free)

```bash
cd submission_lb_v1/docker
# 1. build (HF_TOKEN only needed while the two checkpoint repos are private)
docker build --build-arg HF_TOKEN=$HF_TOKEN -t ghcr.io/yuyang-wyy/b1k-2026-comet:lb_v1 .
# 2. smoke test: serve picking_up_trash and hit the health endpoint
docker run --rm --gpus all -e TASK_NAME=picking_up_trash -p 8000:8000 ghcr.io/yuyang-wyy/b1k-2026-comet:lb_v1 &
sleep 90; curl -fsS http://127.0.0.1:8000/healthz && echo HEALTHY
# 3. full check against the real evaluator (one instance, ~10 min) from the BEHAVIOR-1K checkout:
python -m omnigibson.eval.eval --task-name picking_up_trash --robot-config omnigibson/eval/r1pro.yaml --mode public_test \
  --host 127.0.0.1 --port 8000 --instance-indices 0 --env-wrapper omnigibson.eval.wrappers.RGBDFullResWrapper --output-dir /tmp/smoke --write-video
# 4. push to GitHub Container Registry (token needs write:packages; then make the package public in GitHub -> Packages)
echo $GITHUB_TOKEN | docker login ghcr.io -u Yuyang-wyy --password-stdin
docker push ghcr.io/yuyang-wyy/b1k-2026-comet:lb_v1
docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/yuyang-wyy/b1k-2026-comet:lb_v1   # digest for the form
```
Machines: the remote 4090 has Docker 27.5 + nvidia runtime but the user is not in the `docker` group (ask the admin:
`sudo usermod -aG docker ywang`); sulab1 has Docker 28.5, same problem; the local box has no Docker.
