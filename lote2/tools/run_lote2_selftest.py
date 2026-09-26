#!/usr/bin/env python3
"""Autoteste do Lote 2.

Prova que os verificadores pegam defeitos de verdade, rodando cada um contra
arquivos com erro plantado (tests/fixtures). Se um dia alguem afrouxar uma
regra sem querer, este teste falha.

Rode:  python3 tools/run_lote2_selftest.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
FIXTURES = ROOT / "tests" / "fixtures"

# (fixture, trecho que o analisador precisa acusar)
CASOS_ANALISADOR = [
    ("erro_pcss.gd", "light_angular_distance"),
    ("erro_ambiente.gd", "AMBIENT_SOURCE_SKY"),
    ("erro_msaa.gd", "msaa_3d"),
    ("erro_paleta.gd", "paleta"),
]

# (fixture, trecho que o conferidor de nomes precisa acusar)
CASOS_NOMES = [
    ("erro_nome.gd", "_cooldown_frames"),
    ("erro_nome.gd", "_ajusta_tudo"),
]


def rodar(cmd: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def teste_analisador(codigo_real: Path) -> list:
    falhas = []
    for fixture, esperado in CASOS_ANALISADOR:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "tools").mkdir()
            (tmp_path / "scripts").mkdir()
            shutil.copy(TOOLS / "analyze_render_profile.py", tmp_path / "tools")
            shutil.copy(TOOLS / "render_facts.json", tmp_path / "tools")
            shutil.copy(FIXTURES / fixture, tmp_path / "scripts" / "render_quality.gd")
            res = rodar([sys.executable, "tools/analyze_render_profile.py"], tmp_path)
            if res.returncode == 0:
                falhas.append(f"{fixture}: o analisador deixou passar (esperava erro)")
            elif esperado not in res.stdout:
                falhas.append(f"{fixture}: acusou, mas sem citar '{esperado}'")
    # o codigo de verdade precisa passar limpo
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "tools").mkdir()
        (tmp_path / "scripts").mkdir()
        shutil.copy(TOOLS / "analyze_render_profile.py", tmp_path / "tools")
        shutil.copy(TOOLS / "render_facts.json", tmp_path / "tools")
        shutil.copy(codigo_real, tmp_path / "scripts" / "render_quality.gd")
        shutil.copy(ROOT / "project.godot.lote2", tmp_path / "project.godot.lote2")
        res = rodar([sys.executable, "tools/analyze_render_profile.py"], tmp_path)
        if res.returncode != 0:
            falhas.append("codigo real reprovado no analisador:\n" + res.stdout)
    return falhas


def teste_nomes() -> list:
    falhas = []
    for fixture, esperado in CASOS_NOMES:
        res = rodar([sys.executable, str(TOOLS / "check_def_use.py"), str(FIXTURES / fixture)],
                    ROOT)
        if res.returncode == 0:
            falhas.append(f"{fixture}: o conferidor de nomes deixou passar '{esperado}'")
        elif esperado not in res.stdout:
            falhas.append(f"{fixture}: nao citou '{esperado}'")
    res = rodar([sys.executable, str(TOOLS / "check_def_use.py"),
                 str(ROOT / "scripts" / "render_quality.gd")], ROOT)
    if res.returncode != 0:
        falhas.append("codigo real reprovado no conferidor de nomes:\n" + res.stdout)
    return falhas


def teste_sintaxe() -> list:
    falhas = []
    try:
        from gdtoolkit.parser import parser
    except ImportError:
        return ["gdtoolkit nao instalado: pip install gdtoolkit (nao consegui conferir a sintaxe)"]
    for arquivo in [ROOT / "scripts" / "render_quality.gd",
                    ROOT / "scripts" / "game_3d_lote2_patch.gd"]:
        try:
            parser.parse(arquivo.read_text(encoding="utf-8"))
        except Exception as erro:  # noqa: BLE001
            falhas.append(f"{arquivo.name}: sintaxe invalida: {erro}")
    try:
        parser.parse((FIXTURES / "erro_sintaxe.gd").read_text(encoding="utf-8"))
        falhas.append("erro_sintaxe.gd: o parser aceitou um arquivo quebrado de proposito")
    except Exception:  # noqa: BLE001
        pass
    return falhas


def main() -> int:
    falhas = []
    falhas += teste_sintaxe()
    falhas += teste_nomes()
    falhas += teste_analisador(ROOT / "scripts" / "render_quality.gd")
    print("Autoteste do Lote 2")
    print(f"  casos: {len(CASOS_ANALISADOR)} erros plantados + {len(CASOS_NOMES)} nomes errados"
          " + 1 sintaxe quebrada + os arquivos reais")
    for f in falhas:
        print("  FALHA: " + f)
    print(f"  resumo: {len(falhas)} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
