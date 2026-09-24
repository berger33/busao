#!/usr/bin/env python3
"""Regenera (re-baseline) os manifestos SHA-256 de assets-fonte.

Uso:
  python3 tools/rebaseline_provenance.py            # reescreve entradas SHA
  python3 tools/rebaseline_provenance.py --check    # CI: falha se divergir

Cobre assets/characters/humanos_originais e assets/characters/personagens.
Preserva o cabecalho/prosa do PROVENANCE.md e reescreve apenas as linhas de
hash `<sha256>  <arquivo>  (<bytes> bytes)`. Subprodutos do editor
(*.import, *.uid) nunca entram no manifesto (ver validate_project.py).
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "assets/characters/humanos_originais",
    ROOT / "assets/characters/personagens",
]
ENTRY = re.compile(r"^[0-9a-f]{64}\s+\S+\s+\(\d+ bytes\)$")


def entries_for(root: Path) -> list[str]:
    lines = []
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.name == "PROVENANCE.md":
            continue
        if path.name.endswith(".import") or path.name.endswith(".uid"):
            continue
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        lines.append(f"{digest}  {path.name}  ({len(payload)} bytes)")
    return lines


def process(root: Path, check: bool) -> bool:
    """Retorna True se o manifesto ja estava sincronizado."""
    manifest = root / "PROVENANCE.md"
    if not manifest.is_file():
        print(f"SKIP {root.relative_to(ROOT)}: sem PROVENANCE.md")
        return True
    text = manifest.read_text(encoding="utf-8")
    fresh = entries_for(root)
    current = [ln for ln in text.splitlines() if ENTRY.match(ln.strip())]
    if current == fresh:
        print(f"OK {root.relative_to(ROOT)}/PROVENANCE.md ({len(fresh)} entradas)")
        return True
    if check:
        print(f"DIVERGE {root.relative_to(ROOT)}/PROVENANCE.md "
              f"({len(current)} -> {len(fresh)} entradas)")
        return False
    lines = text.splitlines()
    idx = [i for i, ln in enumerate(lines) if ENTRY.match(ln.strip())]
    if not idx:  # sem entradas: anexa ao fim
        while lines and lines[-1].strip() == "":
            lines.pop()
        lines = lines + [""] + fresh
    else:  # substitui o bloco de entradas in-place (preserva cercas/notas)
        lines[idx[0]:idx[-1] + 1] = fresh
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"REBASELINE {root.relative_to(ROOT)}/PROVENANCE.md ({len(fresh)} entradas)")
    return True


def main() -> int:
    check = "--check" in sys.argv
    synced = all(process(root, check) for root in TARGETS)
    return 0 if synced else 1


if __name__ == "__main__":
    sys.exit(main())
