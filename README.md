# Shorts Generator

YouTube Shorts otomatik oluşturucu - Arda Avcı Kanalı

## Kurulum

```bash
cd shorts-generator
npm install
npm run dev
```

Tarayıcıda `http://localhost:3000` adresine gidin.

## Gereksinimler

- Node.js 18+
- FFmpeg (video işleme için)

## FFmpeg Kurulumu

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

## Kullanım

1. **Proje Seçimi** - Shorts oluşturmak istediğiniz projeyi seçin
2. **Materyal Seçimi** - Kullanılacak script ve görselleri seçin
3. **Ayarlar** - Süre, format (9:16, 16:9, 1:1), stil ve ses tonunu ayarlayın
4. **Oluştur** - Video üretimini başlatın

## Video Stilleri

- **Gizemli/Otoriter** - Tok erkek sesi, karanlık tonlar
- **Enerjik** - Hızlı geçişler, canlı renkler
- **Sakin** - Yumuşak geçişler, soft tonlar
- **Karanlık** - Gerilimli atmosfer, mavi tonları

## Komut Satırı Kullanımı

Python scripti ile doğrudan üretim:

```bash
python scripts/generate_shorts.py \
  --project "Yapay Zeka Ortak Yaşamı" \
  --script "shorts_final_selection.md" \
  --image "shorts_zihin_klonlama_bg.png" \
  --output "output/shorts_123.mp4" \
  --duration 60 \
  --style mysterious \
  --format 9:16
```

## Proje Yapısı

```
shorts-generator/
├── app/
│   ├── page.tsx           # Ana sayfa
│   ├── layout.tsx         # Layout
│   └── api/
│       └── generate/
│           └── route.ts   # Video oluşturma API
├── components/
│   ├── ProjectSelector.tsx
│   ├── MaterialSelector.tsx
│   ├── PreviewPanel.tsx
│   └── GenerationPanel.tsx
└── scripts/
    └── generate_shorts.py # Python CLI
```