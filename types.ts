export interface Material {
  id: string
  name: string
  type: 'video' | 'image' | 'audio' | 'script' | 'subtitle' | 'guide'
  path: string
  duration?: number
  description?: string
}

export interface Project {
  name: string
  materials: Material[]
}

export interface Config {
  duration: number
  style: string
  voiceTone: string
  format: string
  watermarkText?: string
  addMusic?: boolean
  musicVolume?: number
  musicFile?: string
}

export interface GuideOptions {
  clipStrategy?: 'uniform' | 'smart' | 'custom'
  transitions?: boolean
  introDuration?: number
  outroDuration?: number
  addWatermark?: boolean
  subtitleStyle?: 'below' | 'middle' | 'top'
}