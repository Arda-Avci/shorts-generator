import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Shorts Generator - Arda Avcı',
  description: 'YouTube Shorts otomatik oluşturucu',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body style={{ margin: 0, fontFamily: 'system-ui, sans-serif', background: '#0a0a0a', color: '#fff' }}>
        {children}
      </body>
    </html>
  )
}