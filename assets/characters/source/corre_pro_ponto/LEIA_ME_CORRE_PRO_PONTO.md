# Corre pro Ponto — personagem articulada, revisão 2

Preparada para Godot **4.7.2**. O pacote contém o Blender editável, GLB com 15 clipes, código Python gerador, cena de integração Godot, cabelo com simulação em tempo real, prévias e relatórios de validação.

## Usar no Blender

Abra `personagem_runner.blend` e pressione Espaço sobre a Timeline. A ação `DEMO_todas_animacoes_NAO_EXPORTAR` mostra corrida, salto, agachamento e mudanças de pista em sequência. Há marcadores na Timeline. A demonstração existe apenas no Blender; não foi incluída no GLB.

Os 15 clipes individuais estão no Action Editor e em trilhas NLA separadas. Para editar uma ação, selecione `RunnerRig`, escolha a ação e mantenha as outras trilhas NLA mudas. Se precisar inspecionar os ossos, ative Pose Mode.

Para recriar a personagem: **Scripting → Open → criar_personagem_corre_pro_ponto.py → Run Script / Alt+P**. Usa o Python do Blender, sem add-ons. A geração cria uma nova cena e uma pasta de saída própria; não substitui a pasta existente. O gerador foi executado no Blender 5.2.2 LTS.

## Adicionar ao Godot

Copie **estes três arquivos juntos, na mesma pasta do projeto**:

- `personagem_runner.glb`
- `cabelo_fisico.gd`
- `personagem_corre_pro_ponto.tscn`

Instancie `personagem_corre_pro_ponto.tscn` como o visual do `CharacterBody3D` já usado no Corre pro Ponto. A cena não substitui seu controlador, colisão, câmera, obstáculos ou sistema de pistas. O cabelo é configurado em `_ready`, durante a execução.

Mantenha escala 1,1,1. O modelo tem frente local **+Z** no Godot; se o controlador avança em **-Z**, gire o nó visual 180° no eixo Y. Os nomes esquerda/direita seguem o lado da própria personagem: sem essa rotação, esquerda local é +X e direita local é -X. Depois da rotação de 180°, direita corresponde ao +X do controlador.

O script encontra o Skeleton3D e o AnimationPlayer dentro da cena. Ele clona as bibliotecas de animação somente para essa instância, preserva o GLB original, normaliza os nomes `run`, `crouch` e `crouch_run` que o importador pode produzir e ativa a repetição dos clipes cíclicos. Use os nomes abaixo no AnimationPlayer/AnimationTree após a configuração.

## Clipes disponíveis

| Nome | Duração | Uso |
|---|---:|---|
| `idle` | 2 s | Repouso, cíclico |
| `run_loop` | 0,8 s | Corrida, cíclica |
| `jump_start` | 0,2 s | Preparação e impulso |
| `jump_air` | 0,6 s | Pose no ar, cíclica |
| `jump_fall` | 0,2 s | Estende as pernas antes do contato |
| `jump_land` | 0,3 s | Absorve impacto e retorna à corrida |
| `crouch_enter` | 0,3 s | Abaixa o corpo |
| `crouch_loop` | 1,2 s | Mantém agachada e parada |
| `crouch_run_loop` | 0,8 s | Passadas curtas com o corpo abaixado |
| `crouch_exit` | 0,3 s | Levanta e retorna à corrida |
| `lane_left` | 0,8 s | Passada diagonal para esquerda/frente |
| `lane_right` | 0,8 s | Passada diagonal para direita/frente |
| `jump_full_motion` | 1,2 s | Demonstração do salto completo com deslocamento vertical |
| `lane_left_motion` | 0,8 s | Demonstração com deslocamento lateral de 0,65 m |
| `lane_right_motion` | 0,8 s | Demonstração com deslocamento lateral de 0,65 m |

**Os 12 clipes de jogo mantêm o root fixo.** Seu controlador aplica velocidade, gravidade e deslocamento entre pistas. Os três clipes terminados em `_motion` incluem deslocamento do root para visualização; não os combine com o mesmo movimento aplicado novamente pelo CharacterBody3D.

