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

`scripts/runner_character.gd` já usa esta cena como visual ativo da heroína:

- **Personagem ativa:** `CORRE_PRO_PONTO_FOR_IDS = ["julia"]`. A antiga
  `hero_julia.glb` foi removida porque esta v2 é a versão melhorada.
- **Textura/cor:** o runtime liga `vertex_color_use_as_albedo`; sem isso o GLB
  fica branco, pois pele/roupa/cabelo vêm de `COLOR_0` multiplicado por texturas
  claras de detalhe.
- **Sem contorno preto:** o filete `SilhouetteShell` dos personagens antigos é
  pulado para esta v2.
- **Idle no início/carregamento:** o runner começa em `idle` e só entra em
  `run_loop` quando o jogo está em `playing`.
- **Animações:** o controlador usa nomes semânticos (`Sprint_Loop`, `Jump_Loop`,
  `Crouch_Fwd_Loop`, `Crouch_Idle_Loop`...) mapeados para os clipes deste rig via
  `CORRE_PRO_PONTO_CLIP_ALIASES` (`run_loop`, `jump_air`, `crouch_run_loop`,
  `crouch_loop`...). O mapa só é consultado quando o clipe direto não existe, ou
  seja, não afeta os outros rigs.
- **Troca de pista:** `game_3d._change_lane()` chama
  `runner_character.on_lane_change(direction)`, que toca `lane_left` ou
  `lane_right` durante a corrida e depois volta ao `run_loop`.
- **Cadência da corrida:** a v2 usa referência própria
  `CORRE_PRO_PONTO_RUN_SPEED = 2.0588235294117645` e teto
  `CORRE_PRO_PONTO_MAX_PLAYBACK = 2.6`, reduzindo o deslizamento dos pés em
  relação ao valor antigo global de 4 m/s.
- **Rotação/cabelo:** a rotação de 180° (`MODEL_FACING_YAW`) e o cabelo em tempo
  real já são aplicados pelo fluxo existente.

> O sandbox não tem Godot instalado, então a validação aqui é estática/offline.
> Abra no editor Godot 4.7.2 e valide visualmente troca de pista, velocidade,
> pulo, agachamento e cabelo.
