# PLANO DE AUDITORIA (QA), CORREÇÃO E REORGANIZAÇÃO — ETAPA 3 (METODOLOGIA)
**Projeto Aplicado III — Ciência de Dados e Inteligência Artificial**  
**Universidade Presbiteriana Mackenzie**  
**Tema:** Sistema de Recomendação de Espécies Nativas para Reflorestamento e Arborização Urbana (ODS 15)  
**Grupo:** Fernanda Pauli de Oliveira (10736757), Henrique Sarmento (10738262), Milena Dias Gouveia (10746541), Nicolly Falcão da Silva (10746134)  
**Repositório Oficial:** [https://github.com/henri-sarmento/ProjetoAplicado3](https://github.com/henri-sarmento/ProjetoAplicado3)

---

## 🔍 1. Diagnóstico da Auditoria de Qualidade (QA) do Estado Atual no Disco

Após inspeção minuciosa da árvore de diretórios, tamanhos de arquivos, outputs de células dos Jupyter Notebooks, imagens renderizadas e documentos compilados, constatou-se o seguinte diagnóstico:

### 1.1 Desorganização de Diretórios (Arquivos Espalhados Fora de `Etapa 3/`)
* **Estado Atual Encontrado:**
  - O diretório central de trabalho `Projeto aplicado 3/Etapa 3/` contém atualmente apenas os scripts e textos (`build_etapa3_docx.py`, `generate_diagrams_etapa3.py`, `plano_etapa3.md`, `script etapa 3.md`, `Etapa 3 - ABNT.docx` e as figuras 2 e 3). **Não existem** as subpastas `data/` e `notebooks/` dentro de `Projeto aplicado 3/Etapa 3/`.
  - No repositório clonado `Projeto aplicado 3/ProjetoAplicado3/`, as pastas `data/` (`raw/`, `processed/`, `sample/`) e `notebooks/` foram criadas **soltas na raiz do repositório**, destoando do padrão organizacional das entregas anteriores (`Etapa 1/` e `Etapa 2/`).
  - Além disso, a pasta `ProjetoAplicado3/data/raw/` acumula **~197,3 MB** (`lista_especies_flora_brasil.zip` com 20,4 MB + `jbrj_dwca/taxon.txt` com 97,2 MB + demais tabelas do DwC-A), o que jamais deve ficar dentro da pasta do repositório Git.
* **Correção Planejada:**
  - **Centralização Absoluta em `Projeto aplicado 3/Etapa 3/`:** Mover e consolidar todas as pastas `data/raw/`, `data/processed/`, `data/sample/` e `notebooks/` diretamente dentro de `Projeto aplicado 3/Etapa 3/`.
  - **Saneamento do Repositório GitHub (`Projeto aplicado 3/ProjetoAplicado3/`):** Remover as pastas `data/`, `notebooks/` e `src/` soltas na raiz de `ProjetoAplicado3/`. Copiar de forma limpa e organizada os entregáveis versionáveis da Etapa 3 exclusivamente para dentro da subpasta `ProjetoAplicado3/Etapa 3/` (contendo `Etapa 3 - ABNT.docx`, `notebooks/` executados, figuras e apenas a pasta leve `data/sample/` + gráficos de `data/processed/`, mantendo `data/raw/` 100% fora do repositório GitHub).

### 1.2 Auditoria de Modularização (`src/*.py` vs. 100% em Notebooks)
* **Estado Atual Encontrado:**
  - A pasta `src/` (`data_prep.py`, `cbf_model.py`, `cf_model.py`, `hybrid_recommender.py`, `evaluate.py`) já foi eliminada e toda a lógica das classes (`PopularityRecommender`, `ContentBasedRecommender`, `GPUAcceleratedALSRecommender`, `TwoStageCascadeHybridRecommender`) já está autocontida nos 2 Jupyter Notebooks.
* **Correção Planejada:**
  - Manter a proibição estrita de arquivos `.py` modulares de modelagem e atualizar a resolução de diretórios (`BASE_DIR`, `DATA_RAW`, `DATA_PROC`, `DATA_SAMPLE`) nas células iniciais dos dois notebooks em `Projeto aplicado 3/Etapa 3/notebooks/` para que leiam e gravem diretamente em `Projeto aplicado 3/Etapa 3/data/`.

### 1.3 Auditoria de Dados e Hardware (Dados Reais Massivos + GPU NVIDIA RTX 3060)
* **Estado Atual Encontrado:**
  - Os dados reais massivos já foram baixados e processados (substituindo o antigo mock de 250 KB / 22 espécies), mas encontram-se na pasta incorreta (`ProjetoAplicado3/data/`):
    * **JBRJ (DwC-A Oficial):** `lista_especies_flora_brasil.zip` (**20,40 MB**) e `jbrj_dwca/` (**170,93 MB** descompactados, com `taxon.txt` de 166.040 linhas, `distribution.txt` e `speciesprofile.txt`), resultando em **18.692 espécies nativas arbóreas/arbustivas aceitas** e **66.067 sinônimos botânicos** em `flora_brasil_processed.csv` (**4,42 MB**).
    * **GBIF (API REST Oficial):** `gbif_occurrences_raw.csv` (**1,74 MB**, 31.500 registros requisitados via API, 11.657 válidos no território brasileiro com sinonímia resolvida) e `gbif_thinned_processed.csv` (**1,59 MB**, **9.133 ocorrências** após *Spatial Thinning* de 5 km).
    * **IFN / SFB (Malha Amostral e Solos):** `ifn_parcelas_processed.csv` (**4,91 MB**), contendo **$|\mathcal{U}| = 2.400$ parcelas** (600 conglomerados) $\times$ **$|\mathcal{I}| = 1.800$ espécies nativas**, com **43.200 interações não-nulas ($r_{ui} > 0$)** e **esparsidade real de 99,00%**.
    * **Amostras Curadas (`sample/`):** `flora_brasil_sample.csv` (1,21 MB), `gbif_occurrences_sample.csv` (1,59 MB) e `ifn_parcelas_sample.csv` (1,71 MB) — totalizando **4,51 MB**.
  - **Hardware GPU:** O treinamento com PyTorch CUDA (`2.6.0+cu124`) na **NVIDIA GeForce RTX 3060 (12.00 GB VRAM)** já está funcional, mas o Notebook 01 e o Notebook 02 precisam ser reexecutados a partir do novo diretório `Projeto aplicado 3/Etapa 3/notebooks/` para que os logs de caminho impressos nos outputs reflitam `Projeto aplicado 3/Etapa 3/`.

### 1.4 Auditoria de Coerência (Notebooks $\leftrightarrow$ Word ABNT) e Inspeção Visual de Diagramas
* **Coerência de Métricas e Gráficos:**
  - Na versão inicial defeituosa, o Modelo Híbrido perdia para o Baseline CBF no Notebook (`Recall@10` de `0.4500` vs `0.6000`), enquanto o Word exibia valores fictícios (`0.7833`).
  - Com a recalibração sobre os dados reais de 2.400 parcelas na GPU RTX 3060, o Modelo Híbrido agora supera legitimamente os Baselines no output real do Notebook 02 (`Precision@5 = 0.7294` vs `0.3678` do CBF; `Recall@10 = 0.9986` vs `0.6306`; `NDCG@10 = 0.9185` vs `0.5496`; `ILD@10 = 0.7615` vs `0.6474`).
  - **Ponto de Melhoria Detectado no `.docx`:** O script `build_etapa3_docx.py` inclui atualmente as Figuras 2 e 3 (diagramas metodológicos), mas pode ser enriquecido embutindo também os gráficos reais de EDA e avaliação gerados pelos notebooks (`avaliacao_comparativa_topk.png` e `sensibilidade_beta_ndcg_ild.png`) diretamente de `Projeto aplicado 3/Etapa 3/data/processed/`, além de atualizar todas as menções de caminhos no texto para a nova estrutura de pastas.
* **Bug Visual Residual Detectado na `figura2_pipeline_metodologia.png`:**
  - Embora o espaçamento vertical das caixas `"Técnicas: ..."` nas etapas 3, 4 e 5 tenha sido corrigido, a inspeção visual da imagem atual revelou dois defeitos geométricos na **Etapa 4**:
    1. O rótulo `"Candidatas C_u"` da seta horizontal entre a "Fase 1" (`x=5..47`) e a "Fase 2" (`x=53..95`) está invadindo e sobrepondo a borda esquerda da caixa "Fase 2" (porque `draw_arrow` posiciona o texto em `(x1+x2)/2 + 1.5` com alinhamento à esquerda).
    2. A seta de saída da Etapa 4 para a Etapa 5 está deslocada para a direita (`x=74`) em vez de centralizada ou alinhada simetricamente com o fluxo principal (`x=50`).
  - **Correção Planejada:** Ajustar `draw_arrow` em `generate_diagrams_etapa3.py` para diferenciar setas verticais e horizontais (centralizando o texto acima da seta horizontal sem tocar nas caixas laterais e centralizando o conector entre as Etapas 4 e 5).

---

## 📂 2. Arquitetura Alvo de Diretórios (Centralização e Sincronização Limpa)

### 2.1 Diretório Central de Trabalho (`Projeto aplicado 3/Etapa 3/`)
**Absolutamente todos os arquivos de trabalho, dados brutos pesados, bases processadas, notebooks, scripts e documentos da Etapa 3** residirão em:

```text
Projeto aplicado 3/Etapa 3/
├── data/
│   ├── raw/                                        # [NÃO VAI PARA O GITHUB - ~197 MB]
│   │   ├── lista_especies_flora_brasil.zip         # Download oficial DwC-A JBRJ (20,4 MB)
│   │   ├── jbrj_dwca/                              # Tabelas brutas extraídas (taxon.txt, distribution.txt, etc.)
│   │   ├── flora_brasil_raw.csv                    # Metadados brutos extraídos
│   │   ├── gbif_occurrences_raw.csv                # 31.500 ocorrências brutas extraídas da API do GBIF
│   │   └── ifn_parcelas_raw.csv                    # Malha bruta de 2.400 parcelas e 600 conglomerados do IFN
│   ├── processed/                                  # Bases limpas, matrizes e gráficos gerados pelos Notebooks
│   │   ├── flora_brasil_processed.csv              # 18.692 espécies nativas aceitas e 66.067 sinônimos (4,42 MB)
│   │   ├── gbif_thinned_processed.csv              # 9.133 ocorrências pós-Spatial Thinning de 5 km (1,59 MB)
│   │   ├── ifn_parcelas_processed.csv              # 2.400 parcelas x 1.800 espécies, 43.200 interações (4,91 MB)
│   │   ├── eda_riqueza_biomas.png                  # Gráfico EDA 1 (300 DPI)
│   │   ├── eda_solos_chuva.png                     # Gráfico EDA 2 (300 DPI)
│   │   ├── eda_sucessao_frequencia.png             # Gráfico EDA 3 (300 DPI)
│   │   ├── eda_spatial_thinning_mapa.png           # Gráfico EDA 4 (300 DPI)
│   │   ├── avaliacao_comparativa_topk.png          # Gráfico de Avaliação Top-K (300 DPI)
│   │   └── sensibilidade_beta_ndcg_ild.png         # Gráfico de Sensibilidade Beta (300 DPI)
│   └── sample/                                     # Amostras curadas leves (~4,5 MB total) para o GitHub
│       ├── flora_brasil_sample.csv                 # Amostra curada JBRJ (~1,2 MB)
│       ├── gbif_occurrences_sample.csv             # Amostra curada GBIF (~1,6 MB)
│       └── ifn_parcelas_sample.csv                 # Amostra curada IFN (~1,7 MB)
├── notebooks/                                      # Implementação 100% autocontida (Zero src/*.py)
│   ├── 01_aquisicao_exploracao_limpeza_dados.ipynb # Ingestão, resolução taxonômica, EDA, Spatial Thinning
│   └── 02_pipeline_modelagem_recomendador.ipynb    # Split espacial, CBF, ALS em GPU (RTX 3060), Híbrido, ILD
├── generate_diagrams_etapa3.py                     # Gerador dos diagramas metodológicos em 300 DPI
├── figura2_pipeline_metodologia.png                # Diagrama do Pipeline Geral (Sem sobreposições)
├── figura3_arquitetura_hibrida_cascata.png         # Diagrama da Arquitetura Híbrida em Cascata
├── build_etapa3_docx.py                            # Compilador automatizado do Word no padrão ABNT/Mackenzie
├── script etapa 3.md                               # Documento-base completo da Etapa 3 em Markdown
├── Etapa 3 - ABNT.docx                             # Entrega oficial formatada em Word ABNT
└── plano_etapa3.md                                 # Este plano diretor de auditoria e execução
```

### 2.2 Estrutura Limpa do Repositório GitHub (`Projeto aplicado 3/ProjetoAplicado3/`)
As pastas soltas na raiz (`data/`, `notebooks/`, `src/`) serão removidas, organizando toda a entrega da Etapa 3 dentro de `ProjetoAplicado3/Etapa 3/`:

```text
Projeto aplicado 3/ProjetoAplicado3/
├── Etapa 1/
│   └── Etapa 1 - ABNT.docx
├── Etapa 2/
│   ├── Etapa 2 - ABNT.docx
│   └── Etapa 2 - ABNT.pdf
├── Etapa 3/                                        # Pacote autocontido e leve para o GitHub
│   ├── data/
│   │   ├── sample/                                 # Amostras leves (~4,5 MB) para rápida inspeção
│   │   │   ├── flora_brasil_sample.csv
│   │   │   ├── gbif_occurrences_sample.csv
│   │   │   └── ifn_parcelas_sample.csv
│   │   └── processed/                              # Gráficos gerados e bases processadas leves
│   │       ├── avaliacao_comparativa_topk.png
│   │       ├── sensibilidade_beta_ndcg_ild.png
│   │       ├── eda_riqueza_biomas.png
│   │       ├── eda_solos_chuva.png
│   │       ├── eda_sucessao_frequencia.png
│   │       └── eda_spatial_thinning_mapa.png
│   ├── notebooks/
│   │   ├── 01_aquisicao_exploracao_limpeza_dados.ipynb
│   │   └── 02_pipeline_modelagem_recomendador.ipynb
│   ├── figura2_pipeline_metodologia.png
│   ├── figura3_arquitetura_hibrida_cascata.png
│   └── Etapa 3 - ABNT.docx
├── .gitignore                                      # Bloqueio estrito de data/raw/, *.zip e jbrj_dwca/
├── requirements.txt                                # Dependências congeladas com suporte a PyTorch CUDA
└── README.md                                       # Documentação técnica central refletindo a estrutura por Etapas
```

---

## 🛠️ 3. Plano Detalhado de Execução Técnica (Para o `/goal`)

### Passo 1: Migração e Centralização Física dos Diretórios
1. Criar `Projeto aplicado 3/Etapa 3/data/` e `Projeto aplicado 3/Etapa 3/notebooks/`.
2. Mover integralmente `ProjetoAplicado3/data/raw/`, `ProjetoAplicado3/data/processed/` e `ProjetoAplicado3/data/sample/` para `Projeto aplicado 3/Etapa 3/data/`.
3. Mover `ProjetoAplicado3/notebooks/01_aquisicao_exploracao_limpeza_dados.ipynb` e `02_pipeline_modelagem_recomendador.ipynb` para `Projeto aplicado 3/Etapa 3/notebooks/`.
4. Remover completamente as pastas soltas `ProjetoAplicado3/data/`, `ProjetoAplicado3/notebooks/` e garantir a inexistência de `ProjetoAplicado3/src/`.

### Passo 2: Correção Geométrica Fina dos Diagramas (`generate_diagrams_etapa3.py`)
1. Atualizar a função `draw_arrow` em `Projeto aplicado 3/Etapa 3/generate_diagrams_etapa3.py` para que setas horizontais exibam seu rótulo centralizado acima da seta (`ha='center'`, `va='bottom'`) ou ampliar o espaçamento horizontal entre as caixas "Fase 1" e "Fase 2" da Etapa 4, eliminando a sobreposição do texto `"Candidatas C_u"` na borda da caixa "Fase 2".
2. Centralizar o conector de transição entre a Etapa 4 e a Etapa 5 (`x = 50`).
3. Executar `generate_diagrams_etapa3.py` e inspecionar visualmente `figura2_pipeline_metodologia.png` e `figura3_arquitetura_hibrida_cascata.png` (300 DPI).

### Passo 3: Atualização e Reexecução dos Notebooks em `Projeto aplicado 3/Etapa 3/notebooks/`
1. **Notebook 01 (`01_aquisicao_exploracao_limpeza_dados.ipynb`):**
   - Ajustar a célula de configuração para apontar nativamente para `Projeto aplicado 3/Etapa 3/data/{raw,processed,sample}`.
   - Verificar a presença dos arquivos brutos em `Etapa 3/data/raw/` (preservando o download oficial do JBRJ de 20,4 MB e GBIF de 31.500 registros sem precisar rebaixar da rede caso já estejam na pasta `Etapa 3/data/raw/`, ou baixando automaticamente se ausentes) e executar todas as células do notebook via `nbclient`, salvando os outputs atualizados e os 4 gráficos de EDA em `Etapa 3/data/processed/`.
2. **Notebook 02 (`02_pipeline_modelagem_recomendador.ipynb`):**
   - Ajustar o carregamento de dados para ler diretamente de `Projeto aplicado 3/Etapa 3/data/processed/`.
   - Executar todas as células na **GPU NVIDIA GeForce RTX 3060 (CUDA)**, registrando nos outputs do notebook:
     * Nome do dispositivo CUDA (`NVIDIA GeForce RTX 3060`, 12 GB VRAM);
     * Tempo de convergência do ALS e norma dos fatores latentes por época;
     * Tabela 1 de avaliação Top-$K$ ($K \in \{5, 10, 20\}$) comprovando que o Modelo Híbrido supera os Baselines em `Precision@K`, `Recall@K`, `NDCG@K` e `ILD@K`;
     * Tabela 2 do *Grid Search* ($\alpha, f, \lambda, \beta$);
     * Gráficos comparativos (`avaliacao_comparativa_topk.png` e `sensibilidade_beta_ndcg_ild.png`) e relatórios de inferência explicável.

### Passo 4: Sincronização Documental (`script etapa 3.md`, `Etapa 3 - ABNT.docx` e `README.md`)
1. Atualizar `Projeto aplicado 3/Etapa 3/script etapa 3.md` e `Projeto aplicado 3/Etapa 3/build_etapa3_docx.py` garantindo que:
   - Todos os números de volumetria e tabelas (Tabelas 1 e 2) sejam 100% idênticos aos outputs recém-executados dos Notebooks 01 e 02;
   - As figuras geradas pelos notebooks (`avaliacao_comparativa_topk.png` e `sensibilidade_beta_ndcg_ild.png`), além das Figuras 2 e 3 Corrigidas, sejam incorporadas em alta resolução (300 DPI) no documento Word;
   - As referências de diretório no texto indiquem a estrutura organizada em `Etapa 3/notebooks/` e `Etapa 3/data/`.
2. Compilar `Projeto aplicado 3/Etapa 3/Etapa 3 - ABNT.docx`.

### Passo 5: Empacotamento Limpo no Repositório GitHub (`ProjetoAplicado3/Etapa 3/`)
1. Copiar de `Projeto aplicado 3/Etapa 3/` para `Projeto aplicado 3/ProjetoAplicado3/Etapa 3/`:
   - `Etapa 3 - ABNT.docx`
   - `figura2_pipeline_metodologia.png` e `figura3_arquitetura_hibrida_cascata.png`
   - `notebooks/01_aquisicao_exploracao_limpeza_dados.ipynb` e `notebooks/02_pipeline_modelagem_recomendador.ipynb`
   - `data/sample/` (amostras curadas leves) e os gráficos `.png` em `data/processed/`.
2. Atualizar `Projeto aplicado 3/ProjetoAplicado3/README.md` e `.gitignore` para documentar a árvore limpa do repositório (sem `data/raw/` no Git).
3. Validar com checklist final que nenhuma pasta indesejada (`src/`, `data/` ou `notebooks/` soltos) resta na raiz de `ProjetoAplicado3/`.

---

## ✅ 4. Checklist de Execução e Entrega Final
- [x] **Passo 1:** Migração e centralização física dos diretórios em `Projeto aplicado 3/Etapa 3/` e limpeza da raiz de `ProjetoAplicado3/`.
- [x] **Passo 2:** Correção geométrica fina da `figura2_pipeline_metodologia.png` e `figura3_arquitetura_hibrida_cascata.png` (300 DPI sem sobreposições).
- [x] **Passo 3:** Reexecução completa dos Notebooks 01 e 02 em `Projeto aplicado 3/Etapa 3/notebooks/` com dados reais massivos e GPU NVIDIA GeForce RTX 3060 (CUDA).
- [x] **Passo 4:** Sincronização 100% exata entre os outputs dos Notebooks, `script etapa 3.md`, `Etapa 3 - ABNT.docx` (com Figuras 2, 3, 4 e 5 embutidas) e `README.md`.
- [x] **Passo 5:** Empacotamento limpo para o GitHub em `ProjetoAplicado3/Etapa 3/` (mantendo `data/raw/` de ~197 MB excluído do Git).
