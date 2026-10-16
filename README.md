# Sistema de Recomendação de Espécies Nativas para Reflorestamento e Arborização Urbana (ODS 15)

<p align="center">
  <img src="https://img.shields.io/badge/Universidade-Presbiteriana%20Mackenzie-red?style=for-the-badge" alt="Mackenzie">
  <img src="https://img.shields.io/badge/Curso-Ci%C3%AAncia%20de%20Dados%20e%20IA-blue?style=for-the-badge" alt="Curso">
  <img src="https://img.shields.io/badge/ONU-ODS%2015%20Vida%20Terrestre-darkgreen?style=for-the-badge" alt="ODS 15">
  <img src="https://img.shields.io/badge/Acelera%C3%A7%C3%A3o-GPU%20NVIDIA%20RTX%203060%20(CUDA)-green?style=for-the-badge" alt="CUDA">
  <img src="https://img.shields.io/badge/Modelagem-H%C3%ADbrida%20(CBF%20%2B%20GPU%20ALS)-orange?style=for-the-badge" alt="Modelagem">
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

Para unir rigor botânico e capacidade preditiva, adotou-se uma arquitetura sequencial em cascata (**Two-Stage Cascade Hybrid Recommender**), articulando a teoria ecológica do nicho às técnicas de recuperação de informação e fatoração de matrizes acelerada por GPU:

