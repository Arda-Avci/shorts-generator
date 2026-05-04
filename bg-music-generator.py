"""
Professional Shorts Background Music Generator
Hip-hop / Techno-Trance Tarzı, Sürükleyici Ritimler
"""
import numpy as np
from scipy.io import wavfile
import os
import struct

SAMPLE_RATE = 44100
OUTPUT_DIR = r"c:\users\Damla\Proje\Muhabbet\shorts-generator\bg-music"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_as_mp3(data, filename, bitrate=320):
    """WAV oluştur, mp3'e cevir"""
    wav_path = os.path.join(OUTPUT_DIR, filename.replace('.mp3', '.wav'))
    mp3_path = os.path.join(OUTPUT_DIR, filename)

    # Normalize and apply soft clipping
    data = data / np.max(np.abs(data)) * 0.85
    data = np.tanh(data * 1.5) * 0.85  # Soft saturation
    data = np.int16(data * 32767)

    wavfile.write(wav_path, SAMPLE_RATE, data)
    os.system('ffmpeg -y -i "{0}" -b:a {1}k -ar 44100 "{2}" 2>nul'.format(wav_path, bitrate, mp3_path))
    os.remove(wav_path)
    print("[+] {0}".format(filename))

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

def soft_clip(x, threshold=0.8):
    """Soft clipping distortion"""
    return np.tanh(x / threshold) * threshold

def safe_add(audio, start, data, max_len=None):
    """Safely add audio data at position, handling length mismatches"""
    if start >= len(audio):
        return
    if max_len is None:
        max_len = len(audio) - start
    end = min(start + len(data), start + max_len, len(audio))
    actual_len = end - start
    if actual_len > 0:
        audio[start:end] += data[:actual_len]

# ====== SES KAYNAKLARI ======

def synth_808(freq=45, duration=1.0, decay=0.5, sr=SAMPLE_RATE):
    """808 tarzı kick/bass -gercekci"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Pitch envelope - duseyen
    pitch_env = np.exp(-t * 15)
    pitch = freq * (1 + pitch_env * 3)  # Baslangicta yuksek, sonra dusuk

    # Amplitude envelope
    amp = np.exp(-t * (3 + decay * 10))

    # Synthesize
    phase = np.cumsum(2 * np.pi * pitch / sr)
    sine1 = np.sin(phase)
    sine2 = np.sin(phase * 2) * 0.3  # Harmonic
    sine3 = np.sin(phase * 0.5) * 0.2  # Sub

    audio = (sine1 + sine2 + sine3) * amp

    # Saturation
    audio = soft_clip(audio, 0.6)

    return audio

def synth_kick(freq=60, duration=0.3, sr=SAMPLE_RATE):
    """Dusuk frekansli kick"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Pitch drop
    pitch_env = np.exp(-t * 25)
    freq_env = freq * (4 + pitch_env * 10)

    # Phase accumulation
    phase = np.cumsum(2 * np.pi * freq_env / sr)

    # Sine with envelope
    amp = np.exp(-t * 8)
    audio = np.sin(phase) * amp

    # Sub layer
    sub = np.sin(2 * np.pi * 30 * t) * np.exp(-t * 15)

    return (audio * 0.6 + sub * 0.4) * 0.9

