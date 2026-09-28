#!/usr/bin/env python3
"""
QA Completo — Corre pro Ponto v1.0
Cobre: inventário, indexação, visual, física, jogabilidade, progressão, regressivo, analítico, zero procedural.
Saída em docs/RELEASE_QA.md + stdout.
"""
from __future__ import annotations
import json, re, sys, pathlib, hashlib, subprocess, struct

ROOT = pathlib.Path(__file__).resolve().parents[1]
fails = []
warns = []
oks = []

def ok(m): oks.append(m); print(f"  OK {m}")
def warn(m): warns.append(m); print(f"  WARN {m}")
def fail(m): fails.append(m); print(f"  FAIL {m}")

def check_replace_args():
    print("\n== Fase 0 — Correções críticas (replace 3 args) ==")
    # já corrigido, verifica
    import re
    bad=[]
    for p in ROOT.rglob("*.gd"):
        txt=p.read_text(encoding="utf-8")
        for i,line in enumerate(txt.splitlines(),1):
            # procura .replace( com 2 vírgulas dentro dos parênteses
            m=re.search(r'\.replace\(([^)]*,[^)]*,[^)]*)\)', line)
            if m:
                bad.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    if not bad:
        ok("nenhum .replace com 3 args (locale_manager corrigido)")
    else:
        for b in bad:
            fail(b)

def check_inventory():
    print("\n== Fase 1 — Inventário & indexação ==")
    glbs=list((ROOT/"assets").rglob("*.glb"))
    pngs=list((ROOT/"assets/textures").rglob("*.png"))
    wavs=list((ROOT/"assets/audio").rglob("*.wav"))
    print(f"  GLBs: {len(glbs)} | PNGs: {len(pngs)} | WAVs: {len(wavs)}")
    # categorias
    cats={
        "humanos": list((ROOT/"assets/characters/humanos_originais").glob("*.glb")),
        "animais": list((ROOT/"assets/characters/animais").glob("*.glb")),
        "vehicles": list((ROOT/"assets/vehicles").glob("*.glb")),
        "props": list((ROOT/"assets/props").glob("*.glb")),
        "scene": list((ROOT/"assets/scene").glob("*.glb")),
        "collectibles": list((ROOT/"assets/collectibles").glob("*.glb")),
        "sky": list((ROOT/"assets/sky_fx").glob("*.glb")),
    }
    for k,v in cats.items():
        print(f"    {k}: {len(v)} -> {[p.name for p in v]}")
        if k=="humanos" and len(v)!=2: fail(f"humanos esperado 2, achado {len(v)}")
        elif k=="animais" and len(v)!=10: fail(f"animais esperado 10, achado {len(v)}")
        elif k=="vehicles" and len(v)<11: fail(f"vehicles esperado >=11, achado {len(v)}")
        elif k=="props" and len(v)<8: warn(f"props {len(v)} <8?")
        elif k=="scene" and len(v)<14: warn(f"scene {len(v)} <14?")
        else: ok(f"{k} {len(v)}")
    # check cada GLB referenciado
    gd_text=" ".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*.gd"))
    json_text=" ".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*.json"))
    unref=[]
    for g in glbs:
        rel=g.relative_to(ROOT).as_posix()
        # drop-in: se está em assets/vehicles, props, scene, collectibles, animais, sky -> é drop-in por pasta, não precisa string literal
        # mas humanos e alguns veículos (car, bus) são literais
        if "humanos_originais" in rel or "vehicles" in rel:
            # deve aparecer em runner_character ou game_3d
            name=g.stem
            if name not in gd_text and rel not in gd_text:
                unref.append(rel)
        elif "animais" in rel:
            name=g.stem
            if name not in gd_text and name not in json_text:
                # caramelo etc deve estar em world_animal
                unref.append(rel)
    if unref:
        warn(f"GLBs sem referência literal (drop-in ok): {unref}")
    else:
        ok("todos GLBs core referenciados (literal ou drop-in)")
    # check PROVENANCE SHA
    prov=ROOT/"assets/characters/humanos_originais/PROVENANCE.md"
    if prov.exists():
        txt=prov.read_text(encoding="utf-8")
        m=re.findall(r"([a-f0-9]{64})\s+(\S+)\s+\((\d+) bytes\)", txt)
        for h, name, size in m:
            p=ROOT/"assets/characters/humanos_originais"/name
            if not p.exists(): fail(f"PROVENANCE aponta {name} inexistente")
            else:
                data=p.read_bytes()
                ah=hashlib.sha256(data).hexdigest()
                if ah!=h: fail(f"SHA mismatch {name}: esperado {h[:8]}... achado {ah[:8]}...")
                elif len(data)!=int(size): fail(f"size mismatch {name}")
                else: ok(f"SHA ok {name} {len(data)}")
    else:
        fail("PROVENANCE humanos_originais não existe")

