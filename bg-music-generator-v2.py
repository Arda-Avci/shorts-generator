"""
Professional Shorts Background Music Generator v2
Hip-hop / Techno-Trance - 60+ saniye, zengin enstrümanlar
"""
import numpy as np
from scipy.io import wavfile
import os

SAMPLE_RATE = 44100
OUTPUT_DIR = r"c:\users\Damla\Proje\Muhabbet\shorts-generator\bg-music"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_as_mp3(data, filename, bitrate=320):
    """WAV oluştur, mp3'e cevir"""
    wav_path = os.path.join(OUTPUT_DIR, filename.replace('.mp3', '.wav'))
    mp3_path = os.path.join(OUTPUT_DIR, filename)

    # Normalize
    peak = np.max(np.abs(data))
    if peak > 0:
        data = data / peak * 0.85
    data = np.tanh(data * 1.3) * 0.85
    data = np.int16(data * 32767)

    wavfile.write(wav_path, SAMPLE_RATE, data)
    os.system('ffmpeg -y -i "{0}" -b:a {1}k -ar 44100 "{2}" 2>nul'.format(wav_path, bitrate, mp3_path))
    os.remove(wav_path)
    print("[+] {0}".format(filename))

# ====== YARDIMCI FONKSIYONLAR ======

def create_envelope(length, attack=0.005, decay=0.1, sustain=0.7, release=0.2, sr=SAMPLE_RATE):
    """ADSR envelope - exact length"""
    length = int(length)
    if length <= 0:
        return np.array([])

    a = min(int(attack * sr), length // 4)
    d = min(int(decay * sr), length // 4)
    r = min(int(release * sr), length // 4)
    s = max(0, length - a - d - r)

    env = np.zeros(length)
    idx = 0

    if a > 0:
        env[idx:idx+a] = np.linspace(0, 1, a)
        idx += a
    if s > 0:
        env[idx:idx+s] = sustain
        idx += s
    if d > 0 and idx < length:
        remaining = min(d, length - idx)
        env[idx:idx+remaining] = np.linspace(1, sustain, remaining)
        idx += remaining
    if r > 0 and idx < length:
        remaining = min(r, length - idx)
        env[idx:idx+remaining] = np.linspace(sustain, 0, remaining)

    return env

def lpf(audio, cutoff=0.3):
    """Basit low-pass filter"""
    result = np.zeros_like(audio)
    for i in range(1, len(audio)):
        result[i] = result[i-1] + cutoff * (audio[i] - result[i-1])
    return result

def hpf(audio, cutoff=0.3):
    """Basit high-pass filter"""
    result = np.zeros_like(audio)
    for i in range(1, len(audio)):
        result[i] = result[i-1] + cutoff * (audio[i] - audio[i-1])
    return result

def soft_clip(x, threshold=0.8):
    """Soft clipping"""
    return np.tanh(x / threshold) * threshold

def safe_add(audio, start, data, gain=1.0, max_len=None):
    """Guvenli audio ekleme"""
    if start >= len(audio) or len(data) == 0:
        return
    if max_len is None:
        max_len = len(audio) - start
    end = min(start + len(data), start + max_len, len(audio))
    actual_len = end - start
    if actual_len > 0:
        audio[start:end] += data[:actual_len] * gain

# ====== SES SENTEZLEYICILER ======

def synth_808(freq=45, duration=1.0, decay=0.5, sr=SAMPLE_RATE):
    """808 tarzi kick/bass - derin ve gucclu"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Pitch envelope - dusuyen
    pitch_env = np.exp(-t * 12)
    pitch = freq * (1 + pitch_env * 4)

    # Amplitude envelope
    amp = np.exp(-t * (2 + decay * 8))

    # Phase accumulation
    phase = np.cumsum(2 * np.pi * pitch / sr)

    # Katmanli synth
    sine1 = np.sin(phase)
    sine2 = np.sin(phase * 2) * 0.4
    sine3 = np.sin(phase * 0.5) * 0.3
    sine4 = np.sin(phase * 3) * 0.1

    audio = (sine1 + sine2 + sine3 + sine4) * amp

    # Saturation
    return soft_clip(audio, 0.7)

def synth_kick(freq=60, duration=0.4, sr=SAMPLE_RATE):
    """Dusuk frekansli kick"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Pitch drop
    pitch_env = np.exp(-t * 20)
    freq_env = freq * (5 + pitch_env * 12)

    # Phase accumulation
    phase = np.cumsum(2 * np.pi * freq_env / sr)

    # Sine with envelope
    amp = np.exp(-t * 6)
    audio = np.sin(phase) * amp

    # Sub layer
    sub = np.sin(2 * np.pi * 30 * t) * np.exp(-t * 12)
    click = np.exp(-t * 100) * 0.3  # Transient click

    return (audio * 0.5 + sub * 0.4 + click * 0.1) * 0.9

def synth_snare(duration=0.25, sr=SAMPLE_RATE):
    """Gercekci snare"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Noise
    noise = np.random.randn(n)
    noise = hpf(noise, 0.2)

    # Tonal component - body
    tone1 = np.sin(2 * np.pi * 180 * t)
    tone2 = np.sin(2 * np.pi * 220 * t) * 0.5
    tone3 = np.sin(2 * np.pi * 340 * t) * 0.3
    tone = tone1 + tone2 + tone3

    # Rim click
    click = np.sin(2 * np.pi * 400 * t) * np.exp(-t * 80)

    # Combined
    audio = noise * 0.5 + tone * 0.4 + click * 0.1
    amp = np.exp(-t * 12)

    return audio * amp

def synth_clap(duration=0.15, sr=SAMPLE_RATE):
    """Clap sound"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple noise bursts
    audio = np.zeros(n)
    for offset in [0, 0.01, 0.02, 0.03]:
        if int(offset * sr) < n:
            idx = int(offset * sr)
            burst_len = min(n - idx, int(0.03 * sr))
            burst = np.random.randn(burst_len)
            burst = hpf(burst, 0.4)
            audio[idx:idx+burst_len] += burst[:burst_len] * 0.25

    amp = np.exp(-t * 25)
    return audio * amp

def synth_hihat(open=False, vel=0.3, sr=SAMPLE_RATE):
    """Zengin hi-hat"""
    duration = 0.06 if not open else 0.25
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Noise
    noise = np.random.randn(n)

    # Filtered noise layers
    filtered = np.zeros(n)
    for i in range(1, n):
        filtered[i] = filtered[i-1] + 0.6 * (noise[i] - filtered[i-1])

    filtered2 = np.zeros(n)
    for i in range(1, n):
        filtered2[i] = filtered2[i-1] + 0.8 * (noise[i] - filtered2[i-1])

    # Metallic tones
    metallic = np.sin(2 * np.pi * 7500 * t) * 0.25
    metallic += np.sin(2 * np.pi * 9500 * t) * 0.2
    metallic += np.sin(2 * np.pi * 12000 * t) * 0.15
    metallic += np.sin(2 * np.pi * 5000 * t) * 0.2

    audio = filtered * 0.4 + filtered2 * 0.3 + metallic * 0.3
    amp = np.exp(-t * (35 if not open else 10))

    return audio * amp * vel

def synth_rimshot(duration=0.08, sr=SAMPLE_RATE):
    """Rimshot"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # High pitched click
    click = np.sin(2 * np.pi * 800 * t)
    click += np.sin(2 * np.pi * 1600 * t) * 0.5

    amp = np.exp(-t * 60)
    return click * amp

def synth_bass(freq, duration, octave=1, sr=SAMPLE_RATE):
    """Synth bass - kalın ve dinamik"""
    n = int(sr * duration)
    t = np.arange(n) / sr
    f = freq * octave

    # Multiple oscillators
    sine = np.sin(2 * np.pi * f * t)
    saw = 2 * (t * f - np.floor(t * f + 0.5))
    square = np.sign(np.sin(2 * np.pi * f * t))

    audio = sine * 0.5 + saw * 0.3 + square * 0.2

    # Filter envelope
    filter_env = create_envelope(n, attack=0.02, decay=0.15, sustain=0.4, release=0.3, sr=sr)

    # Apply filter sweep
    filtered = np.zeros(n)
    cutoff_start = 0.1
    cutoff_end = 0.6
    for i in range(n):
        cutoff = cutoff_start + (cutoff_end - cutoff_start) * filter_env[i]
        if i > 0:
            filtered[i] = filtered[i-1] + cutoff * (audio[i] - filtered[i-1])
        else:
            filtered[i] = audio[i] * cutoff

    # Amp envelope
    env = create_envelope(n, attack=0.01, decay=0.1, sustain=0.7, release=0.4, sr=sr)

    return filtered * env * 0.5

def synth_sub_bass(freq, duration, sr=SAMPLE_RATE):
    """Sub bass - pure sine"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    audio = np.sin(2 * np.pi * freq * t)
    env = create_envelope(n, attack=0.01, sustain=0.8, release=0.3, sr=sr)

    return audio * env * 0.6

def synth_pad(freqs, duration, sr=SAMPLE_RATE):
    """Atmosferik pad - zengin"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    audio = np.zeros(n)
    for f in freqs:
        # Multiple detuned oscillators
        for detune in [-0.05, -0.025, 0, 0.025, 0.05]:
            audio += np.sin(2 * np.pi * f * (1 + detune) * t) * 0.06

    # Slow amplitude modulation (breathing)
    mod = 1 + np.sin(2 * np.pi * 0.3 * t) * 0.15
    mod += np.sin(2 * np.pi * 0.7 * t) * 0.05

    # Slow filter modulation
    env = create_envelope(n, attack=0.5, decay=0.3, sustain=0.6, release=0.5, sr=sr)

    return audio * mod * env * 0.3

def synth_strings(freq, duration, sr=SAMPLE_RATE):
    """String section sound"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Saw + square mix
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))
    square = np.sign(np.sin(2 * np.pi * freq * t))

    audio = saw * 0.5 + square * 0.3

    # Vibrato
    vibrato = 1 + np.sin(2 * np.pi * 5 * t) * 0.01
    audio = audio * vibrato

    # Long envelope
    env = create_envelope(n, attack=0.2, decay=0.1, sustain=0.8, release=0.5, sr=sr)

    # Lowpass filter for warmth
    filtered = lpf(audio, 0.3)

    return filtered * env * 0.25

def synth_brass(freq, duration, sr=SAMPLE_RATE):
    """Brass sound"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple oscillators
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))

    audio = saw

    # Bright envelope
    env = create_envelope(n, attack=0.05, decay=0.1, sustain=0.7, release=0.3, sr=sr)

    # Filter
    filtered = lpf(audio, 0.4)

    return filtered * env * 0.3

def synth_organ(freq, duration, sr=SAMPLE_RATE):
    """Organ sound"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Drawbars (organ harmonics)
    audio = np.sin(2 * np.pi * freq * t) * 1.0
    audio += np.sin(2 * np.pi * freq * 2 * t) * 0.5
    audio += np.sin(2 * np.pi * freq * 3 * t) * 0.25
    audio += np.sin(2 * np.pi * freq * 4 * t) * 0.125
    audio += np.sin(2 * np.pi * freq * 8 * t) * 0.06

    env = create_envelope(n, attack=0.01, decay=0.05, sustain=0.9, release=0.2, sr=sr)

    return audio * env * 0.2

def synth_lead(freq, duration, sr=SAMPLE_RATE):
    """Lead synth - supersaw tarzi"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple detuned saws
    saw = np.zeros(n)
    detunes = [-0.04, -0.02, 0, 0.02, 0.04, 0.06]
    for detune in detunes:
        f = freq * (1 + detune)
        saw += 2 * (t * f - np.floor(t * f + 0.5))

    audio = saw / len(detunes)

    # Filter envelope
    filter_env = create_envelope(n, attack=0.1, decay=0.15, sustain=0.4, release=0.4, sr=sr)

    # Apply filter
    filtered = np.zeros(n)
    cutoff_start = 0.15
    cutoff_end = 0.7
    for i in range(n):
        cutoff = cutoff_start + (cutoff_end - cutoff_start) * filter_env[i]
        if i > 0:
            filtered[i] = filtered[i-1] + cutoff * (audio[i] - filtered[i-1])
        else:
            filtered[i] = audio[i] * cutoff

    # Amp envelope
    env = create_envelope(n, attack=0.08, decay=0.1, sustain=0.6, release=0.5, sr=sr)

    return filtered * env * 0.4

def synth_arp(freq, duration, sr=SAMPLE_RATE):
    """Arpeggio synth"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Bright waveform
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))
    sine = np.sin(2 * np.pi * freq * t)

    audio = saw * 0.6 + sine * 0.4

    # Short staccato envelope
    env = create_envelope(n, attack=0.005, decay=0.05, sustain=0.3, release=0.1, sr=sr)

    # Filter
    filtered = lpf(audio, 0.5)

    return filtered * env * 0.35

