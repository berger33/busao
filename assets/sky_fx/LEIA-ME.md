# Céu (sky fx) — modelos 3D originais (Lote 8)

Todos os `.glb` desta pasta são **assets originais do projeto**, modelados por
script no Blender 4.5 headless (`tools/blender/build_lote8.py`, reutilizando o
`tools/blender/kit_base.py`). Nada aqui é baixado de terceiros; para regenerar:

```
python3 tools/blender/build_lote8.py   # requer: pip install bpy==4.5.14
```

## Contrato com o jogo

- **Centro do volume na origem** (`0,0,0`): o jogo gira o node pai em Y num
  rodopio lento e contínuo (`_update_sky_fx`), então o modelo precisa girar em
  torno do próprio centro — como um avião de plástico pendurado girando.
- **Escala real em metros** — o jogo instancia 1:1, sem fit.

## Peças

| Arquivo      | Objeto                                                  | Dimensões (L×P×A) |
|--------------|---------------------------------------------------------|-------------------|
| `aviao.glb`  | Avião comercial branco: fuselagem, asa baixa, deriva azul, motores | 2,15 × 0,72 × 2,26 m |
| `drone.glb`  | Quadricóptero: corpo, 4 braços com rotores, gimbal e trens | 1,00 × 1,00 × 0,59 m |

## Integração (drop-in)

- `scripts/game_3d.gd` → `_build_aerial(...)`: chama `_optional_glb(
  "sky_fx/<kind>.glb")` para os tipos `aviao` e `drone`. Se o arquivo existir,
  ele substitui o modelo de primitivas; senão, o builder antigo continua.
- Aves (`pombo`, `passaro`, `gaivota`, `urubu`) continuam usando o
  `Animal3D` articulado — não passam por esta pasta.
