import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ContentBasedRecommender:
    """
    Fase 1: Filtragem Baseada em Conteúdo (CBF) — Nicho Fundamental de Hutchinson.
    Compara vetores edafoclimáticos do terreno de entrada com as tolerâncias fisiológicas
    das espécies via Similaridade do Cosseno, aplicando poda rígida de inaptidão.
    """
    def __init__(self, user_vectors, item_vectors, plot_list, species_list, df_flora):
        self.user_vectors = user_vectors
        self.item_vectors = item_vectors
        self.plot_list = plot_list
        self.species_list = species_list
        self.df_flora = df_flora.set_index('accepted_name')
        
        self.plot2idx = {p: i for i, p in enumerate(plot_list)}
        self.species2idx = {s: i for i, s in enumerate(species_list)}
        
        # Pré-computa matriz de similaridade do cosseno
        self.sim_matrix = cosine_similarity(self.user_vectors, self.item_vectors)

    def is_physiologically_viable(self, plot_biome, plot_ph, species_name):
        """
        Poda rígida (Hard Filter): verifica se a espécie viola limites fisiológicos do nicho fundamental.
        """
        if species_name not in self.df_flora.index:
            return False
        row = self.df_flora.loc[species_name]
        
        # 1. Bioma de ocorrência natural
        if plot_biome not in str(row['biome']):
            return False
            
        # 2. Tolerância a pH
        ph_min = float(row.get('ph_min', 4.0)) - 0.5
        ph_max = float(row.get('ph_max', 8.0)) + 0.5
        if not (ph_min <= plot_ph <= ph_max):
            return False
            
        return True

    def get_candidacy_set(self, plot_id, plot_biome=None, plot_ph=None, min_similarity=0.20):
        """
        Retorna o conjunto C_u de espécies candidatas viáveis para a Fase 2 (Reranking).
        """
        if plot_id not in self.plot2idx:
            raise ValueError(f"Parcela {plot_id} não encontrada no índice CBF.")
            
        u_idx = self.plot2idx[plot_id]
        scores = self.sim_matrix[u_idx].copy()
        
        candidates = []
        for i_idx, sp in enumerate(self.species_list):
            sim_score = scores[i_idx]
            
            # Aplica verificação abiótica se parâmetros fornecidos
            viable = True
            if plot_biome is not None and plot_ph is not None:
                viable = self.is_physiologically_viable(plot_biome, plot_ph, sp)
            
            if viable and sim_score >= min_similarity:
                candidates.append((sp, float(sim_score)))
                
        # Ordena decrescente por similaridade do cosseno
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def recommend(self, plot_id, k=10, plot_biome=None, plot_ph=None):
        """
        Recomendação direta Top-K baseada puramente em Conteúdo (Linha de Base / Baseline).
        Retorna lista de dicionários com metadados para compatibilidade com avaliador.
        """
        candidates = self.get_candidacy_set(plot_id, plot_biome, plot_ph, min_similarity=0.0)
        top_k = candidates[:k]
        result = []
        for sp, score in top_k:
            row = self.df_flora.loc[sp] if sp in self.df_flora.index else {}
            result.append({
                'scientific_name': sp,
                'family': row.get('family', 'Indeterminada'),
                'successional_stage': row.get('successional_stage', 'Secundária'),
                'biome': row.get('biome', 'N/A'),
                'cbf_score': round(float(score), 4),
                'cf_score': 0.0,
                'hybrid_score': round(float(score), 4)
            })
        return result
