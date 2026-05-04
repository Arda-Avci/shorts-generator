export * from './types'
export * from './provider-registry'
export * from './runtime'
export { createMinimaxVideoProvider } from './providers/minimax'
export { createCogVideoProvider } from './providers/cogvideo'

import { createMinimaxVideoProvider } from './providers/minimax'
import { createCogVideoProvider } from './providers/cogvideo'
import { registerVideoProvider } from './provider-registry'

const MINIMAX_API_KEY = process.env.MINIMAX_API_KEY ?? ''

export function initializeProviders(): void {
  // MiniMax - kredi gerektirir
  if (MINIMAX_API_KEY) {
    registerVideoProvider('minimax', () => createMinimaxVideoProvider(MINIMAX_API_KEY))
  }

  // CogVideo - yerel GPU'da çalışır, ücretsiz
  registerVideoProvider('cogvideo', () => createCogVideoProvider())
}

initializeProviders()
