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
# openpi post-install step for the PyTorch model path: patched transformers modules must overwrite the installed ones
RUN cd openpi-comet && uv pip install transformers==4.53.2 && cp -r ./src/openpi/models_pytorch/transformers_replace/* .venv/lib/python3.11/site-packages/transformers/
# checkpoints from HuggingFace (model repos listed in README; HF_TOKEN only needed while they are private)
ARG HF_TOKEN=""
COPY hf_download.py /app/hf_download.py
RUN cd openpi-comet && uv pip install huggingface_hub && HF_TOKEN=$HF_TOKEN .venv/bin/python /app/hf_download.py
# PaliGemma tokenizer expected by openpi at $OPENPI_DATA_HOME/big_vision/
COPY big_vision/paligemma_tokenizer.model /root/.cache/openpi/big_vision/paligemma_tokenizer.model
ENV OPENPI_DATA_HOME=/root/.cache/openpi
COPY routing_zero_shot_tasks.txt entrypoint.sh /app/
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
