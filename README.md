# Sistema de Recomendação de Espécies Nativas para Reflorestamento e Arborização Urbana (ODS 15)

<p align="center">
  <img src="https://img.shields.io/badge/Status-Etapa%202%20Conclu%C3%ADda-brightgreen?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Universidade-Presbiteriana%20Mackenzie-red?style=for-the-badge" alt="Mackenzie">
  <img src="https://img.shields.io/badge/Curso-Ci%C3%AAncia%20de%20Dados%20%26%20IA-blue?style=for-the-badge" alt="Curso">
  <img src="https://img.shields.io/badge/ONU-ODS%2015%20Vida%20Terrestre-darkgreen?style=for-the-badge" alt="ODS 15">
  <img src="https://img.shields.io/badge/Modelagem-H%C3%ADbrida%20(CBF%20%2B%20Implicit%20CF)-orange?style=for-the-badge" alt="Modelagem">
</p>

> **Projeto Aplicado III — Tecnologia em Ciência de Dados e Inteligência Artificial**  
> **Faculdade de Computação e Informática (FCI) — Universidade Presbiteriana Mackenzie**

---

## 👥 Integrantes do Grupo

| Nome | TIA | GitHub |
| :--- | :---: | :---: |
| **Fernanda Pauli de Oliveira** | 10736757 | [@Fernanda-Pauli](https://github.com/Fernanda-Pauli) |
| **Henrique Sarmento** | 10738262 | [@henri-sarmento](https://github.com/henri-sarmento) |
| **Milena Dias Gouveia** | 10746541 | [@milenadgouveia](https://github.com/milenadgouveia) |
| **Nicolly Falcão da Silva** | 10746134 | [@Nicollyfalcao](https://github.com/Nicollyfalcao) |

---

## 📌 1. Visão Geral e Contexto (ODS 15)

A degradação de biomas nativos e a perda acelerada de biodiversidade figuram entre as maiores ameaças socioambientais contemporâneas. Em alinhamento ao **Objetivo de Desenvolvimento Sustentável 15 (ODS 15 — Vida Terrestre)** das Nações Unidas, este projeto visa proteger, recuperar e promover o uso sustentável dos ecossistemas terrestres através da ciência de dados e inteligência artificial aplicada.

### O Problema
Projetos de reflorestamento rural e de arborização urbana sofrem rotineiramente com **altos índices de mortalidade precoce de mudas** nos dois primeiros anos de implantação. Esse insucesso decorre primariamente de:
* **Incompatibilidade Edafoclimática:** Seleção de espécies com tolerâncias ecológicas que não correspondem às propriedades do solo (pH, textura, drenagem) ou do microclima local (precipitação, radiação solar e amplitude térmica);
* **Falta de Sinergia Comunitária:** Plantio desordenado sem observar as relações ecológicas de facilitação, sucessão florestal e convivência fitossociológica;
* **Prejuízo Financeiro e Logístico:** Desperdício de recursos de secretarias municipais, viveiros florestais e iniciativas privadas decorrente de replantios recorrentes.

### A Solução Proposta
Desenvolver um **Sistema de Recomendação Inteligente Top-$K$** que atue como ponte técnica entre catálogos botânicos oficiais e os executores de políticas de plantio. A solução analisa os atributos ambientais do sítio de plantio e sugere uma lista ranqueada de espécies arbóreas nativas com máxima probabilidade de sobrevivência, otimizando investimentos e acelerando a restauração de serviços ecossistêmicos.

---

## 🏛️ 2. Arquitetura da Solução: Recomendador Híbrido em Duas Fases

Para unir rigor botânico e capacidade preditiva, adotou-se uma arquitetura sequencial em cascata (**Two-Stage Cascade Hybrid Recommender**), articulando a teoria ecológica do nicho às técnicas de recuperação de informação e fatoração de matrizes.

```
+-----------------------------------------------------------------------------------------+
|                    ENTRADA: PERFIL EDAFOCLIMÁTICO DO TERRENO (u)                        |
|        (Bioma, Textura do Solo, pH, Drenagem Hídrica, Radiação Solar, Pluviosidade)      |
+-----------------------------------------------------------------------------------------+
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: FILTRAGEM BASEADA EM CONTEÚDO (CBF) — GERAÇÃO DE CANDIDATAS                     │
│ • Fundamentação Ecológica: Modelagem do Nicho Fundamental (Hutchinson, 1957)            │
│ • Algoritmo: Modelo de Espaço Vetorial & Similaridade do Cosseno                        │
│ • Função: Podar espécies fisiologicamente inaptas às restrições abióticas locais        │
│ • Saída: Subconjunto C_u de Espécies Candidatas Viáveis                                 │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             │ [Candidatas Viáveis C_u]
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: FILTRAGEM COLABORATIVA COM FEEDBACK IMPLÍCITO (CF) — RERANKING FITOSSOCIOLÓGICO │
│ • Fundamentação Ecológica: Modelagem do Nicho Efetivo e Coexistência Florestal          │
│ • Algoritmo: Decomposição de Matrizes por ALS (Hu, Koren & Volinsky, 2008)              │
│ • Dados: Matriz Parcela x Espécie das unidades amostrais sistemáticas do IFN/SFB        │
│ • Função: Reordenar as candidatas priorizando espécies que coexistem sinergicamente     │
│ • Saída: Predição de afinidade latente p̂_ui                                            │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ SCORE HÍBRIDO PONDERADO & DIVERSIFICAÇÃO TOP-N                                          │
│ • Combinação Linear: S(u, i) = β · Simil_CBF(u, i) + (1 - β) · p̂_ui_CF                 │
│ • Pós-Processamento: Maximização de Diversidade Intra-Lista (ILD - Ziegler et al.)       │
│ • Saída Final: Top-K Espécies Nativas Resilientes, Diversificadas e Explicáveis         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Detalhamento das Camadas

### 2.1 Fase 1 — Filtragem Baseada em Conteúdo (Nicho Fundamental)
A primeira fase atua na **geração de candidatas (*candidacy generation*)**. O terreno $u$ é representado por um vetor $\mathbf{u} \in \mathbb{R}^d$ de variáveis ambientais, e cada espécie $i$ é caracterizada por seu vetor $\mathbf{i} \in \mathbb{R}^d$ contendo requisitos ecológicos extraídos do catálogo botânico.
A compatibilidade abiótica é calculada via **Similaridade do Cosseno**:

$$\text{Simil}(\mathbf{u}, \mathbf{i}) = \frac{\mathbf{u} \cdot \mathbf{i}}{\|\mathbf{u}\| \|\mathbf{i}\|} = \frac{\sum_{k=1}^d u_k \cdot i_k}{\sqrt{\sum_{k=1}^d u_k^2} \cdot \sqrt{\sum_{k=1}^d i_k^2}}$$

Espécies que violem restrições físicas eliminatórias (ex.: planta de solo arenoso seco em terreno encharcado argiloso) recebem pontuação nula, produzindo um conjunto filtrado de candidatas viáveis $\mathcal{C}_u$.

---

### 2.2 Fase 2 — Filtragem Colaborativa com Feedback Implícito (Nicho Efetivo)
> **Resposta ao Feedback da Banca:**  
> A banca solicitou esclarecer como se define uma *interação* entre terreno e espécie no contexto botânico. Na ausência de usuários humanos avaliando plantas com notas explícitas, modelamos o ecossistema como um problema formal de **Feedback Implícito (*Implicit Feedback*)**:

* **Entidade "Usuário" ($u$):** Unidades amostrais físicas de campo — as **parcelas padronizadas de $20 \times 20\text{ m}$ do Inventário Florestal Nacional (IFN)** e células de grade ecológica (*grids*) com coletas integradas do GBIF.
* **Entidade "Item" ($i$):** Espécies arbóreas e vegetais nativas catalogadas no Flora e Funga do Brasil.
* **Interação ($r_{ui} \ge 0$):** 
  * $r_{ui} = 0$ denota dado não observado/esparso (e **não** aversão ou incompatibilidade ativa);
  * $r_{ui} > 0$ representa a contagem numérica ou frequência relativa de espécimes vivos observados colonizando a parcela $u$.

Seguindo o formalismo de **Hu, Koren e Volinsky (2008)**, decompõe-se a observação em:
1. **Preferência Binária ($p_{ui}$):**
   $$p_{ui} = \begin{cases} 1, & \text{se } r_{ui} > 0 \\ 0, & \text{se } r_{ui} = 0 \end{cases}$$
2. **Confiança da Observação ($c_{ui}$):**
   $$c_{ui} = 1 + \alpha \cdot r_{ui}$$
   *(onde $\alpha$ calibra a intensidade da evidência de sobrevivência).*
3. **Predição por Fatores Latentes:**
   $$\hat{p}_{ui} = \mathbf{x}_u^T \mathbf{y}_i$$
4. **Otimização ALS (Mínimos Quadrados Alternados):**
   $$\mathcal{L}_{ALS} = \sum_{u, i} c_{ui} \left( p_{ui} - \mathbf{x}_u^T \mathbf{y}_i \right)^2 + \lambda \left( \sum_u \|\mathbf{x}_u\|_2^2 + \sum_i \|\mathbf{y}_i\|_2^2 \right)$$

Essa camada captura dimensões ecológicas latentes (simbioses micorrízicas no solo, complementariedade de estratos e facilitação sucessional), promovendo um ranqueamento que privilegia espécies que prosperam em conjunto na natureza.

---

### 2.3 Combinação Linear de Scores
A pontuação final $S(u, i)$ de cada espécie $i \in \mathcal{C}_u$ é determinada pela combinação balanceada:

$$S(u, i) = \beta \cdot \text{Simil}_{CBF}(\mathbf{u}, \mathbf{i}) + (1 - \beta) \cdot \hat{p}_{ui}^{CF}$$

onde $\beta \in [0, 1]$ pondera a conformidade ao nicho abiótico individual versus o ganho de sinergia fitossociológica empírica.

---

## 🗄️ 3. Bases de Dados Integradas

O projeto integra três grandes repositórios biológicos de domínio público:

| Base de Dados | Instituição Mantenedora | Papel no Sistema | Granularidade / Conteúdo | Formato / Acesso |
| :--- | :--- | :--- | :--- | :--- |
| **Flora e Funga do Brasil** | Jardim Botânico do Rio de Janeiro (JBRJ) | Catálogo oficial de "Itens" (descritores de conteúdo para CBF) | Morfologia vegetal, formas de vida, bioma de ocorrência nativa, substrato, endemismo e exigência luminosa. | IPT / CSV / API RESTful |
| **Inventário Florestal Nacional (IFN)** | Serviço Florestal Brasileiro (SFB / MAPA) | Matriz de "Interações" Parcela $\times$ Espécie (CF) | Levantamentos de campo em malha regular de conglomerados (parcelas de $20 \times 20\text{ m}$), abundância de indivíduos vivos e laudos físico-químicos de solos. | Dados Abertos SFB / Tabular |
| **Global Biodiversity Information Facility (GBIF)** | Consórcio Científico Internacional GBIF | Suporte espacial e densidade contínua | Ocorrências georreferenciadas (latitude/longitude), herbários digitais e registros de coletas botânicas históricas e recentes. | API REST (`pygbif`) / Darwin Core |

---

## 🔬 4. Desafios de Engenharia de Dados e Avaliação

### 4.1 Mitigação de Vieses e Qualidade dos Dados
* **Spatial Thinning (Subamostragem Espacial):** Dados abertos de biodiversidade sofrem forte viés amostral, concentrando-se próximos a universidades, centros urbanos e rodovias pavimentadas (Meyer et al., 2015). Aplica-se subamostragem geográfica impondo distância euclidiana mínima entre coletas da mesma espécie para regularizar a densidade territorial;
* **Resolução Taxonômica:** Nomes botânicos sofrem constantes atualizações filogenéticas, gerando sinonímias. Adota-se o repositório Flora e Funga do Brasil como autoridade única para unificar espécimes em seus nomes válidos aceitos;
* **Tratamento de Dados Esparsos:** Tolerâncias físico-químicas ausentes para espécies menos documentadas são imputadas através de conservadorismo filogenético (média do gênero ou família botânica).

### 4.2 Métricas de Avaliação Offline (Top-N)
A validação do recomendador utiliza divisão temporal/espacial das parcelas do IFN e avalia:
* **Precision@K:** Proporção de espécies recomendadas no Top-$K$ que são comprovadamente adaptadas ao ambiente;
* **Recall@K:** Capacidade de recuperar as espécies conhecidas como compatíveis para o microambiente da parcela;
* **NDCG@K (Normalized Discounted Cumulative Gain):** Avalia a qualidade do ordenamento, atribuindo maior recompensa quando as espécies mais aptas figuram nas primeiras posições;
* **Diversidade Intra-Lista (ILD — Ziegler et al., 2005):**
  $$\text{ILD}(L) = \frac{2}{|L|(|L|-1)} \sum_{i \in L} \sum_{j \in L, j \neq i} d(i, j)$$
  *(onde $d(i, j)$ representa a dissimilaridade funcional e taxonômica).* Na ecologia, a ILD atua prevenindo a indicação de monoculturas ou espécies de uma única família, garantindo a formação de estratos vegetais diversificados e resilientes a pragas e choques climáticos.

---

## 📚 5. Referências Bibliográficas Principais

* AGGARWAL, C. C. **Recommender Systems: The Textbook**. Cham: Springer International Publishing, 2016.
* BRANCALION, P. H. S. et al. Global restoration opportunities in tropical rainforest landscapes. **Science Advances**, v. 5, n. 7, p. eaav3223, 2019.
* BURKE, R. Hybrid Recommender Systems: Survey and Experiments. **User Modeling and User-Adapted Interaction**, v. 12, n. 4, p. 331-370, 2002.
* CHAZDON, R. L. **Second growth: the promise of tropical forest regeneration in an age of deforestation**. Chicago: University of Chicago Press, 2014.
* HU, Y.; KOREN, Y.; VOLINSKY, C. Collaborative Filtering for Implicit Feedback Datasets. In: **IEEE International Conference on Data Mining (ICDM)**, 8., 2008, Pisa. Proceedings... Pisa: IEEE, 2008. p. 263-272.
* HUTCHINSON, G. E. Concluding remarks. **Cold Spring Harbor Symposia on Quantitative Biology**, v. 22, p. 415-427, 1957.
* JÄRVELIN, K.; KEKÄLÄINEN, J. Cumulated gain-based evaluation of retrieval techniques. **ACM Transactions on Information Systems**, v. 20, n. 4, p. 422-446, 2002.
* JBRJ. **Flora e Funga do Brasil**. Rio de Janeiro: Jardim Botânico do Rio de Janeiro, 2026.
* KOREN, Y.; BELL, R.; VOLINSKY, C. Matrix Factorization Techniques for Recommender Systems. **Computer**, v. 42, n. 8, p. 30-37, 2009.
* MEYER, C.; KREFT, H.; GURNEY, R.; JETZ, W. Global priorities for an effective information basis of biodiversity distributions. **Nature Communications**, v. 6, n. 8221, p. 1-8, 2015.
* RICCI, F.; ROKACH, L.; SHAPIRA, B. (ed.). **Recommender Systems Handbook**. Boston: Springer, 2011.
* SFB. **Inventário Florestal Nacional: dados biofísicos e socioambientais**. Brasília: Serviço Florestal Brasileiro, MAPA, 2025.
* ZIEGLER, C.-N. et al. Improving recommendation lists through topic diversification. In: **International Conference on World Wide Web (WWW)**, 14., 2005, Chiba. Proceedings... New York: ACM, 2005. p. 22-32.
