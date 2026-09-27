# Personagem "Corre pro Ponto" — revisão 2

Personagem runner articulada (Godot 4.7.2). Substitui o pacote antigo
`personagem_runner_pacote.zip` (removido). Documentação completa em
`res://assets/characters/source/corre_pro_ponto/LEIA_ME_CORRE_PRO_PONTO.md`.

## Arquivos de runtime (usar no jogo)

- `personagem_runner.glb` — malha + esqueleto (25 ossos) + 15 clipes de animação.
- `cabelo_fisico.gd` — cabelo em tempo real (SpringBoneSimulator3D); remove os
  tracks `hair.*` das cópias locais e normaliza os nomes de clipe.
- `personagem_corre_pro_ponto.tscn` — cena pronta: instancia o GLB como `Visual`
  e adiciona o nó `CabeloFisico`.

Fontes editáveis (blend, gerador Python, prévias, mp4, validações) ficam em
`res://assets/characters/source/corre_pro_ponto/`.

## Novidades desta revisão

- **Andar pro lado enquanto corre:** `lane_left`, `lane_right` (0,8 s; troca de
  pista de 0,65 m). Versões de prévia com deslocamento: `lane_left_motion`,
  `lane_right_motion`.
- **Pulo completo:** `jump_start → jump_air → jump_fall → jump_land → run_loop`
  (blends de ~0,08–0,12 s). Prévia com deslocamento: `jump_full_motion`.
- **Agachamento:** `crouch_enter`, `crouch_loop` (parado), `crouch_run_loop`
  (agachado em movimento), `crouch_exit`.
- Base: `idle`, `run_loop`.

Os 12 clipes de jogo mantêm o root fixo (in-place); os 3 clipes `*_motion` são só
para demonstração e não devem ser combinados com o movimento do CharacterBody3D.

## Integração rápida

Instancie `personagem_corre_pro_ponto.tscn` como visual do seu
`CharacterBody3D`. Escala 1,1,1. Frente local **+Z**: se o controlador avança em
**-Z**, gire o nó visual 180° no eixo Y. O `cabelo_fisico.gd` se configura em
`_ready`; chame `reset_after_teleport()` ao reposicionar a personagem.

## Integração já feita no runner (Lote 29)

`scripts/runner_character.gd` já sabe usar esta cena:

- **Ativar:** edite a constante `CORRE_PRO_PONTO_FOR_IDS` e liste os ids de
  personagem que devem virar o runner v2 — ex.: `["julia"]`. Vazio (padrão) =
  nada muda, o pipeline por personagem continua igual.
- **Animações:** o controlador usa nomes semânticos (`Sprint_Loop`, `Jump_Loop`,
  `Crouch_Fwd_Loop`, `Crouch_Idle_Loop`...) mapeados para os clipes deste rig via
  `CORRE_PRO_PONTO_CLIP_ALIASES` (`run_loop`, `jump_air`, `crouch_run_loop`,
  `crouch_loop`...). O mapa só é consultado quando o clipe direto não existe, ou
  seja, não afeta os outros rigs.
- **Rotação/cabelo:** a rotação de 180° (`MODEL_FACING_YAW`) e o cabelo em tempo
  real já são aplicados pelo fluxo existente.

> O sandbox não tem Godot instalado, então esta parte não foi testada em runtime.
> Abra no editor Godot 4.7.2, defina `CORRE_PRO_PONTO_FOR_IDS` e valide a cena.
