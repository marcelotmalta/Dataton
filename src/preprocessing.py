"""Funções de pré-processamento — adapte conforme o dicionário de dados."""
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

def basic_impute(df: pd.DataFrame, numeric_cols, categorical_cols):
    imputer_num = SimpleImputer(strategy='median')
    df[numeric_cols] = imputer_num.fit_transform(df[numeric_cols])
    df[categorical_cols] = df[categorical_cols].fillna('missing')
    return df

def scale_numeric(df: pd.DataFrame, numeric_cols):
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df
