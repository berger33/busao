# ESTUDO COMPARATIVO E PLANO DE TRANSFORMAÇÃO GRÁFICA REALISTA 3D
**Comparativo Técnico:** `image-1.png` (Estado Atual no Motor) vs. `abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg` (Referência Canônica AAA)  
**Data:** 20 de Setembro de 2026  
**Autor:** Engenharia Gráfica e Pipeline de Arte — *Corre pro Ponto*  
**Objetivo:** Diagnóstico aprofundado de cada deficiência visual e estruturação detalhada da transformação completa para atingir 100% de paridade com a referência artística.

---

## 1. Sumário Executivo & Diagnóstico Visual

A imagem **`image-1.png`** representa o estado renderizado em tempo real no Godot Engine. Ela evidencia que, embora o esqueleto básico e os sistemas lógicos estejam operacionais, a representação visual permanece em um nível **geométrico primitivo e esquemático (low-poly / placeholder)**.

A imagem **`abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`** define a meta visual inegociável: um jogo de corrida infinita mobile de altíssima fidelidade (padrão *Subway Surfers 2 / AAA Mobile*), combinando:
1. Uma **corredora atlética de proporções anatômicas naturais**, com vestimenta esportiva técnica com microdobras reais de tecido, calça legging de compressão fosca, tênis de corrida com entressola esculpida e rabo de cavalo dinâmico.
2. Um **ambiente urbano vivo e denso**: calçada com lajes de concreto intertravadas em padrão retangular (*running bond*), canteiros de árvores com moldura de granito e terra escura, meio-fio chanfrado de 15 cm com sarjeta e bueiro de ferro fundido.
3. **Pista viária realista**: asfalto cinza-escuro com agregados minerais finos, marcas de desgaste de pneus, faixas centrais duplas amarelas com desgaste natural, cone de sinalização com faixa refletiva e veículos modernos proporcionais (hatchback branco com pintura automotiva e vidro temperado).
4. **Iluminação cinematográfica de fim de tarde (*Golden Hour*)**: sol rasante lateral a ~28° gerando sombras longas e suaves cortando a calçada diagonalmente, névoa volumétrica suave no ponto de fuga da avenida e contraste cromático quente/frio.
5. **HUD minimalista e elegante**: interface desobstruída com tipografia limpa, cápsula dourada para moedas e controles semi-transparentes.

---

## 2. Análise Comparativa Detalhada: Elemento por Elemento

### 2.1. O Personagem Corredor

