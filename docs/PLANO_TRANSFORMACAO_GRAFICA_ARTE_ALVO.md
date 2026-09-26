# 🎨 Plano Mestre de Transformação Gráfica: "Corre pro Ponto" ➔ Padrão Visual 10/10

## 🎯 Objetivo
Transformar o visual 3D in-game atual para atingir exatamente a qualidade artística da **Arte Conceitual Alvo (Avenida Tropical com Moedas R$ e Cenário Brasileiro)**:
- **Estilo:** *Stylized PBR Vibrant* (referência: Subway Surfers, Pixar, Disney Mobile).
- **Atmosfera:** Iluminação tropical acolhedora, sombras suaves, céu aberto radiante e leitura limpa em telas móveis.
- **Cenário:** Identidade visual brasileira autêntica (padarias, mercadinhos com toldos, orelhões verdes, ipês amarelos, calçadas limpas, asfalto com sinalização nítida).

---

## 🗺️ Roadmap de Execução Passo a Passo (5 Etapas)

### ☀️ Etapa 1: Atmosfera Tropical, Iluminação Solar & Horizonte Aberto (EM EXECUÇÃO)
- **Eliminação da Névoa Escura:** Ajuste da densidade de névoa de `0.50` (parede cinza opaca) para `0.0018` (haze atmosférico suave e dourado).
- **Iluminação Solar Quente:** Luz direcional solar (5500K) balanceada com luz ambiente do céu (Sky Ambient Energy `1.25`) para preencher sombras pretas e revelar detalhes dos materiais.
- **Calibração de Materiais de Piso:** Redução drástica da rugosidade e relevo excessivo (`normal_scale` de `1.25` para `0.20`, desativação de heightmaps agressivos que geravam efeito de cascalho/areia).

### 🛣️ Etapa 2: Pista Central de 3 Faixas & Calçadas Urbanas Limpas
- **Geometria de Pista:** 3 faixas de rolamento com asfalto acetinado limpo e marcações viárias brancas e amarelas com acabamento nítido.
- **Meio-Fio 3D Chanfrado:** Guias de calçada com perfil 3D e sarjeta de concreto conectando o asfalto às calçadas laterais.
- **Calçadas Estilizadas:** Texturas de pedras portuguesas / ladrilho hidráulico / concreto claro sem repetição ruidosa de UV.

### 🏢 Etapa 3: Fachadas Brasileiras Vivas & Cenografia Urbana
- **Arquitetura Brasileira:** Fachadas com paleta pastel quente (amarelo canário, rosa antigo, azul colonial, verde hortelã).
- **Comércios de Bairro:** Lojas com toldos listrados (padarias, bares, mercadinhos), portas de enrolar de aço e letreiros comerciais.
- **Vegetação & Mobiliário:** Ipês amarelos floridos, árvores urbanas de copa densa, orelhão verde clássico, lixeiras vermelhas e postes com fiação aérea sutil.
- **Ônibus no Ponto:** Coletivo urbano amarelo/verde posicionado no horizonte aguardando na baía do ponto de ônibus.

### 💰 Etapa 4: Moedas 3D "R$" Flutuantes em Arco & Colecionáveis Nacionais
- **Moedas R$:** Malha 3D de moedas de Real com alto relevo metálico reflexivo e emissão dourada suave.
- **Padrão de Coleta:** Spawner em trilhas contínuas e arcos elegantes sobre obstáculos.
- **Power-ups Temáticos:** Modelos 3D de coxinha, cafezinho, pastel de feira e passe dourado com partículas e glow volumétrico.

### 🏃 Etapa 5: Protagonista Estilizado & HUD Mobile Vibrante
- **Personagem:** Corredor estilizado com proporções atléticas, animações suaves de corrida/pulo/deslize, camiseta/uniforme esportivo brasileiro e mochila.
- **HUD Mobile Integrada:** Tipografia com stroke escuro nítido ("CORRE PRO PONTO", "DISTÂNCIA"), corações 3D de vida, ícone 3D de moeda R$ e botão de pause moderno.

---

## 📊 Critérios de Sucesso e Validação
1. **Contraste Visual:** $> 3:1$ entre corredor, pista e obstáculos.
2. **Performance:** 60 FPS estáveis em dispositivos móveis padrão.
3. **Fidelidade à Arte Alvo:** 100% de alinhamento com a imagem conceitual aprovada.
