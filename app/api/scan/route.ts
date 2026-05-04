import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

function scanDirectory(dirPath: string, baseDir: string): { name: string; path: string; type: string }[] {
  const items: { name: string; path: string; type: string }[] = []

  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name)
      const relativePath = path.relative(baseDir, fullPath)

      if (entry.isDirectory()) {
        // Only include series directories (must contain Gorseller or Senaryolar or Scripts)
        // shorts-generator folder should NOT be included - it doesn't have content folders
        const subItems = fs.readdirSync(fullPath, { withFileTypes: true })
        const hasContent = subItems.some(e =>
          e.name === 'Gorseller' ||
          e.name === 'Senaryolar' ||
          e.name === 'Scripts'
        )

        if (hasContent) {
          items.push({
            name: entry.name,
            path: relativePath,
            type: 'directory'
          })
        }
      }
    }
  } catch (error) {
    console.error(`Error scanning ${dirPath}:`, error)
  }

  return items
}

function scanMaterials(dirPath: string): { id: string; name: string; type: string; path: string }[] {
  const materials: { id: string; name: string; type: string; path: string }[] = []
  const baseDir = path.join(dirPath, '..')

  // Önce ana klasördeki dosyaları tara (mp4 vb.)
  try {
    const rootEntries = fs.readdirSync(dirPath, { withFileTypes: true })
    for (const entry of rootEntries) {
      if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase()
        if (['.mp4', '.mov', '.avi', '.webm'].includes(ext)) {
          const relativePath = path.relative(baseDir, path.join(dirPath, entry.name))
          materials.push({
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            name: entry.name.replace(ext, ''),
            type: 'video',
            path: relativePath.replace(/\\/g, '/')
          })
        }
      }
    }
  } catch (e) { /* ignore */ }

  // Alt klasörleri tara
  const scanDirs = ['Senaryolar', 'Scripts', 'Gorseller', '']

  for (const subDir of scanDirs) {
    const searchDir = subDir ? path.join(dirPath, subDir) : dirPath

    if (!fs.existsSync(searchDir)) continue

    try {
      const entries = fs.readdirSync(searchDir, { withFileTypes: true })

      for (const entry of entries) {
        if (entry.isFile()) {
          const ext = path.extname(entry.name).toLowerCase()
          let type = 'file'

          if (['.md', '.txt'].includes(ext)) {
            const lowerName = entry.name.toLowerCase()
            if (lowerName.includes('rehber') || lowerName.includes('guide')) {
              type = 'guide'
            } else {
              type = 'script'
            }
          }
          else if (['.srt', '.vtt', '.ass'].includes(ext)) type = 'subtitle'
          else if (['.png', '.jpg', '.jpeg', '.gif', '.webp'].includes(ext)) type = 'image'
          else if (['.mp4', '.mov', '.avi', '.webm'].includes(ext)) type = 'video'
          else if (['.mp3', '.wav', '.ogg', '.m4a'].includes(ext)) type = 'audio'
          else continue

          const relativePath = path.relative(baseDir, path.join(searchDir, entry.name))

          materials.push({
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            name: entry.name.replace(ext, ''),
            type,
            path: relativePath.replace(/\\/g, '/')
          })
        }
      }
    } catch (error) {
      console.error(`Error scanning ${searchDir}:`, error)
    }
  }

  return materials
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const mode = searchParams.get('mode') || 'projects'
  const dirPath = searchParams.get('path')

  const baseDir = 'C:/Users/Damla/Proje/Muhabbet'

  if (mode === 'projects') {
    const projects = scanDirectory(baseDir, baseDir)
    return NextResponse.json({ status: 'success', projects })
  }

  if (mode === 'materials' && dirPath) {
    const fullPath = path.join(baseDir, dirPath)
    const materials = scanMaterials(fullPath)
    return NextResponse.json({ status: 'success', materials })
  }

  if (mode === 'music') {
    const musicDir = path.join(baseDir, 'shorts-generator', 'bg-music')
    const files: { name: string; path: string; size: number }[] = []
    try {
      if (fs.existsSync(musicDir)) {
        const entries = fs.readdirSync(musicDir, { withFileTypes: true })
        for (const entry of entries) {
          if (entry.isFile() && entry.name.endsWith('.mp3')) {
            const fullPath = path.join(musicDir, entry.name)
            const stats = fs.statSync(fullPath)
            files.push({
              name: entry.name,
              path: fullPath.replace(/\\/g, '/'),
              size: stats.size
            })
          }
        }
      }
    } catch (e) { /* ignore */ }
    return NextResponse.json({ status: 'success', files })
  }

  return NextResponse.json({ status: 'error', message: 'Invalid request' }, { status: 400 })
}