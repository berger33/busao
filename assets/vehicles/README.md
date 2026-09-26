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
| `bicycle.glb`           | Obstáculo "bicycle" (calçada)      | 1,85 m × 1,15 m       |

O jogo escala o modelo para o tamanho-alvo e o assenta no chão automaticamente.

## Variantes do Lote 6 (cores e rodas baked)

A partir do Lote 6 o jogo sorteia **variantes** quando existirem (drop-in opcional,
mesmo ajuste `GLB_FIT` da base). Se só a base existir, ela é usada.

| Arquivo | Variante de | Cor | Roda | Geração |
|---|---|---|---|---|
| `car_azul.glb` | `car` | azul (0.14,0.28,0.68) | aro prata com faixa azul baked 256² | `build_lote6.py` |
| `car_prata.glb` | `car` | prata (0.76) | aro preto | `build_lote6.py` |
| `truck_vermelho.glb` | `truck` | vermelho (0.70,0.14,0.13) | cromada | `build_lote6.py` |
| `motorcycle_verde.glb` | `motorcycle` | verde (0.14,0.52,0.22) | cromada | `build_lote6.py` |

A roda azul tem textura baked procedural (PIL, 256×256, fundo prata + disco azul +
parafusos) aplicada como `ShaderNodeTexImage` no `Principled BSDF`; o GLB embala a
imagem. O sorteio é determinístico por `hash(kind+entities.size()+phase_index)` em
`_pick_vehicle_variant()` — auditável e sem RNG extra.

## Efeitos e captura (Lote 6)

- Poeira de deslize e respingo em pista molhada (`_clima.get_wetness()>0.35`) via
  `GPUParticles3D` leves (≤80 partículas, `fx_root`).
- Modo captura: **C** alterna órbita livre, arraste com botão esquerdo para girar,
  **P** (em captura) ou **F10** salva `user://captura_*.png`.

O modelo deve estar orientado com o comprimento no eixo **Z** e virado para **-Z**
(o mesmo padrão dos veículos procedurais).

**Esta pasta já vem com os 7 modelos originais do projeto (Lote 5)**,
modelados por Blender headless via `tools/blender/build_lote5.py`
(hatch, sedan, moto, caminhão de carroceria de madeira, dois ônibus urbanos —
o do ponto com letreiro LED "PONTO FINAL" — e bicicleta). Nós de roda nomeados
`Wheel*`/`BusWheel*`/`MotoWheel*` giram sozinhos no trânsito. Para trocar por
outro modelo, basta substituir o arquivo mantendo o nome.

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
