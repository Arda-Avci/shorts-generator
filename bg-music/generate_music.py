import numpy as np
from scipy.io import wavfile
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, filtfilt
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

def apply_lpf(audio, cutoff=3000, sr=SAMPLE_RATE):
    b, a = butter(4, cutoff / (sr / 2), btype='low')
    return filtfilt(b, a, audio)

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

def synth_kick(duration=0.5, pitch_start=180, pitch_end=35, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    pitch_curve = np.linspace(pitch_start, pitch_end, n)
    phase = np.cumsum(2 * np.pi * pitch_curve / sr)
    body = np.sin(phase) + np.sin(phase * 0.5) * 0.4 + np.sin(phase * 2) * 0.15
    click = np.random.randn(int(sr * 0.003)) * 0.3 * np.exp(-np.arange(int(sr * 0.003)) / (sr * 0.001))
    click = np.pad(click, (0, n - len(click)))
    amp = create_envelope(n, 0.001, 0.08, 0.3, 0.15, sr)
    audio = (body * amp + click) * 0.95
    return apply_lpf(audio, 150)

def synth_pad(freqs, duration, detune=0.003, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.zeros(n)
    for f in freqs:
        for dt in [-detune*2, -detune, 0, detune, detune*2]:
            audio += np.sin(2 * np.pi * f * (1 + dt) * t) * 0.05
    env = create_envelope(n, 0.5, 0.2, 0.7, 0.6, sr)
    mod = 1 + np.sin(2 * np.pi * 0.3 * t) * 0.1
    for delay in [0.023, 0.037, 0.047]:
        delayed = np.zeros_like(audio)
        d = int(delay * sr)
        if d < n: delayed[d:] = audio[:-d] * 0.2
        audio += delayed
    return audio * mod * env * 0.4

def synth_sub_bass(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.sin(2 * np.pi * freq * t)
    env = create_envelope(n, 0.01, 0.8, 0.3, sr)
    return audio * env

def create_epic_cinematic():
    bpm = 100
    duration = 65
    bar_dur = 60 / bpm * 4
    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)
        start = int(t * SAMPLE_RATE)
        if start < samples:
            k = synth_kick(pitch_start=180, pitch_end=35, duration=0.5)
            audio[start:start+len(k)] += k

    dark_chords = [[55, 82, 110], [51, 77, 103], [58, 87, 116], [46, 69, 92]]
    for section in range(int(duration / 16)):
        chord = dark_chords[section % len(dark_chords)]
        start = int(section * 16 * SAMPLE_RATE)
        pad = synth_pad(chord, 15.5, detune=0.002)
        if start + len(pad) <= samples: audio[start:start+len(pad)] += pad

    for t in np.arange(0, duration, bar_dur * 2):
        start = int(t * SAMPLE_RATE)
        if start < samples:
            sub = synth_sub_bass(41, bar_dur * 1.8)
            if start + len(sub) <= samples: audio[start:start+len(sub)] += sub * 0.5

    peak = np.max(np.abs(audio))
    if peak > 0: audio = audio / peak * 0.9

    return audio

audio = create_epic_cinematic()
save_as_mp3(audio, "bg_epic_cinematic.mp3")