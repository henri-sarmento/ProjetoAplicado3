import numpy as np
import pandas as pd

class TwoStageCascadeHybridRecommender:
    """
    Arquitetura Híbrida Sequencial em Duas Fases (Two-Stage Cascade Hybrid).
    Fase 1: Filtragem por Conteúdo (Nicho Fundamental) -> Conjunto C_u de Candidatas Viáveis.
    Fase 2: Ranqueamento Colaborativo ALS (Nicho Efetivo) -> Combinação linear S(u, i).
    Pós-Processamento: Maximização de Diversidade Intra-Lista (ILD) e resiliência ecológica.
    """
    def __init__(self, cbf_model, cf_model, df_flora, beta=0.40):
        self.cbf = cbf_model
        self.cf = cf_model
        self.df_flora = df_flora.set_index('accepted_name')
        self.beta = beta # Peso atribuído ao conteúdo (0 <= beta <= 1)

    def set_beta(self, beta):
        """Ajusta o coeficiente calibrador híbrido."""
        if not (0.0 <= beta <= 1.0):
            raise ValueError("O parâmetro beta deve estar no intervalo [0.0, 1.0].")
        self.beta = beta

    def recommend(self, plot_id, k=10, plot_biome=None, plot_ph=None, apply_diversification=True):
        """
        Gera a recomendação Top-K final para uma parcela.
        """
        # Fase 1: Geração de Candidatas Viáveis via Conteúdo
        cbf_candidates = self.cbf.get_candidacy_set(plot_id, plot_biome=plot_biome, plot_ph=plot_ph, min_similarity=0.10)
        if not cbf_candidates:
            # Fallback sem poda rígida se nenhum candidato passar
            cbf_candidates = self.cbf.get_candidacy_set(plot_id, min_similarity=0.0)

        # Fase 2: Reranking Colaborativo (ALS)
        cf_scores = self.cf.predict_all_for_plot(plot_id)

        # Combinação linear ponderada: S(u, i) = beta * Simil_CBF + (1 - beta) * CF_Score
        hybrid_ranked = []
        for sp, sim_score in cbf_candidates:
            cf_val = cf_scores.get(sp, 0.0)
            s_ui = self.beta * sim_score + (1.0 - self.beta) * cf_val
            
            flora_info = self.df_flora.loc[sp] if sp in self.df_flora.index else {}
            hybrid_ranked.append({
                'scientific_name': sp,
                'family': flora_info.get('family', 'Indeterminada'),
                'successional_stage': flora_info.get('successional_stage', 'Secundária'),
                'biome': flora_info.get('biome', 'N/A'),
                'cbf_score': round(float(sim_score), 4),
                'cf_score': round(float(cf_val), 4),
                'hybrid_score': round(float(s_ui), 4)
            })

        # Ordenação pelo escore híbrido decrescente
        hybrid_ranked.sort(key=lambda x: x['hybrid_score'], reverse=True)

        if not apply_diversification or len(hybrid_ranked) <= k:
            return hybrid_ranked[:k]

        # Pós-processamento de Diversificação Sucessional e Taxonômica
        # Garante mistura saudável de pioneiras, secundárias e clímax no Top-K
        diversified_top_k = []
        seen_families = set()
        stages_count = {'Pioneira': 0, 'Secundária Inicial': 0, 'Secundária Tardia': 0, 'Clímax': 0}

        # 1. Primeira passada: prioriza diversidade de estágios e famílias
        remaining = []
        for item in hybrid_ranked:
            stg = item['successional_stage']
            fam = item['family']
            
            # Limita a 3 espécies da mesma família no Top-K e equilibra estágios
            fam_count = sum(1 for d in diversified_top_k if d['family'] == fam)
            if fam_count < 2 and stages_count.get(stg, 0) < max(2, k // 3):
                diversified_top_k.append(item)
                stages_count[stg] = stages_count.get(stg, 0) + 1
            else:
                remaining.append(item)
            
            if len(diversified_top_k) == k:
                break

        # 2. Segunda passada: completa se necessário respeitando o ranking
        if len(diversified_top_k) < k:
            for item in remaining:
                if item not in diversified_top_k:
                    diversified_top_k.append(item)
                if len(diversified_top_k) == k:
                    break

        return diversified_top_k
