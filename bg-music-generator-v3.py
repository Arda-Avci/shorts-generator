"""
Professional Background Music Generator v3
Gerçekçi, doğal, yapay olmayan sesler
"""
import numpy as np
from scipy.io import wavfile
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, filtfilt
import os

SAMPLE_RATE = 44100
OUTPUT_DIR = r"c:\users\Damla\Proje\Muhabbet\shorts-generator\bg-music"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_as_mp3(data, filename, bitrate=320):
    wav_path = os.path.join(OUTPUT_DIR, filename.replace('.mp3', '.wav'))
    mp3_path = os.path.join(OUTPUT_DIR, filename)

    # Final mastering
    data = soft_clip(data * 0.85, 0.9)
    data = np.int16(data * 32767)

    wavfile.write(wav_path, SAMPLE_RATE, data)
    os.system('ffmpeg -y -i "{0}" -b:a {1}k -ar 44100 "{2}" 2>nul'.format(wav_path, bitrate, mp3_path))
    os.remove(wav_path)
    print("[+] {0}".format(filename))

# ====== FILTER FONKSIYONLARI ======

def butter_lowpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_highpass(cutoff, fs, order=2):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def apply_lpf(audio, cutoff=3000, sr=SAMPLE_RATE):
    b, a = butter_lowpass(cutoff, sr, order=4)
    return filtfilt(b, a, audio)

def apply_hpf(audio, cutoff=80, sr=SAMPLE_RATE):
    b, a = butter_highpass(cutoff, sr, order=2)
    return filtfilt(b, a, audio)

def apply_eq(audio, low_gain=1.0, mid_gain=1.0, high_gain=1.0):
    """Simple 3-band EQ"""
    low = apply_lpf(apply_hpf(audio.copy(), 200), 300)
    mid = apply_lpf(apply_hpf(audio.copy(), 300), 3000)
    high = apply_hpf(audio.copy(), 3000)
    return audio * 0 + low * low_gain + mid * mid_gain + high * high_gain

def soft_clip(x, threshold=0.85):
    """Tape saturation simulation"""
    return np.tanh(x / threshold) * threshold

def safe_add(audio, start, data, gain=1.0):
    if start >= len(audio) or len(data) == 0:
        return
    end = min(start + len(data), len(audio))
    audio[start:end] += data[:end-start] * gain

# ====== REVERB SIMULATION ======

def plate_reverb(audio, decay=0.3, mix=0.2, sr=SAMPLE_RATE):
    """Basit plate reverb simülasyonu"""
    output = audio.copy()

    # Multiple delay taps for diffusion
    delays = [int(sr * d) for d in [0.023, 0.037, 0.047, 0.071, 0.097, 0.113, 0.131]]
    decays = [decay * (1 - i * 0.1) for i in range(len(delays))]

    for delay, dec in zip(delays, decays):
        delayed = np.zeros_like(audio)
        if delay < len(audio):
            delayed[delay:] = audio[:-delay] * dec
        output += delayed

    # Smooth the tail
    output = gaussian_filter1d(output, sigma=10)

    return audio * (1 - mix) + output * mix

def conv_reverb(audio, size=0.1, decay=0.4, sr=SAMPLE_RATE):
    """Basit convolution reverb"""
    ir_len = int(size * sr)
    impulse = np.random.randn(ir_len) * np.exp(-np.arange(ir_len) / (ir_len * decay))

    # Convolve
    output = np.convolve(audio, impulse, mode='same')
    return audio * 0.7 + output * 0.3

# ====== SES SENTEZLEYICILER ======

def noise_burst(duration, decay=20, sr=SAMPLE_RATE):
    """Noise burst generator"""
    n = int(sr * duration)
    t = np.arange(n) / sr
    noise = np.random.randn(n)
    env = np.exp(-t * decay)
    return noise * env

def create_envelope(length, attack=0.005, decay=0.1, sustain=0.7, release=0.2, sr=SAMPLE_RATE):
    length = int(length)
    if length <= 0:
        return np.ones(1)

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

    return env if idx > 0 else np.ones(length)

# ====== GERCEKCI DAVUL SENTEZLEYICILERI ======

def synth_kick_pro(duration=0.4, pitch_start=180, pitch_end=40, sr=SAMPLE_RATE):
    """Profesyonel kick drum"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Pitch envelope - linear drop
    pitch_curve = np.linspace(pitch_start, pitch_end, n)

    # Phase accumulation
    phase = np.cumsum(2 * np.pi * pitch_curve / sr)

    # Multiple harmonics
    body = np.sin(phase)
    body += np.sin(phase * 0.5) * 0.4
    body += np.sin(phase * 2) * 0.15

    # Transient click - extended to full length
    click_duration = 0.003
    click_n = int(sr * click_duration)
    click = np.zeros(n)
    if click_n > 0:
        click[:click_n] = noise_burst(click_duration, decay=500, sr=sr) * 0.3

    # Amplitude envelope
    amp = create_envelope(n, attack=0.001, decay=0.08, sustain=0.3, release=0.15, sr=sr)

    # Combine
    audio = body * amp + click

    # Low-pass filter for warmth
    audio = apply_lpf(audio, 150)

    # Add sub
    sub_env = create_envelope(n, attack=0.001, decay=0.1, sustain=0.4, release=0.2, sr=sr)
    sub = np.sin(2 * np.pi * pitch_end * t) * sub_env

    return (audio * 0.7 + sub * 0.3) * 0.95

def synth_snare_pro(duration=0.25, tune=200, sr=SAMPLE_RATE):
    """Profesyonel snare"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Noise (snare wires)
    wire_noise = noise_burst(duration, decay=25, sr=sr)

    # Tone (drum head)
    tone1 = np.sin(2 * np.pi * tune * t)
    tone2 = np.sin(2 * np.pi * tune * 1.5 * t) * 0.5
    tone3 = np.sin(2 * np.pi * tune * 2 * t) * 0.3

    # High frequency attack - full length
    attack_n = int(sr * 0.01)
    attack_noise = np.zeros(n)
    if attack_n > 0:
        attack_noise[:attack_n] = noise_burst(0.01, decay=150, sr=sr) * 0.4

    # Combined
    tone = tone1 + tone2 + tone3
    tone = apply_hpf(tone, 100)

    # Snap
    snap = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 100)

    audio = wire_noise * 0.5 + tone * 0.35 + attack_noise * 0.3 + snap * 0.1

    # Envelope
    amp = create_envelope(n, attack=0.001, decay=0.05, sustain=0.2, release=0.1, sr=sr)

    return audio * amp