def synth_pluck(freq, duration, sr=SAMPLE_RATE):
    """Plucked string sound"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Karplus-Strong inspired
    audio = np.zeros(n)

    # Initial noise burst
    noise_len = int(0.002 * sr)
    if noise_len < n:
        audio[:noise_len] = np.random.randn(noise_len) * 0.5

    # Resonant filter
    for i in range(noise_len, n):
        audio[i] = audio[i-1] + 0.99 * (audio[i-1] - audio[i-2])
        audio[i] *= 0.996

    # Add sine component
    sine = np.sin(2 * np.pi * freq * t)
    audio = audio * 0.3 + sine * 0.7

    # Envelope
    env = create_envelope(n, attack=0.002, decay=0.1, sustain=0.3, release=0.4, sr=sr)

    return audio * env * 0.4

def synth_wobble_bass(freq, duration, wobble_rate=4, sr=SAMPLE_RATE):
    """Wobble bass - techno/ dubstep tarzi"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # LFO for wobble
    lfo = np.sin(2 * np.pi * wobble_rate * t)

    # Modulated frequency
    freq_mod = 1 + lfo * 0.15
    f = freq * freq_mod

    # Phase
    phase = np.cumsum(2 * np.pi * f / sr)

    # Audio
    sine = np.sin(phase)
    saw = 2 * (t * f - np.floor(t * f + 0.5))

    audio = sine * 0.6 + saw * 0.4

    # Filter envelope
    filter_env = 0.3 + lfo * 0.2 + 0.3
    filter_env = np.clip(filter_env, 0.1, 0.8)

    # Apply dynamic filter
    filtered = np.zeros(n)
    for i in range(1, n):
        filtered[i] = filtered[i-1] + filter_env[i] * (audio[i] - filtered[i-1])

    # Amp envelope
    env = create_envelope(n, attack=0.01, decay=0.1, sustain=0.7, release=0.3, sr=sr)

    return filtered * env * 0.5

