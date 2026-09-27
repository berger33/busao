# Herói 10/10 — Fase 3 (rosto completo, cabelo e olhos)

**Data:** 2026-09-26
**Script principal:** `tools/blender/build_heroi_julia.py`
**Bake:** `tools/blender/bake_heroi_julia.py --res 2048 --samples 24`

## Entrega

- Rosto completo sobre a escultura já existente: lábios com superfície curva, linha da boca, narinas discretas, pálpebras superiores/inferiores, sobrancelhas em arco, cílios finos, pupilas e brilho ocular.
- Olhos separados em **esclera + íris + pupila + córnea**; córnea usa `KHR_materials_transmission`/IOR barata, e a íris ganhou textura própria com **normal radial** procedural.
- Cabelo em **cards com alpha scissor**: franja/volumes de calota e rabo de cavalo com exatamente **5 mechas** sinuosas.
- Material `CabeloJulia_alpha_scissor`: glTF `alphaMode=MASK` com cutoff efetivo 0,5, sem alpha blend nem ordenação por transparência no cabelo. A única peça em `BLEND` é a córnea.
- Contrato do runtime não foi alterado: `assets/characters/personagens/hero_julia.glb` continua sendo substituído apenas na Fase 6.

## Gate 3 / métricas

`assets/characters/source/heroi_julia/heroi_julia_fase3_metrics.json` registra:

| Métrica | Valor | Gate |
| --- | ---: | --- |
| Tris corpo | 35.952 | ✅ |
| Tris extras Fase 3 | 4.158 | — |
| Tris total GLB | 40.110 | ✅ 24k–46k |
| Altura | 1,720 m | ✅ |
| Sola | 0,012 m | ✅ |
| Arestas não-manifold no corpo | 0 | ✅ |
| Objetos Fase 3 | 49 | — |
| Mechas do rabo | 5 | ✅ |
| GLB mesh-only | 952,2 KB | ✅ |

`assets/characters/source/heroi_julia/heroi_julia_pbr_metrics.json` registra: atlas UV 61,2%, GLB PBR 1.971,9 KB (≤ 2.048 KB), 6 imagens embutidas (`julia_albedo`, `julia_normal`, `julia_orm`, `julia_iris_color`, `julia_iris_normal_radial`, `julia_cabelo_alpha`) e gate verde.

Evidências visuais:

- `docs/arte_alvo_final/15_turnaround_fase3.png` — corpo completo com cabelo/rosto.
- `docs/arte_alvo_final/16_rosto_fase3.png` — close do rosto completo a distância de validação.
- `docs/arte_alvo_final/18_rosto_fase3_final_1_perfil_esq.png` a `18_rosto_fase3_final_5_perfil_dir.png` — **5 fotos finais** do rosto em ângulos diferentes para aprovação antes da Fase 4/cabelo final.
- `docs/arte_alvo_final/18_rosto_fase3_final_contato_5_angulos.png` — contato horizontal com as 5 vistas.

Artefatos WIP persistidos:

- `assets/characters/source/heroi_julia/heroi_julia_fase3.glb/.blend` + métricas.
- `assets/characters/source/heroi_julia/heroi_julia_pbr.glb/.blend` + métricas.
- Texturas em `assets/textures/heroi/`: albedo, normal, ORM, alpha do cabelo, cor da íris e normal radial da íris.

## Reprodução

```sh
sh tools/blender/make_env.sh
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24
sh tools/blender/run_bpy.sh tools/blender/render_turnaround.py tools/blender/out/heroi_julia_pbr.glb docs/arte_alvo_final/15_turnaround_fase3.png
sh tools/blender/run_bpy.sh tools/blender/render_detalhe.py tools/blender/out/heroi_julia_pbr.glb docs/arte_alvo_final/16_rosto_fase3.png --alvo rosto
sh tools/blender/run_bpy.sh tools/blender/render_rosto_5_angulos.py tools/blender/out/heroi_julia_pbr.glb docs/arte_alvo_final --prefix 18_rosto_fase3_final --res-x 720 --res-y 900 --samples 24
```

## Observações para a Fase 4

O herói continua mesh-only. A próxima etapa é o armature de 60 ossos com `eye_l/r` e `jaw`; as peças de olho/cílios/cabelo já estão separadas para receber parent/weights ou rig auxiliar sem alterar o contrato do runtime.
