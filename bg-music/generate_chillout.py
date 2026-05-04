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

def synth_pad_chillout(freqs, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.zeros(n)
    for f in freqs:
        for dt in [-0.002, 0, 0.002, 0.004]:
            audio += np.sin(2 * np.pi * f * (1 + dt) * t) * 0.04
    env = create_envelope(n, 0.8, 0.3, 0.7, 0.8, sr)
    mod = 1 + np.sin(2 * np.pi * 0.2 * t) * 0.05
    return audio * mod * env * 0.4

def synth_arp_chillout(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    triangle = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    env = create_envelope(n, 0.1, 0.1, 0.5, 0.3, sr)
    return triangle * env * 0.25

def synth_sub_chillout(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.sin(2 * np.pi * freq * t)
    env = create_envelope(n, 0.2, 0.8, 0.5, 0.6, sr)
    return audio * env * 0.35

def synth_soft_kick(sr=SAMPLE_RATE):
    n = int(sr * 0.5)
    t = np.arange(n) / sr
    pitch_curve = np.linspace(80, 40, n)
    phase = np.cumsum(2 * np.pi * pitch_curve / sr)
    body = np.sin(phase)
    env = create_envelope(n, 0.01, 0.15, 0.4, 0.3, sr)
    return body * env * 0.6

def create_ambient_chillout():
    bpm = 90
    duration = 68
    bar_dur = 60 / bpm * 4
    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    for t in np.arange(0, duration, beat_dur):
        start = int(t * SAMPLE_RATE)
        if start < samples:
            kick = synth_soft_kick()
            audio[start:start+len(kick)] += kick

    chord_prog = [
        [261.63, 329.63, 392.00],
        [220.00, 277.18, 329.63],
        [293.66, 349.23, 440.00],
        [246.94, 293.66, 369.99]
    ]
    for section in range(int(duration / 16)):
        chord = chord_prog[section % len(chord_prog)]
        start = int(section * 16 * SAMPLE_RATE)
        pad = synth_pad_chillout(chord, 15.5)
        if start + len(pad) <= samples: audio[start:start+len(pad)] += pad

    arp_notes = [523, 659, 784, 659, 523, 392, 523, 659]
    for bar in range(int(duration / (bar_dur * 2))):
        for i, note in enumerate(arp_notes):
            t = bar * bar_dur * 2 + i * (beat_dur / 4)
            start = int(t * SAMPLE_RATE)
            if start < samples:
                arp = synth_arp_chillout(note, beat_dur / 4 * 0.8)
                audio[start:start+len(arp)] += arp * 0.5

    for section in range(int(duration / 16)):
        start = int(section * 16 * SAMPLE_RATE)
        if start < samples:
            sub = synth_sub_chillout(65.41, 15.5)
            if start + len(sub) <= samples: audio[start:start+len(sub)] += sub

    peak = np.max(np.abs(audio))
    if peak > 0: audio = audio / peak * 0.9

    return audio

audio = create_ambient_chillout()
save_as_mp3(audio, "bg_ambient_chillout.mp3")