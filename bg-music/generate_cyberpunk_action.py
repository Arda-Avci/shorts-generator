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

def synth_808(duration=0.8, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    pitch_curve = 38 * (1 + 0.4 * np.exp(-t * 10))
    phase = np.cumsum(2 * np.pi * pitch_curve / sr)
    sine = np.sin(phase)
    sine2 = np.sin(phase * 2)
    sine05 = np.sin(phase * 0.5)
    audio = sine * 0.5 + sine2 * 0.3 + sine05 * 0.2
    env = create_envelope(n, 0.001, 0.3, 0.4, 0.3, sr)
    return np.tanh(audio * env * 0.7)

def synth_snare_cyber(sr=SAMPLE_RATE):
    n = int(sr * 0.2)
    noise = noise_burst(0.2, 25, sr) * 0.5
    tone = np.sin(2 * np.pi * 210 * np.arange(n) / sr) * 0.4
    snap = np.sin(2 * np.pi * 800 * np.arange(n) / sr) * np.exp(-np.arange(n) / sr * 100) * 0.2
    env = create_envelope(n, 0.001, 0.05, 0.2, 0.08, sr)
    return (noise + tone + snap) * env

def synth_bass_cyber(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))
    square = np.sign(np.sin(2 * np.pi * freq * t))
    audio = saw * 0.5 + square * 0.3
    env = create_envelope(n, 0.01, 0.1, 0.6, 0.3, sr)
    return np.tanh(audio * env * 0.5)

def synth_stab(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))
    env = create_envelope(n, 0.001, 0.05, 0.3, 0.05, sr)
    return saw * env * 0.4

def synth_pad_cyber(freqs, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.zeros(n)
    for f in freqs:
        audio += np.sin(2 * np.pi * f * t) * 0.1
        audio += np.sin(2 * np.pi * f * 3 * t) * 0.05
    env = create_envelope(n, 0.3, 0.2, 0.7, 0.5, sr)
    return audio * env * 0.35

def create_cyberpunk_action():
    bpm = 140
    duration = 58
    bar_dur = 60 / bpm * 4
    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    for bar in range(int(duration / bar_dur)):
        for beat in [0, 1, 2, 3]:
            t = bar * bar_dur + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                k = synth_808()
                audio[start:start+len(k)] += k

    for bar in range(int(duration / (bar_dur * 2))):
        for beat in [1, 3]:
            t = bar * bar_dur * 2 + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                s = synth_snare_cyber()
                audio[start:start+len(s)] += s

    bass_notes = [36, 0, 41, 38, 36, 43, 41, 38]
    for bar in range(int(duration / (bar_dur * 2))):
        for i, note in enumerate(bass_notes):
            if note > 0:
                t = bar * bar_dur * 2 + i * beat_dur
                start = int(t * SAMPLE_RATE)
                if start < samples:
                    bass = synth_bass_cyber(note, beat_dur * 0.85)
                    audio[start:start+len(bass)] += bass

    stab_times = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]
    for bar in range(int(duration / (bar_dur * 4))):
        for offset in stab_times:
            t = bar * bar_dur * 4 + offset * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                stab = synth_stab(311, 0.15)
                audio[start:start+len(stab)] += stab * 0.3

    dark_chords = [[155.56, 185.00, 232.00], [138.59, 174.61, 207.65], [146.83, 174.61, 220.00]]
    for section in range(int(duration / 8)):
        chord = dark_chords[section % len(dark_chords)]
        start = int(section * 8 * SAMPLE_RATE)
        pad = synth_pad_cyber(chord, 7.5)
        if start + len(pad) <= samples: audio[start:start+len(pad)] += pad

    peak = np.max(np.abs(audio))
    if peak > 0: audio = audio / peak * 0.9

    return audio

audio = create_cyberpunk_action()
save_as_mp3(audio, "bg_cyberpunk_action.mp3")