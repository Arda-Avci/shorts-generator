import { NextRequest, NextResponse } from 'next/server'
import { execSync, spawn } from 'child_process'
import path from 'path'
import fs from 'fs'

interface Material {
  id: string
  name: string
  type: 'video' | 'image' | 'audio' | 'script' | 'subtitle' | 'guide'
  path: string
}

interface Config {
  duration: number
  style: string
  voiceTone: string
  format: string
  watermarkText?: string
  addMusic?: boolean
  musicVolume?: number
  musicFile?: string
}

interface GuideOptions {
  clipStrategy?: 'uniform' | 'smart' | 'custom'
  transitions?: boolean
  introDuration?: number
  outroDuration?: number
  addWatermark?: boolean
  subtitleStyle?: 'below' | 'middle' | 'top'
  voiceTone?: string
  style?: string
  watermarkText?: string
  addMusic?: boolean
  musicVolume?: number
  musicFile?: string
}

function findNextFileNumber(outputDir: string, baseName: string): number {
  try {
    const files = fs.readdirSync(outputDir)
    const existingNumbers: number[] = []
    for (const file of files) {
      if (file.startsWith(baseName)) {
        const match = file.match(/_(\d+)\.mp4$/)
        if (match) existingNumbers.push(parseInt(match[1]))
      }
    }
    return existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1
  } catch {
    return 1
  }
}

function cleanupTempFiles(outputDir: string, baseName: string) {
  try {
    fs.readdirSync(outputDir).forEach(f => {
      // Geçici dosyaları sil (ör. _c1.mp4, _wm.mp4, _ic.mp4), numaralandırılmış ana videoları (ör. _1.mp4) KORU
      if (f.startsWith(baseName) && !f.match(/_\d+\.mp4$/)) {
        try { fs.unlinkSync(path.join(outputDir, f)) } catch {}
      }
    })
  } catch (e) {}
}

function parseGuide(content: string): GuideOptions {
  const options: GuideOptions = {}
  const lines = content.split('\n')

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//')) continue

    // clipStrategy
    if (trimmed.match(/^clipStrategy[\s:]+(\w+)/i)) {
      const match = trimmed.match(/^clipStrategy[\s:]+(\w+)/i)
      if (match && ['uniform', 'smart', 'custom'].includes(match[1].toLowerCase())) {
        options.clipStrategy = match[1].toLowerCase() as 'uniform' | 'smart' | 'custom'
      }
    }

    // transitions
    if (trimmed.match(/^transitions[\s:]+(true|false|yes|no|evet|hayır)/i)) {
      const match = trimmed.match(/^transitions[\s:]+(true|false|yes|no|evet|hayır)/i)
      if (match) {
        const val = match[1].toLowerCase()
        options.transitions = val === 'true' || val === 'yes' || val === 'evet'
      }
    }

    // introDuration
    if (trimmed.match(/^introDuration[\s:]+(\d+)/i)) {
      const match = trimmed.match(/^introDuration[\s:]+(\d+)/i)
      if (match) options.introDuration = parseInt(match[1])
    }

    // outroDuration
    if (trimmed.match(/^outroDuration[\s:]+(\d+)/i)) {
      const match = trimmed.match(/^outroDuration[\s:]+(\d+)/i)
      if (match) options.outroDuration = parseInt(match[1])
    }

    // addWatermark
    if (trimmed.match(/^addWatermark[\s:]+(true|false|yes|no|evet|hayır)/i)) {
      const match = trimmed.match(/^addWatermark[\s:]+(true|false|yes|no|evet|hayır)/i)
      if (match) {
        const val = match[1].toLowerCase()
        options.addWatermark = val === 'true' || val === 'yes' || val === 'evet'
      }
    }

    // subtitleStyle
    if (trimmed.match(/^subtitleStyle[\s:]+(\w+)/i)) {
      const match = trimmed.match(/^subtitleStyle[\s:]+(\w+)/i)
      if (match && ['below', 'middle', 'top'].includes(match[1].toLowerCase())) {
        options.subtitleStyle = match[1].toLowerCase() as 'below' | 'middle' | 'top'
      }
    }

    // voiceTone
    if (trimmed.match(/^voiceTone[\s:]+(.+)/i)) {
      const match = trimmed.match(/^voiceTone[\s:]+(.+)/i)
      if (match) options.voiceTone = match[1].trim()
    }

    // style
    if (trimmed.match(/^style[\s:]+(.+)/i)) {
      const match = trimmed.match(/^style[\s:]+(.+)/i)
      if (match) options.style = match[1].trim()
    }

    // watermarkText
    if (trimmed.match(/^watermarkText[\s:]+(.+)/i)) {
      const match = trimmed.match(/^watermarkText[\s:]+(.+)/i)
      if (match) options.watermarkText = match[1].trim()
    }

    // addMusic
    if (trimmed.match(/^addMusic[\s:]+(true|false|yes|no|evet|hayır)/i)) {
      const match = trimmed.match(/^addMusic[\s:]+(true|false|yes|no|evet|hayır)/i)
      if (match) {
        const val = match[1].toLowerCase()
        options.addMusic = val === 'true' || val === 'yes' || val === 'evet'
      }
    }

    // musicVolume
    if (trimmed.match(/^musicVolume[\s:]+(\d+)/i)) {
      const match = trimmed.match(/^musicVolume[\s:]+(\d+)/i)
      if (match) options.musicVolume = parseInt(match[1])
    }
  }

  return options
}

