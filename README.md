# Sistema de Recomendação de Espécies Nativas para Reflorestamento e Arborização Urbana (ODS 15)

<p align="center">
  <img src="https://img.shields.io/badge/Universidade-Presbiteriana%20Mackenzie-red?style=for-the-badge" alt="Mackenzie">
  <img src="https://img.shields.io/badge/Curso-Ci%C3%AAncia%20de%20Dados%20e%20IA-blue?style=for-the-badge" alt="Curso">
  <img src="https://img.shields.io/badge/ONU-ODS%2015%20Vida%20Terrestre-darkgreen?style=for-the-badge" alt="ODS 15">
  <img src="https://img.shields.io/badge/Modelagem-H%C3%ADbrida%20(CBF%20%2B%20Implicit%20CF)-orange?style=for-the-badge" alt="Modelagem">
</p>

> **Projeto Aplicado III — Sistemas de Recomendação**  
> **Faculdade de Computação e Informática — Universidade Presbiteriana Mackenzie**

---

## 👥 Integrantes do Grupo

| Nome | TIA |
| :--- | :---: |
| **Fernanda Pauli de Oliveira** | 10736757 | 
| **Henrique Sarmento** | 10738262 | 
| **Milena Dias Gouveia** | 10746541 | 
| **Nicolly Falcão da Silva** | 10746134 |

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

## 🗂️ 3. Estrutura Oficial do Repositório

```
ProjetoAplicado3/
├── data/
│   ├── raw/                            # Downloads e arquivos brutos das fontes públicas
│   ├── processed/                      # Datasets saneados com resolução taxonômica
│   │   ├── flora_brasil_processed.csv  # Catálogo oficial limpo (JBRJ)
│   │   ├── ifn_parcelas_processed.csv  # Parcelas e abundância viva (IFN/SFB)
│   │   └── gbif_thinned_processed.csv  # Ocorrências com spatial thinning
│   └── sample/                         # Amostras curadas e leves versionadas no Git
│       ├── flora_brasil_sample.csv
│       ├── ifn_parcelas_sample.csv
│       └── gbif_occurrences_sample.csv
├── src/                                # Código-fonte modular da solução
│   ├── __init__.py                     # Inicialização do pacote
│   ├── data_prep.py                    # Pré-processamento, spatial cluster split e matriz R
│   ├── cbf_model.py                    # Fase 1: Nicho Fundamental e Similaridade de Cosseno
│   ├── cf_model.py                     # Fase 2: Fatoração ALS com Feedback Implícito
│   ├── hybrid_recommender.py           # Recomendador em Cascata e Diversificação ILD
│   └── evaluate.py                     # Métricas Top-K (Precision, Recall, NDCG, ILD)
├── notebooks/                          # Jupyter Notebooks interativos e executáveis
│   ├── 01_aquisicao_exploracao_limpeza_dados.ipynb  # Download, EDA e tratamento das bases
│   └── 02_pipeline_modelagem_recomendador.ipynb     # Treinamento comparativo, tuning e curvas
├── Etapa 1/                            # Documentação da Etapa 1
├── Etapa 2/                            # Documentação da Etapa 2
├── Etapa 3/                            # Documentação e Relatório Final da Etapa 3 (Metodologia)
│   └── Etapa 3 - ABNT.docx             # Documento cumulativo ABNT da Etapa 3
├── requirements.txt                    # Dependências do projeto Python
└── README.md                           # Documentação central do repositório
```

---

## 🚀 4. Como Executar o Projeto

### 4.1 Instalação do Ambiente
Recomenda-se utilizar Python 3.10 ou superior:

```bash
git clone https://github.com/henri-sarmento/ProjetoAplicado3.git
cd ProjetoAplicado3
pip install -r requirements.txt
```

### 4.2 Execução Sequencial dos Notebooks
1. **Aquisição, Exploração e Limpeza de Dados:**
   Abra e execute o notebook `notebooks/01_aquisicao_exploracao_limpeza_dados.ipynb`. Ele ingere as bases brutas, aplica a resolução taxonômica e gera os arquivos tratados em `data/processed/`.
2. **Treinamento e Avaliação do Recomendador Híbrido:**
   Abra e execute o notebook `notebooks/02_pipeline_modelagem_recomendador.ipynb`. Ele treina os modelos, calcula as métricas offline ($Precision@K, Recall@K, NDCG@K, ILD$), plota as curvas de sensibilidade do peso $\beta$ e exibe prescrições botânicas Top-5 explicáveis.

### 4.3 Utilização Modular via Script Python
```python
from src import load_data, prepare_matrices, encode_features_for_cbf
from src import ContentBasedRecommender, ImplicitALSRecommender, TwoStageCascadeHybridRecommender

# 1. Carrega dados
df_flora, df_ifn, _ = load_data()

# 2. Prepara matrizes e vetores
u_vecs, i_vecs, p_list, s_list = encode_features_for_cbf(df_ifn, df_flora)
R_sparse, p2i, _, s2i, _ = prepare_matrices(df_ifn, df_flora)

# 3. Treina modelos
cbf = ContentBasedRecommender(u_vecs, i_vecs, p_list, s_list, df_flora)
cf = ImplicitALSRecommender(factors=32, alpha=40.0).fit(R_sparse, p2i, s2i)
hybrid = TwoStageCascadeHybridRecommender(cbf, cf, df_flora, beta=0.40)

# 4. Gera prescrição para uma parcela
recomendacoes = hybrid.recommend('CONGLOM_001_SUB1', k=5, plot_biome='Mata Atlântica', plot_ph=5.8)
for r in recomendacoes:
    print(f"Espécie: {r['scientific_name']} | Estágio: {r['successional_stage']} | Escore: {r['hybrid_score']}")
```

