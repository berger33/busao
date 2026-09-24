# Blueprint de produção — Corre pro Ponto

Plano proposto em 20/09/2026, baseado no código desta pasta e na imagem enviada pelo usuário. Este documento descreve melhorias futuras; não significa que tenham sido implementadas ou aprovadas em teste de jogo.

**Objetivo:** um runner 3D em terceira pessoa no qual a protagonista percorre uma fase urbana, supera obstáculos e embarca no ônibus antes de ele partir. O jogador progride por percursos finitos, aprende novas situações e reconhece por que ganhou ou perdeu.

**Recomendação principal:** produzir primeiro uma fase curta com a qualidade visual, o controle e o embarque desejados. Essa fase será o padrão para as demais. O projeto já tem volume de sistemas; agora precisa de unidade visual, regras confiáveis e percursos desenhados com intenção.

Premissas de planejamento: Godot 4; Android como plataforma principal; tela vertical, seguindo o projeto; teclado para desenvolvimento no PC; campanha para um jogador; funcionamento offline. São decisões iniciais revisáveis, não requisitos adicionais informados pelo usuário. Não há motivo demonstrado para trocar de engine neste momento.

![Referência visual fornecida pelo usuário](media/referencia-blueprint-runner.jpg)

Catálogo complementar: [plano das 50 fases](PLANO_50_FASES_CORRE_PRO_PONTO.md).

## 1. O que o protótipo realmente oferece

Inspeção realizada: cena principal, configuração do projeto, controlador 3D, personagens, dados de fases, catálogo de obstáculos, construção do cenário, física, iluminação, HUD e scripts de auditoria. Documentos antigos foram usados como contexto, não como prova de funcionamento atual.

| Área | Evidência no projeto | Decisão proposta |
|---|---|---|
| Base 3D | `scenes/main.tscn` instancia `scripts/game_3d.gd` | Evoluir a base existente |
| Movimento | Corrida automática, troca de faixa, pulo, deslize e dash | Preservar o conceito; revisar resposta e coerência das ações |
| Fases | `phase_data.gd` cataloga 50 fases, com 400–792 m e velocidade base de 5–18 m/s | Manter IDs; substituir progressão predominantemente numérica por percursos autorais |
| Distribuição | `_build_course()` usa intervalos, ciclos de tipos, variação aleatória e eventos forçados | Introduzir sequências de desafios com caminho válido e ritmo controlado |
| Três faixas | Centros em X = −3,25 / 0 / 3,25; uma rua e duas calçadas | Testar três corredores invisíveis mais próximos na calçada; rua como contexto e eventos específicos |
| Chegada | Em `_update_run()`, a contagem de espera começa em `at_stop`; ao zerar, chama vitória | Implementar prazo de partida contado durante a corrida |
| Colisões | `_resolve_entity()` considera pulo ou dash seguros contra veículos; deslize também evita a maior parte dos obstáculos de calçada | Cada obstáculo terá altura, volume e ações permitidas próprias |
| Cenário | `building_kit.gd` já monta e recicla quarteirões; `world_spec.json` concentra medidas | Aproveitar esse kit como base para módulos editáveis |
| Corredores | `runner_character.gd` tenta GLB próprio por personagem e tem modelos alternativos | Escolher uma protagonista para alcançar primeiro o padrão da referência |
| Câmera | Parâmetros iniciais de 54° de FOV, altura 2,25 m e recuo 4,85 m | Calibrar composição a partir dessa base; não reiniciar no escuro |
| Renderização | Configuração geral usa Mobile; override mobile usa Compatibility | Definir aparelho de referência e validar o visual no renderer realmente exportado |
| Interface e progressão | HUD, mapa, estrelas, loja, save e vários gerenciadores já existem | Simplificar a experiência da corrida e preservar o que funciona |
| Economia | `starting_coins = 100000` está marcado como configuração de teste | Separar desenvolvimento e lançamento; rebalancear antes de publicar |

**Verificações executadas nesta análise:**

- `python tools/audit_balance.py`: passou a auditoria numérica existente. Ela não comprova a diversão, a rota segura de cada sequência ou a fidelidade visual.
- `python tools/validate_project.py`: falhou por divergência entre a lista dos manifestos SHA-256 e arquivos `.glb.import` dos personagens. Investigar o contrato do manifesto antes de alterá-lo; não há evidência aqui de corrupção dos modelos.
- `python tools/check_gdscript.py`: não executou a análise porque o Python usado não tem a dependência `lark`.
- Godot não foi localizado no PATH; não executei o jogo nem medi FPS. A imagem local `docs/media/humano_F.png` é um registro de asset, não uma captura atual validada de gameplay. Nenhuma nota de qualidade abaixo é uma medição do jogo rodando.

O problema mais importante de design identificado é concreto: **o protótipo ainda não exige chegar antes do ônibus partir**. O segundo é a generalização das ações de defesa, que reduz o significado de cada obstáculo.

## 2. Passo 1 — Fixar a experiência que será construída

O ciclo de uma fase será:

1. Escolher a fase no mapa.
2. Ver rapidamente destino, ônibus e uma novidade daquela fase.
3. Contagem de largada; câmera já enquadra o caminho.
4. Correr, desviar, pular ou deslizar; coletar moedas opcionais.
5. Ver o ponto e o ônibus na aproximação final.
6. Entrar na área de embarque antes do prazo.
7. Assistir a uma conclusão curta e receber estrelas; avançar ou repetir imediatamente.

Três pilares orientam as decisões: **ler o caminho**, **sentir o corpo correndo** e **chegar por pouco de forma justa**. Um recurso novo só entra se melhorar um deles.

Para o primeiro marco: uma protagonista, um bairro, uma fase de 336 m, cinco famílias de obstáculos e uma sequência completa de chegada. Depois: cinco fases boas; depois dez; depois vinte; finalmente cinquenta. O catálogo atual de 50 entradas continuará disponível como material de migração, sem fingir que ele representa 50 percursos finalizados.