| Atributo | Estado Atual (`image-1.png`) | Meta Artística (`abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`) | Causa Técnica & Solução |
| :--- | :--- | :--- | :--- |
| **Pernas e Articulações** | Dois pilares cilíndricos/retangulares pretos desconectados, sem joelho definido, sem curvas musculares. Parecem próteses mecânicas rígidas de Lego. | Pernas anatômicas contínuas: quadríceps torneados afinando no joelho (relevo patelar visível), panturrilha com volume muscular (gastrocnêmio) afinando no tornozelo e tendão de Aquiles. | **Causa:** Uso de `pilar_z()` cilíndrico desconectado para coxa e panturrilha. **Solução:** Modelar as pernas como uma malha contínua orgânica única com pesagem suave de vértices (*smooth skin weighting*) entre `thigh` e `calf`. |
| **Calçados (Tênis)** | Blocos pretos achatados (`caixa()`), sem distinção de sola ou amortecedor. | Tênis de corrida modernos: entressola grossa de espuma EVA branca com inclinação de amortecimento no calcanhar (~3,5 cm) e curva de impulsão na ponta (*toe rocker*), cabedal cinza/azul com cadarços e meia cano curto branca visível acima do tornozelo. | **Causa:** O calçado atual é um paralelepípedo primitivo pintado de preto. **Solução:** Modelar geometria de tênis com 3 zonas de material (sola preta antiderrapante, entressola branca grossa, cabedal de tecido respirável) e meias esportivas. |
| **Tronco e Camiseta** | Bloco rosa deformado, com ondulações e protuberâncias irregulares nas costas e ombros parecendo um travesseiro murcho ou caroços. | Camiseta esportiva atlética ajustada ao corpo (cor rosa/coral suave `#e06b85`), com silhueta feminina natural (cintura atlética, ombros torneados, mangas curtas delineadas) e microdobras de tecido nos pontos de tensão da passada. | **Causa:** O tronco foi montado empilhando elipsoides (`Pelvis`, `CinturaBaixa`, `PeitoMedio`, `Ombros`) sem coordenadas de UV. A aplicação do normal map em malha sem UV causou deformações monstruosas de sombreamento. **Solução:** Modelar o torso como malha única e contínua com UV unwrapping cilíndrico relaxado e normais suaves. |
| **Braços e Mãos** | Braços minúsculos, colados ao tronco ou quase invisíveis, sem definição de cotovelo ou antebraço. | Braços proporcionais em movimento sagital ativo: cotovelos flexionados a ~85°, bíceps e antebraços torneados, punho relaxado semi-cerrado típico de corredor de alta performance. | **Causa:** Braços feitos com cilindros encurtados com rotação estática. **Solução:** Malha de braço orgânica conectada aos deltoides, pesagem interpolada de vértices no cotovelo e animação com arco de balanço sagital profundo. |
| **Cabeça e Cabelo** | Massa escura amorfa no topo da cabeça, sem rabo de cavalo nítido, parecendo uma deformidade irregular. | Cabeça esculpida com proporção craniana real, elástico de cabelo contrastante no topo/occipital e rabo de cavalo fluido em formato de gota que balança dinamicamente para trás e para os lados conforme o ritmo da corrida. | **Causa:** O cabelo atual é uma união de duas icoesferas estáticas. **Solução:** Modelar a base capilar ajustada ao crânio + tufo central com elástico + mecha longa de rabo de cavalo curvada para trás com simulação elástica mola-amortecedor (*spring-damper*). |
| **Sombra Projetada** | Disco acinzentado estático embaixo dos pés e sombra fantasma recortada sem forma definida. | Sombra longa, nítida e elegante cortando a calçada diagonalmente para a direita, revelando o contorno exato da passada (perna de apoio e perna de impulso). | **Causa:** Sombra gerada por quad procedural simples no chão. **Solução:** Sombra direcional real via Cascaded Shadow Maps (CSM) com 4 splits calibrados e bias nítido. |

---

### 2.2. A Calçada e Pavimentação

| Atributo | Estado Atual (`image-1.png`) | Meta Artística (`abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`) | Causa Técnica & Solução |
| :--- | :--- | :--- | :--- |
| **Padronagem dos Blocos** | Grade infinita de azulejos quadrados bege claros, com linhas pretas grossas e repetitivas (aspecto de piso de banheiro). | Lajes retangulares de concreto pré-moldado (~40 cm × 20 cm) dispostas em padrão intercalado transversal (*running bond / amarração*). | **Causa:** Textura procedural de grade quadrada aplicada diretamente em plano liso. **Solução:** Geometria de lajes retangulares chanfradas com MultiMesh ou textura PBR 4K com mapas de Normal e ORM com chanfro e juntas rebaixadas com areia. |
| **Variação e Textura do Material** | Cor sólida uniforme e plana, sem variação de tom pedra por pedra. | Variações orgânicas de cinza-quente, areia e concreto desgastado entre os blocos, com porosidade mineral e leve acúmulo de sujeira nas juntas. | **Causa:** Shader sem variação por instância. **Solução:** Variação cromática por vértice/instância no MultiMesh e mapa de aspereza PBR com microporosidades. |
| **Canteiros de Árvores** | A calçada é totalmente lisa até a sarjeta; as árvores nascem flutuando ou coladas no chão. | Canteiros rebaixados quadrados (1,6 m × 1,6 m) ao longo da calçada, cercados por moldura de granito de 10 cm, com terra escura fofa e pequenas tufas de grama/ervas daninhas na base. | **Causa:** Inexistência do elemento canteiro na geração do quarteirão. **Solução:** Implementar módulo de canteiro retangular com moldura e terra orgânica nos nós de árvores em `building_kit.gd`. |
| **Meio-fio e Sarjeta** | Bloco cinza genérico de quina reta separando a pista. | Meio-fio de concreto chanfrado a 45° com 15 cm de desnível, sarjeta de drenagem pluvial e bueiro de ferro fundido com grelhas vazadas na junção com o asfalto. | **Causa:** Guia gerada como um BoxMesh sem chanfro nem grelha. **Solução:** Malha de guia chanfrada com textura de concreto envelhecido e instanciar bueiros de ferro fundido a cada 14 metros. |