async function generateSubtitlesFromVideo(
  videoPath: string,
  outputSrtPath: string,
  log: (msg: string, type?: string) => void,
  ffmpegExe: string = 'ffmpeg'
): Promise<boolean> {
  return new Promise((resolve) => {
    try {
      const scriptPath = path.join(process.cwd(), 'scripts', 'transcribe.py')
      if (!fs.existsSync(scriptPath)) {
        log(`   ⚠️ Transkripsiyon scripti bulunamadı: ${scriptPath}`, 'error')
        resolve(false)
        return
      }

      const videoPathUnix = videoPath.replace(/\\/g, '/')
      const srtPathUnix = outputSrtPath.replace(/\\/g, '/')
      const ffmpegUnix = ffmpegExe.replace(/\\/g, '/')

      log(`   🎙️ Whisper ile altyazı oluşturuluyor...`, 'info')
      log(`   🎙️ FFmpeg: ${ffmpegUnix}`, 'info')
      const cmd = `python "${scriptPath}" "${videoPathUnix}" "${srtPathUnix}" base "${ffmpegUnix}"`
      const proc = spawn(cmd, [], { shell: true })

      let stdout = ''
      let stderr = ''
      if (proc.stdout) proc.stdout.on('data', (d: Buffer) => {
        const line = d.toString().trim()
        stdout += line + '\n'
        if (line) log(`   🎙️ ${line}`, 'info')
      })
      if (proc.stderr) proc.stderr.on('data', (d: Buffer) => { stderr += d.toString() })

      proc.on('close', (code: number | null) => {
        if (code === 0 && fs.existsSync(outputSrtPath)) {
          const content = fs.readFileSync(outputSrtPath, 'utf-8')
          const segmentCount = (content.match(/^\d+$/gm) || []).length
          log(`   ✅ Whisper transkripsiyon tamamlandı (${segmentCount} segment)`, 'success')
          resolve(true)
        } else {
          log(`   ⚠️ Whisper transkripsiyon başarısız: ${stderr.slice(-300)}`, 'error')
          // Fallback: boş SRT oluştur (video yine de üretilsin)
          try {
            fs.writeFileSync(outputSrtPath, '', 'utf-8')
          } catch {}
          resolve(false)
        }
      })

      proc.on('error', (err: Error) => {
        log(`   ⚠️ Python çalıştırılamadı: ${err.message}`, 'error')
        resolve(false)
      })
    } catch (e: any) {
      log(`   ⚠️ Altyazı oluşturma hatası: ${e.message}`, 'error')
      resolve(false)
    }
  })
}

async function burnSubtitles(ffmpegExe: string, videoPath: string, subtitlePath: string, outputPath: string): Promise<boolean> {
  return new Promise((resolve) => {
    try {
      // FFmpeg subtitle filtresi Windows yollarında : ve \ ile sorun çıkarır
      // Yolu / ile değiştir ve : karakterini escape et
      const escapedSubPath = subtitlePath
        .replace(/\\/g, '/')
        .replace(/:/g, '\\\\:')
      const videoPathUnix = videoPath.replace(/\\/g, '/')
      const outputPathUnix = outputPath.replace(/\\/g, '/')
      const cmd = `"${ffmpegExe}" -y -i "${videoPathUnix}" -vf "subtitles='${escapedSubPath}':force_style='FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,MarginV=30'" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${outputPathUnix}"`
      console.log('[burnSubtitles] cmd:', cmd.substring(0, 300))
      const proc = spawn(cmd, [], { shell: true })
      let stderr = ''
      if (proc.stderr) proc.stderr.on('data', (d: Buffer) => { stderr += d.toString() })
      proc.on('close', (code: number | null) => {
        if (code !== 0) {
          console.error('[burnSubtitles] FFmpeg error:', stderr.slice(-500))
        }
        resolve(code === 0 && fs.existsSync(outputPath))
      })
      proc.on('error', (err) => {
        console.error('[burnSubtitles] spawn error:', err.message)
        resolve(false)
      })
    } catch (e: any) {
      console.error(`   ⚠️ Burn subtitles failed: ${e.message}`)
      resolve(false)
    }
  })
}