def synth_snare(duration=0.3, sr=SAMPLE_RATE):
    """Gercekci snare"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Noise component
    noise = np.random.randn(n)

    # Tonal component
    tone_freq = 200
    tone = np.sin(2 * np.pi * tone_freq * t)
    tone += np.sin(2 * np.pi * tone_freq * 1.5 * t) * 0.5

    # Combined
    audio = noise * 0.6 + tone * 0.4
    amp = np.exp(-t * 15)
    return audio * amp

def synth_hihat(open=False, sr=SAMPLE_RATE):
    """Zengin hi-hat"""
    duration = 0.08 if not open else 0.2
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Noise with filtering
    noise = np.random.randn(n)
    filtered = np.zeros(n)
    for i in range(1, n):
        filtered[i] = filtered[i-1] + 0.7 * (noise[i] - filtered[i-1])

    # Metallic component
    metallic = np.sin(2 * np.pi * 8000 * t) * 0.3
    metallic += np.sin(2 * np.pi * 10000 * t) * 0.2

    audio = filtered * 0.7 + metallic * 0.3
    amp = np.exp(-t * (30 if not open else 12))

    return audio * amp

def synth_bass(freq, duration, octave=1, sr=SAMPLE_RATE):
    """Synth bass"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    f = freq * octave

    # Multiple oscillators
    saw = 2 * (t * f - np.floor(t * f + 0.5))
    sine = np.sin(2 * np.pi * f * t)

    audio = saw * 0.3 + sine * 0.7

    # Filter envelope
    filter_env = create_envelope(n, attack=0.01, decay=0.1, sustain=0.3, release=0.2, sr=sr)

    return audio * 0.4

def synth_pad(freqs, duration, sr=SAMPLE_RATE):
    """Atmosferik pad"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    audio = np.zeros(n)
    for f in freqs:
        # Detuned oscillators
        for detune in [-0.02, 0, 0.02]:
            audio += np.sin(2 * np.pi * f * (1 + detune) * t) * 0.1

    # Slow amplitude modulation
    mod = 1 + np.sin(2 * np.pi * 0.5 * t) * 0.1

    return audio * mod

def synth_lead(freq, duration, sr=SAMPLE_RATE):
    """Lead synth"""
    n = int(sr * duration)
    t = np.arange(n) / sr

    # Saw wave with filter
    saw = 2 * (t * freq - np.floor(t * freq + 0.5))

    # Simple lowpass
    filtered = np.zeros(n)
    cutoff = 0.3
    for i in range(1, n):
        filtered[i] = filtered[i-1] + cutoff * (saw[i] - filtered[i-1])

    # Envelope
    env = create_envelope(n, attack=0.1, decay=0.1, sustain=0.6, release=0.4, sr=sr)

    return filtered * env

def sidechain_comp(audio, kick_times, threshold=0.3, ratio=4, sr=SAMPLE_RATE):
    """Sidechain compression simulation"""
    result = audio.copy()

    for kt in kick_times:
        start = int(kt * sr)
        env_len = int(0.15 * sr)
        end = min(start + env_len, len(audio))
        if start < len(audio):
            chunk = audio[start:end]
            env = create_envelope(len(chunk), attack=0.001, decay=0.05, sustain=0, release=0.1, sr=sr)
            amount = threshold + (1 - threshold) * (1 - env * ratio)
            amount = np.clip(amount, 0.1, 1)
            result[start:end] = chunk * amount

    return result

# ====== MUZIK TASARIMLARI ======

def create_hiphop_bounce():
    """90'lara selam, modern production"""
    bpm = 92
    duration = 55
    bar_dur = 60 / bpm * 4  # 4 beat = 1 bar

    samples = int(sr := SAMPLE_RATE) * duration
    audio = np.zeros(samples)

    # BPM-synchronized timing
    beat_dur = 60 / bpm

    # Pattern: Kick on 1, Snare on 2.5, 3, 3.5
    kick_times = []
    snare_times = []
    hihat_times = []

    for t in np.arange(0, duration, beat_dur):
        beat_in_bar = (t / beat_dur) % 4

        if beat_in_bar < 0.1:
            kick_times.append(t)
        elif beat_in_bar in [1.5, 2, 2.5]:
            snare_times.append(t)

        # Hi-hats on 8ths
        hihat_times.append(t)
        hihat_times.append(t + beat_dur * 0.5)

    # Build drums
    for kt in kick_times:
        start = int(kt * SAMPLE_RATE)
        k = synth_808(45, 0.8, decay=0.4)
        l = min(len(k), samples - start)
        audio[start:start+l] += k[:l] * 0.85

    for st in snare_times:
        start = int(st * SAMPLE_RATE)
        s = synth_snare(0.2)
        l = min(len(s), samples - start)
        audio[start:start+l] += s[:l] * 0.7

    for ht in hihat_times:
        start = int(ht * SAMPLE_RATE)
        h = synth_hihat(open=(ht % (beat_dur * 2) < 0.1))
        l = min(len(h), samples - start)
        audio[start:start+l] += h[:l] * 0.4

    # Bass line - 2-bar pattern
    bass_notes = [
        (36, 0, bar_dur),      # Bar 1
        (36, bar_dur, bar_dur * 2),
        (38, bar_dur * 2, bar_dur * 3),
        (41, bar_dur * 3, bar_dur * 4),
    ]

    for freq, start_t, end_t in bass_notes:
        start = int(start_t * SAMPLE_RATE)
        dur = end_t - start_t
        b = synth_bass(freq, dur, octave=1)
        l = min(len(b), samples - start)
        audio[start:start+l] += b[:l] * 0.5

    # Chords - slow evolving
    chord_prog = [
        (130.81, 164.81, 196.00),  # C minor
        (146.83, 174.61, 220.00),  # D minor
        (130.81, 155.56, 196.00),  # Eb
        (123.47, 155.56, 185.00),  # Ab
    ]

    chord_dur = bar_dur * 2
    for i, (c1, c2, c3) in enumerate(chord_prog):
        start = int(i * chord_dur * SAMPLE_RATE)
        pad = synth_pad([c1, c2, c3], chord_dur * 0.9)
        l = min(len(pad), samples - start)
        audio[start:start+l] += pad[:l] * 0.25

    # Lead melody - catchy hook
    melody = [
        (392, 0.375), (440, 0.375), (523, 0.375),
        (392, 0.25), (349, 0.5),
        (330, 0.375), (392, 0.375), (440, 0.75),
    ]

    offset = 0
    for i in range(6):  # 6 repeats
        for freq, dur in melody:
            start = int(offset * SAMPLE_RATE)
            lead = synth_lead(freq, dur * 0.95)
            l = min(len(lead), samples - start)
            if l > 0:
                audio[start:start+l] += lead[:l] * 0.25
            offset += dur
            if offset > duration:
                break
        if offset > duration:
            break

    # Sidechain
    audio = sidechain_comp(audio, kick_times)

    return audio