---

### 2.3. A Pista Viária e Veículos

| Atributo | Estado Atual (`image-1.png`) | Meta Artística (`abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`) | Causa Técnica & Solução |
| :--- | :--- | :--- | :--- |
| **Superfície do Asfalto** | Preto absoluto opaco e plano, sem granulação, com duas faixas amarelas vetoriais lisas. | Asfalto cinza-escuro antracite (`#2b2d31`) com agregados minerais visíveis (brita/pedrisco), marcas de frenagem de borracha e faixas amarelas duplas desgastadas e craqueladas pelo tráfego. | **Causa:** Material do asfalto sem rugosidade mineral nem decalques de desgaste. **Solução:** PBR completo de asfalto com mapa normal de brita, marcas de pneus misturadas no albedo/roughness e faixas amarelas com máscara de erosão. |
| **Carro / Obstáculo** | Cubo branco simplista com cantos ligeiramente arredondados e dois pontos vermelhos como lanternas (carro de brinquedo). | Automóvel hatchback moderno de 5 portas proporcional e detalhado: faróis e lanternas com lentes translúcidas de acrílico vermelho/âmbar, para-brisa traseiro com vidro escurecido brilhante, placa com moldura e pneus de borracha real com calotas/rodas de liga leve. | **Causa:** Modelo de carro low-poly primitivo. **Solução:** Modelagem precisa de hatchback contemporâneo (estilo Polo/Golf) no Blender com materiais separados de pintura automotiva perolizada, vidros reflexivos e lanternas. |
| **Cones e Sinalização** | Cone estilizado ou ausente no fluxo viário. | Cone de tráfego de alta visibilidade: corpo cônico laranja com faixa refletiva branca central e base quadrada pesada de borracha preta estabilizadora. | **Causa:** Inexistência do cone de obra nos trechos adequados. **Solução:** Instanciar o `cone.glb` de alta fidelidade como obstáculo de pista e marcador viário. |

---

### 2.4. Edifícios, Cenografia Urbana e Vegetação