function execFfmpeg(ffmpegExe: string, args: string[], log: (msg: string, type?: string) => void): Promise<boolean> {
  return new Promise((resolve) => {
    const proc = spawn(ffmpegExe, args, { shell: true })

    let stderr = ''
    proc.stderr.on('data', (data) => {
      stderr += data.toString()
    })

    proc.on('close', (code) => {
      if (code === 0) {
        resolve(true)
      } else {
        log(`   ❌ FFmpeg hatası: ${stderr.slice(-200)}`, 'error')
        resolve(false)
      }
    })

    proc.on('error', (err) => {
      log(`   ❌ FFmpeg başlatılamadı: ${err.message}`, 'error')
      resolve(false)
    })
  })
}

function getRandomMusic(baseDir: string): string | null {
  const musicDir = path.join(baseDir, 'shorts-generator', 'bg-music')
  try {
    if (!fs.existsSync(musicDir)) return null
    const files = fs.readdirSync(musicDir).filter(f => f.endsWith('.mp3'))
    if (files.length === 0) return null
    const selected = files[Math.floor(Math.random() * files.length)]
    return path.join(musicDir, selected)
  } catch {
    return null
  }
}

function execFfmpegAsync(cmd: string, log: (msg: string, type?: string) => void): Promise<boolean> {
  return new Promise((resolve) => {
    log(`   🔧 FFmpeg cmd: ${cmd.substring(0, 200)}...`, 'info')
    const proc = spawn(cmd, [], { shell: true })
    let stderr = ''
    if (proc.stderr) proc.stderr.on('data', (d: Buffer) => { stderr += d.toString() })
    proc.on('close', (code: number | null) => {
      if (code === 0) resolve(true)
      else { log(`   ❌ Hata: ${stderr.slice(-300)}`, 'error'); resolve(false) }
    })
    proc.on('error', (err: Error) => {
      log(`   ❌ FFmpeg başlatılamadı: ${err.message}`, 'error'); resolve(false)
    })
  })
}

