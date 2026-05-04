'use client'

import { useState, useEffect, useRef } from 'react'
import { Material, Config } from '../types'

interface Props {
  projectName: string
  projectPath: string | null
  materials: Material[]
  config: Config
  onBack: () => void
}

type LogEntry = { message: string; type: 'info' | 'success' | 'error' }
type GenerationMode = 'clip' | 'ai'

export default function GenerationPanel({ projectName, projectPath, materials, config, onBack }: Props) {
  const [status, setStatus] = useState<'idle' | 'generating' | 'done' | 'error'>('idle')
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [outputFiles, setOutputFiles] = useState<{ fileName: string; filePath: string }[]>([])
  const [generationMode, setGenerationMode] = useState<GenerationMode>('clip')
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiDuration, setAiDuration] = useState(6)
  const [aiAspectRatio, setAiAspectRatio] = useState('9:16')
  const abortControllerRef = useRef<AbortController | null>(null)

  const BASE_DIR = 'C:/Users/Damla/Proje/Muhabbet'

  const addLog = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
    setLogs(prev => [...prev, { message, type }])
  }

  const clearLogs = () => setLogs([])

  const handleGenerate = async () => {
    if (generationMode === 'ai') {
      await handleAIGenerate()
    } else {
      await handleClipGenerate()
    }
  }

  const handleAIGenerate = async () => {
    if (!aiPrompt.trim()) {
      addLog('❌ Lütfen bir prompt girin', 'error')
      return
    }

    setStatus('generating')
    setProgress(0)
    setStage('Hazırlanıyor...')
    clearLogs()
    setOutputFiles([])

    const outputDir = projectPath
      ? `${BASE_DIR}/${projectPath}/output`
      : `${BASE_DIR}/shorts-generator/output`

    addLog('📁 Klasör hazırlanıyor...', 'info')

    try {
      const dirResponse = await fetch('/api/create-dir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: outputDir })
      })
      const dirResult = await dirResponse.json()

      if (!dirResult.success) {
        addLog(`❌ Klasör hatası: ${dirResult.error}`, 'error')
        setStatus('error')
        return
      }
      addLog('✅ Klasör hazır', 'success')
    } catch (err: any) {
      addLog(`❌ Bağlantı hatası: ${err.message}`, 'error')
      setStatus('error')
      return
    }

    addLog('🎬 AI video oluşturma başladı...', 'info')
    addLog(`📝 Prompt: ${aiPrompt.substring(0, 100)}...`, 'info')

    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch('/api/video-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: aiPrompt,
          durationSeconds: aiDuration,
          aspectRatio: aiAspectRatio,
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        addLog(`❌ Sunucu hatası: ${response.status}`, 'error')
        setStatus('error')
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        addLog('❌ Stream okunamadı', 'error')
        setStatus('error')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              switch (data.type) {
                case 'log':
                  addLog(data.message, data.logType || 'info')
                  break

                case 'progress':
                  setProgress(data.progress)
                  setStage(data.stage || '')
                  break

                case 'file':
                  setOutputFiles(prev => [...prev, { fileName: data.fileName, filePath: data.filePath }])
                  break

                case 'complete':
                  if (data.status === 'success' && data.video) {
                    // Save video to file
                    const videoBuffer = Buffer.from(data.video.buffer, 'base64')
                    const safeProjectName = projectName.replace(/[^a-zA-Z0-9ığüşöçİĞÜŞÖÇ]/g, '_').replace(/_+/g, '_')
                    const fileName = `ai_short_${safeProjectName}_${Date.now()}.mp4`
                    const filePath = `${outputDir}/${fileName}`

                    addLog(`💾 Video kaydediliyor...`, 'info')

                    const saveResponse = await fetch('/api/save-video', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        buffer: data.video.buffer,
                        filePath: filePath,
                        mimeType: data.video.mimeType,
                      })
                    })

                    const saveResult = await saveResponse.json()

                    if (saveResult.success) {
                      setProgress(100)
                      setStage('Tamamlandı!')
                      addLog('✅ AI video oluşturuldu!', 'success')
                      setOutputFiles([{ fileName, filePath: filePath.replace(/\\/g, '/') }])
                      setStatus('done')
                    } else {
                      addLog(`❌ Kayıt hatası: ${saveResult.error}`, 'error')
                      setStatus('error')
                    }
                  } else {
                    addLog(`❌ Hata: ${data.message}`, 'error')
                    setStatus('error')
                  }
                  break

                case 'error':
                  addLog(`❌ Hata: ${data.message}`, 'error')
                  setStatus('error')
                  break
              }
            } catch (e: any) {
              // JSON parse hatası - devam et
            }
          }
        }
      }

    } catch (err: any) {
      if (err.name === 'AbortError') {
        addLog('❌ İşlem iptal edildi', 'error')
      } else {
        addLog(`❌ Bağlantı hatası: ${err.message}`, 'error')
      }
      setStatus('error')
    }
  }

  const handleClipGenerate = async () => {
    setStatus('generating')
    setProgress(0)
    setStage('Hazırlanıyor...')
    clearLogs()
    setOutputFiles([])

    const outputDir = projectPath
      ? `${BASE_DIR}/${projectPath}/output`
      : `${BASE_DIR}/shorts-generator/output`

    addLog('📁 Klasör hazırlanıyor...', 'info')

    try {
      const dirResponse = await fetch('/api/create-dir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: outputDir })
      })
      const dirResult = await dirResponse.json()

      if (!dirResult.success) {
        addLog(`❌ Klasör hatası: ${dirResult.error}`, 'error')
        setStatus('error')
        return
      }
      addLog('✅ Klasör hazır', 'success')
    } catch (err: any) {
      addLog(`❌ Başlatılamadı`, 'error')
      setStatus('error')
      return
    }

    addLog('🎬 Video oluşturma başladı...', 'info')

    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectName,
          materials,
          config,
          outputPath: `${outputDir}/shorts_output.mp4`
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        addLog(`❌ Sunucu hatası: ${response.status}`, 'error')
        setStatus('error')
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        addLog('❌ Stream okunamadı', 'error')
        setStatus('error')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              switch (data.type) {
                case 'log':
                  addLog(data.message, data.logType || 'info')
                  break

                case 'progress':
                  setProgress(data.progress)
                  setStage(data.stage || '')
                  break

                case 'file':
                  setOutputFiles(prev => [...prev, { fileName: data.fileName, filePath: data.filePath }])
                  break

                case 'complete':
                  if (data.status === 'success') {
                    setProgress(100)
                    setStage('Tamamlandı!')
                    addLog('✅ Tüm videolar oluşturuldu!', 'success')
                    setStatus('done')
                  } else {
                    addLog(`❌ Hata: ${data.message}`, 'error')
                    setStatus('error')
                  }
                  break

                case 'error':
                  addLog(`❌ Hata: ${data.message}`, 'error')
                  setStatus('error')
                  break
              }
            } catch (e: any) {
              // JSON parse hatası - devam et
            }
          }
        }
      }

    } catch (err: any) {
      if (err.name === 'AbortError') {
        addLog('❌ İşlem iptal edildi', 'error')
      } else {
        addLog(`❌ Bağlantı hatası: ${err.message}`, 'error')
      }
      setStatus('error')
    }
  }

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const openFolder = () => {
    if (!outputFiles.length) return
    let folder = outputFiles[0].filePath.replace(/\\/g, '/')
    const lastSlash = folder.lastIndexOf('/')
    if (lastSlash > 0) {
      folder = folder.substring(0, lastSlash)
    }
    const winPath = folder.replace(/^\//, '').replace(/\//g, '\\')
    window.open(`file:///${winPath.replace(/^([A-Za-z]):/, '$1:')}`, '_blank')
  }

  return (
    <div style={{ background: '#1a1a1a', borderRadius: '16px', padding: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.5rem' }}>Shorts Oluşturma</h2>
        <button onClick={onBack} style={{ background: 'transparent', border: '1px solid #666', color: '#fff', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>
          ← Geri
        </button>
      </div>

      {/* Mode Toggle */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={() => setGenerationMode('clip')}
          style={{
            flex: 1,
            padding: '12px',
            background: generationMode === 'clip' ? '#00d4ff' : '#333',
            color: generationMode === 'clip' ? '#000' : '#fff',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            cursor: 'pointer',
          }}
        >
          🎬 Videodan Kırp
        </button>
        <button
          onClick={() => setGenerationMode('ai')}
          style={{
            flex: 1,
            padding: '12px',
            background: generationMode === 'ai' ? '#00d4ff' : '#333',
            color: generationMode === 'ai' ? '#000' : '#fff',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            cursor: 'pointer',
          }}
        >
          🤖 AI Oluştur
        </button>
      </div>

      {/* AI Generation Panel */}
      {generationMode === 'ai' && (
        <div style={{ background: '#2a2a2a', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
          <h3 style={{ color: '#00d4ff', marginBottom: '15px' }}>AI Video Oluştur</h3>
          <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '15px' }}>
            MiniMax AI ile metinden video oluşturun. 9:16 formatında YouTube Shorts için ideal.
          </p>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', color: '#888', marginBottom: '8px', fontSize: '0.9rem' }}>
              Video Prompt (Ne oluşturulsun?)
            </label>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="Örnek: Futuristik bir şehir manzarası, neon ışıklarıyla dolu sokaklar, dron çekimi..."
              rows={4}
              style={{
                width: '100%',
                padding: '12px',
                background: '#1a1a1a',
                border: '1px solid #444',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '0.9rem',
                resize: 'vertical',
                fontFamily: 'inherit',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', color: '#888', marginBottom: '8px', fontSize: '0.9rem' }}>
                Süre
              </label>
              <select
                value={aiDuration}
                onChange={(e) => setAiDuration(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#1a1a1a',
                  border: '1px solid #444',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '0.9rem',
                }}
              >
                <option value={6}>6 saniye</option>
                <option value={10}>10 saniye</option>
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', color: '#888', marginBottom: '8px', fontSize: '0.9rem' }}>
                Format
              </label>
              <select
                value={aiAspectRatio}
                onChange={(e) => setAiAspectRatio(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#1a1a1a',
                  border: '1px solid #444',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '0.9rem',
                }}
              >
                <option value="9:16">9:16 (Shorts)</option>
                <option value="16:9">16:9 (YouTube)</option>
                <option value="1:1">1:1 (Square)</option>
              </select>
            </div>
          </div>

          <div style={{ background: '#1a1a1a', padding: '12px', borderRadius: '8px', border: '1px solid #333' }}>
            <p style={{ color: '#666', fontSize: '0.8rem', margin: 0 }}>
              💡 <strong>İpucu:</strong> Detaylı ve görsel bir prompt kullanın. Örneğin: &quot;Cinematic drone shot of a futuristic city at night with neon lights, rain-slicked streets, cyberpunk aesthetic&quot;
            </p>
          </div>
        </div>
      )}

      {/* Clip Generation Info */}
      {generationMode === 'clip' && (
        <div style={{ background: '#2a2a2a', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ color: '#888' }}>Proje:</span>
            <span style={{ fontWeight: 'bold' }}>{projectName}</span>
          </div>
          {projectPath && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ color: '#888' }}>Çıkış:</span>
              <span style={{ color: '#00d4ff', fontSize: '0.85rem' }}>{projectPath}/output/</span>
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ color: '#888' }}>Materyaller:</span>
            <span>{materials.map(m => m.name).join(', ')}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#888' }}>Format:</span>
            <span>{config.format} • {config.duration}sn</span>
          </div>
        </div>
      )}

      {status === 'idle' && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '4rem', marginBottom: '20px' }}>
            {generationMode === 'ai' ? '🤖' : '🎬'}
          </div>
          <h3 style={{ marginBottom: '10px' }}>
            {generationMode === 'ai' ? 'AI Video Oluşturmaya Hazır' : 'Shorts Oluşturmaya Hazır'}
          </h3>
          <p style={{ color: '#888', marginBottom: '30px' }}>
            {generationMode === 'ai'
              ? 'MiniMax AI ile yeni video oluşturulacak.'
              : '3 adet 60 saniyelik YouTube Shorts oluşturulacak.'}
          </p>
          <button
            onClick={handleGenerate}
            style={{
              padding: '15px 40px',
              background: 'linear-gradient(90deg, #00d4ff, #ff00ff)',
              color: '#fff',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1.1rem',
              fontWeight: 'bold',
              cursor: 'pointer',
            }}
          >
            ▶️ Oluşturmaya Başla
          </button>
        </div>
      )}

      {(status === 'generating' || status === 'error') && (
        <div style={{ padding: '40px' }}>
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ color: status === 'error' ? '#ff4444' : '#00d4ff' }}>
                {status === 'generating' ? stage || 'İşleniyor...' : 'Hata oluştu'}
              </span>
              <span style={{ fontWeight: 'bold' }}>{progress}%</span>
            </div>
            <div style={{ background: '#333', borderRadius: '8px', height: '20px', overflow: 'hidden' }}>
              <div style={{
                width: `${progress}%`,
                height: '100%',
                background: status === 'error' ? '#ff4444' : 'linear-gradient(90deg, #00d4ff, #ff00ff)',
                transition: 'width 0.3s ease',
              }} />
            </div>
          </div>

          <div style={{ background: '#1a1a1a', borderRadius: '8px', padding: '15px', maxHeight: '250px', overflowY: 'auto' }}>
            {logs.map((log, i) => (
              <div key={i} style={{
                color: log.type === 'error' ? '#ff4444' : log.type === 'success' ? '#00ff88' : '#aaa',
                marginBottom: '8px',
                padding: '8px',
                background: log.type === 'error' ? 'rgba(255,68,68,0.1)' : log.type === 'success' ? 'rgba(0,255,136,0.1)' : 'transparent',
                borderRadius: '4px',
                borderLeft: log.type === 'error' ? '3px solid #ff4444' : log.type === 'success' ? '3px solid #00ff88' : '3px solid #555'
              }}>
                {log.message}
              </div>
            ))}
            {status === 'generating' && (
              <div style={{ color: '#00d4ff', marginTop: '10px', animation: 'blink 1s infinite' }}>
                ⏳ İşleniyor...
              </div>
            )}
          </div>

          {status === 'error' && (
            <button
              onClick={() => { setStatus('idle'); clearLogs(); setProgress(0); setStage('') }}
              style={{
                marginTop: '20px',
                padding: '12px 24px',
                background: '#333',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
              }}
            >
              ← Geri Dön
            </button>
          )}
        </div>
      )}

      {status === 'done' && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '4rem', marginBottom: '20px' }}>✅</div>
          <h3 style={{ color: '#00ff88', marginBottom: '10px' }}>
            {generationMode === 'ai' ? 'AI Video Oluşturuldu!' : '3 Shorts Oluşturuldu!'}
          </h3>
          <p style={{ color: '#888', marginBottom: '20px' }}>Videolarınız hazır.</p>
          <div style={{ background: '#2a2a2a', padding: '15px', borderRadius: '8px', marginBottom: '20px', textAlign: 'left' }}>
            {outputFiles.map((f, i) => (
              <div key={i} style={{ marginBottom: '8px', color: '#00d4ff' }}>
                📄 {f.fileName}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
            <button onClick={openFolder} style={{ padding: '12px 24px', background: '#333', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
              📁 Klasörü Aç
            </button>
            <button onClick={() => { setStatus('idle'); clearLogs(); setProgress(0); setStage(''); setOutputFiles([]) }} style={{ padding: '12px 24px', background: '#00d4ff', color: '#000', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
              🔄 Yeni Shorts Oluştur
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
