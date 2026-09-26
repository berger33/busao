#!/usr/bin/env python3
"""Autoteste do Lote 3.

Prova que o auditor do cenario pega defeito de verdade: cada caso abaixo planta
um erro na especificacao (ou no kit) e exige que o auditor acuse. Se alguem
afrouxar uma regra sem perceber, este teste falha.

Rode:  python3 tools/run_lote3_selftest.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
SPEC = ROOT / "resources" / "world_spec.json"
KIT = ROOT / "scripts" / "building_kit.gd"
FACTS = TOOLS / "world_facts.json"


def rodar(tmp: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "tools/audit_world.py", "--quieto"],
                          cwd=str(tmp), capture_output=True, text=True)


def preparar(tmp: Path, spec: dict, kit_texto: str = None) -> None:
    (tmp / "tools").mkdir(parents=True, exist_ok=True)
    (tmp / "resources").mkdir(parents=True, exist_ok=True)
    (tmp / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy(TOOLS / "audit_world.py", tmp / "tools")
    shutil.copy(FACTS, tmp / "tools")
    (tmp / "resources" / "world_spec.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    (tmp / "scripts" / "building_kit.gd").write_text(
        kit_texto if kit_texto is not None else KIT.read_text(encoding="utf-8"),
        encoding="utf-8")


def spec_base() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def casos() -> list:
    lista = []

    # 1) faixa central estreita demais para correr
    s = spec_base()
    s["faixas"]["piso_central_m"] = 1.2
    lista.append(("faixa central estreita", s, None, "piso_central_m"))

    # 2) material apontando para textura que o Lote 1 nao gera
    s = spec_base()
    s["materiais"]["pista"]["pbr"] = "cimento_queimado"
    lista.append(("PBR inexistente", s, None, "PBR inexistente"))

    # 3) sombra quente (a referencia tem sombra azulada)
    s = spec_base()
    s["paletas"][0]["sombra"] = [0.55, 0.42, 0.30]
    lista.append(("sombra quente", s, None, "sombra quente"))

    # 4) orcamento acima do teto do Adreno 610
    s = spec_base()
    s["orcamento"]["malhas_max_por_quarteirao"] = 220
    lista.append(("orcamento estourado", s, None, "Adreno 610"))

    # 5) medida fixa no kit (a borda da calcada tem de sair do spec)
    kit = KIT.read_text(encoding="utf-8").replace("_x_calcada(faixas)", "13.9", 1)
    lista.append(("medida fixa no kit", spec_base(), kit, "medida fixa 13.9"))

    # 6) kit sem MultiMesh (nao escala no celular)
    kit = KIT.read_text(encoding="utf-8").replace("MultiMesh", "Node3D")
    lista.append(("kit sem MultiMesh", spec_base(), kit, "MultiMesh"))

    return lista


def main() -> int:
    falhas = []
    # o caso real precisa passar limpo
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        preparar(tmp, spec_base())
        res = rodar(tmp)
        if res.returncode != 0 or "0 problema(s)" not in res.stdout:
            falhas.append("o cenario real foi reprovado:\n" + res.stdout + res.stderr)

    for nome, spec, kit, esperado in casos():
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            preparar(tmp, spec, kit)
            res = rodar(tmp)
            if res.returncode == 0:
                falhas.append(f"{nome}: o auditor deixou passar (esperava erro)")
            elif esperado not in (res.stdout + res.stderr):
                falhas.append(f"{nome}: acusou, mas sem citar '{esperado}'")

    print("Autoteste do Lote 3")
    print(f"  casos: {len(casos())} defeitos plantados + o cenario real")
    for f in falhas:
        print("  FALHA: " + f)
    print(f"  resumo: {len(falhas)} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