def synth_clap_pro(duration=0.15, sr=SAMPLE_RATE):
    """Gerçekçi clap"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple burst technique
    audio = np.zeros(n)

    # 4 layered noise bursts (simulating hand claps)
    offsets = [0, 0.008, 0.015, 0.022]
    for i, offset in enumerate(offsets):
        start_idx = int(offset * sr)
        if start_idx < n:
            burst_len = min(int(0.025 * sr), n - start_idx)
            burst = np.random.randn(burst_len)

            # Bandpass the burst
            burst = apply_hpf(burst, 400)
            burst = apply_lpf(burst, 4000)

            # Slight pitch variation
            gain = 0.3 - i * 0.03
            audio[start_idx:start_idx+burst_len] += burst * gain

    # Tail
    tail_noise = noise_burst(duration, decay=30, sr=sr)
    tail_noise = apply_lpf(tail_noise, 2000)

    amp = create_envelope(n, attack=0.001, decay=0.05, sustain=0.3, release=0.05, sr=sr)

    return (audio * 0.6 + tail_noise * 0.4) * amp

def synth_hihat_pro(open=False, vel=0.3, decay_time=0.06, sr=SAMPLE_RATE):
    """Gerçekçi hi-hat"""
    duration = 0.25 if open else 0.06
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple noise sources
    noise1 = noise_burst(duration, decay=1/decay_time if decay_time > 0 else 30, sr=sr)
    noise2 = noise_burst(duration, decay=25, sr=sr)

    # Metallic resonances
    metallic = np.zeros(n)
    for freq in [6000, 8000, 10000, 12000]:
        metallic += np.sin(2 * np.pi * freq * t + np.random.rand() * 0.1) * 0.15

    # Combine
    audio = noise1 * 0.3 + noise2 * 0.4 + metallic * 0.3

    # High-pass for brightness
    audio = apply_hpf(audio, 7000)

    # Velocity envelope
    amp = create_envelope(n, attack=0.001, decay=decay_time, sustain=0.1, release=0.01, sr=sr)

    return audio * amp * vel

def synth_rim_pro(duration=0.05, sr=SAMPLE_RATE):
    """Rimshot"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # High pitched click
    click = np.sin(2 * np.pi * 1500 * t) * 0.5
    click += np.sin(2 * np.pi * 2500 * t) * 0.3

    # Noise component - full length
    click_n = int(sr * 0.01)
    if click_n > 0 and click_n < n:
        noise_part = noise_burst(0.01, decay=200, sr=sr) * 0.2
        click[:click_n] += noise_part[:click_n]
    elif click_n > 0:
        noise_part = noise_burst(0.01, decay=200, sr=sr) * 0.2
        click[:min(len(noise_part), n)] += noise_part[:min(len(noise_part), n)]

    amp = create_envelope(n, attack=0.0005, decay=0.02, sustain=0, release=0.01, sr=sr)

    return click * amp

# ====== BAS SENTEZLEYICILERI ======

def synth_808_pro(freq=45, duration=1.0, decay=0.5, pitch_sweep=0.3, sr=SAMPLE_RATE):
    """808 tarzı kick/bass - profesyonel"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Pitch envelope with sweep
    pitch_curve = freq * (1 + pitch_sweep * np.exp(-t * 10))

    # Phase accumulation
    phase = np.cumsum(2 * np.pi * pitch_curve / sr)

    # Multiple oscillators
    sine = np.sin(phase)
    sine2 = np.sin(phase * 2)
    sine05 = np.sin(phase * 0.5)

    audio = sine * 0.5 + sine2 * 0.3 + sine05 * 0.2

    # Amplitude envelope
    amp = create_envelope(n, attack=0.001, decay=0.1 + decay * 0.3, sustain=0.4, release=0.3, sr=sr)

    # Tone
    audio = audio * amp

    # Saturation
    audio = soft_clip(audio, 0.7)

    return audio

def synth_sub_bass(freq, duration, sr=SAMPLE_RATE):
    """Pure sub bass"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    audio = np.sin(2 * np.pi * freq * t)
    env = create_envelope(n, attack=0.01, sustain=0.8, release=0.3, sr=sr)

    return audio * env

