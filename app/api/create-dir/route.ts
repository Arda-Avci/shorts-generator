import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { path: dirPath } = body

    if (!dirPath) {
      return NextResponse.json({ success: false, error: 'Path is required' }, { status: 400 })
    }

    // Normalize path for Windows
    const normalizedPath = dirPath.replace(/\//g, path.sep)

    // Create directory if it doesn't exist
    if (!fs.existsSync(normalizedPath)) {
      fs.mkdirSync(normalizedPath, { recursive: true })
      console.log(`✅ Created directory: ${normalizedPath}`)
    } else {
      console.log(`📁 Directory already exists: ${normalizedPath}`)
    }

    return NextResponse.json({
      success: true,
      path: normalizedPath,
      exists: fs.existsSync(normalizedPath)
    })
  } catch (error: any) {
    console.error('❌ Create directory error:', error)
    return NextResponse.json({ success: false, error: error.message }, { status: 500 })
  }
}