def synth_riser(duration, start_freq=50, end_freq=400, sr=SAMPLE_RATE):
    """Noise riser/whoosh"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Noise
    noise = np.random.randn(n)

    # Frequency sweep
    freq_sweep = start_freq * (end_freq / start_freq) ** (t / duration)

    # Bandpass filtered noise
    filtered = np.zeros(n)
    for i in range(1, n):
        # Dynamic cutoff
        cutoff = 0.1 + 0.6 * (t[i] / duration)
        filtered[i] = filtered[i-1] + cutoff * (noise[i] - filtered[i-1])

    # Add tonal component
    phase = np.cumsum(2 * np.pi * freq_sweep / sr)
    tone = np.sin(phase) * 0.3

    audio = filtered * 0.7 + tone * 0.3

    # Envelope
    env = create_envelope(n, attack=0.1, decay=0, sustain=1, release=0, sr=sr)

    return audio * env * 0.5

def synth_fx_hit(duration, freq=200, sr=SAMPLE_RATE):
    """Impact/impact FX"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Downward pitch sweep
    freq_env = freq * (1 + (1 - t / duration) * 3)

    phase = np.cumsum(2 * np.pi * freq_env / sr)

    # Multiple harmonics
    audio = np.sin(phase)
    audio += np.sin(phase * 2) * 0.5
    audio += np.sin(phase * 0.5) * 0.3

    # Envelope
    env = np.exp(-t * 8)

    return audio * env * 0.6