def synth_bass_pro(freq, duration, octave=1, filter_sweep=True, sr=SAMPLE_RATE):
    """Synth bass - profesyonel"""
    n = int(sr * duration)
    t = np.arange(n) / sr
    f = freq * octave

    # Multiple waveforms
    sine = np.sin(2 * np.pi * f * t)
    saw = 2 * (t * f - np.floor(t * f + 0.5))

    # Square with PWM effect
    pwm = 0.3 + 0.2 * np.sin(2 * np.pi * 0.5 * t)
    square = np.sign(np.sin(2 * np.pi * f * t + np.pi * pwm))

    audio = sine * 0.3 + saw * 0.4 + square * 0.3

    # Dynamic filter
    if filter_sweep:
        filter_env = create_envelope(n, attack=0.01, decay=0.15, sustain=0.3, release=0.2, sr=sr)
        cutoff_curve = 500 + filter_env * 3000
    else:
        cutoff_curve = np.ones(n) * 1500

    # Apply filter sample-by-sample
    filtered = np.zeros(n)
    for i in range(1, n):
        cutoff_norm = cutoff_curve[i] / (SAMPLE_RATE / 2)
        cutoff_norm = min(0.95, max(0.01, cutoff_norm))
        filtered[i] = filtered[i-1] + cutoff_norm * (audio[i] - filtered[i-1])

    # Amp envelope
    env = create_envelope(n, attack=0.01, decay=0.1, sustain=0.7, release=0.4, sr=sr)

    return filtered * env * 0.5

# ====== PAD & LEAD SENTEZLEYICILERI ======

def synth_pad_pro(freqs, duration, detune=0.003, sr=SAMPLE_RATE):
    """Zengin pad - gerçekçi"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    audio = np.zeros(n)

    for f in freqs:
        # Multiple detuned oscillators
        for dt in [-detune*2, -detune, 0, detune, detune*2, detune*8]:
            freq = f * (1 + dt)
            # Triangle for warmth
            phase = np.sin(2 * np.pi * freq * t)
            audio += phase * 0.05

    # Slow amplitude modulation (breathing)
    mod_rate = 0.3 + np.random.rand() * 0.2
    mod = 1 + np.sin(2 * np.pi * mod_rate * t) * 0.1

    # Envelope
    env = create_envelope(n, attack=0.5, decay=0.2, sustain=0.7, release=0.6, sr=sr)

    # Light reverb
    audio = conv_reverb(audio * mod * env, size=0.05, decay=0.5, sr=sr)

    return audio * 0.4

def synth_strings_pro(freq, duration, sr=SAMPLE_RATE):
    """String section - gerçekçi"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Saw wave
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))

    # Vibrato
    vibrato = 1 + np.sin(2 * np.pi * 5 * t) * 0.008
    vibrato += np.sin(2 * np.pi * 0.5 * t) * 0.002  # Slow drift

    phase = np.cumsum(2 * np.pi * freq * vibrato / sr) / (2 * np.pi)
    audio = np.sin(phase * 2 * np.pi)  # Resynth

    # Slow attack for realism
    env = create_envelope(n, attack=0.3, decay=0.1, sustain=0.8, release=0.5, sr=sr)

    # Warm filter
    audio = apply_lpf(audio, 3500)

    # Reverb
    audio = plate_reverb(audio, decay=0.4, mix=0.25, sr=sr)

    return audio * env * 0.3

def synth_piano_pro(freq, duration, velocity=0.7, sr=SAMPLE_RATE):
    """Basit piano sound"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple harmonics
    audio = np.sin(2 * np.pi * freq * t) * 1.0
    audio += np.sin(2 * np.pi * freq * 2 * t) * 0.5
    audio += np.sin(2 * np.pi * freq * 3 * t) * 0.25
    audio += np.sin(2 * np.pi * freq * 4 * t) * 0.125
    audio += np.sin(2 * np.pi * freq * 5 * t) * 0.06

    # Hammer noise (attack) - placed at start, full length
    hammer_n = min(int(sr * 0.01), n)
    hammer = np.zeros(n)
    if hammer_n > 0:
        hammer[:hammer_n] = noise_burst(0.01, decay=200, sr=sr) * 0.1 * velocity

    # Envelope
    env = create_envelope(n, attack=0.002, decay=0.3, sustain=0.3, release=0.4, sr=sr)

    # Combine
    audio = (audio + hammer) * env

    # Filter for warmth
    audio = apply_lpf(audio, 2500)

    return audio * velocity * 0.4

def synth_electric_piano(freq, duration, sr=SAMPLE_RATE):
    """Electric piano (Rhodes-style)"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple bells
    audio = np.sin(2 * np.pi * freq * t) * 0.6
    audio += np.sin(2 * np.pi * freq * 2 * t) * 0.25
    audio += np.sin(2 * np.pi * freq * 3.5 * t) * 0.15

    # Slight tremolo
    tremolo = 1 + np.sin(2 * np.pi * 5 * t) * 0.02

    # Envelope
    env = create_envelope(n, attack=0.01, decay=0.4, sustain=0.4, release=0.5, sr=sr)

    # Filter
    audio = apply_lpf(audio, 3000)

    return audio * tremolo * env * 0.35