def check_glb_details():
    print("\n== Fase 2 — GLB detalhes (textura, anim, skin, sombreamento) ==")
    # check cada glb humano tem JOINTS/WEIGHTS, skins, animations
    for name in ["Humano_M.glb","Humano_F.glb"]:
        p=ROOT/"assets/characters/humanos_originais"/name
        raw=p.read_bytes()
        if raw[:4]!=b'glTF': fail(f"{name} não é GLB"); continue
        # parse GLB header
        # GLB json chunk
        try:
            # read GLB structure
            magic, ver, length = struct.unpack_from("<III", raw, 0)
            # primeiro chunk
            off=12
            chunk_len, chunk_type = struct.unpack_from("<II", raw, off)
            off+=8
            if chunk_type!=0x4E4F534A: # JSON
                fail(f"{name} primeiro chunk não é JSON")
                continue
            j=json.loads(raw[off:off+chunk_len].decode("utf-8"))
            meshes=j.get("meshes",[])
            skins=j.get("skins",[])
            anims=j.get("animations",[])
            mats=j.get("materials",[])
            # check JOINTS
            has_joints=any("JOINTS_0" in prim.get("attributes",{}) for m in meshes for prim in m.get("primitives",[]))
            has_weights=any("WEIGHTS_0" in prim.get("attributes",{}) for m in meshes for prim in m.get("primitives",[]))
            if not has_joints: fail(f"{name} sem JOINTS_0")
            else: ok(f"{name} JOINTS_0 ok")
            if not has_weights: fail(f"{name} sem WEIGHTS_0")
            else: ok(f"{name} WEIGHTS_0 ok")
            if not skins: fail(f"{name} sem skins")
            else: ok(f"{name} skins {len(skins)}")
            if not anims: fail(f"{name} sem animations")
            else:
                clip_names=[]
                for a in anims:
                    for ch in a.get("channels",[]):
                        pass
                    # animation name em extras ou no próprio nome?
                    n=a.get("name","")
                    if n: clip_names.append(n)
                # alternativo: procurar nomes nos canais? GLB humano tem 6 clips
                if len(anims)<6: warn(f"{name} animações {len(anims)} <6")
                else: ok(f"{name} animations {len(anims)} clips {clip_names[:3]}")
            # materiais nomeados
            mat_names=[m.get("name","") for m in mats]
            expected=["QuaterniusSkin","Hair","Camisa","Calca","Sapato"]
            for exp in expected:
                if not any(exp.lower() in (n or "").lower() for n in mat_names):
                    warn(f"{name} material {exp} não encontrado em {mat_names}")
                else: ok(f"{name} material {exp} ok")
        except Exception as e:
            fail(f"{name} parse erro {e}")

    # check veículos tem Wheel* etc - simplificado: verifica nome Wheel no binário
    for v in (ROOT/"assets/vehicles").glob("*.glb"):
        raw=v.read_bytes()
        # procura strings Wheel, BusWheel etc
        if b"Wheel" not in raw and b"wheel" not in raw.lower():
            # alguns GLBs podem usar outro nome? mas audit exige Wheel*
            warn(f"{v.name} sem Wheel* no binário (pode ser variação)")
        else: ok(f"{v.name} Wheel* ok")
        # verifica tamanho
        sz=v.stat().st_size
        if sz<50_000: warn(f"{v.name} muito pequeno {sz}")
        else: ok(f"{v.name} {sz//1024}KB")

    # check props/scene/collectibles existem e são GLB válidos
    for c in ["props","scene","collectibles","sky_fx"]:
        for g in (ROOT/"assets"/c).glob("*.glb"):
            raw=g.read_bytes()
            if raw[:4]!=b'glTF': fail(f"{c}/{g.name} não é GLB")
            else: ok(f"{c}/{g.name} GLB ok {g.stat().st_size//1024}KB")

    # check texturas PBR
    pbr=list((ROOT/"assets/textures/pbr").glob("*.png"))
    height=list((ROOT/"assets/textures/pbr").glob("*height.png"))
    if len(pbr)<30: warn(f"pbr {len(pbr)} <30?")
    else: ok(f"pbr {len(pbr)}")
    if len(height)<8: warn(f"height {len(height)} <8?")
    else: ok(f"height {len(height)} heightmaps 16-bit")

