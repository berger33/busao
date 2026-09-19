# Assets gerados por Blender headless (bpy)

Os GLBs desta pipeline sao modelados por codigo (sem download externo).
Requisitos: `pip install bpy==4.5.14` (Python 3.11) — o mesmo Blender LTS
used no sandbox; roda 100% headless.

## Regenerar o pombo

```bash
python3 tools/blender/build_pombo.py
```

Escreve `assets/characters/animais/pombo.glb` (rig + clipes Walk/Idle) e
previews PNG em `tools/blender/out/` (variaveis `POMBO_OUT_GLB` e
`POMBO_OUT_DIR` sobrescrevem os destinos).

## Regenerar as aves do lote 2 (passaro, gaivota, urubu)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_aves.py
```

Kit compartilhado em `kit_base.py` (corpo loftero, asas, rig de 12 ossos,
clips Walk + Fly). Escreve `assets/characters/animais/{passaro,gaivota,
urubu}.glb` com resting e Walk assentados no chao (o `Fly` e a pose de voo)
e previews PNG em `tools/blender/out/` (duas angulacoes por ave). Duracao
total: ~45 s em Cycles CPU 640x480.

O drop-in no jogo: `scripts/world_animal.gd` escala cada GLB pelos tamanhos
de `BIRD_PROFILES` (`glb_comprimento`/`glb_altura`), assenta no chao e, no
voo, toca o clip `fly` em loop (`behavior_mode == "flight"`); no chao, o
clip `walk`/`trot`.

## Regenerar os quadrúpedes do lote 3 (capivara, cavalo, boi)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_quadrupedes.py
```

Mesmo kit `kit_base.py`, mas com pernas articuladas: corpo/pescoco em loft,
cabeça/focinho/olhos/orelhas em elipsoides, 4 pernas em 3 segmentos
(Coxa → Canela → Pe) com **sobreposição de 3 cm nas juntas** — com subsurf,
peças que apenas se tocam ficam separadas. Cauda + tufo por espécie
(crina e topete no cavalo; chifres, manchas e úbere no boi).

Rig de **16 ossos**: `Corpo → Pescoco → Cabeca` + `Cauda` + 4 pernas
(`Coxa/Canela/Pe` por pé). Clips por espécie:

- capivara: `Idle` (respiração + cauda, 12f), `Lie` (deitada, 16f),
  `Walk` (diagonais FE+TR / FD+TD, 16f)
- cavalo: `Idle`, `Graze` (pastando: cabeça no chão + mastigar), `Walk`
- boi: `Idle`, `Graze`, `Walk` (ciclo mais lento, bob maior)

**Regra do exportador glTF (importante para os lotes 4+):** com
`export_animation_mode='ACTIONS'`, só sai clip que já foi atribuído ao
armature pelo menos uma vez (`animation_data.action = clip`). O script
atribui cada clip antes de exportar e devolve o default no final — sem isso
o glTF exporter **descarta o clip em silêncio**.

Outra pegadinha do bpy: `bpy.ops.object.transform_apply` tem defaults
`location=True, rotation=True, scale=True` — passar só
`transform_apply(scale=True)` aplica o location junto (a origem da peça
vai para 0,0,0 e qualquer rotação feita depois orbita a peça em torno da
origem do mundo). Sempre passe os três argumentos explicitamente.

Duração total: ~45 s (Cycles CPU 640x480, 6 previews).

## Regenerar o lote 4 (macaco e caranguejo)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_lote4.py
```

Macaco meio-ereto com cauda em 2 segmentos (10 ossos no rig:
Corpo/Pescoco/Cabeca, Cauda/CaudaPonta, 2 bracos, 2 pernas) e
caranguejo com casco em cupula, pinças e 3 patas por lado (9 ossos).
Clipes Walk + Idle + Lie (o Lie e o crouch dos dois). O macaco reusa a
nova helper `coluna_entre` do proprio script (pilar entre dois pontos
arbitrarios via quaternion — evita o cacete de alinhar Euler na mao).
O `world_animal.gd` nao precisou de mudanca: o drop-in generico do
lote 3 cobre qualquer especie com GLB + `GLB_SIZES`.

## Regenerar o lote 5 (veículos)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_lote5.py
```

