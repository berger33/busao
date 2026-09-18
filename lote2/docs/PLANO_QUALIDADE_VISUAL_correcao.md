# Correções do plano trazidas pelo Lote 2

Estas linhas devem substituir/adicionar trechos em
`docs/PLANO_QUALIDADE_VISUAL.md` e em `docs/QUALITY_AUDIT.md` quando o código
voltar para o repositório.

## 1. Lote 4: trocar PCSS por sombra suave (PCSS não existe no Mobile)

**Antes (no plano):** "PCSS no sol (`light_angular_distance`) + `shadow_blur`".

**Depois:**

> **Lote 4 – sombra do sol:** no Forward+ ligar PCSS pelo
> `DirectionalLight3D.light_angular_distance` (penumbra fisicamente maior perto
> do objeto); **no Mobile/Compatibilidade** (caminho do Honor X8b) usar
> `shadow_blur` mais alto, 4 splits com `directional_shadow_blend_splits` e
> `directional_shadow_fade_start` em 0,9, que é o que existe de fato.
> Fonte: doc do 4.7.2 em `Light3D.light_angular_distance` – "PCSS for
> directional lights is only supported in the Forward+ rendering method, not
> Mobile or Compatibility".

## 2. Matriz de recurso por renderizador (conferida no 4.7.2)

| Recurso | Forward+ | Mobile (Honor X8b) | Compatibility (plano B) |
|---|---|---|---|
| MSAA 3D | sim | sim | não |
| Escala 3D + FSR2 | sim | sim | não |
| Debanding | sim | sim | sim |
| DOF (CameraAttributesPractical) | sim | sim | não |
| Auto-exposição | sim | **não** | não |
| Ambient vindo do céu | sim | **não** (usar cor) | não |
| SSAO | sim | **não** | sim |
| SSIL / SSR / SDFGI | sim | **não** | não |
| Névoa volumétrica | sim | **não** | não |
| Glow completo | sim | reduzido | reduzido (sem `glow_strength`, `glow_blend_mode`, `glow_map`) |
| PCSS | sim | **não** | não |
| Céu físico / nuvens procedurais | sim | sim (procedural) | procedural, sem nuvens |

Consequência prática para o Lote 2: o clima precisa de **dois caminhos** — um
com ambiente do céu + auto-exposição (Forward+) e outro com cor de ambiente fixa
azulada + exposição resolvida na mão (Mobile/Compatibilidade). Os dois caminhos
existem no `render_quality.gd`.

## 3. Tone mapping: números medidos, não estimados

O `tools/audit_render_tone.py` reproduz o shader `effects/tonemap.glsl` da tag
4.7.2 (matrizes do BakingLab com bias 1.8, depois `ACES`, e em seguida
brilho/contraste/saturação aplicados **depois** da conversão para sRGB). Com os
valores do Lote 2 (brilho 1,02 / contraste 1,06 / saturação 0,94):

| Amostra | Luma na tela (0-255) |
|---|---|
| Sol no céu | 255 (croma 0 – realce sem cor, como na referência) |
| Céu perto do sol | 225 |
| Calçada ao sol | 127 (alvo da referência: 128) |
| Tijolo ao sol | 62 |
| Folhagem | 54 |
| Calçada na sombra | 36 (azulada: 31/37/45) |
| Sombra funda | 4 (nunca 0 - detalhe preservado) |
| Névoa a 60 / 140 / 260 m | 143 / 181 / 194 |

Exposição resolvida: **0,506** → arredondada para **0,51** no perfil do jogo.
Se o editor mostrar a cena clara ou escura demais, esse é o botão a girar
(`"exposure"` no perfil), e a auditoria diz para onde ele deve ir.

## 4. O que o Lote 2 NÃO resolve (fica registrado para não se perder)

- **Céu por capítulo:** o controlador monta um céu só (geral). A variação por
  capítulo entra no Lote 3, junto dos quarteirões.
- **Câmera:** os números novos (altura 2,65 m, FOV 49°/52°) precisam ser colados
  no `_update_camera()` pelo roteiro; o controlador ajusta FOV e `far`, mas não
  a posição, porque o jogo reposiciona a câmera todo quadro.
- **Personagem/efeitos:** continuam fora, Lote 6.
- **Colisões e física:** continuam fora, Lote 5.
