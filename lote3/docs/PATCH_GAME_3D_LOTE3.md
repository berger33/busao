# Lote 3 — como ligar a rua nova no seu jogo (game_3d.gd)

> Este roteiro assume que o **Lote 2 já está aplicado** (arquivo `scripts/render_quality.gd`,
> autoload `RenderQuality` no `project.godot` e o `_render_profile()` colado no `game_3d.gd`).
> Se ainda não aplicou, aplique primeiro o pacote do Lote 2.

São **4 colagens** e **1 chamada**. Tempo: uns 10 minutos.

---

## Antes de começar

1. Copie o arquivo **`scripts/building_kit.gd`** (do pacote do Lote 3) para a pasta
   **`scripts/`** do projeto, ao lado do `game_3d.gd`.
2. Copie a pasta **`resources/`** do pacote para a raiz do projeto (o arquivo
   `resources/world_spec.json` é a "planta" da rua — é ele que o kit lê).
3. Abra o projeto no Godot 4.7.2. Se aparecer erro vermelho no
   `building_kit.gd`, me mande o texto do painel **Saída** (Output).

---

## Colagem 1 de 4 — constantes

No topo do `game_3d.gd`, junto das outras constantes (`const CAMERA_...`),
cole este bloco:

```gdscript
# --- Lote 3: rua construida pelo building_kit.gd -------------------------
const WORLD_KIT_ATIVO := true          # false desliga a rua nova
const WORLD_Y_OFFSET := -0.15          # deixa a calcada no nivel do chao do jogo
const WORLD_INVERTER := false          # true se a rua aparecer virada (correndo ao contrario)
const WORLD_SPEED_PADRAO := 18.0       # so para reciclar o quarteirao na hora certa
```

**`WORLD_SPEED_PADRAO`**: troque pelo valor de velocidade do seu jogo, se você já
tem uma variável com isso (a mesma que move o cenário). Não é crítico: serve
apenas para o quarteirão ser reciclado quando sai de vista.

---

## Colagem 2 de 4 — variáveis

Junto das outras variáveis (`var ...` no meio do arquivo), cole:

```gdscript
# --- Lote 3 -------------------------------------------------------------
var _world_kit: Node3D = null
var _world_travel := 0.0
var _world_last_head := 0.0
```

---

## Colagem 3 de 4 — funções novas

Cole estas três funções junto das outras funções do `game_3d.gd`:

```gdscript
# --- Lote 3: rua --------------------------------------------------------
func _setup_world_kit() -> void:
	if not WORLD_KIT_ATIVO:
		return
	var kit := BuildingKit.ChunkStreamer.new()
	kit.name = "CenarioRua"
	kit.position = Vector3(0.0, WORLD_Y_OFFSET, 0.0)
	kit.rotation.y = PI if WORLD_INVERTER else 0.0
	add_child(kit)
	kit.setup()
	_world_kit = kit

func _update_world_kit(delta: float) -> void:
	if _world_kit == null:
		return
	# TODO: se o seu jogo ja tem a distancia percorrida numa variavel, use ela
	# aqui no lugar do calculo por tempo (fica mais preciso).
	_world_travel += WORLD_SPEED_PADRAO * delta
	if _world_travel - _world_last_head < 1.0:
		return
	_world_last_head = _world_travel
	_world_kit.update_head(_world_travel)

func _render_profile_world() -> Dictionary:
	# Paleta do capitulo vinda do world_spec.json (a mesma que o kit usa).
	var spec := BuildingKit.load_spec()
	return BuildingKit.chapter_profile(spec, run_level if "run_level" in self else 0)
```

> Se a última linha do `_render_profile_world()` der erro por causa do nome
> `run_level`, troque por `0` (ou pelo nome da sua variável de capítulo/fase).

---

## Colagem 4 de 4 — chamadas no lugar certo

### 4.1 — ao montar o mundo

No **final** da função `_ready()` (depois de montar câmera, luz e cenário), cole:

```gdscript
	_setup_world_kit()
```

### 4.2 — a cada quadro

Dentro do `_process(delta)`, **depois** da linha que move o cenário/curso, cole:

```gdscript
	_update_world_kit(delta)
```

### 4.3 — quando troca de capítulo

No ponto em que o jogo **reconstrói o mundo** (troca de capítulo/fase,
geralmente junto do código que recria o `course_root` ou chama o `_setup_world()`),
cole:

```gdscript
	_update_world_kit(0.0)
```

e, se o seu jogo tiver `_render_profile()` (do Lote 2), troque o corpo dele por:

```gdscript
	return _render_profile_world()
```

---

## Desligar o cenário antigo (recomendado)

O kit desenha a rua inteira. Se o cenário antigo (o que o jogo criava sozinho)
ficar por cima, procure a função que monta a pista antiga (`_build_track()` ou
parecido) e faça ela parar logo no começo:

```gdscript
func _build_track() -> void:
	return  # Lote 3: a rua agora vem do building_kit
```

Isso é seguro: o kit não mexe nos obstáculos/entidades do jogo, só no cenário
(piso, guias, pistas, calçadas, prédios, árvores, postes, folhas e horizonte).

---

## O que deve aparecer na tela

- **Faixa central** de lajes cinza-claro com folhinhas espalhadas;
- **guias** (degrau de 15 cm) dos dois lados, com **postes** finos ao longo;
- **pistas escuras** com **linha amarela dupla** junto de cada guia;
- **calçadas** com piso quadriculado, **árvores** e, na direita, **esferas verdes**;
- **prédios de 2 a 3 andares**: tijolo vermelho, reboco claro, algumas lojas com toldo;
- lá longe, um **horizonte lavado pela névoa**, com caixa d'água em alguns blocos.

### Se algo estiver errado

| Sintoma | O que ajustar |
| --- | --- |
| Personagem afundado ou flutuando | `WORLD_Y_OFFSET` (comece com −0.15 e vá de 0.05 em 0.05) |
| A rua corre ao contrário | `WORLD_INVERTER = true` |
| Cenário antigo aparecendo junto | faça o `_build_track()` antigo retornar logo no início |
| Tudo quadrado/cinza, sem textura | o Lote 1 (texturas PBR) não foi aplicado: veja `assets/textures/pbr/` |
| Travando no celular | mande a linha `[render] ...` e as medições do painel Saída |

---

## O que me mandar de volta

1. Um **print** da tela correndo (a rua nova);
2. O texto do painel **Saída** (Output) — principalmente as linhas que começam
   com `[world] quarteirao`, `[render]` e `[medicao]`;
3. O modelo do celular (já sei: Honor X8b) e se travou ou esquentou.
