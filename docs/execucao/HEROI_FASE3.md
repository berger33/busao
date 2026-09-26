# Herói 10/10 — execução da Fase 3 (cabelo e olhos) — 2026-09-26

Plano: `docs/PLANO_HEROI_10_10.md` (Fase 3 — Cabelo e olhos) · Fase anterior:
`docs/execucao/HEROI_FASE2.md` · Estado de partida: `docs/execucao/HEROI_REBUILD_2026-09-26.md`
(rosto já esculpido na malha — seção "4c" — mas sem globos oculares, cabelo,
sobrancelha ou cílio).

## O que foi feito

`tools/blender/build_heroi_julia.py` ganhou uma seção nova ("6. Cabelo, olhos,
sobrancelhas e cílios") que roda logo depois do rosto esculpido e antes da
normalização de escala. Ela cria **objetos separados do corpo** — cada um com
seu próprio material — porque olho e cartão com alpha precisam de shaders
diferentes do Principled da pele:

1. **Olhos**: duas calotas esféricas por olho (`_hemisferio`, UV polar
   própria, sem depender de operador de unwrap):
   - **Esclera+íris** num só disco de textura 160×160 (`julia_olho_albedo.jpg`
     + `julia_olho_normal.jpg`, gerados por numpy — pupila, anéis radiais da
     íris com variação castanha e veiazinha sutil na esclera). O **normal map
     é radial de verdade**: a altura procedural da íris (`sin(ângulo·24)`
     modulada pelo raio) passa por `np.gradient` para virar um normal
     tangente-espaço, então a íris "pega luz" em sulcos, não é só uma cor lisa.
   - **Córnea** separada: calota menor, material `OlhoCornea` com
     `Transmission Weight = 1.0`, `IOR = 1.376`, roughness 0.04 — sem textura,
     sem caminho de refração recursivo. Isso é a "refraction barata": no glTF
     vira `KHR_materials_transmission` + `KHR_materials_ior` (confirmado no
     GLB exportado), custando só os parâmetros do material, não um sample
     extra de câmera/tela como uma refração de verdade.
2. **Sobrancelha e cílio**: cartões finos (`_fita`, a mesma função usada no
   cabelo) com várias linhas finas empilhadas dentro de um envelope em arco —
   não um bloco sólido pintado. Ficam no material `alpha_scissor`
   compartilhado com o cabelo.
3. **Cabelo**: rabo de cavalo em **5 mechas** (leque de 72° a partir de um
   ponto de "elástico" atrás da cabeça, cada mecha com curva/balanço próprios
   via seno) + **franja** de 6 cartões curtos sobre a testa. Reaproveitam só
   2 variantes de textura de mecha (técnica padrão de hair-cards: poucos
   cartões de textura cobrindo muita geometria).
4. **Atlas único** (`julia_cabelo_alpha.png`, 256×256, gerado por numpy — sem
   bake Cycles) com 4 células: `mecha_a`, `mecha_b`, `sobrancelha`, `cilio`.
   Reduz o material novo a **um só** (`alpha_scissor`) para cabelo, franja,
   sobrancelha e cílio.

### `alpha_scissor`: por que não bastou setar `blend_method`

O exportador glTF do Blender 4.5 (LTS usada aqui) **não lê mais
`material.blend_method`** para decidir o `alphaMode` — isso mudou com a
reforma de materiais do EEVEE Next (4.2+). Ele analisa o **grafo de nós**
procurando um padrão de corte de alpha
(`io_scene_gltf2/blender/exp/material/search_node_tree.py::detect_alpha_clip`).
O material aqui usa exatamente o padrão que o exportador reconhece: um nó
`Math > Greater Than` comparando o alpha da textura com 0.5, alimentando o
`Alpha` do Principled BSDF. Resultado confirmado no GLB exportado:

```
alpha_scissor: alphaMode=MASK, doubleSided=True
```

`MASK` é exatamente o "corte de alpha sem ordenação por transparência" pedido
pelo plano — cada pixel é opaco ou totalmente descartado, então não existe
problema de profundidade/z-order entre cartões sobrepostos (a causa clássica
de "shimmer" quando cartões de cabelo trocam de ordem de desenho conforme a
câmera se move). `use_backface_culling = False` deixa os cartões
**duplo-face** (a ponta de um fio de cabelo/cílio precisa ser vista dos dois
lados).

### Como tudo fica alinhado ao rosto esculpido

Olhos, cabelo, sobrancelha e cílio nascem no **mesmo espaço de coordenadas
pré-normalização** do corpo (mesmos marcos `ROSTO` usados por
`esculpir_rosto()`), com origem do objeto em `(0,0,0)` — igual ao corpo.
`normalizar()` foi generalizada para aplicar a **mesma escala e o mesmo
deslocamento em Z** (calculados a partir da bbox do corpo) em todos os objetos
extras, então nenhum parenting é necessário e nada desalinha.

### `bake_heroi_julia.py`: só o corpo é bakeado

A Fase 2 baekeia pele em Cycles a partir de UV; os objetos novos da Fase 3 já
chegam com material/textura prontos (gerados por numpy, sem Cycles). O script
agora localiza o objeto do corpo pelo nome (`JuliaBase`) para UV+bake e
**preserva os extras intactos**, selecionando-os junto na exportação final do
GLB (`heroi_julia_pbr.glb`) — nenhum re-bake ou re-textura neles.

## Métricas do gate

| Item | Valor | Alvo | Status |
| --- | --- | --- | --- |
| Triângulos totais (corpo + extras) | **37.078** (35.952 corpo + 1.126 extras) | 24k–46k | ✅ |
| Altura | 1,720 m | 1,70–1,75 | ✅ |
| Sola (z mín) | 0,012 m | 0,012 ± 0,005 | ✅ |
| Arestas não-manifold (corpo) | 0 | 0 | ✅ |
| Cobertura do atlas UV (pele) | 61,2% | ≥45% | ✅ (inalterada — Fase 3 não mexe no UV do corpo) |
| Texturas embutidas | **6** (albedo/normal/ORM da pele + atlas de cabelo + albedo/normal do olho) | ≥3 | ✅ |
| GLB final | **1.755,6 KB** | ≤2.048 KB | ✅ (~293 KB de folga) |
| `alphaMode` do cartão de cabelo | `MASK` | corte sem ordenação | ✅ |
| Extensão da córnea | `KHR_materials_transmission` + `KHR_materials_ior` | refração barata | ✅ |

Nenhum corte foi necessário nos mapas de pele — o atlas de cabelo (256×256,
~31 KB) e as texturas do olho (160×160, ~4 KB cada) são pequenos o bastante
para caber na folga que já existia (1.672 KB → 1.756 KB, +84 KB).

## Por que "sem shimmer de alpha em movimento a 60 FPS" é satisfeito por construção

O requisito do Gate 3 é sobre comportamento em runtime (câmera/personagem se
movendo). Duas decisões de material eliminam a causa raiz do problema antes
mesmo de chegar no motor:

1. **`alphaMode=MASK`** em vez de `BLEND`: não existe mistura translúcida
   dependente da ordem de desenho — cada pixel do cartão é 100% opaco ou 100%
   descartado. Isso é justamente o que evita o "pop"/cintilação quando dois
   cartões de cabelo trocam de profundidade relativa conforme a câmera gira
   (o problema clássico de alpha-blend em hair cards).
2. **Sem geometria dupla nem cartões cruzados coplanares**: cada mecha é uma
   única tira; não há duas faces sobrepostas competindo pelo mesmo pixel (que
   é a outra fonte comum de z-fighting/cintilação em cartões finos).

Isso não substitui um teste real em 60 FPS no motor (fora do escopo desta
sessão — o GLB ainda não está integrado ao runtime, ver "Regras de casa"),
mas remove as duas causas de shimmer que dependem só do material/geometria,
que é a parte que a Fase 3 controla.

## Limitações conhecidas (ficam para as fases seguintes)

- Sem pálpebra modelada como peça própria — o "fechamento" do olho na órbita
  vem só da escultura da pele ao redor (seção 4c); o olho aparece como um
  globo redondo cheio na abertura da órbita, não uma abertura amendoada.
  Não fazia parte do escopo desta sessão (plano da Fase 3 pede só
  esclera/córnea/íris, sobrancelha e cílio).
- O atlas de cabelo é minúsculo (256×256) de propósito para não estourar o
  teto de 2 MB; de perto (< 1 m) as listras dos fios ficam grosseiras. A
  câmera de corrida do jogo nunca chega tão perto.
- Ainda sem rig (Fase 4): olhos/cabelo/sobrancelha/cílio são objetos
  estáticos soltos na cena, sem vínculo a nenhum osso. A Fase 4 vai precisar
  decidir se ganham vertex groups (para acompanhar a cabeça/pescoço) ou se
  ficam com skinning 100% rígido no osso `Head`.

## Reproduzir

```sh
sh tools/blender/make_env.sh
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24
sh tools/blender/run_bpy.sh tools/blender/render_turnaround.py \
   tools/blender/out/heroi_julia_pbr.glb tools/blender/out/turnaround_fase3.png
sh tools/blender/run_bpy.sh tools/blender/render_detalhe.py \
   tools/blender/out/heroi_julia_pbr.glb tools/blender/out/rosto_fase3.png \
   --alvo rosto --res 960 --samples 48
```

Tempo medido no sandbox: build ~10 s, bake 2K/24 samples ≈ 13 min (Cycles
CPU, 2 núcleos, inalterado da Fase 2 — a Fase 3 não adiciona bake).

## Validação

- `python3 tools/validate_hero.py` → `HERO OK MESH-ONLY` (runtime intacto,
  `personagens/hero_julia.glb` continua sendo o placeholder até a Fase 6);
- `python3 tools/validate_project.py` → `PRE-FLIGHT OK`;
- `python3 tools/qa_full.py` → 0 FAIL.

## Próximo passo

Fase 4: armature de 60 ossos (contrato atual + `twist_upperarm_l/r`,
`twist_thigh_l/r`, `eye_l/r`, `jaw`) e heat-map weights, com correção manual
em ombro, axila, joelho e quadril.