async function createShortsVideo(
  ffmpegExe: string,
  sourcePath: string,
  outputPath: string,
  baseDir: string,
  clip1Start: number,
  clip2Start: number,
  clip3Start: number,
  introImage: string,
  outroImage: string | null,
  size: string,
  subtitlePath: string | null,
  watermarkText: string,
  addMusic: boolean = false,
  musicVolume: number = 70,
  musicFile: string | null = null,
  log: (msg: string, type?: string) => void,
  send: (data: any) => void,
  guideOptions: GuideOptions = {},
  videoNum: number = 1
): Promise<boolean> {
  try {
    const CLIP_DURATION = 18
    const INTRO_DURATION = guideOptions.introDuration || 2
    const OUTRO_DURATION = guideOptions.outroDuration || 2

    const baseName = path.basename(outputPath, '.mp4')
    const outputDir = path.dirname(outputPath)
    const vLabel = `Video ${videoNum}/3`

    // Progress helper: 0-100 arası relative progress gönderir
    const p = (pct: number, label: string) => {
      send({ type: 'progress', progress: pct, stage: `${vLabel} - ${label}` })
    }

    log(`🎬 ${vLabel}: ${baseName}`, 'info')
    log(`📹 Klipler: ${clip1Start}s, ${clip2Start}s, ${clip3Start}s`, 'info')

    // Watermark metni iki satıra böl
    const watermarkLines = watermarkText.split(',')
    const line1 = watermarkLines[0] || watermarkText
    const line2 = watermarkLines.slice(1).join(',').trim() || ''

    // === 1. Klipler ===
    const clip1 = path.join(outputDir, `${baseName}_c1.mp4`)
    const clip2 = path.join(outputDir, `${baseName}_c2.mp4`)
    const clip3 = path.join(outputDir, `${baseName}_c3.mp4`)

    log(`📹 [1/9] Clip 1 oluşturuluyor (${clip1Start}s)...`, 'info')
    p(2, 'Clip 1 oluşturuluyor')
    const sourcePathUnix = sourcePath.replace(/\\/g, '/')
    const clip1Unix = clip1.replace(/\\/g, '/')
    let cmd = `"${ffmpegExe}" -y -ss ${clip1Start} -i "${sourcePathUnix}" -t ${CLIP_DURATION} -vf "scale=${size}:force_original_aspect_ratio=decrease,pad=${size}:(ow-iw)/2:(oh-ih)/2,fade=t=out:st=15:d=3" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${clip1Unix}"`
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Clip 1 tamam`, 'success')
    p(12, 'Clip 1 tamamlandı')

    log(`📹 [2/9] Clip 2 oluşturuluyor (${clip2Start}s)...`, 'info')
    p(14, 'Clip 2 oluşturuluyor')
    const clip2Unix = clip2.replace(/\\/g, '/')
    cmd = `"${ffmpegExe}" -y -ss ${clip2Start} -i "${sourcePathUnix}" -t ${CLIP_DURATION} -vf "scale=${size}:force_original_aspect_ratio=decrease,pad=${size}:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=1,fade=t=out:st=15:d=3" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${clip2Unix}"`
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Clip 2 tamam`, 'success')
    p(24, 'Clip 2 tamamlandı')

    log(`📹 [3/9] Clip 3 oluşturuluyor (${clip3Start}s)...`, 'info')
    p(26, 'Clip 3 oluşturuluyor')
    const clip3Unix = clip3.replace(/\\/g, '/')
    cmd = `"${ffmpegExe}" -y -ss ${clip3Start} -i "${sourcePathUnix}" -t ${CLIP_DURATION} -vf "scale=${size}:force_original_aspect_ratio=decrease,pad=${size}:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=1" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${clip3Unix}"`
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Clip 3 tamam`, 'success')
    p(36, 'Clip 3 tamamlandı')

    // === 2. Intro ve Outro ===
    const intro = path.join(outputDir, `${baseName}_intro.mp4`)
    const outro = path.join(outputDir, `${baseName}_outro.mp4`)

    log(`📹 [4/9] Giriş görseli oluşturuluyor...`, 'info')
    p(38, 'Giriş görseli oluşturuluyor')
    const introImageUnix = introImage.replace(/\\/g, '/')
    const introUnix = intro.replace(/\\/g, '/')
    cmd = `"${ffmpegExe}" -y -loop 1 -i "${introImageUnix}" -f lavfi -i anullsrc=r=44100:cl=stereo -t ${INTRO_DURATION} -vf "scale=${size}" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -r 25 -c:a aac -y "${introUnix}"`
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Giriş görseli tamam`, 'success')
    p(42, 'Giriş görseli tamamlandı')

    log(`📹 [5/9] Çıkış görseli oluşturuluyor...`, 'info')
    p(44, 'Çıkış görseli oluşturuluyor')
    const outroUnix = outro.replace(/\\/g, '/')
    if (outroImage && fs.existsSync(outroImage)) {
      const outroImageUnix = outroImage.replace(/\\/g, '/')
      cmd = `"${ffmpegExe}" -y -loop 1 -i "${outroImageUnix}" -f lavfi -i anullsrc=r=44100:cl=stereo -t ${OUTRO_DURATION} -vf "scale=${size}" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -r 25 -c:a aac -y "${outroUnix}"`
    } else {
      cmd = `"${ffmpegExe}" -y -loop 1 -i "${introImageUnix}" -f lavfi -i anullsrc=r=44100:cl=stereo -t ${OUTRO_DURATION} -vf "scale=${size}" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -r 25 -c:a aac -y "${outroUnix}"`
    }
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Çıkış görseli tamam`, 'success')
    p(48, 'Çıkış görseli tamamlandı')

    // === 3. Klipleri birleştir ===
    log(`📹 [6/9] Klipler birleştiriliyor...`, 'info')
    p(50, 'Klipler birleştiriliyor')
    const clips = path.join(outputDir, `${baseName}_clips.mp4`)
    const listFile = path.join(outputDir, `${baseName}_list.txt`)
    const clip1Abs = clip1.replace(/\\/g, '/')
    const clip2Abs = clip2.replace(/\\/g, '/')
    const clip3Abs = clip3.replace(/\\/g, '/')
    fs.writeFileSync(listFile, `file '${clip1Abs}'\nfile '${clip2Abs}'\nfile '${clip3Abs}'`)
    const clipsUnix = clips.replace(/\\/g, '/')
    cmd = `"${ffmpegExe}" -y -f concat -safe 0 -i "${listFile}" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${clipsUnix}"`
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Klipler birleştirildi`, 'success')
    p(56, 'Klipler birleştirildi')

    // === 4. Intro ekle ===
    log(`📹 [7/9] Giriş ekleniyor...`, 'info')
    p(58, 'Giriş ekleniyor')
    const withIntro = path.join(outputDir, `${baseName}_ic.mp4`)
    const list1 = path.join(outputDir, `${baseName}_l1.txt`)
    const introAbs = intro.replace(/\\/g, '/')
    const clipsAbs = clips.replace(/\\/g, '/')
    fs.writeFileSync(list1, `file '${introAbs}'\nfile '${clipsAbs}'`)
    const withIntroUnix = withIntro.replace(/\\/g, '/')
    cmd = `"${ffmpegExe}" -y -f concat -safe 0 -i "${list1}" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${withIntroUnix}"`
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Giriş eklendi`, 'success')
    p(62, 'Giriş eklendi')

    // === 5. Outro ekle ===
    log(`📹 [8/9] Çıkış ekleniyor...`, 'info')
    p(64, 'Çıkış ekleniyor')
    const withOutro = path.join(outputDir, `${baseName}_wo.mp4`)
    const list2 = path.join(outputDir, `${baseName}_l2.txt`)
    const withIntroAbs = withIntro.replace(/\\/g, '/')
    const outroAbs = outro.replace(/\\/g, '/')
    fs.writeFileSync(list2, `file '${withIntroAbs}'\nfile '${outroAbs}'`)
    const withOutroUnix = withOutro.replace(/\\/g, '/')
    cmd = `"${ffmpegExe}" -y -f concat -safe 0 -i "${list2}" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${withOutroUnix}"`
    if (!await execFfmpegAsync(cmd, log)) return false
    log(`   ✅ Çıkış eklendi`, 'success')
    p(68, 'Çıkış eklendi')

    // === 6. Müzik ekleme ===
    let finalVideo = withOutro

    if (addMusic) {
      log(`📹 [9/9] Müzik ekleniyor...`, 'info')
      p(70, 'Müzik ekleniyor')
      const mixedVideo = path.join(outputDir, `${baseName}_mixed.mp4`)

      // Müzik seviyeleri: kullanıcının ayarladığı seviye (ön tanımlı %70)
      const highVol = musicVolume / 100  // intro, outro, geçişlerde
      const lowVol = 0.3 * highVol       // normal akışta (~%30 oranında)

      // Zaman noktaları
      const introEnd = INTRO_DURATION
      const trans1Start = INTRO_DURATION + 15  // clip1 fade-out başlangıcı
      const trans1End = INTRO_DURATION + 19    // clip2 fade-in bitişi
      const trans2Start = INTRO_DURATION + 33  // clip2 fade-out başlangıcı
      const trans2End = INTRO_DURATION + 37    // clip3 fade-in bitişi
      const outroStart = INTRO_DURATION + 54   // outro başlangıcı

      let musicPath: string | null = null
      if (musicFile) {
        if (fs.existsSync(musicFile)) {
          musicPath = musicFile
          log(`   🎵 Müzik dosyası bulundu: ${musicPath}`, 'success')
        } else {
          log(`   ❌ Müzik dosyası bulunamadı: ${musicFile}`, 'error')
        }
      } else {
        musicPath = getRandomMusic(baseDir)
        log(`   🎵 Rastgele müzik seçildi: ${musicPath}`, 'info')
      }

      if (musicPath && fs.existsSync(musicPath)) {
        log(`🎵 Müzik: ${path.basename(musicPath)} (yüksek: %${musicVolume}, düşük: %${Math.round(lowVol * 100)})`, 'info')
        // Video sesi SABİT kalır (volume=1, değişmez)
        // Müzik: intro/outro/geçişlerde HIGH, ana içerikte LOW
        const musicVolExpr = `if(lt(t\\,${introEnd})\\,${highVol}\\,if(lt(t\\,${trans1Start})\\,${lowVol}\\,if(lt(t\\,${trans1End})\\,${highVol}\\,if(lt(t\\,${trans2Start})\\,${lowVol}\\,if(lt(t\\,${trans2End})\\,${highVol}\\,if(lt(t\\,${outroStart})\\,${lowVol}\\,${highVol}))))))`
        const musicPathUnix = musicPath.replace(/\\/g, '/')
        const withOutroUnix2 = withOutro.replace(/\\/g, '/')
        const mixedVideoUnix = mixedVideo.replace(/\\/g, '/')
        // Video sesi weight=1 (sabit), müzik volume expression ile kontrol edilir
        cmd = `"${ffmpegExe}" -y -i "${withOutroUnix2}" -i "${musicPathUnix}" -filter_complex "[1:a]volume=${musicVolExpr}:eval=frame[music];[0:a]volume=1.0[va];[va][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]" -map 0:v -map "[aout]" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${mixedVideoUnix}"`
        if (!await execFfmpegAsync(cmd, log)) {
          log(`   ⚠️ Müzik ekleme hatası, müziksüz devam ediliyor...`, 'error')
          p(78, 'Müzik eklenemedi')
        } else {
          finalVideo = mixedVideo
          log(`   ✅ Müzik eklendi`, 'success')
          p(80, 'Müzik eklendi')
        }
      } else {
        log(`   ❌ Müzik dosyası bulunamadı`, 'error')
        p(78, 'Müzik bulunamadı')
      }
    } else {
      p(78, 'Birleştirildi')
    }

    // === 7. Watermark ===
    log(`📹 Watermark ekleniyor...`, 'info')
    p(82, 'Watermark ekleniyor')
    const withWatermark = path.join(outputDir, `${baseName}_wm.mp4`)

    // Watermark son 10 saniyede (48-58) gösterilecek - ÜST KENARA YAKIN
    const fontSize = 'h/34'
    const drawTextFilter = line2
      ? `drawtext=text='${line1}':fontsize=${fontSize}:fontcolor=white:x=(w-text_w)/2:y=30:borderw=2:bordercolor=black:enable='between(t,48,58)',drawtext=text='${line2}':fontsize=${fontSize}:fontcolor=white:x=(w-text_w)/2:y=30+text_h+10:borderw=2:bordercolor=black:enable='between(t,48,58)'`
      : `drawtext=text='${line1}':fontsize=${fontSize}:fontcolor=white:x=(w-text_w)/2:y=30:borderw=2:bordercolor=black:enable='between(t,48,58)'`

    const finalVideoUnix = finalVideo.replace(/\\/g, '/')
    const withWatermarkUnix = withWatermark.replace(/\\/g, '/')
    
    // Yalnızca metin varsa watermark ekle, aksi halde atla
    if (watermarkText && watermarkText.trim() !== "") {
      cmd = `"${ffmpegExe}" -y -i "${finalVideoUnix}" -vf "${drawTextFilter}" -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac -y "${withWatermarkUnix}"`
      if (!await execFfmpegAsync(cmd, log)) {
        log(`   ⚠️ Watermark hatası, mevcut video ile devam ediliyor...`, 'error')
      } else {
        finalVideo = withWatermark
        log(`   ✅ Watermark eklendi`, 'success')
      }
    }
    p(88, 'Watermark tamamlandı')

    // Final videoyu outputPath'e taşı
    if (finalVideo !== outputPath && fs.existsSync(finalVideo)) {
      if (fs.existsSync(outputPath)) {
        try { fs.unlinkSync(outputPath) } catch {}
      }
      fs.copyFileSync(finalVideo, outputPath)
    }

    // === 8. Alt yazı ekle ===
    log(`📹 Alt yazı kontrolü: subtitlePath=${subtitlePath}`, 'info')
    log(`📹 Alt yazı dosyası var mı: ${subtitlePath ? fs.existsSync(subtitlePath) : 'yol yok'}`, 'info')
    log(`📹 Output dosyası var mı: ${fs.existsSync(outputPath)}`, 'info')
    if (subtitlePath && fs.existsSync(subtitlePath) && fs.existsSync(outputPath)) {
      log(`📹 Alt yazı ekleniyor: ${subtitlePath}`, 'info')
      p(90, 'Alt yazı ekleniyor')
      const withSubs = path.join(outputDir, `${baseName}_subs_final.mp4`)
      if (await burnSubtitles(ffmpegExe, outputPath, subtitlePath, withSubs)) {
        fs.unlinkSync(outputPath)
        fs.renameSync(withSubs, outputPath)
        log(`   ✅ Alt yazı eklendi`, 'success')
      } else {
        log(`   ⚠️ Alt yazı eklenemedi - FFmpeg hatası (sunucu konsolunu kontrol edin)`, 'error')
      }
    }

    p(98, 'Tamamlandı')

    // === TEMİZLİK (final video kopyalandıktan SONRA çalıştır) ===
    log(`🧹 Temizlik yapılıyor...`, 'info')

    // Debug: list files in output directory before cleanup
    try {
      const allFiles = fs.readdirSync(outputDir).filter(f => f.startsWith(baseName))
      log(`🧹 Files in output dir (before cleanup): ${allFiles.join(', ')}`, 'info')
    } catch (e) {}

    cleanupTempFiles(outputDir, baseName)

    // Debug: list files after cleanup
    try {
      const remainingFiles = fs.readdirSync(outputDir).filter(f => f.startsWith(baseName))
      log(`🧹 Files in output dir (after cleanup): ${remainingFiles.join(', ')}`, 'info')
    } catch (e) {}

    log(`   ✅ Temizlik tamam`, 'success')

    const finalExists = fs.existsSync(outputPath)
    log(`🧹 outputPath final exists check: ${finalExists}`, 'info')
    return finalExists

  } catch (e: any) {
    log(`   ❌ Error: ${e.message}`, 'error')
    return false
  }
}