def sidechain_comp(audio, trigger_times, threshold=0.3, ratio=4, attack=0.001, release=0.15, sr=SAMPLE_RATE):
    """Sidechain compression"""
    result = audio.copy()

    for kt in trigger_times:
        start = int(kt * sr)
        env_len = int(release * sr)
        end = min(start + env_len, len(audio))
        if start < len(audio):
            chunk = audio[start:end]
            env = create_envelope(len(chunk), attack=attack, decay=0, sustain=0, release=release * 0.5, sr=sr)
            amount = threshold + (1 - threshold) * (1 - env * ratio)
            amount = np.clip(amount, 0.05, 1)
            result[start:end] = chunk * amount

    return result

# ====== MUZIK TASARIMLERI ======

def create_techno_thumper_extended():
    """Genisletilmis techno thumper - 65 sn"""
    bpm = 128
    duration = 65
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)

    # Ana ritim
    for kt in kick_times:
        start = int(kt * SAMPLE_RATE)
        k = synth_kick(55, 0.35)
        safe_add(audio, start, k, 0.95)

    # Percussion
    for bar in range(int(duration / (beat_dur * 4))):
        bar_start = bar * 4 * beat_dur

        # Snare on 3
        st = bar_start + 2 * beat_dur
        start = int(st * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.2)
            safe_add(audio, start, s, 0.6)

        # Clap on 3.5
        ct = bar_start + 2.5 * beat_dur
        start = int(ct * SAMPLE_RATE)
        if start < samples:
            c = synth_clap(0.12)
            safe_add(audio, start, c, 0.5)

        # Rimshot on 2.5
        rt = bar_start + 1.5 * beat_dur
        start = int(rt * SAMPLE_RATE)
        if start < samples:
            r = synth_rimshot()
            safe_add(audio, start, r, 0.3)

    # Hi-hats - 16ths with variation
    for bar in range(int(duration / (beat_dur * 4))):
        for i in range(16):
            t = bar * 4 * beat_dur + i * beat_dur / 4
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            vel = 0.35 if i % 4 == 0 else 0.25
            open_hat = (i % 8 == 6)
            h = synth_hihat(open=open_hat, vel=vel)
            safe_add(audio, start, h, 1.0)

    # Acid bass line
    acid_notes = [55, 55, 73, 55, 65, 55, 73, 82]
    step = beat_dur / 4

    for bar in range(int(duration / (beat_dur * 4))):
        for i, note in enumerate(acid_notes):
            t = bar * 4 * beat_dur + i * step
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            acid = synth_bass(note, step * 0.9, octave=1)
            safe_add(audio, start, acid, 0.4)

    # Atmosphere pads - evolving
    pad_chords = [
        [82, 110, 164],
        [73, 98, 146],
        [87, 123, 174],
        [65, 98, 130],
    ]

    for section in range(int(duration / 8)):
        chord = pad_chords[section % len(pad_chords)]
        start = int(section * 8 * SAMPLE_RATE)
        pad = synth_pad(chord, 7.5)
        safe_add(audio, start, pad, 0.35)

    # String sections - building
    for section in range(int(duration / 8)):
        if section >= 2:  # Start after 16 seconds
            chord_freqs = [220, 261, 329] if section % 2 == 0 else [196, 246, 293]
            start = int(section * 8 * SAMPLE_RATE)
            strings = synth_strings(chord_freqs[0], 7.5)
            safe_add(audio, start, strings, 0.25)

    # Brass stabs
    stab_pattern = [0, 2.5, 4, 6.5, 8, 10.5, 12, 14.5]
    for bar in range(int(duration / 16)):
        for offset in stab_pattern:
            if offset < 16:
                t = bar * 16 * beat_dur + offset * beat_dur
                start = int(t * SAMPLE_RATE)
                if start >= samples:
                    break

                stab = synth_brass(440, 0.3)
                safe_add(audio, start, stab, 0.2)

    # Riser before transition
    for bar in range(int(duration / (beat_dur * 16))):
        if bar >= 3:
            riser_start = int((bar * 16 + 14) * beat_dur * SAMPLE_RATE)
            if riser_start < samples:
                riser = synth_riser(beat_dur * 2, 80, 500)
                safe_add(audio, riser_start, riser, 0.4)

    audio = sidechain_comp(audio, kick_times, threshold=0.35)
    return audio

