# Herói 10/10 — execução da Fase 2 (UV + bake PBR) — 2026-09-26

Plano: `docs/PLANO_HEROI_10_10.md` · Fase anterior: `docs/execucao/HEROI_FASE0_FASE1.md`

## O que foi feito

Novo `tools/blender/bake_heroi_julia.py`, que parte do `heroi_julia_base.blend`
da Fase 1 e entrega o corpo texturizado:

1. **UV**: Smart UV Project (limite 64°) + `average_islands_scale` +
   `pack_islands` → **57,3% de cobertura** do atlas (era 43,1% só com o smart
   project; o gate pedia ≥45%).
2. **Material procedural de pele** em Cycles como fonte do bake:
   - variação macro de tom (noise + ramp entre três tons de pele morena);
   - rubor em soft light nas regiões de dobra;
   - microrrelevo: Voronoi de poro (escala 420) combinado em overlay com noise
     fino (escala 120) entrando num nó Bump;
   - roughness variável (0,38 oleoso → 0,66 fosco) por noise;
   - SSS 0,18 com raio (12, 5, 3) mm.
3. **Bake** dos quatro canais: `DIFFUSE` (só cor), `NORMAL`, `ROUGHNESS` e `AO`.
4. **ORM** empacotado via numpy no padrão glTF (R=oclusão, G=roughness, B=metal=0).
5. **Material final** enxuto (Principled + 3 texturas) e export GLB com as
   imagens embarcadas.

## Métricas do gate

| Item | Valor | Alvo | Status |
| --- | --- | --- | --- |
| Texturas embarcadas | **3** (albedo, normal, ORM) | ≥3 | ✅ |
| Cobertura do atlas UV | **57,3%** | ≥45% | ✅ |
| Albedo | 2048², JPEG q88 — 374 KB | 2K | ✅ |
| Normal | 1024², JPEG q92 — 151 KB | — | ✅ |
| ORM | 1024², JPEG q88 — 238 KB | — | ✅ |
| GLB final | **1.487 KB** | ≤2.048 KB | ✅ |
| Desvio-padrão dos bakes | albedo 0,371 · normal 0,250 · rough 0,357 · AO 0,427 | > 0 (não chapado) | ✅ |

Texturas versionadas em `assets/textures/heroi/`.
Comparativo Fase 1 (barro) × Fase 2 (PBR): `docs/arte_alvo_final/8_fase2_pbr.png`.
Close-up da pele: `docs/arte_alvo_final/9_fase2_closeup_pele.png`.

## Duas armadilhas encontradas (documentadas no código)

1. **Bake sem nó selecionado não grava nada.** O `bpy.ops.object.bake` escreve
   no nó de imagem ativo **e selecionado**; só marcar `nodes.active` fazia o
   operador retornar `FINISHED` com a textura intacta. O script agora
   deseleciona tudo, seleciona o nó e ainda valida o desvio-padrão do buffer.
2. **`Image.save()` numa imagem GENERATED grava o padrão gerado, não o bake.**
   O PNG saía chapado (std 0,000) mesmo com o buffer correto (std 0,234).
   Solução: copiar o buffer para uma imagem nova via `pixels.foreach_set` e
   salvar essa cópia. Medido antes/depois no próprio log.
3. **PNG 2K nos três mapas = GLB de 11,5 MB.** Resolvido com albedo 2K + normal
   e ORM em 1K, todos em JPEG (q88/q92) → 1,49 MB.

## Reproduzir

```sh
sh tools/blender/make_env.sh                                  # venv bpy fica fora do repo
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24
sh tools/blender/run_bpy.sh tools/blender/render_turnaround.py \
   tools/blender/out/heroi_julia_pbr.glb tools/blender/out/turnaround_depois_f2.png
```

Tempo medido no sandbox: bake 2K/24 samples ≈ 7,7 min (Cycles CPU).

## Limitações conhecidas (entram na Fase 3)

- A concentração de poro ainda aparece em manchas em algumas ilhas do atlas —
  ajuste de escala do Voronoi por região resolve junto com o mapa de rosto.
- Corpo continua sem rosto, cabelo e roupa: é Fase 3 (rosto/cabelo) e Fase 6
  (camisa, legging, tênis).
- Sem rig ainda — Fase 4.

## Próximo passo

Fase 3: rosto detalhado (olho na órbita, pálpebra, lábio) e cabelo em cards com
alpha. É o que faz o personagem "olhar" para a câmera na tomada de close.
