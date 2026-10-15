"""
Projeto Aplicado III — Ciência de Dados e Inteligência Artificial (Mackenzie)
Sistema de Recomendação de Espécies Nativas para Reflorestamento e Arborização Urbana (ODS 15)
Módulos do Sistema de Recomendação Híbrido
"""

from .data_prep import load_data, prepare_matrices, encode_features_for_cbf, spatial_cluster_split, create_leave_k_out_mask
from .cbf_model import ContentBasedRecommender
from .cf_model import ImplicitALSRecommender
from .hybrid_recommender import TwoStageCascadeHybridRecommender
from .evaluate import evaluate_recommender, precision_at_k, recall_at_k, ndcg_at_k, intra_list_diversity

__all__ = [
    'load_data',
    'prepare_matrices',
    'encode_features_for_cbf',
    'spatial_cluster_split',
    'create_leave_k_out_mask',
    'ContentBasedRecommender',
    'ImplicitALSRecommender',
    'TwoStageCascadeHybridRecommender',
    'evaluate_recommender',
    'precision_at_k',
    'recall_at_k',
    'ndcg_at_k',
    'intra_list_diversity'
]
