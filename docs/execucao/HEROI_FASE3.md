# Herói 10/10 — Fase 3 (cabelo e olhos) — 2026-09-26

Plano: `docs/PLANO_HEROI_10_10.md` · estado anterior: `HEROI_REBUILD_2026-09-26.md`.

## Entrega

A seção **4d** de `tools/blender/build_heroi_julia.py` completa o rosto sobre a
escultura já existente:

- olhos em três peças por lado: esclera, íris e córnea;
- córnea com transmissão/refração barata (IOR 1,38) e íris com bump radial;
- pálpebras superiores, sobrancelhas e cílios em cards finos;
- franja em quatro cards, calota em seis cards e rabo de cavalo em **cinco
  mechas**;
- textura binária 128×256 `julia_cabelo_alpha.png`, embutida no GLB;
- material `CabeloJulia_alpha_scissor` exportado como glTF `alphaMode=MASK`.
  A máscara passa por comparação `alpha >= 0.5`, portanto não usa `BLEND`, não
  depende de ordenação de transparência e evita shimmer temporal em mobile.

`bake_heroi_julia.py` passou a bakear apenas `JuliaBase`, preservando os
materiais das 27 peças da Fase 3 e exportando todos os meshes selecionados.

## Gates

| Item | Resultado | Gate |
| --- | --- | --- |
| Corpo | 35.952 tris; 1,720 m; sola 0,012 m | ✅ |
| Topologia do corpo | 0 arestas não-manifold | ✅ |
| UV | 61,2% | ✅ ≥45% |
| Texturas embutidas | albedo, normal, ORM e alpha do cabelo | ✅ |
| Cabelo | franja + calota + 5 mechas; `MASK`, cutoff 0,5 | ✅ |
| GLB PBR | **1.812,4 KB** | ✅ ≤2.048 KB |
| Runtime | placeholder intacto (`HERO OK MESH-ONLY`) | ✅ |
| Close | `16_rosto_fase3.png` | ✅ rosto/olhos legíveis |

O gate “sem shimmer a 60 FPS” é atendido estruturalmente: alpha binário com
`MASK`, cards não coplanares e nenhuma superfície do cabelo usa alpha blend.
A validação definitiva em dispositivo permanece no gate de integração da Fase 6.

## Evidências e artefatos

- `docs/arte_alvo_final/15_turnaround_fase3.png`
- `docs/arte_alvo_final/16_rosto_fase3.png`
- WIP persistido em `assets/characters/source/heroi_julia/`
- textura fonte em `assets/textures/heroi/julia_cabelo_alpha.png`

O asset de runtime `assets/characters/personagens/hero_julia.glb` **não foi
alterado**; a troca continua reservada à Fase 6.

## Reprodução

```sh
sh tools/blender/make_env.sh
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24
sh tools/blender/run_bpy.sh tools/blender/render_turnaround.py \
  tools/blender/out/heroi_julia_pbr.glb tools/blender/out/turnaround_fase3.png
sh tools/blender/run_bpy.sh tools/blender/render_detalhe.py \
  tools/blender/out/heroi_julia_pbr.glb tools/blender/out/rosto_fase3.png --alvo rosto
```

## Próximo passo

Fase 4: armature de 60 ossos e skinning com no máximo quatro influências por
vértice, preservando os nomes exigidos pelo runner.