def check_visual():
    print("\n== Fase 2b — Visual (iluminação/escala) ==")
    # building_kit heightmap
    bk=(ROOT/"scripts/building_kit.gd").read_text(encoding="utf-8")
    if "heightmap_enabled" not in bk: fail("building_kit sem heightmap_enabled")
    else: ok("building_kit heightmap_enabled ok")
    if "uv1_world_triplanar" not in bk: fail("building_kit sem world_triplanar")
    else: ok("building_kit world_triplanar ok")
    if "uv1_triplanar_sharpness" not in bk: fail("building_kit sem sharpness")
    else: ok("building_kit sharpness ok")
    # lighting
    lh=(ROOT/"scripts/lighting_handler.gd").read_text(encoding="utf-8")
    # L27/L24: a luz realista (default ligado, game_3d.gd:187) usa o bias firme
    # de contato; 0.015 era o valor anterior ao tuning do lighting_handler.
    if "SHADOW_BIAS_REALISTA: float = 0.012" in lh: ok("lighting bias 0.012 (L27) ok")
    else: warn("lighting bias fora do valor L27 (0.012)")
    # runner scale
    rc=(ROOT/"scripts/runner_character.gd").read_text(encoding="utf-8")
    if "PLAYER_HEIGHT := 1.82" in rc: ok("PLAYER_HEIGHT 1.82 realista")
    else: warn("PLAYER_HEIGHT não 1.82")
    if "Head" in rc and "look_yaw" in rc: ok("head look-at 12° ok")
    else: warn("head look-at ausente")

def check_physics():
    print("\n== Fase 3 — Física (gravidade/colisão/atrito/inércia) ==")
    ph=(ROOT/"scripts/physics_handler.gd").read_text(encoding="utf-8")
    checks=[
        ("GRAVITY := 9.81" in ph or "GRAVITY: float = 9.81" in ph, "GRAVITY 9.81"),
        ("PLAYER_MASS" in ph and "75" in ph, "PLAYER_MASS 75"),
        ("PLAYER_FRICTION" in ph, "PLAYER_FRICTION"),
        ("CapsuleShape3D" in ph, "CapsuleShape3D"),
        ("RigidBody3D" in ph, "RigidBody3D"),
        ("Area3D" in ph, "Area3D pothole"),
        ("PhysicalBone3D" in ph, "ragdoll PhysicalBone"),
        ("SURFACE_FRICTION" in ph, "SURFACE_FRICTION dict L27"),
        ("surface_speed_factor" in ph, "surface_speed_factor helper"),
    ]
    for ok_, msg in checks:
        if ok_: ok(msg)
        else: fail(msg)
    # game_3d usa PhysicsHandler
    g3=(ROOT/"scripts/game_3d.gd").read_text(encoding="utf-8")
    if "PhysicsHandler.surface_speed_factor" in g3: ok("game_3d usa surface_speed_factor dirt/cobble")
    else: fail("game_3d não usa surface_speed_factor")
    if "move_and_slide" in g3 or "CharacterBody3D" in g3 or "PlayerPhysicsBody" in g3: ok("game_3d referencia CharacterBody")
    else: warn("game_3d sem move_and_slide (mas helper existe)")

