import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'


def create_pipeline_diagram(output_path):
    """
    Figura 2: Metodologia e Pipeline Geral de Engenharia de Dados e Modelagem Híbrida.
    Layout vertical espaçado em 300 DPI sem qualquer sobreposição de textos ou caixas.
    """
    fig, ax = plt.subplots(figsize=(14.5, 20.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    c_ingest = '#1E88E5'
    c_prep = '#43A047'
    c_split = '#FB8C00'
    c_model = '#8E24AA'
    c_eval = '#D81B60'
    c_deploy = '#00897B'
    c_text_dark = '#263238'
    c_text_muted = '#455A64'

    ax.text(50, 98.3, "PIPELINE METODOLÓGICO DE ENGENHARIA DE DADOS E MODELAGEM HÍBRIDA",
            ha='center', va='center', fontsize=15, fontweight='bold', color=c_text_dark)
    ax.text(50, 96.7, "Arquitetura Sistemática de Recomendação Ecológica Top-K para Restauração Florestal (ODS 15)",
            ha='center', va='center', fontsize=11, fontstyle='italic', color=c_text_muted)

    def draw_box(x, y, w, h, title, desc, tech, color_header, color_bg='#FFFFFF'):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.1",
                             facecolor=color_bg, edgecolor='#B0BEC5', linewidth=1.2, zorder=2)
        ax.add_patch(box)
        header_h = 2.35
        header_box = FancyBboxPatch((x, y + h - header_h), w, header_h,
                                    boxstyle="round,pad=0.18,rounding_size=0.8",
                                    facecolor=color_header, edgecolor='none', zorder=3)
        ax.add_patch(header_box)
        ax.text(x + w/2, y + h - header_h/2, title, ha='center', va='center',
                fontsize=9.8, fontweight='bold', color='#FFFFFF', zorder=4)

        tech_h = 1.95
        tech_y = y + 0.55
        tech_box = FancyBboxPatch((x + 0.9, tech_y), w - 1.8, tech_h,
                                  boxstyle="round,pad=0.18,rounding_size=0.5",
                                  facecolor='#ECEFF1', edgecolor='#CFD8DC', linewidth=0.8, zorder=3)
        ax.add_patch(tech_box)
        ax.text(x + w/2, tech_y + tech_h/2, f"Técnica: {tech}", ha='center', va='center',
                fontsize=7.6, fontweight='bold', color=c_text_muted, zorder=4)

        desc_top = y + h - header_h - 0.85
        ax.text(x + 1.1, desc_top, desc, ha='left', va='top',
                fontsize=8.1, color=c_text_dark, zorder=4, multialignment='left', linespacing=1.28)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(facecolor='#455A64', edgecolor='#455A64', width=2.0, headwidth=7.5, headlength=7.5),
                    zorder=5)
        if label:
            if abs(y1 - y2) < 0.5:
                ax.text((x1+x2)/2, y1 + 1.15, label, ha='center', va='bottom',
                        fontsize=7.6, color='#4A148C', fontweight='bold', zorder=6,
                        bbox=dict(boxstyle='round,pad=0.22', facecolor='#F3E5F5', edgecolor='#CE93D8', linewidth=0.7))
            else:
                ax.text((x1+x2)/2 + 1.4, (y1+y2)/2, label, ha='left', va='center',
                        fontsize=8.0, color='#37474F', fontweight='bold', zorder=6)

    # 1. ETAPA: COLETA E INGESTÃO DE DADOS (y: 83.5 a 95.0)
    ax.add_patch(FancyBboxPatch((3, 83.5), 94, 11.5, boxstyle="round,pad=0.5,rounding_size=1.4",
                                facecolor='#F0F4F8', edgecolor='#B0BEC5', linewidth=1.0, linestyle='--', zorder=1))
    ax.text(5, 93.8, "1. COLETA E INGESTÃO DE BASES PÚBLICAS E ESTRUTURAÇÃO AMOSTRAL", fontsize=10, fontweight='bold', color=c_ingest)

    draw_box(5, 84.4, 28, 8.6, "Flora e Funga do Brasil (JBRJ)",
             "• 18.692 espécies arbóreas/arbustivas\n• 66.067 sinônimos (194 famílias)\n• Biomas, hábito e exigência lumínica",
             "Darwin Core Archive (DwC-A) / IPT", c_ingest)

    draw_box(36, 84.4, 28, 8.6, "Malha Amostral IFN (SFB/MAPA)",
             "• 600 conglomerados (2.400 parcelas)\n• 1.800 espécies (43.200 interações)\n• pH, V%, textura e precipitação",
             "Malha 20x20 m Estruturada por Bioma", c_ingest)

    draw_box(67, 84.4, 28, 8.6, "GBIF Ocorrências no Brasil",
             "• 31.500 registros via API REST\n• 11.657 presenças válidas no Brasil\n• Coordenadas decimais auditadas",
             "GBIF REST API Multithreaded", c_ingest)

    draw_arrow(19, 84.4, 25, 80.6)
    draw_arrow(50, 84.4, 50, 80.6)
    draw_arrow(81, 84.4, 75, 80.6)

    # 2. ETAPA: PRÉ-PROCESSAMENTO E ENGENHARIA (y: 66.4 a 80.5)
    ax.add_patch(FancyBboxPatch((3, 66.4), 94, 14.1, boxstyle="round,pad=0.5,rounding_size=1.4",
                                facecolor='#F1F8E9', edgecolor='#C5E1A5', linewidth=1.0, linestyle='--', zorder=1))
    ax.text(5, 79.2, "2. PRÉ-PROCESSAMENTO, SANEAMENTO TAXONÔMICO E ENGENHARIA DE ATRIBUTOS", fontsize=10, fontweight='bold', color=c_prep)

    draw_box(5, 67.3, 28, 11.0, "Resolução Taxonômica",
             "• Unificação por acceptedNameUsage\n• 538 sinônimos convertidos no GBIF\n• Expurgo de híbridos e exóticas\n• Vocabulário JBRJ como autoridade",
             "Dicionário Relacional DwC-A JBRJ", c_prep)

    draw_box(36, 67.3, 28, 11.0, "Subamostragem & Imputação",
             "• Spatial Thinning (grade 0,05° ~5,5 km)\n• 11.657 → 9.134 registros (-21,64%)\n• Imputação por conservadorismo\n  filogenético (gênero → família)",
             "Filtro Espacial em Grade / Filogenia", c_prep)

    draw_box(67, 67.3, 28, 11.0, "Vetorização & Matrizes",
             "• One-Hot Encoding edafoclimático\n• Escalonamento contínuo [0, 1]\n• Matriz R (2.400 x 1.800) esparsa\n• Esparsidade estrita de 99,00%",
             "Tensores Esparsos / Vetores ℝᵈ", c_prep)

    draw_arrow(50, 66.4, 50, 63.6, "Bases Saneadas")

    # 3. ETAPA: DIVISÃO ESPACIAL SEM DATA LEAKAGE (y: 50.2 a 63.5)
    ax.add_patch(FancyBboxPatch((3, 50.2), 94, 13.3, boxstyle="round,pad=0.5,rounding_size=1.4",
                                facecolor='#FFF8E1', edgecolor='#FFE082', linewidth=1.0, linestyle='--', zorder=1))
    ax.text(5, 62.2, "3. DIVISÃO ESPACIAL ESTRATIFICADA POR CONGLOMERADOS (ZERO LEAKAGE)", fontsize=10, fontweight='bold', color=c_split)

    draw_box(5, 51.1, 28, 10.2, "Treino Espacial (70%)",
             "• 420 conglomerados (1.680 parcelas)\n• 30.240 interações observadas\n• Aprendizado de fatores X, Y (ALS)\n• Índice ambiental k-NN (Cold-Start)",
             "Spatial Cluster Split (Isolado)", c_split)

    draw_box(36, 51.1, 28, 10.2, "Validação (15%)",
             "• 90 conglomerados (360 parcelas)\n• Calibração exclusiva (α, f, λ, β, γ)\n• Mascaramento k=4 spp. (22,2%)\n• Zero contato com Teste Cego",
             "Leave-K-Out (k=4 | 22,2%)", c_split)

    draw_box(67, 51.1, 28, 10.2, "Teste Cego (15%)",
             "• 90 conglomerados (360 parcelas)\n• Aferição única de generalização\n• Cenários O_u ≠ ∅ e Cold-Start O_u = ∅\n• Pool competitivo por bioma",
             "Avaliação Offline Top-K & ILD", c_split)

    draw_arrow(50, 50.2, 50, 47.7)

    # 4. ETAPA: MODELAGEM HÍBRIDA EM CASCATA (y: 27.2 a 47.6)
    ax.add_patch(FancyBboxPatch((3, 27.2), 94, 20.4, boxstyle="round,pad=0.5,rounding_size=1.4",
                                facecolor='#F3E5F5', edgecolor='#CE93D8', linewidth=1.0, linestyle='--', zorder=1))
    ax.text(5, 46.3, "4. MODELAGEM RECOMENDADORA HÍBRIDA EM DUAS FASES (TWO-STAGE CASCADE)", fontsize=10, fontweight='bold', color=c_model)

    draw_box(4.5, 28.2, 40.0, 17.2, "Fase 1: Filtragem por Conteúdo (CBF)",
             "• Adequabilidade terreno u x espécie i\n• Nicho Fundamental de Hutchinson\n• Filtro rígido (Hard Filter) de bioma/solo\n• Parametrizável para restrições urbanas\n• Normalização Min-Max intra-candidatas\n• Saída: Subconjunto C_u viável",
             "Adequabilidade Abiótica + Hard Filter", c_model)

    draw_box(55.5, 28.2, 40.0, 17.2, "Fase 2: Filtragem Colaborativa (CF-ALS)",
             "• Confiança ponderada: c_ui = 1 + α·r_ui\n• ALS acelerado em GPU (RTX 3060 CUDA)\n• Regeneração: ALS Fold-In analítico\n• Terreno vazio (O_u=∅): Projeção k-NN\n• Fusão: S = β·s̃_CBF + (1-β)·s̃_CF\n• Seleção gulosa de diversidade (γ)",
             "PyTorch CUDA ALS + Fold-In / k-NN", c_model)

    draw_arrow(45.1, 36.8, 54.9, 36.8, "Candidatas\nC_u")
    draw_arrow(50, 27.2, 50, 25.1)

    # 5. ETAPA: AVALIAÇÃO EXPERIMENTAL E OTIMIZAÇÃO (y: 9.8 a 25.0)
    ax.add_patch(FancyBboxPatch((3, 9.8), 94, 15.2, boxstyle="round,pad=0.5,rounding_size=1.4",
                                facecolor='#FCE4EC', edgecolor='#F48FB1', linewidth=1.0, linestyle='--', zorder=1))
    ax.text(5, 23.7, "5. AVALIAÇÃO TOP-K, DIVERSIFICAÇÃO FUNCIONAL E OTIMIZAÇÃO", fontsize=10, fontweight='bold', color=c_eval)

    draw_box(5, 10.7, 42, 12.1, "Métricas de Recuperação & Ranking",
             "• Precision@K, Recall@K e NDCG@K (K = 5, 10, 20)\n• Monotonicidade verificada (P@5 > P@10 > P@20)\n• Comparativo: Popularidade vs. CBF vs. Híbrido\n• Teste complementar em Cold-Start estrito",
             "Avaliação Offline Top-K (Teste Cego)", c_eval)

    draw_box(53, 10.7, 42, 12.1, "Diversidade & Grid Search (Validação)",
             "• Intra-List Diversity (ILD — família + sucessão)\n• Grid Search estrito na Validação (|V| = 360):\n  α ∈ {5..80}, f ∈ {16..64}, λ, β ∈ [0,1] e γ\n• Compromisso ótimo acurácia-resiliência",
             "ILD (Ziegler et al.) / Grid Search", c_eval)

    draw_arrow(50, 9.8, 50, 7.4)

    # 6. ETAPA: IMPLANTAÇÃO E MONITORAMENTO (y: 1.2 a 7.2)
    ax.add_patch(FancyBboxPatch((8, 1.2), 84, 6.0, boxstyle="round,pad=0.5,rounding_size=1.2",
                                facecolor=c_deploy, edgecolor='#004D40', linewidth=1.2, zorder=2))
    ax.text(50, 5.4, "6. REPRODUTIBILIDADE E GOVERNANÇA FUTURA DE IMPLANTAÇÃO",
            ha='center', va='center', fontsize=10.5, fontweight='bold', color='#FFFFFF', zorder=4)
    ax.text(50, 3.8, "2 Jupyter Notebooks Autocontidos • Sementes Fixas (SEED=42) • Inferência Explicável Auditável no GitHub",
            ha='center', va='center', fontsize=8.6, fontweight='bold', color='#E0F2F1', zorder=4)
    ax.text(50, 2.3, "Governança Prevista: Monitoramento de Taxonomic Drift (JBRJ) • Climate Drift • Apoio Técnico Human-in-the-Loop",
            ha='center', va='center', fontsize=8.0, color='#B2DFDB', zorder=4)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura 2 salva com sucesso em: {output_path}")


