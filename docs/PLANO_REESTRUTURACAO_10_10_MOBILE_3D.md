# Plano completo de reestruturação gráfica — 10/10 mobile 3D estilizado-realista

**Projeto:** Corre pro Ponto  
**Data:** 2026-09-22  
**Base:** auditoria `docs/AUDITORIA_QUALIDADE_GRAFICA_ATUAL.md`  
**Objetivo:** elevar a qualidade mobile 3D estilizado-realista de 5,8/10 para 10/10 dentro de um orçamento realista de Android intermediário.

## 1. Definição de 10/10

Neste projeto, 10/10 não significa fotorealismo de console. Significa:

- leitura imediata da ação em tela pequena;
- personagens com anatomia convincente e materiais coerentes;
- cenário brasileiro reconhecível, detalhado e sem repetição evidente;
- iluminação consistente em sol, nublado, chuva e entardecer;
- UI integrada ao jogo e sem poluição;
- ausência de gaps, z-fighting, clipping, T-pose, textura estourada ou sombra flutuante;
- 60 FPS no aparelho-alvo principal e 30 FPS estáveis no aparelho mínimo;
- qualidade previsível nos renderers Mobile e Compatibility.

## 2. Metas mensuráveis

| Métrica | Meta alta | Meta mínima |
|---|---:|---:|
| FPS em corrida | 60 | 30 estáveis |
| Frame time | ≤16,7 ms | ≤33,3 ms |
| Memória de textura | ≤180 MB | ≤256 MB |
| Draw calls visíveis | ≤180 | ≤260 |
| Triângulos visíveis | ≤1,2 M | ≤1,8 M |
| Cold start | ≤2,8 s | ≤4,0 s |
| Textura sem mipmap/LOD incorreto | 0 | 0 |
| Gaps de quarteirão | 0 | 0 |
| Entidades em T-pose | 0 | 0 |
| Materiais sem textura esperada | 0 | 0 |
| Toques/gestos sem resposta | <1% | <3% |

## 3. Arquitetura de qualidade

Criar três perfis de renderização, sem alterar a direção de arte:

### Mobile Alto

- renderer Mobile;
- MSAA 2x;
- sombras 2048;
- SSAO leve;
- ReflectionProbe por quarteirão;
- LOD alto até 35 m;
- textura 2K para hero e 1K/2K para cenário.

### Mobile Balanceado

- renderer Mobile;
- MSAA 2x ou FXAA;
- sombras 1024;
- SSAO reduzido;
- ReflectionProbe atualizada por trecho;
- LOD agressivo depois de 24 m;
- textura 1K.

### Compatibilidade

- sem recursos Forward+;
- sombras 1024;
- sem GI caro;
- materiais com fallback albedo/normal;
- sem volumetric fog;
- escala 3D adaptativa entre 0,70 e 1,00.

O perfil deve ser escolhido por capacidade do aparelho e permitir override manual em “Qualidade gráfica”.

## 4. Fases de implementação

## Fase 0 — Instrumentação e baseline

**Objetivo:** parar de avaliar por impressão visual apenas.

Implementar:

- painel de debug com FPS, frame time, draw calls, triângulos, memória e renderer;
- captura automática em 720×1280 nos capítulos 1, 10, 25, 40 e 50;
- validação de AABB, escala, gaps e materiais;
- comparação antes/depois usando as mesmas sementes;
- relatório de regressão visual por commit.

**Aceite:** toda alteração gráfica gera captura e números comparáveis.

## Fase 1 — Pipeline de assets

**Objetivo:** estabelecer padrão único para GLB e texturas.

Implementar:

- convenção de nomes de materiais e ossos;
- exportação GLB sem Draco incompatível;
- origem no chão e frente padronizada;
- escala em metros validada automaticamente;
- LOD0/LOD1/LOD2 para cada asset grande;
- limite de materiais por asset;
- mapas albedo, normal, roughness, AO e emissive apenas quando necessário;
- compressão de texturas com mipmaps e formato compatível com Android;
- manifesto com polígonos, materiais, tamanho e licença.

**Aceite:** nenhum GLB entra no projeto sem passar pelo manifesto e pelo validador.

## Fase 2 — Heroína principal

**Objetivo:** resolver o maior bloqueador visual.

Produzir uma personagem dedicada com:

- proporções humanas naturais entre 1,68 m e 1,75 m;
- 7,25–7,75 cabeças de altura;
- rosto com pálpebras, nariz, boca, orelhas e olhos separados;
- córnea e íris com materiais próprios;
- mãos com dedos simplificados, mas legíveis;
- cabelo em mechas/cards com alpha e variação;
- camiseta, jeans e tênis com geometria separada;
- malha LOD0 de 35–60 mil triângulos;
- LOD1 de 15–25 mil;
- LOD2 de 5–8 mil;
- rig de 55–65 ossos;
- clips Idle, Walk, Sprint, Jump, Landing, Crouch e Turn;
- pés alinhados ao piso e braços em antifase;
- materiais de pele com SSS moderado e micro-normal;
- roupa com normal/roughness próprios.

**Aceite:** captura a 2 m e 4 m sem aparência de boneco; sem T-pose, clipping, mãos unidas ou pés flutuando.

## Fase 3 — Elenco humano

Derivar o corpo-base da heroína sem duplicar apenas cores:

- 20 personagens com variação de rosto;
- 5 faixas de idade;
- variação de pele, cabelo, peso e postura;
- roupas com silhuetas brasileiras reconhecíveis;
- acessórios presos ao osso correto;
- mesmo contrato de animação;
- NPCs de baixa prioridade usando LOD e animação simplificada.

**Aceite:** nenhum NPC importante compartilha aparência idêntica com outro.

## Fase 4 — Veículos