def synth_organ_pro(freq, duration, sr=SAMPLE_RATE):
    """Organ - gerçekçi"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Drawbars
    audio = np.sin(2 * np.pi * freq * t) * 1.0
    audio += np.sin(2 * np.pi * freq * 2 * t) * 0.5
    audio += np.sin(2 * np.pi * freq * 3 * t) * 0.25
    audio += np.sin(2 * np.pi * freq * 4 * t) * 0.125
    audio += np.sin(2 * np.pi * freq * 6 * t) * 0.08
    audio += np.sin(2 * np.pi * freq * 8 * t) * 0.04

    # Slight detuning for chorus
    chorus = np.sin(2 * np.pi * freq * 1.003 * t) * 0.3
    chorus += np.sin(2 * np.pi * freq * 0.997 * t) * 0.3

    # Envelope
    env = create_envelope(n, attack=0.005, sustain=0.9, release=0.1, sr=sr)

    return (audio + chorus) * env * 0.25

def synth_brass_pro(freq, duration, sr=SAMPLE_RATE):
    """Brass section - gerçekçi"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Multiple oscillators
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))
    square = np.sign(np.sin(2 * np.pi * freq * t))

    audio = saw * 0.5 + square * 0.3 + np.sin(2 * np.pi * freq * t) * 0.2

    # Vibrato
    vibrato = 1 + np.sin(2 * np.pi * 6 * t) * 0.015
    audio = audio * vibrato

    # Envelope
    env = create_envelope(n, attack=0.08, decay=0.1, sustain=0.7, release=0.3, sr=sr)

    # Filter
    audio = apply_lpf(audio, 4000)

    return audio * env * 0.3

def synth_lead_pro(freq, duration, sr=SAMPLE_RATE):
    """Lead synth - kaliteli"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Supersaw with more oscillators
    audio = np.zeros(n)
    detunes = [-0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06, 0.08]
    for dt in detunes:
        f = freq * (1 + dt)
        saw = 2 * (t * f - np.floor(t * f + 0.5))
        audio += saw

    audio = audio / len(detunes)

    # Filter envelope
    filter_env = create_envelope(n, attack=0.15, decay=0.2, sustain=0.4, release=0.5, sr=sr)
    cutoff_curve = 800 + filter_env * 4000

    # Apply filter
    filtered = np.zeros(n)
    for i in range(1, n):
        cutoff_norm = cutoff_curve[i] / (SAMPLE_RATE / 2)
        cutoff_norm = min(0.9, max(0.05, cutoff_norm))
        filtered[i] = filtered[i-1] + cutoff_norm * (audio[i] - filtered[i-1])

    # Amp envelope
    env = create_envelope(n, attack=0.1, decay=0.1, sustain=0.6, release=0.5, sr=sr)

    # Light reverb
    filtered = plate_reverb(filtered * env, decay=0.2, mix=0.15, sr=sr)

    return filtered * 0.4

def synth_pluck_pro(freq, duration, sr=SAMPLE_RATE):
    """Plucked string - gerçekçi"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Karplus-Strong inspired
    period = int(sr / freq)
    audio = np.zeros(n)

    # Initial noise burst
    noise_len = min(int(0.003 * sr), n)
    audio[:noise_len] = np.random.randn(noise_len)

    # Recursive filter
    for i in range(noise_len, n):
        audio[i] = audio[i-1] + 0.997 * (audio[i-1] - audio[i-2])
        audio[i] *= 0.999

    # Add sine component
    sine = np.sin(2 * np.pi * freq * t)
    audio = audio * 0.4 + sine * 0.6

    # Envelope
    env = create_envelope(n, attack=0.002, decay=0.1, sustain=0.3, release=0.4, sr=sr)

    return audio * env * 0.45

# ====== EFECTLER ======

def sidechain_compress(audio, trigger_times, threshold=0.35, ratio=4, attack=0.001, release=0.1, sr=SAMPLE_RATE):
    """Sidechain compression"""
    result = audio.copy()

    for kt in trigger_times:
        start = int(kt * sr)
        env_len = int(release * sr)
        end = min(start + env_len, len(audio))
        if start < len(audio):
            env = create_envelope(end - start, attack=attack, decay=0, sustain=0, release=release * 0.5, sr=sr)
            amount = threshold + (1 - threshold) * (1 - env * ratio)
            amount = np.clip(amount, 0.05, 1)
            result[start:end] *= amount

    return result

def add_delay(audio, delay_time=0.25, feedback=0.3, mix=0.3, sr=SAMPLE_RATE):
    """Simple delay effect"""
    delay_samples = int(delay_time * sr)
    output = audio.copy()

    for i in range(3):  # Multiple delays
        delayed = np.zeros_like(audio)
        offset = delay_samples * (i + 1)
        if offset < len(audio):
            delayed[offset:] = audio[:-offset] * (feedback ** (i + 1))
            output += delayed

    return audio * (1 - mix) + output * mix

def master_bus(audio, threshold=0.6, ratio=3):
    """Master compression and limiting"""
    # Soft clip
    audio = soft_clip(audio, threshold)

    # Normalize
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.9

    return audio

# ====== MUZIK TASARIMI ======

