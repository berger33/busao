# Herói 10/10 — Fase 3 (cabelo e olhos)

**Data:** 2026-09-26  
**Script:** `tools/blender/build_heroi_julia.py`

## Entrega

- Olhos separados em esclera, íris e córnea; córnea usa transmissão/IOR barata e a íris usa bump radial procedural.
- Pálpebras superiores, sobrancelhas e cílios como cards finos separados.
- Cabelo em cards: 4 cards de franja, 6 de calota e **5 mechas** do rabo de cavalo.
- Material `CabeloJulia_alpha_scissor`: máscara binária com cutoff 0,5, sem blend/transparência ordenada; textura alpha 128×256 para manter o orçamento mobile.
- Contrato do runtime não foi alterado: o GLB ainda não substitui `personagens/hero_julia.glb`.

## Gate 3 / métricas

`heroi_julia_fase3_metrics.json` registra: 35.952 tris, 1,720 m, sola 0,012 m, 0 arestas não-manifold, 27 objetos Fase 3 e 5 mechas. O GLB mesh-only gerado ficou em 772,3 KB; todos os gates geométricos ficaram verdes.

Evidência visual: `docs/arte_alvo_final/15_rosto_detalhe_fase3.png`.
Artefatos WIP: `assets/characters/source/heroi_julia/heroi_julia_fase3.glb/.blend`, métricas e `julia_cabelo_alpha.png`.

## Reprodução

```sh
sh tools/blender/make_env.sh
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/render_detalhe.py tools/blender/out/heroi_julia_base.glb tools/blender/out/rosto_fase3.png --alvo rosto
```

O bake PBR da Fase 2 permanece separado; antes de publicar o GLB texturizado final, executar o bake sobre o `heroi_julia_base.blend` recém-gerado e repetir os gates de tamanho/texturas.
