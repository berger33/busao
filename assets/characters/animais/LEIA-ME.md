# Modelos de animais opcionais (drop-in)

Esta pasta aceita modelos **GLB** que substituem automaticamente os animais
procedurais do jogo. O arquivo existe? Ele entra; não existe? O jogo segue com
o modelo procedural. Nada quebra.

## Nomes reconhecidos

| Arquivo       | Substitui                        | Observação |
| ------------- | -------------------------------- | ---------- |
| `caramelo.glb` | o cachorro caramelo (obstáculo) | toca a 1ª animação com "walk" no nome, em loop |
| `pombo.glb`    | os pombos do chão               | idem |

O jogo escala o modelo para ~0,95 m de comprimento e o assenta no chão.

## Onde baixar (CC0, uso comercial livre)

- **Quaternius — Ultimate Animated Animals** (cachorro, raposa, galinha etc.
  rigados, com Walk/Run/Idle): <https://quaternius.itch.io/ultimate-animated-animals>
  — licença CC0. Baixe o pack, pegue o `.glb` do cão, renomeie para
  `caramelo.glb` e solte aqui.
- **Khronos glTF-Sample-Assets** — `Fox.glb` (CC0, animada) e `Boxer.glb`
  (Apple, CC-BY 4.0 — credite no `CREDITS.md`):
  <https://github.com/KhronosGroup/glTF-Sample-Assets>

Ao adicionar um modelo de terceiros, atualize o `CREDITS.md` com autor, URL e
licença (obrigatório para CC-BY; CC0 dispensa, mas é boa prática).
