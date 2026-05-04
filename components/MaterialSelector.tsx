'use client'

import { useState } from 'react'
import { Material } from '../types'

interface Props {
  projectName: string
  materials: Material[]
  onBack: () => void
  onNext: (materials: Material[]) => void
}

export default function MaterialSelector({ projectName, materials, onBack, onNext }: Props) {
  const [selected, setSelected] = useState<Material[]>([])

  const toggleMaterial = (mat: Material) => {
    if (selected.find(s => s.id === mat.id)) {
      setSelected(selected.filter(s => s.id !== mat.id))
    } else {
      setSelected([...selected, mat])
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'script': return '📝'
      case 'image': return '🖼️'
      case 'video': return '🎬'
      case 'audio': return '🔊'
      default: return '📁'
    }
  }

  return (
    <div style={{ background: '#1a1a1a', borderRadius: '16px', padding: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.5rem' }}>{projectName}</h2>
        <button
          onClick={onBack}
          style={{ background: 'transparent', border: '1px solid #666', color: '#fff', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}
        >
          ← Geri
        </button>
      </div>

      <p style={{ color: '#888', marginBottom: '20px' }}>Kullanmak istediğiniz materyalleri seçin (birden fazla seçebilirsiniz)</p>

      {materials.length === 0 ? (
        <p style={{ color: '#666', textAlign: 'center', padding: '40px' }}>Materyal bulunamadı</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '30px' }}>
          {materials.map(mat => {
            const isSelected = selected.find(s => s.id === mat.id)
            return (
              <button
                key={mat.id}
                onClick={() => toggleMaterial(mat)}
                style={{
                  background: isSelected ? '#00d4ff20' : '#2a2a2a',
                  border: `2px solid ${isSelected ? '#00d4ff' : '#333'}`,
                  borderRadius: '12px',
                  padding: '15px 20px',
                  cursor: 'pointer',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '15px',
                  textAlign: 'left',
                }}
              >
                <span style={{ fontSize: '1.5rem' }}>{getTypeIcon(mat.type)}</span>
                <div>
                  <div style={{ fontWeight: 'bold' }}>{mat.name}</div>
                  <div style={{ color: '#888', fontSize: '0.85rem' }}>{mat.type} • {mat.path}</div>
                </div>
                {isSelected && (
                  <span style={{ marginLeft: 'auto', color: '#00d4ff', fontWeight: 'bold' }}>✓</span>
                )}
              </button>
            )
          })}
        </div>
      )}

      <button
        onClick={() => onNext(selected)}
        disabled={selected.length === 0}
        style={{
          width: '100%',
          padding: '15px',
          background: selected.length > 0 ? '#00d4ff' : '#333',
          color: selected.length > 0 ? '#000' : '#666',
          border: 'none',
          borderRadius: '12px',
          fontSize: '1.1rem',
          fontWeight: 'bold',
          cursor: selected.length > 0 ? 'pointer' : 'not-allowed',
        }}
      >
        {selected.length > 0 ? `${selected.length} materyal ile devam et →` : 'Materyal seçin'}
      </button>
    </div>
  )
}