A primeira entrega não depende de clima complexo, muitos personagens, compras, anúncios, animais variados, chefes ou modo infinito. Esses sistemas podem permanecer preservados no projeto, mas deixam de ditar a produção da experiência principal.

**Pronto quando:** todas as pessoas envolvidas conseguem descrever o mesmo jogo em uma frase e existe uma lista explícita do que pertence à fase piloto.

## 3. Passo 2 — Transformar a imagem em uma direção de arte executável

A referência é uma cena 3D estilizada com proporções plausíveis. As árvores têm copas facetadas; fachadas, piso e iluminação fornecem riqueza. Buscar uma cidade coerente com essa linguagem é mais útil do que perseguir realismo fotográfico em cada objeto.

| Elemento da referência | O que produzir | Como conferir |
|---|---|---|
| Personagem vista de costas | Mulher de camiseta rosa, calça escura, tênis e cabelo preso; silhueta natural | Vista traseira e três quartos, parada e correndo, na câmera final |
| Calçada dominante à direita | Piso claro de peças retangulares, guia contínua, faixa livre para correr | Piso conduz o olhar ao ponto de fuga e não compete com obstáculos |
| Rua à esquerda | Asfalto escuro, sinalização, carros com escala coerente | Carros parecem pertencer à mesma cidade que a protagonista |
| Fachadas baixas | Prédios de dois a três pavimentos, reboco, tijolo, portas e janelas com profundidade | Ritmo variado sem duplicação óbvia a cada poucos metros |
| Árvores e mobiliário | Árvores de copas simples, canteiros, bancos, postes e grelhas | Objetos decorativos deixam o corredor visualmente legível |
| Sol baixo | Luz quente lateral, sombras longas, ambiente mais frio nas áreas sombreadas | Pés, carros e bancos parecem apoiados no chão |
| Profundidade | Contraste mais baixo ao longe, céu claro e névoa leve | Obstáculos relevantes continuam legíveis antes da reação |
| HUD discreto | Pausa, prazo, progresso e moedas nas bordas | Centro da tela permanece livre durante decisões |

**Ordem da melhoria visual:** composição e escala → silhueta da personagem → animação → luz e contato com o chão → arquitetura → materiais → detalhes e efeitos. Texturas maiores não corrigem uma silhueta inadequada ou uma corrida com pés deslizando.

### Composição e câmera

- Tratar a imagem quadrada como referência de composição. O jogo está em 9:16; não esticar a imagem nem copiar coordenadas de tela literalmente.
- Criar uma cena de comparação em 1:1 e outra no formato final 9:16. Ajustar cada composição para preservar rua à esquerda, calçada à direita e profundidade.
- Partir da câmera existente e testar FOV de 50–60°, altura de 2,2–2,8 m e recuo de 4,8–6 m. São intervalos de experimentação, não valores finais.
- Procurar personagem ocupando aproximadamente 28–35% da altura visível, com pés dentro do quadro e espaço suficiente acima para antecipar perigos. Confirmar no aparelho.
- Suavização lateral curta e previsível; evitar que a câmera esconda a faixa de destino quando o jogador muda de corredor.
- Oscilação de corrida e tremor muito discretos; opção de movimento reduzido elimina ambos. Não usar desfoque forte para esconder limitações gráficas.

### Protagonista e animação

1. Definir desenho frontal, lateral e traseiro, com proporções consistentes. Usar a atleta existente como candidata e conferir o GLB efetivamente carregado, antes de decidir reaproveitar ou remodelar.
2. Modelar corpo, roupa e cabelo com silhueta suave nos ombros, braços, quadril e pernas; roupa precisa ter volume próprio.
3. Preparar UVs, materiais simples de pele/tecido/cabelo, rig e pesos de deformação. Cada joelho e cotovelo deve dobrar sem colapsar.
4. Criar ou adaptar clips: idle, largada, corrida, passo lateral esquerdo/direito, preparação de salto, salto, queda/aterrissagem, deslize, recuperação, tropeço, exaustão, embarque e comemoração.
5. Usar transições de animação sem travar o comando. A resposta de controle começa antes de terminar uma animação decorativa.
6. Sincronizar cadência, distância e contato dos pés. Validar corrida a velocidades baixa, média e alta e durante boost.
7. Animar cabelo preso com poucos ossos; evitar simulação pesada de tecido no primeiro marco.

O código declara ciclo de locomoção de referência de 4 m/s e limite de reprodução de 2,2×, enquanto o catálogo chega a 18 m/s. Isso é um **risco a medir** de incompatibilidade entre passada e velocidade; verificar o clipe e os ajustes reais antes de decidir a correção.

O fluxo recomendado de asset é fonte editável no Blender → GLB → cena herdada/adaptadora no Godot → teste na câmera do jogo. Registrar origem, licença quando aplicável e versão de cada asset. A documentação oficial cobre a [importação de cenas 3D](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/index.html).

### Iluminação e materiais