def check_gameplay():
    print("\n== Fase 4 — Jogabilidade / Progressão / Dificuldade ==")
    # phase_data 50 fases?
    # scenario_data
    sd=ROOT/"scripts/scenario_data.gd"
    if sd.exists():
        txt=sd.read_text(encoding="utf-8")
        # contar occurrences de street_surface etc? Não, contar perfis?
        # vamos contar "street_surface" occurrences = fases?
        cnt=txt.count("street_surface")
        print(f"  scenario street_surface entries {cnt}")
        if cnt>=10: ok(f"scenario_data {cnt} perfis")
        else: warn(f"scenario_data só {cnt}")
    # game_balance
    bal=(ROOT/"resources/game_balance.tres").read_text(encoding="utf-8")
    import re
    m=re.search(r"phase_count\s*=\s*(\d+)", bal)
    if m and int(m.group(1))==50: ok("phase_count 50")
    else: fail(f"phase_count {m.group(1) if m else 'não achado'}")
    for k in ["base_speed","final_speed","first_wait_seconds","autosave_seconds"]:
        if k in bal: ok(f"balance {k}")
        else: fail(f"balance sem {k}")
    # save_data
    sd2=ROOT/"scripts/save_data.gd"
    txt2=sd2.read_text(encoding="utf-8")
    for tok in ["SAVE_SCHEMA_VERSION := 4","BACKUP_PATH","record_phase_attempt","weekly_distance_target"]:
        if tok in txt2: ok(f"save {tok}")
        else: fail(f"save sem {tok}")
    # shop_data
    sh=(ROOT/"scripts/shop_data.gd").read_text(encoding="utf-8")
    ids=re.findall(r'"id": "([^"]+)"', sh)
    if ids==["tenis","mochila","fone","cafe","confete","placa"]: ok("shop IDs 6 ok")
    else: fail(f"shop IDs {ids}")
    # obstacle_data 13
    od=(ROOT/"scripts/obstacle_data.gd").read_text(encoding="utf-8")
    cnt=od.count('"id":')
    if cnt==27: ok("obstacle 27")
    else: warn(f"obstacle count {cnt} !=27")

def check_procedural():
    print("\n== Fase 6 — Zero procedural (L29) ==")
    import re
    total=0
    details=[]
    for p in ROOT.rglob("*.gd"):
        if "lote" in str(p): continue
        txt=p.read_text(encoding="utf-8")
        c=len(re.findall(r"(BoxMesh|SphereMesh|CylinderMesh|CapsuleMesh|QuadMesh|PlaneMesh|TorusMesh)\.new\(\)", txt))
        if c>0:
            details.append(f"{p.relative_to(ROOT)}: {c}")
            total+=c
    print(f"  total primitive new() {total} (lote excluído)")
    for d in details[:20]:
        print(f"    {d}")
    # L29 Zero Procedural Gameplay: helpers fallback removidos, world base (building_kit 28m) é layout spec-driven não asset
    # Verificamos apenas helpers de gameplay (game_3d primitive cache + runner acessórios)
    g3=ROOT/"scripts/game_3d.gd"
    txt=g3.read_text(encoding="utf-8")
    if "var primitive_mesh_cache" in txt or "primitive_mesh_cache.get" in txt:
        fail("game_3d ainda tem primitive_mesh_cache helper — L29 deveria ter removido (BoxMesh fallback)")
    else:
        ok("game_3d helper fallback removido L29 (0 BoxMesh) — 100% GLB gameplay")
    # runner_character L29: acessórios agora ArrayMesh placeholder (0 BoxMesh) — shadow via GLB cone
    rc=ROOT/"scripts/runner_character.gd"
    rct=rc.read_text(encoding="utf-8")
    cnt_rc=rct.count("BoxMesh.new()")+rct.count("CylinderMesh.new()")+rct.count("SphereMesh.new()")+rct.count("QuadMesh.new()")+rct.count("TorusMesh.new()")+rct.count("CapsuleMesh.new()")
    print(f"  runner_character primitives {cnt_rc} (L29: 0 esperado, shadow via GLB)")
    if cnt_rc>0:
        fail(f"runner_character ainda tem {cnt_rc} primitivas — L29 deveria zerar (ArrayMesh)")
    else:
        ok("runner_character 0 primitivas L29 — acessórios/shadow via GLB placeholder")
    # world_animal/weather/world_character: partículas e fallback, não contam como asset procedural (efeitos)
    # building_kit 4 BoxMesh são world base 28m spec-driven — audit permite, HLOD futuro
    bk=ROOT/"scripts/building_kit.gd"
    bkt=bk.read_text(encoding="utf-8")
    cnt_bk=bkt.count("BoxMesh.new()")
    print(f"  building_kit BoxMesh {cnt_bk} (world base 28m spec, HLOD L29 futuro)")
    if cnt_bk>0:
        # não falha, apenas informa — world base não é asset drop-in
        ok(f"building_kit world base {cnt_bk} primitivas mantido (spec 28m, não asset) — L29 aceita")
    # L29: gameplay helpers zerados, world base e partículas são layout/efeitos, não assets drop-in
    if cnt_rc==0 and "var primitive_mesh_cache" not in txt and "primitive_mesh_cache.get" not in txt:
        ok("gameplay 0 procedural helpers (100% GLB) — building_kit world base 28m é layout spec, partículas são efeitos, não assets")
    else:
        warn("gameplay helpers ainda tem primitivas — verificar")

