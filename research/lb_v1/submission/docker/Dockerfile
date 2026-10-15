# Policy server for the BEHAVIOR-1K 2026 challenge submission (Comet pi0.5 fine-tune, per-task checkpoint routing).
# Build:  docker build --build-arg HF_TOKEN=<read token if the HF repos are private> -t <registry>/b1k-2026-comet:lb_v1 .
# Run:    docker run --gpus all -e TASK_NAME=<task> -p 8000:8000 <registry>/b1k-2026-comet:lb_v1
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates build-essential libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH=/root/.local/bin:$PATH
WORKDIR /app
# policy code: upstream openpi-comet at the pinned commit + the submission patch + the server module
RUN git clone https://github.com/mli0603/openpi-comet.git openpi-comet && cd openpi-comet && git checkout 4bb2aa7 && git submodule update --init --recursive
COPY openpi-comet.patch /app/openpi-comet.patch
COPY websocket_b1k_server.py /app/openpi-comet/src/openpi/serving/websocket_b1k_server.py
RUN cd openpi-comet && git apply /app/openpi-comet.patch && GIT_LFS_SKIP_SMUDGE=1 uv sync
# checkpoints from HuggingFace (model repos listed in README; HF_TOKEN only needed while they are private)
ARG HF_TOKEN=""
RUN uv pip install --system huggingface_hub || pip3 install huggingface_hub
RUN HF_TOKEN=$HF_TOKEN python3 -c "import huggingface_hub as h, os; t=os.environ.get('HF_TOKEN') or None; \
    h.snapshot_download('YuyoungWang/b1k-2026-comet-ft40k', local_dir='/ckpt/ft40k', token=t); \
    h.snapshot_download('YuyoungWang/b1k-2026-comet-zs-pt50', local_dir='/ckpt/zs-pt50', token=t)"
# PaliGemma tokenizer expected by openpi at $OPENPI_DATA_HOME/big_vision/
COPY big_vision/paligemma_tokenizer.model /root/.cache/openpi/big_vision/paligemma_tokenizer.model
ENV OPENPI_DATA_HOME=/root/.cache/openpi
COPY routing_zero_shot_tasks.txt entrypoint.sh /app/
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