export async function POST(request: NextRequest) {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: any) => {
        try {
          const json = JSON.stringify(data)
          controller.enqueue(encoder.encode(`data: ${json}\n\n`))
        } catch (e: any) {
          console.error('Send error:', e?.message)
        }
      }

      const log = (message: string, type: string = 'info') => {
        send({ type: 'log', message, logType: type })
      }

      // Flush initial progress immediately
      send({ type: 'progress', progress: 0, stage: 'Hazırlanıyor...' })

      try {
        const body = await request.json()
        const { projectName, materials, config, outputPath } = body as { projectName: string, materials: Material[], config: Config, outputPath: string }

        if (!outputPath) {
          send({ type: 'error', message: 'Output path is required' })
          controller.close()
          return
        }

        send({ type: 'log', message: '========== SHORTS GENERATOR ==========', logType: 'info' })
        send({ type: 'log', message: `📦 Proje: ${projectName}`, logType: 'info' })
        send({ type: 'log', message: `🔍 Raw material path: ${materials?.[0]?.path}`, logType: 'info' })
        send({ type: 'progress', progress: 1, stage: 'Proje yükleniyor...' })

        const baseDir = 'C:/Users/Damla/Proje/Muhabbet'

        const normalizedOutputPath = path.isAbsolute(outputPath.replace(/\//g, path.sep))
          ? outputPath.replace(/\//g, path.sep)
          : path.join(baseDir, outputPath.replace(/\//g, path.sep))
        const outputDir = path.dirname(normalizedOutputPath)

        const safeProjectName = projectName.replace(/[^a-zA-Z0-9ığüşöçİĞÜŞÖÇ]/g, '_').replace(/_+/g, '_')
        const baseFileName = `shorts_${safeProjectName}`

        if (!fs.existsSync(outputDir)) {
          fs.mkdirSync(outputDir, { recursive: true })
        }
        send({ type: 'progress', progress: 2, stage: 'Klasör hazır' })

        // FFmpeg bul
        send({ type: 'progress', progress: 3, stage: 'FFmpeg kontrolü...' })
        let ffmpegPath = 'ffmpeg'
        const possiblePaths = [
          'C:\\Program Files (x86)\\EaseUS\\RecExperts\\bin\\ffmpeg.exe',
          'C:\\ffmpeg\\bin\\ffmpeg.exe',
          'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        ]
        for (const fp of possiblePaths) {
          if (fs.existsSync(fp)) {
            ffmpegPath = fp
            break
          }
        }
        const ffmpegExe = ffmpegPath

        const videoMaterial = materials?.find((m: Material) => m.type === 'video')
        const imageMaterials = materials?.filter((m: Material) => m.type === 'image')
        const subtitleMaterial = materials?.find((m: Material) => m.type === 'subtitle')
        const guideMaterial = materials?.find((m: Material) => m.type === 'guide')

        // Rehber dosyasını oku ve ayarları uygula
        let guideOptions: GuideOptions = {}
        if (guideMaterial) {
          const guidePath = path.join(baseDir, decodeURIComponent(guideMaterial.path.replace(/\//g, path.sep)))
          if (fs.existsSync(guidePath)) {
            try {
              const guideContent = fs.readFileSync(guidePath, 'utf-8')
              guideOptions = parseGuide(guideContent)
              log(`📋 Rehber ayarları uygulanıyor...`)
              log(`   - clipStrategy: ${guideOptions.clipStrategy || 'varsayılan'}`, 'info')
              log(`   - transitions: ${guideOptions.transitions ?? true}`, 'info')
              log(`   - watermarkText: ${guideOptions.watermarkText || 'varsayılan'}`, 'info')
              log(`   - addMusic: ${guideOptions.addMusic ?? false}`, 'info')
            } catch (e: any) {
              log(`   ⚠️ Rehber okunamadı: ${e.message}`, 'error')
            }
          }
        }

        if (!videoMaterial) {
          send({ type: 'error', message: 'Video file is required' })
          controller.close()
          return
        }
        send({ type: 'progress', progress: 5, stage: 'Video dosyası kontrol ediliyor...' })

        const videoPath = path.join(baseDir, decodeURIComponent(videoMaterial.path).replace(/\//g, path.sep))

        let subtitlePath: string | null = null
        if (subtitleMaterial) {
          subtitlePath = path.join(baseDir, decodeURIComponent(subtitleMaterial.path.replace(/\//g, path.sep)))
        } else {
          const autoSrtPath = path.join(outputDir, `${baseFileName}_subs.srt`)
          log(`🎙️ Otomatik altyazı oluşturuluyor (Whisper)...`, 'info')
          send({ type: 'progress', progress: 6, stage: 'Altyazı oluşturuluyor (Whisper)...' })
          const whisperOk = await generateSubtitlesFromVideo(videoPath, autoSrtPath, log, ffmpegExe)
          if (whisperOk) {
            subtitlePath = autoSrtPath
          } else {
            log(`   ⚠️ Whisper transkripsiyon başarısız, altyazısız devam ediliyor`, 'error')
            subtitlePath = null
          }
        }

        const sizes: Record<string, string> = {
          '9:16': '1080:1920',
          '16:9': '1920:1080',
          '1:1': '1080:1080'
        }
        const size = sizes[config?.format || '9:16']

        log(`🔍 videoPath check: ${videoPath}`, 'info')
        log(`🔍 videoPath exists: ${fs.existsSync(videoPath)}`, 'info')
        log(`🔍 Path buffer hex: ${Buffer.from(videoPath).toString('hex')}`, 'info')

        if (!fs.existsSync(videoPath)) {
          send({ type: 'error', message: `Video file not found: ${videoPath}` })
          controller.close()
          return
        }

        const introImage = imageMaterials && imageMaterials.length > 0
          ? path.join(baseDir, decodeURIComponent(imageMaterials[0].path.replace(/\//g, path.sep)))
          : null
        const outroImage = imageMaterials && imageMaterials.length > 1
          ? path.join(baseDir, decodeURIComponent(imageMaterials[1].path.replace(/\//g, path.sep)))
          : introImage

        if (!introImage || !fs.existsSync(introImage)) {
          send({ type: 'error', message: 'Intro image is required' })
          controller.close()
          return
        }

        const watermarkText = guideOptions.watermarkText || config.watermarkText || "Daha fazlası için,.youtube.com/@ArdaAvc"
        const addMusic = guideOptions.addMusic ?? config.addMusic ?? false
        const musicVolume = guideOptions.musicVolume || config.musicVolume || 70
        const selectedMusicFile = guideOptions.musicFile || config.musicFile || null

        log(`📹 Kaynak: ${videoMaterial.name}`)
        log(`🖼️ Intro: ${path.basename(introImage)}`)
        log(`📝 Watermark: ${watermarkText}`)
        log(`🎵 Müzik: ${addMusic ? 'Evet' : 'Hayır'}`)

        send({ type: 'progress', progress: 8, stage: 'Video bölümleri hesaplanıyor...' })

        // Video süresini al
        let totalVideoDuration = 300
        try {
          const probeResult = execSync(`"${ffmpegExe}" -i "${videoPath}" 2>&1`, { encoding: 'utf-8', shell: 'cmd' })
          const durationMatch = probeResult.match(/Duration: (\d+):(\d+):(\d+)/)
          if (durationMatch) {
            totalVideoDuration = parseInt(durationMatch[1]) * 3600 + parseInt(durationMatch[2]) * 60 + parseInt(durationMatch[3])
          }
        } catch (e) {
          log('Video süresi alınamadı, 5 dakika varsayılıyor')
        }
        log(`📊 Kaynak süre: ${totalVideoDuration}s`)

        const createdFiles: string[] = []
        const startNum = findNextFileNumber(outputDir, baseFileName)

        // 3 video oluştur
        for (let v = 0; v < 3; v++) {
          const videoNum = v + 1
          // Her video %33'lük dilime sahip: Video1=1-33, Video2=34-66, Video3=67-99
          const sliceStart = Math.round(v * 33) + 1
          const sliceSize = 33
          send({ type: 'progress', progress: sliceStart, stage: `Video ${videoNum}/3 başlıyor...` })
          log(`\n========== Video ${videoNum}/3 ==========`)
          const fileName = `${baseFileName}_${startNum + v}.mp4`
          const filePath = path.join(outputDir, fileName)

          const segmentSize = (totalVideoDuration - 60) / 4
          const baseStart = v * segmentSize

          const clip1Start = Math.floor(baseStart)
          const clip2Start = Math.floor(baseStart + segmentSize)
          const clip3Start = Math.floor(baseStart + segmentSize * 2)

          // Progress callback - 0-100 relative progress -> sliceStart..sliceStart+sliceSize overall
          const videoSend = (data: any) => {
            if (data.type === 'progress') {
              const stageMsg = data.stage || ''
              const overallProgress = Math.min(99, sliceStart + Math.round((data.progress / 100) * sliceSize))
              send({ type: 'progress', progress: overallProgress, stage: stageMsg })
            } else {
              send(data)
            }
          }

          const success = await createShortsVideo(
            ffmpegExe, videoPath, filePath, baseDir,
            clip1Start, clip2Start, clip3Start,
            introImage, outroImage, size,
            subtitlePath, watermarkText,
            addMusic, musicVolume, selectedMusicFile,
            log, videoSend, guideOptions, videoNum
          )

          const currentProgress = Math.round(((v + 1) / 3) * 100)
          send({ type: 'progress', progress: currentProgress, stage: `Video ${v + 1}/3 tamamlandı` })

          if (success && fs.existsSync(filePath)) {
            const stats = fs.statSync(filePath)
            log(`✅ ${fileName} (${(stats.size / 1024 / 1024).toFixed(2)} MB)`)
            createdFiles.push(fileName)
            send({ type: 'file', fileName, filePath: path.join(outputDir, fileName).replace(/\\/g, '/') })
          } else {
            log(`❌ Başarısız: ${fileName}`)
          }
        }

        // Son temizlik - sadece .srt dosyaları
        try {
          fs.readdirSync(outputDir).forEach(f => {
            if (f.endsWith('.srt') && f.startsWith(baseFileName)) {
              try { fs.unlinkSync(path.join(outputDir, f)) } catch {}
            }
          })
        } catch (e) {}

        log('\n========== SONUÇ ==========')
        log(`✅ ${createdFiles.length} video oluşturuldu`)

        send({ type: 'progress', progress: 100, stage: 'Tamamlandı!' })
        send({ type: 'complete', status: 'success', outputFiles: createdFiles.map(f => ({ fileName: f, filePath: path.join(outputDir, f).replace(/\\/g, '/') })) })

      } catch (error: any) {
        log(`❌ ERROR: ${error.message}`)
        send({ type: 'error', status: 'error', message: error.message })
      }

      controller.close()
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}