def create_architecture_diagram(output_path):
    """
    Figura 3: Arquitetura Conceitual Híbrida em Cascata (Two-Stage Cascade Hybrid)
    """
    fig, ax = plt.subplots(figsize=(13.5, 10.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    c_cbf = '#1565C0'
    c_cf = '#6A1B9A'
    c_input = '#37474F'
    c_output = '#2E7D32'

    ax.text(50, 96.8, "ARQUITETURA RECOMENDADORA HÍBRIDA EM DUAS FASES (TWO-STAGE CASCADE)",
            ha='center', va='center', fontsize=13.5, fontweight='bold', color='#263238')
    ax.text(50, 94.2, "Acoplamento entre Nicho Fundamental (CBF), Nicho Efetivo (CF-ALS em GPU) e Diversificação Gulosa (ILD)",
            ha='center', va='center', fontsize=9.8, fontstyle='italic', color='#546E7A')

    b_input = FancyBboxPatch((16, 82.0), 68, 9.2, boxstyle="round,pad=0.5,rounding_size=1.2",
                             facecolor='#ECEFF1', edgecolor=c_input, linewidth=1.5, zorder=2)
    ax.add_patch(b_input)
    ax.text(50, 88.2, "ENTRADA: PERFIL EDAFOCLIMÁTICO DO SÍTIO (u) E REMANESCENTES (O_u)", ha='center', va='center',
            fontsize=11.0, fontweight='bold', color=c_input, zorder=3)
    ax.text(50, 84.5, "Vetor u ∈ ℝᵈ (Bioma, Textura, pH, V%, Chuva) + Espécies Observadas O_u (ou O_u = ∅ em Cold-Start)",
            ha='center', va='center', fontsize=8.8, color='#37474F', zorder=3)

    ax.annotate('', xy=(50, 73.2), xytext=(50, 82.0),
                arrowprops=dict(facecolor='#455A64', edgecolor='#455A64', width=2.0, headwidth=7.5, headlength=7.5), zorder=5)

    b_cbf = FancyBboxPatch((10, 48.5), 80, 24.5, boxstyle="round,pad=0.5,rounding_size=1.5",
                           facecolor='#E3F2FD', edgecolor=c_cbf, linewidth=1.5, zorder=2)
    ax.add_patch(b_cbf)
    ax.text(50, 70.2, "FASE 1: FILTRAGEM BASEADA EM CONTEÚDO (CBF) — NICHO FUNDAMENTAL", ha='center', va='center',
            fontsize=11.2, fontweight='bold', color=c_cbf, zorder=3)
    ax.text(13.5, 66.2, "• Fundamentação Ecológica: Envelope Abiótico do Nicho Fundamental de Hutchinson (1957)", fontsize=8.9, color='#0D47A1', zorder=3)
    ax.text(13.5, 63.2, "• Base Taxonômica Mestre: Flora e Funga do Brasil (JBRJ) — 18.692 espécies nativas aceitas", fontsize=8.9, color='#0D47A1', zorder=3)
    ax.text(13.5, 60.2, "• Adequabilidade Edafoclimática: Resposta contínua a pH e pluviosidade + afinidade taxonômica", fontsize=8.9, fontweight='bold', color='#1A237E', zorder=3)
    ax.text(13.5, 57.2, "• Poda Rígida (Hard Filter): Eliminação imediata de espécies fora do bioma (extensível a restrições urbanas)", fontsize=8.9, color='#B71C1C', zorder=3)

    b_cbf_out = FancyBboxPatch((22, 49.6), 56, 4.8, boxstyle="round,pad=0.3,rounding_size=0.8",
                               facecolor='#BBDEFB', edgecolor=c_cbf, linewidth=1.0, zorder=3)
    ax.add_patch(b_cbf_out)
    ax.text(50, 52.0, "Saída da Fase 1: Subconjunto Viável C_u ⊂ I e Escore Normalizado s̃_CBF(u, i) ∈ [0, 1]",
            ha='center', va='center', fontsize=9.1, fontweight='bold', color='#0D47A1', zorder=4)

    ax.annotate('', xy=(50, 40.2), xytext=(50, 48.5),
                arrowprops=dict(facecolor='#455A64', edgecolor='#455A64', width=2.0, headwidth=7.5, headlength=7.5), zorder=5)
    ax.text(52, 44.2, "Subconjunto Viável C_u", fontsize=8.6, fontweight='bold', color='#1565C0', zorder=6)

    b_cf = FancyBboxPatch((10, 13.8), 80, 26.2, boxstyle="round,pad=0.5,rounding_size=1.5",
                          facecolor='#F3E5F5', edgecolor=c_cf, linewidth=1.5, zorder=2)
    ax.add_patch(b_cf)
    ax.text(50, 37.2, "FASE 2: FILTRAGEM COLABORATIVA (CF-ALS EM GPU) & DIVERSIFICAÇÃO ILD", ha='center', va='center',
            fontsize=11.0, fontweight='bold', color=c_cf, zorder=3)
    ax.text(13.5, 33.4, "• Confiança Implícita (Hu, Koren & Volinsky, 2008): c_ui = 1 + α·r_ui | Treino em GPU RTX 3060", fontsize=8.9, fontweight='bold', color='#311B92', zorder=3)
    ax.text(13.5, 30.4, "• Inferência em Regeneração (O_u ≠ ∅): Projeção analítica ALS Fold-In sobre remanescentes", fontsize=8.9, color='#4A148C', zorder=3)
    ax.text(13.5, 27.4, "• Inferência em Cold-Start Estrito (O_u = ∅): Projeção ambiental k-NN (k=10 parcelas similares)", fontsize=8.9, color='#4A148C', zorder=3)
    ax.text(13.5, 24.4, "• Reordenamento Guloso (MMR Ecológico): Maximiza V(i) = (1 - γ)·S(u, i) + γ·div(i, S_sel)", fontsize=8.9, color='#4A148C', zorder=3)

    b_cf_out = FancyBboxPatch((15, 14.9), 70, 6.2, boxstyle="round,pad=0.3,rounding_size=0.8",
                              facecolor='#E1BEE7', edgecolor=c_cf, linewidth=1.0, zorder=3)
    ax.add_patch(b_cf_out)
    ax.text(50, 18.0, "Fusão Normalizada: S(u, i) = β · s̃_CBF(u, i) + (1 - β) · s̃_CF(u, i)   [β = 0,35 | γ = 0,25]\nCalibrada estritamente no Conjunto de Validação (|V| = 360 parcelas)",
            ha='center', va='center', fontsize=8.9, fontweight='bold', color='#4A148C', zorder=4)

    ax.annotate('', xy=(50, 7.6), xytext=(50, 13.8),
                arrowprops=dict(facecolor='#455A64', edgecolor='#455A64', width=2.0, headwidth=7.5, headlength=7.5), zorder=5)

    b_out = FancyBboxPatch((18, 0.6), 64, 6.8, boxstyle="round,pad=0.5,rounding_size=1.2",
                           facecolor='#E8F5E9', edgecolor=c_output, linewidth=1.5, zorder=2)
    ax.add_patch(b_out)
    ax.text(50, 5.0, "PRESCRIÇÃO EXPLICÁVEL TOP-K ESPÉCIES NATIVAS", ha='center', va='center',
            fontsize=11.2, fontweight='bold', color=c_output, zorder=3)
    ax.text(50, 2.2, "Viabilidade Abiótica + Sinergia Fitossociológica + Diversidade Taxonômica e Sucessional (ILD)",
            ha='center', va='center', fontsize=8.5, color='#1B5E20', zorder=3)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura 3 salva com sucesso em: {output_path}")


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    fig2 = os.path.join(out_dir, "figura2_pipeline_metodologia.png")
    fig3 = os.path.join(out_dir, "figura3_arquitetura_hibrida_cascata.png")
    create_pipeline_diagram(fig2)
    create_architecture_diagram(fig3)
