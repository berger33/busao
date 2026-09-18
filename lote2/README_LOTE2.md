# Lote 2 - renderizador, céu, luz e câmera

Pacote pronto para entrar no projeto. Foi escrito longe do repositório (o
ambiente desta sessão perdeu o acesso ao clone completo), então ele vem como
**conjunto de arquivos + roteiro de colagem**, e não como commit direto.

## Conteúdo

| Arquivo | Papel |
|---|---|
| `scripts/render_quality.gd` | Autoload "RenderQuality": escolhe o caminho de cada renderizador, monta céu/clima/sol/câmera, mede o quadro e troca de degrau por FPS. ~527 linhas. |
| `scripts/game_3d_lote2_patch.gd` | Roteiro com os blocos que entram no `game_3d.gd` (constantes, perfil de clima, chamada e números da câmera). |
| `project.godot.lote2` | Linhas de `project.godot`: renderizador mobile + plano B, MSAA 2x, debanding, sombra 2048 e o autoload. |
| `tools/render_facts.json` | Fatos do Godot 4.7.2 (membros/constantes conferidos) + matriz de recurso por renderizador + o que ainda falta conferir. |
| `tools/analyze_render_profile.py` | Auditor: confere o código contra os fatos e contra as regras do plano (guarda de Forward+, paleta, exigências). |
| `tools/check_def_use.py` | Confere nomes: membro sem `var/const` e função chamada que não existe. |
| `tools/audit_render_tone.py` | Auditoria de tom: reproduz o tone mapping do Godot (ACES + BCS), resolve a exposição e confere as faixas da referência; desenha o preview. |
| `tools/run_lote2_selftest.py` | Prova que os auditores pegam defeito de verdade (4 erros plantados + 2 nomes errados + 1 sintaxe quebrada). |
| `tests/fixtures/` | Os arquivos com defeito plantado usados pelo autoteste. |
| `docs/CHECKLIST_LOTE2.md` | Passo a passo para aplicar e testar no PC e no Honor X8b. |
| `docs/preview_render_lote2.png` | Preview: curva de tom, paleta resultante, rampa de névoa e degraus. |
| `docs/render_tone_report.json` | A exposição que a auditoria resolveu (0,506) para uso no perfil. |
| `docs/PLANO_QUALIDADE_VISUAL_correcao.md` | Correção a aplicar no plano (PCSS não existe no Mobile) e os recursos que ficam de fora. |

## Decisões (com o motivo)

1. **Renderizador `mobile` com plano B automático.** No Honor X8b (Adreno 610,
   Vulkan 1.1) o caminho Mobile é o recomendado. `renderer/rendering_method.mobile
   = "gl_compatibility"` deixa o Godot cair para OpenGL se o Vulkan não iniciar.
2. **Nada de exclusividade sem guarda.** O código pergunta em tempo de execução
   (`RenderingServer.get_current_rendering_method()`) e só liga o que existe:
   PCSS, auto-exposição e ambiente-do-céu são exclusivos do Forward+; SSAO, SSIL,
   SSR, SDFGI e névoa volumétrica não existem no Mobile; glow tem versão reduzida
   na Compatibilidade; DOF existe em Forward+ e Mobile; MSAA/escala 3D/FSR2 não
   existem na Compatibilidade.
3. **Céu físico só no Forward+.** No Mobile/Compatibilidade o céu vira Procedural
   Sky com nuvens (`sky_cover`), que dá o mesmo degradê claro no horizonte.
4. **Sombra suave sem PCSS.** `shadow_blur` + 4 splits + bias/normal bias baixos.
5. **Câmera e FOV vêm da referência.** Altura 2,65 m (era 4,85), FOV base 49°
   (era 59°) e FOV de corrida 52° (era 64-69°); `far` de 380 m para a serra e o
   horizonte entrarem. Em retrato o `KEEP_WIDTH` faz o FOV valer na horizontal.
6. **Exposição resolvida por conta, não por chute.** A auditoria de tom aplica o
   tone mapping real do 4.7.2 (matrizes do BakingLab com bias 1.8 + ACES, depois
   brilho/contraste/saturação **em sRGB**, como no `tonemap.glsl`) e resolve a
   exposição que põe a calçada ao sol em 127/255 - o cinza médio da referência.
   Resultado: `exposure = 0,51`.
7. **Degraus com histerese.** Queda só depois de 15 quadros abaixo de 52 fps;
   subida só depois de 300 quadros (5 s) acima de 58 fps, com 150 quadros de
   respiro entre trocas - o quadro não fica "piscando" de qualidade.
8. **Prova numérica do quadro.** Depois de aplicar, o controlador lê o viewport e
   imprime a menor luminância e a fração de pixels estourados (amostragem de
   ~20 mil pontos), e sobe o ambiente se a cena ficar escura demais. É também a
   defesa contra a troca de cena do Lote 3: uma conexão em `node_added`
   reaplica o clima quando o mundo é refeito.

## Portões (rodar antes de commitar)

```bash
python3 tools/analyze_render_profile.py     # 0 problema(s), 0 aviso(s)
python3 tools/check_def_use.py scripts/render_quality.gd
python3 tools/run_lote2_selftest.py         # 0 falha(s)
pip install pillow                          # necessario para o preview
python3 tools/audit_render_tone.py          # 0 problema(s)
```

`gdtoolkit` (parser do GDScript) é usado no autoteste para provar que os dois
scripts são sintaticamente válidos em GDScript 2.0.

## O que ainda fica para os próximos lotes

- **Lote 3**: ruas/quarteirões/horizonte com os materiais PBR do Lote 1,
  `building_kit.gd`, e o céu por capítulo (hoje o controlador cuida do céu geral).
- **Lote 4**: clima e chuva (asfalto molhado), com a linha do PCSS reescrita.
- **Lote 5**: física de verdade no jogador (`CharacterBody3D` + `ShapeCast3D`).
- **Lote 6**: efeitos, personagem com PBR e modo captura.
