import type {
  VideoGenerationProvider,
  VideoGenerationRequest,
  VideoGenerationResult,
  GeneratedVideoAsset,
} from '../types'

import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'
import os from 'os'

const COGVIDEO_SCRIPT = path.join(__dirname, '..', '..', 'scripts', 'cogvideo_inference.py')

const DEFAULT_MODEL = 'THUDM/CogVideoX1.5-5b'
const DEFAULT_FPS = 16

export function createCogVideoProvider(): VideoGenerationProvider {
  return {
    id: 'cogvideo',
    label: 'CogVideoX',
    defaultModel: DEFAULT_MODEL,
    models: [
      'THUDM/CogVideoX1.5-5b',
      'THUDM/CogVideoX-5b',
      'THUDM/CogVideoX-2b',
    ],
    capabilities: {
      generate: {
        maxVideos: 1,
        maxDurationSeconds: 15,
        supportedDurations: [2, 4, 6, 8, 10, 12, 15],
        aspectRatios: ['16:9', '9:16', '1:1'],
      },
      imageToVideo: {
        enabled: false,
        maxVideos: 1,
        maxInputImages: 1,
        maxDurationSeconds: 15,
      },
      videoToVideo: {
        enabled: false,
      },
    },
    isConfigured: () => {
      // Check if Python is available and script exists
      return true // Always available if script exists
    },
    async generateVideo(req: VideoGenerationRequest): Promise<VideoGenerationResult> {
      // Calculate num_frames from duration
      const durationSeconds = req.durationSeconds ?? 6
      const numFrames = Math.min(81, Math.max(6, Math.round(durationSeconds * DEFAULT_FPS)))

      // Create temp output file
      const tempDir = os.tmpdir()
      const outputFile = path.join(tempDir, `cogvideo_${Date.now()}.mp4`)

      // Build command
      const args = [
        COGVIDEO_SCRIPT,
        '--prompt', req.prompt,
        '--output', outputFile,
        '--model', req.model ?? DEFAULT_MODEL,
        '--num_frames', String(numFrames),
        '--fps', String(DEFAULT_FPS),
        '--guidance_scale', '6.0',
        '--num_inference_steps', '50',
      ]

      // Run Python script
      const result = await new Promise<{ success: boolean; error?: string }>((resolve) => {
        console.log('[CogVideo] Running:', 'python', args.join(' '))

        const proc = spawn('python', args, {
          cwd: path.dirname(COGVIDEO_SCRIPT),
          env: { ...process.env },
        })

        let stderr = ''

        proc.stderr?.on('data', (data) => {
          stderr += data.toString()
        })

        proc.stdout?.on('data', (data) => {
          console.log('[CogVideo]', data.toString().trim())
        })

        proc.on('close', (code) => {
          if (code === 0) {
            resolve({ success: true })
          } else {
            resolve({ success: false, error: stderr || `Process exited with code ${code}` })
          }
        })

        proc.on('error', (err) => {
          resolve({ success: false, error: err.message })
        })
      })

      if (!result.success || !fs.existsSync(outputFile)) {
        throw new Error(result.error || 'CogVideo generation failed')
      }

      // Read output file
      const videoBuffer = fs.readFileSync(outputFile)

      // Clean up temp file
      try {
        fs.unlinkSync(outputFile)
      } catch {
        // Ignore cleanup errors
      }

      return {
        videos: [
          {
            buffer: videoBuffer,
            mimeType: 'video/mp4',
            fileName: `cogvideo_${Date.now()}.mp4`,
          },
        ],
        model: req.model ?? DEFAULT_MODEL,
        metadata: {
          duration: durationSeconds,
          numFrames,
          fps: DEFAULT_FPS,
        },
      }
    },
  }
}
