import type {
  VideoGenerationProvider,
  VideoGenerationRequest,
  VideoGenerationResult,
  GeneratedVideoAsset,
} from '../types'

const DEFAULT_MINIMAX_VIDEO_BASE_URL = 'https://api.minimax.io'
const DEFAULT_MINIMAX_VIDEO_MODEL = 'MiniMax-Hailuo-2.3'
const DEFAULT_TIMEOUT_MS = 120_000
const POLL_INTERVAL_MS = 10_000
const MAX_POLL_ATTEMPTS = 90

const MINIMAX_MODEL_ALLOWED_DURATIONS: Record<string, readonly number[]> = {
  'MiniMax-Hailuo-2.3': [6, 10],
  'MiniMax-Hailuo-02': [6, 10],
}

type MinimaxBaseResp = {
  status_code?: number
  status_msg?: string
}

type MinimaxCreateResponse = {
  task_id?: string
  base_resp?: MinimaxBaseResp
}

type MinimaxQueryResponse = {
  task_id?: string
  status?: string
  file_id?: string
  video_url?: string
  base_resp?: MinimaxBaseResp
}

function assertMinimaxBaseResp(baseResp: MinimaxBaseResp | undefined, context: string): void {
  if (!baseResp || typeof baseResp.status_code !== 'number' || baseResp.status_code === 0) {
    return
  }
  throw new Error(`${context} (${baseResp.status_code}): ${baseResp.status_msg ?? 'unknown error'}`)
}

function toDataUrl(buffer: Buffer, mimeType: string): string {
  return `data:${mimeType};base64,${buffer.toString('base64')}`
}

function resolveDurationSeconds(params: {
  model: string
  durationSeconds: number | undefined
}): number | undefined {
  if (typeof params.durationSeconds !== 'number' || !Number.isFinite(params.durationSeconds)) {
    return undefined
  }
  const rounded = Math.max(1, Math.round(params.durationSeconds))
  const allowed = MINIMAX_MODEL_ALLOWED_DURATIONS[params.model]
  if (!allowed || allowed.length === 0) {
    return rounded
  }
  return allowed.reduce((best, current) =>
    Math.abs(current - rounded) < Math.abs(best - rounded) ? current : best,
  )
}

async function pollMinimaxVideo(params: {
  taskId: string
  headers: Headers
  timeoutMs?: number
  baseUrl: string
}): Promise<MinimaxQueryResponse> {
  const deadline = Date.now() + (params.timeoutMs ?? DEFAULT_TIMEOUT_MS)
  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
    if (Date.now() > deadline) {
      throw new Error(`MiniMax video generation task ${params.taskId} timed out`)
    }
    const url = new URL(`${params.baseUrl}/v1/query/video_generation`)
    url.searchParams.set('task_id', params.taskId)
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: params.headers,
    })
    if (!response.ok) {
      throw new Error(`MiniMax video status request failed: ${response.status}`)
    }
    const payload = (await response.json()) as MinimaxQueryResponse
    assertMinimaxBaseResp(payload.base_resp, 'MiniMax video generation failed')
    switch (payload.status) {
      case 'Success':
        return payload
      case 'Fail':
        throw new Error(payload.base_resp?.status_msg ?? 'MiniMax video generation failed')
      case 'Preparing':
      case 'Processing':
      default:
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS))
        break
    }
  }
  throw new Error(`MiniMax video generation task ${params.taskId} did not finish in time`)
}

async function downloadVideoFromUrl(params: {
  url: string
  timeoutMs?: number
}): Promise<GeneratedVideoAsset> {
  const response = await fetch(params.url, { method: 'GET' })
  if (!response.ok) {
    throw new Error('MiniMax generated video download failed')
  }
  const mimeType = response.headers.get('content-type') ?? 'video/mp4'
  const arrayBuffer = await response.arrayBuffer()
  return {
    buffer: Buffer.from(arrayBuffer),
    mimeType,
    fileName: `video-1.${mimeType.includes('webm') ? 'webm' : 'mp4'}`,
  }
}

function resolveFirstFrameImage(req: VideoGenerationRequest): string | undefined {
  const input = req.inputImages?.[0]
  if (!input) {
    return undefined
  }
  if (input.url) {
    return input.url
  }
  if (!input.buffer) {
    throw new Error('MiniMax image-to-video input is missing image data.')
  }
  return toDataUrl(input.buffer, input.mimeType ?? 'image/png')
}

export function createMinimaxVideoProvider(apiKey: string): VideoGenerationProvider {
  return {
    id: 'minimax',
    label: 'MiniMax',
    defaultModel: DEFAULT_MINIMAX_VIDEO_MODEL,
    models: [
      DEFAULT_MINIMAX_VIDEO_MODEL,
      'MiniMax-Hailuo-2.3-Fast',
      'MiniMax-Hailuo-02',
    ],
    capabilities: {
      generate: {
        maxVideos: 1,
        maxDurationSeconds: 10,
        supportedDurations: [6, 10],
        aspectRatios: ['16:9', '9:16', '1:1'],
      },
      imageToVideo: {
        enabled: true,
        maxVideos: 1,
        maxInputImages: 1,
        maxDurationSeconds: 10,
        supportedDurations: [6, 10],
        aspectRatios: ['16:9', '9:16', '1:1'],
      },
      videoToVideo: {
        enabled: false,
      },
    },
    isConfigured: () => Boolean(apiKey),
    async generateVideo(req: VideoGenerationRequest): Promise<VideoGenerationResult> {
      if (!apiKey) {
        throw new Error('MiniMax API key missing')
      }

      const model = req.model ?? DEFAULT_MINIMAX_VIDEO_MODEL
      const baseUrl = DEFAULT_MINIMAX_VIDEO_BASE_URL
      const headers = new Headers({
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      })

      const body: Record<string, unknown> = {
        model,
        prompt: req.prompt,
      }

      const firstFrameImage = resolveFirstFrameImage(req)
      if (firstFrameImage) {
        body.first_frame_image = firstFrameImage
      }

      if (req.resolution) {
        body.resolution = req.resolution
      }

      const durationSeconds = resolveDurationSeconds({
        model,
        durationSeconds: req.durationSeconds,
      })
      if (typeof durationSeconds === 'number') {
        body.duration = durationSeconds
      }

      // Create video
      const createResponse = await fetch(`${baseUrl}/v1/video_generation`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      if (!createResponse.ok) {
        throw new Error(`MiniMax video generation failed: ${createResponse.status}`)
      }

      const submitted = (await createResponse.json()) as MinimaxCreateResponse
      assertMinimaxBaseResp(submitted.base_resp, 'MiniMax video generation failed')

      const taskId = submitted.task_id
      if (!taskId) {
        throw new Error('MiniMax video generation response missing task_id')
      }

      // Poll for completion
      const completed = await pollMinimaxVideo({
        taskId,
        headers,
        timeoutMs: req.timeoutMs ?? DEFAULT_TIMEOUT_MS,
        baseUrl,
      })

      // Download video
      const videoUrl = completed.video_url
      if (!videoUrl) {
        throw new Error('MiniMax video generation completed without a video URL')
      }

      const video = await downloadVideoFromUrl({
        url: videoUrl,
        timeoutMs: req.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      })

      return {
        videos: [video],
        model,
        metadata: {
          taskId,
          status: completed.status,
          fileId: completed.file_id,
          videoUrl,
        },
      }
    },
  }
}
