import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const filePath = searchParams.get('path')

  if (!filePath) {
    return NextResponse.json({ error: 'Path is required' }, { status: 400 })
  }

  // Clean the path - handle both forward and backslashes
  const cleanPath = filePath.replace(/\//g, '\\')
  const fullPath = path.resolve(cleanPath)

  // Security check - only allow files from bg-music directory
  const bgMusicDir = path.resolve('C:\\Users\\Damla\\Proje\\Muhabbet\\shorts-generator\\bg-music').toLowerCase()
  const fullPathLower = fullPath.toLowerCase()

  if (!fullPathLower.startsWith(bgMusicDir)) {
    return NextResponse.json({ error: 'Access denied' }, { status: 403 })
  }

  if (!fs.existsSync(fullPath)) {
    return NextResponse.json({ error: 'File not found' }, { status: 404 })
  }

  try {
    const stat = fs.statSync(fullPath)
    const fileName = path.basename(fullPath)

    const readStream = fs.createReadStream(fullPath)

    return new NextResponse(readStream as any, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': stat.size.toString(),
        'Content-Disposition': `inline; filename="${fileName}"`,
        'Accept-Ranges': 'bytes',
      },
    })
  } catch (error) {
    return NextResponse.json({ error: 'Failed to read file' }, { status: 500 })
  }
}