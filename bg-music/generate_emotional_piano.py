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

def synth_piano_emotional(freq, duration, velocity=0.8, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.sin(2 * np.pi * freq * t) * 1.0
    audio += np.sin(2 * np.pi * freq * 2 * t) * 0.5
    audio += np.sin(2 * np.pi * freq * 3 * t) * 0.25
    audio += np.sin(2 * np.pi * freq * 4 * t) * 0.125
    audio += np.sin(2 * np.pi * freq * 5 * t) * 0.06
    env = create_envelope(n, 0.005, 0.4, 0.3, 0.5, sr)
    return audio * env * velocity * 0.4

def synth_strings_emotional(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))
    vibrato = 1 + np.sin(2 * np.pi * 5 * t) * 0.008
    phase = np.cumsum(2 * np.pi * freq * vibrato / sr) / (2 * np.pi)
    audio = np.sin(phase * 2 * np.pi)
    env = create_envelope(n, 0.4, 0.1, 0.8, 0.5, sr)
    return audio * env * 0.25

def synth_sub_emotional(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.arange(n) / sr
    audio = np.sin(2 * np.pi * freq * t)
    env = create_envelope(n, 0.1, 0.8, 0.5, 0.5, sr)
    return audio * env * 0.4

def create_emotional_piano():
    bpm = 70
    duration = 70
    bar_dur = 60 / bpm * 4
    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    chords = [
        (261.63, 329.63, 392.00, 493.88),
        (220.00, 277.18, 329.63, 392.00),
        (293.66, 349.23, 440.00, 523.25),
        (246.94, 293.66, 369.99, 493.88)
    ]

    for bar in range(int(duration / (bar_dur / 2))):
        chord = chords[bar % len(chords)]

        # Piano chord
        start = int(bar * (bar_dur / 2) * SAMPLE_RATE)
        for i, note in enumerate(chord):
            t = bar * (bar_dur / 2) + i * beat_dur * 0.5
            note_start = int(t * SAMPLE_RATE)
            if note_start < samples:
                piano = synth_piano_emotional(note, beat_dur * 0.6, 0.7)
                audio[note_start:note_start+len(piano)] += piano

        # Strings pad
        string = synth_strings_emotional(chord[0], bar_dur * 1.8)
        if start + len(string) <= samples: audio[start:start+len(string)] += string * 0.5

    # Sub bass on downbeats
    for bar in range(int(duration / bar_dur)):
        for beat in [0]:
            t = bar * bar_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                chord = chords[bar % len(chords)]
                sub = synth_sub_emotional(chord[0] / 2, bar_dur * 0.9)
                audio[start:start+len(sub)] += sub

    peak = np.max(np.abs(audio))
    if peak > 0: audio = audio / peak * 0.9

    return audio

audio = create_emotional_piano()
save_as_mp3(audio, "bg_emotional_piano.mp3")