"""Synthesize a short chiptune 'medieval' tune (D dorian) as a WAV file.

Usage: python3 music.py <out.wav>
"""
import sys
import wave

import numpy as np

SR, BPM, DUR = 44100, 132, 10.0
BEAT = 60 / BPM


def freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def tone(midi, beats, kind, vol):
    n = int(SR * beats * BEAT)
    t = np.arange(n) / SR
    ph = (t * freq(midi)) % 1
    if kind == "square":
        w = np.where(ph < 0.25, 1.0, -1.0)          # 25% pulse, lute-ish
    else:
        w = 4 * np.abs(ph - 0.5) - 1                  # triangle bass
    env = np.minimum(1, t / 0.01) * np.exp(-t * (3.0 if kind == "square" else 1.2))
    return w * env * vol


def track(notes, kind, vol):
    parts = [tone(m, b, kind, vol) if m else np.zeros(int(SR * b * BEAT)) for m, b in notes]
    return np.concatenate(parts)


D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, G5, A5 = 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81
melody = [
    (D5, 1), (E5, .5), (F5, .5), (G5, 1), (A5, 1),
    (G5, .5), (F5, .5), (E5, 1), (C5, 1), (D5, 1),
    (A4, 1), (C5, .5), (D5, .5), (E5, 1), (F5, .5), (E5, .5),
    (D5, 1), (C5, 1), (A4, 2),
    (D5, 1), (E5, .5), (F5, .5), (G5, 1), (A5, .5), (G5, .5),
    (F5, 1), (E5, 1), (D5, 2),
]
bass = [(50, 2), (45, 2), (48, 2), (50, 2)] * 3
drone = [(38, 4)] * 6

mel = track(melody, "square", 0.22)
bas = track(bass, "tri", 0.30)
n = int(SR * DUR)
mix = np.zeros(n)
for part in (mel, bas):
    mix[:min(n, len(part))] += part[:n]
fade = np.ones(n)
fade[-SR:] = np.linspace(1, 0, SR)
mix = np.clip(mix * fade, -1, 1)

with wave.open(sys.argv[1], "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((mix * 32000).astype(np.int16).tobytes())
