import type { VideoGenerationProvider } from './types'

type ProviderFactory = () => VideoGenerationProvider | null

const providers = new Map<string, ProviderFactory>()
const providerInstances = new Map<string, VideoGenerationProvider>()

export function registerVideoProvider(id: string, factory: ProviderFactory): void {
  providers.set(id, factory)
}

export function getVideoProvider(id: string): VideoGenerationProvider | null {
  if (providerInstances.has(id)) {
    return providerInstances.get(id)!
  }

  const factory = providers.get(id)
  if (!factory) {
    return null
  }

  const instance = factory()
  if (instance) {
    providerInstances.set(id, instance)
  }
  return instance
}

export function listVideoProviders(): VideoGenerationProvider[] {
  const result: VideoGenerationProvider[] = []
  for (const [id, factory] of providers) {
    const instance = factory()
    if (instance) {
      providerInstances.set(id, instance)
      result.push(instance)
    }
  }
  return result
}

export function clearProviderCache(): void {
  providerInstances.clear()
}
