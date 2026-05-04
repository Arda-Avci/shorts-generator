# 🎬 Shorts Generator

YouTube Shorts otomatik oluşturucu — **Arda Avcı** Kanalı için tasarlanmıştır.

> Kaynak videodan 3 adet kısa video (shorts) üretir. Intro/outro görselleri, arka plan müziği, watermark ve **otomatik Türkçe altyazı** (Whisper AI) desteği sunar.

---

## ⚡ Hızlı Başlangıç

```bash
cd shorts-generator
npm install
npm run dev
```

Tarayıcıda `http://localhost:3000` adresine gidin.

---

## 📋 Gereksinimler

| Bileşen | Versiyon | Açıklama |
|---------|----------|----------|
| **Node.js** | 18+ | Next.js çalıştırma ortamı |
| **FFmpeg** | 4.x+ | Video/ses işleme motoru |
| **Python** | 3.10+ | Whisper transkripsiyon için |
| **openai-whisper** | Son sürüm | Otomatik altyazı (STT) |
| **PyTorch** | 2.x+ | Whisper bağımlılığı |

---

## 🔧 Kurulum Adımları

### 1. Node.js Bağımlılıkları

```bash
npm install
```

### 2. FFmpeg Kurulumu

**Windows:**
```bash
winget install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 3. Python + Whisper (Otomatik Altyazı)

```bash
pip install openai-whisper
```

> **Not:** PyTorch otomatik olarak kurulur. CUDA destekli GPU varsa daha hızlı çalışır.
> GPU sürümü için: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

### 4. Ortam Değişkenleri (Opsiyonel)

AI video üretimi (CogVideo/MiniMax) için `.env.local` dosyası oluşturun:

```bash
cp .env.example .env.local
```

---

## 🎯 Kullanım

1. **Proje Seçimi** — Shorts oluşturmak istediğiniz projeyi seçin
2. **Materyal Seçimi** — Video, görseller ve isteğe bağlı rehber/altyazı dosyası seçin
3. **Ayarlar** — Format (9:16, 16:9, 1:1), müzik, watermark ayarlayın
4. **Oluştur** — Video üretimini başlatın ve ilerlemeyi takip edin

### 📺 Üretim Akışı

```
Kaynak Video → 3 Clip Kesimi → Intro/Outro Ekleme → Klip Birleştirme
    → Müzik Miksajı → Watermark → Whisper Altyazı → Final Video (x3)
```

### 🎙️ Otomatik Altyazı (Whisper)

Materyal olarak `.srt` dosyası eklenmezse, **Whisper AI** otomatik olarak videodan Türkçe altyazı oluşturur:

- Model: `base` (hız/kalite dengesi)
- Dil: Türkçe (`tr`)
- Çıktı: SRT formatı
- Konum: Videonun alt kısmı

> Manuel altyazı kullanmak için `.srt` dosyanızı materyal olarak ekleyin.

### 🎵 Müzik Seviyeleri

| Bölüm | Müzik Seviyesi |
|-------|---------------|
| Intro/Outro | Kullanıcı ayarı (ön tanımlı %70) |
| Geçişler (fade) | Kullanıcı ayarı (ön tanımlı %70) |
| Ana içerik | ~%30 × kullanıcı ayarı |

> Video orijinal sesi **sabit** kalır, dalgalanma olmaz.

---

## 📁 Proje Yapısı

```
shorts-generator/
├── app/
│   ├── page.tsx                 # Ana sayfa
│   ├── layout.tsx               # Layout
│   └── api/
│       ├── generate/route.ts    # Video oluşturma API (SSE)
│       ├── scan/route.ts        # Proje/materyal tarama
│       ├── open-folder/route.ts # Klasör açma (Explorer)
│       └── music/route.ts       # Müzik dosyaları API
├── components/
│   ├── ProjectSelector.tsx      # Proje seçim ekranı
│   ├── MaterialSelector.tsx     # Materyal seçim ekranı
│   ├── PreviewPanel.tsx         # Önizleme paneli
│   └── GenerationPanel.tsx      # Üretim & ilerleme paneli
├── scripts/
│   ├── transcribe.py            # Whisper altyazı scripti
│   ├── generate_shorts.py       # Python CLI (alternatif)
│   └── cogvideo_inference.py    # CogVideo AI üretim
├── bg-music/                    # Arka plan müzik dosyaları
└── bg-music-generator*.py       # Müzik sentezleme scriptleri
```

---

## 🛠️ Komutlar

| Komut | Açıklama |
|-------|----------|
| `npm run dev` | Geliştirme sunucusu (port 3000) |
| `npm run build` | Production build |
| `npm run start` | Production sunucu |
| `python scripts/transcribe.py <video> <output.srt> [model]` | Manuel transkripsiyon |

### Whisper Model Boyutları

| Model | Boyut | Hız | Kalite |
|-------|-------|-----|--------|
| `tiny` | 39 MB | ⚡⚡⚡ | ★★ |
| `base` | 74 MB | ⚡⚡ | ★★★ |
| `small` | 244 MB | ⚡ | ★★★★ |
| `medium` | 769 MB | 🐢 | ★★★★★ |
| `large` | 1550 MB | 🐌 | ★★★★★ |

> Varsayılan: `base` — hız ve kalite arasında iyi bir denge sağlar.

---

## 📝 Rehber Dosyası (Opsiyonel)

Proje klasörüne `shorts_rehber_*.md` dosyası ekleyerek üretimi özelleştirebilirsiniz:

```markdown
clipStrategy: sequential
addMusic: true
musicVolume: 70
watermarkText: Daha fazlası için,.youtube.com/@ArdaAvc
introDuration: 2
outroDuration: 2
```