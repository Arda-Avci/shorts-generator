import numpy as np
from scipy.io import wavfile
import os

SAMPLE_RATE = 44100
OUTPUT_DIR = r"C:\users\Damla\Proje\Muhabbet\shorts-generator\bg-music"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_as_mp3(data, filename, bitrate=320):
    wav_path = os.path.join(OUTPUT_DIR, filename.replace('.mp3', '.wav'))
    mp3_path = os.path.join(OUTPUT_DIR, filename)
    data = np.tanh(data * 0.85 / 0.9) * 0.9
    data = np.int16(data * 32767)
    wavfile.write(wav_path, SAMPLE_RATE, data)
    os.system('ffmpeg -y -i "{0}" -b:a {1}k -ar 44100 "{2}"'.format(wav_path, bitrate, mp3_path))
    os.remove(wav_path)
    print("[+] " + filename)

def create_envelope(length, attack=0.005, decay=0.1, sustain=0.7, release=0.2, sr=SAMPLE_RATE):
    length = int(length)
    if length <= 0: return np.ones(1)
    a = min(int(attack * sr), length // 4)
    d = min(int(decay * sr), length // 4)
    r = min(int(release * sr), length // 4)
    s = max(0, length - a - d - r)
    env = np.zeros(length)
    idx = 0
    if a > 0: env[idx:idx+a] = np.linspace(0, 1, a); idx += a
    if s > 0: env[idx:idx+s] = sustain; idx += s
    if d > 0 and idx < length: env[idx:idx+min(d, length-idx)] = np.linspace(1, sustain, min(d, length-idx)); idx += min(d, length-idx)
    if r > 0 and idx < length: env[idx:idx+min(r, length-idx)] = np.linspace(sustain, 0, min(r, length-idx))
    return env if idx > 0 else np.ones(length)

def noise_burst(duration, decay=20, sr=SAMPLE_RATE):
    n = int(sr * duration)
    noise = np.random.randn(n)
    env = np.exp(-np.arange(n) / sr * decay)
    return noise * env

def synth_kick_oriental(duration=0.4, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    pitch_curve = np.linspace(150, 45, n)
    phase = np.cumsum(2 * np.pi * pitch_curve / sr)
    body = np.sin(phase) + np.sin(phase * 0.5) * 0.4
    env = create_envelope(n, 0.001, 0.12, 0.3, 0.15, sr)
    sub = np.sin(2 * np.pi * 45 * t) * create_envelope(n, 0.001, 0.15, 0.4, 0.2, sr)
    return (body * env + sub * 0.35) * 0.9

def synth_oud(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))
    vibrato = 1 + np.sin(2 * np.pi * 4 * t) * 0.02
    phase = np.cumsum(2 * np.pi * freq * vibrato / sr) / (2 * np.pi)
    audio = np.sin(phase * 2 * np.pi) * 0.4
    audio += saw * 0.3
    env = create_envelope(n, 0.02, 0.2, 0.6, 0.4, sr)
    return audio * env * 0.4

def synth_pad_oriental(freqs, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.zeros(n)
    for f in freqs:
        audio += np.sin(2 * np.pi * f * t) * 0.15
        audio += np.sin(2 * np.pi * f * 2 * t) * 0.08
    env = create_envelope(n, 0.4, 0.2, 0.7, 0.5, sr)
    mod = 1 + np.sin(2 * np.pi * 0.25 * t) * 0.08
    return audio * mod * env * 0.3

def synth_darbuka(dur=0.1, sr=SAMPLE_RATE):
    n = int(sr * dur)
    t = np.arange(n) / sr
    tone = np.sin(2 * np.pi * 200 * t) * 0.5 + np.sin(2 * np.pi * 400 * t) * 0.3
    noise = noise_burst(dur, 50, sr) * 0.4
    env = create_envelope(n, 0.001, 0.03, 0.2, 0.05, sr)
    return (tone + noise) * env * 0.6

def create_oriental_synth():
    bpm = 105
    duration = 64
    bar_dur = 60 / bpm * 4
    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    for t in np.arange(0, duration, beat_dur):
        start = int(t * SAMPLE_RATE)
        if start < samples:
            k = synth_kick_oriental()
            audio[start:start+len(k)] += k

    # Darbuka pattern (oriental rhythm)
    for bar in range(int(duration / (bar_dur / 4))):
        bar_start = bar * (bar_dur / 4)
        patterns = [
            (0, 0.3), (0.5, 0.2), (1.5, 0.25), (2, 0.35), (2.5, 0.2), (3.5, 0.25)
        ]
        for offset, vel in patterns:
            t = bar_start + offset * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                dbk = synth_darbuka(0.15)
                audio[start:start+len(dbk)] += dbk * vel

    # Arabic scale notes (Basmala scale)
    oud_notes = [220, 247, 277, 294, 330, 370, 440, 494]
    for bar in range(int(duration / (bar_dur * 2))):
        for i, note in enumerate(oud_notes[:4]):
            t = bar * bar_dur * 2 + i * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                oud = synth_oud(note, beat_dur * 0.7)
                audio[start:start+len(oud)] += oud

    # Mystical pads
    pad_chords = [[220, 277, 330], [247, 294, 370], [220, 294, 330], [185, 247, 294]]
    for section in range(int(duration / 16)):
        chord = pad_chords[section % len(pad_chords)]
        start = int(section * 16 * SAMPLE_RATE)
        pad = synth_pad_oriental(chord, 15.5)
        if start + len(pad) <= samples: audio[start:start+len(pad)] += pad

    peak = np.max(np.abs(audio))
    if peak > 0: audio = audio / peak * 0.9

    return audio

audio = create_oriental_synth()
save_as_mp3(audio, "bg_oriental_synth.mp3")