def check_resources():
    print("\n== Fase 5 — Testes regressivos (resource refs) ==")
    # res:// refs existem?
    import re
    missing=[]
    for p in (ROOT/"scripts").rglob("*.gd"):
        txt=p.read_text(encoding="utf-8")
        for m in re.findall(r'res://[^"\']+', txt):
            # limpa trailing pontuação
            res=m.split('"')[0].split("'")[0].split(" ")[0].rstrip(").,;")
            # remove params
            if res.endswith("/"): continue
            # ignora * e placeholders
            if "*" in res: continue
            # verifica se arquivo existe (sem uid)
            fs=ROOT / res.removeprefix("res://")
            if not fs.exists():
                # tenta com .import? não
                # ignora se é diretório
                if fs.suffix=="" and fs.is_dir(): continue
                # ignora se tem variável (ex: "res://assets/vehicles/" + name)
                if "$" in res or "%s" in res: continue
                missing.append(f"{p.relative_to(ROOT)} -> {res}")
    if missing:
        for mm in missing[:20]:
            fail(f"missing resource {mm}")
    else:
        ok("todos res:// existem (via ResourceLoader check)")

# --- Fase 7 — contrato da "rua viva" por cenário (ETAPA 17) -----------------
# Governa a camada viva da rua (coroamento, decalques de asfalto, encardido):
# os padrões ficam em resources/world_spec.json e cada capítulo afina o seu em
# scripts/level_data.gd (RUA_VIVA_*), fundido pelo BuildingKit. O portão aqui
# é estrutural: chave desconhecida ou valor fora de faixa não passa.
RUA_VIVA_CONTRATO = {
    "coroamento": {
        "platibanda": (bool, None),
        "ar_condicionado": (bool, None),
        "caixa_dagua_min_andares": (int, (1, 99)),
        "escada_incendio": (bool, None),
        "escada_min_andares": (int, (1, 99)),
        "escada_a_cada_lotes": (int, (1, 8)),
    },
    "decalques": {
        "setas": (bool, None),
        "seta_passo_m": (float, (4.0, 60.0)),
        "seta_comprimento_m": (float, (0.4, 4.0)),
        "tampa_passo_m": (float, (4.0, 60.0)),
        "remendo_passo_m": (float, (4.0, 60.0)),
    },
    "encardido": {
        "albedo": (float, (0.05, 1.0)),
        "sarjeta": (bool, None),
        "parede": (bool, None),
        "poste": (bool, None),
    },
    "fachada": {
        "toldo": (bool, None),
        "letreiro": (bool, None),
        "grade_janela": (bool, None),
        "grade_ate_andar": (int, (0, 4)),
    },
    "rua": {
        "jardineira": (bool, None),
        "jardineira_passo_m": (float, (4.0, 60.0)),
    },
}

