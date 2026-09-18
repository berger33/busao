# Lote 3 — a rua (cenário por quarteirões, materiais PBR e horizonte)

Objetivo do lote: transformar o cenário em algo próximo da imagem de
referência — faixa central elevada de lajes, guias, pistas com linha amarela
dupla, calçadas com mosaico, prédios de 2-3 pavimentos, árvores, mobiliário,
folhas no chão e horizonte lavado pela névoa — mantendo o orçamento de
desempenho do Honor X8b (Adreno 610).

## Arquivos

| Arquivo | O que é |
| --- | --- |
| `resources/world_spec.json` | **Fonte única da verdade**: faixas, lajes, prédios, mobiliário, paletas, orçamento e o mapa de materiais PBR. O jogo e o auditor leem daqui. |
| `scripts/building_kit.gd` | Construtor do cenário (741 linhas): monta um quarteirão inteiro a partir do spec, com `MultiMesh` para o que se repete, semente fixa por quarteirão e metas (`superficie`/`colisor`) para o Lote 5. Inclui o `ChunkStreamer` que recicla quarteirões e o `build_horizon()`. |
| `tools/audit_world.py` | Auditor numérico: valida o spec (faixas, materiais, orçamento, paletas), espelha o leiaute do quarteirão em Python e cobra as invariantes, e confere o código do kit. Desenha `docs/preview_world_lote3.png`. |
| `tools/run_lote3_selftest.py` | Autoteste: 6 defeitos plantados (faixa estreita, PBR inexistente, sombra quente, orçamento estourado, medida fixa, kit sem MultiMesh) + o cenário real. |
| `tools/world_facts.json` | Fatos do engine (4.7.2) e orçamento de referência do Adreno 610. |
| `tools/check_def_use.py` | Verificador de nomes: nenhuma variável/função usada sem existir (0 problemas). |
| `docs/PATCH_GAME_3D_LOTE3.md` | Roteiro de colagem no `game_3d.gd` (4 blocos + 3 chamadas). |
| `docs/CHECKLIST_LOTE3.md` | Passo a passo para o usuário (do ZIP até o print no celular). |
| `project.godot.lote3` | Fragmento de `project.godot` com a linha do autoload do Lote 2 (confira se já existe). |
| `docs/preview_world_lote3.png` | Prévia desenhada pelo auditor (corte transversal, planta de 2 quarteirões, materiais e paletas). |

## Decisões

- **Nada de medida solta no código**: toda medida vem do `world_spec.json`
  (o auditor reprova se achar um número fixo como a borda da calçada).
- **Determinismo**: `RandomNumberGenerator` com semente do spec por quarteirão —
  o mesmo quarteirão sai sempre igual, o que permite auditar e comparar.
- **Orçamento**: alvo ≤ 80 malhas por quarteirão (hoje ~210 *objetos*, dos quais
  a maioria entra em 6 `MultiMesh`: lajes, mosaicos, janelas, postes, folhas e o
  que mais se repetir). O auditor cobra o teto do spec e o `visibility_range_end`.
- **Materiais**: `ORMMaterial3D` (albedo + normal + ORM) apontando para as 10
  texturas do Lote 1; o que não tem textura usa cor plana e o auditor avisa.
- **Sem downloads externos**: tudo é gerado/montado a partir do que já existe
  no projeto (restrição do sandbox e escolha de escopo do plano).
- **Física**: por enquanto o cenário é estático; as superfícies já saem com
  `set_meta("superficie", ...)` e `set_meta("colisor", ...)` para o Lote 5
  (CharacterBody3D + colisores) sem precisar refatorar o kit.

## Portões (gates) deste lote

```bash
python3 tools/check_def_use.py scripts/building_kit.gd   # 0 problemas, exit 0
python3 tools/audit_world.py                             # 0 problemas, 0 avisos
python3 tools/run_lote3_selftest.py                      # 0 falhas (6 defeitos plantados)
```

Saída do auditor (execução verde):

```
spec: world_spec.json v3 | seed 20260918 | 15 materiais | 4 paletas
quarteirao 0: 29.852 m, 315 lajes, 7 lotes, 14 postes, 4 arvores
quarteirao 1: 28.152 m, 297 lajes, 7 lotes, 13 postes, 3 arvores
quarteirao 2: 27.824 m, 296 lajes, 6 lotes, 13 postes, 3 arvores
hash do leiaute: 58412010ebc4
resumo: 0 problema(s), 0 aviso(s)
```

> A prévia (`docs/preview_world_lote3.png`) é gerada pelo auditor porque o
> sandbox não tem GPU. A checagem visual de verdade é o seu Godot 4.7.2.

## Próximo lote (4) — anotações para não esquecer

- **PCSS não existe no renderizador `mobile`**: `Light3D.light_angular_distance`
  é exclusivo do Forward+ (confirmado na documentação 4.7.2). No `mobile`, a
  suavidade da sombra vem de `shadow_blur` e do tamanho do shadow map.
- Áreas de efeito do Lote 4: chuva (`GPUParticles3D` com
  `ParticleProcessMaterial`), asfalto molhado (rugosidade + `ReflectionProbe`),
  respingos, névoa volumétrica só no Forward+ (`FogVolume`), trovões e o
  controle de clima por paleta (`world_spec.json → paletas`).
- O auditor do Lote 4 (`tools/audit_lighting.py`) deve cobrar: energia do sol,
  cor da névoa por paleta, brilho especular do asfalto molhado e o custo
  (número de partículas/luzes) dentro do orçamento do Adreno 610.