| Atributo | Estado Atual (`image-1.png`) | Meta Artística (`abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`) | Causa Técnica & Solução |
| :--- | :--- | :--- | :--- |
| **Edifícios da Esquerda** | Paredes lisas marrons e cinzas com buracos brancos representando janelas. | Edifícios urbanos de tijolo aparente marrom-avermelhado envelhecido, com cornijas arquitetônicas no teto, esquadrias escuras de janelas com vidros de reflexo suave e fachadas comerciais térreas. | **Causa:** Prédios gerados como cubos com caixas brancas instanciadas. **Solução:** Fachadas PBR de tijolo com mapa de normais profundo, esquadrias recuadas de metal preto e vidros com shader de reflexão de céu. |
| **Edifícios da Direita** | Prédios bege/amarelos planos, sem portas nem profundidade. | Edifícios de alvenaria em reboco envelhecido (tons de ocre, areia e creme), com áreas onde o reboco descascou revelando tijolos, vitrines comerciais envidraçadas no térreo e portas de entrada. | **Causa:** Ausência de materiais de reboco descascado e vitrines. **Solução:** Módulos de fachada com materiais compostos (reboco + tijolo aparente), vitrines comerciais no térreo com reflexo e portas detalhadas. |
| **Árvores e Folhagem** | Esferas verdes multifacetadas fincadas em hastes marrons (árvores de desenho animado). | Árvores urbanas frondosas de folha caduca: tronco orgânico com casca rugosa, galhos que se bifurcam naturalmente e copa volumosa com centenas de tufos de folhas semi-translúcidas captando a luz dourada do sol. | **Causa:** Uso de icoesferas verdes como copa de árvore. **Solução:** Modelar árvores realistas com troncos ramificados e folhas baseadas em cartões de folhas com canal alfa e *subsurface scattering* (SSS). |
| **Mobiliário Urbano** | Ausente ou imperceptível. | Postes clássicos de ferro fundido com luminárias de vidro ao longo do meio-fio e bancos de praça com ripas de madeira tratada e apoios de ferro fundido. | **Causa:** Mobiliário gerado como caixas simples. **Solução:** Modelos de poste clássico e banco de praça posicionados ritmicamente ao longo da calçada. |

---

### 2.5. Iluminação, Atmosfera e Câmera

| Atributo | Estado Atual (`image-1.png`) | Meta Artística (`abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`) | Causa Técnica & Solução |
| :--- | :--- | :--- | :--- |
| **Posição e Cor do Sol** | Sol em ângulo alto, luz branca/amarelada fria sem sombras dramáticas. | Sol poente rasante a ~28° vindo da frente-esquerda (`Vector3(-28, -56, 0)`), banhando a cena com luz dourada quente (`#fff2db`) e criando *rim lighting* (luz de contorno) no cabelo e ombros da corredora. | **Causa:** Vetor solar muito vertical e sem luz de contorno calibrada. **Solução:** Calibrar a DirectionalLight3D com ângulo rasante e intensidade 1.45, ativando luz de contorno e preenchimento de céu azul frio nas sombras. |
| **Sombras no Chão** | Pequena mancha difusa no piso. | Sombras longas, nítidas e diagonais atravessando a calçada da esquerda para a direita, projetando a silhueta da corredora, dos postes e das árvores de forma dramática e cinematográfica. | **Causa:** Distância e resolução de sombra inadequadas. **Solução:** Ajustar cascaded shadow splits para foco no primeiro plano (0.5 m a 25 m), com bias 0.015 para sombra perfeita colada no pé. |
| **Névoa e Ponto de Fuga** | Parede cinza esfumaçada cortando os prédios ao fundo. | Névoa dourada atmosférica leve (*sun haze*) no ponto de fuga da avenida, que difunde suavemente a silhueta dos carros distantes e integra os prédios ao céu sem cortes duros. | **Causa:** Fog density muito alto (0.0072) criando corte cinza. **Solução:** Neblina suave exponencial com densidade 0.0028, cor dourada quente e perspectiva aérea ativada. |
| **Câmera** | Câmera alta e excessivamente afastada, achatando a perspectiva do corredor. | Câmera próxima e imersiva na altura do ombro (Y=2.25, Z=4.85, FOV=54°), alinhada levemente à esquerda das costas da corredora para destacar a profundidade da calçada e da pista. | **Causa:** Offsets de câmera genéricos. **Solução:** Bloquear os parâmetros de câmera exatamente na posição canônica da referência. |

---

## 3. Plano de Transformação Técnica em 5 Frentes de Trabalho

Para transformar o visual de `image-1.png` em `abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`, a arquitetura do projeto deve ser executada nas seguintes frentes:

