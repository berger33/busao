# Plano das 50 fases — Corre pro Ponto

Proposta de campanha complementar ao [blueprint de produção](BLUEPRINT_CORRE_PRO_PONTO.md), de 20/09/2026.

**Este é o roteiro de design a produzir, não uma descrição de 50 mapas já existentes.** Os nomes abaixo são nomes de trabalho. Manter os IDs e criar uma migração explícita dos dados atuais. As fases 1–20 formam a primeira campanha; 21–50 são expansão, construída somente após validar o núcleo.

Cada fase terá um recurso de dados próprio e uma lista autoral de módulos. A aparência pode variar, mas a regra de cada obstáculo permanece constante. Nenhuma conclusão normal exige moedas, anúncio, personagem comprado ou boost.

## Como ler e utilizar o catálogo

- Comprimentos são múltiplos de 28 m para aproveitar o kit de quarteirões.
- Velocidades e margens são **hipóteses de primeiro balanceamento**.
- A coluna “base + margem” mostra segundos nominais de percurso e folga. Exemplo: 56 + 10 resulta em prazo inicial de 66 s.
- Base nominal = distância / velocidade, arredondada para cima. Depois da montagem, substituir pelo tempo medido de uma rota válida, incluindo efeitos de superfície e trajetória.
- A margem de horário não é a janela de reação. Manter antecipação visual suficiente em todas as fases, independentemente da folga do ônibus.
- “Clímax” significa a combinação mais exigente da fase, colocada antes da aproximação final. A chegada sempre oferece espaço para entender o embarque.
- Toda receita inclui introdução, desafio, respiro e aproximação. Não preencher automaticamente todos os metros com perigos.
- Obstáculos são oportunidades de decisão; alguns têm caminho alternativo. Não exigir todos os pulos/deslizes se houver rota mais simples.
- Nas travessias, veículos têm trajetórias e janelas previsíveis. A corrida continua automática: o jogador escolhe a passagem livre, sem precisar de um comando de freio inexistente.

## Fases 1–5 — A rua da referência

Mesmo bairro, luz de fim de tarde, piso claro, rua à esquerda, árvores e fachadas de dois/três pavimentos. Produzir este conjunto antes de ampliar arte e sistemas.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 1 | Saiu atrasada | 224 / 5,5 | 41 + 14 s | Aprender troca de corredor e pulo; cones baixos isolados; moedas guiam uma rota ampla | Dois cones em estações separadas, sempre com desvio disponível |
| 2 | A praça do bairro | 280 / 5,8 | 49 + 12 s | Distinguir obstáculo baixo de volume sólido; cones, bancos e floreiras | Banco ocupa um corredor; cone ocupa outro; terceiro livre |
| 3 | Rua do Ipê | 336 / 6,0 | 56 + 10 s | Piloto do blueprint; introduzir deslize; cones, bancos e barreiras suspensas | Escolha entre rota livre e rota de moedas sob uma barreira |
| 4 | Remendo na calçada | 336 / 6,0 | 56 + 12 s | Introduzir buraco curto com bordas sinalizadas; cones e barra já conhecidos | Buraco seguido de banco, com aterrissagem e tempo de troca garantidos |
| 5 | Primeiro compromisso | 364 / 6,2 | 59 + 10 s | Revisão das quatro primeiras; nenhum obstáculo novo | Baixo → alto → desvio, com recuperação entre ações e respiro antes do ponto |

**Lote aprovado quando:** iniciantes compreendem o ônibus, reconhecem as três respostas e a fase 3 já sustenta a comparação visual com a imagem.

## Fases 6–10 — Comércio e praça

