"""Reuse the local ASPIRE SAM3 server with an explicit existing weight file."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--aspire-root", type=Path, default=Path(__file__).resolve().parents[3] / "references/ASPIRE")
    parser.add_argument("--port", type=int, default=8114)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if not args.checkpoint.is_file():
        parser.error("An existing, authorized SAM3 checkpoint is required; no automatic weight download")
    sys.path.insert(0, str(args.aspire_root.resolve()))
    import torch
    import uvicorn
    from aspire.sim.cap.serving import launch_sam3_server as server

    if args.device.startswith("cuda"):
        torch.cuda.set_device(torch.device(args.device))
    server._DEVICE = args.device
    server._MODEL = server.build_sam3_image_model(
        checkpoint_path=str(args.checkpoint.resolve()), load_from_HF=False,
        device=args.device, enable_inst_interactivity=True,
    )
    server._PROCESSOR = server.Sam3Processor(server._MODEL, device=args.device, confidence_threshold=0.0)
    uvicorn.run(server.app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