def create_dark_techno_extended():
    """Genisletilmis karanlik techno - 62 sn"""
    bpm = 135
    duration = 62
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)

    # Deep kick
    for kt in kick_times:
        start = int(kt * SAMPLE_RATE)
        k = synth_kick(42, 0.4)
        safe_add(audio, start, k, 1.0)

    # Percussion
    for bar in range(int(duration / (beat_dur * 4))):
        bar_start = bar * 4 * beat_dur

        # Snare
        t = bar_start + 2.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.15)
            safe_add(audio, start, s, 0.55)

        # Clap
        t = bar_start + 2.75 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap(0.1)
            safe_add(audio, start, c, 0.45)

        # Rimshot
        for beat in [0.5, 1.5, 3.5]:
            t = bar_start + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                r = synth_rimshot()
                safe_add(audio, start, r, 0.3)

    # Industrial hats
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        is_open = (t % beat_dur < 0.01) or ((t + beat_dur * 0.5) % beat_dur < 0.01)
        vel = 0.4 if (t % beat_dur) < 0.01 else 0.28
        h = synth_hihat(open=is_open, vel=vel)
        safe_add(audio, start, h, 1.0)

    # Hypnotic bass
    bass_notes = [36, 36, 43, 41, 36, 36, 43, 45, 36, 38, 43, 41, 43, 45, 48, 43]
    step = beat_dur

    for bar in range(int(duration / (beat_dur * 16))):
        for i, note in enumerate(bass_notes):
            t = bar * 16 * beat_dur + i * step
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            bass = synth_bass(note, step * 0.85, octave=1)
            safe_add(audio, start, bass, 0.55)

            # Sub layer
            sub = synth_sub_bass(note / 2, step * 0.9)
            safe_add(audio, start, sub, 0.4)

    # Dark pads - dissonant
    dark_chords = [
        [73, 87, 110, 138],
        [65, 82, 103, 138],
        [70, 87, 116, 155],
        [58, 73, 97, 130],
    ]

    for section in range(int(duration / 16)):
        chord = dark_chords[section % len(dark_chords)]
        start = int(section * 16 * SAMPLE_RATE)
        pad = synth_pad(chord, 15.5)
        safe_add(audio, start, pad, 0.3)

    # String accents
    for section in range(int(duration / 8)):
        if section >= 1:
            start = int(section * 8 * SAMPLE_RATE)
            strings = synth_strings(146, 7.5)
            safe_add(audio, start, strings, 0.2)

    # Wobble sections
    for bar in range(int(duration / (beat_dur * 8))):
        if bar % 2 == 1:  # Every other 8-bar section
            start = int(bar * 8 * beat_dur * SAMPLE_RATE)
            wobble = synth_wobble_bass(55, 7.5, wobble_rate=6)
            safe_add(audio, start, wobble, 0.4)

    # Impact FX
    impact_times = [16, 32, 48]
    for imp_t in impact_times:
        if imp_t < duration:
            start = int(imp_t * SAMPLE_RATE)
            impact = synth_fx_hit(0.5, freq=150)
            safe_add(audio, start, impact, 0.5)

    # Noise risers
    for bar in range(int(duration / (beat_dur * 16))):
        if bar > 0:
            riser_start = int((bar * 16 + 14) * beat_dur * SAMPLE_RATE)
            if riser_start < samples:
                riser = synth_riser(beat_dur * 2, 60, 400)
                safe_add(audio, riser_start, riser, 0.35)

    audio = sidechain_comp(audio, kick_times, threshold=0.3, ratio=5)
    return audio

