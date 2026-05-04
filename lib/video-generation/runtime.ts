import type {
  VideoGenerationProvider,
  VideoGenerateParams,
  VideoGenerateResult,
  VideoGenerationSourceAsset,
} from './types'
import { getVideoProvider, listVideoProviders } from './provider-registry'

export type FallbackAttempt = {
  provider: string
  model: string
  error: string
}

export interface GenerateVideoRuntimeResult extends VideoGenerateResult {
  attempts: FallbackAttempt[]
}

function resolveAspectRatio(params: {
  provider: VideoGenerationProvider
  model: string
  aspectRatio?: string
}): string | undefined {
  if (!params.aspectRatio) return undefined

  const caps = params.provider.capabilities.generate ?? params.provider.capabilities
  const supported = caps.aspectRatios

  if (!supported || supported.length === 0) {
    return params.aspectRatio
  }

  if (supported.includes(params.aspectRatio)) {
    return params.aspectRatio
  }

  return supported[0]
}

function resolveDuration(params: {
  provider: VideoGenerationProvider
  model: string
  durationSeconds?: number
}): number | undefined {
  if (typeof params.durationSeconds !== 'number') return undefined

  const caps = params.provider.capabilities.generate ?? params.provider.capabilities
  const supported = caps.supportedDurations

  if (!supported || supported.length === 0) {
    const max = caps.maxDurationSeconds
    if (typeof max === 'number') {
      return Math.min(params.durationSeconds, max)
    }
    return params.durationSeconds
  }

  if (supported.includes(params.durationSeconds)) {
    return params.durationSeconds
  }

  return supported.reduce((best, current) =>
    Math.abs(current - params.durationSeconds!) < Math.abs(best - params.durationSeconds!)
      ? current
      : best,
  )
}

export async function generateVideo(
  params: VideoGenerateParams,
  preferredProvider?: string,
): Promise<GenerateVideoRuntimeResult> {
  const candidates: Array<{ provider: VideoGenerationProvider; model: string }> = []

  if (preferredProvider) {
    const provider = getVideoProvider(preferredProvider)
    if (provider && provider.isConfigured()) {
      candidates.push({ provider, model: provider.defaultModel ?? '' })
    }
  }

  if (candidates.length === 0) {
    for (const provider of listVideoProviders()) {
      if (provider.isConfigured()) {
        candidates.push({ provider, model: provider.defaultModel ?? '' })
      }
    }
  }

  if (candidates.length === 0) {
    throw new Error(
      'No video generation provider configured. Please ensure CogVideo is running locally or set MINIMAX_API_KEY.',
    )
  }

  const attempts: FallbackAttempt[] = []
  let lastError: unknown

  for (const candidate of candidates) {
    try {
      const sanitized = {
        aspectRatio: resolveAspectRatio({
          provider: candidate.provider,
          model: candidate.model,
          aspectRatio: params.aspectRatio,
        }),
        durationSeconds: resolveDuration({
          provider: candidate.provider,
          model: candidate.model,
          durationSeconds: params.durationSeconds,
        }),
      }

      const result = await candidate.provider.generateVideo({
        provider: candidate.provider.id,
        model: candidate.model,
        prompt: params.prompt,
        aspectRatio: sanitized.aspectRatio,
        durationSeconds: sanitized.durationSeconds,
        resolution: params.resolution,
        inputImages: params.inputImages,
        inputVideos: params.inputVideos,
        timeoutMs: params.durationSeconds
          ? (params.durationSeconds + 30) * 1000
          : undefined,
      })

      return {
        videos: result.videos,
        provider: candidate.provider.id,
        model: result.model ?? candidate.model,
        attempts,
        metadata: result.metadata,
      }
    } catch (err) {
      lastError = err
      attempts.push({
        provider: candidate.provider.id,
        model: candidate.model,
        error: err instanceof Error ? err.message : String(err),
      })
    }
  }

  const attemptSummary = attempts
    .map(a => `${a.provider}/${a.model}: ${a.error}`)
    .join('; ')

  throw new Error(`All video providers failed. Attempts: ${attemptSummary}`)
}