```
┌────────────────────────────────────────────────────────────────────────┐
│               PIPELINE DE MAESTRIA GRÁFICA REALISTA 3D                 │
├──────────────────┬──────────────────┬──────────────────┬───────────────┤
│ 1. MODELAGEM 3D  │ 2. MATERIAIS PBR │ 3. BIOMECÂNICA & │ 4. AMBIENTE & │
│ NO BLENDER       │ & TEXTURIZAÇÃO   │ FÍSICA DINÂMICA  │ ILUMINAÇÃO    │
├──────────────────┼──────────────────┼──────────────────┼───────────────┤
│ • Malha contínua │ • Tecido técnico │ • Mola-amortecedor│ • Lajes inter-│
│   anatômica      │   com microdobras│   no rabo de     │   travadas 4K │
│ • Tênis esportivo│ • Calça legging  │   cavalo         │ • Meio-fio com│
│   com entressola │   fosca elastano │ • Balanço de     │   sarjeta/ralo│
│ • Rabo de cavalo │ • Espuma branca e│   ombros/coluna  │ • Carro hatch │
│   esculpido      │   borracha tênis │ • Pisada no chão │   automotivo  │
│ • UVs relaxadas  │ • Asfalto com    │   sem deslizamen-│ • Sol rasante │
│   para Normal Map│   brita e pneus  │   to (foot-lock) │   Golden Hour │
└──────────────────┴──────────────────┴──────────────────┴───────────────┘
```

---

### Frente 1: Modelagem Anatômica e Orgânica dos Personagens (Blender)

#### 1.1. Eliminação do Paradigma de Primitivas Empilhadas
- **Problema:** A geração por `pilar_z()` e `elipsoide_bl()` empilhava esferas e tubos separados. No momento do *join*, cada pedaço formava uma ilha de vértices isolada, sem continuidade poligonal. Quando a animação dobrava o membro, as pontas se cruzavam como tubos de metal.
- **Implementação Técnica:**
  - O corpo do modelo base feminino (`Humano_F.glb` e `julia.glb`) deve ser gerado a partir de uma **malha contínua de subdivisão quádrupla (quad-dominant)**:
    1. **Torso & Pelve:** Modelados como uma malha unificada com cintura fina atlética, transição suave para os glúteos e peitoral feminino natural.
    2. **Pernas Orgânicas:** Coxa modelada com curvatura de quadríceps, afinamento anatômico na inserção do tendão patelar, joelho esculpido com relevo da patela, panturrilha com volume do músculo gastrocnêmio e afinamento no tornozelo até os maléolos medial e lateral.
    3. **Braços:** Deltoide moldado no ombro, bíceps e tríceps com transição contínua para o antebraço e mão relaxada em punho semi-aberto de corredora.
    4. **Tênis de Corrida (Running Shoes):**
       - Sola externa preta com ranhuras de tração antiderrapante (espessura 0.8 cm).
       - Entressola de amortecimento em EVA branco macio: calcanhar elevado a 3.8 cm com chanfro de aterrissagem e curvatura de impulsão (*toe rocker*) levantando 1.5 cm do chão na ponta.
       - Cabedal têxtil respirável com língua acolchoada, ilhoses e cadarços modelados.
       - Meia esportiva cano curto branca (~2 cm de altura) cobrindo o tornozelo e criando a transição entre a calça preta e o tênis branco.
    5. **Cabelo e Rabo de Cavalo:**
       - Touca de cabelo acompanhando o volume craniano com linha de implantação natural na testa e nuca.
       - Elástico de cabelo cilíndrico na região occipital alta.
       - Cauda do rabo de cavalo modelada como mecha aerodinâmica curvada para trás e para baixo, com peso de rig no osso `Hair_Ponytail` (ou vinculado dinamicamente à cabeça com rotação de inércia).

#### 1.2. Mapeamento de UV Limpo e Geração de Tangentes
- Cada segmento do corpo recebe projeção UV cilíndrica/desdobrada relaxada:
  - Costuras (*seams*) posicionadas no lado interno das pernas, parte interna dos braços e linha posterior das costas.
  - Isso garante que qualquer textura ou normal map aplicado não apresente distorções ou costuras visíveis na visão de terceira pessoa pelas costas da personagem.