def create_modern_boombap_extended():
    """Genisletilmis modern boom bap - 68 sn"""
    bpm = 88
    duration = 68
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    for bar in range(int(duration / bar_dur)):
        for beat in [0, 2.5, 3.5]:  # Complex kick pattern
            t = bar * bar_dur + beat * beat_dur
            kick_times.append(t)
            start = int(t * SAMPLE_RATE)
            if start < samples:
                k = synth_808(42, 0.7, decay=0.35)
                safe_add(audio, start, k, 0.9)

    # Snare pattern
    for bar in range(int(duration / bar_dur)):
        for beat in [1, 3]:
            t = bar * bar_dur + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                s = synth_snare(0.25)
                safe_add(audio, start, s, 0.65)

        # Off-beat snare
        t = bar * bar_dur + 2.75 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.15) * 0.4
            safe_add(audio, start, s, 1.0)

    # Chopped hi-hats
    for bar in range(int(duration / (bar_dur / 2))):
        for i in range(16):
            t = bar * (bar_dur / 2) + i * (bar_dur / 32)
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            vel = 0.4 if i % 4 == 0 else 0.25
            h = synth_hihat(open=(i % 16 == 8), vel=vel)
            safe_add(audio, start, h, 1.0)

    # Soulful bass
    bass_pattern = [
        (55, 0, bar_dur, 0.6),
        (55, bar_dur, bar_dur * 2, 0.55),
        (58, bar_dur * 2, bar_dur * 3, 0.5),
        (62, bar_dur * 2.5, bar_dur * 3.5, 0.6),
        (65, bar_dur * 3, bar_dur * 4, 0.65),
    ]

    for bar in range(int(duration / (bar_dur * 4))):
        for freq, st, en, g in bass_pattern:
            start = int((bar * bar_dur * 4 + st) * SAMPLE_RATE)
            dur = en - st
            if start < samples:
                bass = synth_bass(freq, dur, octave=1)
                safe_add(audio, start, bass, g)

                # Sub layer
                sub = synth_sub_bass(freq / 2, dur * 0.95)
                safe_add(audio, start, sub, g * 0.5)

    # Lo-fi chords with different instruments
    chords = [
        (261.63, 329.63, 392.00),  # Cmaj7
        (233.08, 293.66, 349.23),  # Bbmaj7
        (220.00, 277.18, 329.63),  # Am9
        (207.65, 261.63, 311.13),  # Gmaj7
    ]

    for bar in range(int(duration / bar_dur)):
        chord = chords[bar % len(chords)]
        start = int(bar * bar_dur * SAMPLE_RATE)

        # Pad layer
        pad = synth_pad(chord, bar_dur * 0.9)
        safe_add(audio, start, pad, 0.35)

        # String layer
        strings = synth_strings(chord[0], bar_dur * 0.85)
        safe_add(audio, start, strings, 0.25)

        # Organ layer (every 2 bars)
        if bar % 2 == 0:
            organ = synth_organ(chord[0] / 2, bar_dur * 0.9)
            safe_add(audio, start, organ, 0.2)

    # Lead melody - smooth and soulful
    melody = [
        (523, 0.5), (587, 0.5), (659, 0.5), (587, 0.5),
        (523, 0.75), (494, 0.25), (523, 0.5),
        (659, 0.5), (587, 0.5), (523, 1.0),
        (494, 0.5), (523, 0.5), (587, 0.5), (659, 0.5),
        (698, 0.75), (659, 0.25), (587, 0.5),
        (523, 1.0), (494, 0.5), (440, 0.5),
    ]

    offset = 0
    for section in range(2):  # 2 melody sections
        for freq, dur in melody:
            t = section * 32 * beat_dur + offset
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            lead = synth_lead(freq, dur * 0.92)
            safe_add(audio, start, lead, 0.3)
            offset += dur

        offset += 16 * beat_dur  # Gap between sections

    # Pluck accents
    pluck_notes = [784, 659, 587, 523, 494, 440]
    for bar in range(int(duration / (bar_dur * 2))):
        for i, note in enumerate(pluck_notes):
            t = bar * bar_dur * 2 + i * beat_dur * 0.5
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            pluck = synth_pluck(note, 0.3)
            safe_add(audio, start, pluck, 0.2)

    return audio

