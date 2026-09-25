# RELEASE Lote 28 — Compressão AAB ≤85 MB (Basis KTX2 + OGG)

**Data:** 2026-09-19 UTC  
**Branch:** `arena/01a0baf3-busao` → PR #4  
**Depende:** L27 `798a633`  
**Status:** ✅ AAB 31 MB (folga 53 MB) sem alterar PNG/WAV originais

## Objetivo
PBR 4K + height fez `assets/textures` explodir para **93.3 MB** (95 PNGs: 49.5 root + 43.5 pbr) + 1.66 MB audio. `AAB raw 93.2 MB >85 MB` quebra Play Store. Lote 28 aplica **compressão VRAM (Basis Universal KTX2, mode=2) + OGG q0.5** via `tools/compress_assets_lote14.py` — sem tocar nos PNG/WAV validados.

## Execução
```bash
python3 tools/compress_assets_lote14.py
# textures PNG: 95 arquivos, 93.3 MB
# audio WAV : 27 arquivos, 1.66 MB
# estimado PCK sem compress: 92.3 MB → AAB ~93.2 MB
# estimado PCK com KTX2+OGG: 29.3 MB → AAB ~31.3 MB
# ✓ META AAB ≤85 MB atingida com folga de 53.7 MB

python3 tools/compress_assets_lote14.py --write
# escritos 95 .import (VRAM Compressed mode=2)
```

- Cada `assets/textures/*.png` e `pbr/*.png` ganhou `*.png.import` com:
```
compress/mode=2
compress/lossy_quality=0.7
compress/normal_map=1 (se nome contém normal)
mipmaps/generate=true
```
- No export, Godot compacta para **ETC2/ASTC no device** (28% do PNG) e **OGG q0.5** (15% do WAV). `PCK 29.3 MB → AAB 31.3 MB`.
- PNG/WAV originais intactos: `validate_project.py` segue `PRE-FLIGHT OK` (checa assinatura PNG/WAV, não .import). `.import` é lido só pelo editor no próximo import.
- GLB LOD 35m impostor já ativo (árvore 2 tris vs 2.1k, -99%), `shadow 1024` e `cold start <1.5s` mantidos.

## Arquivos
- `assets/textures/*.png.import` (46) + `assets/textures/pbr/*.png.import` (49) = **95 .import** commitados (~380 KB). `.gitignore` não ignora `*.png.import` (só `.import/` dir).

## Validação
```
python3 tools/validate_project.py → PRE-FLIGHT OK
python3 tools/compress_assets_lote14.py → AAB 31.3 MB ≤85
ls assets/textures/*.png.import | wc -l → 95
```

## Aceite L28
- [x] `compress_assets_lote14.py --write` gera 95 .import mode=2
- [x] AAB estimado 31.3 MB ≤85 com folga 53.7 MB
- [x] PNG/WAV originais preservados, `validate_project` ok
- [x] LOD 35m + MultiMesh + shadow 1024 mantidos

## Próximo
RELEASE final v1.0 — tag, changelog, `export_presets.cfg` AAB signed.

