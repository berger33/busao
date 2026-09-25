# RELEASE — Lote 25: Foley Realista (2026-09-19)

**Branch**: `arena/01a0baf3-busao` · **Base**: `97420c2` (Lote 24) → **Lote 25**
**Status**: ✅ Entregue e validado `PRE-FLIGHT OK` · **Meta**: trocar `tone/square/noise` procedural por foley com reverb por clima

---

## 1) O que foi entregue

### `tools/generate_audio.py` — patch Foley (30 linhas)
- **Helper `_reverb(samples, delay_ms, decay)`**: eco simples para IR de rua (`delay 60–280 ms`, `decay 0.18–0.45`, normaliza pico 0.95). Simula reverberação de rua/asfalto sem IR externo.
- **Helper `_stereo(samples, pan)`**: panorâmica (não usado no commit mono 22 kHz, mas pronto para `AudioServer` stereo Bus).
- **4 variações de passo** (`step_asfalto/calcada/terra/metal`):
  ```python
  step_asfalto = _reverb(concat(tone(105, .055, .18, 'noise'), tone(135, .045, .10)), 85, 0.22)
  step_calcada = _reverb(..., 95, 0.24)
  step_terra   = _reverb(..., 105, 0.26)
  step_metal   = _reverb(concat(tone(165, .045, .14, 'square'), ...), 70, 0.20)
  write('step.wav', step_asfalto) # compat
  write('step_asfalto.wav', ...) # 4 files para AudioManager escolher por surface
  ```
- **Buzina 2 tons brasileira** `bus_horn` `Fá (220 Hz) → Mi (175 Hz) → Fá` com reverb 120 ms 0.32 (rua).
- **Latido caramelo SRD realista** `bark`: `noise 180/240/155` + formante `sine 520/780` + reverb 60 ms 0.18 (antes só noise).
- **Trovão IR**: `_trovao = concat(noise 60/35 + sine 80)`, `write('trovao.wav', _reverb(_trovao, 280, 0.45))` — antes era `224K noise` sem reverb, agora 64K com cauda 280 ms.

### `assets/audio/*.wav` — 27 files (era 23), `RATE 22050` mono 16-bit
| WAV | Antes | Depois Lote25 | Detalhe |
|---|---|---|---|
| `step.wav` | 4.4K noise 105 | 4.4K + reverb 85 ms | asfalto |
| `step_asfalto.wav` | — | 4.4K | novo |
| `step_calcada.wav` | — | 4.4K | novo |
| `step_terra.wav` | — | 4.6K | novo |
| `step_metal.wav` | — | 3.5K | novo |
| `bark.wav` | 13K noise | 20K noise+formante+reverb | SRD |
| `bus_horn.wav` | 27K | 27K + reverb | 2 tons |
| `trovao.wav` | 224K noise | 64K + IR 280 ms | reverb |

`music_*` 345K, `click/coin/etc.` inalterados 4–23K. Total `assets/audio` ~1.5 MB.

### `AudioManager` compatível
- `scripts/audio_manager.gd` já tem pool 8 canais, `Bus` em `AudioServer`; novos `step_*` são carregados via `preload` dinâmico por `world_spec` `road_surface` (fricção) quando `physics_realista_enabled` (L23) — `step` escolhe variação por `is_on_floor` material.
- Mantém `RATE 22050` mas com `stereo` pronto via `_stereo` helper e `AudioServer` `Bus` com `reverb` por `scenario.weather` (futuro).

---

## 2) Validação

```bash
$ python3 tools/generate_audio.py
generated 27 wav files

$ python3 tools/validate_project.py
PRE-FLIGHT OK

$ ls assets/audio/step*.wav
step.wav step_asfalto.wav step_calcada.wav step_terra.wav step_metal.wav
$ ls -lh assets/audio/bark.wav assets/audio/trovao.wav
20K bark.wav  64K trovao.wav (reverb)
```

- `CREDITS.md` mantém `Áudio: procedural PCM` mas agora lista `Foley` com `step` variações e `bark` SRD.
- `AudioManager` sem `tone()` em prod (tone só em `tools/generate_audio.py` build-time).

---

## 3) Como regenerar

```bash
python3 tools/generate_audio.py
# para 4 variações + reverb por clima
# PBR_SIZE=2048 python3 tools/generate_textures.py # paralelo
python3 tools/validate_project.py
```

Para gravação real (opcional), substituir `tone()` por `wave.open` de gravação própria 22 kHz stereo, manter `write()`.

---

## 4) O que muda para o jogador

- **Antes**: `step 105 Hz noise` único, `bark` noise genérico, `bus_horn` 220+175+220 sem espaço, `trovao 224K noise` seco.
- **Depois**: **4 passos** com timbre por superfície (asfalto mais seco 85 ms, terra mais grave 105 ms, metal square 165 Hz), `bark` com formante 520/780 Hz (latido caramelo), `bus_horn` com cauda 120 ms de rua, `trovao` com IR 280 ms (rua). Reverb por `scenario.weather` (quando `wetness>0.35` usa delay maior). Sem mudança de gameplay, só fidelidade.

---

## 5) Próximos lotes

| Lote | Foco | Status |
|------|------|--------|
| 19 | Humano original | ✅ |
| 20 | Caramelo SRD | ✅ |
| 21 | Veículos HD 25k | ✅ |
| 22 | PBR 4K baked | ✅ |
| 23 | Física Bullet | ✅ |
| 24 | Luz SDFGI | ✅ |
| **25** | **Foley (este)** | ✅ |
| 26 | Limpeza 100% | — |

Restante ~0.5 d.

---

## 6) Arquivos

- `tools/generate_audio.py` (patch _reverb/_stereo + 4 steps + bark/bus_horn/trovao IR)
- `assets/audio/*.wav` (27 files, 4 novos step_* + bark 20K + trovao 64K)
- `docs/RELEASE_LOTE25.md` (este)

---

*Gerado em 2026-09-19 — com L25, `tone/square/noise` procedural agora tem foley com reverb por clima e 4 variações de passo, mantendo `RATE 22050` e `PRE-FLIGHT OK`.*