Reaproveitar o bairro; adicionar vitrines, placas, comércio e pequenas entregas. Introduzir movimento humano sem transformar a calçada numa multidão opaca.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 6 | Na porta da padaria | 364 / 6,2 | 59 + 12 s | Hidrante, lixeira e orelhão como bloqueios altos; cones como revisão | Alternância de bloqueio alto em E e D, com rota C legível |
| 7 | Passagem de pedestres | 364 / 6,3 | 58 + 12 s | Primeiro pedestre atravessa após preparar o movimento; bancos fixos | Pedestre cruza um corredor enquanto uma rota lateral permanece livre |
| 8 | Hora da entrega | 392 / 6,4 | 62 + 11 s | Carrinho de entrega lateral, com aviso; lixeiras e pedestres | Carrinho e banco criam uma escolha anunciada entre dois caminhos |
| 9 | A van da esquina | 392 / 6,5 | 61 + 11 s | Veículo parado invade a borda; desviar pelo corredor aberto; nunca saltar o teto | Van e barreira baixa em estações separadas |
| 10 | Feira de sábado | 420 / 6,5 | 65 + 10 s | Revisão de movimento lateral e bloqueios; faixa de corrida limpa entre barracas | Carrinho → pedestre → desvio de banco; intervalo de recuperação mantido |

**Lote aprovado quando:** pedestres são previsíveis e nenhuma decoração de comércio se confunde com a passagem disponível.

## Fases 11–15 — Obras e travessias

Adicionar andaimes, cones de obra e dois módulos de cruzamento. Manter cores e iluminação da cidade; a fase continua legível ao primeiro olhar.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 11 | Sob o andaime | 392 / 6,6 | 60 + 12 s | Andaime com vão para deslize; apoios laterais; buracos conhecidos | Barra suspensa seguida de desvio, nunca salto obrigatório sob a barra |
| 12 | Poças da manhã | 392 / 6,6 | 60 + 12 s | Poças bem delimitadas; piso molhado leve; sem escorregão aleatório | Rota seca simples versus moedas com salto sobre poça |
| 13 | Ciclovia na praça | 420 / 6,8 | 62 + 10 s | Ciclista cruza à frente com sinal visual; floreiras limitam um corredor | Ciclista em janela fixa, seguido de trecho livre e cone baixo |
| 14 | Olha a moto | 420 / 6,8 | 62 + 11 s | Moto atravessa no cruzamento; aviso visual e sonoro; caminho seguro explícito | Dois cruzamentos com comportamentos ensinados separadamente |
| 15 | Desvio de obra | 448 / 7,0 | 64 + 9 s | Combinar andaime, buraco, poça e passagem dinâmica | Pulo → trecho livre → deslize → escolha de corredor no cruzamento |

**Lote aprovado quando:** o validador confirma janelas temporais e a execução humana confirma que os avisos são perceptíveis com som desligado.

## Fases 16–20 — Avenida e primeiro terminal

Uma avenida mais aberta, ponto maior e terminal reconhecível. Aumentar a intensidade por combinações, preservando espaços de recuperação.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 16 | O caramelo da praça | 420 / 7,0 | 60 + 11 s | Cachorro prepara e cruza uma passagem; pedestres e bancos | Cruzamento do cachorro seguido de desvio anunciado; sem perseguição surpresa |
| 17 | Entregas da avenida | 448 / 7,2 | 63 + 10 s | Van, caixas baixas e carrinhos; praticar leitura de volumes | Rota rápida com salto e rota simples com desvio |
| 18 | Travessia do caminhão | 448 / 7,2 | 63 + 10 s | Caminhão/ônibus cruza uma área sinalizada; corredor de escape amplo | Veículo ocupa o cruzamento enquanto uma passagem lateral continua válida |
| 19 | Últimas quadras | 476 / 7,4 | 65 + 9 s | Combinar pedestre, obra e entrega em ordem conhecida | Três decisões separadas; último respiro revela o ponto |
| 20 | Peguei o ônibus! | 504 / 7,5 | 68 + 8 s | Encerrar campanha inicial com famílias já dominadas; três pontos de fôlego | Revisão em três blocos com recuperação; embarque marcante, sem truque final |

**Lote aprovado quando:** fase 20 é vencível sem bônus, tem derrota explicável e conclusão recompensadora. Aqui já existe um produto pequeno completo para testar com público.

## Fases 21–25 — Centro histórico

