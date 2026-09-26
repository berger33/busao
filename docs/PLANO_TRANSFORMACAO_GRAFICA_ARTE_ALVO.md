# 🎨 Plano Mestre de Transformação Gráfica: "Corre pro Ponto" ➔ Padrão Visual 10/10

## 🎯 Objetivo
Transformar o visual 3D in-game atual para atingir exatamente a qualidade artística da **Arte Conceitual Alvo (Avenida Tropical com Moedas R$ e Cenário Brasileiro)**:
- **Estilo:** *Stylized PBR Vibrant* (referência: Subway Surfers, Pixar, Disney Mobile).
- **Atmosfera:** Iluminação tropical acolhedora, sombras suaves, céu aberto radiante e leitura limpa em telas móveis.
- **Cenário:** Identidade visual brasileira autêntica (padarias, mercadinhos com toldos, orelhões verdes, ipês amarelos, calçadas limpas, asfalto com sinalização nítida).

---

## 🗺️ Roadmap de Execução (5 Etapas Concluídas)

### ☀️ Etapa 1: Atmosfera Tropical, Iluminação Solar & Horizonte Aberto (WIB-13: DONE)
- **Eliminação da Névoa Escura:** Ajuste da densidade de névoa de `0.50` para `0.002` com alcance de `600 m`.
- **Iluminação Solar Quente:** Luz direcional solar (5500K, -42° de inclinação) e luz ambiente do céu (`1.25`) para preencher sombras pretas.
- **Calibração de Materiais de Piso:** Redução da rugosidade e relevo excessivo (`normal_scale: 0.20`, heightmaps ásperos desativados).

### 🛣️ Etapa 2: Pista Central de 3 Faixas & Calçadas Urbanas Limpas (WIB-14: DONE)
- **Geometria de Pista:** Asfalto acetinado escuro (`roughness: 0.78`, `normal: 0.25`) e marcações viárias nítidas.
- **Meio-Fio 3D Chanfrado:** Guias de calçada com acabamento de concreto cinza claro e sarjetas de drenagem.
- **Calçadas Niveladas:** Camada de ladrilhos nivelada rente ao deck sem degraus ásperos ou z-fighting.

### 🏢 Etapa 3: Fachadas Brasileiras Vivas & Cenografia Urbana (WIB-15: DONE)
- **Arquitetura Brasileira:** Comércios com toldos vibrantes (`material: linha_amarela`), portas de enrolar e vitrines espelhadas.
- **Vegetação & Mobiliário:** Distribuição de ipês amarelos floridos (`ipe_amarelo.glb`), palmeiras, árvores urbanas densas, orelhão verde brasileiro (`orelhao.glb`) e lixeiras urbanas.

### 💰 Etapa 4: Moedas 3D "R$" Flutuantes em Arco & Colecionáveis Nacionais (WIB-16: DONE)
- **Moedas R$:** Escala estilizada ampliada para `0.55` (~33 cm de diâmetro) com emissão dourada brilhante (`emission_energy: 0.85`).
- **Colecionáveis Nacionais:** Ajuste de proporção estilizada e auras luminosas para Coxinha, Cafezinho, Passe Dourado, Pix, Pastel e Guaraná.

### 🏃 Etapa 5: Protagonista Estilizado & HUD Mobile Vibrante (WIB-17: DONE)
- **Protagonista:** Uniforme esportivo brasileiro (amarelo canário com detalhes verdes), tênis esportivo e mochila de corrida.
- **HUD Mobile Vibrante:** Tipografia com stroke/outline de alto contraste em qualquer iluminação, ícones 3D e botão de pause estilizado.

---

## 📊 Status Final: 100% CONCLUÍDO (5/5 Etapas Green)
- **Suíte QA:** 133/133 checks aprovados (0 avisos, 0 falhas).
- **Linear:** Issues WIB-13 a WIB-17 marcadas como Done.
- **Git:** Sincronizado e com push ativo na branch `arena/01a0db52-busao`.
