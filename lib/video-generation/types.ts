export type GeneratedVideoAsset = {
  buffer?: Buffer
  url?: string
  mimeType: string
  fileName?: string
  metadata?: Record<string, unknown>
}

export type VideoGenerationResolution = '480P' | '720P' | '768P' | '1080P'

export type VideoGenerationSourceAsset = {
  url?: string
  buffer?: Buffer
  mimeType?: string
  fileName?: string
  role?: string
  metadata?: Record<string, unknown>
}

export type VideoGenerationRequest = {
  provider: string
  model?: string
  prompt: string
  aspectRatio?: string
  resolution?: VideoGenerationResolution
  durationSeconds?: number
  inputImages?: VideoGenerationSourceAsset[]
  inputVideos?: VideoGenerationSourceAsset[]
  timeoutMs?: number
}

export type VideoGenerationResult = {
  videos: GeneratedVideoAsset[]
  model?: string
  metadata?: Record<string, unknown>
}

export type VideoGenerationModeCapabilities = {
  maxVideos?: number
  maxInputImages?: number
  maxInputVideos?: number
  maxDurationSeconds?: number
  supportedDurations?: readonly number[]
  aspectRatios?: readonly string[]
  resolutions?: readonly VideoGenerationResolution[]
  supportsAudio?: boolean
  supportsWatermark?: boolean
}

export type VideoGenerationProviderCapabilities = VideoGenerationModeCapabilities & {
  generate?: VideoGenerationModeCapabilities
  imageToVideo?: VideoGenerationModeCapabilities & { enabled: boolean }
  videoToVideo?: VideoGenerationModeCapabilities & { enabled: boolean }
}

export type VideoGenerationProvider = {
  id: string
  label: string
  defaultModel?: string
  models?: string[]
  capabilities: VideoGenerationProviderCapabilities
  isConfigured: () => boolean
  generateVideo: (req: VideoGenerationRequest) => Promise<VideoGenerationResult>
}

export interface VideoGenerateParams {
  prompt: string
  model?: string
  aspectRatio?: string
  resolution?: VideoGenerationResolution
  durationSeconds?: number
  inputImages?: VideoGenerationSourceAsset[]
  inputVideos?: VideoGenerationSourceAsset[]
}

export interface VideoGenerateResult {
  videos: GeneratedVideoAsset[]
  provider: string
  model: string
  metadata?: Record<string, unknown>
}
