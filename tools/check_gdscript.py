"""Analise estatica de GDScript que reproduz o analisador do Godot 4.

Existe porque nem toda maquina tem um binario Godot disponivel para rodar
`godot --headless --editor --quit`: este script pega as mesmas classes de erro
que impedem o projeto de abrir e as mesmas advertencias que o editor mostra.

Erros:
  UNDECLARED       - identificador nao declarado no escopo (ex.: `chrome`)
  DUPLICATE        - variavel ja declarada no mesmo escopo (ex.: `chapter`)
  TOO_MANY_ARGS    - argumentos demais em chamada de engine/script
  TOO_FEW_ARGS     - argumentos de menos
  UNKNOWN_METHOD   - metodo inexistente em receptor com tipo conhecido
  UNKNOWN_MEMBER   - propriedade inexistente em receptor de tipo conhecido
                     (ex.: `mesh.receive_shadow`, API do Godot 3)
  SHADOWED_VARIABLE / SHADOWED_VARIABLE_BASE_CLASS - local ou parametro com o
                     mesmo nome de um membro do proprio script, de um script pai
                     ou de uma classe nativa (ex.: `name`, `scale`, `size`,
                     `position`, `ready`); o Godot mostra isso como aviso no
                     editor, e as mensagens saem iguais as dele
  SHADOWED_GLOBAL_IDENTIFIER - local com nome de funcao, classe ou tipo do engine
  MISSING_RETURN   - funcao com tipo de retorno sem nenhum `return`
  ASSIGN_CONST     - atribuicao a constante
Advertencias:
  INTEGER_DIVISION - divisao inteira (parte decimal descartada)

Sobre UNKNOWN_MEMBER: atribuicao a propriedade inexistente sempre entra na
lista (o Godot 4 quebra em tempo de execucao). Leitura de membro inexistente
so entra quando o nome existia no Godot 3 e sumiu no 4 (mapa GODOT4_RENAMES),
porque o proprio engine trata `evento.position` em `InputEvent` como acesso
inseguro e nao como erro.

Dependencias:
  pip install gdtoolkit
  opcional: XMLs de doc/classes do Godot (para checar a API do engine), por
  exemplo extraidos do tarball de fontes da versao usada pelo projeto.

Uso:
  python3 tools/check_gdscript.py                     # projeto atual
  python3 tools/check_gdscript.py --godot-doc /caminho/doc/classes
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from lark import Token, Tree
from gdtoolkit.parser import parser as gdparser


# --------------------------------------------------------------------------
# Engine database (Godot doc/classes XML)
# --------------------------------------------------------------------------
@dataclass
class Sig:
    name: str
    required: int
    maximum: int | None  # None => vararg
    returns: str = ""    # tipo de retorno ("" => desconhecido)


class EngineDB:
    def __init__(self, doc_dir: Path):
        self.classes: set[str] = set()
        self.inherits: dict[str, str] = {}
        self.methods: dict[str, dict[str, Sig]] = {}
        self.members: dict[str, set[str]] = {}
        self.member_types: dict[str, dict[str, str]] = {}
        self.consts: dict[str, set[str]] = {}
        self.signals: dict[str, set[str]] = {}
        self.constructors: dict[str, list[Sig]] = {}
        self.global_consts: set[str] = set()
        self.global_funcs: dict[str, Sig] = {}
        for path in sorted(doc_dir.glob("*.xml")):
            self._load(path)

    @staticmethod
    def _sig(node: ET.Element, name: str) -> Sig:
        params = list(node.findall("param"))
        required = sum(1 for p in params if "default" not in p.attrib)
        vararg = "vararg" in node.attrib.get("qualifiers", "").split()
        ret = node.find("return")
        returns = ret.attrib.get("type", "") if ret is not None else ""
        return Sig(name, required, None if vararg else len(params), returns)

    def _load(self, path: Path) -> None:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            return
        name = root.attrib.get("name", "")
        if name == "@GlobalScope":
            for c in root.iter("constant"):
                self.global_consts.add(c.attrib["name"])
            for m in root.iter("method"):
                self.global_funcs[m.attrib["name"]] = self._sig(m, m.attrib["name"])
            return
        if not name or name.startswith("@"):
            return
        self.classes.add(name)
        self.inherits[name] = root.attrib.get("inherits", "")
        methods: dict[str, Sig] = {}
        for m in root.iter("method"):
            methods[m.attrib["name"]] = self._sig(m, m.attrib["name"])
        self.methods[name] = methods
        members = list(root.iter("member"))
        self.members[name] = {m.attrib["name"] for m in members}
        self.member_types[name] = {m.attrib["name"]: m.attrib.get("type", "") for m in members}
        self.consts[name] = {c.attrib["name"] for c in root.iter("constant")}
        self.signals[name] = {s.attrib["name"] for s in root.iter("signal")}
        ctors = [self._sig(c, "new") for c in root.iter("constructor")]
        if ctors:
            self.constructors[name] = ctors

    def chain(self, cls: str):
        seen = set()
        while cls and cls not in seen:
            seen.add(cls)
            yield cls
            cls = self.inherits.get(cls, "")

    def find_method(self, cls: str, method: str) -> Sig | None:
        for c in self.chain(cls):
            sig = self.methods.get(c, {}).get(method)
            if sig:
                return sig
        return None

    def symbol_kind(self, cls: str, name: str) -> tuple[str, str] | None:
        """(tipo do simbolo, classe nativa onde ele nasce)."""
        cur = cls
        seen: set[str] = set()
        while cur and cur not in seen:
            seen.add(cur)
            if name in self.methods.get(cur, {}):
                return ("method", cur)
            if name in self.signals.get(cur, set()):
                return ("signal", cur)
            if name in self.members.get(cur, set()):
                return ("property", cur)
            if name in self.consts.get(cur, set()):
                return ("constant", cur)
            cur = self.inherits.get(cur, "")
        return None

    def has_member(self, cls: str, attr: str) -> bool:
        for c in self.chain(cls):
            if attr in self.members.get(c, set()) or attr in self.consts.get(c, set()):
                return True
            if attr in self.signals.get(c, set()):
                return True
        return False

    def member_type(self, cls: str, attr: str) -> str:
        """Static type of a documented member (walking the inheritance chain)."""
        for c in self.chain(cls):
            elem = self.member_types.get(c, {}).get(attr)
            if elem:
                return elem
        return ""


# --------------------------------------------------------------------------
# Project model
# --------------------------------------------------------------------------
@dataclass
class ScriptInfo:
    path: Path
    cls: str = ""
    extends: str = ""
    members: dict[str, str] = field(default_factory=dict)   # name -> type
    consts: dict[str, str] = field(default_factory=dict)    # name -> type/script
    enums: dict[str, list[str]] = field(default_factory=dict)
    signals: set[str] = field(default_factory=set)
    funcs: dict[str, Sig] = field(default_factory=dict)
    ret_types: dict[str, str] = field(default_factory=dict)
    preloads: dict[str, str] = field(default_factory=dict)  # const name -> res:// path
    symbol_kinds: dict[str, tuple[str, int]] = field(default_factory=dict)  # nome -> (tipo, linha)

    def symbol_kind(self, name: str) -> tuple[str, int] | None:
        return self.symbol_kinds.get(name)

    @property
    def symbols(self) -> set[str]:
        out = set(self.members) | set(self.consts) | set(self.signals) | set(self.funcs)
        for values in self.enums.values():
            out |= set(values)
        out |= set(self.enums)
        return out


def tree_walk(nodes) -> list:
    """Depth-first walk; lambdas count as leaves (their returns are their own)."""
    out = []
    stack = list(nodes)
    while stack:
        n = stack.pop(0)
        if isinstance(n, Tree):
            out.append(n)
            if str(n.data) == "lambda":
                continue
            stack = list(n.children) + stack
    return out


def text_of(node) -> str:
    if isinstance(node, Token):
        return str(node)
    if isinstance(node, Tree):
        return "".join(text_of(c) for c in node.children)
    return ""


def token_nodes(node) -> list[Token]:
    out: list[Token] = []

    def walk(n):
        if isinstance(n, Token):
            out.append(n)
        elif isinstance(n, Tree):
            for c in n.children:
                walk(c)

    walk(node)
    return out


def token_trees(node) -> list:
    out = []

    def walk(n):
        if isinstance(n, Tree):
            out.append(n)
            for c in n.children:
                walk(c)

    walk(node)
    return out


def literal_type_of(node) -> str:
    """Literal type inference used at load time (no engine access)."""
    if isinstance(node, Token):
        if node.type == "NUMBER":
            raw = str(node)
            return "float" if ("." in raw or "e" in raw.lower()) else "int"
        if node.type == "REGULAR_STRING":
            return "String"
        return ""
    if isinstance(node, Tree):
        if str(node.data) in ("true", "false"):
            return "bool"
        if str(node.data) == "expr" and node.children:
            return literal_type_of(node.children[0])
    return ""


def parse(path: Path) -> Tree:
    return gdparser.parse(path.read_text(encoding="utf-8"))


def load_script(path: Path) -> ScriptInfo:
    info = ScriptInfo(path=path)
    tree = parse(path)
    info.tree = tree  # type: ignore[attr-defined]
    for child in tree.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "classname_stmt":
            info.cls = str(token_nodes(child)[0])
        elif child.data == "extends_stmt":
            info.extends = str(token_nodes(child)[0])
        elif child.data == "const_stmt":
            inner = child.children[0] if child.children else None
            toks = token_nodes(child)
            name = str(toks[0])
            info.symbol_kinds[name] = ("constant", int(toks[0].line))
            if isinstance(inner, Tree) and inner.data == "const_assigned":
                info.consts[name] = ""
            else:
                info.consts.setdefault(name, "")
            raw = text_of(child)
            m = re.search(r'preload\("res://([^"]+)"\)', raw)
            if m:
                info.preloads[name] = "res://" + m.group(1)
        elif child.data == "class_var_stmt":
            toks = token_nodes(child)
            info.symbol_kinds[str(toks[0])] = ("variable", int(toks[0].line))
            typed = next((t for t in toks if t.type == "TYPE_HINT"), None)
            if typed:
                info.members[str(toks[0])] = str(typed)
            else:
                inner_expr = next((c for c in token_trees(child) if isinstance(c, Tree) and str(c.data) == "expr"), None)
                info.members[str(toks[0])] = literal_type_of(inner_expr)
        elif child.data == "signal_stmt":
            toks = token_nodes(child)
            info.signals.add(str(toks[0]))
            info.symbol_kinds[str(toks[0])] = ("signal", int(toks[0].line))
        elif child.data == "enum_stmt":
            toks = token_nodes(child)
            if toks:
                info.enums[str(toks[0])] = [str(t) for t in toks[1:]]
                info.symbol_kinds[str(toks[0])] = ("enum", int(toks[0].line))
        elif child.data in ("func_def", "static_func_def"):
            func = child.children[0] if child.data == "static_func_def" else child
            header = func.children[0]
            name = str(token_nodes(header)[0])
            args = header.children[1] if len(header.children) > 1 else None
            required = maximum = 0
            vararg = False
            if isinstance(args, Tree):
                for a in args.children:
                    if not isinstance(a, Tree):
                        continue
                    if a.data == "func_arg_variadic":
                        vararg = True
                    elif a.data.startswith("func_arg"):
                        maximum += 1
                        typed = [t for t in token_nodes(a) if t.type == "TYPE_HINT"]
                        has_expr = any(isinstance(c, Tree) and c.data == "expr" for c in a.children)
                        if not has_expr:
                            required += 1
                if not isinstance(args, Tree):
                    pass
            elif args is not None:
                pass
            ret = ""
            for t in token_nodes(header):
                if t.type == "TYPE_HINT":
                    ret = str(t)
            info.funcs[name] = Sig(name, required, None if vararg else maximum, ret)
            info.ret_types[name] = ret
            name_tok = next((t for t in token_nodes(header) if t.type == "NAME"), None)
            if name_tok is not None:
                info.symbol_kinds[name] = ("function", int(name_tok.line))
    return info


def parse_autoloads(project: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    cfg = project / "project.godot"
    if not cfg.exists():
        return out
    section = ""
    for line in cfg.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif section == "autoload" and "=" in line:
            name, value = line.split("=", 1)
            path = value.strip().strip('"').lstrip("*")
            if path.startswith("res://"):
                out[name.strip()] = path
    return out


# --------------------------------------------------------------------------
# Scope analysis
# --------------------------------------------------------------------------
class Scope:
    def __init__(self, parent: "Scope | None" = None, label: str = ""):
        self.parent = parent
        self.label = label
        self.names: dict[str, str] = {}  # name -> type

    def lookup(self, name: str, stop_at: "Scope | None" = None) -> str | None:
        scope: Scope | None = self
        while scope is not None:
            if name in scope.names:
                return scope.names[name] or ""
            if scope is stop_at:
                break
            scope = scope.parent
        return None

    def declared_in_chain(self, name: str, stop_at: "Scope | None" = None) -> bool:
        return self.lookup(name, stop_at) is not None


@dataclass
class Problem:
    path: Path
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code}: {self.message}"


class Analyzer:
    def __init__(self, project: Path, docs: Path):
        self.project = project
        self.engine = EngineDB(docs)
        self.scripts: dict[Path, ScriptInfo] = {}
        self.by_cls: dict[str, ScriptInfo] = {}
        self.autoloads = parse_autoloads(project)
        self.problems: list[Problem] = []
        self.script_dirs = sorted({p.parent for p in project.rglob("*.gd")})
        for path in sorted(project.rglob("*.gd")):
            info = load_script(path)
            self.scripts[path] = info
            if info.cls:
                self.by_cls[info.cls] = info
        # resolve preload consts to scripts
        for info in self.scripts.values():
            resolved: dict[str, ScriptInfo] = {}
            for const, res in info.preloads.items():
                target = project / res.removeprefix("res://")
                if target in self.scripts:
                    resolved[const] = self.scripts[target]
            info.resolved = resolved  # type: ignore[attr-defined]

    # -- helpers -----------------------------------------------------------
    def is_known_global(self, name: str) -> bool:
        return (
            name in self.engine.classes
            or name in self.engine.global_consts
            or name in self.engine.global_funcs
            or name in self.by_cls
            or name in self.autoloads
            or name in LANGUAGE
        )

    def script_of(self, info: ScriptInfo, name: str) -> ScriptInfo | None:
        resolved = getattr(info, "resolved", {})
        if name in resolved:
            return resolved[name]
        if name in self.autoloads:
            target = self.project / self.autoloads[name].removeprefix("res://")
            return self.scripts.get(target)
        if name in self.by_cls:
            return self.by_cls[name]
        return None

    def error(self, path: Path, node, code: str, message: str) -> None:
        line = getattr(node, "line", None) or getattr(node, "line", 0) or 0
        self.problems.append(Problem(path, line, code, message))

    # -- entry -------------------------------------------------------------
    def check_class_symbols(self, info: ScriptInfo) -> None:
        seen: dict[str, int] = {}
        for name in list(info.members) + list(info.consts) + sorted(info.signals):
            seen[name] = seen.get(name, 0) + 1
        # duplicate member declarations (Godot: "Variable X is already declared")
        declared: list[str] = []
        for child in info.tree.children:  # type: ignore[attr-defined]
            if isinstance(child, Tree) and child.data == "class_var_stmt":
                tok = token_nodes(child)[0] if token_nodes(child) else None
                if tok is not None:
                    name = str(tok)
                    if name in declared:
                        self.error(info.path, tok, "DUPLICATE",
                                   f'Variable "{name}" is already declared in this scope.')
                    declared.append(name)

    def check_returns(self, info: ScriptInfo, func: Tree, header: Tree) -> None:
        toks = [t for t in token_nodes(header) if t.type == "TYPE_HINT"]
        ret = str(toks[-1]) if toks else ""
        if not ret or ret == "void":
            return
        body = func.children[1:]
        has_return = any(
            isinstance(n, Tree) and str(n.data) == "return_stmt" for n in tree_walk(body)
        )
        name_tok = token_nodes(header)[0] if token_nodes(header) else None
        if not has_return and name_tok is not None:
            self.error(info.path, name_tok, "MISSING_RETURN",
                       f'Not all code paths return a value in function "{name_tok}".')

    def run(self) -> list[Problem]:
        for info in self.scripts.values():
            self.check_class_symbols(info)
            for child in info.tree.children:  # type: ignore[attr-defined]
                if isinstance(child, Tree) and child.data in ("func_def", "static_func_def"):
                    func = child.children[0] if child.data == "static_func_def" else child
                    self.analyze_func(info, func)
        return self.problems

    def analyze_func(self, info: ScriptInfo, func: Tree) -> None:
        header = func.children[0]
        args = header.children[1] if len(header.children) > 1 else None
        scope = Scope(None, "func")
        if isinstance(args, Tree):
            for a in args.children:
                if not isinstance(a, Tree):
                    continue
                toks = token_nodes(a)
                if not toks:
                    continue
                pname = str(toks[0])
                ptype = next((str(t) for t in toks if t.type == "TYPE_HINT"), "")
                param_tok = next((t for t in toks if t.type == "NAME"), a)
                self.is_shadowing(info, param_tok, pname, "function parameter")
                if pname in scope.names:
                    self.error(info.path, a, "DUPLICATE", f'There is already a variable named "{pname}" declared in this scope.')
                scope.names[pname] = ptype
        self.check_returns(info, func, header)
        for stmt in func.children[1:]:
            self.stmt(info, stmt, scope)

    # -- statements --------------------------------------------------------
    def stmt(self, info: ScriptInfo, node, scope: Scope) -> None:
        if isinstance(node, Token):
            return
        if not isinstance(node, Tree):
            return
        data = str(node.data)
        if data in ("func_var_stmt", "func_const_stmt"):
            self.var_stmt(info, node.children[0], scope)
        elif data == "expr_stmt":
            self.expr_tree(info, node, scope)
        elif data == "return_stmt":
            for c in node.children:
                self.value(info, c, scope)
        elif data == "if_stmt":
            for branch in node.children:
                self.branch(info, branch, scope)
        elif data == "for_stmt":
            self.for_stmt(info, node, scope)
        elif data == "while_stmt":
            self.block(info, node, scope, skip_first=True)
        elif data == "match_stmt":
            self.match_stmt(info, node, scope)
        elif data in ("pass_stmt", "break_stmt", "continue_stmt", "annotation", "docstr_stmt"):
            self.expr_tree(info, node, scope)
        elif data in ("class_def",):
            self.expr_tree(info, node, scope)
        else:
            self.expr_tree(info, node, scope)

    def block(self, info: ScriptInfo, node: Tree, scope: Scope, skip_first: bool = False,
              label: str = "block") -> Scope:
        inner = Scope(scope, label)
        children = node.children[1:] if skip_first else node.children
        for child in children:
            self.stmt(info, child, inner)
        return inner

    def branch(self, info: ScriptInfo, node, scope: Scope) -> None:
        if not isinstance(node, Tree):
            return
        data = str(node.data)
        if data == "if_branch":
            self.expr_tree(info, node.children[0], scope)
            inner = Scope(scope, "if")
            for stmt in node.children[1:]:
                self.stmt(info, stmt, inner)
        elif data == "elif_branch":
            self.expr_tree(info, node.children[0], scope)
            inner = Scope(scope, "elif")
            for stmt in node.children[1:]:
                self.stmt(info, stmt, inner)
        elif data == "else_branch":
            inner = Scope(scope, "else")
            for stmt in node.children:
                self.stmt(info, stmt, inner)

    def for_stmt(self, info: ScriptInfo, node: Tree, scope: Scope) -> None:
        children = list(node.children)
        var_tok = children[0]
        inner = Scope(scope, "for")
        if isinstance(var_tok, Token):
            name = str(var_tok)
            self.is_shadowing(info, var_tok, name, '"for" iterator variable')
            if inner.declared_in_chain(name, scope):
                self.error(info.path, var_tok, "DUPLICATE", f'There is already a variable named "{name}" declared in this scope.')
            inner.names[name] = self.iter_type(info, children[1]) or ""
            self.expr_tree(info, children[1], scope)
            rest = children[2:]
        else:
            # for_stmt_typed: TYPE, NAME, expr, body
            toks = token_nodes(var_tok)
            name = str(toks[-1])
            inner.names[name] = str(toks[0]) or ""
            self.expr_tree(info, children[1], scope)
            rest = children[2:]
        for stmt in rest:
            self.stmt(info, stmt, inner)

    def iter_type(self, info: ScriptInfo, node) -> str:
        """`for i in 6:`, `for i in range(n):`, `for x in Array[T]()`."""
        while isinstance(node, Tree) and str(node.data) == "expr" and node.children:
            node = node.children[0]
        # for x in vector: -> elementos do vetor
        if isinstance(node, Tree) and str(node.data) == "standalone_call" and node.children:
            callee = node.children[0]
            if isinstance(callee, Token):
                ret = info.ret_types.get(str(callee), "")
                m = re.fullmatch(r"Array\[(\w+)\]", ret or "")
                if m:
                    return m.group(1)
        # for x in [A.new(), B.new()]: -> tipo do primeiro elemento
        if isinstance(node, Tree) and str(node.data) in ("array", "array_expr"):
            for c in node.children:
                t = self.infer(info, c, Scope(None))
                if t:
                    return t
        return "int" if self.is_intish(info, Scope(None), node) else ""

    def match_stmt(self, info: ScriptInfo, node: Tree, scope: Scope) -> None:
        self.expr_tree(info, node.children[0], scope)
        for branch in node.children[1:]:
            if not isinstance(branch, Tree):
                continue
            inner = Scope(scope, "match")
            pattern = branch.children[0]
            self.pattern(info, pattern, inner, scope)
            for stmt in branch.children[1:]:
                self.stmt(info, stmt, inner)

    def pattern(self, info: ScriptInfo, node, inner: Scope, outer: Scope) -> None:
        if isinstance(node, Token):
            return
        if not isinstance(node, Tree):
            return
        if str(node.data) == "pattern":
            for c in node.children:
                self.pattern(info, c, inner, outer)
            return
        # `var x` bindings inside array/dict patterns
        toks = token_nodes(node)
        if str(node.data) == "array_pattern":
            for c in node.children:
                if isinstance(c, Tree) and text_of(c).strip().startswith("var"):
                    token_nodes(c)[-1]
            for c in node.children:
                if isinstance(c, Token):
                    continue
                if isinstance(c, Tree):
                    ctext = text_of(c)
                    ctoks = token_nodes(c)
                    # `var a` -> binding declaration
                    if ctoks and str(ctoks[0]) == "var":
                        bind = str(ctoks[-1])
                        if bind not in inner.names:
                            inner.names[bind] = ""
                        continue
                    self.expr_tree(info, c, outer)
            return
        self.expr_tree(info, node, outer)

    def var_stmt(self, info: ScriptInfo, node, scope: Scope) -> None:
        if not isinstance(node, Tree):
            return
        data = str(node.data)
        if data == "func_var_typed_assgnd":
            name = str(node.children[0])
            ptype = str(node.children[1])
            self.declare(info, node.children[0], name, ptype, scope)
            for c in node.children[2:]:
                self.expr_tree(info, c, scope)
            return
        if data == "func_var_typed":
            name = str(node.children[0])
            ptype = str(node.children[1])
            self.declare(info, node.children[0], name, ptype, scope)
            return
        if data == "func_var_inf":
            name = str(node.children[0])
            for c in node.children[1:]:
                self.expr_tree(info, c, scope)
            inferred = self.infer(info, node.children[1] if len(node.children) > 1 else None, scope)
            self.declare(info, node.children[0], name, inferred, scope)
            return
        if data in ("func_var_assigned", "func_var_empty"):
            name = str(node.children[0])
            for c in node.children[1:]:
                self.expr_tree(info, c, scope)
            self.declare(info, node.children[0], name, "", scope)
            return
        for c in node.children:
            self.expr_tree(info, c, scope)

    ## Reproduz GDScriptAnalyzer::is_shadowing: um nome local nao pode repetir um
    ## identificador global, um membro do proprio script, um membro da cadeia de
    ## scripts pais nem um membro da cadeia de classes nativas.
    def is_shadowing(self, info: ScriptInfo, tok, name: str, context: str) -> None:
        if name in self.engine.global_funcs or name in self.engine.classes or name in BUILTIN_TYPES:
            self.error(info.path, tok, "SHADOWED_GLOBAL_IDENTIFIER",
                       f'The {context} "{name}" has the same name as a built-in identifier.')
            return
        own = info.symbol_kind(name)
        if own is not None:
            self.error(info.path, tok, "SHADOWED_VARIABLE",
                       f'The local {context} "{name}" is shadowing an already-declared '
                       f'{own[0]} at line {own[1]} in the current class.')
            return
        parents, engine_base = self.base_chain(info)
        for parent in parents:
            inherited = parent.symbol_kind(name)
            if inherited is not None:
                self.error(info.path, tok, "SHADOWED_VARIABLE_BASE_CLASS",
                           f'The local {context} "{name}" is shadowing an already-declared '
                           f'{inherited[0]} at line {inherited[1]} in the base class '
                           f'"{parent.cls or parent.path.stem}".')
                return
        if engine_base:
            found = self.engine.symbol_kind(engine_base, name)
            if found is not None:
                self.error(info.path, tok, "SHADOWED_VARIABLE_BASE_CLASS",
                           f'The local {context} "{name}" is shadowing an already-declared '
                           f'{found[0]} in the base class "{found[1]}".')

    def declare(self, info: ScriptInfo, tok, name: str, ptype: str, scope: Scope) -> None:
        self.is_shadowing(info, tok, name, "variable")
        if name in scope.names:
            self.error(info.path, tok, "DUPLICATE", f'There is already a variable named "{name}" declared in this scope.')
        elif scope.declared_in_chain(name, scope.parent):
            self.error(info.path, tok, "DUPLICATE", f'There is already a variable named "{name}" declared in this scope.')
        scope.names[name] = ptype or ""

    def infer(self, info: ScriptInfo, node, scope: Scope) -> str:
        if not isinstance(node, Tree):
            return ""
        if str(node.data) == "expr" and node.children:
            return self.infer(info, node.children[0], scope)
        if str(node.data) == "standalone_call" and node.children:
            callee = node.children[0]
            if isinstance(callee, Token):
                name = str(callee)
                if name == "int":
                    return "int"
                if name == "float":
                    return "float"
                if name in ("str", "String"):
                    return "String"
                if name == "bool":
                    return "bool"
        kind = self.literal_type(node)
        if kind:
            return kind
        # call to a project function with a typed return
        if str(node.data) == "standalone_call" and node.children:
            callee = node.children[0]
            if isinstance(callee, Token):
                ret = info.ret_types.get(str(callee), "")
                if ret:
                    return ret
        data = str(node.data)
        # var x := SomeClass.new()  /  var x := SomeClass(...)  /  var x := proj_func()
        if data == "standalone_call" and node.children:
            callee = node.children[0]
            if isinstance(callee, Token):
                name = str(callee)
                if name in self.engine.classes:
                    return name
                if self.script_of(info, name) is not None:
                    return name
        if data == "getattr_call" and node.children:
            toks = token_nodes(node.children[0])
            if len(toks) >= 3 and str(toks[-1]) == "new":
                owner = str(toks[0])
                if owner in self.engine.classes:
                    return owner
                if self.script_of(info, owner) is not None:
                    return owner
        # x as T  /  x as T  em chamada com cast
        if data == "actual_type_cast":
            hint = next((t for t in token_nodes(node) if t.type == "TYPE_HINT"), None)
            if hint is not None:
                return str(hint)
        # arithmetic on ints stays int (same inference Godot does)
        if self.is_intish(info, scope, node):
            return "int"
        return ""

    # -- expressions -------------------------------------------------------
    def expr_tree(self, info: ScriptInfo, node, scope: Scope) -> None:
        if isinstance(node, Token):
            return
        if not isinstance(node, Tree):
            return
        data = str(node.data)
        if data == "annotation":
            return
        if data == "lambda":
            self.lambda_expr(info, node, scope)
            return
        if data == "getattr_call":
            self.getattr_call(info, node, scope)
            return
        if data == "standalone_call":
            self.standalone_call(info, node, scope)
            return
        if data == "getattr":
            self.check_property_read(info, node, scope)
            self.ref(info, node.children[0], scope)
            return
        if data == "mdr_expr":
            self.mdr_expr(info, node, scope)
            return
        if data == "actual_type_cast":
            for c in node.children:
                self.expr_tree(info, c, scope)
            return
        if data == "assnmnt_expr":
            target = node.children[0]
            if isinstance(target, Tree) and str(target.data) == "getattr":
                self.check_property_assignment(info, target, scope)
            if isinstance(target, Token) and target.type == "NAME" and str(target) in info.consts:
                self.error(info.path, target, "ASSIGN_CONST",
                           f'Cannot assign a new value to the constant "{target}".')
            if isinstance(target, Tree) and str(target.data) == "getattr":
                # alvo de atribuicao: membro ja checado acima; valida so o nome base
                toks = token_nodes(target)
                if toks:
                    self.ref(info, toks[0], scope)
            else:
                self.ref(info, target, scope)
            for c in node.children[2:]:
                self.value(info, c, scope)
            return
        # member / type tokens: skip TYPE_HINT, walk the rest
        for c in node.children:
            if isinstance(c, Token):
                if c.type in ("TYPE_HINT", "TYPE", "DOT", "AND", "OR", "NOT", "IN", "IS", "AS", "COMMENT"):
                    continue
                if c.type == "NAME":
                    self.ref(info, c, scope)
                continue
            self.expr_tree(info, c, scope)

    def attr_path(self, attr: Tree) -> tuple[str, list[str]]:
        """`a.b.c` -> ("a", ["b", "c"]), tanto em no flat quanto aninhado."""
        path: list[str] = []
        node = attr
        while isinstance(node, Tree) and str(node.data) == "getattr":
            direct = [str(t) for t in node.children if isinstance(t, Token) and t.type == "NAME"]
            path = direct + path
            node = node.children[0]
        if not isinstance(node, Token) or node.type != "NAME":
            return "", []
        if not path or path[0] != str(node):
            path = [str(node)] + path
        return path[0], path[1:]

    def receiver_type(self, info: ScriptInfo, scope: Scope, attr: Tree) -> tuple[str, str, str]:
        """(rotulo_do_receptor, tipo_do_receptor, membro_acessado) para `a.b.c`."""
        base, hops = self.attr_path(attr)
        if not base or not hops:
            return "", "", ""
        member = hops[-1]
        receiver_hops = hops[:-1]
        if base == "self":
            ctype = ""
        else:
            ctype = scope.lookup(base) or info.members.get(base, "")
        if not ctype and base in self.engine.classes:
            ctype = base
        label = base
        if ctype and self.script_of(info, ctype) is not None:
            ctype = self.script_of(info, ctype).cls or ctype
        for name in receiver_hops:
            if ctype in self.engine.classes:
                ntype = self.engine.member_type(ctype, name)
                if not ntype:
                    return label, "", member
                ctype = ntype
            elif self.script_of(info, ctype) is not None:
                target = self.script_of(info, ctype)
                ctype = getattr(target, "member_types", {}).get(name, "")
                if not ctype:
                    return label, "", member
            else:
                return label, "", member
            label = f"{label}.{name}"
        return label, ctype, member

    def call_return_type(self, info: ScriptInfo, scope: Scope, node: Tree) -> str:
        """Tipo de retorno de uma chamada (funcao do projeto ou do engine)."""
        if str(node.data) == "expr" and node.children:
            return self.call_return_type(info, scope, node.children[0])
        if str(node.data) == "standalone_call" and node.children:
            callee = node.children[0]
            if isinstance(callee, Token):
                name = str(callee)
                if name in info.ret_types:
                    return info.ret_types[name]
                sig = self.engine.global_funcs.get(name)
                if sig is not None:
                    return sig.returns
                if name in self.engine.classes:
                    return name
            return ""
        if str(node.data) == "getattr_call" and node.children:
            _label, ctype, member = self.receiver_type(info, scope, node.children[0])
            if not member or not ctype:
                return ""
            if ctype in self.engine.classes:
                if member == "new":
                    return ctype
                sig = self.engine.find_method(ctype, member)
                if sig is not None:
                    return sig.returns
                return self.engine.member_type(ctype, member)
            target = self.script_of(info, ctype)
            if target is not None:
                if member in target.funcs:
                    return target.funcs[member].returns
                return target.members.get(member, "")
            return ""
        return ""

    def property_type(self, info: ScriptInfo, scope: Scope, node: Tree) -> str:
        """Tipo estatico de uma leitura `a.b`."""
        _label, ctype, member = self.receiver_type(info, scope, node)
        if not member or not ctype:
            return ""
        if ctype in self.engine.classes:
            return self.engine.member_type(ctype, member)
        target = self.script_of(info, ctype)
        if target is not None:
            return target.members.get(member, "")
        return ""

    def owner_type(self, info: ScriptInfo, scope: Scope, attr: Tree) -> tuple[str, str]:
        label, ctype, _member = self.receiver_type(info, scope, attr)
        return label, ctype

    def getattr_call(self, info: ScriptInfo, node: Tree, scope: Scope) -> None:
        attr = node.children[0]
        args = [c for c in node.children[1:]]
        if isinstance(attr, Tree) and str(attr.data) == "getattr":
            owner_label, owner_type, method = self.receiver_type(info, scope, attr)
            toks = token_nodes(attr)
            method_tok = toks[-1]
            if not method or not isinstance(method_tok, Token):
                for c in node.children:
                    self.value(info, c, scope)
                return
            base_tok = token_nodes(attr.children[0])[0] if isinstance(attr.children[0], Tree) else attr.children[0]
            if isinstance(base_tok, Token) and base_tok.type == "NAME":
                self.ref(info, base_tok, scope)
            if not owner_type:
                for a in args:
                    self.value(info, a, scope)
                return
            if owner_type in self.engine.classes:
                sig = self.engine.find_method(owner_type, method)
                if sig is None:
                    if not self.engine.has_member(owner_type, method) and method not in (
                            "new", "call", "callv", "bind", "connect", "emit", "is_valid", "instantiate"):
                        self.error(info.path, method_tok, "UNKNOWN_METHOD",
                                   f'{owner_type} has no method "{method}".')
                else:
                    self.check_args(info, method_tok, sig, args, f"{owner_type}.{method}()")
                return
            target = self.script_of(info, owner_type)
            if target is not None:
                if method not in target.symbols:
                    engine_ext = target.extends
                    if not (engine_ext in self.engine.classes and self.engine.find_method(engine_ext, method)):
                        self.error(info.path, method_tok, "UNKNOWN_METHOD",
                                   f'{target.path.name} has no method "{method}".')
                elif method in target.funcs:
                    self.check_args(info, method_tok, target.funcs[method], args, f"{owner_label}.{method}()")
            for a in args:
                self.value(info, a, scope)
            return
        for c in node.children:
            self.expr_tree(info, c, scope)
            owner_type = ""
            local = scope.lookup(owner)
            if local:
                owner_type = local
            elif owner in info.members:
                owner_type = info.members[owner]
            elif owner == "self":
                owner_type = info.cls or info.extends
            if owner_type in self.engine.classes:
                sig = self.engine.find_method(owner_type, method)
                if sig is None:
                    if not self.engine.has_member(owner_type, method) and method not in ("new", "call", "callv", "bind", "connect", "emit", "is_valid"):
                        self.error(info.path, method_tok, "UNKNOWN_METHOD",
                                   f'{owner_type} has no method "{method}".')
                else:
                    self.check_args(info, method_tok, sig, args, f"{owner_type}.{method}()")
                return
            target = self.script_of(info, owner_type) if owner_type else None
            if target is None:
                target = self.script_of(info, owner)
            if target is not None:
                owner_script = self.script_of(info, owner)
                if owner_script is not None and method not in owner_script.symbols:
                    # maybe inherited from engine class
                    if not (owner_script.extends in self.engine.classes
                            and self.engine.find_method(owner_script.extends, method)):
                        self.error(info.path, method_tok, "UNKNOWN_METHOD",
                                   f'{owner_script.path.name} has no method "{method}".')
                elif method in owner_script.funcs:
                    self.check_args(info, method_tok, owner_script.funcs[method], args, f"{owner}.{method}()")
            for a in args:
                self.value(info, a, scope)
            return
        for c in node.children:
            self.value(info, c, scope)

    def standalone_call(self, info: ScriptInfo, node: Tree, scope: Scope) -> None:
        callee = node.children[0]
        args = list(node.children[1:])
        if isinstance(callee, Token):
            name = str(callee)
            if name in self.engine.global_funcs:
                self.check_args(info, callee, self.engine.global_funcs[name], args, f"{name}()")
            elif name in info.funcs:
                self.check_args(info, callee, info.funcs[name], args, f"{name}()")
            elif name in self.engine.classes:
                sigs = self.engine.constructors.get(name, [])
                if sigs and not any(self.fits(sig, len(args)) for sig in sigs):
                    best = max((s.maximum or 0) for s in sigs)
                    self.error(info.path, callee, "TOO_MANY_ARGS",
                               f'No constructor for "{name}" accepts {len(args)} argument(s) (max {best}).')
            elif self.resolve_implicit_method(info, callee, args, scope):
                pass
            else:
                self.ref(info, callee, scope)
        else:
            self.value(info, callee, scope)
        for a in args:
            self.value(info, a, scope)

    @staticmethod
    def literal_type(node) -> str:
        """Type of a literal (the way GDScript infers `:=`)."""
        if isinstance(node, Token):
            if node.type == "NUMBER":
                raw = str(node)
                return "float" if ("." in raw or "e" in raw.lower()) else "int"
            if node.type == "REGULAR_STRING":
                return "String"
            return ""
        if isinstance(node, Tree):
            if str(node.data) in ("true", "false"):
                return "bool"
            if str(node.data) == "expr" and node.children:
                return Analyzer.literal_type(node.children[0])
        return ""

    def is_intish(self, info: ScriptInfo, scope: Scope, node) -> bool:
        if isinstance(node, Token):
            if node.type == "NAME":
                t = scope.lookup(str(node)) or info.members.get(str(node), "")
                return t == "int"
            if node.type == "NUMBER":
                raw = str(node)
                return "." not in raw and "e" not in raw.lower()
            return False
        if not isinstance(node, Tree):
            return False
        if str(node.data) == "expr" and node.children:
            return self.is_intish(info, scope, node.children[0])
        if str(node.data) == "standalone_call" and node.children:
            callee = node.children[0]
            if isinstance(callee, Token):
                cname = str(callee)
                if cname in ("int", "maxi", "mini", "absi", "clampi", "roundi", "floori",
                             "ceili", "snappedi", "range", "range_stepped"):
                    return True
                if info.ret_types.get(cname, "") == "int":
                    return True
                sig = self.engine.global_funcs.get(cname)
                if sig is not None and sig.returns == "int":
                    return True
        if str(node.data) == "standalone_call" and node.children:
            if self.call_return_type(info, scope, node) == "int":
                return True
        if str(node.data) == "getattr_call":
            toks = token_nodes(node.children[0])
            if toks and str(toks[-1]) in ("size", "count", "length"):
                return True
            if self.call_return_type(info, scope, node) == "int":
                return True
        if str(node.data) == "getattr" and node.children:
            if self.property_type(info, scope, node) == "int":
                return True
        if str(node.data) in ("mdr_expr", "arith_expr"):
            kids = list(node.children)
            if len(kids) == 3 and isinstance(kids[1], Token) and str(kids[1]) in ("+", "-", "*"):
                return self.is_intish(info, scope, kids[0]) and self.is_intish(info, scope, kids[2])
        if str(node.data) in ("par_expr", "expr") and node.children:
            return self.is_intish(info, scope, node.children[0])
        if str(node.data) == "getattr":
            pass
        toks = [t for t in token_nodes(node)]
        if len(toks) == 1 and toks[0].type == "NAME":
            t = scope.lookup(str(toks[0]))
            if t is None:
                t = info.members.get(str(toks[0]), "")
            if t in ("int",):
                return True
        if len(toks) == 1 and toks[0].type == "NUMBER":
            return "." not in str(toks[0]) and "e" not in str(toks[0]).lower()
        return False

    def mdr_expr(self, info: ScriptInfo, node: Tree, scope: Scope) -> None:
        children = list(node.children)
        if len(children) == 3 and isinstance(children[1], Token) and str(children[1]) == "/":
            left, right = children[0], children[2]
            if self.is_intish(info, scope, left) and self.is_intish(info, scope, right):
                op = children[1]
                self.error(info.path, op, "INTEGER_DIVISION",
                           "Integer division. Decimal part will be discarded.")
        for c in children:
            self.value(info, c, scope)

    def lambda_expr(self, info: ScriptInfo, node: Tree, scope: Scope) -> None:
        header = node.children[0] if node.children else None
        body = node.children[1:]
        inner = Scope(scope, "lambda")
        if isinstance(header, Tree) and str(header.data) == "lambda_header":
            args = next((c for c in header.children if isinstance(c, Tree) and c.data == "func_args"), None)
            if isinstance(args, Tree):
                for a in args.children:
                    if not isinstance(a, Tree):
                        continue
                    toks = token_nodes(a)
                    if toks:
                        ptype = next((str(t) for t in toks if t.type == "TYPE_HINT"), "")
                        self.is_shadowing(info, toks[0], str(toks[0]), "function parameter")
                        inner.names[str(toks[0])] = ptype
        elif isinstance(header, Tree) and str(header.data) == "func_args":
            for a in header.children:
                if isinstance(a, Tree) and token_nodes(a):
                    inner.names[str(token_nodes(a)[0])] = ""
            body = node.children[1:]
        for stmt in body:
            self.stmt(info, stmt, inner)

    def check_property_read(self, info: ScriptInfo, node: Tree, scope: Scope) -> None:
        """Leitura `a.b`: o membro existe no tipo do receptor?"""
        owner_label, owner_type, member = self.receiver_type(info, scope, node)
        toks = token_nodes(node)
        if not member or not owner_type or len(toks) < 3:
            return
        prop_tok = toks[-1]
        if not isinstance(prop_tok, Token) or prop_tok.type != "NAME":
            return
        if member.startswith("_") or member in DYNAMIC_MEMBERS:
            return
        if owner_type in self.engine.classes:
            if member not in GODOT4_RENAMES:
                # leitura insegura em tipo de classe: o proprio Godot 4 so emite
                # aviso (UNSAFE_PROPERTY_ACCESS), entao nao entra como problema.
                return
            if self.engine.has_member(owner_type, member):
                return
            if any(member in self.engine.consts.get(c, set()) for c in self.engine.chain(owner_type)):
                return
            if self.engine.find_method(owner_type, member) is not None:
                return
            hint = GODOT4_RENAMES.get(member, "")
            extra = f' No Godot 4 use {hint}.' if hint else ""
            self.error(info.path, prop_tok, "UNKNOWN_MEMBER",
                       f'{owner_type} has no property "{member}".{extra}')
            return
        target_script = self.script_of(info, owner_type)
        if target_script is None:
            return
        chain = [target_script] + self.base_chain(target_script)[0]
        for script in chain:
            if member in script.symbols:
                return
        engine_base = self.base_chain(target_script)[1]
        if engine_base and (self.engine.has_member(engine_base, member)
                            or self.engine.find_method(engine_base, member)
                            or any(member in self.engine.consts.get(c, set()) for c in self.engine.chain(engine_base))):
            return
        self.error(info.path, prop_tok, "UNKNOWN_MEMBER",
                   f'{target_script.path.name} has no property "{member}".')

    def check_property_assignment(self, info: ScriptInfo, target: Tree, scope: Scope) -> None:
        toks = token_nodes(target)
        if len(toks) < 3:
            return
        owner_label, owner_type, prop = self.receiver_type(info, scope, target)
        prop_tok = toks[-1]
        if not prop or not isinstance(prop_tok, Token):
            return
        if not owner_type:
            return
        if owner_type in self.engine.classes:
            if self.engine.has_member(owner_type, prop) or self.engine.find_method(owner_type, prop):
                return
            if prop.startswith("_") or prop in DYNAMIC_MEMBERS:
                return
            hint = GODOT4_RENAMES.get(prop, "")
            extra = f' No Godot 4 use {hint}.' if hint else ""
            self.error(info.path, prop_tok, "UNKNOWN_MEMBER",
                       f'{owner_type} has no property "{prop}".{extra}')
            return
        target_script = self.script_of(info, owner_type)
        if target_script is None:
            return
        if prop in target_script.symbols:
            return
        parents, engine_base = self.base_chain(target_script)
        for parent in parents:
            if prop in parent.symbols:
                return
        if engine_base and (self.engine.has_member(engine_base, prop)
                            or self.engine.find_method(engine_base, prop)):
            return
        if prop in DYNAMIC_MEMBERS:
            return
        self.error(info.path, prop_tok, "UNKNOWN_MEMBER",
                   f'{target_script.path.name} has no property "{prop}".')

    def check_args(self, info: ScriptInfo, tok, sig: Sig, args: list, label: str) -> None:
        n = len(args)
        if sig.maximum is not None and n > sig.maximum:
            self.error(info.path, tok, "TOO_MANY_ARGS",
                       f'Too many arguments for "{label}" call. Expected at most {sig.maximum} but received {n}.')
        elif n < sig.required:
            self.error(info.path, tok, "TOO_FEW_ARGS",
                       f'Too few arguments for "{label}" call. Expected at least {sig.required} but received {n}.')

    def fits(self, sig: Sig, n: int) -> bool:
        if n < sig.required:
            return False
        if sig.maximum is not None and n > sig.maximum:
            return False
        return True

    def base_chain(self, info: ScriptInfo) -> tuple[list[ScriptInfo], str]:
        """(parent scripts, first engine class) walking the extends chain."""
        parents: list[ScriptInfo] = []
        cur = info
        engine_base = ""
        seen = set()
        while cur is not None and cur.path not in seen:
            seen.add(cur.path)
            ext = cur.extends
            if not ext:
                return parents, engine_base
            if ext in self.engine.classes:
                engine_base = ext
                return parents, engine_base
            nxt = self.by_cls.get(ext)
            if nxt is None and ext.endswith(".gd"):
                nxt = self.scripts.get((self.project / ext.removeprefix("res://")))
            if nxt is None:
                return parents, engine_base
            parents.append(nxt)
            cur = nxt
        return parents, engine_base

    def resolve_implicit_method(self, info: ScriptInfo, tok, args, scope: Scope) -> bool:
        """Bare name used as a method call (implicit self) -> valid?"""
        name = str(tok)
        parents, engine_base = self.base_chain(info)
        for parent in parents:
            if name in parent.funcs:
                self.check_args(info, tok, parent.funcs[name], args, f"{name}()")
                return True
            if name in parent.symbols:
                return True
        if engine_base:
            sig = self.engine.find_method(engine_base, name)
            if sig is not None:
                self.check_args(info, tok, sig, args, f"{name}()")
                return True
            if self.engine.has_member(engine_base, name):
                return True
        if name in VIRTUALS:
            return True
        return False

    def value(self, info: ScriptInfo, node, scope: Scope) -> None:
        """An expression slot: bare NAME tokens must be resolved too."""
        if isinstance(node, Token):
            if node.type == "NAME":
                self.ref(info, node, scope)
            return
        self.expr_tree(info, node, scope)

    def ref(self, info: ScriptInfo, node, scope: Scope) -> None:
        if not isinstance(node, Token):
            if isinstance(node, Tree):
                self.expr_tree(info, node, scope)
            return
        if node.type != "NAME":
            return
        name = str(node)
        if name in LANGUAGE or name in ("self",):
            return
        if scope.declared_in_chain(name):
            return
        if name in info.symbols:
            return
        if name in self.engine.global_consts or name in self.engine.global_funcs:
            return
        parents, engine_base = self.base_chain(info)
        if engine_base and (
            self.engine.has_member(engine_base, name)
            or any(name in self.engine.consts.get(c, set()) for c in self.engine.chain(engine_base))
            or self.engine.find_method(engine_base, name) is not None
        ):
            return
        for parent in parents:
            if name in parent.symbols:
                return
        if name in self.engine.classes or name in self.by_cls or name in self.autoloads:
            return
        if name in info.members or name in info.consts:
            return
        self.error(info.path, node, "UNDECLARED", f'Identifier "{name}" not declared in the current scope.')


# Tipos nativos do Variant: declarar um local com esses nomes gera
# SHADOWED_GLOBAL_IDENTIFIER ("built-in type") no Godot.
BUILTIN_TYPES = {
    "bool", "int", "float", "String", "StringName", "NodePath", "Vector2", "Vector2i",
    "Vector3", "Vector3i", "Vector4", "Vector4i", "Rect2", "Rect2i", "Transform2D",
    "Transform3D", "Basis", "Quaternion", "Plane", "Projection", "Color", "RID",
    "Callable", "Signal", "Dictionary", "Array", "PackedByteArray", "PackedInt32Array",
    "PackedInt64Array", "PackedFloat32Array", "PackedFloat64Array", "PackedStringArray",
    "PackedVector2Array", "PackedVector3Array", "PackedColorArray", "Variant", "Object",
    "AABB", "Nil", "Type", "Error", "Key", "JoyAxis", "JoyButton", "MouseButton",
    "Variant.Type", "Variant.Operator",
}


# Propriedades do Godot 3 que sumiram no Godot 4 (leitura gera erro em runtime).
GODOT4_RENAMES = {
    "receive_shadow": "BaseMaterial3D.disable_receive_shadows (falso por padrao)",
    "receive_shadows": "BaseMaterial3D.disable_receive_shadows (falso por padrao)",
    "flags_receive_shadow": "BaseMaterial3D.disable_receive_shadows",
    "shadow_casting_setting": "cast_shadow (GeometryInstance3D)",
    "use_in_baked_light": "GeometryInstance3D.gi_mode",
    "lightmap_mode": "GeometryInstance3D.gi_mode",
    "set_as_toplevel": "Node3D.top_level",
    "translation": "Node3D.position",
    "visible_in_tree": "Node3D.is_visible_in_tree()",
}


# Propriedades legitimas fora da lista documentada (dinamicas por natureza).
DYNAMIC_MEMBERS = {
    "callable_mp", "scene_file_path", "owner", "multiplayer", "data",
}

VIRTUALS = {
    "_init", "_ready", "_process", "_physics_process", "_input", "_unhandled_input",
    "_unhandled_key_input", "_shortcut_input", "_enter_tree", "_exit_tree", "_draw",
    "_notification", "_gui_input", "_input_event", "_to_string", "_get_property_list",
    "_set", "_get", "_get_configuration_warnings", "_validate_property", "_property_can_revert",
    "_property_get_revert", "_integrate_forces", "_body_entered", "_body_exited",
    "_area_entered", "_area_exited", "_on_", "print_debug", "print_stack", "print_rich",
    "push_error", "push_warning", "printerr", "printraw", "printt", "prints",
}

LANGUAGE = {
    "preload", "load", "assert", "true", "false", "null", "self", "super",
    "void", "int", "float", "bool", "String", "Array", "Dictionary", "Vector2",
    "Vector3", "Vector4", "Color", "Callable", "Signal", "NodePath", "StringName",
    "PackedByteArray", "PackedStringArray", "PackedInt32Array", "PackedInt64Array",
    "PackedFloat32Array", "PackedFloat64Array", "PackedVector2Array",
    "PackedVector3Array", "PackedColorArray", "RID", "Variant", "Object",
    "breakpoint", "range", "print", "str", "len", "typeof", "is_instance_valid",
    "null_instance", "func", "await", "yield", "not", "and", "or", "in", "is", "as",
    "match", "if", "elif", "else", "for", "while", "return", "pass", "continue",
    "break", "class_name", "extends", "static", "const", "var", "enum", "signal",
    "set", "get", "_ready", "_init",
    "PI", "TAU", "INF", "NAN", "E",
}


def _default_docs() -> Path | None:
    for candidate in (
        Path("/tmp/godot-4.7.2-stable/doc/classes"),
        Path("/tmp/godot-4.7-stable/doc/classes"),
        Path.home() / "godot-doc/classes",
    ):
        if candidate.is_dir() and any(candidate.glob("*.xml")):
            return candidate
    return None


from pathlib import Path as _Path  # noqa: E402  (selftest)

SELFTEST_SCRIPT = """extends SelftestBase

