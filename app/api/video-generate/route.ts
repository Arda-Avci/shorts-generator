import { NextRequest, NextResponse } from 'next/server'
import { generateVideo } from '../../../lib/video-generation'
import type { VideoGenerateParams } from '../../../lib/video-generation/types'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: unknown) => {
        try {
          const json = JSON.stringify(data)
          controller.enqueue(encoder.encode(`data: ${json}\n\n`))
        } catch (e) {
          console.error('Send error:', e)
        }
      }

      const log = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
        send({ type: 'log', message, logType: type })
      }

      try {
        const body = await request.json()
        const { prompt, model, aspectRatio, resolution, durationSeconds } = body as VideoGenerateParams

        if (!prompt) {
          send({ type: 'error', message: 'Prompt is required' })
          controller.close()
          return
        }

        log('========== AI VIDEO GENERATION ==========', 'info')
        log(`Provider: CogVideoX (yerel GPU)`, 'info')
        log(`Model: ${model ?? 'THUDM/CogVideoX1.5-5b'}`, 'info')
        log(`Aspect Ratio: ${aspectRatio ?? '9:16'}`, 'info')
        log(`Duration: ${durationSeconds ?? 6}s`, 'info')
        log('', 'info')
        log('🎬 Generating video (GPU kullanılıyor)...', 'info')

        send({ type: 'progress', progress: 10, stage: 'Initializing generation...' })

        const result = await generateVideo(
          {
            prompt,
            model,
            aspectRatio: aspectRatio ?? '9:16',
            resolution,
            durationSeconds: durationSeconds ?? 6,
          },
          'cogvideo', // CogVideoX - yerel GPU, ücretsiz
        )

        send({ type: 'progress', progress: 80, stage: 'Downloading video...' })
        log('✅ Video generated successfully!', 'success')

        const videoBuffer = result.videos[0]?.buffer
        if (!videoBuffer) {
          throw new Error('No video buffer returned')
        }

        send({ type: 'progress', progress: 95, stage: 'Preparing response...' })

        send({
          type: 'complete',
          status: 'success',
          video: {
            buffer: videoBuffer.toString('base64'),
            mimeType: result.videos[0].mimeType,
            fileName: result.videos[0].fileName ?? 'generated-video.mp4',
          },
          metadata: result.metadata,
        })

        log('✅ Complete!', 'success')
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : String(error)
        log(`❌ Error: ${message}`, 'error')
        send({ type: 'error', status: 'error', message })
      }

      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