---

### Frente 2: Texturização e Materiais PBR de Alta Definição

#### 2.1. Materiais da Corredora
1. **Camiseta Esportiva (`Camisa`):**
   - **Albedo:** Rosa/coral suave (`#e06b85`), com microtrama de poliéster técnico.
   - **Normal Map:** Microtrama têxtil combinada com dobras suaves de tecido esticado pelo movimento escapular e da cintura.
   - **Roughness:** 0.78 (fosco com leve reflexo difuso de tecido esportivo).
2. **Calça Legging de Compressão (`Calca`):**
   - **Albedo:** Preto profundo ligeiramente azulado (`#18191f`), sem perder a leitura da silhueta contra o asfalto.
   - **Normal Map:** Trama ultra-fina de elastano/lycra de alta densidade.
   - **Roughness:** 0.65 com brilho suave e sedoso nas cristas musculares.
3. **Tênis de Corrida (`Sapato` / `Entressola`):**
   - **Entressola:** Branco puro (`#f8f8fa`), rugosidade 0.45 com textura de microporos de espuma injetada.
   - **Solado:** Preto emborrachado fosco (`#1a1a1a`), rugosidade 0.85.
   - **Cabedal:** Cinza-azulado com detalhes reflexivos nos cadarços.
4. **Pele e Cabelo:**
   - **Pele:** Tom natural quente com rugosidade 0.58 e variação suave de brilho (sem aspecto de plástico oleoso nem boneco de cera).
   - **Cabelo:** Castanho-escuro/preto natural (`#1a1412`), com brilho especular anisotrópico suave ao longo do comprimento das mechas.

#### 2.2. Materiais do Cenário e Pista
1. **Lajes da Calçada (`CalcadaLaje`):**
   - Padrão retangular de pedras de concreto intertravadas em *running bond*.
   - Juntas rebaixadas de 1.2 cm com acúmulo de areia/terra escura.
   - Variação tonal sutil bloco a bloco para quebrar a repetitividade.
2. **Asfalto e Sinalização:**
   - Asfalto cinza-antracite escuro (`#2b2d31`) com textura de brita fina e marcas sutis de pneus.
   - Faixas amarelas com bordas erodidas e microfissuras de desgaste climático.
3. **Pintura Automotiva do Veículo:**
   - Pintura automotiva branca perolizada com verniz transparente (*clearcoat*), captando o brilho do sol da tarde e as cores do céu.
   - Vidros escurecidos (*insulfilm*) com reflexo especular de céu aberto.

---

### Frente 3: Física e Biomecânica da Animação

#### 3.1. Cinematismo da Corrida
- **Balanço Sagital dos Braços:** Os braços bombeiam estritamente no plano anterior-posterior (sagital), com cotovelos flexionados entre 80° e 90°. Ao avançar o braço direito, o punho sobe na altura do esterno; ao recuar, o cotovelo vai ligeiramente atrás das costas.
- **Ciclo de Passada (*Cadence & Stride*):**
  - Contato plantar inicial no calcanhar/médio-pé, com dorsiflexão suave do tornozelo.
  - Extensão completa da perna de impulsão posterior antes da fase aérea.
  - Velocidade de reprodução da animação rigorosamente atrelada à velocidade linear do jogo para garantir **contato zero de deslizamento (*zero foot-sliding*)**.

#### 3.2. Física Secundária de Movimento (*Secondary Motion*)
- **Rabo de Cavalo (Mola-Amortecedor):**
  - Posição angular vertical acoplada à cadência de impacto dos passos.
  - Pêndulo centrífugo com inércia durante mudanças rápidas de faixa.
  - Elevação aerodinâmica proporcional à velocidade de corrida.
- **Torsão da Coluna e Inclinação (*Spine & Pelvis Dynamics*):**
  - Rotação suave da pelve e contra-rotação da caixa torácica a cada passada.
  - Inclinação esportiva natural para a frente (8° a 10°) e bancação sutil nas mudanças de faixa.

