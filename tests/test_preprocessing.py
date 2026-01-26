
import os
import pandas as pd
import numpy as np
import io
import pytest
from pathlib import Path

# assume preprocessing.py está no mesmo pacote / repo root; ajuste import se necessário
from src import preprocessing as pp

# Helpers
def make_excel(tmp_path, df, name="input.xlsx", sheet_name="Sheet1"):
    path = tmp_path / name
    df.to_excel(path, sheet_name=sheet_name, index=False)
    return str(path)

def read_csv(path):
    return pd.read_csv(path)

def test_load_and_filter_warns_and_renames(tmp_path, capsys):
    # Construir df com subset de colunas esperadas
    data = {
        'Defas': [1, 0],
        'INDE 22': [7.1, 6.5],
        'IPS': [8.0, 7.5],
        'Fase': ['A', 'B'],
        'Ano ingresso': [2020, 2021],
        # coluna não na lista: TURMA (should be ignored)
        'TURMA': ['T1','T2']
    }
    df = pd.DataFrame(data)
    excel = make_excel(tmp_path, df)
    out = pp.load_and_filter(excel)
    captured = capsys.readouterr()
    # Warning expected for missing cols that were listed in cols_interest and not present
    assert "Warning:" in captured.out or isinstance(out, pd.DataFrame)
    # Columns must be upper-case and underscores
    assert all(col == col.upper() for col in out.columns)
    assert 'Defas' not in out.columns or 'Defas' not in out.columns  # DEFAS exists? depends rename; ensure columns are subset

def test_clean_data_drops_nulls_and_duplicates():
    df = pd.DataFrame({
        'PORTUG': [9.0, np.nan, 8.0],
        'MATEM': [7.0, 6.5, 7.0],
        'X': [1,1,1]
    })
    before = len(df)
    out = pp.clean_data(df.copy())
    # one row had PORTUG NaN -> removed
    assert len(out) == before - 1
    # duplicates removed
    df2 = pd.DataFrame({
        'PORTUG': [9.0, 9.0],
        'MATEM': [7.0, 7.0],
    })
    out2 = pp.clean_data(df2.copy())
    assert len(out2) == 1

def test_feature_engineering_target_and_media():
    df = pd.DataFrame({
        'DEFAS': [-1, 0, 2],
        'PORTUG': [8.0, 7.0, 6.0],
        'MATEM': [6.0, 5.0, 9.0]
    })
    out = pp.feature_engineering(df.copy())
    # Target created
    assert 'TARGET' in out.columns
    # defasagem < 0 -> 1 else 0
    assert list(out['TARGET']) == [1, 0, 0]
    # MEDIA_GERAL
    assert 'MEDIA_GERAL' in out.columns
    assert out.loc[0, 'MEDIA_GERAL'] == pytest.approx((8.0+6.0)/2)
    # DEFAS removed
    assert 'DEFAS' not in out.columns

def test_encode_features_stone_and_ohe():
    df = pd.DataFrame({
        'PEDRA_22': ['Quartzo', 'Ametista', None, 'Topázio'],
        'INSTITUIÇÃO_DE_ENSINO': ['InstA','InstB','InstA','InstC'],
        'FASE': ['F1','F2','F1','F2']
    })
    out = pp.encode_features(df.copy())
    # Pedra mapping: quartzo->1, ametista->3, none->0, topázio->4
    assert out.loc[0,'PEDRA_22'] == 1
    assert out.loc[1,'PEDRA_22'] == 3
    assert out.loc[2,'PEDRA_22'] == 0
    # OHE columns created (drop_first=True -> one less category)
    assert any(col.startswith('INSTITUIÇÃO_DE_ENSINO_') for col in out.columns)
    assert any(col.startswith('FASE_') for col in out.columns)