def create_techno_thumper():
    """Karanlik, surukleyici techno"""
    bpm = 128
    duration = 58

    samples = int(sr := SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    # 4/4 kick on every beat
    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)

    for kt in kick_times:
        start = int(kt * SAMPLE_RATE)
        k = synth_kick(55, 0.25)
        l = min(len(k), samples - start)
        audio[start:start+l] += k[:l]

    # Percussion variation
    for bar in range(int(duration / (beat_dur * 4))):
        bar_start = bar * 4 * beat_dur

        # Snare on 3
        st = bar_start + 2 * beat_dur
        start = int(st * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.15)
            l = min(len(s), samples - start)
            audio[start:start+l] += s[:l] * 0.6

        # Clap-like on 3.5
        ct = bar_start + 2.5 * beat_dur
        start = int(ct * SAMPLE_RATE)
        if start < samples:
            c = synth_snare(0.1) * 0.5
            l = min(len(c), samples - start)
            audio[start:start+l] += c[:l]

    # Hi-hats - 16ths
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        # Velocity variation
        vel = 0.3 if (t % (beat_dur)) < 0.01 else 0.2
        open_hat = (t % (beat_dur * 2)) < 0.01

        h = synth_hihat(open=open_hat)
        l = min(len(h), samples - start)
        audio[start:start+l] += h[:l] * vel

    # Acid bass line
    acid_notes = [55, 55, 73, 55, 65, 55, 73, 82]
    step = beat_dur / 4

    for bar in range(int(duration / (beat_dur * 2))):
        for i, note in enumerate(acid_notes):
            t = bar * 2 * beat_dur + i * step
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            # Acid sound with resonant filter
            n = int(step * SAMPLE_RATE)
            t_arr = np.arange(n) / SAMPLE_RATE

            # Saw with envelope
            saw = 2 * (t_arr * note - np.floor(t_arr * note + 0.5))
            env = np.exp(-t_arr * 8)
            acid = saw * env

            l = min(len(acid), samples - start)
            audio[start:start+l] += acid[:l] * 0.3

    # Atmosphere
    for bar in range(int(duration / 4)):
        start = int(bar * 4 * SAMPLE_RATE)
        pad = synth_pad([82, 110, 164], 3.5)
        l = min(len(pad), samples - start)
        audio[start:start+l] += pad[:l] * 0.2

    # Sidechain for pumping
    audio = sidechain_comp(audio, kick_times)

    return audio

