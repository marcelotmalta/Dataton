import pytest
import pandas as pd
import numpy as np
from src.preprocessing import impute_data, normalize_data, clean_data

def test_clean_data():
    df = pd.DataFrame({
        'PORTUG': [1.0, None, 3.0, 1.0],
        'MATEM': [2.0, 2.0, None, 2.0],
        'OTHER': [1, 2, 3, 1]
    })
    # Should drop row 1 (PORTUG None), row 2 (MATEM None).
    # Row 3 is duplicate of row 0? No, row 0 is 1.0, 2.0, 1. Row 3 is 1.0, 2.0, 1. Yes duplicate.
    
    df_clean = clean_data(df)
    
    # Original: 4 rows.
    # Row 1 dropped (None in PORTUG).
    # Row 2 dropped (None in MATEM).
    # Remaining: Row 0 and Row 3.
    # Row 3 is duplicate of Row 0. Should be dropped.
    # Final should be 1 row.
    
    assert len(df_clean) == 1
    assert df_clean.iloc[0]['PORTUG'] == 1.0

def test_impute_data_numeric():
    df = pd.DataFrame({
        'A': [1.0, np.nan, 3.0],
        'B': [2.0, 2.0, np.nan]
    })
    
    # Mean inputation: A -> mean(1,3)=2. B -> mean(2,2)=2.
    df_imputed = impute_data(df.copy(), numeric_strategy='mean')
    assert df_imputed['A'].iloc[1] == 2.0
    assert df_imputed['B'].iloc[2] == 2.0
    assert not df_imputed.isnull().any().any()

def test_impute_data_categorical():
    df = pd.DataFrame({
        'Cat': ['A', 'A', np.nan, 'B']
    })
    # Mode imputation: A is mode.
    df_imputed = impute_data(df.copy(), categorical_strategy='mode')
    assert df_imputed['Cat'].iloc[2] == 'A'
    assert not df_imputed.isnull().any().any()

def test_normalize_data_standard():
    df = pd.DataFrame({
        'A': [1.0, 2.0, 3.0, 4.0, 5.0], # Mean 3, Std ~1.58
        'TARGET': [0, 1, 0, 1, 0] # Should ignore
    })
    
    df_norm = normalize_data(df.copy(), method='standard')
    
    # Check if A is scaled (mean approx 0)
    assert abs(df_norm['A'].mean()) < 1e-6
    # Check TARGET is untouched
    assert df_norm['TARGET'].equals(df['TARGET'])

def test_normalize_data_minmax():
    df = pd.DataFrame({
        'A': [0.0, 10.0]
    })
    df_norm = normalize_data(df.copy(), method='minmax')
    assert df_norm['A'].iloc[0] == 0.0
    assert df_norm['A'].iloc[1] == 1.0
