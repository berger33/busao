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

---

## 2026-09-27 — REBUILD do rosto (Fase 3 v2): o que estava errado e o que mudou

As 5 fotos `18_rosto_fase3_final_*` da v1 foram reprovadas ("tudo errado: cabeça, orelhas,
cabelo, olhos, pálpebras, cílios, boca"). Diagnóstico numérico independente
(`tools/blender/diag_rosto.py`, numpy puro sobre o GLB) confirmou e quantificou:

| Defeito v1 | Medida v1 | Causa raiz | Correção v2 |
| --- | --- | --- | --- |
| Nariz atrás da testa | ponta −2,4 cm vs sobrancelha | tabela `PONTE_NARIZ` em z decrescente: busca binária do `_perfil` devolvia sempre o 1º valor (0,25 mm) | tabela ordenada crescente; ponta agora +1,4 cm à frente da sobrancelha (0,0911 vs 0,0768 m) |
| Queixo engolido pelo trapézio | corpo com 0,36 m de largura em z=1,51 | cabeça esculpida DENTRO da malha do corpo (Skin), sem queixo/mandíbula próprios | corpo termina no pescoço (z=1,50); cabeça é loft paramétrico próprio (97 anéis, campo facial com nariz/lábios/queixo/órbitas) |
| Crânio 17% fundo demais / caixa | profundidade excessina | seção craniana sem squash correto | largura 0,161 m / frente 0,079 m na linha do olho (gates 0,132–0,162 / 0,068–0,086) |
| Olhos a 39% da altura da cabeça | (canônico 50%) | z dos olhos herdado do corpo | olhos EXATAMENTE na linha média por construção (íris z=1,6213 vs meio 1,6201) |
| Boca/lábios/narinas/cílios/sobrancelhas FLUTUANDO | lábios +5,1 cm, linha da boca +5,0 cm, narinas +3,4 cm, cílios +1,7 cm, pálpebra inf. +1,65 cm, sobrancelha +0,9 cm, íris +3,4 mm da pele | móveis posicionados por coordenadas fixas assumidas, sem medir a pele real | TODO móvel pendurado por raycast (BVHTree) na malha final normalizada; aderência máx. 1,7 mm (sobrancelha), 0,5 mm (lábios/boca), 0 raio perdido |
| Sem orelhas | 0 malhas de orelha | — | 2 orelhas (elipsoide + concha + hélice), altura 48,5 mm, saliência 12,1 mm, espelhadas com recalc de normais |
| Coroa careca / franja enterrada | couro exposto no topo, franja dentro da testa | calota não acompanhava a linha do cabelo | calota por varredura esférica (≤1,95 rad, 40 passos, interpolação da linha do cabelo por azimute), 120/120 raios de cobertura sem furo; franja nasce da borda exata da calota, pontas a z=1,649 (olho +30 mm) |
| Rabo de cavalo no TRONCO | mechas em z −0,06–0,83 | Catmull-Rom com termo constante `p1·0,5` (deveria ser `p1`) e coeficiente cúbico de p0 errados | fórmula corrigida (passa exatamente pelos pontos de controle); 5 mechas na nuca, z 1,471–1,662, y 0,065–0,131 + elástico |
| Cabelo sombreando ao contrário | calota 0/331 faces para fora; franja virada para +Y | winding invertido + `from_pydata` descarta faces duplicadas (cards "duplos" viraram single) | `_mesh(..., refs=)` mede dot médio e vira TUDO quando a casca aponta para dentro; calota 331/331, franja 8/8 para fora; materiais doubleSided |
| Escleras/córneas "no chão" (validação cega) | centróide lido em (0,0,0) | primitivas de esfera guardam posição em `object.location`, vértices locais | `transform_apply` após criar: vértices em espaço-mundo; gates de olho reais (globo 9,9 mm atrás da pele, pálpebras 6/6 no globo) |

Métricas v2 (`heroi_julia_fase3_metrics.json` / `heroi_julia_pbr_metrics.json`):

- 18 gates anatômicos `gate_rosto` **verdes** (nariz frontal, olho na linha média, mandíbula
  0,125 m, crânio, órbita, pálpebras, aderência, orelhas, calota, franja, rabo, cílios).
- Tris total GLB **41.912** (orçamento 24k–46k); corpo 19.189 faces com 91,6% de quads;
  0 arestas não-manifold; altura 1,720 m; sola 0,012 m.
- GLB base 904,6 KB; GLB PBR **2.037,8 KB ≤ 2.048 KB** com 6 imagens embutidas; atlas 64,5%.
- Íris com textura radial + pupilas, cílios 4/olho a 0,35 mm da borda da pálpebra.
- 5 fotos re-renderizadas a 780×960@40spp + contato (estatística de pixels sã: luminância
  média 0,31–0,34, sem estouro/preto, 23–39% de tons de pele).

Reprodução v2 (render em resolução/amostragem maiores que a v1):

```sh
sh tools/blender/make_env.sh
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
/home/user/venv-blender/bin/python tools/blender/diag_rosto.py tools/blender/out/heroi_julia_base.glb
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24
sh tools/blender/run_bpy.sh tools/blender/render_rosto_5_angulos.py tools/blender/out/heroi_julia_pbr.glb docs/arte_alvo_final --prefix 18_rosto_fase3_final
cp tools/blender/out/heroi_julia_base.glb assets/characters/source/heroi_julia/heroi_julia_fase3.glb  # + demais artefatos
```

Fase 4 (rig) segue AGUARDANDO aprovação destas 5 fotos, conforme o plano.
