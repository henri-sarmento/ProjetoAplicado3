import numpy as np
from scipy.sparse import csr_matrix

try:
    import implicit
    from implicit.als import AlternatingLeastSquares
    HAS_IMPLICIT_LIB = True
except ImportError:
    HAS_IMPLICIT_LIB = False

class ImplicitALSRecommender:
    """
    Fase 2: Filtragem Colaborativa com Feedback Implícito (CF) — Nicho Efetivo / Fitossociologia.
    Fatoração matricial via Mínimos Quadrados Alternados (ALS - Hu, Koren & Volinsky, 2008),
    capturando coocorrência e complementariedade ecológica entre espécies nas parcelas do IFN.
    """
    def __init__(self, factors=32, regularization=0.1, alpha=40.0, iterations=20, random_state=42):
        self.factors = factors
        self.regularization = regularization
        self.alpha = alpha
        self.iterations = iterations
        self.random_state = random_state
        
        self.model = None
        self.user_factors = None
        self.item_factors = None
        self.plot2idx = None
        self.idx2plot = None
        self.species2idx = None
        self.idx2species = None

    def fit(self, R_sparse, plot2idx, species2idx):
        """
        Treina o modelo ALS sobre a matriz esparsa de interação parcela-espécie.
        R_sparse: matriz CSR (M parcelas x N espécies) com abundância r_ui.
        """
        self.plot2idx = plot2idx
        self.idx2plot = {i: p for p, i in plot2idx.items()}
        self.species2idx = species2idx
        self.idx2species = {i: s for s, i in species2idx.items()}

        # Hu, Koren & Volinsky: Confiança c_ui = 1 + alpha * r_ui
        # O pacote implicit recebe a matriz multiplicada por alpha
        C_sparse = (R_sparse * self.alpha).astype(np.float32)

        if HAS_IMPLICIT_LIB:
            self.model = AlternatingLeastSquares(
                factors=self.factors,
                regularization=self.regularization,
                iterations=self.iterations,
                random_state=self.random_state
            )
            # implicit 0.6+ espera matriz (user x item) no fit
            self.model.fit(C_sparse, show_progress=False)
            self.user_factors = self.model.user_factors
            self.item_factors = self.model.item_factors
        else:
            # Fallback robusto em NumPy/SciPy puro
            self._fit_numpy_fallback(R_sparse)

        return self

    def _fit_numpy_fallback(self, R_sparse):
        """
        Implementação pura em NumPy do ALS para feedback implícito (Hu, Koren & Volinsky).
        """
        np.random.seed(self.random_state)
        M, N = R_sparse.shape
        f = self.factors
        X = np.random.normal(0, 0.01, (M, f)).astype(np.float32)
        Y = np.random.normal(0, 0.01, (N, f)).astype(np.float32)
        
        R_dense = R_sparse.toarray()
        P = (R_dense > 0).astype(np.float32)
        C = 1.0 + self.alpha * R_dense
        I_f = np.eye(f, dtype=np.float32) * self.regularization

        for _ in range(self.iterations):
            # Passo 1: Atualiza X (parcelas)
            YtY = Y.T @ Y
            for u in range(M):
                Cu = C[u]
                diag_Cu_minus_I = Cu - 1.0
                # Y^T (C_u - I) Y
                A = YtY + (Y.T * diag_Cu_minus_I) @ Y + I_f
                b = Y.T @ (Cu * P[u])
                X[u] = np.linalg.solve(A, b)

            # Passo 2: Atualiza Y (espécies)
            XtX = X.T @ X
            for i in range(N):
                Ci = C[:, i]
                diag_Ci_minus_I = Ci - 1.0
                A = XtX + (X.T * diag_Ci_minus_I) @ X + I_f
                b = X.T @ (Ci * P[:, i])
                Y[i] = np.linalg.solve(A, b)

        self.user_factors = X
        self.item_factors = Y

    def predict_score(self, plot_id, species_name):
        """
        Retorna a pontuação de afinidade fitossociológica predita p̂_ui = x_u^T y_i.
        """
        if plot_id not in self.plot2idx or species_name not in self.species2idx:
            return 0.0
            
        u_idx = self.plot2idx[plot_id]
        i_idx = self.species2idx[species_name]
        
        score = float(np.dot(self.user_factors[u_idx], self.item_factors[i_idx]))
        return score

    def predict_all_for_plot(self, plot_id):
        """
        Prediz a afinidade fitossociológica para todas as espécies conhecidas.
        """
        if plot_id not in self.plot2idx:
            raise ValueError(f"Parcela {plot_id} não cadastrada no modelo colaborativo.")
            
        u_idx = self.plot2idx[plot_id]
        raw_scores = self.user_factors[u_idx] @ self.item_factors.T
        
        # Normalização Min-Max para a faixa [0, 1]
        s_min = raw_scores.min()
        s_max = raw_scores.max()
        norm_scores = (raw_scores - s_min) / (s_max - s_min + 1e-8) if s_max > s_min else raw_scores
        
        return {self.idx2species[i]: float(norm_scores[i]) for i in range(len(self.idx2species))}
