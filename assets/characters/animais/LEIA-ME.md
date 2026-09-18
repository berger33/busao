# Modelos de animais (drop-in)

O jogo usa o arquivo `<especie>.glb` desta pasta se ele existir
(`caramelo.glb`, `pombo.glb`); sem o arquivo, entra o modelo procedural.
Escala, assentamento no chao e animacao de caminhada (loop) sao automaticos.

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

## Como trocar por outros modelos

Substitua qualquer `<especie>.glb` por um GLB rigado com animacao de
caminhada. Fonte CC0 recomendada para cao (dog/shiba/husky com Walk/Run/
Idle): **Quaternius — Ultimate Animated Animals**
<https://quaternius.itch.io/ultimate-animated-animals>

Requisitos: frente do modelo no eixo **+Z**, origem no chao, animacao com
"walk" no nome (o jogo escolhe sozinho). Ao adicionar assets de terceiros,
atualize o `CREDITS.md` com autor, URL e licenca.