def create_groovy_hiphop():
    """Groovy hip-hop - 68 sn"""
    bpm = 92
    duration = 68
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    # Kicks with swing
    kick_times = []
    for bar in range(int(duration / bar_dur)):
        for i, offset in enumerate([0, 0.55, 2.4, 3]):
            t = bar * bar_dur + offset * beat_dur
            kick_times.append(t)
            start = int(t * SAMPLE_RATE)
            if start < samples:
                k = synth_kick_pro(pitch_start=160, pitch_end=45, duration=0.35)
                safe_add(audio, start, k, 0.9)

    # Snare with variations
    for bar in range(int(duration / bar_dur)):
        for beat in [1, 3]:
            t = bar * bar_dur + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                s = synth_snare_pro(tune=195 + np.random.randint(-5, 5))
                safe_add(audio, start, s, 0.7)

        # Ghost snare
        if bar % 2 == 0:
            t = bar * bar_dur + 2.75 * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                s = synth_snare_pro(tune=200) * 0.4
                safe_add(audio, start, s, 1.0)

    # Hi-hats with groove
    for bar in range(int(duration / (bar_dur / 4))):
        for i in range(4):
            t = bar * (bar_dur / 4) + i * (bar_dur / 16)
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            # Velocity variation
            vel = 0.35 if i == 0 else (0.2 if i == 2 else 0.25)
            vel *= (0.9 + np.random.rand() * 0.2)

            open_hat = (i == 3 and bar % 2 == 1)
            h = synth_hihat_pro(open=open_hat, vel=vel, decay_time=0.08 if not open_hat else 0.2)
            safe_add(audio, start, h, 1.0)

    # Bass - melodic and musical
    bass_notes = [
        (55, 0), (55, 1), (58, 2), (60, 3),
        (55, 4), (55, 5), (58, 5.5), (62, 6.5),
        (55, 8), (55, 9), (58, 10), (60, 11),
        (65, 12), (62, 13), (58, 14), (55, 15),
    ]

    for bar in range(int(duration / (bar_dur * 4))):
        for freq, beat in bass_notes:
            t = bar * bar_dur * 4 + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                bass = synth_bass_pro(freq, beat_dur * 0.9)
                safe_add(audio, start, bass, 0.5)

                sub = synth_sub_bass(freq / 2, beat_dur * 0.85)
                safe_add(audio, start, sub, 0.4)

    # Chords - rich and warm
    chords = [
        (130.81, 164.81, 196.00, 246.94),  # Cmaj9
        (146.83, 174.61, 220.00, 261.63),  # Dm9
        (123.47, 155.56, 196.00, 246.94),  # Bbmaj7
        (116.54, 146.83, 174.61, 220.00),  # Am7
    ]

    for bar in range(int(duration / bar_dur)):
        chord = chords[bar % len(chords)]
        start = int(bar * bar_dur * SAMPLE_RATE)

        # Pad
        pad = synth_pad_pro(chord[:3], bar_dur * 0.9)
        safe_add(audio, start, pad, 0.35)

        # Electric piano
        for i, note in enumerate(chord[:2]):
            t = bar * bar_dur + i * beat_dur * 0.5
            note_start = int(t * SAMPLE_RATE)
            if note_start < samples:
                ep = synth_electric_piano(note, beat_dur * 0.4)
                safe_add(audio, note_start, ep, 0.25)

        # Strings every 4 bars
        if bar % 4 == 0:
            strings = synth_strings_pro(chord[0], bar_dur * 3.8)
            safe_add(audio, start, strings, 0.2)

    # Lead melody - soulful
    melody = [
        (392, 0.5), (440, 0.5), (523, 0.5), (587, 0.5),
        (523, 1.0), (494, 0.5), (440, 0.5),
        (392, 0.75), (440, 0.25), (523, 0.5), (587, 0.5),
        (659, 1.0), (523, 0.5), (494, 0.5),
    ]

    offset = 0
    for phrase in range(2):
        for freq, dur in melody:
            t = phrase * 16 * beat_dur + offset
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            lead = synth_lead_pro(freq, dur * 0.92)
            safe_add(audio, start, lead, 0.3)
            offset += dur

        offset += 8 * beat_dur

    # Pluck accents
    for bar in range(int(duration / (bar_dur * 2))):
        notes = [659, 587, 523, 494]
        for i, note in enumerate(notes):
            t = bar * bar_dur * 2 + i * beat_dur * 0.25
            start = int(t * SAMPLE_RATE)
            if start < samples:
                pluck = synth_pluck_pro(note, 0.2)
                safe_add(audio, start, pluck, 0.2)

    # Apply sidechain to pads
    audio = sidechain_compress(audio, kick_times, threshold=0.4)

    # Master
    audio = master_bus(audio)

    return audio

def create_deep_techno():
    """Deep techno - 65 sn"""
    bpm = 124
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
            k = synth_kick_pro(pitch_start=200, pitch_end=40, duration=0.4)
            safe_add(audio, start, k, 1.0)

    # Percussion - sparse
    for bar in range(int(duration / (bar_dur * 4))):
        bar_start = bar * 4 * bar_dur

        # Snare
        t = bar_start + 2.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare_pro(tune=180) * 0.7
            safe_add(audio, start, s, 1.0)

        # Clap
        t = bar_start + 2.55 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap_pro()
            safe_add(audio, start, c, 0.5)

        # Rimshot
        for beat in [0.5, 1.5, 3.5]:
            t = bar_start + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                r = synth_rim_pro()
                safe_add(audio, start, r, 0.35)

    # Hi-hats
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        vel = 0.4 if (t % beat_dur) < 0.01 else 0.28
        open_hat = (t % (beat_dur * 2)) < 0.01
        h = synth_hihat_pro(open=open_hat, vel=vel, decay_time=0.1 if not open_hat else 0.25)
        safe_add(audio, start, h, 1.0)

    # Acid bass
    acid_notes = [55, 55, 73, 55, 65, 55, 73, 82]
    step = beat_dur / 4

    for bar in range(int(duration / (bar_dur * 4))):
        for i, note in enumerate(acid_notes):
            t = bar * bar_dur * 4 + i * step
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            bass = synth_bass_pro(note, step * 0.85, filter_sweep=True)
            safe_add(audio, start, bass, 0.45)

    # Atmospheric pads
    pad_chords = [
        [73, 98, 110, 146],
        [65, 87, 110, 146],
        [82, 110, 146, 174],
        [58, 82, 110, 146],
    ]

    for section in range(int(duration / 16)):
        chord = pad_chords[section % len(pad_chords)]
        start = int(section * 16 * SAMPLE_RATE)
        pad = synth_pad_pro(chord, 15.5, detune=0.004)
        safe_add(audio, start, pad, 0.4)

    # String accents
    for section in range(int(duration / 8)):
        if section >= 1:
            start = int(section * 8 * SAMPLE_RATE)
            freq = [196, 220, 246, 293][section % 4]
            strings = synth_strings_pro(freq, 7.5)
            safe_add(audio, start, strings, 0.25)

    # Riser
    for bar in range(int(duration / (bar_dur * 16))):
        if bar >= 2:
            riser_start = int((bar * 16 + 14.5) * beat_dur * SAMPLE_RATE)
            if riser_start < samples:
                n = int(beat_dur * 1.5 * SAMPLE_RATE)
                t = np.arange(n) / SAMPLE_RATE
                riser = noise_burst(beat_dur * 1.5, decay=2, sr=SAMPLE_RATE)
                riser_env = create_envelope(n, attack=0.2, decay=0, sustain=1, release=0, sr=SAMPLE_RATE)
                riser = apply_lpf(riser, 3000 * (t / t[-1]))  # Sweeping filter
                safe_add(audio, riser_start, riser * riser_env, 0.4)

    audio = sidechain_compress(audio, kick_times, threshold=0.3, ratio=5)
    audio = master_bus(audio)

    return audio

