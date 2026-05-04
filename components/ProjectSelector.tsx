'use client'

import { Project } from '../types'

interface Props {
  projects: Project[]
  onSelect: (name: string) => void
}

export default function ProjectSelector({ projects, onSelect }: Props) {
  return (
    <div style={{ background: '#1a1a1a', borderRadius: '16px', padding: '30px' }}>
      <h2 style={{ marginBottom: '20px', fontSize: '1.5rem' }}>Proje Seçin</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '15px' }}>
        {projects.map(project => (
          <button
            key={project.name}
            onClick={() => onSelect(project.name)}
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
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#00d4ff'; e.currentTarget.style.transform = 'translateY(-2px)' }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#333'; e.currentTarget.style.transform = 'translateY(0)' }}
          >
            <h3 style={{ margin: '0 0 10px 0', color: '#00d4ff' }}>{project.name}</h3>
            <p style={{ margin: 0, color: '#888', fontSize: '0.9rem' }}>
              {project.materials.length} materyal
            </p>
          </button>
        ))}
      </div>
    </div>
  )
}