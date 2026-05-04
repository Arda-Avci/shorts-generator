import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const { folderPath } = await request.json()

    if (!folderPath) {
      return NextResponse.json({ error: 'folderPath is required' }, { status: 400 })
    }

    // Normalize path for Windows
    const winPath = folderPath.replace(/\//g, '\\')

    // Open folder in Windows Explorer
    exec(`explorer "${winPath}"`)

    return NextResponse.json({ status: 'success' })
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
