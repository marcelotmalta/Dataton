import joblib
import pandas as pd
from pathlib import Path

# Caminho do modelo
MODEL_PATH = Path("data/modelo/modelo_pedra_conceito_v1.pkl")

try:
    if MODEL_PATH.exists():
        artifact = joblib.load(MODEL_PATH)
        print(f"Tipo do artefato carregado: {type(artifact)}")
        
        if isinstance(artifact, dict):
            print("Chaves encontradas no dicionário:")
            for key in artifact.keys():
                print(f" - {key}: {type(artifact[key])}")
        else:
            print("O artefato não é um dicionário.")
            print(artifact)
    else:
        print(f"Erro: Arquivo não encontrado em {MODEL_PATH}")

except Exception as e:
    print(f"Erro ao carregar o modelo: {e}")
