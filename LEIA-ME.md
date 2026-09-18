# Pacote dos lotes 2, 3 e 4 — a rodada visual do jogo

Este pacote entrega **os três lotes prontos** da rodada de qualidade visual.
Cada um tem o seu próprio `docs/CHECKLIST_LOTE*.md` (passo a passo para você
aplicar no projeto) e o seu auditor numérico.

## 1. Ordem de aplicação (importante)

| Ordem | Lote | O que muda |
| --- | --- | --- |
| 1º | **Lote 2** (`lote2/`) | Renderizador `mobile` com plano B, céu, sol, câmera, tom de cor (ACES), medição de brilho |
| 2º | **Lote 3** (`lote3/`) | A rua da imagem: lajes, guias, pistas com linha amarela, calçadas, prédios, árvores e horizonte |
| 3º | **Lote 4** (`lote4/`) | Clima: chuva, asfalto molhado, poças, relâmpago e trovão |

> O Lote 3 depende do Lote 2 (o `_render_profile()`), e o Lote 4 depende dos dois.
> Aplicar fora de ordem dá erro de função não encontrada no `game_3d.gd`.

## 2. O que NÃO está aqui (e por quê)

| Peça | Situação |
| --- | --- |
| **Lote 1 — texturas PBR** (`assets/textures/pbr/`) | **Faltando.** Foram geradas em um ambiente anterior que foi apagado, e **não estão na branch do GitHub** (conferido: a pasta não existe no repositório). Sem elas, a rua do Lote 3 aparece com **cor plana** e o console avisa: *"texturas PBR ausentes; usando cor plana"*. |
| **Lote 5 — física** (CharacterBody3D, colisão, degrau na guia, atrito no chão molhado) | Ainda não construído (próximo da fila). |
| **Lote 6 — efeitos e personagem** (partículas de respingo/poeira, PBR do personagem, captura) | Ainda não construído. |
| **O jogo em si** (`scripts/game_3d.gd`, `project.godot`, cenas, sons) | Vem do repositório — veja a seção 4. |

## 3. Como conferir este pacote sozinho

```bash
python3 verificar_lotes.py          # contratos entre os lotes (0 problema esperado)

cd lote2 && python3 tools/check_def_use.py scripts/render_quality.gd scripts/game_3d_lote2_patch.gd
cd lote2 && python3 tools/analyze_render_profile.py && python3 tools/run_lote2_selftest.py
cd lote3 && python3 tools/check_def_use.py scripts/building_kit.gd && python3 tools/run_lote3_selftest.py
cd lote4 && python3 tools/check_def_use.py scripts/weather_system.gd && python3 tools/run_lote4_selftest.py
```

(Os auditores `audit_*.py` precisam do Pillow: `pip install pillow`.)

## 4. Qual branch baixar para testar

| Branch | O que tem | Para quem |
| --- | --- | --- |
| **`arena/01a0b492-busao`** | Jogo + trabalho visual **mais novo**, já integrado no projeto (texturas PBR, pele/pelo/pena, docs/QUALITY_AUDIT.md). Último envio: hoje às 16:44 | **Baixe esta se quiser ver o que há de mais novo no jogo** |
| `arena/01a0b48a-busao` / `arena/01a0adcf-busao` | Jogo no estado da rodada 4 (0 erro e 0 aviso de parser, verificado) | Base para aplicar os lotes deste pacote |
| `main` | Só o README | — |

**Recomendação prática:** baixe `arena/01a0b492-busao` (**Code → Download ZIP**)
para jogar/testar a versão mais recente do jogo. Se quiser testar exatamente a
base que eu verifiquei **mais** os lotes deste pacote, baixe
`arena/01a0b48a-busao` e siga os checklists (nesta ordem: 2, 3, 4).

> **Atenção:** os lotes 2/3/4 **não estão em nenhuma branch do GitHub** — esta
> sessão não tem permissão de enviar (push) para o repositório. Eles vêm por
> este pacote. Veja a seção 6 para o caminho de juntar tudo numa branch só.

## 5. Resumo do que foi verificado (nesta sessão)

| Verificação | Resultado |
| --- | --- |
| Arquivos obrigatórios dos 3 lotes | 34/34 presentes |
| Contratos entre lotes (perfil de render, materiais do clima × cenário, caminhos `res://`, roteiros de colagem, `project.godot`) | 0 problemas |
| Portões do Lote 2 (nomes, perfil, autoteste, tom) | 0 / 0 / 0 falhas / 0 problemas |
| Portões do Lote 3 (nomes, autoteste, auditor do cenário) | 0 / 0 falhas / 0 problemas |
| Portões do Lote 4 (nomes, autoteste, auditor do clima) | 0 / 0 falhas / 0 problemas |
| Reprodição dos assets do Lote 4 (nuvens + trovão) | idênticos byte a byte (determinísticos) |

Isso prova que os pacotes são **coerentes e reproduzíveis**. Não prova que o
jogo roda: **essa prova só o Godot** (no seu PC ou no Honor X8b) dá.

## 6. Como juntar tudo numa branch só (para a próxima sessão)

Esta sessão está encerrada e não pode enviar ao GitHub, então os lotes 2/3/4
vivem **no clone local** (`arena/01a0b48a-busao`, commits `290f497`, `a469924`,
`11f22e9`, `7f181ab`) e neste pacote. Numa sessão nova (que pode fazer push), o
caminho para ter tudo numa branch única é:

```bash
git clone https://github.com/berger33/busao.git
cd busao
git checkout -b visual/lotes-2-3-4 origin/arena/01a0b492-busao   # base mais nova
# descompacte este pacote por cima do clone e depois:
git add lote2 lote3 lote4 verificar_lotes.py LEIA-ME.md
git commit -m "Lotes 2-4 da rodada visual: renderizador, cenario da rua e clima"
git push -u origin visual/lotes-2-3-4
```

Depois, aplicar (ou pedir para a sessão aplicar) os blocos de colagem dos
checklists no `scripts/game_3d.gd` e no `project.godot` — é isso que faz os
lotes entrarem em ação dentro do jogo.
