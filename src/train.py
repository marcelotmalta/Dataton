"""Script de treino mínimo — adapte para o seu pipeline."""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
from src.preprocessing import basic_impute, scale_numeric

def train_example(csv_path="data/train.csv", model_out="models/model.joblib"):
    df = pd.read_csv(csv_path)
    # exemplo: ajustar nomes de colunas conforme dicionário
    numeric = ["nota_port", "nota_mat", "ips"]
    categorical = []
    df = basic_impute(df, numeric, categorical)
    df = scale_numeric(df, numeric)
    X = df[numeric + categorical]
    y = df["target"]
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_out)

if __name__ == '__main__':
    train_example()