Expansão de arquitetura: fachadas com molduras, praça, piso e mobiliário próprios. O piso decorativo não altera velocidade até isso ser explicitamente introduzido.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 21 | Rua das fachadas | 448 / 7,4 | 61 + 11 s | Reentrada mais tranquila; bancos, floreiras e pedestre | Reconhecer regras familiares numa nova aparência |
| 22 | Entrega na livraria | 476 / 7,5 | 64 + 10 s | Caixas e carrinho; vitrines como pano de fundo | Sequência de volumes baixos e altos com uma rota simples |
| 23 | Foto na praça | 476 / 7,6 | 63 + 10 s | Dois pedestres com trajetórias separadas e pausas visíveis | Cruzamentos alternados, nunca simultâneos fechando tudo |
| 24 | Restauração da fachada | 504 / 7,6 | 67 + 9 s | Andaimes, vala curta e cone | Deslize → respiro → salto → troca lateral |
| 25 | O ponto da igreja | 504 / 7,7 | 66 + 8 s | Revisão do centro histórico; ponto como marco arquitetônico | Obra e pedestres em três padrões aprovados |

## Fases 26–30 — Mercado e entregas

Adicionar barracas e novos modelos cosméticos para obstáculos existentes. Não criar regra diferente para cada fruta, caixa ou bancada.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 26 | Abertura do mercado | 476 / 7,6 | 63 + 11 s | Barracas delimitam rota; caixas baixas e banco/bancada sólida | Separar obstáculo de decoração sem elevar precisão |
| 27 | Corredor de entregas | 504 / 7,7 | 66 + 10 s | Carrinhos cruzam em intervalos regulares | Dois eventos laterais com sentidos alternados |
| 28 | Toldos da feira | 504 / 7,8 | 65 + 10 s | Toldo usa a regra da barreira alta; caixas usam pulo | Alternância salto/deslize com espaço de recuperação |
| 29 | A esquina do mercado | 532 / 7,8 | 69 + 9 s | Van de entrega, pedestres e cruzamento | Escolha de rota antecipada antes de passar pela van |
| 30 | Fechou a feira | 532 / 8,0 | 67 + 8 s | Revisão do mercado, sem fechar a visão com barracas | Combinações mais longas e um grande respiro antes do ônibus |

## Fases 31–35 — Parque e orla

Luz mais aberta, árvores, canteiros e horizontes amplos. Preservar sombra de contato, escala humana e estilo das fachadas nas transições.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 31 | Alamedas do parque | 476 / 7,8 | 62 + 11 s | Bancos, floreiras e cones; início de capítulo com menor pressão | Desvios largos numa ambientação nova |
| 32 | Passeio com o caramelo | 504 / 8,0 | 63 + 10 s | Cachorro e pedestres cruzam em eventos separados | Animal anuncia ação antes de uma sequência conhecida |
| 33 | Ciclistas da orla | 504 / 8,0 | 63 + 10 s | Ciclistas com janelas previsíveis e longas linhas de visão | Dois ciclistas em momentos diferentes; escape lateral disponível |
| 34 | Manutenção do calçadão | 532 / 8,1 | 66 + 9 s | Vala, barra e cone; pintura do piso não mascara buraco | Pulo e deslize combinados com rota alternativa de moedas |
| 35 | O ônibus da orla | 560 / 8,2 | 69 + 8 s | Revisão de parque, ciclovia e manutenção | Série em três blocos; aproximação limpa com vista do ônibus |

## Fases 36–40 — Depois da chuva

Chuva leve e poças, sem esconder perigos com reflexos, gotas ou névoa. O clima muda apresentação; a introdução da superfície lenta é separada e anunciada.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 36 | Chuva passageira | 476 / 7,8 | 62 + 12 s | Clima novo com desafios fáceis; poças e cones | Reaprender leitura visual sem elevar velocidade |
| 37 | Procurando piso seco | 504 / 8,0 | 63 + 11 s | Poça com efeito de velocidade explícito; rota seca garantida | Rota de recompensa versus rota de conclusão |
| 38 | Entrega debaixo d'água | 532 / 8,1 | 66 + 10 s | Carrinhos e pedestres, com aviso reforçado | Um evento dinâmico seguido de solo seguro |
| 39 | Obra molhada | 532 / 8,2 | 65 + 9 s | Buraco, barra e poças fora das aterrissagens obrigatórias | Combinação que testa leitura, não aderência aleatória |
| 40 | O sol voltou | 560 / 8,3 | 68 + 8 s | Revisão; clima clareia gradualmente sem mudar exposição abruptamente | Último trecho firme com sequência conhecida e ônibus ao sol |

