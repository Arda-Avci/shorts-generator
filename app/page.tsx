'use client'

import { useState, useEffect, useCallback } from 'react'
import { Material, Project, Config } from '../types'
import ProjectSelector from '../components/ProjectSelector'
import MaterialSelector from '../components/MaterialSelector'
import PreviewPanel from '../components/PreviewPanel'
import GenerationPanel from '../components/GenerationPanel'
import HelpPanel from '../components/HelpPanel'

const BASE_DIR = 'C:/Users/Damla/Proje/Muhabbet'

interface DiscoveredProject {
  name: string
  path: string
  type: string
}

export default function Home() {
  const [step, setStep] = useState(1)
  const [selectedProjectPath, setSelectedProjectPath] = useState<string | null>(null)
  const [selectedProjectName, setSelectedProjectName] = useState<string>('')
  const [selectedMaterials, setSelectedMaterials] = useState<Material[]>([])
  const [config, setConfig] = useState<Config>({
    duration: 60,
    style: 'mysterious',
    voiceTone: 'tok_otoriter',
    format: '9:16',
  })

  const [projects, setProjects] = useState<DiscoveredProject[]>([])
  const [customPath, setCustomPath] = useState('')
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [helpDismissed, setHelpDismissed] = useState(false)

  const scanProjects = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/scan?mode=projects')
      const data = await res.json()
      if (data.status === 'success') {
        setProjects(data.projects)
      }
    } catch (error) {
      console.error('Proje taraması hatası:', error)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    scanProjects()
  }, [scanProjects])

  const scanMaterials = async (projectPath: string) => {
    setLoading(true)
    try {
      const res = await fetch(`/api/scan?mode=materials&path=${encodeURIComponent(projectPath)}`)
      const data = await res.json()
      if (data.status === 'success') {
        setMaterials(data.materials)
      }
    } catch (error) {
      console.error('Materyal taraması hatası:', error)
    }
    setLoading(false)
  }

  const handleProjectSelect = (project: DiscoveredProject) => {
    setSelectedProjectPath(project.path)
    setSelectedProjectName(project.name)
    setSelectedMaterials([])
    scanMaterials(project.path)
    setStep(2)
  }

  const handleCustomPathSubmit = () => {
    if (!customPath.trim()) return

    const projectName = customPath.split('/').pop() || customPath.split('\\').pop() || 'Custom'
    const project: DiscoveredProject = {
      name: projectName,
      path: customPath.replace(/^\/+/, '').replace(/\\/g, '/'),
      type: 'directory'
    }

    handleProjectSelect(project)
  }

  const handleMaterialsSelect = (selected: Material[]) => {
    setSelectedMaterials(selected)
    setStep(3)
  }

  const handleGenerate = () => {
    setStep(4)
  }

  const handleBackToProjects = () => {
    setStep(1)
    setSelectedProjectPath(null)
    setSelectedProjectName('')
    setMaterials([])
  }

  return (
    <div style={{ minHeight: '100vh', padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '40px', textAlign: 'center', position: 'relative' }}>
        <div style={{ position: 'absolute', top: 0, right: 0 }}>
          <button
            onClick={() => { setShowHelp(true); setHelpDismissed(true) }}
            style={{
              background: helpDismissed ? '#333' : 'linear-gradient(90deg, #00d4ff, #ff00ff)',
              border: 'none',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              color: helpDismissed ? '#888' : '#000',
              fontSize: '1.2rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              animation: helpDismissed ? 'none' : 'pulse 1.5s ease-in-out infinite',
            }}
            title="Yardım"
          >
            ?
          </button>
        </div>
        <h1 style={{
          fontSize: '2rem',
          fontWeight: 'bold',
          background: 'linear-gradient(90deg, #00d4ff, #ff00ff)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Shorts Generator
        </h1>
        <p style={{ color: '#888' }}>Arda Avcı Kanalı - Otomatik Shorts Oluşturucu</p>
        <style>{`
          @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
          }
        `}</style>
      </header>

      {showHelp && <HelpPanel onDismiss={() => setShowHelp(false)} />}

      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px', justifyContent: 'center' }}>
        {[1, 2, 3, 4].map(s => (
          <div key={s} style={{
            padding: '10px 20px',
            borderRadius: '20px',
            background: step >= s ? '#00d4ff' : '#333',
            color: step >= s ? '#000' : '#666',
            fontWeight: 'bold',
            cursor: step > s ? 'pointer' : 'default'
          }}
          onClick={() => {
            if (s === 1) handleBackToProjects()
            else if (s === 2 && selectedProjectPath) setStep(2)
            else if (s === 3 && selectedMaterials.length > 0) setStep(3)
          }}>
            {s === 1 && 'Proje'}
            {s === 2 && 'Materyaller'}
            {s === 3 && 'Önizleme'}
            {s === 4 && 'Oluştur'}
          </div>
        ))}
      </div>

      {step === 1 && (
        <div style={{ background: '#1a1a1a', borderRadius: '16px', padding: '30px' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '1.5rem' }}>Proje Seçin</h2>

          {loading && <p style={{ color: '#888' }}>Taranıyor...</p>}

          <div style={{
            background: '#2a2a2a',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '30px',
            border: '1px solid #333'
          }}>
            <h3 style={{ color: '#00d4ff', marginBottom: '15px', fontSize: '1rem' }}>Özel Klasör</h3>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={customPath}
                onChange={(e) => setCustomPath(e.target.value)}
                placeholder="C:/Users/Damla/Proje/Muhabbet/Gorunmez_Kodlar"
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#1a1a1a',
                  border: '1px solid #444',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '0.9rem'
                }}
              />
              <button
                onClick={handleCustomPathSubmit}
                style={{
                  padding: '12px 24px',
                  background: '#00d4ff',
                  color: '#000',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Tara
              </button>
            </div>
          </div>

          <div style={{
            background: '#2a2a2a',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <h3 style={{ color: '#888', marginBottom: '15px', fontSize: '1rem' }}>VEYA Otomatik Tarama</h3>
            <button
              onClick={scanProjects}
              style={{
                padding: '10px 20px',
                background: '#333',
                color: '#fff',
                border: '1px solid #444',
                borderRadius: '8px',
                cursor: 'pointer',
                marginBottom: '15px'
              }}
            >
              🔄 Yeniden Tara
            </button>
          </div>

          {projects.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '15px' }}>
              {projects.map(project => (
                <button
                  key={project.path}
                  onClick={() => handleProjectSelect(project)}
                  style={{
                    background: 'linear-gradient(135deg, #1e1e2e, #2a2a3e)',
                    border: '1px solid #333',
                    borderRadius: '12px',
                    padding: '20px',
                    cursor: 'pointer',
                    color: '#fff',
                    textAlign: 'left',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#00d4ff'
                    e.currentTarget.style.transform = 'translateY(-2px)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#333'
                    e.currentTarget.style.transform = 'translateY(0)'
                  }}
                >
                  <h3 style={{ margin: '0 0 10px 0', color: '#00d4ff' }}>{project.name}</h3>
                  <p style={{ margin: 0, color: '#666', fontSize: '0.85rem', wordBreak: 'break-all' }}>
                    {project.path}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {step === 2 && selectedProjectPath && (
        <MaterialSelector
          projectName={selectedProjectName}
          materials={materials}
          onBack={handleBackToProjects}
          onNext={handleMaterialsSelect}
        />
      )}

      {step === 3 && (
        <PreviewPanel
          projectName={selectedProjectName}
          materials={selectedMaterials}
          config={config}
          onConfigChange={setConfig}
          onBack={() => setStep(2)}
          onGenerate={handleGenerate}
        />
      )}

      {step === 4 && (
        <GenerationPanel
          projectName={selectedProjectName}
          projectPath={selectedProjectPath}
          materials={selectedMaterials}
          config={config}
          onBack={() => setStep(3)}
        />
      )}
    </div>
  )
}