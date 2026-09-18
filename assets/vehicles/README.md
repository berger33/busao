# Modelos de veículos opcionais (drop-in)

Esta pasta aceita modelos **GLB/glTF** que substituem automaticamente os veículos
procedurais do jogo. Se o arquivo existir, ele é usado; se não, o jogo continua
com os veículos construídos em código (nada quebra).

## Nomes reconhecidos

| Arquivo                 | Substitui                          | Ajuste automático     |
| ----------------------- | ---------------------------------- | --------------------- |
| `onibus.glb`            | O ônibus do ponto (objetivo final) | 8,2 m × 3,0 m         |
| `carro.glb`             | Carros estacionados (decoração)    | 4,4 m × 1,55 m        |
| `car.glb`               | Obstáculo "car" (trânsito)         | 4,4 m × 1,55 m        |
| `motorcycle.glb`        | Obstáculo "motorcycle"             | 2,1 m × 1,15 m        |
| `truck.glb`             | Obstáculo "truck"                  | 6,4 m × 2,7 m         |
| `bus_traffic.glb`       | Obstáculo "bus_traffic"            | 7,4 m × 3,0 m         |

O jogo escala o modelo para o tamanho-alvo e o assenta no chão automaticamente.
O modelo deve estar orientado com o comprimento no eixo **Z** e virado para **-Z**
(o mesmo padrão dos veículos procedurais).

## Onde baixar com licença aberta (uso comercial OK)

Todas as fontes abaixo permitem monetização (anúncios e compras no app):

- **Quaternius** — <https://quaternius.com/packs/ultimatedesktop.html> e
  <https://quaternius.itch.io/> (packs *Cars*, *Public Transport*, *Animated
  Vehicles*). Licença **CC0** — sem necessidade de crédito. FBX + GLB.
- **Poly Haven** — <https://polyhaven.com/models> (inclusive pneus e carros
  cobertos). Licença **CC0**. GLTF/FBX/Blend.
- **Kenney** — <https://kenney.nl/assets> (*Car Kit*, *City Kit*). **CC0**.
- **ambientCG** — <https://ambientcg.com> (texturas PBR e HDRIs, não modelos).
  **CC0**.
- **Poly Pizza** — <https://poly.pizza> (buscador de modelos CC0/CC-BY; confira
  a licença de cada modelo antes de usar).

Ao adicionar um modelo, atualize o `CREDITS.md` com autor, URL e licença
(exigência apenas para CC-BY; CC0 dispensa, mas é boa prática).

## Regras de licença na prática

- **CC0**: domínio público — use, modifique e monetize sem crédito.
- **CC-BY**: comercial OK, **crédito obrigatório** (nome do autor + link).
- **CC-BY-NC / Editorial**: **proibido** em jogo monetizado.
- Downloads do Sketchfab/BlendSwap variam por arquivo: filtre por CC0 ou CC-BY.
