# Lote 4 — clima: chuva, asfalto molhado, relâmpago e trovão

Objetivo: dar vida ao cenário do Lote 3 com clima de verdade — chuva em GPU,
chão que molha e seca, poças que refletem, céu que fecha e relâmpago com trovão —
sem estourar o orçamento do Honor X8b (Adreno 610).

## Arquivos

| Arquivo | O que é |
| --- | --- |
| `resources/weather_spec.json` | **Fonte única da verdade** do clima: estados, chuva, relâmpago, molhado, poças, sonda, orçamento e céu. |
| `scripts/weather_system.gd` | Sistema de clima (694 linhas): chuva em `GPUParticles3D`, luz de relâmpago + véu branco, molhado nos materiais do kit, poças em `MultiMesh` por trecho, sonda de reflexo e trovão em `AudioStreamPlayer3D`. |
| `assets/textures/ceu/nuvens.png` | Textura equirretangular de nuvens (1024×512, sem emenda no horizontal, 206 KB). |
| `assets/audio/trovao.wav` | Trovão de 2,6 s (44100 Hz, mono, 16 bits): estalo + estrondo, 224 KB. |
| `tools/generate_clouds.py` | Gera a textura de nuvens (determinística). |
| `tools/generate_thunder.py` | Gera o trovão (determinístico, com filtros simples). |
| `tools/audit_lighting.py` | Auditor do clima: spec, assets, tom (ACES do Lote 2) e o código do sistema. Desenha `docs/preview_clima_lote4.png`. |
| `tools/run_lote4_selftest.py` | Autoteste: 11 defeitos plantados + o pacote real. |
| `tools/weather_facts.json` | Fatos do engine 4.7.2 usados aqui, com fonte e a armadilha do `sky_cover`. |
| `tools/check_def_use.py` | Verificador de nomes (0 problemas). |
| `docs/PATCH_GAME_3D_LOTE4.md` | Roteiro de colagem no `game_3d.gd`. |
| `docs/CHECKLIST_LOTE4.md` | Passo a passo para testar e mandar o feedback. |
| `tests/fixtures/world_spec.json` | Cópia de referência do Lote 3 (usada só quando o projeto real não está por perto). |

## Decisões

- **Nenhum número de clima no código**: chuva, relâmpago, molhado e poças vêm
  todos do `weather_spec.json`. O auditor reprova se achar um desses valores
  escritos no `.gd` (é o que impede o "número mágico" voltar).
- **`sky_cover` é TEXTURA, não número** (confirmado na doc 4.7.2): a intensidade
  das nuvens vai em `sky_cover_modulate`, e o céu de tempestade vem de deixar o
  topo/horizonte acinzentados + `sky_energy_multiplier` menor, porque as cores
  da textura são *somadas* ao céu (nuvem escura por textura não existe).
- **Orçamento no celular**: 1150 pingos na tempestade (teto 1200), **uma** luz
  extra (o relâmpago, sem sombra), poças em `MultiMesh` (36 instâncias),
  sonda de reflexo **desligada** no `mobile` (ligada no Forward+).
- **Determinismo**: semente do spec no `_rng`; poças por trecho com hash do
  índice do trecho; o auditor tem regra específica contra `randomize()`.
- **Clima reaplica o estado a cada 2 s**: assim ele ganha de qualquer outro
  sistema que mexa no sol/névoa depois dele (o Lote 2 reaplica no `node_added`).
- **Física pronta para o Lote 5**: `get_wetness()` (0..1) já é a umidade do chão,
  que o Lote 5 vai usar para atrito e frenagem do `CharacterBody3D`.

## Portões (gates)

```bash
python3 tools/check_def_use.py scripts/weather_system.gd   # 0 problemas, exit 0
python3 tools/audit_lighting.py                            # 0 problemas (1 aviso: cópia de referência)
python3 tools/run_lote4_selftest.py                        # 0 falhas (11 defeitos plantados)
python3 tools/generate_clouds.py && python3 tools/generate_thunder.py   # assets reprodutíveis
```

Saída do auditor (verde):

```
tom: Laje ao sol (limpo) = 128        <- bate com a âncora do Lote 2 (127/128)
tom: Laje ao sol (tempestade) = 79
tom: Laje na sombra (tempestade) = 45
tom: Asfalto molhado (tempestade) = 28
tom: Pico do relampago = 198
tom: Clarao na tela (raio) = 114
nuvens: 1024x512 | emenda 0.05/255 | contraste 146
trovao: 2.6s | pico 0.89 | cauda 0.050
resumo: 0 problema(s)
```

O autoteste cobre, entre outros: asfalto que ficaria **mais fosco** molhado,
relâmpago em céu limpo, chuva acima do orçamento, pingo grosso, poça escura
demais, trecho das poças fora do compasso do quarteirão, script sem semente,
`sky_cover` recebendo número, nuvem com emenda e trovão fraco.

## Próximo lote (5) — anotações

- Trocar o visual do corredor por `CharacterBody3D` de verdade: `ShapeCast3D`
  para degrau/rampa, `Area3D` para gatilhos, coyote time, dash e knockback.
- Usar as metas já gravadas pelo kit (`superficie`/`colisor`) e o
  `get_wetness()` do clima: atrito menor no chão molhado (derrapagem) e
  respingo/pó conforme a superfície.
- Auditor novo (`tools/audit_physics.py`): gravidade, altura do pulo, tempo de
  coyote, raio do `ShapeCast3D`, atrito seco × molhado e o custo por quadro.