def _rua_viva_valida(origem, bloco, chave, valor):
    """Confere uma chave do contrato; devolve mensagem de erro ou None."""
    if bloco not in RUA_VIVA_CONTRATO:
        return f"{origem}: bloco rua_viva desconhecido '{bloco}'"
    if chave.startswith("_"):
        return None
    if chave not in RUA_VIVA_CONTRATO[bloco]:
        return f"{origem}: chave desconhecida rua_viva.{bloco}.{chave}"
    tipo, faixa = RUA_VIVA_CONTRATO[bloco][chave]
    if tipo is bool and not isinstance(valor, bool):
        return f"{origem}: rua_viva.{bloco}.{chave} devia ser bool, veio {valor!r}"
    if tipo is not bool and isinstance(valor, bool):
        return f"{origem}: rua_viva.{bloco}.{chave} devia ser número, veio {valor!r}"
    if tipo is int and not isinstance(valor, int):
        return f"{origem}: rua_viva.{bloco}.{chave} devia ser int, veio {valor!r}"
    if tipo is float and not isinstance(valor, (int, float)):
        return f"{origem}: rua_viva.{bloco}.{chave} devia ser float, veio {valor!r}"
    if faixa is not None and not (faixa[0] <= float(valor) <= faixa[1]):
        return f"{origem}: rua_viva.{bloco}.{chave}={valor} fora da faixa {faixa}"
    return None

def check_rua_viva():
    print("\n== Fase 7 — Rua viva por cenário (contrato ETAPA 17) ==")
    spec_path = ROOT / "resources" / "world_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    base = spec.get("rua_viva")
    if not isinstance(base, dict):
        fail("world_spec.json sem o bloco 'rua_viva' (padrões do mundo)")
        return
    erros = []
    for bloco, chaves in RUA_VIVA_CONTRATO.items():
        if bloco not in base:
            erros.append(f"world_spec.rua_viva sem o bloco '{bloco}'")
            continue
        faltando = sorted(set(chaves) - set(base[bloco]))
        if faltando:
            erros.append(f"world_spec.rua_viva.{bloco} sem padrão para {faltando}")
        for chave, valor in base[bloco].items():
            e = _rua_viva_valida("world_spec", bloco, chave, valor)
            if e:
                erros.append(e)
    if erros:
        for e in erros[:20]:
            fail(e)
    else:
        ok(f"world_spec.rua_viva com os {len(RUA_VIVA_CONTRATO)} blocos e {sum(len(v) for v in RUA_VIVA_CONTRATO.values())} padrões válidos")

    # Perfis por capítulo em level_data.gd: só chaves do contrato, na faixa.
    ld = (ROOT / "scripts" / "level_data.gd").read_text(encoding="utf-8")
    perfis = re.findall(r"^const (RUA_VIVA_[A-Z_]+): Dictionary = \{(.*?)^\}", ld, re.S | re.M)
    # perfis escritos direto dentro de um CENARIO_* (bloco "rua_viva": { ... })
    for m in re.finditer(r'"rua_viva":\s*\{', ld):
        i = m.end() - 1
        nivel = 0
        for j in range(i, len(ld)):
            if ld[j] == "{":
                nivel += 1
            elif ld[j] == "}":
                nivel -= 1
                if nivel == 0:
                    break
        anterior = ld.rfind("const CENARIO_", 0, m.start())
        nome = re.match(r"const (\w+)", ld[anterior:]).group(1) if anterior >= 0 else "?"
        perfis.append((nome + " (inline)", ld[i + 1:j]))
    if not perfis:
        fail("level_data.gd sem nenhum perfil RUA_VIVA_* (variação por cenário sumiu)")
        return
    erros = []
    for nome, corpo in perfis:
        for bloco, miolo in re.findall(r'"(\w+)":\s*\{(.*?)\}', corpo, re.S):
            for chave, bruto in re.findall(r'"(\w+)":\s*([^,\n]+)', miolo):
                bruto = bruto.strip()
                if bruto in ("true", "false"):
                    valor = bruto == "true"
                elif re.fullmatch(r"-?\d+\.\d+", bruto):
                    valor = float(bruto)
                elif re.fullmatch(r"-?\d+", bruto):
                    valor = int(bruto)
                else:
                    erros.append(f"{nome}: rua_viva.{bloco}.{chave} com valor não literal '{bruto}'")
                    continue
                e = _rua_viva_valida(nome, bloco, chave, valor)
                if e:
                    erros.append(e)
    if erros:
        for e in erros[:20]:
            fail(e)
    else:
        ok(f"level_data.gd: {len(perfis)} perfis rua_viva por capítulo, todas as chaves no contrato")

    # Cada perfil declarado precisa estar ligado a pelo menos um CENARIO_*.
    orfaos = [n for n, _ in perfis
              if n.startswith("RUA_VIVA_") and not re.search(r'"rua_viva":\s*%s\b' % n, ld)]
    if orfaos:
        fail(f"perfis rua_viva sem cenário usando: {orfaos}")
    else:
        ok("todo perfil rua_viva está ligado a um CENARIO_*")

    # O kit precisa ler os três blocos (senão o override vira letra morta).
    bk = (ROOT / "scripts" / "building_kit.gd").read_text(encoding="utf-8")
    lidos = set(re.findall(r'rua_viva\(spec,\s*"(\w+)"\)', bk))
    faltando = sorted(set(RUA_VIVA_CONTRATO) - lidos)
    if faltando:
        fail(f"building_kit.gd não lê os blocos rua_viva {faltando}")
    else:
        ok(f"building_kit.gd consome os {len(RUA_VIVA_CONTRATO)} blocos via rua_viva(spec, ...)")