def create_trance_driver():
    """Uplifting trance, but dark"""
    bpm = 138
    duration = 52

    samples = int(sr := SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    # Kick every beat
    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)
        start = int(t * SAMPLE_RATE)
        k = synth_kick(50, 0.3)
        l = min(len(k), samples - start)
        audio[start:start+l] += k[:l] * 0.9

    # Snare on 2.5 and 4
    for t in np.arange(0, duration, beat_dur):
        if t % beat_dur > beat_dur * 0.5:
            start = int(t * SAMPLE_RATE)
            s = synth_snare(0.2)
            l = min(len(s), samples - start)
            audio[start:start+l] += s[:l] * 0.65

    # Hi-hats
    for t in np.arange(0, duration, beat_dur / 2):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break
        h = synth_hihat(open=(t % beat_dur < beat_dur * 0.01))
        l = min(len(h), samples - start)
        audio[start:start+l] += h[:l] * 0.35

    # Arpeggiated bass
    arp_notes = [41, 55, 65, 55, 41, 55, 73, 55]
    arp_step = beat_dur / 4

    for bar in range(int(duration / (beat_dur * 8))):
        for i, note in enumerate(arp_notes):
            t = bar * 8 * beat_dur + i * arp_step
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            bass = synth_bass(note, arp_step * 0.8, octave=1)
            l = min(len(bass), samples - start)
            audio[start:start+l] += bass[:l] * 0.6

    # Trance lead - supersaw
    for phrase in range(int(duration / (beat_dur * 16))):
        phrase_start = phrase * 16 * beat_dur

        # 8-note arpeggio pattern
        lead_notes = [523, 659, 784, 659, 784, 1047, 784, 1047]

        for i, freq in enumerate(lead_notes):
            t = phrase_start + i * beat_dur
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            # Supersaw lead
            n = int(beat_dur * 0.9 * SAMPLE_RATE)
            t_arr = np.arange(n) / SAMPLE_RATE

            saw = np.zeros(n)
            for detune in [-0.03, 0, 0.03, 0.06, -0.06]:
                saw += np.sin(2 * np.pi * freq * (1 + detune) * t_arr)

            # Filter sweep
            cutoff = 0.2 + 0.4 * np.exp(-t_arr * 3)
            filtered = np.zeros(n)
            for j in range(1, n):
                filtered[j] = filtered[j-1] + cutoff[j] * (saw[j] - filtered[j-1])

            env = create_envelope(n, attack=0.05, decay=0.1, sustain=0.5, release=0.4)
            lead = filtered * env

            l = min(len(lead), samples - start)
            audio[start:start+l] += lead[:l] * 0.35

    # Pad layer - building
    for section in range(int(duration / 8)):
        start = int(section * 8 * SAMPLE_RATE)
        if section % 2 == 0:  # Even sections
            pad = synth_pad([261, 329, 392], 7.5)
            l = min(len(pad), samples - start)
            audio[start:start+l] += pad[:l] * 0.3

    audio = sidechain_comp(audio, kick_times, threshold=0.4)

    return audio

