import numpy as np

def _extract_item_info(item):
    if isinstance(item, dict):
        return item.get('scientific_name', ''), item.get('family', ''), item.get('successional_stage', '')
    elif isinstance(item, (list, tuple)):
        return str(item[0]), '', ''
    else:
        return str(item), '', ''

def precision_at_k(recommended, ground_truth, k=10):
    """
    Precision@K = |Rec@K ∩ GroundTruth| / K
    """
    if k <= 0 or not ground_truth:
        return 0.0
    rec_k = [_extract_item_info(item)[0] for item in recommended[:k]]
    hits = len(set(rec_k).intersection(set(ground_truth)))
    return hits / float(k)

def recall_at_k(recommended, ground_truth, k=10):
    """
    Recall@K = |Rec@K ∩ GroundTruth| / |GroundTruth|
    """
    if not ground_truth:
        return 0.0
    rec_k = [_extract_item_info(item)[0] for item in recommended[:k]]
    hits = len(set(rec_k).intersection(set(ground_truth)))
    return hits / float(len(ground_truth))

def ndcg_at_k(recommended, ground_truth, k=10):
    """
    NDCG@K = DCG@K / IDCG@K
    Recompensa quando espécies relevantes aparecem no topo do ranking.
    """
    if not ground_truth or k <= 0:
        return 0.0
    rec_k = [_extract_item_info(item)[0] for item in recommended[:k]]
    
    dcg = 0.0
    for i, sp in enumerate(rec_k):
        if sp in ground_truth:
            dcg += 1.0 / np.log2(i + 2) # i=0 -> log2(2) = 1

    # IDCG (melhor ordenamento possível)
    n_rel = min(k, len(ground_truth))
    idcg = sum(1.0 / np.log2(r + 2) for r in range(n_rel))
    
    return (dcg / idcg) if idcg > 0 else 0.0

def intra_list_diversity(recommended_items, k=10):
    """
    Intra-List Diversity (ILD - Ziegler et al., 2005):
    Mede a dissimilaridade taxonômica e funcional média entre todos os pares de espécies do Top-K.
    Distância d(i, j): 0.5 se famílias diferentes + 0.5 se estágios sucessionais diferentes.
    """
    rec_k = recommended_items[:k]
    n = len(rec_k)
    if n <= 1:
        return 0.0

    total_dist = 0.0
    n_pairs = 0

    for i in range(n):
        for j in range(i + 1, n):
            _, fam_i, stg_i = _extract_item_info(rec_k[i])
            _, fam_j, stg_j = _extract_item_info(rec_k[j])
            
            d_tax = 0.5 if (fam_i and fam_j and fam_i != fam_j) else (0.25 if not fam_i or not fam_j else 0.0)
            d_func = 0.5 if (stg_i and stg_j and stg_i != stg_j) else (0.25 if not stg_i or not stg_j else 0.0)
            
            total_dist += (d_tax + d_func)
            n_pairs += 1

    return total_dist / float(n_pairs) if n_pairs > 0 else 0.0

def evaluate_recommender(recommender, ground_truth_dict, plots_metadata, k_list=[5, 10, 20]):
    """
    Avalia o recomendador em todas as parcelas do conjunto de teste/validação.
    """
    results = {f'Precision@{k}': [] for k in k_list}
    results.update({f'Recall@{k}': [] for k in k_list})
    results.update({f'NDCG@{k}': [] for k in k_list})
    results.update({f'ILD@{k}': [] for k in k_list})

    for plot_id, gt_species in ground_truth_dict.items():
        if not gt_species:
            continue
        p_meta = plots_metadata.get(plot_id, {})
        biome = p_meta.get('bioma')
        ph = p_meta.get('ph_solo')

        max_k = max(k_list)
        recs = recommender.recommend(plot_id, k=max_k, plot_biome=biome, plot_ph=ph)

        for k in k_list:
            results[f'Precision@{k}'].append(precision_at_k(recs, gt_species, k=k))
            results[f'Recall@{k}'].append(recall_at_k(recs, gt_species, k=k))
            results[f'NDCG@{k}'].append(ndcg_at_k(recs, gt_species, k=k))
            results[f'ILD@{k}'].append(intra_list_diversity(recs, k=k))

    summary = {metric: round(float(np.mean(vals)), 4) for metric, vals in results.items() if vals}
    return summary