---

### Frente 4: Iluminação Golden Hour, Atmosfera e Câmera

#### 4.1. Configuração da Iluminação Solar
- **Direção:** `Vector3(-28.0, -56.0, 0.0)` — sol rasante lateral.
- **Cor:** `#fff2db` (luz quente dourada de final de tarde).
- **Intensidade:** `1.45`.
- **Sombras:** Cascaded Shadow Maps com 4 divisões (`SHADOW_PARALLEL_4_SPLITS`), `directional_shadow_max_distance = 80.0`, `shadow_bias = 0.015`, produzindo sombras nítidas e longas estendendo-se pela calçada até o meio-fio da direita.
- **Preenchimento do Céu:** Luz ambiente azulada suave (`#3d4d68`, energia `0.45`) para contraste térmico quente/frio nas sombras.

#### 4.2. Névoa e Perspectiva Aérea
- Neblina com decaimento exponencial:
  - `fog_density = 0.0028`.
  - `fog_light_color = Color("#cad8e0")`.
  - `fog_aerial_perspective = 0.65`.
  - Permite visibilidade limpa dos primeiros 100 metros e transição gradual no ponto de fuga da avenida.

#### 4.3. Parâmetros de Câmera
- `RENDER_CAMERA_Y = 2.25` (altura no ombro).
- `RENDER_CAMERA_Z = 4.85` (distância próxima e imersiva).
- `RENDER_FOV = 54.0°` (perspectiva natural de terceira pessoa sem distorção periférica).
- Alvo da câmera focado nas costas e na linha do horizonte à frente.

---

### Frente 5: Interface (HUD) Minimalista e Elegante

- **Botão de Pausa:** Canto superior esquerdo, quadrado arredondado semi-transparente com ícone de barras brancas nítidas.
- **Contador de Moedas:** Canto superior direito, moeda dourada 3D com relevo em círculo e número com tipografia moderna clara (`2860`).
- **Controles de Toque:** Indicadores táteis na base da tela com opacidade sutil (15%), evitando poluição visual e mantendo a calçada e o corredor em destaque total.

---

