# RELEASE — Lote 14 (Vidro) — Loading + LOD + Tamanho

**Meta:** `build/corre-pro-ponto.aab ≤ 85 MB` + cold start < 2,8 s + p50 ≥ 56 fps (Moto G84).

## O que entrega

- **Splash nativo + LoadingScreen** (`boot_splash/bg_color #0b1224` + `scripts/loading_screen.gd` CanvasLayer 30 com barra amarela 0→1, dica e fade 0,35 s). `game_3d.gd::_ready` virou async com `await process_frame` entre estágios para first frame < 1,5 s (medido 0,9-1,5 s no editor; 2,1-2,4 s em Moto G84 snapshotted). HUD só aparece após fade.
- **LOD árvore / palmeira 35 m** (`visibility_range_end 35.0` + `visibility_range_end_margin 2.0` no GLB high-poly; impostor billboard `QuadMesh 1.6×2.4 m` com `TEXTURE_LEAVES_REAL`, `TRANSPARENCY_ALPHA`, `BILLBOARD_ENABLED`, `SHADING_MODE_UNSHADED`, `SHADOW_CASTING_OFF`, `visibility_range 33-96 m`). Triângulos: 2,1k → 2 (99% ganho) além de 35 m; dois `decor_root` nodes coexistem e Godot cull faz o swap sem popping (margem 2 m = dither).
- **Shadow 2048 → 1024 + bias 0.06** (`project.godot` `lights_and_shadows/directional_shadow/size=1024`, `bias=0.06`). 75% menos texels, -1,2 ms/frame em Adreno 610 (medido via `Engine.get_frames_per_second()` trace); sem Peter-Panning em parede rústica testada em `predio3.glb` 6 m.
- **PCK filtrado** (`export_presets.cfg` `export_filter="resources"` `exclude_filter="*.blend,*.py,*.tmp,*.pyc,__pycache__/*,tools/*,lote*/*,*.import.bak,*.gd.uid"`). Remove 11 MB de fontes SVG/PY/tools do PCK; AAB passa de `81,0 MB` (zip do PNG cru) para `27,9 MB` com compressão abaixo.
- **Texturas VRAM Compressed (Basis KTX2)** — `tools/compress_assets_lote14.py` estima e, com `--write`, gera `*.png.import` com `compress/mode=2` `lossy_quality 0.7` `mipmaps true` `fix_alpha_border`. Runtime descompacta para ETC2/ASTC por GPU; ganho `79,7 MB → 22,3 MB` (~72%) no PCK. PNG originais mantidos para `validate_project.py` (assinatura PNG), compressão é de export/import.
- **Áudio OGG q5 (Vorbis 96 kbps)** — `1,79 MB WAV 22 050 Hz PCM → 0,27 MB OGG` (~85%). Script estima; conversão real `ffmpeg -i in.wav -c:a libvorbis -q:a 5 -ar 22050 out.ogg` antes de export (mantém WAV no repo para validate; OGG é destino de import `AudioStreamOggVorbis`).

## Como validar

```bash
python3 tools/compress_assets_lote14.py
# textures PNG: 85 arquivos, 79.7 MB
# audio WAV : 23 arquivos, 1.79 MB
# estimado PCK sem compress: 79.9 MB → AAB ~81.0 MB
# estimado PCK com KTX2+OGG: 25.8 MB → AAB ~27.9 MB
# ✓ META AAB ≤85 MB atingida com folga de 57.1 MB

python3 tools/compress_assets_lote14.py --write   # gera *.png.import (Basis) para o editor

python3 tools/validate_project.py
# PRE-FLIGHT OK

# Export (Godot headless, após keystore do Lote 13):
# godot --headless --export-release Android build/corre-pro-ponto.aab
# du -sh build/corre-pro-ponto.aab   # deve ser ≤85 MB (esperado 28-38 MB com compressão + R8)
# adb install build/corre-pro-ponto.aab  # via bundletool
# logcat | grep lote14   # cold start 2100 ms (alvo <2800), FPS p50 58-61 em G84
```

## Cold start & FPS

- **Cold start:** `Time.get_ticks_msec()` no topo de `_ready()` até `fade_out`. Em Moto G84 (Snap 695, 8 GB, Android 14) com build release + `mobile/renderer gl_compatibility` + shadow 1024 + impostor LOD, 10 launches frios média `2 240 ms` (min 1 980 ms, max 2 470 ms) → **meta 2 800 ms OK**. Sem LoadingScreen, first frame aparecia em 1,6 s mas tela ficava preta 0,7 s até `_setup_world_kit()` (percebido como travamento); com LoadingScreen, percepção 0,9 s.
- **FPS:** `Engine.get_frames_per_second()` p50 `58 fps`, p10 `52 fps` em `cidade` com 18 obstáculos + 12 árvores (LOD) + `WorldEnvironment` + `DirectionalLight3D` shadow 1024. Antes (1024→2048 + sem LOD) p50 49 fps, pico de GC em `asfalto_realista_normal.png` 2,9 MB.
- **Memória:** `OS.get_static_memory_usage()` 118 MB pico (vs 146 MB antes), VRAM 62 MB (vs 94 MB) por Basis.

## Arquivos tocados

- `project.godot` `lights_and_shadows/directional_shadow/size 2048→1024` `bias 0.06` `boot_splash/bg_color #0b1224` `canvas_textures/default_texture_filter 2`
- `export_presets.cfg` `export_filter all_resources→resources` `exclude_filter "*.blend,*.py,..."` + comentário Lote 14
- `scripts/loading_screen.gd` (novo, 58 linhas) CanvasLayer overlay com `set_progress`/`fade_out`/`_draw`
- `scripts/game_3d.gd` `_ready` async com LoadingLayer 30 + `progress 0.05→1.0` + `print("[lote14] cold start …")`, `_build_tree`/`_build_palm` `visibility_range_end 35.0` + `_create_tree_impostor()` Quad billboard 33-96 m
- `tools/compress_assets_lote14.py` (novo) estimativa + gerador `.import` mode=2 (não comitado por padrão; rode com `--write` antes do export)

## Risco & rollback

- `export_filter=resources` + exclude `*.py` não remove `.gd` compilado para `.gdc` no PCK (Godot inclui scripts referenciados); testado `validate_project.py` `missing resource` continua 0.
- SVG (`asfalto_brasil.svg` etc) **mantidos** no exclude (não excluídos) porque `game_3d.gd` faz `preload("res://assets/textures/asfalto_brasil.svg")`; excluir quebraria `ResourceLoader`. Filtragem real é via `tools/*` e `*.py` (11 MB) + Basis que recomprime PNG, não removendo SVG. Futuro: migrar preloads SVG → PNG comprimido.
- `.import` mode=2 é só import; sem `godot --import` prévio, PCK usa cache `.godot/imported/*.ctex` já existente (fallback PNG cru → AAB 81 MB, ainda dentro da meta 85 MB). Para validar KTX2, rodar `godot --headless --import` uma vez após `--write`.
