'use client'

import { useState } from 'react'

interface HelpPanelProps {
  onDismiss: () => void
}

export default function HelpPanel({ onDismiss }: HelpPanelProps) {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}
    onClick={onDismiss}
    >
      <div style={{
        background: '#1a1a1a',
        borderRadius: '16px',
        padding: '30px',
        maxWidth: '700px',
        maxHeight: '80vh',
        overflow: 'auto',
        border: '1px solid #333'
      }}
      onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ color: '#00d4ff', margin: 0 }}>📖 Nasıl Kullanılır?</h2>
          <button
            onClick={onDismiss}
            style={{
              background: 'transparent',
              border: '1px solid #666',
              color: '#fff',
              padding: '8px 16px',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            ✕ Kapat
          </button>
        </div>

        <div style={{ color: '#ccc', lineHeight: 1.6 }}>
          <h3 style={{ color: '#ff00ff', marginTop: '20px' }}>1. Adım: Proje Seçimi</h3>
          <p>Sol taraftan bir proje klasörü seçin veya &quot;Özel Klasör&quot; bölümüne klasör yolunu yazın.</p>
          <ul style={{ color: '#888', marginLeft: '20px' }}>
            <li>Proje klasörü <code style={{ background: '#2a2a2a', padding: '2px 6px', borderRadius: '4px' }}>Gorseller</code>, <code style={{ background: '#2a2a2a', padding: '2px 6px', borderRadius: '4px' }}>Senaryolar</code> veya <code style={{ background: '#2a2a2a', padding: '2px 6px', borderRadius: '4px' }}>Scripts</code> alt klasörlerinden birini içermelidir</li>
          </ul>

          <h3 style={{ color: '#ff00ff', marginTop: '20px' }}>2. Adım: Materyaller</h3>
          <p>Projenize uygun materyalleri seçin:</p>

          <div style={{ background: '#2a2a2a', padding: '15px', borderRadius: '8px', margin: '10px 0' }}>
            <h4 style={{ color: '#00d4ff', margin: '0 0 10px 0' }}>📹 Video (ZORUNLU)</h4>
            <p style={{ margin: 0, color: '#888' }}>Ana video kaynağı. MP4, MOV, AVI veya WebM formatlarında olabilir.</p>
            <p style={{ margin: '5px 0 0 0', color: '#ff4444', fontSize: '0.9rem' }}>⚠️ Seçilmezse video oluşturulamaz</p>
          </div>

          <div style={{ background: '#2a2a2a', padding: '15px', borderRadius: '8px', margin: '10px 0' }}>
            <h4 style={{ color: '#00d4ff', margin: '0 0 10px 0' }}>🖼️ Görseller (ZORUNLU)</h4>
            <p style={{ margin: 0, color: '#888' }}>İlk görsel = Giriş (intro), İkinci görsel = Çıkış (outro)</p>
            <p style={{ margin: '5px 0 0 0', color: '#888', fontSize: '0.9rem' }}>PNG, JPG veya WebP formatlarında olabilir.</p>
            <p style={{ margin: '5px 0 0 0', color: '#ff4444', fontSize: '0.9rem' }}>⚠️ Seçilmezse video oluşturulamaz</p>
          </div>

          <div style={{ background: '#2a2a2a', padding: '15px', borderRadius: '8px', margin: '10px 0' }}>
            <h4 style={{ color: '#00d4ff', margin: '0 0 10px 0' }}>📝 Alt Yazı (OPSİYONEL)</h4>
            <p style={{ margin: 0, color: '#888' }}>SRT, VTT veya ASS formatında alt yazı dosyası seçilebilir.</p>
            <p style={{ margin: '5px 0 0 0', color: '#888', fontSize: '0.9rem' }}>Seçilmezse video içinden otomatik oluşturulur (placeholder)</p>
          </div>

          <div style={{ background: '#2a2a2a', padding: '15px', borderRadius: '8px', margin: '10px 0' }}>
            <h4 style={{ color: '#00d4ff', margin: '0 0 10px 0' }}>📋 Rehber/Guide (OPSİYONEL)</h4>
            <p style={{ margin: 0, color: '#888' }}>İsminde &quot;rehber&quot; veya &quot;guide&quot; geçen dosyalar otomatik olarak işlem talimatları olarak algılanır.</p>
            <p style={{ margin: '5px 0 0 0', color: '#888', fontSize: '0.9rem' }}>İçeriği doğrudan kullanılmaz, sadece işlemlerin nasıl yapılacağını belirler.</p>
          </div>

          <h3 style={{ color: '#ff00ff', marginTop: '20px' }}>3. Adım: Önizleme</h3>
          <p>Seçilen materyalleri ve konfigürasyonu kontrol edin.</p>

          <h3 style={{ color: '#ff00ff', marginTop: '20px' }}>4. Adım: Oluşturma</h3>
          <p>&quot;Oluşturmaya Başla&quot; butonuna tıklayarak 3 adet 60 saniyelik Shorts videosu oluşturulur.</p>
          <ul style={{ color: '#888', marginLeft: '20px' }}>
            <li>Her video 2s giriş + 18s kesit1 + 1s geçiş + 18s kesit2 + 1s geçiş + 18s kesit3 + 2s çıkış = 60s</li>
            <li>Son 10 saniyede YouTube kanal linki görünür</li>
            <li>Videolar proje klasörünün <code style={{ background: '#2a2a2a', padding: '2px 6px', borderRadius: '4px' }}>output</code> alt klasörüne kaydedilir</li>
          </ul>

          <h3 style={{ color: '#ff00ff', marginTop: '20px' }}>Dosya Bağımlılıkları</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', color: '#888' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #333' }}>
                <th style={{ textAlign: 'left', padding: '8px 0' }}>Dosya Türü</th>
                <th style={{ textAlign: 'left', padding: '8px 0' }}>Konum</th>
                <th style={{ textAlign: 'left', padding: '8px 0' }}>Zorunlu?</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid #222' }}>
                <td style={{ padding: '8px 0' }}>Video</td>
                <td style={{ padding: '8px 0' }}>Proje klasörü veya alt klasörler</td>
                <td style={{ color: '#ff4444' }}>Evet</td>
              </tr>
              <tr style={{ borderBottom: '1px solid #222' }}>
                <td style={{ padding: '8px 0' }}>Görseller</td>
                <td style={{ padding: '8px 0' }}>Gorseller klasörü</td>
                <td style={{ color: '#ff4444' }}>Evet</td>
              </tr>
              <tr style={{ borderBottom: '1px solid #222' }}>
                <td style={{ padding: '8px 0' }}>Alt Yazı</td>
                <td style={{ padding: '8px 0' }}>Herhangi bir konum</td>
                <td style={{ color: '#00ff88' }}>Hayır</td>
              </tr>
              <tr>
                <td style={{ padding: '8px 0' }}>Rehber</td>
                <td style={{ padding: '8px 0' }}>Senaryolar/Scripts</td>
                <td style={{ color: '#00ff88' }}>Hayır</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