Melhorar carros, motos, caminhões e ônibus:

- carroceria com bevel real;
- para-brisa, lanternas e faróis separados;
- calotas alinhadas no eixo do cubo;
- pneus com normal e roughness;
- interior simplificado visível pelo vidro;
- placas, retrovisores e maçanetas;
- LOD para tráfego distante;
- escala validada contra a faixa da rua;
- ônibus final com letreiro de destino e portas funcionais.

**Aceite:** nenhum veículo invade calçada, roda orbita o eixo ou calota fica inclinada.

## Fase 5 — Rua, chão e calçadas

**Objetivo:** eliminar o aspecto procedural repetitivo.

Implementar:

- material macro de asfalto com manchas grandes;
- detail map de agregado pequeno;
- roughness variável por faixa de rodagem;
- remendos, rachaduras ramificadas e marcas de pneu;
- poças com bordas e reflexão local;
- calçada com peças de tamanhos variados e juntas corretas;
- guias, sarjetas e bueiros com escala real;
- decals de desgaste por quarteirão;
- blending de três materiais por proximidade/umidade;
- cache determinístico para não repetir o mesmo padrão.

**Aceite:** captura a 1 m não mostra ladrilho repetido em sequência e o piso não parece ruído de estática.

## Fase 6 — Arquitetura brasileira

Substituir fachadas prismáticas por módulos com profundidade:

- portas e janelas recuadas;
- beirais e telhados com espessura;
- sacadas, grades e varandas;
- caixas d’água, fios e condensadores posicionados com lógica;
- lojas com vitrines e letreiros;
- favela com variação de alinhamento e volumetria;
- prédios com entradas e volumes de esquina;
- HLOD por quarteirão;
- variação de desgaste e pintura por capítulo.

**Aceite:** cada fachada continua legível mesmo sem textura; não pode parecer apenas um cubo pintado.

## Fase 7 — Vegetação e vida urbana

Manter a árvore como referência positiva e expandir:

- 3–5 espécies brasileiras;
- variação de copa e tronco;
- folhas alpha com translucência controlada;
- LOD de árvore e impostor correto;
- pedestres de fundo com animação barata;
- aves e cães com ciclos coerentes;
- lixo, placas, postes e bancos com variação de escala;
- distribuição sem interseções com a pista.

**Aceite:** vegetação recebe luz e sombra sem parecer esfera verde; fauna não atravessa geometria.

## Fase 8 — Iluminação e clima

Implementar presets visuais testáveis:

- manhã clara;
- sol tropical;
- fim de tarde;
- nublado;
- chuva;
- noite com iluminação urbana.

Para cada preset:

- exposição calibrada;
- balanço de branco consistente;
- sombra sem peter-panning;
- contato entre pés/rodas e chão;
- fog sem parede cinza;
- emissive controlado;
- ReflectionProbe sem reflexo congelado indevido.

**Aceite:** o mesmo material mantém aparência coerente nos cinco presets.

## Fase 9 — HUD e UX

Finalizar a interface com:

- HUD minimalista durante corrida;
- tutorial em etapas;
- gestos com confirmação visual e tátil;
- sensibilidade configurável;
- opção de botões virtuais;
- tela de resultado com “Próxima fase” como ação principal;
- loja com prévia 3D da personagem;
- estados inequívocos: bloqueado, disponível, comprado e equipado;
- tamanho de fonte configurável;
- alto contraste e modo daltônico;
- controle independente de música, efeitos e vibração;
- sinalização do ponto nos últimos metros.

**Aceite:** usuário identifica objetivo, tempo e próxima ação em menos de 1 segundo.

## Fase 10 — QA visual e performance

Criar matriz de teste:

- aparelho alto, médio e mínimo;
- Mobile e Compatibility;
- sol, chuva e entardecer;
- menu, corrida, colisão, chegada e resultado;
- tela com notch e sem notch;
- orientação retrato;
- baixa memória;
- retomada após pausa.

Bloquear release se houver:

- gap visível;
- T-pose;
- personagem deitado;
- veículo na calçada;
- calota desalinhada;
- UI cortada por safe area;
- queda abaixo da meta de FPS;
- material sem mipmap;
- objeto essencial sem sombra/recepção coerente.

## 5. Ordem de execução recomendada

1. Instrumentação e baseline.
2. Heroína com rig e animações.
3. Pipeline de assets e LOD.
4. Chão/calçadas.
5. Arquitetura.
6. Veículos.
7. Vegetação e vida urbana.
8. Iluminação/clima.
9. HUD, loja e acessibilidade.
10. QA em dispositivos e otimização.

## 6. Critério de conclusão 10/10

O projeto só será considerado 10/10 quando:

- a heroína estiver rigged e animada;
- as cinco capturas de referência não apresentarem regressão;
- o cenário tiver variação de material e profundidade arquitetônica;
- os veículos respeitarem a rua e tiverem rodas alinhadas;
- o HUD não cobrir informações essenciais do mundo;
- acessibilidade e controles puderem ser configurados;
- o aparelho mínimo sustentar 30 FPS estáveis;
- o aparelho principal sustentar 60 FPS na maior parte da corrida;
- todos os validadores técnicos e visuais estiverem verdes.

## 7. Entregáveis por lote

Cada lote deve incluir:

- código e assets;
- captura antes/depois;
- números de performance;
- atualização de `CREDITS`/proveniência;
- teste automatizado correspondente;
- nota de renderer e aparelho testado;
- rollback simples para o perfil anterior.

A meta 10/10 é tratada como um programa de produção, não como uma sequência de ajustes isolados. O primeiro lote recomendado é a heroína com rig, porque ela é o elemento mais observado e atualmente o maior limitador da percepção de qualidade.