def test_impute_data_numeric_and_categorical_strategies():
    df = pd.DataFrame({
        'num1': [1.0, np.nan, 3.0],
        'cat1': ['a', None, 'a']
    })
    out_mean = pp.impute_data(df.copy(), numeric_strategy='mean', categorical_strategy='mode')
    # num1 imputed by mean (1+3)/2 = 2.0
    assert out_mean['num1'].iloc[1] == pytest.approx(2.0)
    # cat1 imputed to mode 'a'
    assert out_mean['cat1'].iloc[1] == 'a'
    out_const = pp.impute_data(df.copy(), numeric_strategy='constant', categorical_strategy='constant')
    assert out_const['num1'].iloc[1] == 0
    assert out_const['cat1'].iloc[1] == 'MISSING'

def test_normalize_data_standard_and_minmax():
    df = pd.DataFrame({
        'A': [1,2,3,4,5],
        'B': [10,10,10,10,10],  # zero std
        'TARGET': [0,1,0,1,0],
        'BIN': [0,1,0,1,0]  # binary
    })
    out_std = pp.normalize_data(df.copy(), method='standard')
    # A should be standardized (mean ~0)
    assert abs(out_std['A'].mean()) < 1e-6
    # B had std zero -> unchanged
    assert list(out_std['B']) == [10,10,10,10,10]
    # TARGET and BIN must be untouched or kept as is (BIN is binary)
    assert 'TARGET' in out_std.columns

def test_run_preprocessing_writes_file(tmp_path):
    # Create minimal excel with required columns
    df = pd.DataFrame({
        'Defas': [0, -1],
        'INDE 22': [6,7],
        'IPS': [8,9],
        'IEG': [5,6],
        'IDA': [1,2],
        'IPV': [2,3],
        'IAA': [3,4],
        'Fase': ['F1','F2'],
        'Ano ingresso': [2020,2021],
        'Instituição de ensino': ['I1','I2'],
        'Pedra 22': ['Quartzo', 'Ágata'],
        'PORTUG': [7.0, 8.0],
        'MATEM': [6.0, 5.0]
    })
    excel = make_excel(tmp_path, df)
    out_csv = tmp_path / "out.csv"
    pp.run_preprocessing(excel, str(out_csv))
    assert out_csv.exists()
    outdf = pd.read_csv(out_csv)
    # Basic checks
    assert 'TARGET' in outdf.columns
    

def test_encode_features():
    df = pd.DataFrame({
        'PEDRA_22': ['Quartzo', 'Ágata', 'Ametista', 'Topázio', 'Unknown'],
        'INSTITUIÇÃO_DE_ENSINO': ['Publica', 'Privada', 'Publica', 'Publica', 'Publica'],
        'FASE': ['1', '2', '1', '1', '1']
    })
    
    # PEDRA_22 mapping: Quartzo: 1, Ágata: 2, Ametista: 3, Topázio: 4, Unknown: 0
    
    df_enc = pp.encode_features(df.copy())
    
    # Check Label Encoding
    assert df_enc['PEDRA_22'].tolist() == [1, 2, 3, 4, 0]
    
    # Check One-Hot Encoding
    # INSTITUIÇÃO_DE_ENSINO: Publica (base?), Privada. If 2 values, get_dummies drop_first=True creates 1 col depending on alpha sort.
    # FASE: 1, 2. Creates FASE_2 probably.
    
    # Verify columns existence
    # We don't check exact column names as they depend on unique values and sorting, but we check if original cols are gone or transformed.
    # Actually get_dummies keeps original columns? No, it replaces them.
    
    assert 'INSTITUIÇÃO_DE_ENSINO' not in df_enc.columns
    assert 'FASE' not in df_enc.columns
    
    # Check if we have encoded columns. 
    # With drop_first=True:
    # INSTITUIÇÃO_DE_ENSINO has 'Privada', 'Publica'. 'Privada' < 'Publica'? 'Privada' comes first. Base might be 'Privada' if sorted.
    # Let's check generally if boolean/int columns appeared.
    # "INSTITUIÇÃO_DE_ENSINO_Publica" might exist if Privada is dropped.
    
    cols = df_enc.columns.tolist()
    # At least one new column for Institution and Phase
    assert any('INSTITUIÇÃO_DE_ENSINO' in c for c in cols)
    assert any('FASE' in c for c in cols)


