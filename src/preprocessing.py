
"""
Módulo de Pré-processamento de Dados (Datathon 2024).
Realiza limpeza, codificação e engenharia de features conforme definido no plano de ação.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder

def load_and_filter(filepath):
    """Carrega dados e seleciona colunas de interesse com nomes padronizados."""
    df = pd.read_excel(filepath)
    
    # 1. Seleção de Colunas
    cols_interest = [
        'Defas', 'Portug', 'Matem',  # (Removido: Inglês - Regra 1)
        'INDE 22', 'IPS', 'IEG', 'IDA', 'IPV', 'IAA', # (Removido: IAN - Regra 3)
        'Fase', 'Ano ingresso', 'Instituição de ensino', 'Pedra 22' # (Removido: Turma - Regra 5)
    ]
    
    # Validação de existencia
    cols_to_keep = []
    for c in cols_interest:
        if c in df.columns:
            cols_to_keep.append(c)
        else:
            print(f"Warning: Coluna '{c}' não encontrada no arquivo original.")
            
    df = df[cols_to_keep].copy()
    
    # 2. Padronização de nomes (snake_case)
    df.columns = [c.strip().upper().replace(' ', '_') for c in df.columns]
    
    return df

def clean_data(df):
    """Remove nulos críticos e colunas desnecessárias."""
    # Regra 4: Remover linhas com PORTUG ou MATEM nulos
    subset_check = [c for c in ['PORTUG', 'MATEM'] if c in df.columns]
    initial_len = len(df)
    df = df.dropna(subset=subset_check)
    print(f"Removidas {initial_len - len(df)} linhas com notas nulas.")
    
    return df

def feature_engineering(df):
    """Cria novas features e transforma o target."""
    
    # Regra 2: Target Binário
    # 1 (Risco) se DEFAS < 0, else 0 (Ideal)
    if 'DEFAS' in df.columns:
        df['TARGET'] = np.where(df['DEFAS'] < 0, 1, 0)
        # Remove original multiclass target to avoid confusion
        df.drop(columns=['DEFAS'], inplace=True)
    
    # Feature 1: Média Geral
    if 'PORTUG' in df.columns and 'MATEM' in df.columns:
        df['MEDIA_GERAL'] = (df['PORTUG'] + df['MATEM']) / 2
        
    return df

def encode_features(df):
    """Aplica One-Hot e Label Encoding conforme regras."""
    
    # Regra 5: Label Encoding para PEDRA_22
    # Ordem: Quartzo (1) -> Ágata (2) -> Ametista (3) -> Topázio (4)
    # Ajuste a ordem hierárquica se necessário. Assumindo ordem crescente de valor da pedra.
    stone_map = {
        'Quartzo': 1,
        'Ágata': 2, 
        'Ametista': 3, 
        'Topázio': 4
    }
    col_stone = 'PEDRA_22'
    if col_stone in df.columns:
        # Preencher nulos ou desconhecidos com 0
        df[col_stone] = df[col_stone].map(stone_map).fillna(0).astype(int)
        
    # Regra 5: One-Hot Encoding para INSTITUIÇÃO e FASE
    cols_ohe = ['INSTITUIÇÃO_DE_ENSINO', 'FASE']
    cols_ohe = [c for c in cols_ohe if c in df.columns]
    
    if cols_ohe:
        df = pd.get_dummies(df, columns=cols_ohe, drop_first=True, dtype=int)
        
    return df

def run_preprocessing(filepath, output_path):
    print("--- Iniciando Pré-processamento ---")
    df = load_and_filter(filepath)
    df = clean_data(df)
    df = feature_engineering(df)
    df = encode_features(df)
    
    print(f"Salvando dataset processado em: {output_path}")
    print(f"Shape final: {df.shape}")
    print("Colunas finais:", df.columns.tolist())
    
    df.to_csv(output_path, index=False)
    print("--- Concluído ---")

if __name__ == "__main__":
    # Exemplo de uso local
    INPUT = r'data\BASE DE DADOS PEDE 2024 - DATATHON.xlsx'
    OUTPUT = r'data\processed_train.csv'
    run_preprocessing(INPUT, OUTPUT)
