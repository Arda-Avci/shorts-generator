'use client'

import { useState, useEffect } from 'react'
import { Material, Config } from '../types'

interface Props {
  projectName: string
  materials: Material[]
  config: Config
  onConfigChange: (config: Config) => void
  onBack: () => void
  onGenerate: () => void
}

interface MusicFile {
  name: string
  path: string
  size: number
}

export default function PreviewPanel({ projectName, materials, config, onConfigChange, onBack, onGenerate }: Props) {
  const [musicFiles, setMusicFiles] = useState<MusicFile[]>([])
  const [loadingMusic, setLoadingMusic] = useState(false)
  const [playingMusic, setPlayingMusic] = useState<string | null>(null)
  const [audioRef, setAudioRef] = useState<HTMLAudioElement | null>(null)

  useEffect(() => {
    const audio = new Audio()
    setAudioRef(audio)
    return () => {
      audio.pause()
    }
  }, [])

  const loadMusicFiles = async () => {
    setLoadingMusic(true)
    try {
      const res = await fetch('/api/scan?mode=music')
      const data = await res.json()
      if (data.status === 'success') {
        setMusicFiles(data.files || [])
      }
    } catch (error) {
      console.error('Müzik yüklenirken hata:', error)
    }
    setLoadingMusic(false)
  }

  useEffect(() => {
    if (config.addMusic && musicFiles.length === 0) {
      loadMusicFiles()
    }
    if (!config.addMusic) {
      setMusicFiles([])
      if (audioRef) {
        audioRef.pause()
        setPlayingMusic(null)
      }
    }
  }, [config.addMusic, musicFiles.length, audioRef])

  const playMusic = (path: string) => {
    if (!audioRef) return

    if (playingMusic === path) {
      audioRef.pause()
      setPlayingMusic(null)
    } else {
      // Use API endpoint to proxy the file instead of direct file:// URL
      const encodedPath = encodeURIComponent(path)
      audioRef.src = `/api/music?path=${encodedPath}`
      audioRef.play()
        .then(() => setPlayingMusic(path))
        .catch(err => {
          console.error('Audio playback error:', err)
          // Fallback: try direct path
          audioRef.src = path
          audioRef.play()
            .then(() => setPlayingMusic(path))
            .catch(err2 => console.error('Fallback also failed:', err2))
        })
    }
  }

  const selectMusic = (path: string, name: string) => {
    onConfigChange({ ...config, musicFile: path })
  }

  return (
    <div style={{ background: '#1a1a1a', borderRadius: '16px', padding: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.5rem' }}>Önizleme & Ayarlar</h2>
        <button onClick={onBack} style={{ background: 'transparent', border: '1px solid #666', color: '#fff', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>
          ← Geri
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
        <div>
          <h3 style={{ color: '#00d4ff', marginBottom: '15px' }}>Seçilen Proje</h3>
          <div style={{ background: '#2a2a2a', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '10px' }}>{projectName}</div>
            <div style={{ color: '#888' }}>{materials.length} materyal seçildi</div>
          </div>

          <h3 style={{ color: '#00d4ff', marginBottom: '15px' }}>Materyaller</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {materials.map(mat => (
              <div key={mat.id} style={{ background: '#2a2a2a', padding: '12px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>{mat.type === 'script' ? '📝' : mat.type === 'image' ? '🖼️' : mat.type === 'video' ? '🎬' : '📄'}</span>
                <span>{mat.name}</span>
              </div>
            ))}
          </div>

          <h3 style={{ color: '#00d4ff', marginBottom: '15px', marginTop: '20px' }}>Video Yapısı</h3>
          <div style={{ background: '#2a2a2a', padding: '15px', borderRadius: '8px', fontSize: '0.85rem', color: '#888' }}>
            <div style={{ marginBottom: '5px' }}>• 2s Giriş (Intro)</div>
            <div style={{ marginBottom: '5px' }}>• 18s Kısım 1 + fade-out</div>
            <div style={{ marginBottom: '5px' }}>• 18s Kısım 2 + fade-in/out</div>
            <div style={{ marginBottom: '5px' }}>• 18s Kısım 3 + fade-in</div>
            <div>• 2s Çıkış (Outro)</div>
            <div style={{ marginTop: '10px', color: '#ff00ff' }}>• Son 10s Watermark</div>
          </div>
        </div>

        <div>
          <h3 style={{ color: '#00d4ff', marginBottom: '15px' }}>Video Ayarları</h3>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#888' }}>Video Formatı</label>
            <select
              value={config.format}
              onChange={e => onConfigChange({ ...config, format: e.target.value })}
              style={{
                width: '100%',
                padding: '12px',
                background: '#2a2a2a',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '1rem',
              }}
            >
              <option value="9:16">9:16 (Portrait - Shorts)</option>
              <option value="16:9">16:9 (Landscape)</option>
              <option value="1:1">1:1 (Square)</option>
            </select>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#888' }}>Video Stili</label>
            <select
              value={config.style}
              onChange={e => onConfigChange({ ...config, style: e.target.value })}
              style={{
                width: '100%',
                padding: '12px',
                background: '#2a2a2a',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '1rem',
              }}
            >
              <option value="mysterious">Gizemli / Otoriter</option>
              <option value="energetic">Enerjik / Hızlı</option>
              <option value="calm">Sakin / Felsefi</option>
              <option value="dark">Karanlık / Gerilim</option>
            </select>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#888' }}>Ses Tonu</label>
            <select
              value={config.voiceTone}
              onChange={e => onConfigChange({ ...config, voiceTone: e.target.value })}
              style={{
                width: '100%',
                padding: '12px',
                background: '#2a2a2a',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '1rem',
              }}
            >
              <option value="tok_otoriter">Tok, Otoriter, Gizemli (Erkek)</option>
              <option value="soft">Yumuşak / Bilgilendirici</option>
              <option value="energetic">Enerjik / Heyecanlı</option>
            </select>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#888' }}>Watermark Metni (son 10s - üst kısım)</label>
            <input
              type="text"
              value={config.watermarkText || "Daha fazlası için,.youtube.com/@ArdaAvc"}
              onChange={e => onConfigChange({ ...config, watermarkText: e.target.value })}
              placeholder="İki satır: virgül ile ayırın"
              style={{
                width: '100%',
                padding: '12px',
                background: '#2a2a2a',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '0.9rem',
              }}
            />
            <small style={{ color: '#555', fontSize: '0.75rem' }}>Virgül ile iki satıra ayırabilirsiniz</small>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <input
                type="checkbox"
                id="addMusic"
                checked={config.addMusic || false}
                onChange={e => onConfigChange({ ...config, addMusic: e.target.checked })}
              />
              <label htmlFor="addMusic" style={{ color: '#fff', cursor: 'pointer' }}>Arka Plan Müziği Ekle</label>
            </div>
            {config.addMusic && (
              <div>
                <label style={{ display: 'block', marginBottom: '8px', color: '#888' }}>Müzik Ses Seviyesi: {config.musicVolume || 70}%</label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={config.musicVolume || 70}
                  onChange={e => onConfigChange({ ...config, musicVolume: parseInt(e.target.value) })}
                  style={{ width: '100%' }}
                />

                {/* Müzik Dosyası Seçimi */}
                <div style={{ marginTop: '15px', background: '#1a1a1a', borderRadius: '8px', padding: '15px' }}>
                  <div style={{ color: '#888', marginBottom: '10px', fontSize: '0.85rem' }}>Müzik Dosyası Seç:</div>

                  {loadingMusic && (
                    <div style={{ color: '#555', textAlign: 'center', padding: '20px' }}>Müzikler yükleniyor...</div>
                  )}

                  {!loadingMusic && musicFiles.length === 0 && (
                    <div style={{ color: '#555', textAlign: 'center', padding: '20px' }}>
                      Müzik dosyası bulunamadı.
                      <button
                        onClick={loadMusicFiles}
                        style={{
                          display: 'block',
                          margin: '10px auto 0',
                          padding: '8px 16px',
                          background: '#333',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer'
                        }}
                      >
                        🔄 Yeniden Dene
                      </button>
                    </div>
                  )}

                  <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    {musicFiles.map((file, idx) => {
                      const isSelected = config.musicFile === file.path
                      const isPlaying = playingMusic === file.path
                      return (
                        <div
                          key={idx}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            padding: '10px',
                            background: isSelected ? '#00d4ff22' : '#2a2a2a',
                            borderRadius: '6px',
                            marginBottom: '6px',
                            cursor: 'pointer',
                            border: isSelected ? '1px solid #00d4ff' : '1px solid transparent'
                          }}
                          onClick={() => selectMusic(file.path, file.name)}
                        >
                          <button
                            onClick={(e) => { e.stopPropagation(); playMusic(file.path) }}
                            style={{
                              width: '32px',
                              height: '32px',
                              borderRadius: '50%',
                              background: isPlaying ? '#ff00ff' : '#00d4ff',
                              color: '#000',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '14px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            {isPlaying ? '⏸' : '▶'}
                          </button>
                          <div style={{ flex: 1 }}>
                            <div style={{ color: '#fff', fontSize: '0.9rem' }}>{file.name}</div>
                            <div style={{ color: '#555', fontSize: '0.75rem' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                          </div>
                          {isSelected && (
                            <span style={{ color: '#00d4ff', fontSize: '1.2rem' }}>✓</span>
                          )}
                        </div>
                      )
                    })}
                  </div>

                  <div style={{ marginTop: '10px', fontSize: '0.75rem', color: '#555' }}>
                    Seçili: {config.musicFile ? config.musicFile.split('/').pop() : 'Rastgele seçilecek'}
                  </div>
                </div>

                <small style={{ color: '#555', fontSize: '0.75rem' }}>Intro: tam ses, Ara: düşük, Outro: tekrar tam ses</small>
              </div>
            )}
          </div>
        </div>
      </div>

      <button
        onClick={onGenerate}
        style={{
          width: '100%',
          marginTop: '20px',
          padding: '18px',
          background: 'linear-gradient(90deg, #00d4ff, #ff00ff)',
          color: '#fff',
          border: 'none',
          borderRadius: '12px',
          fontSize: '1.2rem',
          fontWeight: 'bold',
          cursor: 'pointer',
        }}
      >
        🎬 Shorts Oluştur
      </button>
    </div>
  )
}