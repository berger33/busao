# Modelos de animais (drop-in)

O jogo usa o arquivo `<especie>.glb` desta pasta se ele existir
(pombo, aves do lote 2 e quadrupedes do lote 3); sem o arquivo, entra o
modelo procedural. Escala, assentamento no chao e animacao (caminhada em
loop, idle e a pose de crouch — bicar/pastar/deitar) sao automaticos.

## O que ja vem aqui

- **`pombo.glb`** — pombo urbano (Columba livia) **modelado no proprio
  repositorio** por Blender headless (`tools/blender/build_pombo.py`):
  corpo loftero com pescoco verde iridescente e peito claro, asa dobrada
  com pontas de primarias, cauda em leque com banda branca, pernas com
  articulacao; rig de 13 ossos e clipes `Walk` (16 frames, com o balanco
  de cabeca classico) e `Idle` (48 frames). Licenca: trabalho original do
  projeto (CC0).
- **`caramelo.glb`** — a **raposa** da colecao oficial da Khronos
  (`glTF-Sample-Assets`, CC0 1.0; conversao glTF por AsoboStudio/scurest).
  Rigada e skinada, com os clips `Survey`, `Walk` e `Run` — o jogo toca o
  `Walk` em loop. Canino laranja: em escala de arcade, le como um caramelo
  de rua. Para voltar ao cachorro procedural, basta apagar este arquivo.
- **`passaro.glb`** — tico-tico (Thraupis sayaca) **modelado no proprio
  repositorio** por Blender headless (lote 2, `tools/blender/build_aves.py`):
  peito amarelo, costas/cabeça escuras, cauda listrada,
  patas rosas; rig de 12 ossos e clipes `Walk` (14 frames) e `Fly`
  (bater de asas). No voo o jogo toca o `Fly` em loop; no chao, o `Walk`.
  Licenca: trabalho original do projeto (CC0).
- **`gaivota.glb`** — gaivota de praia (Larus livia) **modelada no proprio
  repositorio** por Blender headless (lote 2, `tools/blender/build_aves.py`):
  corpo branco, capa cinza-azulada, bico amarelo com anel vermelho, patas
  amarelas; rig de 12 ossos e clipes `Walk` (16 frames) e `Fly`. Idem acima
  sobre os clipes. Licenca: trabalho original do projeto (CC0).
- **`urubu.glb`** — urubu-de-crista (Coragyps atratus) **modelado no proprio
  repositorio** por Blender headless (lote 2, `tools/blender/build_aves.py`):
  plumagem preto-carvao, cabeca nua vermelho-alaranjada, cristas curtas,
  patas rosadas; rig de 12 ossos e clipes `Walk` (22 frames, andar arrastado)
  e `Fly`. Idem acima sobre os clipes. Licenca: trabalho original do projeto
  (CC0).

  Aves do lote 2 seguem o mesmo contrato: frente +Z, origem no chao
  (rest e `Walk` assentados — `Fly` eh a pose de voo de pernas recolhidas),
  `Fly` no nome do clip para o ciclo aereo.
- **`capivara.glb`** — capivara (Hydrochoerus hydrochaeris) **modelada no
  proprio repositório** por Blender headless (lote 3,
  `tools/blender/build_quadrupedes.py`): corpo tosa arroxeado, focinho
  quadrado, orelhas curtas; rig de 16 ossos (4 principais + 4 pernas de 3
  segmentos) e clipes `Walk` (16f, diagonais FE+TR / FD+TD), `Idle`
  (respiração + cauda, 12f) e `Lie` (deitada — a capivara se deita no
  crouch). Tamanhos de jogo: 1,35 m x 0,62 m. Licença: trabalho original do
  projeto (CC0).
- **`cavalo.glb`** — cavalo mestiço de rua **modelado no proprio
  repositório** por Blender headless (lote 3): tordilho, crina e topete
  escuros, cauda com tufo; rig de 16 ossos e clipes `Walk` (16f), `Idle`
  (12f) e `Graze` (pastando: cabeça no chao + mastigar — o crouch do
  cavalo). Tamanhos de jogo: 1,90 m x 1,45 m. Licença: trabalho original
  (CC0).
- **`boi.glb`** — boi mestiço de cria **modelado no proprio repositório**
  por Blender headless (lote 3): branco com manchas castanhas, focinho e
  úbere rosados, chifres claros; rig de 16 ossos e clipes `Walk` (16f,
  passo lento), `Idle` (12f) e `Graze` (crouch = pastar). Tamanhos de
  jogo: 2,00 m x 1,50 m. Licença: trabalho original (CC0).

  Quadrúpedes do lote 3 seguem o mesmo contrato das aves (frente +Z,
  origem no chao), com a diferenca de que o crouch usa o clip `Graze`
  (pastar) no cavalo/boi e `Lie` (deitada) na capivara — o
  `world_animal.gd` troca de clip por pose em `_sincronizar_clip_glb`.
- **`macaco.glb`** — sagui meio-ereto **modelado no proprio repositório**
  por Blender headless (lote 4, `tools/blender/build_lote4.py`): pelagem
  castanha, rosto e peito claros, cauda longa enrolada por cima das
  costas; rig de 9 ossos (Corpo/Pescoco/Cabeca, Cauda em 2 segmentos,
  2 bracos e 2 pernas) e clipes `Walk` (16f, membros dianteiros na
  contra-fase das pernas), `Idle` (16f) e `Lie` (agachado, cauda
  enrolada, espiando = crouch). Tamanhos de jogo: 0,85 m x 0,95 m.
  Licença: trabalho original do projeto (CC0).
- **`caranguejo.glb`** — caranguejo-vermelho **modelado no proprio
  repositório** por Blender headless (lote 4): casco em cupula
  laranja, olhos em hastes, pinças grandes e 3 patas por lado; rig de
  9 ossos (Corpo, 2 pinças, 6 patas) e clipes `Walk` (16f, garra de
  tesoura com ondulacao), `Idle` (12f, pinça esquerda em saudação) e
  `Lie` (corpo abaixado, patas dobradas = crouch). Tamanhos de jogo:
  0,60 m x 0,30 m. Licença: trabalho original do projeto (CC0).

## Como trocar por outros modelos

Substitua qualquer `<especie>.glb` por um GLB rigado com animacao de
caminhada. Fonte CC0 recomendada para cao (dog/shiba/husky com Walk/Run/
Idle): **Quaternius — Ultimate Animated Animals**
<https://quaternius.itch.io/ultimate-animated-animals>

Requisitos: frente do modelo no eixo **+Z**, origem no chao, animacao com
"walk" no nome (o jogo escolhe sozinho). Ao adicionar assets de terceiros,
atualize o `CREDITS.md` com autor, URL e licenca.