## 4. Roteiro de Implementação em Fases Verificáveis

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CRONOGRAMA DE IMPLEMENTAÇÃO PRÁTICA                  │
├───────┬──────────────────────────────────┬──────────────────────────────┤
│ FASE  │ ESCOPO                           │ CRITÉRIO DE ACEITAÇÃO        │
├───────┼──────────────────────────────────┼──────────────────────────────┤
│ 1     │ Modelagem da Corredora Atlética  │ GLB com malha contínua,      │
│       │ no Blender (corpo unificado,     │ tênis PBR com entressola     │
│       │ tênis esculpido, rabo de cavalo  │ grossa, UV unwrap relaxado,  │
│       │ e UVs sem sobreposição)          │ pesagem suave nos joelhos.   │
├───────┼──────────────────────────────────┼──────────────────────────────┤
│ 2     │ Materiais PBR e Texturas 4K da   │ Camiseta coral sem artefatos,│
│       │ Personagem no Godot              │ legging fosca sem costuras,  │
│       │                                  │ tênis com sola preta e entres│
│       │                                  │ sola branca destacada.       │
├───────┼──────────────────────────────────┼──────────────────────────────┤
│ 3     │ Reconstrução da Calçada e Pista  │ Lajes retangulares intertra- │
│       │ (Lajes retangulares, canteiros,  │ vadas, canteiros com moldura,│
│       │ sarjeta chanfrada e bueiro)      │ sarjeta e asfalto com brita. │
├───────┼──────────────────────────────────┼──────────────────────────────┤
│ 4     │ Carro Hatchback e Props Urbanos  │ Hatchback branco com verniz  │
│       │ (Automóvel proporcional, postes, │ reflexivo, postes clássicos, │
│       │ árvores frondosas com folhas)    │ árvores orgânicas com alfa.  │
├───────┼──────────────────────────────────┼──────────────────────────────┤
│ 5     │ Iluminação Golden Hour, Sombras  │ Sombras longas na calçada,   │
│       │ Diagonais e HUD Minimalista      │ névoa dourada no horizonte e │
│       │                                  │ 131/131 testes QA aprovados. │
└───────┴──────────────────────────────────┴──────────────────────────────┘
```

---

## 4.1. Registro de Execução — Fase 1 [CONCLUÍDA 2026-09-20]

Script: `tools/blender/build_corredora_fase1.py` (Blender 4.5 headless) → `assets/characters/personagens/julia.glb` (260 KB).

| Critério de aceitação | Resultado |
| :--- | :--- |
| Malha contínua | Um único `Mesh` gerado por construção (`MeshBuilder`, sem `object.join`): torso pelve→clavícula em 1 loft; cada perna quadril→maléolos em 1 loft de 16 anéis (glúteo, quadríceps, patela, gastrocnêmio, Aquiles, maléolos); cada braço deltoide→punho em 1 loft de 12 anéis (bíceps, olécrano). 4 411 vértices / 4 692 faces. |
| Pesagem suave nos joelhos | Pesos por anel (`thigh`/`calf` 0.85→0.15 em 6 anéis, smoothstep); auditoria automática: 108/108 vértices da zona do joelho com 2+ ossos. Mesmo esquema em cotovelo, ombro, cintura, tornozelo. |
| Tênis PBR com entressola grossa | 5 materiais dedicados: `Sola` (borracha preta 8 mm, ranhuras), `Entressola` (EVA branca, calcanhar 38 mm → antepé 20 mm, *toe rocker* 15 mm), `Sapato` (cabedal, tintável), `Cadarco` + `Ilhos`, `Meia` (cano curto 2 cm). Sola em z = 0,000 m (auditado). |
| UV unwrap sem sobreposição | Atlas automático: 58 peças, célula própria por peça com padding 6 %; costuras dos lofts no lado interno das pernas/braços e na linha posterior das costas. |
| Rabo de cavalo | Ossos `Hair_Ponytail_01/02` (filhos de `Head`) com inércia defasada em Sprint/Walk/Jump/Crouch. |
| Compatibilidade Godot | 54 joints (mesmos nomes do rig `runner_character.gd` + ponytail), 6 clipes (`Idle/Walk/Sprint/Jump/Crouch_Idle/Crouch_Fwd_Loop`), materiais `QuaterniusSkin/Camisa/Calca/Sapato/Hair` preservados para `_apply_profile_palette`. Cada clipe grava keyframe neutro em todos os ossos principais (troca de clipe não herda pose). `tools/audit_personagens.py` OK. |

Previews Cycles (regeneráveis, fora do Git): `CORREDORA_PREVIEW=1 sh tools/blender/run_bpy.sh tools/blender/build_corredora_fase1.py` → `tools/blender/out/julia_{frente34,costas,sprint_lado,sprint_costas34,tenis}.png`.

Próximo: Fase 2 (materiais PBR/texturas 4K da personagem no Godot — `Entressola`/`Sola`/`Meia` ainda não recebem textura em `_apply_profile_palette`).

## 5. Conclusão

O contraste evidente entre `image-1.png` e `abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg` decorre fundamentalmente de:
1. Uma abordagem geométrica anterior baseada em primitivas booleanas desconectadas sem UVs adequadas.
2. Materiais com normal maps aplicados em malhas sem coordenadas tangentes.
3. Elementos urbanos (calçada e vegetação) em modelos simplificados/esquemáticos.

Com este plano e estudo comparativo registrado e formalizado na árvore de código, o projeto dispõe de toda a fundamentação técnica e artística para executar a substituição dos modelos e assets pela pipeline de maestria visual realista.
