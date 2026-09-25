# Coletáveis — modelos 3D originais (Lote 8)

Todos os `.glb` desta pasta são **assets originais do projeto**, modelados por
script no Blender 4.5 headless (`tools/blender/build_lote8.py`, reutilizando o
`tools/blender/kit_base.py`). Nada aqui é baixado de terceiros; para regenerar
ou aperfeiçoar qualquer peça, rode:

```
python3 tools/blender/build_lote8.py   # requer: pip install bpy==4.5.14
```

## Contrato com o jogo

- **Centro do volume na origem** (`0,0,0`) em todos os eixos: o jogo instancia
  o coletável a ~1,25 m de altura e **gira o node pai em Y** continuamente
  (`_update_run`), então o pivô do giro é o próprio centro do modelo.
- **Escala real em metros** — o jogo instancia 1:1, sem fit.
- **Frente para -Y no Blender** (= +Z no Godot, virado para o corredor): as
  faces com textura/gravação (valor da moeda, bilhete, cartão, tela do PIX,
  rótulo) ficam nesse lado.
- Materiais PBR (Principled); metal com emissive discreto nos dourados e tela
  emissiva no PIX, para manter a leitura de *pickup* que o glow translúcido do
  jogo reforça por cima.

## Peças

| Arquivo       | Objeto                                                      | Dimensões (L×P×A) |
|---------------|-------------------------------------------------------------|-------------------|
| `coin.glb`    | Moeda de R$ 0,25 em pé: face "R$ 0,25", verso "BRASIL 2026" | 0,60 × 0,06 × 0,60 m |
| `golden.glb`  | Bilhete dourado "PREMIADO" com estrela                      | 0,46 × 0,05 × 0,30 m |
| `coffee.glb`  | Copo de café com tampa e faixa kraft                        | 0,37 × 0,39 × 0,37 m |
| `bread.glb`   | Pão de queijo com manchas de forno                          | 0,43 × 0,39 × 0,35 m |
| `pastel.glb`  | Pastel com borda crimpada                                   | 0,67 × 0,41 × 0,23 m |
| `sugarcane.glb`| Caldo de cana: 3 talos com nós + folhas                     | 0,27 × 0,54 × 0,20 m |
| `pass.glb`    | Vale-transporte "BUSÃO"                                     | 0,46 × 0,04 × 0,30 m |
| `coxinha.glb` | Coxinha em gota com bico                                    | 0,55 × 0,62 × 0,55 m |
| `guarana.glb` | Garrafa de guaraná com rótulo                               | 0,23 × 0,58 × 0,23 m |
| `pix.glb`     | Celular "PIX TURBO" com tela emissiva                       | 0,20 × 0,36 × 0,05 m |
| `umbrella.glb`| Guarda-chuva azul fechado                                   | 0,61 × 0,84 × 0,61 m |

## Integração (drop-in)

- `scripts/game_3d.gd` → `_build_collectible(...)`: chama `_optional_glb(
  "collectibles/<kind>.glb")`. Se o arquivo existir, ele substitui o coletável
  procedural; senão, o builder antigo continua como fallback de segurança.
- O glow translúcido (`Glow`) é adicionado nos dois caminhos para manter a
  silhueta de item coletável nas três faixas.
