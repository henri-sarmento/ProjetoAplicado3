# Sistema de Recomendação de Espécies Nativas para Reflorestamento e Arborização Urbana (ODS 15)

<p align="center">
  <img src="https://img.shields.io/badge/Universidade-Presbiteriana%20Mackenzie-red?style=for-the-badge" alt="Mackenzie">
  <img src="https://img.shields.io/badge/Curso-Ci%C3%AAncia%20de%20Dados%20e%20IA-blue?style=for-the-badge" alt="Curso">
  <img src="https://img.shields.io/badge/ONU-ODS%2015%20Vida%20Terrestre-darkgreen?style=for-the-badge" alt="ODS 15">
  <img src="https://img.shields.io/badge/Acelera%C3%A7%C3%A3o-GPU%20NVIDIA%20RTX%203060%20(CUDA)-green?style=for-the-badge" alt="CUDA">
  <img src="https://img.shields.io/badge/Modelagem-H%C3%ADbrida%20(CBF%20%2B%20GPU%20ALS%20%2B%20ILD)-orange?style=for-the-badge" alt="Modelagem">
</p>

> **Projeto Aplicado III — Sistemas de Recomendação (Projeto Concluído)**  
> **Faculdade de Computação e Informática — Universidade Presbiteriana Mackenzie**  
> **Professor Orientador:** Prof. Gustavo Scalabrini Sampaio

---

## 👥 Integrantes do Grupo

| Nome | TIA |
| :--- | :---: |
| **Fernanda Pauli de Oliveira** | 10736757 |
| **Henrique Sarmento** | 10738262 |
| **Milena Dias Gouveia** | 10746541 |
| **Nicolly Falcão da Silva** | 10746134 |

---

## 📌 1. Visão Geral, Contexto (ODS 15) e Escopo

A degradação acelerada de biomas nativos e a perda de biodiversidade figuram entre os maiores desafios socioambientais contemporâneos. Em alinhamento ao **Objetivo de Desenvolvimento Sustentável 15 (ODS 15 — Vida Terrestre)** da Agenda 2030 da ONU, este projeto desenvolveu e validou um sistema híbrido de recomendação capaz de converter catálogos taxonômicos e inventários biofísicos abertos em prescrições botânicas ordenadas, explicáveis e funcionalmente diversificadas.

### O Problema
Iniciativas de restauração florestal e programas de arborização enfrentam rotineiramente **elevadas taxas de mortalidade precoce de mudas** nos primeiros 24 meses pós-plantio, decorrentes de:
* **Incompatibilidade Edafoclimática:** Seleção de espécies cujas tolerâncias fisiológicas violam as condições locais de pH, fertilidade/saturação por bases ($V\%$), textura do solo e regime pluviométrico;
* **Ausência de Sinergia Fitossociológica e Funcional:** Plantios homogêneos que negligenciam a coexistência entre guildas sucessionais (pioneiras, secundárias e clímax) e a diversidade de famílias botânicas;
* **Desperdício Operacional:** Custos recorrentes de replantio em viveiros florestais, secretarias municipais de meio ambiente e projetos de recomposição ambiental.

### A Solução Desenvolvida e Delimitação Operacional
Implementou-se um **Sistema de Recomendação Híbrido em Cascata Top-$K$** que integra a adequabilidade ao nicho fundamental (Filtragem Baseada em Conteúdo com poda rígida), padrões latentes de coocorrência em parcelas amostrais (Fatoração Matricial via ALS acelerada em GPU com suporte a *cold-start* estrito) e diversificação ecológica intra-lista ($ILD$).

> **Delimitação de Escopo Empírico:** Mantendo a continuidade institucional do título ao longo das Etapas 1 a 3, a validação quantitativa *offline* deste repositório concentrou-se em **parcelas de restauração florestal**. Restrições específicas de infraestrutura de **arborização urbana** (porte máximo sob rede elétrica, largura livre de calçada e agressividade radicular) encontram-se arquiteturalmente parametrizadas como predicados booleanos extensíveis no filtro rígido (*hard filter*) da Fase 1.

---

## 🏛️ 2. Arquitetura da Solução: Recomendador Híbrido em Cascata

