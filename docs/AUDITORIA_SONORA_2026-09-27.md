# Auditoria sonora — pacote high-quality confortável

Data: 2026-09-27  
Jogo: **Corre Pro Ponto / Busão**

## 1. Proposta sonora

O jogo é um runner urbano brasileiro: corrida para alcançar o ponto de ônibus, leitura rápida de rua/calçada, coleta de moedas e bônus, obstáculos cotidianos, interface mobile e progressão por fases. A direção sonora precisa ser:

- **confortável**: sem picos agudos agressivos, sem clipping, transientes arredondados;
- **agradável e hipnótica**: música curta em loop com pulso suave, sem cansar em repetição;
- **coerente**: moedas, recompensas e UI compartilham uma assinatura tonal brilhante; rua/personagem usam foley mais orgânico;
- **legível em gameplay**: pulo, dash, deslize, passos, impacto, ônibus e coleta precisam ser reconhecíveis mesmo em celular.

## 2. Diagnóstico do pacote anterior

Auditoria técnica feita por inventário de chamadas `AudioManager.play_sfx`, lista `SFX`, músicas em `MUSIC` e metadados dos WAVs.

Problemas encontrados:

| Área | Situação anterior | Risco |
| --- | --- | --- |
| Qualidade técnica | WAVs mono 22.05 kHz | sensação simples/placeholder em celular moderno |
| Identidade | muitos efeitos eram tons curtos genéricos | pouca coerência emocional entre UI, moedas e recompensas |
| Ações do personagem | dash reutilizava `whoosh` de troca de faixa | dash não tinha assinatura própria |
| Loops | músicas de 8 s muito simples | repetição cansativa; menos sensação hipnótica |
| Alertas | ônibus/tempo/clima disputavam espaço com efeitos frequentes | risco de feedback importante perder impacto no mix |
| Conforto | alguns efeitos de ruído/impacto eram ásperos | fadiga auditiva em sessões longas |

## 3. Implementação

Todos os WAVs foram recriados de forma autoral e determinística em `tools/generate_audio.py`, sem bibliotecas externas.

Novo padrão técnico:

- **44.1 kHz**;
- **estéreo**;
- **PCM 16-bit**;
- envelopes com fade nas bordas para evitar clique;
- limiter/soft-clip para evitar clipping;
- pequenas ambiências/delays estéreo para sensação de espaço sem exagero.

## 4. Mapa de sons recriados

| Som | Direção aplicada |
| --- | --- |
| `coin.wav` | brilho curto tipo sino/marimba, agradável para repetição frequente |
| `combo.wav` | arpejo ascendente mais celebratório, mas sem estridência |
| `pickup.wav`, `reward.wav`, `streak.wav` | família tonal positiva, coerente com coleta e progressão |
| `jump.wav` | impulso ascendente com ar/tecido, comunica subida sem ficar cartunesco demais |
| `dash.wav` | novo som próprio: sopro rápido + grave curto, separado de troca de faixa |
| `whoosh.wav` | agora reservado para mudança lateral/leitura de faixa |
| `slide.wav` | tecido + atrito filtrado, confortável e reconhecível |
| `step_*` | foley sutil por superfície: asfalto, calçada, terra e metal |
| `hit.wav`, `impact_heavy.wav`, `wall.wav` | impactos mais graves e arredondados, sem estourar ouvido |
| `bus_horn.wav` | buzina de ônibus arredondada, urbana e menos agressiva |
| `bus_doors.wav` | hiss pneumático + fechamento grave para embarque |
| `bark.wav` | latido estilizado do caramelo, audível sem irritar |
| `shout.wav` | vocalização sintética curta de esbarrão, sem depender de voz gravada |
| `rain_loop.wav` | chuva estéreo baixa, loopável e confortável |
| `trovao.wav` | trovão grave e distante, reduzido para não assustar |
| `music_*.wav` | loops de 16 s com pulso suave, ostinato e pads discretos por capítulo |
| `ui_*`, `count_*` | interface com assinatura limpa, responsiva e pouco cansativa |
| `victory.wav`, `defeat.wav`, `levelup.wav`, `purchase.wav`, `chest.wav` | stingers curtos, coerentes e polidos |

## 5. Alterações de código

- `scripts/audio_manager.gd`
  - adiciona `dash` no mapa `SFX`;
  - inclui `bus_doors` em `ALERTS`, usando player dedicado e ducking de música.
- `scripts/game_3d.gd`
  - `_dash()` passa a tocar `dash` em vez de reutilizar `whoosh`.
- `assets/audio/dash.wav.import`
  - criado para manter o novo asset no padrão dos demais imports Godot.

## 6. Critérios de aprovação

- Todos os sons do jogo e ações principais foram regenerados.
- Moeda, pulo, dash, deslize, passos, UI, ônibus, chuva, trovão, vitória/derrota e música têm identidade própria.
- O pacote evita clipping e mantém picos confortáveis.
- O contrato existente de gameplay/personagens não foi alterado.

## 7. Comando de regeneração

```bash
python3 tools/generate_audio.py
```

O comando é determinístico (`seed=20260927`) e recria o pacote completo em `assets/audio/`.
