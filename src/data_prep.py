import os
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler

def load_data(data_dir=None):
    """
    Carrega as bases de dados processadas (ou amostrais se processed não existir).
    """
    if data_dir is None:
        # Detecta diretório data
        curr = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(curr), 'data')
    
    proc_dir = os.path.join(data_dir, 'processed')
    sample_dir = os.path.join(data_dir, 'sample')
    target_dir = proc_dir if os.path.exists(proc_dir) and os.path.exists(os.path.join(proc_dir, 'flora_brasil_processed.csv')) else sample_dir

    df_flora = pd.read_csv(os.path.join(target_dir, 'flora_brasil_processed.csv' if target_dir == proc_dir else 'flora_brasil_sample.csv'))
    df_ifn = pd.read_csv(os.path.join(target_dir, 'ifn_parcelas_processed.csv' if target_dir == proc_dir else 'ifn_parcelas_sample.csv'))
    df_gbif = pd.read_csv(os.path.join(target_dir, 'gbif_thinned_processed.csv' if target_dir == proc_dir else 'gbif_occurrences_sample.csv'))

    return df_flora, df_ifn, df_gbif

def prepare_matrices(df_ifn, df_flora):
    """
    Constrói mapeamentos de índices e a matriz esparsa de interação R (parcelas x espécies).
    """
    plots = sorted(df_ifn['plot_id'].unique())
    species = sorted(df_flora['accepted_name'].unique())

    plot2idx = {p: i for i, p in enumerate(plots)}
    idx2plot = {i: p for i, p in enumerate(plots)}
    species2idx = {s: i for i, s in enumerate(species)}
    idx2species = {i: s for i, s in enumerate(species)}

    row_ind = [plot2idx[p] for p in df_ifn['plot_id'] if p in plot2idx and df_ifn.loc[df_ifn['plot_id'] == p, 'accepted_name'].iloc[0] in species2idx]
    
    rows, cols, data = [], [], []
    for _, row in df_ifn.iterrows():
        p = row['plot_id']
        s = row['accepted_name']
        if p in plot2idx and s in species2idx:
            rows.append(plot2idx[p])
            cols.append(species2idx[s])
            data.append(float(row['individuos_vivos']))

    R_sparse = csr_matrix((data, (rows, cols)), shape=(len(plots), len(species)), dtype=np.float32)

    return R_sparse, plot2idx, idx2plot, species2idx, idx2species