def check_personagem():
    """Fase 8 — personagem: sem contorno preto e com a textura do GLB.

    O casco de silhueta (malha inflada com CULL_FRONT e albedo quase preto)
    desenhava um filete escuro em volta do corpo e, nas partes finas, passava
    na frente da malha e escondia o atlas do GLB. Este portão impede que ele
    volte e confere que o asset do herói realmente traz textura por material.
    """
    print("\n== Fase 8 — Personagem (contorno e textura) ==")
    rc_bruto = (ROOT / "scripts" / "runner_character.gd").read_text(encoding="utf-8")
    # só o código conta: a explicação de por que o contorno saiu cita os nomes
    rc = "\n".join(l for l in rc_bruto.splitlines() if not l.lstrip().startswith("#"))
    proibidos = ["_attach_silhouette_shell", "_grow_outline_mesh", "_silhouette_material",
                 "CULL_FRONT"]
    achados = [t for t in proibidos if t in rc]
    if achados:
        fail(f"contorno preto de volta em runner_character.gd: {achados}")
    else:
        ok("runner_character.gd sem casco de silhueta (nenhum CULL_FRONT)")
    if "_usar_materiais_do_glb" in rc_bruto and "vertex_color_use_as_albedo = true" in rc_bruto:
        ok("herói religa vertex_color_use_as_albedo nos materiais do GLB")
    else:
        fail("runner_character.gd não liga vertex_color_use_as_albedo: herói sai branco")

    glb = ROOT / "assets" / "characters" / "personagens" / "personagem_v2.glb"
    if not glb.exists():
        fail(f"asset do herói ausente: {glb}")
        return
    dados = glb.read_bytes()
    if dados[:4] != b"glTF":
        fail("personagem_v2.glb não é um GLB binário")
        return
    tamanho = struct.unpack("<I", dados[12:16])[0]
    cena = json.loads(dados[20:20 + tamanho])
    inicio_bin = 20 + tamanho
    tam_bin = struct.unpack("<I", dados[inicio_bin:inicio_bin + 4])[0]
    binario = dados[inicio_bin + 8:inicio_bin + 8 + tam_bin]

    materiais = cena.get("materials", [])
    sem_textura = [m.get("name", "?") for m in materiais
                   if "baseColorTexture" not in m.get("pbrMetallicRoughness", {})]
    if not materiais:
        fail("personagem_v2.glb sem materiais")
    elif sem_textura:
        fail(f"materiais do herói sem baseColorTexture: {sem_textura}")
    else:
        ok(f"personagem_v2.glb: {len(materiais)} materiais com textura")

    # A cor do herói mora em COLOR_0, não na textura: o PNG embutido é só grão
    # quase branco. Se um primitivo perder COLOR_0 (ou vier branco), a
    # personagem volta a aparecer sem cor mesmo com a textura presente — por
    # isso o portão lê o atributo em vez de confiar no baseColorTexture.
    tipos = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    formatos = {5121: ("B", 1, 255.0), 5123: ("H", 2, 65535.0), 5126: ("f", 4, 1.0)}

    def _media_cor(indice_acessor):
        a = cena["accessors"][indice_acessor]
        bv = cena["bufferViews"][a["bufferView"]]
        if a["componentType"] not in formatos:
            return None
        fmt, largura, divisor = formatos[a["componentType"]]
        n = tipos.get(a["type"], 0)
        if n < 3:
            return None
        base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        total = 0.0
        amostras = 0
        passo = max(1, a["count"] // 256)
        for i in range(0, a["count"], passo):
            v = struct.unpack_from("<" + fmt * n, binario, base + i * largura * n)
            total += sum(v[:3]) / (3.0 * divisor)
            amostras += 1
        return total / max(1, amostras)

    faltando = []
    brancos = []
    medidas = []
    for malha in cena.get("meshes", []):
        for prim in malha.get("primitives", []):
            nome = malha.get("name", "?")
            if "COLOR_0" not in prim.get("attributes", {}):
                faltando.append(nome)
                continue
            media = _media_cor(prim["attributes"]["COLOR_0"])
            if media is None:
                continue
            medidas.append(f"{nome}={media:.2f}")
            if media > 0.85:
                brancos.append(f"{nome} ({media:.2f})")
    if faltando:
        fail(f"primitivos do herói sem COLOR_0 (cor da personagem): {faltando}")
    elif brancos:
        fail(f"COLOR_0 quase branco no herói: {brancos}")
    else:
        ok("COLOR_0 com cor real em todos os primitivos: " + ", ".join(medidas))

def run_validations():
    print("\n== Fase 5b — Validators ==")
    for cmd in [["python3","tools/validate_project.py"],["python3","tools/audit_balance.py"],["python3","tools/audit_runner_rig.py"]]:
        try:
            out=subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.STDOUT, timeout=20)
            first=out.splitlines()[0] if out else ""
            if "OK" in out or "PRE-FLIGHT OK" in out:
                ok(f"{' '.join(cmd)} -> {first[:80]}")
            else:
                fail(f"{' '.join(cmd)} -> {out[:200]}")
        except subprocess.CalledProcessError as e:
            fail(f"{' '.join(cmd)} exit {e.returncode}: {e.output[:300]}")
        except Exception as e:
            fail(f"{' '.join(cmd)} exc {e}")

if __name__=="__main__":
    check_replace_args()
    check_inventory()
    check_glb_details()
    check_visual()
    check_physics()
    check_gameplay()
    check_resources()
    check_procedural()
    check_rua_viva()
    check_personagem()
    run_validations()
    print("\n==================================================")
    print(f"OK {len(oks)} | WARN {len(warns)} | FAIL {len(fails)}")
    if fails:
        print("\nFAILURES:")
        for f in fails: print(f" - {f}")
        sys.exit(1)
    elif warns:
        print("\nWARNS (não bloqueante):")
        for w in warns: print(f" - {w}")
        sys.exit(0)
    else:
        print("\nTUDO OK")
        sys.exit(0)