O pipeline articula dois estágios preditivos seguidos de reordenamento ecológico guloso, contemplando tanto o **enriquecimento de fragmentos em regeneração ($O_u \neq \emptyset$)** quanto áreas totalmente desprovidas de cobertura arbórea em ***cold-start* estrito ($O_u = \emptyset$)**:

```text
+-----------------------------------------------------------------------------------------+
| ENTRADA: PERFIL EDAFOCLIMÁTICO DO TERRENO (u) + FLORA OBSERVADA (O_u)                   |
| (Bioma, Coordenadas, Textura do Solo, pH em H2O, V%, Precipitação Anual)                |
+-----------------------------------------------------------------------------------------+
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: FILTRAGEM BASEADA EM CONTEÚDO (CBF) + PODA RÍGIDA (HARD FILTER)                 │
│ • Fundamentação: Nicho Fundamental (Hutchinson, 1957)                                   │
│ • Operação: Filtro estrito de bioma/solo + Cosseno abiótico + Afinidade familiar        │
│ • Extensibilidade Urbana: Predicados viários parametrizáveis (rede, calçada, raiz)      │
│ • Saída: Subconjunto qualificado C_u de espécies candidatas fisiologicamente aptas      │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ [Candidatas Viáveis C_u]
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: FILTRAGEM COLABORATIVA IMPLÍCITA (CF-ALS EM GPU NVIDIA RTX 3060)                │
│ • Fundamentação: Nicho Realizado e Coocorrência Florestal (Hu, Koren & Volinsky, 2008)  │
│ • Treinamento: ALS ponderado por abundância viva c_ui = 1 + α·r_ui (PyTorch CUDA)       │
│ • Inferência c/ Remanescentes (O_u ≠ ∅): Projeção analítica indutiva ALS Fold-In        │
│ • Inferência Cold-Start Estrito (O_u = ∅): Interpolação ambiental k-NN (k = 15)         │
│ • Saída: Escore latente de sinergia fitossociológica s_CF(u, i)                         │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ ACOPLAMENTO HÍBRIDO NORMALIZADO & DIVERSIFICAÇÃO ECOLÓGICA TOP-K                        │
│ • Escalonamento: Normalização Min-Max intra-candidatas sobre C_u (s̃_CBF e s̃_CF)       │
│ • Fusão Linear: S(u, i) = β·s̃_CBF(u, i) + (1 - β)·s̃_CF(u, i)   [β = 0,35]             │
│ • Pós-Processamento: Reordenamento guloso ILD (família + grupo sucessional, γ = 0,25)   │
│ • Saída Final: Prescrição Top-K explicável, resiliente e funcionalmente diversa         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ 3. Estrutura Oficial do Repositório

O repositório organiza os entregáveis por etapa acadêmica (`Etapa 1/`, `Etapa 2/`, `Etapa 3/`) e concentra toda a engenharia de dados, modelagem em GPU e avaliação da Etapa 3 de forma **100% autocontida em dois Jupyter Notebooks**, acompanhados dos relatórios finais, painel executivo em Excel e dados processados auditáveis:

```text
ProjetoAplicado3/
├── Etapa 1/
│   └── Etapa 1 - ABNT.docx                                 # Relatório consolidado da Etapa 1
├── Etapa 2/
│   ├── Etapa 2 - ABNT.docx                                 # Relatório consolidado da Etapa 2 (PoC)
│   └── Etapa 2 - ABNT.pdf                                  # Versão em PDF da Etapa 2
├── Etapa 3/                                                # Entrega final completa e auditável da Etapa 3
│   ├── data/
│   │   ├── sample/                                         # Amostras leves para inspeção rápida de esquema
│   │   │   ├── flora_brasil_sample.csv
│   │   │   ├── gbif_occurrences_sample.csv
│   │   │   └── ifn_parcelas_sample.csv
│   │   └── processed/                                      # Bases processadas, métricas JSON e gráficos 300 DPI
│   │       ├── flora_brasil_processed.csv                  # Catálogo curado JBRJ (18.692 espécies nativas)
│   │       ├── gbif_thinned_processed.csv                  # Ocorrências GBIF pós-Spatial Thinning (9.134 reg.)
│   │       ├── ifn_parcelas_processed.csv                  # Malha estruturada (2.400 parcelas / 43.200 interações)
│   │       ├── metricas_oficiais_etapa3.json               # Fonte oficial auditável de todas as métricas e tempos
│   │       ├── eda_riqueza_biomas.png
│   │       ├── eda_solos_chuva.png
│   │       ├── eda_sucessao_frequencia.png
│   │       ├── eda_spatial_thinning_mapa.png
│   │       ├── avaliacao_comparativa_topk.png
│   │       └── sensibilidade_beta_ndcg_ild.png
│   ├── figuras/                                            # Diagramas metodológicos e script gerador (300 DPI)
│   │   ├── figura1_arquitetura_recomendador.png
│   │   ├── figura2_pipeline_metodologia.png
│   │   ├── figura3_arquitetura_hibrida_cascata.png
│   │   └── generate_diagrams_etapa3.py
│   ├── notebooks/                                          # Pipeline 100% autocontido e reprodutível
│   │   ├── 01_aquisicao_exploracao_limpeza_dados.ipynb     # Ingestão (JBRJ, GBIF, malha IFN), EDA e saneamento
│   │   └── 02_pipeline_modelagem_recomendador.ipynb        # Modelos (Pop, CBF, GPU-ALS, Híbrido), k-NN e ILD
│   ├── Resultados_ODS15_Recomendacao.xlsx                  # Painel executivo e planilhas auditáveis de escores
│   ├── Etapa_3_ABNT.docx                                   # Relatório técnico-científico final ABNT (Word OMML)
│   └── Etapa_3_ABNT.pdf                                    # Relatório técnico-científico final ABNT (PDF)
├── .gitignore                                              # Exclusão de arquivos brutos pesados (data/raw/, *.zip)
├── requirements.txt                                        # Dependências enxutas e verificadas para reprodução
└── README.md                                               # Documentação técnica central do repositório
```

> **Nota sobre Dados Brutos (`Etapa 3/data/raw/`):** Os artefatos brutos (~197 MB, incluindo `lista_especies_flora_brasil.zip` de 20,4 MB e os arquivos Darwin Core descompactados em `jbrj_dwca/`) são baixados automaticamente pelo Notebook 01 e permanecem ignorados no `.gitignore`. Como os arquivos finais em `Etapa 3/data/processed/` já estão versionados, o Notebook 02 pode ser executado imediatamente após clonar o repositório.

---

## 📊 4. Volumetria, Particionamento Espacial e Transparência de Dados

| Métrica / Dimensão | Valor Consolidado | Fonte / Protocolo Aplicado |
| :--- | :---: | :--- |
| **Espécies Nativas Aceitas (Árvores/Arbustos)** | **18.692** | Flora e Funga do Brasil — DwC-A real (JBRJ, 2026) |
| **Dicionário Relacional de Sinônimos Botânicos** | **66.067** | JBRJ (`taxon.txt` com 166.040 registros processados) |
| **Famílias / Gêneros Botânicos Representados** | **194 / 1.699** | JBRJ |
| **Registros Brutos Requisitados via API REST** | **31.500** | Global Biodiversity Information Facility (GBIF, 2026) |
| **Ocorrências Válidas Pós-Reconciliação JBRJ** | **11.657** | GBIF (538 binômios sinônimos convertidos) |
| **Ocorrências Pós-*Spatial Thinning* ($0,05^\circ$)** | **9.134** | Grade $\approx 5,5 \times 5,5\text{ km}$ (**$-21,64\%$** de redundância) |
| **Malha de Conglomerados / Parcelas ($|\mathcal{U}|$)** | **600 / 2.400** | Protocolo amostral IFN/SFB (4 subunidades de $20 \times 20\text{ m}$) |
| **Vocabulário Ativo na Matriz ($|\mathcal{I}|$)** | **1.800** | Espécies nativas extraídas dos pools reais JBRJ/GBIF |
| **Interações Positivas ($r_{ui} > 0$) / Esparsidade** | **43.200 / 99,00%** | Média de 18,0 espécies/parcela (densidade de 1,00%) |
| **Split Espacial sem Vazamento (Treino / Val / Teste)** | **420 / 90 / 90** | Conglomerados isolados (**1.680 / 360 / 360** parcelas; interseção 0) |

> **Nota de Transparência Metodológica:** O catálogo taxonômico (18.692 espécies aceitas e 66.067 sinônimos do JBRJ) e os registros georreferenciados (31.500 ocorrências via API do GBIF) provêm integralmente de bases públicas primárias. Para contornar a disponibilização heterogênea de microdados pedológicos em nível de subunidade entre ciclos estaduais do IFN, a matriz de 2.400 parcelas segue estruturação semi-sintética controlada (`SEED = 42`) aderente ao desenho de conglomerados do SFB e parametrizada diretamente sobre os táxons e envelopes edafoclimáticos reais de cada bioma.

---

## ⚡ 5. Aceleração Tensorial em GPU e Hiperparâmetros Calibrados

O motor `ImplicitALSRecommenderGPU` resolve de forma exata e paralelizada os sistemas lineares ponderados por abundância de cada época em hardware dedicado:
* **Hardware Utilizado:** `NVIDIA GeForce RTX 3060` (12,00 GB VRAM, Compute Capability 8.6);
* **Ambiente Tensorial:** `PyTorch 2.6.0+cu124` (`torch.linalg.solve` em precisão `float32`);
* **Configuração Ótima Calibrada na Validação ($|\mathcal{V}| = 360$):** $\alpha = 25$, $f = 32$, $\lambda = 0,10$, $\beta = 0,35$ e $\gamma = 0,25$;
* **Tempo de Treinamento do ALS (8 épocas):** **11,06 segundos** sobre as 1.680 parcelas de treinamento (redução monotônica da perda ponderada média de **0,096832** para **0,037507**);
* **Tempo de Avaliação no Teste Cego:** **6,21 segundos** para inferência indutiva (*fold-in*) e diversificação gulosa nas 360 parcelas isoladas.

---

## 🏆 6. Resultados Consolidados da Avaliação Experimental Offline

Toda a seleção paramétrica foi executada exclusivamente nos **90 conglomerados de validação ($|\mathcal{V}| = 360$ parcelas)**, mantendo os **90 conglomerados de teste cego ($|\mathcal{U}_{\text{teste}}| = 360$ parcelas)** integralmente isolados até a aferição final. Sob o protocolo *leave-$k$-out* ($k = 4$ espécies ocultas em $T_u$ dentre 18 observadas, competindo em um *pool* de 100 espécies nativas do mesmo bioma), obtiveram-se os seguintes resultados oficiais:

### 6.1 Cenário Principal — Enriquecimento Florestal ($O_u \neq \emptyset$, $|\mathcal{U}_{\text{teste}}| = 360$)

| Métrica de Avaliação | Baseline 1 (Popularidade) | Baseline 2 (CBF Puro) | Modelo Híbrido (CBF + ALS + ILD) | Ganho Híbrido vs. CBF |
| :--- | :---: | :---: | :---: | :---: |
| **Precision@5** | 0,0822 | 0,3633 | **0,7478** | **+105,8%** |
| **Precision@10** | 0,0931 | 0,2486 | **0,3994** | **+60,7%** |
| **Precision@20** | 0,0918 | 0,1421 | **0,2000** | **+40,8%** |
| **Recall@5** | 0,1028 | 0,4542 | **0,9347** | **+105,8%** |
| **Recall@10** | 0,2326 | 0,6215 | **0,9986** | **+60,7%** |
| **Recall@20** | 0,4590 | 0,7104 | **1,0000** | **+40,8%** |
| **NDCG@5** | 0,0895 | 0,4463 | **0,8913** | **+99,7%** |
| **NDCG@10** | 0,1551 | 0,5317 | **0,9258** | **+74,1%** |
| **NDCG@20** | 0,2436 | 0,5668 | **0,9264** | **+63,4%** |
| **ILD@5 (Diversidade)** | 0,7254 | 0,5374 | **0,6299** | **+17,2%** |
| **ILD@10 (Diversidade)** | 0,7727 | 0,6461 | **0,7662** | **+18,6%** |
| **ILD@20 (Diversidade)** | 0,7999 | 0,7712 | **0,8090** | **+4,9%** |

### 6.2 Cenário Extremo — *Cold-Start* Estrito em Terrenos Degradados ($O_u = \emptyset$, $|\mathcal{U}_{\text{teste}}| = 360$)

Ocultando-se 100% da vegetação local e fornecendo unicamente o laudo abiótico do terreno, a projeção ambiental $k$-NN ($k = 15$) no espaço latente do ALS manteve ganhos expressivos sobre o modelo puramente baseado em conteúdo:

| Modelo em *Cold-Start* Estrito ($O_u = \emptyset$) | Precision@5 | Precision@10 | Recall@10 | NDCG@10 | ILD@10 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline 2 — CBF Puro Cold-Start** | 0,0411 | 0,0481 | 0,1201 | 0,0810 | 0,8391 |
| **Modelo Híbrido ($k$-NN Ambiental + ALS + ILD)** | **0,0844** | **0,0781** | **0,1951** | **0,1403** | **0,8183** |
| **Ganho Relativo sobre CBF** | **+105,4%** | **+62,4%** | **+62,4%** | **+73,2%** | -2,5% |

*Todos os indicadores acima correspondem exatamente aos valores gravados em `Etapa 3/data/processed/metricas_oficiais_etapa3.json` e reportados em `Etapa 3/Etapa_3_ABNT.pdf`.*

---

## 🛠️ 7. Como Instalar e Reproduzir

### Pré-requisitos
* **Python 3.10+** (testado em Python 3.12);
* **GPU NVIDIA compatível com CUDA** (opcional — os notebooks possuem *fallback* transparente e automático para execução em CPU caso CUDA não esteja disponível);
* **Git** instalado.

### Instalação do Ambiente
```bash
# 1. Clonar o repositório
git clone https://github.com/henri-sarmento/ProjetoAplicado3.git
cd ProjetoAplicado3

