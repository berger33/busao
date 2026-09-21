#!/usr/bin/env python3
"""Migra .import de textura para compressao VRAM (mobile-safe).

Uso:
  python3 tools/fix_texture_imports.py          # migra (idempotente)
  python3 tools/fix_texture_imports.py --check  # CI: falha se houver mode=0

Regras:
- importer="texture" com compress/mode=0 (lossless, PNG cru na VRAM) -> =2
  (VRAM Compressed / S3TC-ETC2-ASTC conforme plataforma — Godot escolhe).
- *normal*.png -> compress/normal_map=1 (codificacao correta de normal map).
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


def process(path: Path, check: bool) -> str:
    """Retorna 'ok' | 'fixed' | 'pending'."""
    text = path.read_text(encoding="utf-8")
    if 'importer="texture"' not in text:
        return "ok"
    mode = MODE.search(text)
    if mode is None or mode.group(1) != "0":
        fixed_normal = False
        if "normal" in path.name.lower():
            normal = NORMAL.search(text)
            if normal is not None and normal.group(1) == "0":
                if not check:
                    path.write_text(NORMAL.sub("compress/normal_map=1", text), encoding="utf-8")
                fixed_normal = True
        return "pending" if (check and fixed_normal) else ("fixed" if fixed_normal else "ok")
    if check:
        return "pending"
    text = MODE.sub("compress/mode=2", text)
    if "normal" in path.name.lower():
        text = NORMAL.sub("compress/normal_map=1", text)
    path.write_text(text, encoding="utf-8")
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
