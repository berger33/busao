# Props urbanos — modelos 3D originais (Lote 7)

Todos os `.glb` desta pasta são **assets originais do projeto**, modelados por
script no Blender 4.5 headless (`tools/blender/build_lote7.py`, reutilizando o
`tools/blender/kit_base.py`). Nada aqui é baixado de terceiros; para
regenerar/aperfeiçoar qualquer peça, rode:

```
python3 tools/blender/build_lote7.py   # requer: pip install bpy==4.5.14
```

## Contrato com o jogo

- **Frente para `-Z`** no Godot (no Blender, modelado com a frente para `+Y`;
  o exportador `yup` converte `(x, y, z) -> (x, z, -y)`).
- **Origem no chão** (`y = 0` no Godot) e **escala real em metros** — o jogo
  instancia os props com escala 1:1, sem ajuste de fit.
- Materiais PBR (Principled) com cor/roughness/metallic e, onde faz sentido,
  emissive (lente do poste, teclado do orelhão, faixa refletiva do cone).

## Peças

| Arquivo        | Objeto                                                                  | Dimensões reais (L×P×A) |
|----------------|-------------------------------------------------------------------------|--------------------------|
| `cone.glb`     | Cone de sinalização com 2 faixas refletivas                             | 0,55 × 0,55 × 0,94 m     |
| `hidrante.glb` | Hidrante vermelho com bocais laterais e volante de latão                | 0,74 × 0,46 × 0,93 m     |
| `orelhao.glb`  | Orelhão: casca laranja aberta, aparelho com teclado e monofone          | 0,87 × 0,70 × 2,41 m     |
| `banco.glb`    | Banco de praça: 3 ripas de assento + 2 de encosto em pés de aço         | 1,72 × 0,57 × 1,00 m     |
| `lixeira.glb`  | Lixeira de rua: tambor verde suspenso em poste de aço                   | 0,37 × 0,54 × 1,04 m     |
| `poste.glb`    | Poste de iluminação com braço para `+X` e luminária emissiva            | 1,09 × 0,56 × 3,65 m     |
| `ponto.glb`    | Abrigo de ponto de ônibus: colunas, teto, vidros, banco e placa         | 2,74 × 1,23 × 3,21 m     |
| `carrinho.glb` | Carrinho de camelô com vitrine, rodas e toldo listrado | 1,74 × 1,23 × 2,15 m |
| `barreira.glb` | Barreira suspensa de obra: 2 postes zincados + barra listrada com vão inferior livre (deslize) | 2,44 × 0,10 × 1,90 m (barra entre 1,12 e 1,50 m) |

A `barreira.glb` (ETAPA 5) foi gerada sem bpy por `tools/glb/build_etapa5.py`
(escritor GLB em Python puro, `tools/glb/glb_writer.py`) — mesmo contrato
acima, modelada direto no espaço do Godot. Para regenerar:

```
python3 tools/glb/build_etapa5.py
```

## Integração (drop-in)

- `scripts/game_3d.gd` → `_optional_prop(...)`: obstáculos de calçada
  (`cone`, `hidrante`, `payphone`, `bench`, `vendor`), `_build_lamp` (poste)
  e `_create_bus_stop` (abrigo).
- `scripts/building_kit.gd` → `_prop_glb(...)`: banco, lixeira e hidrante dos
  quarteirões (rotação do banco alinha o assento à rua).
- Se o arquivo não existir, o builder procedural antigo continua como
  fallback de segurança (código morto enquanto os GLBs estiverem presentes).
