# Auditoria de obstáculos e dificuldade inicial

Data: 2026-09-27  
Jogo: **Corre Pro Ponto / Busão**

## 1. Perguntas da auditoria

- Há obstáculos suficientes no jogo?
- A experiência está agradável?
- Por que as duas primeiras fases pareciam fáceis demais?

## 2. Resumo executivo

O catálogo é suficiente e variado: o jogo possui **27 famílias de obstáculos 3D** com classes de resolução claras (`LOW`, `GROUND`, `FULL`, `VEHICLE`, `SOFT`, `SLIDE_UNDER`). As 50 fases autorais também passam no validador de rota legal.

O problema encontrado não era falta de catálogo, e sim **onboarding muito suave nas duas primeiras fases**:

- Fase 1 tinha apenas **5 padrões** em 224 m, densidade **2,23 obstáculos/100 m**.
- Fase 2 tinha **8 padrões** em 280 m, densidade **2,86 obstáculos/100 m**.
- Os prazos tinham folga alta: cerca de **14,3 s** na fase 1 e **12,7 s** na fase 2.
- A fase 1 usava só cones, deixando a experiência visual/mecânica repetitiva.

Isso fazia o começo parecer uma reta de tutorial longa, sem pressão suficiente.

## 3. Ajustes aplicados

### Fase 1 — “Saiu atrasada”

Antes:

- velocidade: `5.5 m/s`;
- prazo: `55 s`;
- padrões: `5`;
- densidade: `2,23 / 100 m`;
- variedade: só `cone`.

Depois:

- velocidade: `5.8 m/s`;
- prazo: `48 s`;
- padrões: `8`;
- densidade: `3,57 / 100 m`;
- variedade: `cone` + `pothole`;
- adicionada uma estação dupla segura, sem bloquear os três corredores.

Objetivo: continuar tutorial, mas com decisões mais frequentes e um pulo visualmente mais claro.

### Fase 2 — “A praça do bairro”

Antes:

- velocidade: `5.8 m/s`;
- prazo: `61 s`;
- padrões: `8`;
- densidade: `2,86 / 100 m`;
- grande trecho vazio entre o miolo e o clímax.

Depois:

- velocidade: `6.2 m/s`;
- prazo: `54 s`;
- padrões: `12`;
- densidade: `4,29 / 100 m`;
- mais estações de escolha com `cone`, `bench` e `car`;
- moedas do miolo agora têm leitura/decisão, não apenas respiro passivo.

Objetivo: ainda ser agradável, mas deixar claro já na segunda fase que o jogo exige leitura de faixa.

## 4. Variedade disponível

Classes do jogo:

| Classe | Papel |
| --- | --- |
| `LOW` | obstáculos baixos, resolvidos com pulo ou troca de faixa |
| `GROUND` | buracos/poças baixas, resolvidos com pulo ou troca |
| `FULL` | volumes sólidos de calçada, exigem troca de faixa |
| `VEHICLE` | veículos, exigem leitura lateral |
| `SOFT` | pessoas/animais/poças com tropeço sem dano letal |
| `SLIDE_UNDER` | barreiras/andaimes, resolvidos com deslize |

Famílias contratadas e ativas no jogo: **27**.  
Famílias usadas diretamente nas 50 fases autorais: **21**; as demais continuam ativas no ciclo procedural/endless e gags forçadas.  
Rotas legais: **50/50** em velocidade normal e com boost `1.22x`.

## 5. Novo auditor criado

Foi adicionado:

```bash
python3 tools/audit_obstacles.py
```

Ele mede:

- quantidade de famílias no catálogo;
- classes usadas;
- padrões por fase;
- densidade por 100 m;
- velocidade real da fase autoral;
- margem de prazo;
- quantidade de obstáculos dinâmicos;
- quantidade de tipos por fase.

Resultado após ajuste:

```txt
OBSTACLE AUDIT OK: variedade completa, onboarding com densidade mínima e prazos sem folga excessiva.
```

## 6. Validação de rota

Também foi rodado:

```bash
python3 tools/validate_routes.py
```

Resultado:

```txt
ROUTE REPLICA: 50/50 fases com rota legal (1.0x e 1.22x)
```

Ou seja: a dificuldade subiu no começo, mas sem criar fases injustas ou impossíveis.

## 7. Conclusão

Há obstáculos suficientes no jogo, mas o começo estava permissivo demais. A solução aplicada foi não “lotar” a tela, e sim tornar os primeiros minutos mais vivos:

- mais decisões por metro;
- menos tempo sobrando;
- mais variedade visual já na fase 1;
- mais estações de dupla escolha na fase 2;
- rota sempre legível e validada.

Recomendação futura: após novo playtest, se ainda parecer fácil, o próximo ajuste deve ser progressivo nas fases 3–10, aumentando densidade para ~3,5–4,0 padrões/100 m nos trechos de revisão, sem mexer no contrato das 27 famílias.