---

## 📊 5. Resultados Experimentais Preliminares (Etapa 3)

| Métrica | Baseline (Conteúdo Puro) | Modelo Híbrido (CBF + ALS) | Ganho Relativo |
| :--- | :---: | :---: | :---: |
| **Precision@5** | 0.0400 | **0.0800** | **+100.0%** |
| **Precision@10** | 0.0650 | **0.1250** | **+92.3%** |
| **Recall@5** | 0.1500 | **0.3167** | **+111.1%** |
| **Recall@10** | 0.4500 | **0.7833** | **+74.1%** |
| **NDCG@10** | 0.2241 | **0.4285** | **+91.2%** |
| **ILD@10 (Diversidade)** | 0.8120 | **0.8850** | **+9.0%** |

O acoplamento colaborativo com regularização de confiança e pós-processamento de diversificação intra-lista quase dobrou a recuperação de espécies sinérgicas ($Recall@10 = 0.7833$ vs. $0.4500$) preservando alto índice de diversidade botânica ($ILD@10 = 0.8850$).

---

## 📚 6. Referências Bibliográficas Principais

* AGGARWAL, C. C. **Recommender Systems: The Textbook**. Cham: Springer, 2016.
* BRANCALION, P. H. S. et al. Global restoration opportunities in tropical rainforest landscapes. **Science Advances**, v. 5, n. 7, p. eaav3223, 2019.
* BURKE, R. Hybrid Recommender Systems: Survey and Experiments. **User Modeling and User-Adapted Interaction**, v. 12, n. 4, p. 331-370, 2002.
* CHAZDON, R. L. **Second growth: the promise of tropical forest regeneration in an age of deforestation**. Chicago: University of Chicago Press, 2014.
* CROUZEILLES, R. et al. Achieving cost-effective Amazon forest restoration through socially-inclusive and biodiversity-informed spatial prioritization. **Forest Ecology and Management**, v. 465, p. 118098, 2020.
* HE, X. et al. Neural Collaborative Filtering. In: **International Conference on World Wide Web (WWW)**, 26., 2017, Perth. Proceedings... New York: ACM, 2017. p. 173-182.
* HU, Y.; KOREN, Y.; VOLINSKY, C. Collaborative Filtering for Implicit Feedback Datasets. In: **IEEE International Conference on Data Mining (ICDM)**, 8., 2008, Pisa. Proceedings... Pisa: IEEE, 2008. p. 263-272.
* HUTCHINSON, G. E. Concluding remarks. **Cold Spring Harbor Symposia on Quantitative Biology**, v. 22, p. 415-427, 1957.
* JÄRVELIN, K.; KEKÄLÄINEN, J. Cumulated gain-based evaluation of retrieval techniques. **ACM Transactions on Information Systems**, v. 20, n. 4, p. 422-446, 2002.
* JBRJ. **Flora e Funga do Brasil**. Rio de Janeiro: Jardim Botânico do Rio de Janeiro, 2026.
* KOREN, Y.; BELL, R.; VOLINSKY, C. Matrix Factorization Techniques for Recommender Systems. **Computer**, v. 42, n. 8, p. 30-37, 2009.
* KUNAVER, M.; POŽRL, T. Diversity in recommender systems: A survey. **Knowledge-Based Systems**, v. 123, p. 154-162, 2017.
* MEYER, C.; KREFT, H.; GURNEY, R.; JETZ, W. Global priorities for an effective information basis of biodiversity distributions. **Nature Communications**, v. 6, n. 8221, p. 1-8, 2015.
* RENDLE, S. et al. Neural Collaborative Filtering vs. Matrix Factorization Revisited. In: **ACM Conference on Recommender Systems (RecSys)**, 14., 2020, Virtual. Proceedings... New York: ACM, 2020. p. 240-248.
* RICCI, F.; ROKACH, L.; SHAPIRA, B. (ed.). **Recommender Systems Handbook**. Boston: Springer, 2011.
* SFB. **Inventário Florestal Nacional: dados biofísicos e socioambientais**. Brasília: MAPA, 2025.
* STEEN, V. A. et al. Spatial thinning reduces spatial autocorrelation and increases model performance in species distribution modeling. **Ecological Informatics**, v. 65, p. 101402, 2021.
* STRASSBURG, B. B. N. et al. Global priority areas for ecosystem restoration. **Nature**, v. 586, p. 724-729, 2020.
* STUBBLEFIELD, M. et al. Machine learning approaches to predict tree seedling survival in ecological restoration. **Restoration Ecology**, v. 31, n. 4, p. e13880, 2023.
* ZIEGLER, C.-N. et al. Improving recommendation lists through topic diversification. In: **International Conference on World Wide Web (WWW)**, 14., 2005, Chiba. Proceedings... New York: ACM, 2005. p. 22-32.
* ZIZKA, A. et al. CoordinateCleaner: Standardized cleaning of occurrence data from biodiversity databases. **Methods in Ecology and Evolution**, v. 10, n. 5, p. 744-751, 2019.
