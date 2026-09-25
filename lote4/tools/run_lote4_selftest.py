#!/usr/bin/env python3
"""Autoteste do Lote 4 (clima).

Cada caso planta um defeito de clima (no spec, no script ou num asset) e exige
que o auditor acuse. Isso e o que garante que uma regra afrouxada nao passe
despercebida - inclusive a armadilha do `sky_cover`, que e TEXTURA e nao numero.

Rode:  python3 tools/run_lote4_selftest.py
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
SPEC = ROOT / "resources" / "weather_spec.json"
KIT = ROOT / "tests" / "fixtures" / "world_spec.json"
SCRIPT = ROOT / "scripts" / "weather_system.gd"
NUVENS = ROOT / "assets" / "textures" / "ceu" / "nuvens.png"
TROVAO = ROOT / "assets" / "audio" / "trovao.wav"


def preparar(tmp: Path) -> None:
    for pasta in ("tools", "resources", "scripts", "assets/textures/ceu", "assets/audio", "docs",
                  "tests/fixtures"):
        (tmp / pasta).mkdir(parents=True, exist_ok=True)
    shutil.copy(TOOLS / "audit_lighting.py", tmp / "tools")
    shutil.copy(SPEC, tmp / "resources" / "weather_spec.json")
    shutil.copy(KIT, tmp / "tests" / "fixtures" / "world_spec.json")
    shutil.copy(SCRIPT, tmp / "scripts" / "weather_system.gd")
    shutil.copy(NUVENS, tmp / "assets" / "textures" / "ceu" / "nuvens.png")
    shutil.copy(TROVAO, tmp / "assets" / "audio" / "trovao.wav")


def rodar(tmp: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "tools/audit_lighting.py", "--quieto"],
                          cwd=str(tmp), capture_output=True, text=True, env=os.environ.copy())


def spec_em(tmp: Path) -> dict:
    return json.loads((tmp / "resources" / "weather_spec.json").read_text(encoding="utf-8"))


def salvar_spec(tmp: Path, spec: dict) -> None:
    (tmp / "resources" / "weather_spec.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")


def escrever_wav(caminho: Path, pico: float, segundos: float = 2.6) -> None:
    n = int(44100 * segundos)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"".join(struct.pack("<h", int(pico * 32767 * (0.6 + 0.4 * (i % 7) / 7)))
                               for i in range(n)))


def main() -> int:
    falhas = []

    # 1) o pacote real tem de passar limpo
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        preparar(tmp)
        res = rodar(tmp)
        if res.returncode != 0 or "0 problema(s)" not in res.stdout:
            falhas.append("o pacote real foi reprovado:\n" + res.stdout + res.stderr)

    pulados = []

    def caso(nome: str, esperado: str, mexer) -> None:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            preparar(tmp)
            try:
                mexer(tmp)
            except RuntimeError as erro:
                if "PIL_AUSENTE" in str(erro):
                    pulados.append(nome)
                    return
                raise
            res = rodar(tmp)
            saida = res.stdout + res.stderr
            if res.returncode == 0:
                falhas.append(f"{nome}: o auditor deixou passar (esperava erro)")
            elif esperado not in saida:
                falhas.append(f"{nome}: acusou, mas sem citar '{esperado}'\n{saida}")

    def molhado_fosco(tmp: Path) -> None:
        s = spec_em(tmp)
        s["molhado"]["materiais"]["pista"]["rugosidade_molhada"] = 0.9
        salvar_spec(tmp, s)

    def raio_no_nublado(tmp: Path) -> None:
        s = spec_em(tmp)
        s["relampago"]["estados"].append("nublado")
        salvar_spec(tmp, s)

    def chuva_estourada(tmp: Path) -> None:
        s = spec_em(tmp)
        s["chuva"]["estados"]["tempestade"]["quantidade"] = 5000
        salvar_spec(tmp, s)

    def pingo_grosso(tmp: Path) -> None:
        s = spec_em(tmp)
        s["chuva"]["malha_m"] = [0.3, 0.7, 0.3]
        salvar_spec(tmp, s)

    def poca_preta(tmp: Path) -> None:
        s = spec_em(tmp)
        s["molhado"]["materiais"]["pista"]["albedo_molhado"] = 0.2
        salvar_spec(tmp, s)

    def trecho_trocado(tmp: Path) -> None:
        s = spec_em(tmp)
        s["pocas"]["trecho_m"] = 20.0
        salvar_spec(tmp, s)

    def sem_semente(tmp: Path) -> None:
        p = tmp / "scripts" / "weather_system.gd"
        texto = p.read_text(encoding="utf-8").replace("_rng.seed = int(spec.get(\"seed\", 1)) * 2654435761 + 17",
                                                      "randomize()")
        p.write_text(texto, encoding="utf-8")

    def semente_apagada(tmp: Path) -> None:
        p = tmp / "scripts" / "weather_system.gd"
        texto = p.read_text(encoding="utf-8").replace(
            "_rng.seed = int(spec.get(\"seed\", 1)) * 2654435761 + 17", "")
        p.write_text(texto, encoding="utf-8")

    def sky_cover_numero(tmp: Path) -> None:
        p = tmp / "scripts" / "weather_system.gd"
        texto = p.read_text(encoding="utf-8").replace("proc.sky_cover = null",
                                                      "proc.sky_cover = 0.5")
        p.write_text(texto, encoding="utf-8")

    def nuvem_com_emenda(tmp: Path) -> None:
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("PIL_AUSENTE")
        caminho = tmp / "assets" / "textures" / "ceu" / "nuvens.png"
        img = Image.open(caminho).convert("RGB")
        px = img.load()
        w, h = img.size
        for y in range(h):
            px[w - 1, y] = (255, 255, 255)
            px[0, y] = (0, 0, 0)
        img.save(caminho)

    def trovao_fraco(tmp: Path) -> None:
        escrever_wav(tmp / "assets" / "audio" / "trovao.wav", pico=0.35)

    caso("asfalto molhado mais fosco que seco", "MAIS fosco", molhado_fosco)
    caso("relampago no ceu limpo/nublado", "sem ceu carregado", raio_no_nublado)
    caso("chuva acima do orcamento", "estoura o orcamento", chuva_estourada)
    caso("pingo grosso demais", "pingo fino", pingo_grosso)
    caso("poca/asfalto escuro demais", "escurece demais", poca_preta)
    caso("pocas fora do compasso do quarteirao", "casar com o quarteirao", trecho_trocado)
    caso("script usando randomize()", "quebra o determinismo", sem_semente)
    caso("script sem a semente do spec", "precisa da semente do spec", semente_apagada)
    caso("sky_cover recebendo numero", "sky_cover e Texture2D", sky_cover_numero)
    caso("nuvem com emenda no ceu", "emenda no horizontal", nuvem_com_emenda)
    caso("trovao fraco demais", "pico do trovao", trovao_fraco)

    print("Autoteste do Lote 4 (clima)")
    print(f"  casos: {11 - len(pulados)} defeitos plantados + o pacote real"
          + (f" ({len(pulados)} pulado(s) por falta de Pillow: {', '.join(pulados)})" if pulados else ""))
    for f in falhas:
        print("  FALHA: " + f)
    print(f"  resumo: {len(falhas)} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
