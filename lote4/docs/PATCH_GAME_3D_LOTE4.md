# Lote 4 — como ligar o clima no seu jogo (game_3d.gd)

> Assume **Lote 2** (controlador de render) e **Lote 3** (rua do `building_kit`) já aplicados.
> São **3 colagens** e **3 chamadas**. Uns 10 minutos.

## Antes de começar

Copie do pacote para o projeto:

| Do pacote | Para o projeto |
| --- | --- |
| `scripts/weather_system.gd` | pasta `scripts/` |
| `resources/weather_spec.json` | pasta `resources/` |
| `assets/textures/ceu/nuvens.png` | `assets/textures/ceu/` (crie a pasta) |
| `assets/audio/trovao.wav` | `assets/audio/` |

O Godot importa a imagem e o som sozinho ao abrir o projeto (não precisa fazer nada).

---

## Colagem 1 de 3 — constante

No topo do `game_3d.gd`, junto das outras constantes:

```gdscript
# --- Lote 4: clima -------------------------------------------------------
const CLIMA_ATIVO := true      # false desliga chuva/relampago/molhado
```

## Colagem 2 de 3 — variável

Junto das outras variáveis:

```gdscript
# --- Lote 4 --------------------------------------------------------------
var _clima: WeatherSystem = null
```

## Colagem 3 de 3 — funções

```gdscript
# --- Lote 4: clima -------------------------------------------------------
func _setup_clima() -> void:
	if not CLIMA_ATIVO:
		return
	var clima := WeatherSystem.new()
	clima.name = "Clima"
	add_child(clima)
	# usa o mesmo perfil que o RenderQuality recebe (Lote 2) e o mesmo
	# deslocamento do piso do kit (Lote 3)
	clima.setup(_render_profile(), WORLD_Y_OFFSET)
	_clima = clima

func _update_clima(delta: float) -> void:
	if _clima == null:
		return
	_clima.update_head(_world_travel)

func _trocar_clima_do_capitulo(indice: int) -> void:
	if _clima != null:
		_clima.set_chapter(indice)
```

> Se você **não** usa o Lote 3, troque `WORLD_Y_OFFSET` por `0.0` nessa chamada.

---

## As 3 chamadas

1. No **final do `_ready()`**, depois de `_setup_world_kit()`:

```gdscript
	_setup_clima()
```

2. Dentro do `_process(delta)`, depois de `_update_world_kit(delta)`:

```gdscript
	_update_clima(delta)
```

3. Onde o jogo troca de capítulo (o mesmo lugar em que o cenário é refeito):

```gdscript
	_trocar_clima_do_capitulo(0)   # troque 0 pelo índice do capítulo
```

---

## Como testar cada clima na hora (sem esperar capítulo)

Depois de `_setup_clima()`, chame o estado que quiser:

```gdscript
	_clima.set_state("limpo")       # sol, sem chuva, chão seco
	_clima.set_state("nublado")     # nublado, ainda seco
	_clima.set_state("chuva")       # chuva, asfalto brilhando, poças
	_clima.set_state("tempestade")  # chuva forte + relâmpagos + trovão
```

A troca é suave (uns 5 segundos), e o chão **demora bem mais para secar** do que
para molhar — de propósito, como na vida real.

---

## O que deve acontecer

| Estado | O que você vê |
| --- | --- |
| `limpo` | sol quente, chão fosco, sem nuvens |
| `nublado` | luz mais fria, céu encoberto, névoa um pouco maior |
| `chuva` | pingos descendo, asfalto escuro e brilhando, poças nas pistas, céu carregado |
| `tempestade` | tudo acima + piscadas de relâmpago, véu branco rápido e **trovão** (áudio) |

No painel **Saída** aparece:

```
[clima] sistema pronto | metodo=mobile | estados=limpo,nublado,chuva,tempestade
[clima] bases: sol=1.10 nevoa=0.50 ambiente=0.62 nuvens=0.30
[clima] estado=tempestade molhado_alvo=1.00 chuva=1150
```

---

## Se algo estiver errado

| Sintoma | O que ajustar |
| --- | --- |
| Chuva não aparece | a chuva segue a câmera: confira se a `Camera3D` existe e está ativa |
| Travando na chuva | `weather_spec.json` → `chuva.estados.tempestade.quantidade` (baixe para ~800) |
| Poças no lugar errado | `weather_spec.json` → `pocas.tamanho_m` / `afastamento_guia_m` |
| Relâmpago fraco | `relampago.energia_pico` (faixa 1.2 a 4.0) |
| Sem som de trovão | confira se `assets/audio/trovao.wav` entrou no projeto (o Godot importa ao abrir) |
| Chão não seca | `transicoes.secagem_s` (hoje 16 s) |

Qualquer mudança nesses números **não precisa mexer no código**: é só editar o
`weather_spec.json` e rodar de novo.

---

## O que me mandar de volta

1. Print de cada clima (ou pelo menos `chuva` e `tempestade`);
2. Painel **Saída** com as linhas `[clima]`;
3. No Honor X8b: se travou, quando travou (qual clima) e se esquentou.