# 2. Criar e ativar um ambiente virtual isolado (recomendado)
python -m venv .venv
# No Windows (PowerShell):
.venv\Scripts\Activate.ps1
# No Linux / macOS:
# source .venv/bin/activate

# 3. (Opcional — para máquinas com GPU NVIDIA) Instalar PyTorch com suporte a CUDA 12.4
pip install torch --index-url https://download.pytorch.org/whl/cu124

# 4. Instalar as demais dependências verificadas do projeto
pip install -r requirements.txt
```

### Modos de Execução dos Notebooks
Inicie o servidor interativo na pasta dos notebooks:
```bash
jupyter lab "Etapa 3/notebooks/"
```

1. **Modo Rápido — Reprodução Direta da Modelagem e Métricas (~17 s em GPU):**  
   Execute diretamente o notebook `02_pipeline_modelagem_recomendador.ipynb`. Ele consumirá as matrizes limpas já versionadas em `Etapa 3/data/processed/`, treinará o ALS, reproduzirá as tabelas de validação e teste cego (incluindo *cold-start*) e emitirá os relatórios explicáveis Top-$K$.
2. **Modo Completo *End-to-End* — Da Extração Bruta à Prescrição:**  
   Execute primeiramente `01_aquisicao_exploracao_limpeza_dados.ipynb` (que realiza o download automático do DwC-A do JBRJ e consultas REST ao GBIF em `Etapa 3/data/raw/`, aplica resolução taxonômica e *spatial thinning* e regenera `Etapa 3/data/processed/`) e, na sequência, execute `02_pipeline_modelagem_recomendador.ipynb`.

---

## 📜 Licença e Uso Responsável

Trabalho acadêmico desenvolvido no Curso Superior de Tecnologia em **Ciência de Dados e Inteligência Artificial** da **Universidade Presbiteriana Mackenzie**. Os dados primários utilizados são públicos e abertos, providos pelo Jardim Botânico do Rio de Janeiro (JBRJ), Global Biodiversity Information Facility (GBIF) e referenciais metodológicos do Serviço Florestal Brasileiro (SFB/MAPA). O sistema atua exclusivamente como ferramenta computacional de **apoio à decisão técnica**, não substituindo laudos pedológicos locais nem a responsabilidade legal de profissionais habilitados em projetos de intervenção ambiental.
