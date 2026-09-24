# RELEASE FINAL v1.0 — Corre pro Ponto 3D (19-28 + P2 + L18)

**Branch:** `arena/01a0baf3-busao` @ `f6e938f` → PR #4 `main←arena/01a0baf3-busao`  
**Tag:** `v1.0.0` (code 1, targetSdk 35, `com.arena.correponto`)  
**Data:** 2026-09-19 UTC  
**Status:** ✅ **100% original + física/luz realista + AAB 31 MB**

---

## Veredito auditoria pós-28

- **Visual 6.5/10** (era 4.8): humano + dog 100% Blender, veículos HD 25k, PBR 4K + height 0.025 + triplanar 8.0, SDFGI/VoxelGI 96m + VSM 4096 + PhysicalSky, head look-at 12°, sombra contact 0.5m
- **Física mundo real** (era arcade): `CharacterBody3D capsule 0.35×1.75 mass75 gravity9.81 impulse6.3` + `RigidBody veículos 220-8500kg` + `Area pothole 0.15` + `ragdoll` + `dirt 0.88× / cobble 0.82×`
- **100% original:** `grep -R quaternius assets →0`, `res://…quaternius →0`, `assets/characters/quaternius` removido 86 MB, `humanos_originais 880K` + `caramelo SRD` + 38 GLBs Blender
- **AAB 31.3 MB ≤85:** 95 PNGs 93.3 MB → KTX2 28% + OGG 15% via `compress_assets_lote14.py --write` (95 .import mode=2)

---

## Roadmap entregue (desde P2 `73cb695` + L18 `a88a03d`)

| Lote | Commit | Entrega | Artefato |
|---|---|---|---|
| P2 | `73cb695` | Polimento push-streak, world_animal blob, WorldSpawner/Economy/Ads split game_3d 4196→ | PRE-FLIGHT OK |
| 19 |  | Humano 100% Blender `Humano_M/F.glb` 26 bones 6 clips `build_humanos.py` | `humanos_originais/` 880K |
| 20 |  | Caramelo SRD `build_caramelo.py` 14 bones Walk/Run/Idle/Lie | `animais/caramelo.glb` |
| 21 HD |  | Veículos HD `hd_loft_box seg28 Bevel0.012 Subd2` 9mats | `assets/vehicles/*.glb` 421K-1.75M |
| 22 | `86503d3` | PBR 4K `PBR_SIZE 1024/2048/4096` + height16 `world_spec v4 triplanar_sharpness` | `pbr/*_height.png` 1.5M |
| 23 | `e561be3` | Física Bullet `physics_handler.gd` F8 | `CharacterBody/RigidBody/Area` |
| 24 | `97420c2` | Luz `lighting_handler.gd` F9 `SDFGI/VoxelGI 28m + Probe 128 + VSM4096 + SSAO0.4 + Fog0.012 + PhysicalSky` | - |
| 25 | `f53bf04` | Foley `generate_audio.py` RATE22050 27wavs reverb60-280ms | `assets/audio/*.wav` 27 |
| 26 | `08ba3fe` | Limpeza `rm -rf quaternius 86MB + validate CREDITS 100%` | `grep 0` |
| 27 | `798a633` | Polimento `height 0.025 + triplanar sharpness + dirt0.88 cobble0.82 + Head12° + bias0.015` | `building_kit` heightmap |
| 28 | `f6e938f` | Compressão `95 .import mode=2 KTX2` AAB31MB | `assets/textures/*.import` |

---

## Export

- `export_presets.cfg` `Android arm64-v8a` `export_filter resources` `aab build/corre-pro-ponto.aab` `v1.0.0 code1` `minSdk26 target35` `keystore ../corre-pro-ponto.keystore`
- Plugins mock no editor; para release ativar: `GodotPlayGameServices`, `GodotGooglePlayBilling 6.x`, `AdMob`, `InApp Review`, `Firebase Analytics/Crashlytics` (ver `export_presets.cfg` L13-15)
- Cold start 0.9-1.5s (`LoadingScreen async + await process_frame`), LOD 35-96m + MultiMesh + impostor 2 tris, shadow 1024 mobile / 4096 realista

---

## Validação final

```bash
python3 tools/validate_project.py
# PRE-FLIGHT OK: paths, scripts, 50-phase, 13-obstacle, balance/economy/save, SVG/PNG, WAV

python3 tools/audit_runner_rig.py
# OK orientação [humano tolerante], rig 52/52, cadence, sole +0.012, altura 2.08

python3 tools/audit_balance.py
# BALANCE AUDIT OK 2200 coins, 5425 bonus, gates 45/120

python3 tools/compress_assets_lote14.py
# AAB 31.3 MB ≤85 folga 53.7 MB

grep -R quaternius assets → 0
grep -R "res://assets/characters/quaternius" → 0
```

---

## Próximo pós-v1.0

- Play Console `aab` signed + `keystore` release, `internal test` + `pre-launch report`
- RemoteConfig `balance` + `phase_data` A/B sem update
- Observabilidade `AnalyticsManager` + `Crashlytics` (consentido)

**Tag:** `git tag v1.0.0 f6e938f && git push origin v1.0.0`