- Escolher um único horário, fim de tarde, para a fase piloto. Ajustar sol, céu, exposição e névoa juntos.
- Priorizar sombra da protagonista e dos objetos próximos. Iluminação do fundo pode ser simplificada.
- Criar materiais compartilhados: piso, asfalto, tijolo, reboco, madeira, metal, vidro, vegetação, pele e tecido.
- Usar variação de roughness e normal na escala correta. Não aplicar ruído forte em tudo.
- Manter árvore estilizada e personagem natural na mesma paleta. Evitar misturar vários estilos de pacotes de assets.
- A moeda pode ser maior que uma moeda real para continuar legível no celular. Avaliar tamanho em pixels e clareza; não reduzir todos os coletáveis a escala física literal.
- Implementar primeiro a luz que funciona no renderer alvo. SDFGI, VoxelGI e névoa volumétrica são recursos de Forward+; não serão requisitos do visual Android. A [comparação oficial dos renderers do Godot 4.7](https://docs.godotengine.org/en/4.7/tutorials/rendering/renderers.html) explica essas diferenças.
- Lightmaps só entram após teste do modelo de chunks: o projeto move e recicla o cenário. Um bake estático exige geometria, luz e espaço de referência consistentes. AO nos materiais e luz direcional são uma base mais simples para a primeira prova.

**Pronto quando:** uma captura real de gameplay no aparelho, com a câmera final, reproduz as prioridades da referência: silhueta, composição, escala, iluminação e materiais. Não aprovar só por render do Blender ou por screenshot promocional.

## 4. Passo 3 — Tornar o controle preciso e as colisões compreensíveis

### Organização das rotas

Recomendação: três corredores lógicos, sem linhas pintadas, dentro da calçada ampla. O cenário continua mostrando a rua à esquerda. Isso aproxima a composição da foto e reduz a dependência de carros vindo por trás como principal desafio.

Usar, como protótipo de escala, corredores separados por 1,1–1,3 m, com aproximadamente 3,6–4 m de passagem útil e uma faixa adicional de mobiliário. Esses números precisam de teste com câmera, colisores e proporções do kit existente. Não substituir `LANE_X` isoladamente: mapa visual, entidades, física, coletáveis, HUD e tutoriais precisam usar a mesma definição.

Entradas na rua aparecem como eventos desenhados: travessia sinalizada, faixa interditada, veículo cruzando à frente. A rua pode virar uma rota alternativa em fases avançadas, mas precisa mostrar risco, recompensa e retorno à calçada. A primeira campanha pode funcionar inteira sem movimento lateral livre.

### Controles

| Ação | Celular | PC | Resposta proposta |
|---|---|---|---|
| Trocar um corredor | Swipe horizontal | A/D ou setas | Transição de aproximadamente 0,18–0,25 s |
| Pular | Swipe para cima | Espaço/↑ | Salto de duração previsível, com pequena tolerância de entrada |
| Deslizar | Swipe para baixo | S/↓ | Duração aproximada de 0,65–0,80 s; collider acompanha a postura |
| Pausar | Botão fixo | Esc/botão | Congelar simulação e prazo |
| Arrancada, após núcleo validado | Botão opcional | X | Recurso curto e limitado, com pista legível na velocidade resultante |

Botões grandes de direção/pulo/deslize podem existir como alternativa acessível. O joystick desenhado na referência não obriga adotar movimento livre: testar esse modo separadamente só depois de o runner por corredores estar aprovado.

Pontos de implementação: buffer de comando inicial de cerca de 120 ms; um gesto gera uma ação; limiar de swipe proporcional à tela; nenhuma ação no retorno de pausa; visualização de collider no modo de teste; detecção varrida para objetos rápidos; colisão pela posição real durante a troca de corredor, não somente pelo índice de destino.

### Regras de erro

- Três pontos de fôlego/vida como base, inclusive nas fases finais da campanha normal. Não introduzir subitamente morte em um impacto só.
- Um impacto válido retira um ponto e, no primeiro balanceamento, acrescenta 2 s de penalidade ao tempo consumido. Mostrar “+2 s de atraso”.
- Um impacto só pode pontuar uma vez por entidade. Recuperação de cerca de 1 s impede danos em cascata; não deve permitir atravessar indefinidamente obstáculos.
- O breve congelamento visual de impacto, se existir, congela também o relógio para não somar punição invisível.
- Zero de fôlego encerra a tentativa. Prazo expirado também encerra a tentativa. Exibir a causa específica.
- Pular não permite atravessar ônibus ou caminhão. Deslizar não permite atravessar banco, hidrante ou pessoa. Dash não concede imunidade universal na campanha proposta.
- Colisão com pessoas e animais produz desvio/tropeço, sem violência gráfica; priorizar leitura e humor de situação.

O valor de 2 s, os três pontos e as janelas são parâmetros iniciais. Se os playtests mostrarem punição excessiva, reduzir a penalidade ou usar apenas um dos dois custos antes de expandir fases.

**Pronto quando:** dez tentativas seguidas repetem a mesma resposta para o mesmo comando e o jogador consegue explicar por que cada contato causou ou não dano.

## 5. Passo 4 — Fazer o ônibus ser a meta real

O prazo começa na largada, com indicação “Ônibus parte em 01:06”. Pausas e app em segundo plano suspendem a simulação da partida individual. A hora do sistema não controla a fase.

Estados propostos: `preparação → contagem → corrida → aproximação → embarque → resultado`. A aproximação é uma parte da corrida, e o prazo continua correndo nela.

Regra autoritativa: sucesso quando a personagem cruza a área de embarque com fôlego positivo e tempo consumido menor ou igual ao limite. Avaliar impacto, chegada e expiração com ordem determinística; uma tentativa concluída não pode ser concluída novamente.

Para que seja justo, a zona de embarque ocupa a passagem final acessível. Não exigir um toque extra perfeito no último quadro. Chegou dentro do prazo: a animação de entrar no ônibus pode terminar depois sem retirar a vitória.

### Cálculo inicial do prazo

`tempo limite = tempo de referência do percurso + margem de erros`

O tempo de referência deve ser medido com uma rota legal, sem bônus pagos e sem dash obrigatório, incluindo ações, curvas e superfícies que alterem velocidade. A divisão distância/velocidade serve apenas para o primeiro protótipo de uma pista reta.

Exemplo da fase piloto: 336 m a 6 m/s resultam em 56 s nominais. Começar com limite de 66 s, uma margem de 10 s. Com penalidade de 2 s por impacto, o jogador percebe o custo sem depender de uma corrida perfeita. Recalcular após testar animações, rota e superfície.

Margens iniciais por grupo: aprendizado 12–14 s; domínio básico 10–12 s; combinações 8–10 s; avançado 6–8 s. A margem não reduz a janela de reação dos obstáculos. São duas alavancas diferentes.

No trecho final:

1. A 70–90 m, o ponto e a silhueta do ônibus ficam visíveis; nenhum objeto obrigatório os encobre.
2. A 40–60 m, um som curto e a interface reforçam a partida. Sem spam de buzinas.
3. Nos últimos 28 m, um corredor amplo prepara o embarque. Não estrear mecânica ou sortear um obstáculo surpresa.
4. Em caso de sucesso, personagem entra e as portas fecham; conclusão de 2–3 s, pulável em replays.
5. Em caso de atraso, ônibus parte; informar quantos segundos faltaram e permitir repetir rapidamente.

A arrancada opcional serve para recuperar margem ou disputar medalhas. Toda fase normal deve ser vencível sem ela. Limitar usos e validar o percurso à velocidade máxima; não combinar multiplicadores sem limite, porque isso muda o tempo de reação.

**Pronto quando:** existem demonstrações reproduzíveis de chegada adiantada, chegada no limite e ônibus perdido por atraso, com comportamento correto após pausa e retorno do app.

## 6. Passo 5 — Criar uma biblioteca de obstáculos com função clara

O catálogo abaixo é uma proposta de gameplay. IDs existentes serão reaproveitados quando o comportamento e o modelo forem compatíveis.

| Família | Leitura visual | Resposta principal | Introdução | Regra de justiça |
|---|---|---|---|---|
| Cone/caixa baixa | Silhueta pequena, cor contrastante | Pular ou mudar corredor | Fase 1 | Não esconder em sombra densa |
| Banco/floreira | Volume sólido atravessando passagem | Mudar corredor | Fase 2 | Deslize não resolve |
| Barreira suspensa de obra | Vão inferior claramente visível | Deslizar ou mudar corredor | Fase 3 | Collider superior corresponde à barra |
| Buraco/vala curta | Bordas, diferença de altura e aviso | Pular ou contornar | Fase 4 | Largura menor que alcance legal do salto |
| Lixeira/hidrante/orelhão | Objeto fixo alto ou largo | Mudar corredor | Fase 6 | Parte da decoração semelhante não pode mudar de regra sem sinal |
| Pedestre | Olhar e preparação antes de atravessar | Mudar corredor/aguardar janela pela rota | Fase 7 | Trajetória decidida antes da reação; sem perseguir lateralmente o jogador |
| Carrinho de entrega | Movimento lateral lento anunciado | Escolher corredor livre | Fase 8 | Nunca fechar a última saída durante a manobra |
| Carro parado/van de entrega | Grande volume na borda ou cruzamento | Desviar pela passagem aberta | Fase 9 | Não saltar por cima do teto |
| Andaime/toldo | Barra alta e suporte lateral | Deslizar no vão ou contornar | Fase 11 | Não exigir pulo e deslize ao mesmo tempo |
| Poça/trecho irregular | Superfície distinta | Contornar ou pular | Fase 12 | Efeito de velocidade explícito e determinístico; sem comando invertido |
| Ciclista | Aviso e aproximação visível | Escolher corredor de escape | Fase 13 | Passagem pela frente; evitar ataque fora da câmera |
| Motocicleta em cruzamento | Som + sinal visual antes da passagem | Respeitar a janela do cruzamento | Fase 14 | Nunca depender apenas de áudio |
| Cachorro cruzando | Animação de preparação na borda | Contornar | Fase 16 | Sem teleporte e sem dano gratuito |
| Caminhão/ônibus de tráfego | Massa visível no cruzamento | Permanecer na área segura | Fase 18 | Obstáculo ocupa o espaço só na janela anunciada |
| Sequência combinada | Reúne famílias já aprendidas | Duas decisões separadas | A partir da fase 5 | Validar tempo para recuperar da primeira ação |

Cada obstáculo precisa de: ID estável; cena visual; collider; ações válidas; velocidade/trajetória; sinal antecipado; dano/custo; tempo de recuperação; espaço ocupado; distância mínima dos vizinhos; reação sonora; estados ativo/concluído; teste de passagem.

Veículos puramente decorativos não colidem com o jogador. Perigos precisam ser identificáveis. Árvores, bancos e postes fora da rota não ganham collider de gameplay por acidente.

### Espaçamento medido em tempo

Começar com leitura de 2,5–3 s no tutorial, 2–2,5 s no meio da campanha e aproximadamente 1,8–2,2 s nos desafios avançados. São hipóteses para testar, não limites universais da percepção humana.

`distância útil de antecipação ≥ velocidade relativa × (reação + execução da ação + margem)`

Exemplo: 8 m/s × (1,5 s de reação + 0,25 s de troca + 0,25 s de margem) = 16 m de pista efetivamente legível. Um obstáculo estar carregado a 80 m não significa que seja legível a essa distância.

Para veículos que se aproximam, usar velocidade relativa, não só a velocidade da protagonista. Verificar também caminho de saída, sequência seguinte e aterrissagem. Duas decisões obrigatórias consecutivas precisam respeitar o término e a recuperação da primeira ação.

**Pronto quando:** cada família pode ser testada sozinha numa pista de treinamento e um iniciante reconhece sua resposta sem decorar uma exceção.

## 7. Passo 6 — Construir fases com módulos editáveis no Godot

Uma fase não precisa ser um mapa inteiro modelado do zero. Ela é uma sequência autoral de trechos reutilizáveis, com ambientação e desafios definidos separadamente.

### Unidade de construção

Manter inicialmente módulos de 28 m, aproveitando o padrão do projeto. Cada módulo terá entrada e saída que encaixam sem diferença de altura ou largura, piso contínuo, cenário lateral, limites e pontos de obstáculos.

Biblioteca inicial: reta livre; jardim; fachada residencial; comércio; obra baixa; obra suspensa; praça; pedestres; entrega; cruzamento; respiro; chegada ao ponto. Variantes cosméticas não mudam colisões.

No protótipo, `build_chunk()` varia comprimento e o streamer posiciona por comprimento-base. **Revisar os encaixes**, pois essa combinação pode produzir sobreposição ou lacuna; confirmar visualmente antes de classificar como defeito. Na biblioteca nova, escolher entre comprimento fixo de 28 m ou encaixe pela posição real dos conectores, nunca misturar contratos.

Estrutura sugerida de cena, a criar:

```text
Trecho28m (Node3D)
  Visual
  Piso
  Decoracao
  Entrada (Marker3D)
  Saida (Marker3D)
  Corredores
  PontosDeObstaculo
  PontosDeMoeda
  Eventos
  LimitesDeGameplay
```

Estrutura sugerida de dados, também futura:

```text
LevelDefinition: id, versão, tema, velocidade, prazo, módulos, eventos, objetivos
ChunkDefinition: cena, comprimento, conectores, corredores, tags de entrada/saída
PatternDefinition: obstáculos, posições, tempos, ações, rotas permitidas
ObstacleDefinition: visual, volumes, movimento, respostas, penalidade
```

Exemplo conceitual de fase, sem ser código para colar diretamente:

```yaml
id: bairro_03
version: 1
theme: bairro_fim_de_tarde
base_speed_mps: 6.0
deadline_seconds: 66.0
chunks: [intro, baixo, baixo, alto, alto, desvio,
         misto, respiro, escolha, revisao, aproximacao, embarque]
chunk_length_m: 28.0
layout_seed: 103
mandatory_boost: false
```

### Como montar cada fase, na prática

1. Escrever uma frase de objetivo: “ensinar deslize e confirmar que pulo não resolve uma barra alta”.
2. Escolher velocidade, duração, prazo inicial e família nova permitida.
3. Selecionar módulos de 28 m; desenhar começo, ensino, prática, combinação, respiro, clímax e chegada.
4. No Godot, criar uma cena do trecho com `Node3D`, piso, marcadores e placeholders; salvar como `.tscn`.
5. Criar o recurso da fase e preencher a lista de módulos e padrões pelo Inspector. Se o editor de recursos ainda não existir, isso é uma tarefa do passo de arquitetura, não uma função já disponível.
6. Instanciar obstáculos nos marcadores, definindo corredor e distância longitudinal. Desenhar explicitamente a rota simples de conclusão.
7. Adicionar rotas opcionais de moedas; elas podem pedir mais habilidade, mas não conduzir a uma colisão inevitável.
8. Rodar validador de continuidade, sobreposição, salto, recuperação e tempo. Repetir a mesma seed durante a revisão.
9. Jogar a fase em blocos simples, sem arte final. Corrigir dificuldade antes de detalhar fachadas.
10. Trocar placeholders pelos modelos aprovados, preservando o contrato dos volumes.
11. Revisar leitura na câmera real, sons, prazo e embarque; gravar uma tentativa limpa e uma com erros.
12. Testar em celular, registrar resultados e congelar uma versão jogável da fase.

**Duas camadas independentes:** cenário determina aparência; padrões determinam desafio. Uma nova fachada não pode fechar uma rota aprovada. A primeira partida tem sequência fixa; replays podem variar cosmética ou escolher padrões compatíveis já validados.

### Validador de caminho

O verificador deve considerar estado do jogador: corredor, posição lateral durante transição, chão/ar, pulo/deslize em recuperação e instante. Basta existir um corredor vazio em cada fotografia da pista? Não: o jogador precisa conseguir chegar a ele no tempo disponível.

Para cada padrão, calcular pelo menos uma sequência legal de ações e conferir transições entre padrões. Revalidar na velocidade máxima e com posições temporais de pedestres/veículos. Boost opcional nunca pode tornar a única saída impossível. Usar colisão varrida e testes em FPS diferentes para impedir atravessamentos.

**Pronto quando:** uma fase nova pode ser montada com módulos e dados, sem editar o controlador central para cada obstáculo.

## 8. Passo 7 — Produzir a fase piloto de 336 metros

Nome de trabalho: **Rua do Ipê — antes das portas fecharem**. Ambiente diretamente guiado pela foto. Velocidade nominal de 6 m/s; prazo inicial de 66 s; 12 módulos de 28 m. Esse piloto valida o produto e depois pode servir como fase 3, pois reúne mais de uma ação.

Corredores: E, C e D, todos na calçada. Rua visível à esquerda, árvores e bancos fora da passagem. Evento = um desafio desenhado; suas posições exatas são ajustadas após validar volumes e reação.

| Módulo | Distância | Situação | Caminho e intenção |
|---|---|---|---|
| 1 | 0–28 m | Largada livre; três moedas no centro | Reconhecer direção e controle; prazo começa após a contagem |
| 2 | 28–56 m | Cone baixo em C por volta de 42 m | Pular ou sair para E/D; primeiro obstáculo legível |
| 3 | 56–84 m | Outro obstáculo baixo em D por volta de 70 m | Repetir ação; rota central permanece segura |
| 4 | 84–112 m | Barreira suspensa em C por volta de 98 m | Ensinar deslize; E/D oferecem alternativa |
| 5 | 112–140 m | Barra alta em D por volta de 126 m | Praticar sem exigir duas ações simultâneas |
| 6 | 140–168 m | Banco em E por volta de 154 m | Confirmar desvio lateral como resposta ao volume sólido |
| 7 | 168–196 m | Cone em C e banco em D na mesma estação, perto de 182 m | Escolher E ou pular em C; não bloquear as três opções |
| 8 | 196–224 m | Respiro, jardim e moedas | Recuperar atenção e apreciar a cidade |
| 9 | 224–252 m | Moedas em rota com barreira em D; C livre | Risco opcional; conclusão não exige a recompensa |
| 10 | 252–280 m | Revisão: obstáculo baixo em C, perto de 266 m | Última decisão clara; sem novidade |
| 11 | 280–308 m | Ônibus visível; guia por moedas | Construir urgência; área ampla |
| 12 | 308–336 m | Embarque sem obstáculo novo | Cruzar a zona no prazo e entrar no ônibus |

Esse piloto é deliberadamente simples. Ele testa animação, luz, legibilidade, controle e conclusão antes de introduzir travessias dinâmicas. Os intervalos não substituem uma validação com o tamanho real dos objetos.

## 9. Passo 8 — Escalar a campanha sem virar repetição

O [catálogo das 50 fases](PLANO_50_FASES_CORRE_PRO_PONTO.md) especifica ambiente, família de obstáculos e desafio central de cada tela. A proposta substitui temas dispersos por uma viagem urbana coerente com a referência.

| Etapa | Conteúdo | Papel |
|---|---|---|
| Fases 1–5 | Bairro ao entardecer | Aprender e confirmar controles |
| Fases 6–10 | Comércio e praça | Introduzir pessoas e escolhas de rota |
| Fases 11–15 | Obras e cruzamentos | Combinar ações e ler movimento |
| Fases 16–20 | Avenida e terminal | Provar domínio; primeira campanha completa |
| Fases 21–30 | Centro histórico e mercado | Novas composições com regras familiares |
| Fases 31–40 | Parque/orla e chuva leve | Variar espaço, superfície e atmosfera |
| Fases 41–50 | Centro movimentado e terminal final | Desafios avançados sem perder clareza |

Começar com 5,5–6,5 m/s nas primeiras fases e testar um teto normal aproximado de 8,5–10 m/s nas avançadas. Não adotar automaticamente os 18 m/s atuais: essa velocidade deve provar que mantém animação, proporção e leitura desejadas. A dificuldade pode subir com combinações, decisões e margem de horário, sem exigir aceleração contínua.

Ritmo básico: apresentação → prática → combinação → respiro → clímax → embarque. Alternar alguns segundos de concentração com trechos de recuperação. Uma fase difícil pode ter menos objetos que outra se suas escolhas forem melhores.

Cada grupo ensina uma família, varia seu uso e encerra com um teste do que foi aprendido. Fases de encerramento não estreiam obstáculos inéditos. Nunca aumentar simultaneamente velocidade, densidade, clima, câmera e precisão exigida.

### Progressão e recompensa

- Vencer libera a próxima fase. Estrelas extras não devem bloquear a campanha básica.
- Primeira estrela: embarcar no prazo. Segunda: concluir sem colisão. Terceira: completar a rota opcional de moedas ou um objetivo de habilidade informado antes da largada.
- Estrelas 2 e 3 podem ser obtidas em tentativas diferentes, registrando a melhor realização de cada objetivo. Interface deve explicar essa regra.
- Moedas compram aparência; a protagonista inicial consegue completar a campanha. Habilidades dos personagens atuais precisam ser normalizadas, reequilibradas ou reservadas para outro modo.
- Fracasso não consome uma energia que obrigue esperar. Repetir deve ser rápido.
- Oferecer assistência opcional com maior antecipação e prazo; indicar regras próprias para medalhas/recordes, preservando a progressão comum.
- Manter ID estável ao migrar as fases. Versionar objetivos e saves, preservar compras e desbloqueios existentes e não remapear silenciosamente uma estrela antiga para um requisito novo.

## 10. Passo 9 — Limpar a interface e dar personalidade sonora

Durante a corrida: pausa no canto superior esquerdo; prazo e progresso em área compacta; moedas no canto superior direito; fôlego discreto. Ações aparecem em botões somente no modo de controle escolhido.

Mensagens de tutorial somem quando a ação foi aprendida. Evitar texto grande a cada mudança de faixa ou pulo, porque compete com o próximo obstáculo. Sinalizar uma novidade por vez.

Menu principal: jogar, mapa, personagem e configurações. Resultado: sucesso/causa da derrota, objetivos atingidos, moedas, repetir e próxima fase. Controles com área confortável no celular, safe areas e suporte a diferentes proporções de tela.

Som: passos sincronizados por superfície; salto/aterrissagem; raspão; moedas discretas; sinal de veículo; cidade ao fundo; ônibus e portas. A música pode ganhar intensidade perto do prazo, sem alterar a velocidade ou o tempo da física. Controle separado de música e efeitos, legendas/sinais visuais para alertas e opção de vibração.

**Pronto quando:** dá para jogar sem som, entender todos os perigos e enxergar a rota sem ler mensagens durante a decisão.

## 11. Passo 10 — Organizar a implementação sem reescrever o projeto inteiro

`game_3d.gd` concentra mais de quatro mil linhas; já existem extrações parciais. Migrar por partes, mantendo uma fase antiga como referência até o novo fluxo estar validado.

| Parte | Aproveitar | Mudança delimitada |
|---|---|---|
| Fluxo da corrida | `game_3d.gd` | Extrair estados, relógio e conclusão para um diretor de corrida |
| Controle | Movimento existente e `physics_handler.gd` | Um único responsável pela posição/colisão do jogador |
| Fases | `phase_data.gd` | IDs estáveis e referências a recursos de fase, não regras por índice espalhadas |
| Cenário | `building_kit.gd`, `world_spec.json` | Módulos com encaixe e decoração independente do gameplay |
| Obstáculos | `obstacle_data.gd`, `world_spawner.gd` | Contratos por família, padrões autorais e validação |
| Personagem | `runner_character.gd` | Modelo aprovado, clips, transições e sincronização de passada |
| Câmera/luz | Configuração e gerenciadores existentes | Um perfil efetivo por qualidade/tema; conferir quem sobrescreve valores |
| HUD | `hud_3d.gd` | Prazo real, progresso e comunicação simplificada |
| Save | `save_data.gd` | Migração versionada de objetivos, desbloqueios e recordes |

Revisar a coexistência de deslocamento visual e corpo físico: o código atual movimenta a representação do jogador e também chama física em outro caminho. O objetivo é uma fonte única de posição e uma regra única de dano, com comportamento igual em 30 e 60 FPS.

Manter a convenção do mundo que se desloca, se ela se mostrar estável. Todos os módulos usam uma distância autoritativa; obstáculos móveis usam transformação e velocidade relativa coerentes com ela. Não trocar para mundo fixo só por preferência arquitetural.

Não incluir reestruturação de anúncios, billing ou integrações externas no primeiro pacote de controle/arte. Validar essas integrações em um marco próprio de lançamento.

## 12. Passo 11 — Criar orçamento de arte e desempenho

Escolher um Android real como aparelho mínimo e outro como aparelho de referência antes de fechar assets. Sem isso, qualquer promessa de fidelidade e FPS será especulação.

| Item | Hipótese inicial de produção | Critério real |
|---|---|---|
| Protagonista | Aproximadamente 15–30 mil triângulos no nível próximo; materiais limitados | Silhueta/deformação aprovadas e custo medido |
| NPCs | Versões mais simples com níveis de detalhe | Quantidade simultânea cabe no orçamento |
| Texturas | 1K–2K para assets importantes; atlas e materiais compartilhados para props | Nitidez na câmera final sem excesso de memória |
| Vegetação | Poucas malhas e baixa sobreposição transparente | Sombras e preenchimento não dominam GPU |
| Cenário ativo | Cerca de 4–6 módulos visíveis inicialmente, ajustados à câmera | Sem surgimento visível de cenário nem reconstruções que travem |
| Meta principal | 60 FPS no aparelho de referência, aproximadamente 16,7 ms por quadro | Medir CPU/GPU, picos e estabilidade térmica |
| Qualidade reduzida | 30 FPS estáveis quando necessário, aproximadamente 33,3 ms | Controle e percurso continuam idênticos |

São orçamentos de partida, não limites oficiais nem resultados já alcançados. Triângulos, resolução e número de objetos isoladamente não explicam o custo total.

Aplicar pooling a obstáculos e módulos frequentes; pré-carregar recursos; agrupar decoração repetida; reduzir materiais; limitar sombras distantes; usar LOD. O Godot oferece geração de níveis de detalhe para cenas 3D importadas, conforme a [documentação de mesh LOD](https://docs.godotengine.org/en/stable/tutorials/3d/mesh_lod.html).

A troca de qualidade altera sombras, resolução, vegetação e efeitos, nunca o tempo de reação, collider ou velocidade. O cenário distante pode ser simples, porque a prioridade é personagem + piso próximo + próximos obstáculos.

Não decidir que a imagem exige 4K em tudo, GI dinâmica ou centenas de objetos físicos. A fase piloto deve demonstrar quais recursos realmente melhoram o resultado na tela do celular.

## 13. Passo 12 — Testar diversão, justiça e semelhança visual

### Testes funcionais necessários

- Largar, pausar, retomar, ir para segundo plano, morrer, repetir e concluir.
- Chegar antes, exatamente no prazo e depois; testar impacto e chegada no mesmo tick.
- Trocar de corredor durante pulo, deslize, recuperação e coleta.
- Confirmar cada ação válida e inválida da tabela de obstáculos.
- Conferir que nenhum collider fica para trás quando o cenário recicla.
- Jogar com 30 e 60 FPS e simular quedas de desempenho; verificar ausência de atravessamentos.
- Confirmar que toda fase tem solução sem dash, itens pagos ou personagem específico.
- Validar save antigo, save novo, estrelas, desbloqueios e interrupção durante gravação.
- Conferir legibilidade com efeitos reduzidos, sem áudio e em telas pequenas.

### Playtest com pessoas

Fazer sessões curtas com 5–8 pessoas que não montaram a fase. Observar a primeira tentativa sem explicar tudo. Depois perguntar: “o que precisava fazer?”, “por que perdeu?”, “qual obstáculo foi confuso?” e “quis tentar de novo?”.

Registrar por tentativa: fase/versão/seed, duração, distância, ações, impactos por obstáculo e módulo, tempo restante no embarque, abandono, FPS e tipo de controle. Aproveitar a instrumentação local existente antes de criar dependência de servidor.

Alvos iniciais para orientar iteração, sem valor estatístico definitivo:

- Tutorial: maioria compreende o objetivo e vence em até duas tentativas.
- Fases iniciais: 70–90% de conclusão após conhecer os comandos.
- Intermediárias: 50–75%; avançadas: 35–60% nas primeiras tentativas.
- A pessoa consegue atribuir a derrota a uma decisão visível, não a um perigo que apareceu tarde.
- Repetir a mesma fase produz melhoria observável, indicando aprendizado em vez de sorte.

Se uma falha se concentrar em um obstáculo, revisar sinal, espaço e regra antes de tornar a fase inteira mais fácil. Não aumentar densidade só porque jogadores experientes completaram uma fase de aprendizado.

### Aprovação visual

Guardar capturas reais nos mesmos pontos: largada, trecho de árvores, fachadas, obstáculo, corrida e embarque. Comparar com a referência em cinco dimensões: composição, silhueta, proporções, luz e materiais. Olhar também vídeo, porque uma imagem parada não revela pés deslizando, stutter ou transições ruins.

**Condição para expandir:** o usuário reconhece a direção visual desejada em gameplay e os testadores reconhecem as regras. Não multiplicar uma fase que ainda não passou nesses dois critérios.

## 14. Ordem de produção, responsáveis e esforço

Estimativa de planejamento, não orçamento fechado. Unidade: pessoa-semana de trabalho concentrado de alguém já familiarizado com sua função. Uma única pessoa executa as frentes principalmente em sequência; arte encomendada, aprendizado e retrabalho podem ampliar bastante o calendário.

| Marco | Entrega verificável | Depende de | Funções | Esforço inicial |
|---|---|---|---|---|
| M0 | Baseline, engine/renderer confirmados, aparelho e escopo fixados, auditorias recuperadas | — | Programação/QA | 0,5–1 semana |
| M1 | Controle, colisões e prazo real em pista simples | M0 | Programação/design | 1–2 semanas |
| M2 | Protagonista e trecho visual próximos da referência | M0 e câmera inicial de M1 | Arte 3D/animação/arte técnica | 3–5 semanas |
| M3 | Recursos de fase, 12 módulos-base e validador de percurso | Contratos de M1 | Programação/level design | 2–3 semanas |
| M4 | Piloto de 336 m com arte, som e embarque, testado no celular | M1–M3 | Integração/QA | 1–2 semanas |
| M5 | Cinco primeiras fases revisadas com jogadores | M4 aprovado | Level design/QA | 1–2 semanas |
| M6 | Campanha de 20 fases, variações de cenário e progressão | M5 | Design/arte/programação/QA | 3–5 semanas |
| M7 | Otimização, saves, acessibilidade e candidato de lançamento | M6 | Programação/QA | 2–3 semanas |
| M8 | Expansão de 21–50 com novos padrões e ambientes | M7 estável e dados de uso | Design/arte/QA | 4–8 semanas adicionais |

Soma aproximada até M7: **13,5–23 pessoa-semanas**. Isso não é promessa de prazo e não inclui folgas contratuais; prever margem adicional de 20–30% após dimensionar assets e equipe. O piloto completo corresponde a M0–M4, cerca de 7,5–13 pessoa-semanas. Algumas frentes podem ocorrer em paralelo se houver pessoas diferentes.

Não estimar dinheiro sem saber equipe, disponibilidade, aparelho-alvo e origem dos assets. O maior fator de incerteza é a produção da protagonista/animação e sua qualidade real na câmera final.

## 15. Lista objetiva de entregáveis

### Para aprovar o piloto

- [ ] Meta visual definida a partir da imagem, com comparação 1:1 e 9:16.
- [ ] Uma protagonista aprovada, GLB e fonte editável, rig e clips essenciais.
- [ ] Câmera e escala consistentes entre pessoa, piso, edifícios e ônibus.
- [ ] Um kit urbano: 6–8 fachadas/variações, piso/guia, 3 árvores/variações, banco, poste, canteiro e ponto.
- [ ] Um ônibus com porta/embarque; pelo menos dois carros para contexto visual.
- [ ] Obstáculos básicos: cone/caixa, banco/floreira, barra suspensa, buraco e bloqueio alto.
- [ ] Três corredores claros; comandos e colliders coerentes.
- [ ] Prazo contado desde a largada, penalidade e resultados corretos.
- [ ] Doze módulos montáveis e uma fase de 336 m com roteiro fixo.
- [ ] HUD de corrida, resultado, pausa e repetição rápida.
- [ ] Sons essenciais e alertas compreensíveis sem áudio.
- [ ] Capturas e vídeo de gameplay no aparelho de referência.
- [ ] Playtest com iniciantes e ajustes registrados.

### Para aprovar 20 fases

- [ ] Todos os obstáculos dinâmicos previstos têm sinais, rotas e volumes testados.
- [ ] Cada fase possui objetivo, receita de módulos, parâmetros, rota válida e replay de QA.
- [ ] Campanha abre fases por conclusão e preserva progresso.
- [ ] Economia de desenvolvimento removida do perfil de lançamento.
- [ ] Renderers e níveis de qualidade produzem a mesma experiência jogável.
- [ ] Nenhum trecho exige publicidade, compra ou habilidade exclusiva.
- [ ] Testes de save, ciclo do app, telas, calor e desempenho concluídos.
- [ ] Documentação descreve o executável real, sem chamar placeholder de sistema pronto.

### Para ampliar até 50 e publicar

- [ ] Fases 21–50 implementadas e validadas em lotes de cinco.
- [ ] Novos ambientes seguem a mesma direção de arte.
- [ ] Modo infinito, se mantido, usa apenas combinações validadas e tem escopo próprio.
- [ ] Integrações comerciais opcionais foram testadas separadamente do núcleo.
- [ ] Requisitos vigentes da loja e da versão escolhida do Godot foram conferidos no momento da publicação.
- [ ] Materiais promocionais são capturas reais do produto entregue.

**Primeira tarefa concreta de implementação:** montar a pista simples do piloto, corrigir a regra de tempo/embarque e aprovar câmera + protagonista em um trecho de 28 m. Esses resultados tornam o restante do projeto mensurável.

## 16. Referências técnicas e limites desta proposta

- Código local inspecionado: `project.godot`, `scenes/main.tscn`, `scripts/game_3d.gd`, `scripts/phase_data.gd`, `scripts/obstacle_data.gd`, `scripts/world_spawner.gd`, `scripts/physics_handler.gd`, `scripts/building_kit.gd`, `scripts/runner_character.gd`, `scripts/scenario_data.gd`, `scripts/lighting_handler.gd`, `scripts/hud_3d.gd`, `resources/game_balance.tres` e `resources/world_spec.json`.
- Pontos de entrada para a implementação: `_build_course`, `_update_run`, `_resolve_entity`, `_update_player`, `_catch_bus`, `_finish_run`, `ChunkStreamer` e `PhaseData.get_phase`.
- [Godot 4.7 — diferenças entre renderers](https://docs.godotengine.org/en/4.7/tutorials/rendering/renderers.html).
- [Godot — importação de cenas 3D](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/index.html).
- [Godot — mesh LOD](https://docs.godotengine.org/en/stable/tutorials/3d/mesh_lod.html).

As metas numéricas de duração, velocidade, orçamento, dificuldade e prazo de produção são propostas a validar. A imagem estabelece o destino visual; só uma execução no aparelho pode confirmar a distância real entre o protótipo e esse destino.