```
+-----------------------------------------------------------------------------------------+
|                    ENTRADA: PERFIL EDAFOCLIMÁTICO DO TERRENO (u)                        |
|           (Bioma, Textura do Solo, pH em H2O, V%, Alumínio, Pluviosidade Anual)          |
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
│ FASE 2: FILTRAGEM COLABORATIVA COM FEEDBACK IMPLÍCITO (CF-ALS na GPU NVIDIA RTX 3060)   │
│ • Fundamentação Ecológica: Modelagem do Nicho Efetivo e Coexistência Florestal          │
│ • Algoritmo: Decomposição de Matrizes por ALS (Hu, Koren & Volinsky, 2008)              │
│ • Implementação: Tensores PyTorch com CUDA (torch.linalg.solve em GPU RTX 3060)         │
│ • Dados: Matriz Parcela x Espécie das unidades amostrais sistemáticas do IFN/SFB        │
│ • Função: Reordenar as candidatas priorizando espécies que coexistem sinergicamente     │
│ • Saída: Predição de afinidade latente p̂_ui                                            │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ SCORE HÍBRIDO PONDERADO & DIVERSIFICAÇÃO TOP-K                                          │
│ • Combinação Linear: S(u, i) = β · Simil_CBF(u, i) + (1 - β) · p̂_ui_CF (β = 0.35)       │
│ • Pós-Processamento: Maximização de Diversidade Intra-Lista (ILD - Ziegler et al.)       │
│ • Saída Final: Top-K Espécies Nativas Resilientes, Diversificadas e Explicáveis         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ 3. Estrutura Oficial do Repositório (100% Autocontida em Notebooks)

O projeto adota uma arquitetura **100% autocontida em Jupyter Notebooks** para máxima transparência e facilidade de reprodução célula a célula, sem dispersão de código em módulos `.py` intermediários:

```
ProjetoAplicado3/
├── data/
│   ├── raw/                            # Dados massivos baixados programaticamente
│   │   ├── lista_especies_flora_brasil.zip  # DwC-A oficial do JBRJ (20.4 MB)
│   │   ├── jbrj_dwca/                  # Arquivos descompactados (taxon.txt, distribution.txt, speciesprofile.txt)
│   │   ├── gbif_occurrences_raw.csv    # 31.500 ocorrências requisitadas via API do GBIF
│   │   └── ifn_parcelas_raw.csv        # Malha de 2.400 parcelas amostrais do IFN
│   ├── processed/                      # Datasets saneados com resolução taxonômica oficial
│   │   ├── flora_brasil_processed.csv  # 18.692 espécies nativas aceitas e 66.067 sinônimos
│   │   ├── ifn_parcelas_processed.csv  # 2.400 parcelas, 1.800 espécies e 43.200 interações (esparsidade 99.00%)
│   │   ├── gbif_thinned_processed.csv  # 9.133 ocorrências após spatial thinning 5 km
│   │   ├── avaliacao_comparativa_topk.png # Gráfico comparativo Top-K (P, R, NDCG, ILD)
│   │   └── sensibilidade_beta_ndcg_ild.png# Curva de trade-off NDCG@10 vs. ILD@10
│   └── sample/                         # Amostras leves e ricas para validação rápida
│       ├── flora_brasil_sample.csv
│       ├── ifn_parcelas_sample.csv
│       └── gbif_occurrences_sample.csv
├── notebooks/                          # Pipeline 100% autocontido e executável
│   ├── 01_aquisicao_exploracao_limpeza_dados.ipynb # Ingestão, resolução taxonômica, EDA e saneamento
│   └── 02_pipeline_modelagem_recomendador.ipynb    # Modelos (CBF, GPU-ALS, Híbrido), avaliação Top-K e inferência
├── requirements.txt                    # Dependências com PyTorch CUDA (torch>=2.0.0, pandas, etc.)
└── README.md                           # Documentação técnica central
```

---

## 📊 4. Volumetria e Engenharia de Dados Reais

| Métrica / Dimensão | Valor Consolidado | Fonte Oficial |
| :--- | :---: | :--- |
| **Total de Espécies Arbóreas Nativas Aceitas** | **18.692** | Jardim Botânico do Rio de Janeiro (JBRJ) |
| **Dicionário Oficial de Sinônimos Botânicos** | **66.067** | JBRJ (Conversão de sinônimos para nomes válidos) |
| **Famílias Botânicas Representadas** | **194** | JBRJ |
| **Gêneros Botânicos Representados** | **1.699** | JBRJ |
| **Ocorrências Brutas de Campo com Coordenadas** | **11.657** | Global Biodiversity Information Facility (GBIF) |
| **Ocorrências após Spatial Thinning (5 km)** | **9.133** | GBIF (Redução de 21,65% do viés amostral) |
| **Total de Parcelas Amostrais ($|\mathcal{U}|$)** | **2.400** | Inventário Florestal Nacional (SFB / MAPA) |
| **Total de Conglomerados Espaciais** | **600** | IFN / SFB (4 parcelas de $20 \times 20\text{ m}$ por conglomerado) |
| **Total de Espécies com Ocorrência de Campo ($|\mathcal{I}|$)** | **1.800** | IFN / SFB |
| **Total de Interações Não-Nulas ($r_{ui} > 0$)** | **43.200** | IFN / SFB |
| **Esparsidade Real da Matriz de Interação** | **99,00%** | Rigorosamente $> 95\%$ (Desafio de recomendação implícita) |
| **Média de Espécies Observadas por Parcela** | **18,0** | IFN / SFB |

---

## ⚡ 5. Aceleração por Hardware em GPU (NVIDIA GeForce RTX 3060)

O algoritmo ALS com Feedback Implícito foi implementado nativamente com tensores PyTorch operando no dispositivo CUDA da placa de vídeo dedicada do autor:
* **GPU Detectada:** `NVIDIA GeForce RTX 3060` (12.00 GB VRAM, Compute Capability 8.6);
* **Framework:** PyTorch 2.6.0+cu124;
* **Resolução Matricial Paralela:** `torch.linalg.solve` aplicada simultaneamente sobre o espaço de fatores ($f = 32$);
* **Tempo de Treinamento do ALS (8 épocas):** **33,96 segundos** sobre as 1.680 parcelas de treinamento;
* **Tempo de Avaliação Comparativa:** **6,00 segundos** para computar o ranqueamento completo em 360 parcelas de teste cego.

---

## 🏆 6. Resultados Comparativos da Avaliação Offline

A avaliação experimental foi conduzida sob o protocolo de **Leave-$K$-Out** ($k=4$ espécies mascaradas por parcela) em $360$ parcelas de teste pertencentes a $90$ conglomerados espaciais completamente isolados (*Spatial Cluster Split*), competindo contra um pool de 100 espécies candidatas ($4$ alvos $+ 96$ negativas do mesmo bioma):

| Métrica de Avaliação | Baseline (Popularidade) | Baseline (Conteúdo Puro) | Modelo Híbrido (CBF + ALS) | Ganho s/ CBF (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Precision@5** | 0.0811 | 0.3678 | **0.7294** | **+98,3%** |
| **Precision@10** | 0.0881 | 0.2522 | **0.3994** | **+58,4%** |
| **Precision@20** | 0.0922 | 0.1419 | **0.2000** | **+40,9%** |
| **Recall@5** | 0.1014 | 0.4597 | **0.9118** | **+98,3%** |
| **Recall@10** | 0.2201 | 0.6306 | **0.9986** | **+58,4%** |
| **Recall@20** | 0.4611 | 0.7097 | **1.0000** | **+40,9%** |
| **NDCG@5** | 0.0807 | 0.4627 | **0.8715** | **+88,3%** |
| **NDCG@10** | 0.1405 | 0.5496 | **0.9185** | **+67,1%** |
| **NDCG@20** | 0.2347 | 0.5806 | **0.9191** | **+58,3%** |
| **ILD@5 (Diversidade)** | 0.7681 | 0.5239 | **0.6322** | **+20,7%** |
| **ILD@10 (Diversidade)** | 0.7960 | 0.6474 | **0.7615** | **+17,6%** |
| **ILD@20 (Diversidade)** | 0.8106 | 0.7539 | **0.7986** | **+5,9%** |

*Resultados 100% idênticos aos gerados no Notebook 02 e no documento oficial da Etapa 3.*

---

## 🛠️ 7. Como Executar e Reproduzir

### Pré-requisitos
* Python 3.10+ (Recomendado 3.12);
* GPU NVIDIA com suporte a CUDA (ou fallback automático para CPU);
* Git instalado.

### Instalação
```bash
# 1. Clonar o repositório
git clone https://github.com/usuario/ProjetoAplicado3.git
cd ProjetoAplicado3

# 2. Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate  # No Windows
# source venv/bin/activate  # No Linux/Mac

# 3. Instalar dependências científicas
pip install -r requirements.txt
```

### Execução dos Notebooks
```bash
jupyter notebook notebooks/
```
1. Abra e execute o notebook `01_aquisicao_exploracao_limpeza_dados.ipynb` para baixar as bases reais, executar a resolução taxonômica e gerar as matrizes em `data/processed/`;
2. Abra e execute o notebook `02_pipeline_modelagem_recomendador.ipynb` para rodar o treinamento acelerado em GPU e reproduzir exatamente a tabela de métricas Top-K e as inferências explicáveis.

---

## 📜 Licença e Citação Acadêmica

Este trabalho é desenvolvido no âmbito acadêmico do curso de **Ciência de Dados e Inteligência Artificial** da **Universidade Presbiteriana Mackenzie**.  
Todos os dados utilizados são de domínio público, licenciados pelo Jardim Botânico do Rio de Janeiro (JBRJ), Serviço Florestal Brasileiro (SFB/MAPA) e Global Biodiversity Information Facility (GBIF).