Para o salto durante o jogo, a sequência é `jump_start → jump_air → jump_fall → jump_land → run_loop`. Faça as transições conforme a velocidade vertical e o contato com o chão. Use blends curtos, aproximadamente 0,08–0,12 s. A demonstração considera gravidade de 9,81 m/s², voo de 0,72 s e altura máxima do root de aproximadamente 0,636 m; no jogo, esses valores pertencem ao controlador.

Para agachar, use `crouch_enter`, depois `crouch_loop` se estiver parada ou `crouch_run_loop` se continuar andando, e termine com `crouch_exit`. Ajuste também o colisor do CharacterBody3D e verifique espaço acima antes de levantar. O mesh e a animação não redimensionam a colisão do seu jogo automaticamente.

Para mudar de pista, toque `lane_left` ou `lane_right` enquanto seu controlador interpola a posição lateral e mantém o avanço. A largura de referência é 0,65 m em 0,8 s. Ajuste duração e deslocamento em conjunto se suas pistas tiverem outra largura.

A corrida foi calibrada para cerca de **2,06 m/s** e o deslocamento agachado para **0,71 m/s**. Sincronize velocidade e reprodução para evitar pés deslizando. Aumentar muito a velocidade exige retimar ou reanimar a passada.

## Movimento do rabo de cavalo

No `.blend` e no GLB puro, os três ossos do rabo de cavalo têm animação calculada por um solver PBD a 120 Hz, gravada em keyframes a 30 fps. O cálculo usa gravidade, inércia, arrasto, comprimentos fixos e colisores aproximados da cabeça e tronco. Cada clipe possui seu próprio movimento de cabelo.

Na cena `.tscn`, `cabelo_fisico.gd` remove **somente os tracks de `hair.01`, `hair.02` e `hair.03` das cópias locais das animações** e cria um `SpringBoneSimulator3D` com três colisores. Assim o cabelo reage ao movimento real do corpo, saltos e mudanças de pista, sem somar a animação gravada a uma segunda simulação.

Os parâmetros de rigidez, amortecimento e gravidade do spring ficam exportados no Inspector. O parâmetro de gravidade desse recurso do Godot não representa diretamente m/s²; não substitua o valor por 9,81 supondo equivalência. Chame `reset_after_teleport()` no nó `CabeloFisico` ao reposicionar a personagem instantaneamente.

É uma **aproximação física para jogos**, não uma simulação de cada fio. As colisões configuradas são com cabeça e tronco. Colisão do cabelo com paredes/objetos externos precisa ser configurada no projeto; os colisores de spring não utilizam automaticamente todos os corpos do PhysicsServer3D.

Referência da API: [SpringBoneSimulator3D](https://docs.godotengine.org/en/stable/classes/class_springbonesimulator3d.html).

## O que foi revisado e testado

- Esqueleto de 25 ossos com pesos normalizados e, no máximo, duas influências por vértice neste modelo.
- Flexão de pernas por IK calculado e convertido em keyframes; braços contralaterais na corrida, quadril/tronco coordenados e poses de equilíbrio.
- Contatos dos pés nas transições de agachamento e impulso corrigidos; pesos do short ajustados para evitar os atravessamentos observados nas prévias.
- Reimportação do GLB, presença dos 15 clipes, movimento do corpo e cabelo, continuidade dos ciclos, limites de flexão, altura do salto e sentidos dos deslocamentos.
- Execução isolada no Godot 4.7.2: importação, reprodução de clipes e física do cabelo sem erros nos testes registrados.

O modelo possui **18.688 triângulos, três materiais e texturas de 512×512**. Os relatórios `validacao_blender.json` e `validacao_godot.json` registram os testes. Ainda não foi integrado ao projeto Corre pro Ponto nem medido em Android. Novas velocidades, outros colliders e poses fora destes clipes exigem validação na cena real.

O visual continua sendo a base estilizada/procedural da primeira versão. Esta revisão trata principalmente de articulação, animações, deformações e física do cabelo; não transforma o acabamento visual em uma produção no nível de GTA IV.