def create_uk_garage_vibes():
    """UK Garage tarzi - 64 sn"""
    bpm = 130
    duration = 64
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)
        start = int(t * SAMPLE_RATE)
        if start < samples:
            k = synth_808(45, 0.6, decay=0.4)
            safe_add(audio, start, k, 0.8)

    # Skip beat kick (UKG signature)
    for bar in range(int(duration / (bar_dur * 2))):
        t = bar * bar_dur * 2 + 2.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            k = synth_kick(50, 0.15) * 0.6
            safe_add(audio, start, k, 1.0)

    # Snare
    for t in np.arange(0, duration, beat_dur):
        if t % (beat_dur * 2) >= beat_dur:
            start = int(t * SAMPLE_RATE)
            if start < samples:
                s = synth_snare(0.2)
                safe_add(audio, start, s, 0.6)

    # Clap
    for bar in range(int(duration / bar_dur)):
        t = bar * bar_dur + 1.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap(0.15)
            safe_add(audio, start, c, 0.5)

        t = bar * bar_dur + 3.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap(0.15) * 0.8
            safe_add(audio, start, c, 1.0)

    # Hi-hats - shuffled
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        # Off-grid shuffle
        shuffle = (t % beat_dur) < 0.01 or (abs((t % beat_dur) - beat_dur * 0.75) < 0.01)
        vel = 0.4 if shuffle else 0.25
        h = synth_hihat(open=(t % (beat_dur * 2) < 0.01), vel=vel)
        safe_add(audio, start, h, 1.0)

    # 2-step bass
    bass_notes = [41, 0, 55, 0, 41, 55, 48, 0, 41, 0, 55, 0, 48, 55, 53, 0]
    step = beat_dur / 2

    for bar in range(int(duration / (beat_dur * 8))):
        for i, note in enumerate(bass_notes):
            if note > 0:
                t = bar * 8 * beat_dur + i * step
                start = int(t * SAMPLE_RATE)
                if start < samples:
                    bass = synth_bass(note, step * 0.8, octave=1)
                    safe_add(audio, start, bass, 0.5)

    # UKG pad chords
    ukg_chords = [
        (261.63, 329.63, 392.00, 440.00),  # Cmaj9
        (220.00, 277.18, 329.63, 392.00),  # Am9
        (233.08, 293.66, 349.23, 440.00),  # Bbmaj9
        (207.65, 261.63, 311.13, 392.00),  # G9
    ]

    for bar in range(int(duration / bar_dur)):
        chord = ukg_chords[bar % len(ukg_chords)]
        start = int(bar * bar_dur * SAMPLE_RATE)

        pad = synth_pad(chord, bar_dur * 0.9)
        safe_add(audio, start, pad, 0.35)

        strings = synth_strings(chord[0], bar_dur * 0.85)
        safe_add(audio, start, strings, 0.25)

    # Stabby synths
    stab_times = [0, 0.5, 2, 2.5, 4, 4.5, 6, 6.5]
    for bar in range(int(duration / (bar_dur * 4))):
        for offset in stab_times:
            t = bar * bar_dur * 4 + offset * bar_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                stab = synth_brass(523, 0.15)
                safe_add(audio, start, stab, 0.25)

    audio = sidechain_comp(audio, kick_times, threshold=0.4)
    return audio

def create_drill_vibes():
    """UK Drill tarzi - 66 sn"""
    bpm = 140
    duration = 66
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    # Heavy 808 kicks
    for bar in range(int(duration / bar_dur)):
        for beat in [0, 1, 2, 3]:
            t = bar * bar_dur + beat * beat_dur
            kick_times.append(t)
            start = int(t * SAMPLE_RATE)
            if start < samples:
                k = synth_808(36, 1.0, decay=0.6)
                safe_add(audio, start, k, 0.9)

    # Snare - heavy
    for bar in range(int(duration / (bar_dur * 2))):
        t = bar * bar_dur * 2 + 2.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.3)
            safe_add(audio, start, s, 0.7)

        t = bar * bar_dur * 2 + 6.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.25)
            safe_add(audio, start, s, 0.65)

    # Clap on snare
    for bar in range(int(duration / (bar_dur * 2))):
        t = bar * bar_dur * 2 + 2.5 * beat_dur + 0.01
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap(0.2)
            safe_add(audio, start, c, 0.6)

        t = bar * bar_dur * 2 + 6.5 * beat_dur + 0.01
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap(0.18)
            safe_add(audio, start, c, 0.55)

    # Hi-hats
    for bar in range(int(duration / (bar_dur / 4))):
        for i in range(4):
            t = bar * (bar_dur / 4) + i * (bar_dur / 16)
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            vel = 0.35 if i % 4 == 0 else 0.2
            h = synth_hihat(vel=vel)
            safe_add(audio, start, h, 1.0)

    # Dark bass
    bass_notes = [36, 36, 41, 38, 36, 43, 41, 38]
    step = bar_dur

    for bar in range(int(duration / (bar_dur * 4))):
        for i, note in enumerate(bass_notes):
            t = bar * bar_dur * 4 + i * step
            start = int(t * SAMPLE_RATE)
            if start < samples:
                bass = synth_bass(note, step * 0.95, octave=1)
                safe_add(audio, start, bass, 0.6)

                sub = synth_sub_bass(note / 2, step * 0.9)
                safe_add(audio, start, sub, 0.5)

    # Dark minor chord pads
    dark_chords = [
        (155.56, 185.00, 232.00),  # Eb minor
        (138.59, 174.61, 207.65),  # Db minor
        (146.83, 174.61, 220.00),  # D minor
        (130.81, 164.81, 196.00),  # C minor
    ]

    for bar in range(int(duration / bar_dur)):
        chord = dark_chords[bar % len(dark_chords)]
        start = int(bar * bar_dur * SAMPLE_RATE)

        pad = synth_pad(chord, bar_dur * 0.9)
        safe_add(audio, start, pad, 0.3)

    # Aggressive brass stabs
    stab_pattern = [0, 1.5, 4, 5.5, 8, 9.5, 12, 13.5]
    for bar in range(int(duration / (bar_dur * 8))):
        for offset in stab_pattern:
            t = bar * bar_dur * 8 + offset * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                stab = synth_brass(311, 0.2)
                safe_add(audio, start, stab, 0.3)

    audio = sidechain_comp(audio, kick_times, threshold=0.25, ratio=6)
    return audio