Nas fases com redução de velocidade, os tempos acima são apenas nominais. Medir a rota seca legal ou incorporar o custo real da superfície ao tempo de referência; não manter um prazo que só seria possível com velocidade constante.

## Fases 41–45 — Centro movimentado

Mais vida na cidade, mas limitar a quantidade de ameaças simultâneas. Multidão de fundo pode usar animação simplificada e não tem colisão de gameplay.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 41 | A saída do escritório | 504 / 8,2 | 62 + 10 s | Pedestres, floreiras e bancos; volta ao tempo seco | Dois grupos de decisões, com distância clara entre eles |
| 42 | Avenida das entregas | 532 / 8,3 | 65 + 9 s | Van, caixas e carrinho | Escolha antecipada com recompensa opcional em rota mais técnica |
| 43 | Sinal aberto | 560 / 8,4 | 67 + 9 s | Moto, ciclista e veículo grande em cruzamentos separados | Três leituras de movimento, nunca três perigos simultâneos |
| 44 | Quadra em reforma | 560 / 8,5 | 66 + 8 s | Andaime, buraco e bloqueio alto | Padrão longo com respiros internos e saída ampla |
| 45 | Hora do pico | 588 / 8,6 | 69 + 7 s | Revisão do centro; arte movimentada, caminho limpo | Sequência de obra e travessia com aviso suficiente no maior ritmo |

## Fases 46–50 — Caminho do terminal final

Terminal visível como destino, ônibus e sinalização recorrentes. A tensão vem do domínio combinado e da folga menor, não de sustos ou regras novas.

| Fase | Nome de trabalho | Metros / m/s | Base + margem | Objetivo e obstáculos | Clímax previsto |
|---|---|---|---|---|---|
| 46 | Placas para o terminal | 532 / 8,5 | 63 + 9 s | Reapresentar sinalização; lixeira, banco e pedestre | Escolher corredor com antecedência; placas não escondem perigos |
| 47 | Conexão apertada | 560 / 8,6 | 66 + 8 s | Caixas, barra e carrinho | Duas combinações conhecidas unidas por intervalo seguro |
| 48 | Travessia dos ônibus | 588 / 8,7 | 68 + 8 s | Ônibus de tráfego em janelas sinalizadas; ponto de destino distinto | Evento grande, legível e determinístico; sem salto sobre veículo |
| 49 | Falta uma quadra | 588 / 8,8 | 67 + 7 s | Revisão de todas as famílias, escolhidas em blocos | Maior exigência de planejamento; nenhuma redução inesperada de visão |
| 50 | A última chamada | 616 / 9,0 | 69 + 6 s | Exame final em três atos, sem novidade; três pontos de fôlego | Sequência difícil já conhecida → respiro → embarque e conclusão especial |

O teto de 9 m/s desta tabela é uma hipótese conservadora frente aos 18 m/s atuais. Se os testes demonstrarem que a corrida precisa de outro ritmo, ajustar velocidade, animação, extensão e espaçamento juntos. Não acelerar o jogo isoladamente.

## Receita de módulos por tamanho de fase

Esta distribuição ajuda a montar a primeira versão de cada percurso. “Clímax” contém os desafios finais; “aproximação” já mostra o ônibus; “embarque” não tem novo obstáculo. Dentro dos blocos de desafio, incluir pequenos intervalos de descanso.

