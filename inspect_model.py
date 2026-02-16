from pathlib import Path

import joblib

MODEL_PATHS = [
    Path("models/modelo_multiclasse_pedras_2025.pkl"),
    Path("models/modelo_risco_critico_2025.pkl"),
]


def inspect_model(model_path: Path) -> None:
    print(f"\n=== Inspecting: {model_path.as_posix()} ===")

    if not model_path.exists():
        print(f"Model file not found at {model_path.as_posix()}")
        return

    try:
        loaded_data = joblib.load(model_path)
    except Exception as exc:
        print(f"Error loading model: {exc}")
        return

    if not isinstance(loaded_data, dict):
        print(f"Loaded object type: {type(loaded_data)}")
        return

    print(f"Keys in loaded data: {sorted(loaded_data.keys())}")

    model = loaded_data.get("modelo") or loaded_data.get("model") or loaded_data.get("pipeline")
    if model is not None:
        print(f"Model type: {type(model)}")
        if hasattr(model, "steps"):
            print("Pipeline steps:")
            for name, step in model.steps:
                print(f"  - {name}: {step}")

    if "features" in loaded_data:
        print(f"Features ({len(loaded_data['features'])}): {loaded_data['features']}")

    if "mapa_classes" in loaded_data:
        print(f"Class Map: {loaded_data['mapa_classes']}")

    if "versao" in loaded_data:
        print(f"Version: {loaded_data['versao']}")


if __name__ == "__main__":
    for path in MODEL_PATHS:
        inspect_model(path)
