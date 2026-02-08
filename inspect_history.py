
import pandas as pd

# Inspect historical data
try:
    df_old = pd.read_csv(r'data\Bases antigas\PEDE_PASSOS_DATASET_FIAP.csv',  sep=';', encoding='utf-8', nrows=5)
    print("Columns:", df_old.columns.tolist())
    print("First row:", df_old.iloc[0].to_dict())
except Exception as e:
    print(f"CSV Error: {e}")
    try:
        # Fallback for comma sep
        df_old = pd.read_csv(r'data\Bases antigas\PEDE_PASSOS_DATASET_FIAP.csv', sep=',', encoding='utf-8', nrows=5)
        print("Columns (comma):", df_old.columns.tolist())
    except Exception as e2:
        print(f"CSV Error 2: {e2}")

