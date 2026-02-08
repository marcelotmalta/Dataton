import joblib
import pandas as pd
import os

MODEL_PATH = os.path.join('models', 'modelo_pedra_conceito_xgb_2025.pkl')

try:
    if os.path.exists(MODEL_PATH):
        loaded_data = joblib.load(MODEL_PATH)
        print(f"Keys in loaded data: {loaded_data.keys()}")
        if 'modelo' in loaded_data:
            model = loaded_data['modelo']
            print(f"Model type: {type(model)}")
            if hasattr(model, 'steps'):
                print("Pipeline steps:")
                for name, step in model.steps:
                    print(f"  - {name}: {step}")
            else:
                print("Model is not a pipeline or steps attribute missing.")
        
        if 'features' in loaded_data:
            print(f"Features: {loaded_data['features']}")
            
        if 'mapa_classes' in loaded_data:
            print(f"Class Map: {loaded_data['mapa_classes']}")
            
    else:
        print(f"Model file not found at {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")