def create_amapiano_vibes():
    """Amapiano tarzi - 65 sn"""
    bpm = 115
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
            k = synth_808(48, 0.5, decay=0.3)
            safe_add(audio, start, k, 0.85)

    # Shaker/percussion
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        vel = 0.3 if t % beat_dur < 0.01 else 0.2
        h = synth_hihat(vel=vel)
        safe_add(audio, start, h, 1.0)

    # Log drum / log drum simulation
    for bar in range(int(duration / bar_dur)):
        for beat in [1, 3]:
            t = bar * bar_dur + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                log1 = synth_pluck(392, 0.15)
                log2 = synth_pluck(523, 0.12)
                safe_add(audio, start, log1, 0.45)
                safe_add(audio, start, log2, 0.45 * 0.7)

    # Log drum pattern variations
    for bar in range(int(duration / (bar_dur * 2))):
        # Off-beat log
        t = bar * bar_dur * 2 + 1.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            log = synth_pluck(440, 0.12)
            safe_add(audio, start, log, 0.4)

    # Snare
    for t in np.arange(0, duration, beat_dur * 2):
        start = int((t + 2 * beat_dur) * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.2)
            safe_add(audio, start, s, 0.55)

    # Amapiano bass - melodic
    bass_pattern = [
        (220, 0, bar_dur),
        (246, bar_dur, bar_dur * 2),
        (261, bar_dur * 2, bar_dur * 3),
        (220, bar_dur * 3, bar_dur * 4),
    ]

    for bar in range(int(duration / (bar_dur * 4))):
        for freq, st, en in bass_pattern:
            t = bar * bar_dur * 4 + st
            start = int(t * SAMPLE_RATE)
            if start < samples:
                bass = synth_bass(freq, en - st, octave=1)
                safe_add(audio, start, bass, 0.45)

    # Jazz-influenced piano chords
    piano_chords = [
        (261.63, 329.63, 392.00, 493.88),  # Cmaj7
        (293.66, 349.23, 440.00, 523.25),  # Dm9
        (293.66, 369.99, 440.00, 523.25),   # Dm7
        (246.94, 311.13, 369.99, 493.88),   # Bm7
    ]

    for bar in range(int(duration / (bar_dur / 2))):
        chord = piano_chords[bar % len(piano_chords)]
        start = int(bar * (bar_dur / 2) * SAMPLE_RATE)

        # Arpeggio pattern
        for i, note in enumerate(chord):
            t = bar * (bar_dur / 2) + i * beat_dur * 0.25
            note_start = int(t * SAMPLE_RATE)
            if note_start < samples:
                arp_note = synth_pluck(note * 2, 0.2)
                safe_add(audio, note_start, arp_note, 0.35)

        # Pad version every 4 bars
        if bar % 8 == 0:
            pad = synth_pad(chord[:3], bar_dur * 2 * 0.9)
            safe_add(audio, start, pad, 0.3)

    # Soulful strings
    for bar in range(int(duration / (bar_dur * 4))):
        if bar % 2 == 0:
            chord_freqs = [329.63, 392.00, 493.88]
            start = int(bar * bar_dur * 4 * SAMPLE_RATE)
            strings = synth_strings(chord_freqs[0], bar_dur * 3.5)
            safe_add(audio, start, strings, 0.25)

    audio = sidechain_comp(audio, kick_times, threshold=0.45)
    return audio

# ====== MAIN ======
if __name__ == "__main__":
    print("[*] Muzikler olusturuluyor (v2 - 60+ sn)...")
    print("=" * 50)

    tracks = [
        ("bg_techno_thumper_v2.mp3", create_techno_thumper_extended),
        ("bg_dark_techno_v2.mp3", create_dark_techno_extended),
        ("bg_modern_boombap_v2.mp3", create_modern_boombap_extended),
        ("bg_uk_garage.mp3", create_uk_garage_vibes),
        ("bg_drill_vibes.mp3", create_drill_vibes),
        ("bg_amapiano_vibes.mp3", create_amapiano_vibes),
    ]

    for filename, gen in tracks:
        print("[>] {0}".format(filename))
        try:
            audio = gen()
            save_as_mp3(audio, filename)
        except Exception as e:
            import traceback
            print("[!] Hata: {0}".format(e))
            traceback.print_exc()

    print("=" * 50)
    print("[OK] Tamamlandi!")
    print("[>] Konum: {0}".format(OUTPUT_DIR))