#!/usr/bin/env python3
"""Gera todos os sons autorais do jogo, sem dependências externas.

Direção sonora 2026-09-27:
- confortável em celular: transientes arredondados, sem picos agressivos;
- coerente: moedas/UI usam a mesma assinatura pentatônica brilhante;
- hipnótico: músicas curtas em loop com pulsos suaves e ambiência urbana;
- gameplay legível: pulo, dash, deslize, passos e impactos têm envelopes próprios.

O script escreve WAV PCM 16-bit estéreo/44.1 kHz. É determinístico.
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import struct
import wave
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "assets" / "audio"
RATE = 44_100
MASTER_SEED = 20260927
TAU = math.tau
Stereo = Tuple[float, float]

AUDIO.mkdir(parents=True, exist_ok=True)


def db_to_amp(db: float) -> float:
    return 10.0 ** (db / 20.0)


def clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def pan_gains(pan: float) -> Tuple[float, float]:
    p = max(-1.0, min(1.0, pan))
    angle = (p + 1.0) * math.pi * 0.25
    return math.cos(angle), math.sin(angle)


def env_ar(t: float, dur: float, attack: float = 0.006, release: float = 0.05) -> float:
    if dur <= 0:
        return 0.0
    a = 1.0 if attack <= 0 else min(1.0, t / attack)
    r = 1.0 if release <= 0 else min(1.0, max(0.0, dur - t) / release)
    return max(0.0, min(1.0, a * r))


def env_perc(t: float, dur: float, attack: float = 0.004, decay: float = 0.18, release: float = 0.02) -> float:
    if t < 0.0 or t > dur:
        return 0.0
    a = min(1.0, t / max(attack, 1e-5))
    d = math.exp(-max(0.0, t - attack) / max(decay, 1e-5))
    tail = min(1.0, max(0.0, dur - t) / max(release, 1e-5))
    return a * d * tail


def waveform(kind: str, phase: float) -> float:
    s = math.sin(phase)
    if kind == "sine":
        return s
    if kind == "tri":
        return 2.0 / math.pi * math.asin(s)
    if kind == "soft_square":
        return math.tanh(2.2 * s) / math.tanh(2.2)
    if kind == "soft_saw":
        # Série limitada: mais macia que saw pura, sem aliasing severo para SFX curtos.
        return sum(math.sin(phase * h) / h for h in range(1, 7)) / 2.45
    return s


def tone(
    freq: float,
    dur: float,
    amp: float = 0.35,
    *,
    end_freq: float | None = None,
    kind: str = "sine",
    pan: float = 0.0,
    attack: float = 0.006,
    release: float = 0.05,
    decay: float | None = None,
    vibrato: float = 0.0,
    vibrato_hz: float = 5.0,
    harmonics: Sequence[Tuple[float, float]] = (),
) -> List[Stereo]:
    n = int(RATE * dur)
    lg, rg = pan_gains(pan)
    out: List[Stereo] = []
    phase = 0.0
    phase_h = [0.0 for _ in harmonics]
    for i in range(n):
        t = i / RATE
        ratio = t / max(dur, 1e-6)
        f = freq
        if end_freq is not None and freq > 0 and end_freq > 0:
            f = freq * ((end_freq / freq) ** ratio)
        if vibrato:
            f *= 1.0 + math.sin(TAU * vibrato_hz * t) * vibrato
        phase += TAU * f / RATE
        y = waveform(kind, phase)
        for hi, (mul, h_amp) in enumerate(harmonics):
            phase_h[hi] += TAU * f * mul / RATE
            y += waveform("sine", phase_h[hi]) * h_amp
        if decay is None:
            e = env_ar(t, dur, attack, release)
        else:
            e = env_perc(t, dur, attack, decay, release)
        v = y * amp * e
        out.append((v * lg, v * rg))
    return out


def noise(
    dur: float,
    amp: float = 0.25,
    *,
    seed: int = 0,
    pan: float = 0.0,
    attack: float = 0.005,
    release: float = 0.06,
    lowpass_hz: float | None = None,
    highpass_hz: float | None = None,
    color: str = "white",
) -> List[Stereo]:
    rng = random.Random(MASTER_SEED + seed)
    n = int(RATE * dur)
    lg, rg = pan_gains(pan)
    lp = 0.0
    hp = 0.0
    prev_x = 0.0
    if lowpass_hz:
        rc = 1.0 / (TAU * lowpass_hz)
        alpha_lp = (1.0 / RATE) / (rc + 1.0 / RATE)
    else:
        alpha_lp = 1.0
    if highpass_hz:
        rc_hp = 1.0 / (TAU * highpass_hz)
        alpha_hp = rc_hp / (rc_hp + 1.0 / RATE)
    else:
        alpha_hp = 0.0
    out: List[Stereo] = []
    brown = 0.0
    for i in range(n):
        t = i / RATE
        x = rng.uniform(-1.0, 1.0)
        if color == "brown":
            brown = brown * 0.985 + x * 0.045
            x = brown * 4.0
        elif color == "pink":
            brown = brown * 0.92 + x * 0.20
            x = brown
        lp += alpha_lp * (x - lp)
        y = lp
        if highpass_hz:
            hp = alpha_hp * (hp + y - prev_x)
            prev_x = y
            y = hp
        e = env_ar(t, dur, attack, release)
        v = y * amp * e
        out.append((v * lg, v * rg))
    return out


def silence(dur: float) -> List[Stereo]:
    return [(0.0, 0.0)] * int(RATE * dur)


def mix(dur: float, layers: Iterable[Tuple[float, Sequence[Stereo]]]) -> List[Stereo]:
    total = int(RATE * dur)
    out = [[0.0, 0.0] for _ in range(total)]
    for start, layer in layers:
        pos = int(start * RATE)
        if pos >= total:
            continue
        for i, (l, r) in enumerate(layer):
            j = pos + i
            if j >= total:
                break
            out[j][0] += l
            out[j][1] += r
    return [(l, r) for l, r in out]


def add_delay(samples: Sequence[Stereo], taps: Sequence[Tuple[float, float, float]]) -> List[Stereo]:
    out = [[l, r] for l, r in samples]
    n = len(out)
    for delay_s, gain, pan in taps:
        d = int(delay_s * RATE)
        lg, rg = pan_gains(pan)
        for i in range(d, n):
            src_l, src_r = samples[i - d]
            mono = (src_l + src_r) * 0.5 * gain
            out[i][0] += mono * lg
            out[i][1] += mono * rg
    return [(l, r) for l, r in out]


def low_shelf_soft(samples: Sequence[Stereo], amount: float = 0.12) -> List[Stereo]:
    """Pequeno arredondamento analógico: reduz aspereza sem matar transiente."""
    out: List[Stereo] = []
    lp_l = lp_r = 0.0
    alpha = 0.08
    for l, r in samples:
        lp_l += alpha * (l - lp_l)
        lp_r += alpha * (r - lp_r)
        out.append((l * (1 - amount) + lp_l * amount, r * (1 - amount) + lp_r * amount))
    return out


def limit(samples: Sequence[Stereo], target_peak_db: float = -3.0) -> List[Stereo]:
    peak = max((max(abs(l), abs(r)) for l, r in samples), default=0.0)
    if peak <= 0.0:
        return list(samples)
    target = db_to_amp(target_peak_db)
    # Normaliza para alvo; tanh pega eventuais somas internas.
    gain = target / peak
    out = []
    drive = 1.05
    for l, r in samples:
        out.append((math.tanh(l * gain * drive) / math.tanh(drive), math.tanh(r * gain * drive) / math.tanh(drive)))
    return out


def fade_edges(samples: Sequence[Stereo], fade_s: float = 0.006) -> List[Stereo]:
    out = list(samples)
    n = len(out)
    f = min(int(fade_s * RATE), n // 2)
    if f <= 0:
        return out
    as_list = [[l, r] for l, r in out]
    for i in range(f):
        a = i / f
        b = (f - i) / f
        as_list[i][0] *= a
        as_list[i][1] *= a
        as_list[n - 1 - i][0] *= b
        as_list[n - 1 - i][1] *= b
    return [(l, r) for l, r in as_list]


def write_wav(name: str, samples: Sequence[Stereo], *, peak_db: float = -3.0, fade_s: float = 0.004) -> None:
    path = AUDIO / name
    samples = low_shelf_soft(samples)
    samples = fade_edges(samples, fade_s)
    samples = limit(samples, peak_db)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = bytearray()
        for l, r in samples:
            frames += struct.pack("<h", int(clamp(l) * 32767.0))
            frames += struct.pack("<h", int(clamp(r) * 32767.0))
        w.writeframes(frames)
    print(f"  {name:22} {len(samples) / RATE:5.2f}s peak {peak_db:5.1f} dB")


def bell(note: float, dur: float, amp: float, *, pan: float = 0.0, decay: float = 0.16) -> List[Stereo]:
    return tone(
        note,
        dur,
        amp,
        kind="sine",
        pan=pan,
        attack=0.002,
        release=0.035,
        decay=decay,
        harmonics=[(2.01, 0.38), (3.98, 0.15), (6.02, 0.06)],
    )


def chord(freqs: Sequence[float], dur: float, amp: float, *, pan: float = 0.0, decay: float = 0.45) -> List[Stereo]:
    layers = []
    for i, f in enumerate(freqs):
        layers.append((0.0, bell(f, dur, amp / max(1, len(freqs)), pan=pan + (i - len(freqs) / 2) * 0.12, decay=decay)))
    return mix(dur, layers)


# ---------------------------------------------------------------------------
# SFX de interface e feedback positivo
# ---------------------------------------------------------------------------

def gen_ui() -> None:
    write_wav("click.wav", mix(0.095, [
        (0.000, bell(820, 0.055, 0.20, pan=-0.08, decay=0.035)),
        (0.018, tone(260, 0.055, 0.055, kind="tri", pan=0.05, decay=0.030)),
    ]), peak_db=-12.0)

    write_wav("ui_confirm.wav", add_delay(mix(0.26, [
        (0.000, bell(587.33, 0.10, 0.18, pan=-0.18, decay=0.07)),
        (0.055, bell(783.99, 0.12, 0.18, pan=0.10, decay=0.08)),
        (0.118, bell(1174.66, 0.14, 0.14, pan=0.25, decay=0.10)),
    ]), [(0.060, 0.10, -0.5)]), peak_db=-8.5)

    write_wav("ui_back.wav", mix(0.20, [
        (0.000, bell(659.25, 0.105, 0.15, pan=0.10, decay=0.06)),
        (0.060, bell(392.00, 0.115, 0.16, pan=-0.18, decay=0.08)),
        (0.020, tone(180, 0.12, 0.025, kind="tri", decay=0.07)),
    ]), peak_db=-10.5)

    write_wav("count_beep.wav", mix(0.14, [
        (0.000, bell(880.00, 0.13, 0.21, decay=0.08)),
        (0.000, tone(440.00, 0.13, 0.045, kind="sine", decay=0.09)),
    ]), peak_db=-9.0)

    write_wav("count_go.wav", add_delay(mix(0.44, [
        (0.000, bell(659.25, 0.11, 0.18, pan=-0.2, decay=0.06)),
        (0.065, bell(880.00, 0.13, 0.19, pan=0.0, decay=0.08)),
        (0.140, bell(1318.51, 0.22, 0.20, pan=0.22, decay=0.16)),
        (0.020, noise(0.28, 0.040, seed=101, pan=0.0, lowpass_hz=2900, highpass_hz=450)),
    ]), [(0.085, 0.12, -0.45), (0.135, 0.08, 0.5)]), peak_db=-7.5)

    write_wav("coin.wav", add_delay(mix(0.29, [
        (0.000, bell(1174.66, 0.105, 0.17, pan=-0.08, decay=0.055)),
        (0.056, bell(1567.98, 0.16, 0.18, pan=0.14, decay=0.105)),
        (0.017, tone(2349.32, 0.090, 0.032, kind="sine", pan=0.26, decay=0.045)),
    ]), [(0.045, 0.10, 0.55)]), peak_db=-7.0)

    write_wav("combo.wav", add_delay(mix(0.54, [
        (0.000, bell(523.25, 0.11, 0.13, pan=-0.28, decay=0.06)),
        (0.070, bell(659.25, 0.12, 0.14, pan=-0.12, decay=0.065)),
        (0.140, bell(783.99, 0.13, 0.15, pan=0.05, decay=0.075)),
        (0.210, bell(1046.50, 0.16, 0.16, pan=0.20, decay=0.10)),
        (0.300, chord([1318.51, 1567.98], 0.20, 0.16, pan=0.0, decay=0.14)),
    ]), [(0.095, 0.11, -0.40), (0.170, 0.08, 0.42)]), peak_db=-7.0)

    write_wav("pickup.wav", add_delay(mix(0.36, [
        (0.000, bell(440.00, 0.10, 0.13, pan=-0.20, decay=0.07)),
        (0.080, bell(659.25, 0.11, 0.14, pan=0.00, decay=0.08)),
        (0.160, bell(987.77, 0.15, 0.15, pan=0.20, decay=0.10)),
        (0.020, noise(0.20, 0.025, seed=102, lowpass_hz=2400, highpass_hz=600)),
    ]), [(0.075, 0.09, 0.35)]), peak_db=-8.5)

    write_wav("reward.wav", add_delay(mix(0.46, [
        (0.000, bell(659.25, 0.11, 0.15, pan=-0.25, decay=0.08)),
        (0.080, bell(880.00, 0.13, 0.15, pan=-0.05, decay=0.09)),
        (0.165, bell(1174.66, 0.18, 0.16, pan=0.18, decay=0.13)),
        (0.250, chord([880.00, 1318.51, 1760.00], 0.20, 0.12, pan=0.0, decay=0.15)),
    ]), [(0.090, 0.12, -0.45), (0.160, 0.09, 0.55)]), peak_db=-7.5)

    write_wav("streak.wav", add_delay(mix(0.62, [
        (0.000, bell(392.00, 0.12, 0.13, pan=-0.30, decay=0.08)),
        (0.085, bell(523.25, 0.13, 0.13, pan=-0.10, decay=0.08)),
        (0.170, bell(659.25, 0.14, 0.14, pan=0.08, decay=0.09)),
        (0.260, bell(783.99, 0.16, 0.14, pan=0.24, decay=0.11)),
        (0.365, chord([523.25, 659.25, 987.77], 0.22, 0.13, pan=0.0, decay=0.18)),
    ]), [(0.105, 0.11, -0.40), (0.190, 0.08, 0.44)]), peak_db=-7.5)

    write_wav("levelup.wav", add_delay(mix(0.58, [
        (0.000, bell(659.25, 0.10, 0.14, pan=-0.30, decay=0.06)),
        (0.060, bell(880.00, 0.105, 0.15, pan=-0.12, decay=0.06)),
        (0.120, bell(1318.51, 0.13, 0.16, pan=0.10, decay=0.08)),
        (0.185, bell(1760.00, 0.22, 0.16, pan=0.30, decay=0.16)),
        (0.270, chord([659.25, 987.77, 1318.51], 0.24, 0.12, pan=0.0, decay=0.20)),
    ]), [(0.095, 0.12, -0.5), (0.175, 0.10, 0.55)]), peak_db=-7.0)

    write_wav("chest.wav", mix(0.62, [
        (0.000, noise(0.21, 0.10, seed=103, lowpass_hz=1200, highpass_hz=140, color="pink", release=0.12)),
        (0.060, tone(135, 0.19, 0.12, end_freq=96, kind="tri", decay=0.09)),
        (0.220, bell(659.25, 0.15, 0.15, pan=-0.10, decay=0.08)),
        (0.315, bell(987.77, 0.22, 0.16, pan=0.16, decay=0.16)),
        (0.350, noise(0.12, 0.040, seed=104, lowpass_hz=4200, highpass_hz=1200)),
    ]), peak_db=-7.5)

    write_wav("purchase.wav", add_delay(mix(0.56, [
        (0.000, bell(1318.51, 0.09, 0.16, pan=-0.18, decay=0.05)),
        (0.060, bell(1760.00, 0.15, 0.17, pan=0.12, decay=0.10)),
        (0.180, bell(880.00, 0.11, 0.12, pan=-0.05, decay=0.07)),
        (0.255, chord([1046.50, 1318.51, 1760.00], 0.22, 0.13, pan=0.0, decay=0.18)),
    ]), [(0.090, 0.12, -0.45), (0.155, 0.08, 0.50)]), peak_db=-7.5)


# ---------------------------------------------------------------------------
# Personagem, rua e ações de gameplay
# ---------------------------------------------------------------------------

def gen_actions() -> None:
    step_asfalto = mix(0.135, [
        (0.000, tone(92, 0.055, 0.070, end_freq=70, kind="tri", decay=0.030, pan=-0.02)),
        (0.008, noise(0.090, 0.030, seed=201, lowpass_hz=900, highpass_hz=120, color="pink", release=0.045)),
    ])
    step_calcada = mix(0.145, [
        (0.000, tone(112, 0.052, 0.058, end_freq=86, kind="tri", decay=0.026, pan=0.04)),
        (0.012, bell(1450, 0.060, 0.030, pan=-0.10, decay=0.030)),
        (0.018, noise(0.090, 0.022, seed=202, lowpass_hz=1600, highpass_hz=220, color="pink", release=0.050)),
    ])
    step_terra = mix(0.150, [
        (0.000, tone(78, 0.060, 0.076, end_freq=55, kind="tri", decay=0.035, pan=-0.04)),
        (0.004, noise(0.120, 0.042, seed=203, lowpass_hz=650, highpass_hz=70, color="brown", release=0.060)),
    ])
    step_metal = mix(0.125, [
        (0.000, tone(118, 0.045, 0.042, end_freq=90, kind="tri", decay=0.025)),
        (0.010, bell(820, 0.070, 0.038, pan=0.08, decay=0.045)),
        (0.024, bell(1230, 0.055, 0.020, pan=-0.08, decay=0.035)),
    ])
    write_wav("step.wav", step_asfalto, peak_db=-17.0)
    write_wav("step_asfalto.wav", step_asfalto, peak_db=-17.0)
    write_wav("step_calcada.wav", step_calcada, peak_db=-17.0)
    write_wav("step_terra.wav", step_terra, peak_db=-16.0)
    write_wav("step_metal.wav", step_metal, peak_db=-18.0)

    write_wav("jump.wav", add_delay(mix(0.34, [
        (0.000, tone(180, 0.24, 0.085, end_freq=520, kind="sine", pan=0.0, attack=0.010, release=0.070)),
        (0.015, noise(0.20, 0.046, seed=204, lowpass_hz=2600, highpass_hz=350, pan=-0.12, release=0.090)),
        (0.085, bell(780, 0.13, 0.050, pan=0.18, decay=0.070)),
    ]), [(0.070, 0.07, 0.45)]), peak_db=-7.5)

    write_wav("dash.wav", add_delay(mix(0.43, [
        (0.000, noise(0.38, 0.105, seed=205, lowpass_hz=3600, highpass_hz=220, pan=-0.22, attack=0.012, release=0.12, color="pink")),
        (0.020, tone(105, 0.28, 0.065, end_freq=62, kind="tri", pan=0.0, decay=0.10)),
        (0.060, tone(420, 0.24, 0.044, end_freq=980, kind="sine", pan=0.28, attack=0.020, release=0.09)),
    ]), [(0.055, 0.10, 0.55), (0.120, 0.07, -0.5)]), peak_db=-6.8)

    write_wav("whoosh.wav", add_delay(mix(0.28, [
        (0.000, noise(0.25, 0.080, seed=206, lowpass_hz=3000, highpass_hz=500, pan=-0.45, attack=0.010, release=0.100, color="pink")),
        (0.030, noise(0.18, 0.045, seed=207, lowpass_hz=4200, highpass_hz=1000, pan=0.42, attack=0.018, release=0.070)),
        (0.050, tone(300, 0.17, 0.030, end_freq=510, kind="sine", pan=0.0, attack=0.012, release=0.060)),
    ]), [(0.050, 0.08, 0.50)]), peak_db=-8.0)

    write_wav("slide.wav", mix(0.46, [
        (0.000, noise(0.40, 0.090, seed=208, lowpass_hz=1600, highpass_hz=160, color="pink", attack=0.020, release=0.13, pan=-0.08)),
        (0.030, tone(120, 0.24, 0.050, end_freq=78, kind="tri", decay=0.10, pan=0.04)),
        (0.220, noise(0.16, 0.035, seed=209, lowpass_hz=2400, highpass_hz=420, color="pink", release=0.08, pan=0.14)),
    ]), peak_db=-8.8)

    write_wav("hit.wav", mix(0.36, [
        (0.000, noise(0.16, 0.115, seed=210, lowpass_hz=1000, highpass_hz=80, color="pink", release=0.08)),
        (0.015, tone(95, 0.24, 0.115, end_freq=64, kind="tri", decay=0.10)),
        (0.085, tone(180, 0.11, 0.035, kind="sine", decay=0.05)),
    ]), peak_db=-6.5)

    write_wav("impact_heavy.wav", add_delay(mix(0.58, [
        (0.000, noise(0.22, 0.130, seed=211, lowpass_hz=850, highpass_hz=55, color="brown", release=0.13)),
        (0.018, tone(58, 0.42, 0.145, end_freq=38, kind="sine", attack=0.004, release=0.18, decay=0.19)),
        (0.090, noise(0.18, 0.055, seed=212, lowpass_hz=1500, highpass_hz=140, color="pink", release=0.10)),
    ]), [(0.110, 0.08, -0.35)]), peak_db=-5.8)

    write_wav("wall.wav", mix(0.32, [
        (0.000, tone(210, 0.11, 0.085, end_freq=150, kind="tri", decay=0.045)),
        (0.035, bell(520, 0.11, 0.060, pan=-0.10, decay=0.05)),
        (0.070, bell(780, 0.12, 0.045, pan=0.14, decay=0.06)),
        (0.000, noise(0.12, 0.045, seed=213, lowpass_hz=1400, highpass_hz=150, color="pink", release=0.07)),
    ]), peak_db=-8.5)

    # Latido estilizado: dois pulsos com formantes macios, audível sem irritar.
    bark = mix(0.54, [
        (0.000, noise(0.13, 0.105, seed=214, lowpass_hz=1300, highpass_hz=120, color="pink", attack=0.004, release=0.05)),
        (0.018, tone(190, 0.12, 0.060, end_freq=150, kind="tri", decay=0.05)),
        (0.030, tone(520, 0.08, 0.032, end_freq=430, kind="sine", decay=0.04)),
        (0.210, noise(0.15, 0.090, seed=215, lowpass_hz=1200, highpass_hz=110, color="pink", attack=0.004, release=0.06)),
        (0.230, tone(165, 0.13, 0.056, end_freq=132, kind="tri", decay=0.055)),
        (0.245, tone(480, 0.08, 0.026, end_freq=390, kind="sine", decay=0.045)),
    ])
    write_wav("bark.wav", add_delay(bark, [(0.060, 0.08, 0.4)]), peak_db=-7.5)

    write_wav("shout.wav", add_delay(mix(0.42, [
        (0.000, tone(280, 0.20, 0.055, end_freq=335, kind="sine", vibrato=0.020, vibrato_hz=5.2, attack=0.025, release=0.10)),
        (0.030, tone(560, 0.18, 0.030, end_freq=640, kind="sine", vibrato=0.015, attack=0.020, release=0.09)),
        (0.055, tone(880, 0.15, 0.020, end_freq=760, kind="sine", attack=0.030, release=0.08)),
        (0.000, noise(0.24, 0.025, seed=216, lowpass_hz=1800, highpass_hz=350, color="pink", attack=0.020, release=0.11)),
    ]), [(0.085, 0.08, -0.35)]), peak_db=-9.0)


# ---------------------------------------------------------------------------
# Ônibus, clima e alertas
# ---------------------------------------------------------------------------

def gen_world() -> None:
    horn_core = mix(0.88, [
        (0.000, tone(392.00, 0.30, 0.105, kind="sine", attack=0.025, release=0.08, vibrato=0.006, vibrato_hz=3.2, pan=-0.05)),
        (0.000, tone(329.63, 0.30, 0.075, kind="sine", attack=0.025, release=0.08, vibrato=0.006, vibrato_hz=3.1, pan=0.06)),
        (0.300, tone(349.23, 0.32, 0.105, kind="sine", attack=0.025, release=0.10, vibrato=0.006, vibrato_hz=3.0, pan=0.03)),
        (0.300, tone(293.66, 0.32, 0.070, kind="sine", attack=0.025, release=0.10, vibrato=0.006, vibrato_hz=3.0, pan=-0.05)),
        (0.615, tone(392.00, 0.20, 0.080, kind="sine", attack=0.020, release=0.10, pan=0.0)),
    ])
    write_wav("bus_horn.wav", add_delay(horn_core, [(0.120, 0.14, -0.55), (0.205, 0.09, 0.50)]), peak_db=-8.5)

    write_wav("bus_doors.wav", add_delay(mix(0.92, [
        (0.000, noise(0.42, 0.080, seed=301, lowpass_hz=4200, highpass_hz=700, color="pink", attack=0.018, release=0.13, pan=-0.10)),
        (0.320, tone(100, 0.18, 0.065, end_freq=72, kind="tri", decay=0.070)),
        (0.420, noise(0.15, 0.080, seed=302, lowpass_hz=1400, highpass_hz=90, color="pink", release=0.07)),
        (0.570, tone(72, 0.25, 0.070, end_freq=58, kind="sine", decay=0.10)),
        (0.650, noise(0.20, 0.045, seed=303, lowpass_hz=2600, highpass_hz=400, color="pink", release=0.08)),
    ]), [(0.095, 0.08, 0.45)]), peak_db=-6.5)

    # Chuva em loop: cama estéreo macia + gotas raras; bordas em crossfade.
    rng = random.Random(MASTER_SEED + 304)
    dur = 6.0
    n = int(RATE * dur)
    base: List[Stereo] = []
    lp_l = lp_r = 0.0
    for i in range(n):
        t = i / RATE
        l = rng.uniform(-1, 1)
        r = rng.uniform(-1, 1)
        lp_l = lp_l * 0.74 + l * 0.26
        lp_r = lp_r * 0.74 + r * 0.26
        mod = 0.72 + 0.08 * math.sin(TAU * t / dur) + 0.05 * math.sin(TAU * 3.0 * t / dur)
        base.append((lp_l * 0.070 * mod, lp_r * 0.070 * mod))
    # gotas pontuais muito discretas
    drops = [(rng.uniform(0.2, dur - 0.2), rng.uniform(-0.8, 0.8), rng.uniform(0.018, 0.035)) for _ in range(28)]
    rain = mix(dur, [(0.0, base)] + [(t, bell(rng.choice([1760, 2093, 2349]), 0.055, a, pan=pan, decay=0.025)) for t, pan, a in drops])
    # Crossfade circular de 0.5 s para loop sem clique.
    xf = int(0.5 * RATE)
    rain_m = [[l, r] for l, r in rain]
    for i in range(xf):
        k = i / xf
        tail_l, tail_r = rain[-xf + i]
        head_l, head_r = rain[i]
        rain_m[i][0] = tail_l * (1.0 - k) + head_l * k
        rain_m[i][1] = tail_r * (1.0 - k) + head_r * k
    write_wav("rain_loop.wav", [(l, r) for l, r in rain_m], peak_db=-18.0, fade_s=0.0)

    thunder = mix(2.15, [
        (0.000, noise(0.40, 0.070, seed=305, lowpass_hz=180, highpass_hz=25, color="brown", attack=0.030, release=0.22)),
        (0.120, noise(1.45, 0.115, seed=306, lowpass_hz=260, highpass_hz=28, color="brown", attack=0.040, release=0.60)),
        (0.320, tone(42, 1.25, 0.090, end_freq=31, kind="sine", attack=0.030, release=0.75, vibrato=0.02, vibrato_hz=1.1)),
        (0.780, noise(0.90, 0.055, seed=307, lowpass_hz=520, highpass_hz=80, color="pink", attack=0.050, release=0.50)),
    ])
    write_wav("trovao.wav", add_delay(thunder, [(0.240, 0.18, -0.65), (0.430, 0.12, 0.60)]), peak_db=-7.5)


# ---------------------------------------------------------------------------
# Finais e estado de sessão
# ---------------------------------------------------------------------------

def gen_stingers() -> None:
    write_wav("victory.wav", add_delay(mix(0.92, [
        (0.000, bell(523.25, 0.13, 0.16, pan=-0.30, decay=0.08)),
        (0.085, bell(659.25, 0.14, 0.16, pan=-0.12, decay=0.08)),
        (0.175, bell(783.99, 0.16, 0.17, pan=0.06, decay=0.10)),
        (0.280, bell(1046.50, 0.24, 0.18, pan=0.24, decay=0.18)),
        (0.430, chord([523.25, 659.25, 783.99, 1046.50], 0.34, 0.22, pan=0.0, decay=0.28)),
        (0.060, noise(0.30, 0.025, seed=401, lowpass_hz=5200, highpass_hz=1800, color="pink", release=0.20)),
    ]), [(0.105, 0.13, -0.50), (0.185, 0.10, 0.55)]), peak_db=-6.0)

    write_wav("defeat.wav", add_delay(mix(1.10, [
        (0.000, bell(392.00, 0.20, 0.14, pan=-0.08, decay=0.12)),
        (0.190, bell(329.63, 0.22, 0.13, pan=0.08, decay=0.14)),
        (0.390, bell(261.63, 0.28, 0.12, pan=-0.02, decay=0.18)),
        (0.630, tone(196.00, 0.36, 0.055, end_freq=174.61, kind="sine", attack=0.030, release=0.24)),
        (0.050, noise(0.48, 0.030, seed=402, lowpass_hz=900, highpass_hz=90, color="pink", release=0.35)),
    ]), [(0.150, 0.08, -0.45)]), peak_db=-8.0)


# ---------------------------------------------------------------------------
# Música: loops baixos, autorais e hipnóticos
# ---------------------------------------------------------------------------

def music_loop(name: str, *, bpm: float, root: float, mode: Sequence[int], vibe: str, peak_db: float = -13.0) -> None:
    dur = 16.0
    n = int(RATE * dur)
    beat = 60.0 / bpm
    rng = random.Random(MASTER_SEED + int(root * 10) + int(bpm))
    out = [[0.0, 0.0] for _ in range(n)]
    # 16 passos: padrão simples que volta ao início sem tensão.
    pattern = [0, 2, 4, 7, 4, 2, 0, 4, 5, 7, 9, 7, 5, 4, 2, 0]
    bass_pattern = [0, 0, 5, 0, -2, -2, 5, 0]

    def add_layer(start: float, layer: Sequence[Stereo]) -> None:
        pos = int(start * RATE)
        for i, (l, r) in enumerate(layer):
            j = pos + i
            if j >= n:
                break
            out[j][0] += l
            out[j][1] += r

    # Pad circular com períodos que fecham em 16s.
    for i in range(n):
        t = i / RATE
        bar_phase = (t % (beat * 4)) / (beat * 4)
        lfo = 0.5 + 0.5 * math.sin(TAU * t / dur)
        freq = root * (2 ** (mode[0] / 12.0))
        pad = math.sin(TAU * freq * 0.5 * t) * 0.018
        pad += math.sin(TAU * freq * 0.75 * t + 0.7) * 0.012
        pad *= 0.75 + 0.25 * lfo
        # respiração estéreo lenta, hipnótica.
        out[i][0] += pad * (0.82 + 0.18 * math.sin(TAU * t / dur))
        out[i][1] += pad * (0.82 + 0.18 * math.cos(TAU * t / dur))
        if vibe == "terminal":
            out[i][0] += math.sin(TAU * 54.0 * t) * 0.006 * (0.7 + 0.3 * math.sin(TAU * t / 8.0))
            out[i][1] += math.sin(TAU * 54.0 * t + 0.2) * 0.006 * (0.7 + 0.3 * math.sin(TAU * t / 8.0))

    total_beats = int(dur / beat)
    for b in range(total_beats + 1):
        step = b % len(pattern)
        degree = mode[pattern[step] % len(mode)] + 12 * (pattern[step] // len(mode))
        f = root * (2 ** (degree / 12.0))
        start = b * beat
        pan = [-0.24, 0.18, -0.05, 0.28][b % 4]
        amp = 0.070 if vibe in ["city", "commerce"] else 0.058
        add_layer(start, bell(f * 2.0, min(beat * 0.82, 0.42), amp, pan=pan, decay=0.12))
        # Contratempo doce.
        if b % 2 == 1:
            add_layer(start + beat * 0.52, bell(f * 3.0 / 2.0, min(beat * 0.40, 0.22), amp * 0.42, pan=-pan, decay=0.08))
        # Kick muito redondo.
        add_layer(start, tone(90, min(0.12, beat * 0.35), 0.050, end_freq=48, kind="sine", decay=0.045))
        if b % 4 == 2:
            add_layer(start + beat * 0.02, noise(0.09, 0.018, seed=500 + b, lowpass_hz=850, highpass_hz=120, color="pink", release=0.050, pan=0.05))
        # Hi-hat/caxixi muito baixo para movimento.
        if b % 1 == 0:
            add_layer(start + beat * 0.50, noise(0.055, 0.010 if vibe != "beach" else 0.015, seed=700 + b, lowpass_hz=6800, highpass_hz=2400, color="pink", release=0.035, pan=rng.uniform(-0.4, 0.4)))
        # Bass em notas longas.
        if b % 2 == 0:
            bd = bass_pattern[(b // 2) % len(bass_pattern)]
            bf = root * 0.5 * (2 ** (bd / 12.0))
            add_layer(start, tone(bf, min(beat * 1.65, 0.85), 0.035, kind="sine", attack=0.020, release=0.22))

    if vibe == "beach":
        # Shaker leve e ar de orla.
        for b in range(total_beats * 2):
            add_layer(b * beat * 0.5, noise(0.060, 0.010, seed=900 + b, lowpass_hz=5200, highpass_hz=1800, color="pink", release=0.040, pan=rng.uniform(-0.7, 0.7)))
    if vibe == "commerce":
        # Pluck um pouco mais ativo, lembrando centro comercial sem ficar ansioso.
        for b in range(0, total_beats, 4):
            add_layer(b * beat + beat * 1.5, chord([root * 2, root * 2 * 2 ** (7 / 12), root * 2 * 2 ** (12 / 12)], 0.32, 0.050, decay=0.16))

    samples = [(l, r) for l, r in out]
    samples = add_delay(samples, [(0.120, 0.055, -0.50), (0.240, 0.040, 0.55)])
    write_wav(name, samples, peak_db=peak_db, fade_s=0.010)


def gen_music() -> None:
    # Modos pentatônicos/maiores: positivos e pouco cansativos em loop.
    music_loop("music_city.wav", bpm=104, root=220.00, mode=[0, 2, 4, 7, 9], vibe="city", peak_db=-13.0)
    music_loop("music_commerce.wav", bpm=112, root=196.00, mode=[0, 3, 5, 7, 10], vibe="commerce", peak_db=-13.0)
    music_loop("music_beach.wav", bpm=98, root=246.94, mode=[0, 2, 5, 7, 9], vibe="beach", peak_db=-13.5)
    music_loop("music_terminal.wav", bpm=92, root=174.61, mode=[0, 2, 3, 7, 10], vibe="terminal", peak_db=-13.5)


def ensure_import_for_dash() -> None:
    """Cria o .import do novo dash.wav no mesmo formato dos demais WAVs."""
    source = "res://assets/audio/dash.wav"
    digest = hashlib.md5(source.encode()).hexdigest()
    path = AUDIO / "dash.wav.import"
    if path.exists():
        return
    path.write_text(
        "[remap]\n\n"
        "importer=\"wav\"\n"
        "type=\"AudioStreamWAV\"\n"
        "uid=\"uid://c7m0audio9dash\"\n"
        f"path=\"res://.godot/imported/dash.wav-{digest}.sample\"\n\n"
        "[deps]\n\n"
        "source_file=\"res://assets/audio/dash.wav\"\n"
        f"dest_files=[\"res://.godot/imported/dash.wav-{digest}.sample\"]\n\n"
        "[params]\n\n"
        "force/8_bit=false\n"
        "force/mono=false\n"
        "force/max_rate=false\n"
        "force/max_rate_hz=44100\n"
        "edit/trim=false\n"
        "edit/normalize=false\n"
        "edit/loop_mode=0\n"
        "edit/loop_begin=0\n"
        "edit/loop_end=-1\n"
        "compress/mode=2\n"
    )
    print("  dash.wav.import        criado")


def main() -> None:
    print(f"Gerando pacote sonoro high-quality em {AUDIO} ({RATE} Hz estéreo, seed={MASTER_SEED})")
    gen_ui()
    gen_actions()
    gen_world()
    gen_stingers()
    gen_music()
    ensure_import_for_dash()
    wavs = sorted(AUDIO.glob("*.wav"))
    print(f"OK: {len(wavs)} WAVs autorais regenerados.")


if __name__ == "__main__":
    main()