def create_modern_trap():
    """Modern trap - 66 sn"""
    bpm = 140
    duration = 66
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    # Heavy 808s
    for bar in range(int(duration / bar_dur)):
        for beat in [0, 1, 2, 3]:
            t = bar * bar_dur + beat * beat_dur
            kick_times.append(t)
            start = int(t * SAMPLE_RATE)
            if start < samples:
                k = synth_808_pro(38, 0.9, decay=0.5, pitch_sweep=0.4)
                safe_add(audio, start, k, 0.85)

    # Snare
    for bar in range(int(duration / (bar_dur * 2))):
        t = bar * bar_dur * 2 + 2.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare_pro(tune=210)
            safe_add(audio, start, s, 0.75)

        t = bar * bar_dur * 2 + 6.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare_pro(tune=205)
            safe_add(audio, start, s, 0.7)

    # Claps
    for bar in range(int(duration / (bar_dur * 2))):
        t = bar * bar_dur * 2 + 2.55 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap_pro()
            safe_add(audio, start, c, 0.6)

        t = bar * bar_dur * 2 + 6.55 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_clap_pro()
            safe_add(audio, start, c, 0.55)

    # Hi-hats
    for bar in range(int(duration / (bar_dur / 4))):
        for i in range(4):
            t = bar * (bar_dur / 4) + i * (bar_dur / 16)
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            vel = 0.4 if i % 4 == 0 else 0.22
            h = synth_hihat_pro(vel=vel, decay_time=0.06)
            safe_add(audio, start, h, 1.0)

    # Dark bass
    bass_notes = [36, 0, 41, 38, 36, 43, 41, 38, 36, 0, 41, 36, 43, 45, 48, 43]
    step = beat_dur

    for bar in range(int(duration / (bar_dur * 4))):
        for i, note in enumerate(bass_notes):
            if note > 0:
                t = bar * bar_dur * 4 + i * step
                start = int(t * SAMPLE_RATE)
                if start < samples:
                    bass = synth_bass_pro(note, step * 0.9)
                    safe_add(audio, start, bass, 0.55)

                    sub = synth_sub_bass(note / 2, step * 0.85)
                    safe_add(audio, start, sub, 0.5)

    # Dark minor chords
    dark_chords = [
        (155.56, 185.00, 232.00, 293.66),  # Eb minor
        (138.59, 174.61, 207.65, 261.63),  # Db minor
        (146.83, 174.61, 220.00, 277.18),   # D minor
        (130.81, 164.81, 196.00, 246.94),  # C minor
    ]

    for bar in range(int(duration / bar_dur)):
        chord = dark_chords[bar % len(dark_chords)]
        start = int(bar * bar_dur * SAMPLE_RATE)

        pad = synth_pad_pro(chord[:3], bar_dur * 0.9)
        safe_add(audio, start, pad, 0.35)

    # Brass stabs
    stab_times = [0, 2, 4, 6, 8, 10, 12, 14]
    for bar in range(int(duration / (bar_dur * 8))):
        for offset in stab_times:
            if offset < 16:
                t = bar * bar_dur * 8 + offset * beat_dur
                start = int(t * SAMPLE_RATE)
                if start < samples:
                    stab = synth_brass_pro(311, 0.2)
                    safe_add(audio, start, stab, 0.3)

    # 808 sub effect on beat 1
    for bar in range(int(duration / (bar_dur * 4))):
        t = bar * bar_dur * 4
        start = int(t * SAMPLE_RATE)
        if start < samples:
            sub_hit = synth_sub_bass(28, beat_dur * 2)
            safe_add(audio, start, sub_hit, 0.4)

    audio = sidechain_compress(audio, kick_times, threshold=0.25, ratio=6)
    audio = master_bus(audio)

    return audio