| Módulos / distância | Introdução | Ensino ou revisão | Prática | Combinações | Respiro | Clímax | Aproximação + embarque |
|---|---:|---:|---:|---:|---:|---:|---:|
| 8 / 224 m | 1 | 2 | 1 | 0 | 1 | 1 | 2 |
| 10 / 280 m | 1 | 2 | 2 | 1 | 1 | 1 | 2 |
| 12 / 336 m | 1 | 2 | 3 | 2 | 1 | 1 | 2 |
| 13 / 364 m | 1 | 2 | 3 | 2 | 1 | 2 | 2 |
| 14 / 392 m | 1 | 2 | 3 | 3 | 1 | 2 | 2 |
| 15 / 420 m | 1 | 2 | 3 | 3 | 2 | 2 | 2 |
| 16 / 448 m | 1 | 2 | 4 | 3 | 2 | 2 | 2 |
| 17 / 476 m | 1 | 2 | 4 | 4 | 2 | 2 | 2 |
| 18 / 504 m | 1 | 2 | 4 | 4 | 2 | 3 | 2 |
| 19 / 532 m | 1 | 2 | 5 | 4 | 2 | 3 | 2 |
| 20 / 560 m | 1 | 2 | 5 | 5 | 2 | 3 | 2 |
| 21 / 588 m | 1 | 2 | 5 | 5 | 3 | 3 | 2 |
| 22 / 616 m | 1 | 2 | 6 | 5 | 3 | 3 | 2 |

Na fase piloto, seguir o roteiro específico do blueprint. As demais receitas são distribuições de espaço, não uma ordem fixa de todos os blocos; intercalar respiros evita concentrar toda a recuperação em um único ponto.

## Biblioteca inicial de padrões

| Código | Composição | Solução simples | Variação de domínio |
|---|---|---|---|
| P01 | Objeto baixo em C | Mudar para E/D | Pular e pegar moeda |
| P02 | Bloqueio sólido em E | Usar C/D | Entrar em C sem correção tardia |
| P03 | Barra alta em C | Usar E/D | Deslizar sob a barra |
| P04 | Buraco curto em D | Usar E/C | Pular e pousar em área livre |
| P05 | Baixo em C + sólido em D | Usar E | Pular em C |
| P06 | Barra em E; baixo em C em estação posterior | Usar D nos dois momentos | Deslizar e depois pular, com recuperação |
| P07 | Pedestre de D para C; E livre | Antecipar E | Passar após a trajetória encerrar, se validado |
| P08 | Carrinho cruzando C; D livre | Antecipar D | Coletar em E antes de sair |
| P09 | Veículo parado ocupa E | Usar C/D | Escolher rota de moedas em D |
| P10 | Veículo atravessa trecho específico | Rota lateral sinalizada | Passagem temporal opcional, após prova de viabilidade |
| P11 | Poça em E; C seco | Usar C | Pular a poça pela recompensa |
| P12 | Duas famílias conhecidas em estações consecutivas | Rota desenhada com recuperação | Rota opcional exige duas ações |

Esses padrões são especificações de intenção. Converter cada um em dados com comprimentos, posições, tempo de movimento e volumes reais. Não tratá-los como algoritmos já implementados ou automaticamente seguros.

## Ficha obrigatória de cada fase

Antes de marcar uma tela como pronta, preencher:

```text
ID estável e versão:
Nome, capítulo e objetivo do jogador:
Tema visual e horário:
Novidade ensinada, ou revisão:
Comprimento, velocidade e velocidade máxima de boost:
Lista ordenada de módulos e padrões:
Posições/tempos dos obstáculos e coletáveis:
Rota simples válida e rotas de recompensa:
Janelas mínimas de leitura, ação e recuperação:
Tempo medido da rota legal sem boost:
Prazo do ônibus e penalidades:
Objetivos de estrelas:
Sinais visuais e sonoros:
Critério de conclusão e de derrota:
Seed fixa e versões dos assets:
Resultados do validador:
Captura/vídeo de uma conclusão real:
Resultados do playtest e pendências:
Responsável e status:
```

## Sequência de entrega

1. Implementar e avaliar a fase piloto 3.
2. Derivar 1, 2, 4 e 5 usando os módulos aprovados; testar a ordem de aprendizagem.
3. Produzir 6–10 e acrescentar movimento lateral de pedestres/carrinhos.
4. Produzir 11–15 e validar travessias e ações combinadas.
5. Produzir 16–20, fechar progressão e medir repetição/diversão.
6. Só então montar cada novo lote de cinco fases da expansão, liberando por qualidade comprovada.

Entre lotes, revisar índices de falha por obstáculo e trecho, tempo restante e desistência. Se uma fase repetida não ensina nada nem oferece combinação nova, redesenhá-la antes de adicionar mais conteúdo.
