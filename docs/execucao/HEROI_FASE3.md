# Herói 10/10 — Fase 3 concluída (rosto final, olhos e cabelo)

**Data:** 2026-09-26  
**Scripts:** `tools/blender/build_heroi_julia.py`, `tools/blender/bake_heroi_julia.py`, `tools/blender/render_rosto_5_angulos.py`
**Plano:** `docs/PLANO_HEROI_10_10.md` · Fase 3 — cabelo e olhos

## Entrega

- Rosto completo com leitura em close: olhos, pálpebras, sobrancelhas/cílios, lábios, sulco de boca, narinas e o relevo facial já esculpido na malha (órbitas, nariz, queixo, maçãs e orelhas).
- Olhos separados em **esclera + íris + pupila + córnea**; a íris tem textura própria (`julia_iris_color.png`) e **normal radial** (`julia_iris_normal.png`); a córnea é uma casca separada com transmissão/alpha leve para refração barata.
- Cabelo em **cards com alpha scissor**: franja curta, calota em cards, mechas laterais e rabo de cavalo em **5 mechas**; material `CabeloJulia_alpha_scissor` exportado como glTF `alphaMode=MASK` com cutoff 0,5.
- Sobrancelhas e cílios ficam em geometria/card opaco fino, sem depender de sorting por transparência.
- Runtime preservado: `assets/characters/personagens/hero_julia.glb` não foi substituído nesta fase.

## Gate 3 / métricas

| Métrica | Valor | Gate |
| --- | ---: | --- |
| Triângulos do corpo | 35.952 | ✅ |
| Triângulos extras Fase 3 | 3.398 | — |
| **Triângulos totais no GLB** | **39.350** | ✅ (24k–46k) |
| Altura | 1,720 m | ✅ |
| Sola z | 0,012 m | ✅ |
| Arestas não-manifold no corpo | 0 | ✅ |
| Objetos Fase 3 | 43 | — |
| Mechas do rabo | 5 | ✅ |
| Atlas UV do corpo | 61,2% | ✅ (≥45%) |
| Imagens embutidas no GLB PBR | 6 | ✅ (≥4) |
| GLB PBR final | 1.801,0 KB | ✅ (≤2.048 KB) |
| Cabelo alpha | `MASK` | ✅ alpha-scissor/mobile-safe |

Observação do gate de shimmer: os cards do cabelo usam máscara binária 0/1 e `alphaMode=MASK`, não `BLEND`; as mechas do rabo têm espaçamento em Y para evitar coplanaridade durante movimento a 60 FPS.

## Evidência visual — 5 fotos finais para aprovação

As cinco imagens abaixo foram renderizadas a partir de `tools/blender/out/heroi_julia_pbr.glb` com câmera a 2 m:

1. `docs/arte_alvo_final/18_rosto_fase3_final_1_perfil_esq.png`
2. `docs/arte_alvo_final/18_rosto_fase3_final_2_tres_quartos_esq.png`
3. `docs/arte_alvo_final/18_rosto_fase3_final_3_frente.png`
4. `docs/arte_alvo_final/18_rosto_fase3_final_4_tres_quartos_dir.png`
5. `docs/arte_alvo_final/18_rosto_fase3_final_5_perfil_dir.png`

Contato para revisão rápida: `docs/arte_alvo_final/18_rosto_fase3_final_contato_5_angulos.png`.

## Artefatos persistidos

- `assets/characters/source/heroi_julia/heroi_julia_fase3.glb/.blend`
- `assets/characters/source/heroi_julia/heroi_julia_pbr.glb/.blend`
- `assets/characters/source/heroi_julia/heroi_julia_fase3_metrics.json`
- `assets/characters/source/heroi_julia/heroi_julia_pbr_metrics.json`
- Texturas versionadas em `assets/textures/heroi/`: albedo, normal, ORM, cabelo alpha, íris color e íris normal.

## Reprodução

```sh
sh tools/blender/make_env.sh
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24
sh tools/blender/run_bpy.sh tools/blender/render_rosto_5_angulos.py \
  tools/blender/out/heroi_julia_pbr.glb docs/arte_alvo_final \
  --prefix 18_rosto_fase3_final --res-x 720 --res-y 900 --samples 24
```

## Próximo passo

Fase 4: armature de ~60 ossos, pesos por heat-map e correção manual em ombro, axila, joelho e quadril; manter compatibilidade com o contrato atual do runner.
