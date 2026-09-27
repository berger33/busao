#!/usr/bin/env python3
"""Migra .import de textura para compressao VRAM (mobile-safe).

Uso:
  python3 tools/fix_texture_imports.py          # migra (idempotente)
  python3 tools/fix_texture_imports.py --check  # CI: falha se houver mode=0

Regras:
- importer="texture" com compress/mode=0 (lossless, PNG cru na VRAM) -> =2
  (VRAM Compressed / S3TC-ETC2-ASTC conforme plataforma — Godot escolhe).
- *normal*.png -> compress/normal_map=1 (codificacao correta de normal map).
- mipmaps/generate=false -> =true. Os materiais pedem
  TEXTURE_FILTER_LINEAR_WITH_MIPMAPS; sem a cadeia de mipmap a GPU amostra 1
  texel por pixel em superficie inclinada/distante e o granulado fino da
  textura vira cintilacao e "pontos pretos" no asfalto e na calcada.
- Remove o bloco metadata bogus {"vram_texture": ...} (2026-09-21, engine
  real): chave desconhecida faz o importador recusar a textura inteira
  ("Unexpected identifier 'vram_texture'"). Blocos com outras chaves sao
  preservados.
- Audio (.wav), cenas e outros importers: intocados.
- Idempotente: segunda passada nao altera nada.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODE = re.compile(r"^compress/mode=(\d+)\s*$", re.MULTILINE)
NORMAL = re.compile(r"^compress/normal_map=(\d+)\s*$", re.MULTILINE)
MIPMAPS = re.compile(r"^mipmaps/generate=(true|false)\s*$", re.MULTILINE)
BOGUS_META = re.compile(r'\nmetadata=\{\n"vram_texture": (?:true|false)\n\}\n')


def _fix_mode(text: str) -> str:
    """compress/mode=0 (PNG cru na VRAM) -> 2 (VRAM Compressed)."""
    match = MODE.search(text)
    if match is not None and match.group(1) == "0":
        return MODE.sub("compress/mode=2", text)
    return text


def _fix_normal(text: str, name: str) -> str:
    if "normal" not in name.lower():
        return text
    match = NORMAL.search(text)
    if match is not None and match.group(1) == "0":
        return NORMAL.sub("compress/normal_map=1", text)
    return text


def _fix_mipmaps(text: str) -> str:
    """Liga a cadeia de mipmap: sem ela o filtro trilinear dos materiais cai
    para amostragem 1:1 e a textura serrilha/cintila ao longe."""
    match = MIPMAPS.search(text)
    if match is not None and match.group(1) == "false":
        return MIPMAPS.sub("mipmaps/generate=true", text)
    return text


def process(path: Path, check: bool) -> str:
    """Retorna 'ok' | 'fixed' | 'pending'."""
    text = path.read_text(encoding="utf-8")
    if 'importer="texture"' not in text:
        return "ok"
    updated = BOGUS_META.sub("\n", text)
    updated = _fix_mode(updated)
    updated = _fix_normal(updated, path.name)
    updated = _fix_mipmaps(updated)
    if updated == text:
        return "ok"
    if check:
        return "pending"
    path.write_text(updated, encoding="utf-8")
    return "fixed"


def main() -> int:
    check = "--check" in sys.argv
    stats = {"ok": 0, "fixed": 0, "pending": 0}
    for path in sorted(ROOT.rglob("*.import")):
        if ".godot" in path.parts:
            continue
        stats[process(path, check)] += 1
    print(f"imports textura: ok={stats['ok']} fixed={stats['fixed']} pending={stats['pending']}")
    if check and (stats["pending"] or stats["fixed"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
