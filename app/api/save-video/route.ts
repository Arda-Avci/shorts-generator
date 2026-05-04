import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { buffer, filePath, mimeType } = body as {
      buffer: string
      filePath: string
      mimeType: string
    }

    if (!buffer || !filePath) {
      return NextResponse.json(
        { success: false, error: 'buffer and filePath are required' },
        { status: 400 }
      )
    }

    // Ensure directory exists
    const dir = path.dirname(filePath)
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }

    // Write file
    const videoBuffer = Buffer.from(buffer, 'base64')
    fs.writeFileSync(filePath, videoBuffer)

    return NextResponse.json({
      success: true,
      filePath,
      size: videoBuffer.length,
    })
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error)
    return NextResponse.json(
      { success: false, error: message },
      { status: 500 }
    )
  }
}
