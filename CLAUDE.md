# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Next.js 14 (TypeScript) + Python** application for generating short videos (YouTube Shorts, TikTok, Instagram Reels). Two video generation modes exist:

- **Clip Mode**: FFmpeg composites video clips + images + intro/outro + background music + watermark into a 60s short
- **AI Mode**: CogVideoX (local GPU) or MiniMax API (cloud) generates videos from text prompts

## Common Commands

```bash
npm run dev      # Start Next.js dev server (http://localhost:3000)
npm run build    # Production build
npm run start    # Start production server
```

**Requirements:**
- Node.js 18+
- FFmpeg (required for clip mode video processing)

**Python dependencies** (for AI video and music generation): `diffusers`, `transformers`, `torch`, `numpy`, `scipy`

## Architecture

```
app/
├── page.tsx                    # Main UI - 4-step wizard (Project > Materials > Preview > Generate)
└── api/                        # API Routes
    ├── generate/              # Clip-based video generation (core logic)
    ├── video-generate/        # AI video generation (CogVideoX/MiniMax)
    └── scan/                  # Project/material scanning

components/
├── GenerationPanel.tsx        # Generation UI with streaming progress/logs
├── PreviewPanel.tsx           # Format/style/music config panel
├── MaterialSelector.tsx       # Material selection
└── ProjectSelector.tsx        # Project selection

lib/video-generation/         # AI provider abstraction
├── types.ts                   # Interfaces
├── provider-registry.ts       # Factory pattern
├── runtime.ts                 # Fallback logic
└── providers/
    ├── minimax.ts             # MiniMax Hailuo 2.3/02 API (paid cloud)
    └── cogvideo.ts            # CogVideoX local inference

scripts/
├── cogvideo_inference.py      # CogVideoX text-to-video Python script
└── generate_shorts.py         # CLI shorts generator template

bg-music/
└── generate_*.py             # Procedural background music generators
```

## Video Generation Flow

**Clip Mode** creates a structured 60s video:
- 2s Intro (image) + 18s Clip 1 + transition + 18s Clip 2 + transition + 18s Clip 3 + 2s Outro (image)
- Watermark embedded in final 10 seconds

**AI Mode** routes to either:
- `minimax.ts` → MiniMax cloud API (requires `MINIMAX_API_KEY` and credits)
- `cogvideo.ts` → Local CogVideoX-5B inference via Python subprocess

## Key Data Flow

1. User selects project from `C:/Users/Damla/Proje/Muhabbet`
2. Materials (video, images, scripts, subtitles) scanned via `/api/scan`
3. User configures: format (9:16/16:9/1:1), style (mysterious/energetic/calm/dark), watermark
4. Generation via FFmpeg (clip) or AI providers (AI mode)

## Environment Variables

```
MINIMAX_API_KEY=<optional>  # Cloud AI video - paid, skip if using local CogVideoX
```

## Key Dependencies

- **@ffmpeg-installer/ffmpeg** + **fluent-ffmpeg**: Video processing
- **next**: 14 with App Router
- **react**: 18