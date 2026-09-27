# Herói 10/10 — Fase 3A: rosto da Júlia (sem cabelo) — 2026-09-26

Plano: `docs/PLANO_HEROI_10_10.md` · pré-requisito: `docs/execucao/HEROI_FASE2.md`

> Esta entrega separa deliberadamente o rosto do cabelo. **O cabelo de couro
> cabeludo, franja, rabo de cavalo e cards alpha não foi criado nem integrado.**
> A aprovação visual deste rosto é o gate para começar a Fase 3B.

## Entrega

Novo build `tools/blender/build_rosto_heroi_julia.py`, a partir do GLB PBR da
Fase 2:

- substitui o volume provisório de crânio pelo `CabecaRostoBase`: crânio oval,
  mandíbula afunilada, queixo discreto e orelhas, todos em malha manifold;
- cria olhos independentes e legíveis: abertura amendoada na órbita, anel
  limbal, íris castanha, pupila e ponto de brilho de córnea;
- acrescenta pálpebras, sobrancelhas e cílios mínimos. Eles são elementos do
  rosto; não há geometria ou material de penteado;
- acrescenta ponta/asa/narina, lábios superior/inferior com cavidade de boca;
- conserva materiais PBR simples e exportáveis pelo glTF — sem transparência
  de cabelo e sem Draco;
- gera `heroi_julia_rosto.glb` e `.blend` em `tools/blender/out/`, sem alterar
  `assets/characters/personagens/hero_julia.glb` nem o runtime antes da
  aprovação humana.

O renderer de revisão `tools/blender/render_rosto_heroi.py` gera o tríptico de
close (frente, 3/4 e perfil), sem roupa ou cabelo mascarando a leitura facial.

## Gate executado

| Item | Resultado | Status |
| --- | ---: | :---: |
| Malhas faciais | 31 (inclui 2 orelhas) | ✅ |
| Triângulos adicionados ao rosto | 7.468 | ✅ |
| Triângulos totais | 38.381 | ✅ |
| GLB de revisão | 1.766,4 KB | ✅ |
| Recursos faciais obrigatórios | 16/16 | ✅ |
| Cabelo/mecha/rabo de cavalo no GLB | 0 | ✅ |
| Draco | ausente | ✅ |

A checagem embutida falha se faltar qualquer grupo facial obrigatório ou se um
nome de objeto da entrega contiver `hair`, `cabelo`, `ponytail` ou `mecha`.
O exportador também foi verificado sem aviso de malha inválida.

## Revisão visual

`docs/arte_alvo_final/12_fase3_rosto.png`

O render mostra frente, três-quartos e perfil sob a mesma luz de estúdio. Ele
é a peça para validação do usuário: identidade do rosto, escala dos olhos,
formato de nariz, boca e sobrancelhas. O topo está propositalmente sem cabelo.

## Reproduzir

```sh
# Fases 1 e 2 — apenas se o diretório tools/blender/out/ não existir neste sandbox
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24

# Fase 3A — rosto
sh tools/blender/run_bpy.sh tools/blender/build_rosto_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/render_rosto_heroi.py \
  tools/blender/out/heroi_julia_rosto.glb \
  docs/arte_alvo_final/12_fase3_rosto.png
```

## Próximo passo — somente após validação

**Fase 3B — cabelo.** Sobre este mesmo crânio, criar raiz, franja, volume
cacheado e rabo de cavalo em cards `alpha_scissor`, depois verificar shimmer em
movimento. Nenhuma dessas peças entra nesta entrega de rosto.
