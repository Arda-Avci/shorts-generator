#!/usr/bin/env python3
"""
CogVideoX Text-to-Video Inference Script
Usage: python cogvideo_inference.py --prompt "your prompt" --output output.mp4 [--num_frames 81] [--fps 16]
"""

import argparse
import os
import sys
import torch
from diffusers import CogVideoXPipeline, CogVideoXDPMScheduler
from diffusers.utils import export_to_video

def parse_args():
    parser = argparse.ArgumentParser(description='CogVideoX Text-to-Video Inference')
    parser.add_argument('--prompt', type=str, required=True, help='Text prompt for video generation')
    parser.add_argument('--output', type=str, required=True, help='Output video path')
    parser.add_argument('--model', type=str, default='THUDM/CogVideoX1.5-5b', help='Model name or path')
    parser.add_argument('--num_frames', type=int, default=81, help='Number of frames')
    parser.add_argument('--fps', type=int, default=16, help='Frames per second')
    parser.add_argument('--guidance_scale', type=float, default=6.0, help='Guidance scale')
    parser.add_argument('--num_inference_steps', type=int, default=50, help='Number of inference steps')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('--quantize', action='store_true', help='Use INT8 quantization for lower VRAM')
    return parser.parse_args()

def main():
    args = parse_args()

    print(f"[CogVideo] Loading model: {args.model}", file=sys.stderr)
    print(f"[CogVideo] Prompt: {args.prompt}", file=sys.stderr)
    print(f"[CogVideo] Output: {args.output}", file=sys.stderr)

    # Create output directory
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)

    # Load pipeline
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

    pipe = CogVideoXPipeline.from_pretrained(
        args.model,
        torch_dtype=dtype,
    )

    # Use DPM scheduler for 5B models
    if '5b' in args.model.lower():
        pipe.scheduler = CogVideoXDPMScheduler.from_config(
            pipe.scheduler.config,
            timestep_spacing="trailing"
        )

    # Memory optimization
    if torch.cuda.is_available():
        if args.quantize:
            print("[CogVideo] Using INT8 quantization", file=sys.stderr)
            pipe.enable_sequential_cpu_offload()
        else:
            # Try to use GPU, fall back to CPU if OOM
            try:
                pipe.enable_model_cpu_offload()
            except Exception as e:
                print(f"[CogVideo] GPU offload failed ({e}), using CPU", file=sys.stderr)
                pipe.enable_sequential_cpu_offload()
    else:
        print("[CogVideo] No GPU detected, using CPU (slow)", file=sys.stderr)
        pipe.enable_sequential_cpu_offload()

    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()

    # Generate
    print(f"[CogVideo] Generating {args.num_frames} frames...", file=sys.stderr)

    generator = None
    if args.seed is not None:
        generator = torch.Generator().manual_seed(args.seed)

    with torch.no_grad():
        video = pipe(
            prompt=args.prompt,
            num_frames=args.num_frames,
            num_inference_steps=args.num_inference_steps,
            guidance_scale=args.guidance_scale,
            generator=generator,
        ).frames[0]

    # Save
    print(f"[CogVideo] Saving to {args.output}...", file=sys.stderr)
    export_to_video(video, args.output, fps=args.fps)

    print(f"[CogVideo] Done! Video saved to {args.output}", file=sys.stderr)

    # Print file size
    size = os.path.getsize(args.output)
    print(f"[CogVideo] File size: {size / 1024 / 1024:.2f} MB", file=sys.stderr)

if __name__ == '__main__':
    main()