def create_modern_boombap():
    """Lo-fi hip-hop, modern"""
    bpm = 85
    duration = 55

    samples = int(sr := SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm
    bar_dur = beat_dur * 4

    # Sparse kick
    kick_times = []
    for bar in range(int(duration / bar_dur)):
        for beat in [0, 2.5]:  # Off-beat kicks
            t = bar * bar_dur + beat * beat_dur
            kick_times.append(t)
            start = int(t * SAMPLE_RATE)
            k = synth_808(40, 0.6, decay=0.3)
            l = min(len(k), samples - start)
            audio[start:start+l] += k[:l] * 0.9

    # Snare
    for bar in range(int(duration / bar_dur)):
        for beat in [1, 3]:
            t = bar * bar_dur + beat * beat_dur
            start = int(t * SAMPLE_RATE)
            s = synth_snare(0.25)
            l = min(len(s), samples - start)
            audio[start:start+l] += s[:l] * 0.6

    # Chopped hi-hats
    for bar in range(int(duration / (bar_dur / 2))):
        for i in range(8):
            t = bar * (bar_dur / 2) + i * (bar_dur / 16)
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            # Velocity pattern
            vel = 0.35 if i % 4 == 0 else 0.2
            h = synth_hihat(open=(i % 8 == 4))
            l = min(len(h), samples - start)
            audio[start:start+l] += h[:l] * vel

    # Soulful bass
    bass_pattern = [
        (55, 0, bar_dur),
        (55, bar_dur, bar_dur * 2),
        (58, bar_dur * 2, bar_dur * 3),
        (62, bar_dur * 2.5, bar_dur * 3.5),
        (65, bar_dur * 3, bar_dur * 4),
    ]

    for freq, st, en in bass_pattern:
        start = int(st * SAMPLE_RATE)
        dur = en - st
        b = synth_bass(freq, dur, octave=1)
        l = min(len(b), samples - start)
        audio[start:start+l] += b[:l] * 0.55

    # Lo-fi chords
    chords = [
        (261.63, 329.63, 392.00),  # C major 7
        (233.08, 293.66, 349.23),  # Bb major
        (220.00, 277.18, 329.63),  # A minor
        (207.65, 261.63, 311.13),  # G major 7
    ]

    for bar in range(int(duration / bar_dur)):
        chord = chords[bar % len(chords)]
        start = int(bar * bar_dur * SAMPLE_RATE)

        # Filtered pad
        n = min(int(bar_dur * 0.9 * SAMPLE_RATE), samples - start)
        if n > 0:
            t_arr = np.arange(n) / SAMPLE_RATE
            pad = np.zeros(n)

            for f in chord:
                # Very slow filter
                filtered = np.sin(2 * np.pi * f * t_arr) * 0.15
                mod = 1 + np.sin(2 * np.pi * 0.2 * t_arr) * 0.1
                pad += filtered * mod

            audio[start:start+n] += pad * 0.4

    # Vinyl crackle (subtle)
    n = samples
    t_arr = np.arange(n) / SAMPLE_RATE
    crackle = np.random.randn(n) * 0.02
    # Bandpass filter the crackle
    for i in range(1, n):
        crackle[i] = crackle[i-1] + 0.3 * (crackle[i] - crackle[i-1])
    audio += crackle * 0.3

    return audio

def create_dark_techno():
    """Dark, minimal techno"""
    bpm = 135
    duration = 55

    samples = int(sr := SAMPLE_RATE) * duration
    audio = np.zeros(samples)
    beat_dur = 60 / bpm

    # Deep kick
    kick_times = []
    for t in np.arange(0, duration, beat_dur):
        kick_times.append(t)
        start = int(t * SAMPLE_RATE)
        k = synth_kick(45, 0.35)
        l = min(len(k), samples - start)
        audio[start:start+l] += k[:l]

    # Percussion - sparse
    for bar in range(int(duration / (beat_dur * 4))):
        # Snare on 2.5
        t = bar * 4 * beat_dur + 2 * beat_dur + beat_dur * 0.5
        start = int(t * SAMPLE_RATE)
        if start < samples:
            s = synth_snare(0.12)
            l = min(len(s), samples - start)
            audio[start:start+l] += s[:l] * 0.5

        # Clap
        t = bar * 4 * beat_dur + 2 * beat_dur + beat_dur * 0.75
        start = int(t * SAMPLE_RATE)
        if start < samples:
            c = synth_snare(0.1) * 0.4
            l = min(len(c), samples - start)
            audio[start:start+l] += c[:l]

    # Industrial hats
    for t in np.arange(0, duration, beat_dur / 4):
        start = int(t * SAMPLE_RATE)
        if start >= samples:
            break

        # Open on certain beats
        is_open = (t % beat_dur < 0.01) or ((t + beat_dur * 0.5) % beat_dur < 0.01)
        h = synth_hihat(open=is_open)
        l = min(len(h), samples - start)

        # Ghost hits
        vel = 0.25 if (t % beat_dur) > 0.01 else 0.4
        audio[start:start+l] += h[:l] * vel

    # Bass - hypnotic
    bass_notes = [36, 36, 43, 41, 36, 36, 43, 45]
    step = beat_dur

    for bar in range(int(duration / (beat_dur * 8))):
        for i, note in enumerate(bass_notes):
            t = bar * 8 * beat_dur + i * step
            start = int(t * SAMPLE_RATE)
            if start >= samples:
                break

            # Sub bass
            n = min(int(step * 0.9 * SAMPLE_RATE), samples - start)
            if n > 0:
                t_arr = np.arange(n) / SAMPLE_RATE
                sub = np.sin(2 * np.pi * note * t_arr)
                env = np.exp(-t_arr * 3)
                bass = sub * env

                audio[start:start+n] += bass * 0.6

    # Dark pad
    for section in range(int(duration / 16)):
        start = int(section * 16 * SAMPLE_RATE)
        # Dissonant chord
        pad = synth_pad([73, 87, 110, 146], 15.5)
        l = min(len(pad), samples - start)
        audio[start:start+l] += pad[:l] * 0.2

    # Noise riser before drops
    for bar in range(int(duration / (beat_dur * 16))):
        if bar > 0:
            riser_start = int(bar * 16 * beat_dur * SAMPLE_RATE)
            riser_dur = int(beat_dur * 4 * SAMPLE_RATE)
            riser_end = min(riser_start + riser_dur, samples)

            if riser_start < samples:
                t_arr = np.arange(riser_end - riser_start) / SAMPLE_RATE
                noise = np.random.randn(riser_end - riser_start)
                # Bandpass sweep
                sweep = 0.1 + 0.5 * (t_arr / t_arr[-1])
                riser = noise * sweep * 0.3
                audio[riser_start:riser_end] += riser

    audio = sidechain_comp(audio, kick_times, threshold=0.35)

    return audio

# ====== MAIN ======
if __name__ == "__main__":
    print("[*] Muzikler olusturuluyor...")
    print("=" * 50)

    tracks = [
        ("bg_hiphop_bounce.mp3", create_hiphop_bounce),
        ("bg_techno_thumper.mp3", create_techno_thumper),
        ("bg_trance_driver.mp3", create_trance_driver),
        ("bg_modern_boombap.mp3", create_modern_boombap),
        ("bg_dark_techno.mp3", create_dark_techno),
    ]

    for filename, gen in tracks:
        print("[>] {0}".format(filename))
        try:
            audio = gen()
            save_as_mp3(audio, filename)
        except Exception as e:
            print("[!] Hata: {0}".format(e))

    print("=" * 50)
    print("[OK] Tamamlandi!")
    print("[>] Konum: {0}".format(OUTPUT_DIR))