const LIMIT := 10

var counter := 0

func helper() -> int:
    return 1

func sample(scale: float) -> int:
    var counter := 0
    var scale := 2.0
    var inherited_value := 3
    var helper := 4
    var total := 0
    total = 10 / 3
    total = int(3.5 / 2.0)
    helper(1, 2)
    return total
"""

SELFTEST_BASE = """class_name SelftestBase

var inherited_value := 0
"""

SELFTEST_EXPECTED = {
    (11, "SHADOWED_VARIABLE"),                 # local counter sombreia o membro da linha 5
    (12, "DUPLICATE"),                         # local scale duplica o parametro
    (13, "SHADOWED_VARIABLE_BASE_CLASS"),      # inherited_value vem de SelftestBase
    (14, "SHADOWED_VARIABLE"),                 # helper sombreia a funcao
    (16, "INTEGER_DIVISION"),                  # 10 / 3 com inteiros
    (18, "TOO_MANY_ARGS"),                     # helper() aceita 0 argumentos
}


def selftest() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = _Path(tmp)
        (root / "scripts").mkdir()
        (root / "scripts" / "selftest_base.gd").write_text(SELFTEST_BASE, encoding="utf-8")
        (root / "scripts" / "selftest_sample.gd").write_text(SELFTEST_SCRIPT, encoding="utf-8")
        problems = Analyzer(root, _default_docs() or Path("/nonexistent")).run()
    found = {(p.line, p.code) for p in problems if p.path.name == "selftest_sample.gd"}
    missing = SELFTEST_EXPECTED - found
    extra = found - SELFTEST_EXPECTED
    for line, code in sorted(missing):
        print(f"FALTANDO {code} na linha {line}")
    for line, code in sorted(extra):
        print(f"INESPERADO {code} na linha {line}")
    if missing or extra:
        return 1
    print(f"selftest OK: {len(found)} achados na fixture (sombreamento, divisao inteira, argumentos, duplicata)")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Analise estatica de GDScript (Godot 4).")
    parser.add_argument("project", nargs="?", default=".", help="raiz do projeto Godot")
    parser.add_argument("--godot-doc", default="", help="pasta doc/classes do Godot (opcional)")
    parser.add_argument("--selftest", action="store_true", help="auto-verificacao das regras do analisador")
    ns = parser.parse_args()

    try:
        import gdtoolkit  # noqa: F401
    except ImportError:
        print("gdtoolkit ausente: rode `pip install gdtoolkit` antes de usar este script.")
        return 2

    if ns.selftest:
        return selftest()

    project = Path(ns.project).resolve()
    docs = Path(ns.godot_doc).resolve() if ns.godot_doc else _default_docs()
    if docs is None:
        docs = Path("/nonexistent")  # checagens do engine ficam desativadas

    analyzer = Analyzer(project, docs)
    problems = analyzer.run()
    problems.sort(key=lambda p: (str(p.path), p.line))
    for problem in problems:
        print(problem)
    engine_note = "" if docs.is_dir() else " (sem doc/classes: checagens de API do engine desativadas)"
    print(f"\n{len(problems)} problema(s) encontrado(s){engine_note}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