def create_soulful_beat():
    """Soul/R&B tarzi - 68 sn"""
    bpm = 78
    duration = 68
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    # Soft kicks
    for bar in range(int(duration / bar_dur)):
        for beat in [0, 2.5]:
            t = bar * bar_dur + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                k = synth_kick_pro(pitch_start=120, pitch_end=50, duration=0.3) * 0.75
                safe_add(audio, start, k, 1.0)

    # Snare
    for bar in range(int(duration / bar_dur)):
        for beat in [1, 3]:
            t = bar * bar_dur + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                s = synth_snare_pro(tune=190)
                safe_add(audio, start, s, 0.65)

        # Ghost snare
        t = bar * bar_dur + 1.75 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare_pro(tune=195) * 0.35
            safe_add(audio, start, s, 1.0)

    # Soft hi-hats
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        vel = 0.25 if t % beat_dur < 0.01 else 0.15
        h = synth_hihat_pro(vel=vel, decay_time=0.05)
        safe_add(audio, start, h, 1.0)

    # Bass - smooth and melodic
    bass_pattern = [
        (82, 0, 2), (82, 2, 3), (87, 3, 4),
        (82, 4, 6), (87, 6, 7), (92, 7, 8),
        (87, 8, 10), (82, 10, 11), (77, 11, 12),
        (82, 12, 14), (87, 14, 15), (92, 15, 16),
    ]

    for bar in range(int(duration / (bar_dur * 4))):
        for freq, st, en in bass_pattern:
            t = bar * bar_dur * 4 + st * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                dur = (en - st) * beat_dur
                bass = synth_bass_pro(freq, dur, filter_sweep=False)
                safe_add(audio, start, bass, 0.45)

    # Chords - rich
    chords = [
        (261.63, 329.63, 392.00, 493.88),  # Cmaj7
        (293.66, 349.23, 440.00, 523.25),  # Dm9
        (220.00, 277.18, 329.63, 392.00),  # Am7
        (246.94, 311.13, 369.99, 493.88),   # Bm7
    ]

    for bar in range(int(duration / (bar_dur / 2))):
        chord = chords[bar % len(chords)]
        start = int(bar * (bar_dur / 2) * SAMPLE_RATE)

        # Pad
        pad = synth_pad_pro(chord[:3], bar_dur * 1.8)
        safe_add(audio, start, pad, 0.3)

        # Piano chords
        for i, note in enumerate(chord[:3]):
            t = bar * (bar_dur / 2) + i * beat_dur * 0.5
            note_start = int(t * SAMPLE_RATE)
            if note_start < samples:
                piano = synth_piano_pro(note, beat_dur * 0.45)
                safe_add(audio, note_start, piano, 0.25)

        # Organ
        if bar % 2 == 0:
            organ = synth_organ_pro(chord[0] / 2, bar_dur * 0.9)
            safe_add(audio, start, organ, 0.2)

    # Strings
    for bar in range(int(duration / (bar_dur * 4))):
        if bar >= 1:
            chord_freqs = [261.63, 329.63, 392.00]
            start = int(bar * bar_dur * 4 * SAMPLE_RATE)
            strings = synth_strings_pro(chord_freqs[bar % len(chord_freqs)], bar_dur * 3.5)
            safe_add(audio, start, strings, 0.25)

    # Melody
    melody = [
        (523, 0.75), (587, 0.5), (659, 0.5), (587, 0.75),
        (523, 0.5), (494, 0.5), (523, 0.5), (659, 0.5),
        (587, 0.75), (523, 0.5), (494, 0.5), (440, 1.0),
    ]

    offset = 0
    for phrase in range(2):
        for freq, dur in melody:
            t = phrase * 20 * beat_dur + offset
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            lead = synth_lead_pro(freq, dur * 0.92)
            safe_add(audio, start, lead, 0.25)
            offset += dur

        offset += 12 * beat_dur

    # Light mastering
    audio = master_bus(audio)

    return audio

def create_afrobeats_vibes():
    """Afrobeats tarzi - 65 sn"""
    bpm = 108
    duration = 65
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    # Soft kicks
    for t in np.arange(0, duration, beat_dur):
        start = int(t * SAMPLE_RATE)
        if start < samples:
            k = synth_kick_pro(pitch_start=140, pitch_end=48, duration=0.25) * 0.8
            safe_add(audio, start, k, 1.0)

    # Skip beat
    for bar in range(int(duration / (bar_dur * 2))):
        t = bar * bar_dur * 2 + 2.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            k = synth_kick_pro(pitch_start=100, pitch_end=45, duration=0.15) * 0.6
            safe_add(audio, start, k, 1.0)

    # Snare
    for bar in range(int(duration / bar_dur)):
        t = bar * bar_dur + 2.5 * beat_dur
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare_pro(tune=200)
            safe_add(audio, start, s, 0.6)

    # Shakers
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        vel = 0.25 if t % beat_dur < 0.01 else 0.18
        h = synth_hihat_pro(vel=vel, decay_time=0.04)
        safe_add(audio, start, h, 1.0)

    # Log drum / percussion
    for bar in range(int(duration / (bar_dur * 2))):
        for beat in [1, 3]:
            t = bar * bar_dur * 2 + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                log = synth_pluck_pro(440, 0.1)
                safe_add(audio, start, log, 0.4)

    # Bass - melodic
    bass_notes = [
        (110, 0, 2), (123, 2, 3), (131, 3, 4),
        (110, 4, 6), (123, 6, 7), (131, 7, 8),
    ]

    for bar in range(int(duration / (bar_dur * 4))):
        for freq, st, en in bass_notes:
            t = bar * bar_dur * 4 + st * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                dur = (en - st) * beat_dur
                bass = synth_bass_pro(freq, dur)
                safe_add(audio, start, bass, 0.45)

    # Afrobeats chords - major with 7th
    chords = [
        (261.63, 329.63, 392.00, 493.88),  # Cmaj7
        (293.66, 369.99, 440.00, 523.25),  # Dmaj7
        (293.66, 349.23, 440.00, 523.25),  # D7
        (246.94, 311.13, 392.00, 493.88),  # Bm7
    ]

    for bar in range(int(duration / (bar_dur / 2))):
        chord = chords[bar % len(chords)]
        start = int(bar * (bar_dur / 2) * SAMPLE_RATE)

        # Pad
        pad = synth_pad_pro(chord[:3], bar_dur * 0.9)
        safe_add(audio, start, pad, 0.35)

        # Piano arpeggio
        for i, note in enumerate(chord[:3]):
            t = bar * (bar_dur / 2) + i * beat_dur * 0.5
            note_start = int(t * SAMPLE_RATE)
            if note_start < samples:
                piano = synth_piano_pro(note, beat_dur * 0.35)
                safe_add(audio, note_start, piano, 0.25)

    # Lead melody
    melody = [
        (523, 0.5), (587, 0.5), (659, 0.5), (523, 0.5),
        (494, 0.5), (523, 1.0), (587, 0.5),
        (659, 0.5), (698, 0.5), (659, 1.0),
    ]

    offset = 0
    for phrase in range(3):
        for freq, dur in melody:
            t = phrase * 12 * beat_dur + offset
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            lead = synth_lead_pro(freq, dur * 0.9)
            safe_add(audio, start, lead, 0.3)
            offset += dur

        offset += 4 * beat_dur

    # Pluck accents
    for bar in range(int(duration / bar_dur)):
        notes = [784, 659, 587, 523]
        for i, note in enumerate(notes):
            t = bar * bar_dur + i * beat_dur * 0.25
            start = int(t * SAMPLE_RATE)
            if start < samples:
                pluck = synth_pluck_pro(note, 0.15)
                safe_add(audio, start, pluck, 0.2)

    audio = master_bus(audio)

    return audio

