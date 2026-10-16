"""Download the two checkpoints at image build time. The zero-shot checkpoint is one tar (the JAX export has ~6000
small files, which trips HuggingFace's anonymous rate limit); ft40k is 6 files. Retries with backoff on 429/network."""
import os, sys, time, tarfile
import huggingface_hub as h
tok = os.environ.get("HF_TOKEN") or None

def retry(fn, what):
    for attempt in range(12):
        try:
            return fn()
        except Exception as e:
            wait = min(300, 30 * (attempt + 1)); print(f"retry {attempt+1} for {what} after {type(e).__name__}: {str(e)[:120]} - sleeping {wait}s", flush=True); time.sleep(wait)
    sys.exit(f"could not download {what}")

retry(lambda: h.snapshot_download("YuyoungWang/b1k-2026-comet-ft40k", local_dir="/ckpt/ft40k", token=tok, max_workers=2), "ft40k")
tar = retry(lambda: h.hf_hub_download("YuyoungWang/b1k-2026-comet-zs-pt50", "zs-pt50.tar", token=tok, local_dir="/ckpt/_dl"), "zs-pt50.tar")
os.makedirs("/ckpt", exist_ok=True)
with tarfile.open(tar) as t:
    t.extractall("/ckpt")                                  # creates /ckpt/zs-pt50/
os.remove(tar)
print("checkpoints ready:", sorted(os.listdir("/ckpt")), flush=True)