def encode_features_for_cbf(df_ifn, df_flora):
    """
    Vetoriza variáveis ambientais das parcelas (u) e tolerâncias das espécies (i) para CBF.
    """
    species_list = sorted(df_flora['accepted_name'].unique())
    
    # 1. Atributos das Espécies (i)
    # Codificação de Biomas suportados (Mata Atlântica, Cerrado, etc.)
    biomes = ['Mata Atlântica', 'Cerrado', 'Amazônia', 'Caatinga', 'Pantanal']
    biome_mat = np.zeros((len(species_list), len(biomes)), dtype=np.float32)
    
    # Sucessão: Pioneira (1, 0, 0), Secundária (0, 1, 0), Clímax (0, 0, 1)
    stages = ['Pioneira', 'Secundária Inicial', 'Secundária Tardia', 'Clímax']
    stage_mat = np.zeros((len(species_list), len(stages)), dtype=np.float32)

    # Faixas de pH normalizadas (4.0 a 8.5)
    ph_min_vec = np.zeros((len(species_list), 1), dtype=np.float32)
    ph_max_vec = np.zeros((len(species_list), 1), dtype=np.float32)

    # Tolerância a seca: Baixa (0.2), Média (0.6), Alta (1.0)
    drought_map = {'Baixa': 0.2, 'Média': 0.6, 'Alta': 1.0}
    drought_vec = np.zeros((len(species_list), 1), dtype=np.float32)

    for i, sp in enumerate(species_list):
        sp_row = df_flora[df_flora['accepted_name'] == sp].iloc[0]
        # Biomas
        for b_idx, b_name in enumerate(biomes):
            if b_name in str(sp_row['biome']):
                biome_mat[i, b_idx] = 1.0
        # Sucessão
        for s_idx, s_name in enumerate(stages):
            if s_name == str(sp_row['successional_stage']):
                stage_mat[i, s_idx] = 1.0
        # pH normalizado
        ph_min_vec[i, 0] = (float(sp_row.get('ph_min', 5.0)) - 4.0) / 4.5
        ph_max_vec[i, 0] = (float(sp_row.get('ph_max', 7.0)) - 4.0) / 4.5
        # Seca
        drought_vec[i, 0] = drought_map.get(str(sp_row.get('drought_tolerance', 'Média')), 0.6)

    item_vectors = np.hstack([biome_mat, stage_mat, ph_min_vec, ph_max_vec, drought_vec])

    # 2. Atributos Ambientais das Parcelas (u)
    # Agrupa por plot_id para ter 1 linha por parcela
    plots_env = df_ifn.drop_duplicates(subset=['plot_id']).set_index('plot_id')
    plot_list = sorted(plots_env.index)

    user_biome_mat = np.zeros((len(plot_list), len(biomes)), dtype=np.float32)
    user_stage_mat = np.ones((len(plot_list), len(stages)), dtype=np.float32) * 0.25 # demanda equilibrada
    user_ph_min_vec = np.zeros((len(plot_list), 1), dtype=np.float32)
    user_ph_max_vec = np.zeros((len(plot_list), 1), dtype=np.float32)
    user_drought_vec = np.zeros((len(plot_list), 1), dtype=np.float32)

    for u_idx, p_id in enumerate(plot_list):
        p_row = plots_env.loc[p_id]
        # Bioma do terreno
        for b_idx, b_name in enumerate(biomes):
            if b_name == str(p_row['bioma']):
                user_biome_mat[u_idx, b_idx] = 1.0
        # pH do solo medido
        ph_val = (float(p_row['ph_solo']) - 4.0) / 4.5
        user_ph_min_vec[u_idx, 0] = ph_val
        user_ph_max_vec[u_idx, 0] = ph_val
        # Déficit hídrico (baseado em drenagem e chuva)
        if str(p_row['drenagem_solo']) == 'Encharcado':
            user_drought_vec[u_idx, 0] = 0.2
        elif str(p_row['drenagem_solo']) == 'Úmido':
            user_drought_vec[u_idx, 0] = 0.5
        else:
            user_drought_vec[u_idx, 0] = 0.8 if float(p_row['precipitacao_anual_mm']) < 1400 else 0.5

    user_vectors = np.hstack([user_biome_mat, user_stage_mat, user_ph_min_vec, user_ph_max_vec, user_drought_vec])

    return user_vectors, item_vectors, plot_list, species_list

def spatial_cluster_split(df_ifn, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_state=42):
    """
    Realiza divisão espacial por conglomerados do IFN, evitando data leakage espacial.
    """
    np.random.seed(random_state)
    conglomerados = sorted(df_ifn['conglomerado_id'].unique())
    np.random.shuffle(conglomerados)

    n_total = len(conglomerados)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_conglom = set(conglomerados[:n_train])
    val_conglom = set(conglomerados[n_train:n_train + n_val])
    test_conglom = set(conglomerados[n_train + n_val:])

    train_plots = df_ifn[df_ifn['conglomerado_id'].isin(train_conglom)]['plot_id'].unique()
    val_plots = df_ifn[df_ifn['conglomerado_id'].isin(val_conglom)]['plot_id'].unique()
    test_plots = df_ifn[df_ifn['conglomerado_id'].isin(test_conglom)]['plot_id'].unique()

    return set(train_plots), set(val_plots), set(test_plots)

def create_leave_k_out_mask(df_ifn, test_plots, mask_ratio=0.25, random_state=42):
    """
    Mascara uma porcentagem das espécies observadas nas parcelas de teste para avaliação Top-K.
    """
    np.random.seed(random_state)
    df_eval = df_ifn[df_ifn['plot_id'].isin(test_plots)].copy()
    
    ground_truth = {}
    train_interactions = df_ifn[~df_ifn['plot_id'].isin(test_plots)].copy()
    test_visible_interactions = []

    for p in test_plots:
        p_records = df_eval[df_eval['plot_id'] == p]
        species = list(p_records['accepted_name'].unique())
        n_mask = max(1, int(len(species) * mask_ratio))
        
        masked = set(np.random.choice(species, size=n_mask, replace=False))
        ground_truth[p] = masked

        visible = p_records[~p_records['accepted_name'].isin(masked)]
        test_visible_interactions.append(visible)

    df_test_visible = pd.concat(test_visible_interactions, ignore_index=True)
    df_train_full = pd.concat([train_interactions, df_test_visible], ignore_index=True)

    return df_train_full, ground_truth
