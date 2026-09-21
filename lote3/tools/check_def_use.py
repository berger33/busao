#!/usr/bin/env python3
"""Confere definicao/uso de nomes num script GDScript.

Pega os dois erros que o editor do Godot costuma apontar como
"Identifier not found" / "Function not found":
  - leitura de um membro (_x) que nunca foi declarado com var/const;
  - chamada de uma funcao que nao existe no arquivo.

Rode:  python3 tools/check_def_use.py scripts/render_quality.gd
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Funcoes globais do GDScript (nao precisam ser declaradas).
GLOBAIS = {
    "print", "printerr", "printraw", "prints", "printt", "print_debug", "print_verbose",
    "push_error", "push_warning", "assert", "range", "min", "max", "clamp", "clampi",
    "clampf", "lerp", "lerpf", "abs", "absf", "absi", "floor", "floorf", "floori",
    "ceil", "ceilf", "ceili", "round", "roundf", "roundi", "sqrt", "sin", "cos", "tan",
    "asin", "acos", "atan", "atan2", "pow", "sign", "signf", "signi", "fmod", "fposmod",
    "deg_to_rad", "rad_to_deg", "randf", "randi", "randf_range", "randi_range", "randomize",
    "is_instance_valid", "is_equal_approx", "is_zero_approx", "snapped", "snappedf",
    "move_toward", "remap", "smoothstep", "ease", "pingpong", "wrapf", "wrapi",
    "nearest_po2", "hash", "type_exists", "weakref", "str", "int", "float", "bool",
    "preload", "load", "len", "get_stack", "error_string", "lerp_angle", "posmod", "typeof",
    "floorf", "ceilf", "roundi", "minf", "maxf", "mini", "maxi", "absi", "signi",
}

# Classes do engine usadas como construtor (Nome.new()).
CLASSES = {
    "Environment", "WorldEnvironment", "DirectionalLight3D", "Camera3D", "CameraAttributes",
    "CameraAttributesPractical", "ProceduralSkyMaterial", "PhysicalSkyMaterial", "Sky",
    "Viewport", "Node", "Node3D", "RenderingServer", "Engine", "OS", "Time", "ResourceLoader",
    "Vector2", "Vector3", "Vector4", "Color", "Dictionary", "Array", "String", "PackedByteArray",
    "Image", "ImageTexture", "MeshInstance3D", "StandardMaterial3D", "ParticleProcessMaterial",
}

# Metodos que todo Object/Node ja tem (o script do Lote 2 estende Node).
METODOS_NODE = {
    "get_tree", "get_viewport", "get_node", "get_node_or_null", "get_parent", "add_child",
    "remove_child", "is_inside_tree", "is_node_ready", "set_process", "set_process_input",
    "queue_free", "call_deferred", "emit_signal", "get_children", "find_children", "has_node",
    "set_deferred", "connect", "disconnect", "is_connected", "get_index", "duplicate",
}

CONTROLE = {"if", "elif", "else", "for", "while", "match", "return", "func", "class_name",
            "extends", "and", "or", "not", "in", "is", "as", "await", "signal", "enum",
            "const", "var", "static", "break", "continue", "pass", "self", "super"}

DECL = re.compile(r"^\s*(?:@[A-Za-z_]+(?:\([^)]*\))?\s+)*(?:static\s+)?(?:var|const)\s+([A-Za-z_][A-Za-z0-9_]*)")
FUNC = re.compile(r"^\s*(?:static\s+)?func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
FORVAR = re.compile(r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\b")
PARAM = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^,=]*)?(?:=|,)")
CHAMADA = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
MEMBRO = re.compile(r"\b_[A-Za-z][A-Za-z0-9_]*\b")


def sem_comentario(linha: str) -> str:
    return linha.split("#", 1)[0] if "#" in linha else linha


STRING = re.compile(r'"(?:[^"\\]|\\.)*"')


def sem_strings(linha: str) -> str:
    return STRING.sub('""', linha)


def coletar(texto: str):
    definidos: set = set()
    funcoes: set = set()
    linhas = texto.splitlines()
    i = 0
    while i < len(linhas):
        linha = sem_strings(sem_comentario(linhas[i]))
        if not linha.strip():
            i += 1
            continue
        m = DECL.match(linha)
        if m:
            definidos.add(m.group(1))
        m = FUNC.match(linha)
        if m:
            nome = m.group(1)
            funcoes.add(nome)
            assinatura = linha
            j = i
            while not assinatura.rstrip().endswith(":") and j + 1 < len(linhas):
                j += 1
                assinatura += " " + sem_strings(sem_comentario(linhas[j]))
            abre = assinatura.find("(")
            fecha = assinatura.rfind(")")
            if abre >= 0 and fecha > abre:
                for p in assinatura[abre + 1:fecha].split(","):
                    p = p.strip()
                    if not p:
                        continue
                    nome_param = p.split(":")[0].split("=")[0].strip()
                    if nome_param and nome_param != ")":
                        definidos.add(nome_param)
            i = j
        m = FORVAR.search(linha)
        if m:
            definidos.add(m.group(1))
        i += 1
    return definidos, funcoes



def main() -> int:
    if len(sys.argv) < 2:
        print("uso: check_def_use.py arquivo.gd [arquivo2.gd ...]")
        return 2
    problemas = 0
    avisos = 0
    for nome_arq in sys.argv[1:]:
        caminho = Path(nome_arq)
        if not caminho.exists():
            print(f"ERRO: {caminho} nao encontrado")
            problemas += 1
            continue
        texto = caminho.read_text(encoding="utf-8")
        definidos, funcoes = coletar(texto)
        chamadas: set = set()
        membros: dict = {}
        for num, linha in enumerate(texto.splitlines(), start=1):
            linha = sem_strings(sem_comentario(linha))
            if not linha.strip():
                continue
            for m in CHAMADA.finditer(linha):
                nome = m.group(1)
                if nome in CONTROLE:
                    continue
                if m.start() > 0 and linha[m.start() - 1] == ".":
                    continue  # chamada de metodo de um objeto: obj.metodo()
                chamadas.add(nome)
                if nome in GLOBAIS or nome in CLASSES or nome in funcoes or nome in definidos:
                    continue
                if nome in METODOS_NODE:
                    continue
                if nome[0].isupper():
                    continue  # construtor de classe do engine
                print(f"ERRO {caminho.name}:{num} funcao desconhecida: {nome}()")
                problemas += 1
            for m in MEMBRO.finditer(linha):
                nome = m.group(0)
                if nome in definidos or nome in funcoes or nome in {"__init__"}:
                    continue
                if nome.split(".")[0] in CLASSES:
                    continue
                if re.search(r"\b(?:var|const)\s+" + nome + r"\b", linha):
                    continue  # declaracao local na propria linha (var/const)
                membros.setdefault(nome, num)
        for nome, num in sorted(membros.items(), key=lambda kv: kv[1]):
            print(f"ERRO {caminho.name}:{num} membro sem declaracao: {nome}")
            problemas += 1
        nao_usadas = sorted(f for f in funcoes if f not in chamadas and not f.startswith("_"))
        for f in nao_usadas:
            print(f"AVISO {caminho.name}: funcao publica nunca chamada: {f}()")
            avisos += 1
    print(f"resumo: {problemas} problema(s), {avisos} aviso(s)")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