def create_dark_ambient():
    """Dark ambient techno - 70 sn"""
    bpm = 100
    duration = 70
    bar_dur = 60 / bpm * 4

    samples = int(SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)
        start = int(t * SAMPLE_RATE)
        if start < samples:
            k = synth_kick_pro(pitch_start=180, pitch_end=35, duration=0.5) * 1.1
            safe_add(audio, start, k, 1.0)

    # Sparse percussion
    for bar in range(int(duration / (bar_dur * 8))):
        if bar % 2 == 1:
            bar_start = bar * 8 * bar_dur

            # Snare
            t = bar_start + 2.5 * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                s = synth_snare_pro(tune=160) * 0.6
                safe_add(audio, start, s, 1.0)

            # Clap
            t = bar_start + 2.6 * beat_dur
            start = int(t * SAMPLE_RATE)
            if start < samples:
                c = synth_clap_pro()
                safe_add(audio, start, c, 0.5)

    # Hi-hats
    for t in np.arange(0, duration, beat_dur / 2):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        vel = 0.3 if (t % (beat_dur * 2)) < 0.01 else 0.2
        h = synth_hihat_pro(open=(t % beat_dur < 0.01), vel=vel, decay_time=0.15)
        safe_add(audio, start, h, 1.0)

    # Sub bass drone
    for t in np.arange(0, duration, bar_dur * 2):
        start = int(t * SAMPLE_RATE)
        if start < samples:
            sub = synth_sub_bass(41, bar_dur * 1.8)
            safe_add(audio, start, sub, 0.5)

    # Dark pads - evolving
    dark_chords = [
        [55, 82, 110, 138],
        [51, 77, 103, 138],
        [58, 87, 116, 155],
        [46, 69, 92, 123],
    ]

    for section in range(int(duration / 16)):
        chord = dark_chords[section % len(dark_chords)]
        start = int(section * 16 * SAMPLE_RATE)

        # Multiple pad layers
        pad1 = synth_pad_pro(chord[:2], 15.5, detune=0.002)
        safe_add(audio, start, pad1, 0.4)

        # Higher octave
        pad2 = synth_pad_pro([c * 2 for c in chord[:2]], 15.5, detune=0.003)
        safe_add(audio, start, pad2, 0.2)

    # Ethereal strings
    for section in range(int(duration / 8)):
        start = int(section * 8 * SAMPLE_RATE)
        freq = [138, 155, 174, 185][section % 4]
        strings = synth_strings_pro(freq, 7.5)
        safe_add(audio, start, strings, 0.25)

    # Occasional risers
    for bar in range(int(duration / (bar_dur * 16))):
        if bar >= 1:
            riser_start = int((bar * 16 + 15) * beat_dur * SAMPLE_RATE)
            if riser_start < samples:
                n = int(beat_dur * SAMPLE_RATE)
                t_arr = np.arange(n) / SAMPLE_RATE
                riser = noise_burst(beat_dur, decay=1.5, sr=SAMPLE_RATE)
                riser_env = create_envelope(n, attack=0.3, decay=0, sustain=1, release=0, sr=SAMPLE_RATE)
                riser = riser * riser_env
                safe_add(audio, riser_start, riser, 0.35)

    audio = sidechain_compress(audio, kick_times, threshold=0.25, ratio=5)
    audio = master_bus(audio)

    return audio

# ====== MAIN ======
if __name__ == "__main__":
    print("[*] Muzikler olusturuluyor (v3 - Gercekci)...")
    print("=" * 50)

    tracks = [
        ("bg_groovy_hiphop.mp3", create_groovy_hiphop),
        ("bg_deep_techno.mp3", create_deep_techno),
        ("bg_modern_trap.mp3", create_modern_trap),
        ("bg_soulful_beat.mp3", create_soulful_beat),
        ("bg_afrobeats.mp3", create_afrobeats_vibes),
        ("bg_dark_ambient.mp3", create_dark_ambient),
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