Sete GLBs em `assets/vehicles/`: `car` (hatch), `carro` (sedan),
`motorcycle`, `truck` (cabine + carroceria de madeira), `bus_traffic`,
`onibus` (letreiro LED "PONTO FINAL" com textura emissiva gerada por PIL) e
`bicycle`. Frente = +Y no Blender (vira -Z no Godot, contrato do README da
pasta). `loft_box` faz cascos super-elipse com `subd=1` (subd 2 derrete as
caixas). Rodas em nós separados com eixo no X e nomes `Wheel*/BusWheel*/
MotoWheel*` — `_animate_traffic` em `game_3d.gd` gira `rotation.x` delas com
busca recursiva. `caixa()` gera UVs 0..1 por face (obrigatório para texturas,
ex.: o letreiro). Duração: ~90 s (7 exports + 7 previews Cycles).

Em sandboxes sem bibliotecas X11/GL do sistema, o import do bpy resolve com
stubs `.so` em `/home/user/blender-stubs` expostos via `LD_LIBRARY_PATH` —
o modo headless (Cycles CPU) nao toca em GL/X de verdade. O venv e os stubs
ficam FORA do repo e podem ser limpos entre sessoes; para reconstruir tudo
(venv + stubs, com a lista de simbolos extraida dos proprio .so do bpy):

```bash
sh tools/blender/make_env.sh
```

## Lote 8 — coletaveis + ceu (build_lote8.py)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_lote8.py
```

Onze coletaveis em `assets/collectibles/` (`coin` com faces "R$ 0,25" /
"BRASIL 2026", `golden` bilhete "PREMIADO", `coffee`, `bread`, `pastel`,
`sugarcane`, `pass` vale "BUSÃO", `coxinha`, `guarana`, `pix` celular com
tela emissiva, `umbrella`) + `aviao` e `drone` em `assets/sky_fx/`.
**Centrados na origem** (o node pai gira em Y no jogo) com frente -Y no
Blender. Textos/letreiros gerados por PIL no proprio build. O glow
translucido continua no GDScript nos dois caminhos (GLB e fallback).

## Lote 7 — mobiliario urbano (build_lote7.py)

Oito props originais em escala real: `cone`, `hidrante`, `orelhao`, `banco`,
`lixeira`, `poste`, `ponto` e `carrinho`, exportados para `assets/props/`.
Contrato: frente -Z no Godot (+Y no Blender), origem no chao, escala 1:1
(sem fit em runtime). Licao aprendida aqui: **nunca aplique subsurf em caixas
finas** (catmull-clark encolhe/entorta ripas e tetos); o orelhao usa casca
esferica com abertura recortada via bmesh. Drop-ins: `_optional_prop()` em
`game_3d.gd` e `_prop_glb()` em `building_kit.gd`.

## Lote 9A — cenario miudo (build_lote9a.py)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_lote9a.py
```

Oito GLBs em `assets/scene/`: `palmeira` (folhas = `painel_pena` do kit +
nervuras + 3 cocos), `arvore`, `caixa_dagua`, `varal`, `bandeira` (pano em
grade ondulada + Solidify), `outdoor`, `portao` e `barraca`. Pecas com cor
da fase usam materiais `Tint*` de albedo branco (`TintFabric`, `TintPaint`,
`TintMetal`) — o jogo pinta via `_tint_glb()`; nos previews eles recebem
uma cor-amostra mostarda so para a foto (o GLB sai branco). Licao daqui: a
luz `Cheia` do `setup_preview` nasce colada na origem e vira holofote no
chao em pecas altas — o `render_prop` deste lote a reposiciona proporcional
a distancia, e a limpeza entre pecas purga datablocks orfaos (luzes/cameras/
mundos/malhas) para nao colidir nomes (`Sol.001`...).
