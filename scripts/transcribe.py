#!/usr/bin/env python3
"""
Whisper ile videodan otomatik altyazı (SRT) oluşturma scripti.
Kullanım: python transcribe.py <video_path> <output_srt_path> [model_size] [ffmpeg_path]
Model boyutları: tiny, base, small, medium, large
Varsayılan: base (hızlı ve yeterli kalite)
"""

import sys
import os
import tempfile
import subprocess

def find_ffmpeg(hint_path: str = "") -> str:
    """FFmpeg yolunu bul."""
    # Parametre ile verildiyse
    if hint_path and os.path.exists(hint_path):
        return hint_path

    # Bilinen konumlar
    candidates = [
        r"C:\Program Files (x86)\EaseUS\RecExperts\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p

    return "ffmpeg"  # PATH'te olması umut edilir

def extract_audio(video_path: str, audio_path: str, ffmpeg_exe: str) -> bool:
    """Videodan ses çıkar (WAV formatında)."""
    cmd = [ffmpeg_exe, "-y", "-i", video_path,
           "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
           audio_path]
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        return True
    except FileNotFoundError:
        print(f"HATA: FFmpeg bulunamadı: {ffmpeg_exe}", file=sys.stderr)
        # shell=True ile dene
        try:
            shell_cmd = f'"{ffmpeg_exe}" -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}"'
            subprocess.run(shell_cmd, shell=True, capture_output=True, check=True)
            return True
        except Exception as e2:
            print(f"Shell denemesi de başarısız: {e2}", file=sys.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg ses çıkarma hatası: {e.stderr.decode()[-300:]}", file=sys.stderr)
        return False

def format_timestamp(seconds: float) -> str:
    """Saniyeyi SRT zaman formatına çevir: HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def transcribe_to_srt(video_path: str, output_srt: str, model_size: str = "base", ffmpeg_hint: str = ""):
    """Video dosyasından Whisper ile altyazı oluştur."""
    import whisper

    ffmpeg_exe = find_ffmpeg(ffmpeg_hint)
    print(f"FFmpeg yolu: {ffmpeg_exe}")

    # FFmpeg'in bulunduğu dizini PATH'e ekle (Whisper da ffmpeg kullanıyor)
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    if ffmpeg_dir and ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        print(f"PATH'e eklendi: {ffmpeg_dir}")

    # Geçici ses dosyası oluştur
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name

    try:
        print(f"[1/3] Ses çıkarılıyor: {os.path.basename(video_path)}")
        if not extract_audio(video_path, audio_path, ffmpeg_exe):
            print("HATA: Ses çıkarılamadı!", file=sys.stderr)
            sys.exit(1)

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            print("HATA: Ses dosyası boş!", file=sys.stderr)
            sys.exit(1)

        print(f"[2/3] Whisper modeli yükleniyor: {model_size}")
        model = whisper.load_model(model_size)

        print("[3/3] Transkripsiyon yapılıyor...")
        result = model.transcribe(
            audio_path,
            language="tr",
            task="transcribe",
            verbose=False
        )

        # SRT formatında yaz
        srt_content = ""
        for i, segment in enumerate(result["segments"], 1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"

        with open(output_srt, "w", encoding="utf-8") as f:
            f.write(srt_content)

        segment_count = len(result["segments"])
        print(f"Tamamlandi! {segment_count} altyazi segmenti olusturuldu: {output_srt}")

    finally:
        # Geçici dosyayı temizle
        if os.path.exists(audio_path):
            os.unlink(audio_path)

if __name__ == "__main__":
    # Windows'ta UTF-8 desteği için
    if os.name == 'nt':
        import locale
        # stdout/stderr için utf-8 zorla
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    if len(sys.argv) < 3:
        print("Kullanim: python transcribe.py <video_path> <output_srt_path> [model_size] [ffmpeg_path]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_srt = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "base"
    ffmpeg_hint = sys.argv[4] if len(sys.argv) > 4 else ""

    print(f"DEBUG: Python Encoding: {sys.getfilesystemencoding()}")
    print(f"DEBUG: Video Path: {video_path}")

    if not os.path.exists(video_path):
        print(f"HATA: Video dosyasi bulunamadi: {video_path}", file=sys.stderr)
        # Mevcut klasördeki dosyaları listele (debug için)
        try:
            dir_name = os.path.dirname(os.path.abspath(video_path))
            print(f"Klasör içeriği ({dir_name}): {os.listdir(dir_name)}", file=sys.stderr)
        except:
            pass
        sys.exit(1)

    transcribe_to_srt(video_path, output_srt, model_size, ffmpeg_hint)
