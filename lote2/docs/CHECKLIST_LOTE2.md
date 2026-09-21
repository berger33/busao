# Lote 2 - o que fazer no seu PC (passo a passo)

Este pacote muda **como o jogo desenha a cena**: renderizador Mobile com plano B,
céu com sol baixo, névoa clara, tone mapping ACES, sombra suave, câmera mais
baixa e degraus de qualidade que se ajustam sozinhos no Honor X8b.

Tempo: uns 15 minutos. Não precisa saber programar - é copiar e colar.

---

## 1. Descompacte o pacote

Baixe `lote2_pacote.zip` e extraia. Você vai ver estas pastas:

- `scripts/` → `render_quality.gd` (arquivo novo) e `game_3d_lote2_patch.gd` (roteiro de colagem)
- `tools/` → os auditores (não precisam ir para o jogo)
- `docs/` → este checklist, o preview e a correção do plano
- `project.godot.lote2` → as linhas que você vai colar no `project.godot`

## 2. Copie o arquivo novo para o projeto

1. Abra a pasta do seu projeto (a que tem `project.godot`).
2. Copie `scripts/render_quality.gd` para dentro da pasta `scripts/` do projeto.

## 3. Ajuste o `project.godot`

1. Faça um **backup** do `project.godot` (copie e cole com outro nome).
2. Abra `project.godot` com o Bloco de Notas e o `project.godot.lote2` do pacote.
3. Cole a seção `[autoload]` inteira (se já existir uma, cole só a linha
   `RenderQuality="*res://scripts/render_quality.gd"` dentro dela).
4. Dentro da seção `[rendering]`, ajuste/cole as chaves:
   - `renderer/rendering_method="mobile"`
   - `renderer/rendering_method.mobile="gl_compatibility"`
   - `anti_aliasing/quality/msaa_3d=1`
   - `anti_aliasing/quality/use_debanding=true`
   - `anti_aliasing/quality/screen_space_aa=0`
   - `lights_and_shadows/directional_shadow/size=2048`
5. Salve e abra o projeto no Godot (ele reescreve o arquivo na ordem dele - normal).

## 4. Ajuste o `scripts/game_3d.gd`

Abra o `game_3d_lote2_patch.gd` do pacote: ele diz exatamente onde cada coisa
entra. São 4 blocos:

- **Bloco 1** – 6 linhas de constantes: cole junto das outras constantes do topo.
- **Bloco 2** – duas funções (`_render_profile` e `_apply_render_quality`): cole
  no fim do arquivo.
- **Bloco 3** – **uma linha** no fim do `_ready()`:
  `_apply_render_quality()`.
- **Bloco 4** – trocar os números fixos da câmera no `_update_camera()`:
  altura 4.85 → `RENDER_CAMERA_Y`, profundidade 9.4 → `RENDER_CAMERA_Z`,
  FOV 59 → `RENDER_FOV` (e 64/69 → `RENDER_FOV_RUN`), `far` 125 → `RENDER_CAMERA_FAR`.

Salve. Se aparecer aviso em vermelho, é sinal de que um pedaço ficou pela metade -
me mande o texto que eu digo o que falta.

## 5. Rode o jogo (F5)

No painel **Saída (Output)** do Godot deve aparecer uma linha assim:

```
[render] metodo=mobile adaptador='...' api=... degrau=mobile-alto
[render] pronto: mobile-alto escala 0.95 luminancia min 0.xxx
```

O que você deve ver na tela:

- sol baixo, quase de frente, com o céu claro em volta;
- névoa clara no fim da rua (o fundo "some" no creme, como na referência);
- sombra do corredor longa e com borda suave (não mais dura);
- câmera mais baixa, com o personagem ocupando mais a tela e o céu aparecendo em cima.

## 6. Testar no Honor X8b

1. No Godot: **Projeto > Exportar** e exporte o APK (Android).
2. Instale e abra. O aparelho vai usar Vulkan (renderizador Mobile).
3. Se por algum motivo o Vulkan não iniciar, o Godot cai sozinho para OpenGL e o
   `render_quality.gd` ajusta o resto - o jogo não fica preto.
4. Deixe rodando 1 minuto: o FPS decide os degraus. Se cair abaixo de 52 fps por
   alguns quadros, ele **baixa** a escala (0,95 → 0,85 → 0,75 → 0,68) e desliga
   MSAA/DOF; com 5 segundos estáveis acima de 58 fps, ele **sobe** de volta.

## 7. O que me mandar de volta

1. Um print da tela do jogo rodando (no PC ou no celular).
2. O texto do painel **Saída** do Godot (as linhas `[render] ...`).
3. Se aparecer erro: copie a mensagem inteira em vermelho.

Com isso eu sei exatamente em que degrau o seu aparelho ficou e o que ajustar no
Lote 3 (ruas, quarteirões e horizonte).

---

### Dúvida comum

**"Mudei para `mobile` e o jogo ficou diferente no PC."** Era o esperado: o PC
também passa a usar o caminho Mobile, que é o mesmo do seu celular. Assim você
testa no PC o que vai ver no aparelho. Se quiser voltar atrás, o backup do
`project.godot` resolve.
