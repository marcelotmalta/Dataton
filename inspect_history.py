from pathlib import Path

import pandas as pd

HISTORY_PATH = Path("data/Bases antigas/PEDE_PASSOS_DATASET_FIAP.csv")


def inspect_history() -> None:
    print(f"Inspecting historical data: {HISTORY_PATH.as_posix()}")

    if not HISTORY_PATH.exists():
        print(f"CSV file not found at {HISTORY_PATH.as_posix()}")
        return

    try:
        df_old = pd.read_csv(HISTORY_PATH, sep=";", encoding="utf-8", nrows=5)
        print("Columns:", df_old.columns.tolist())
        if not df_old.empty:
            print("First row:", df_old.iloc[0].to_dict())
    except Exception as exc:
        print(f"CSV Error (sep=';'): {exc}")
        try:
            # Fallback para arquivo separado por vírgula
            df_old = pd.read_csv(HISTORY_PATH, sep=",", encoding="utf-8", nrows=5)
            print("Columns (comma):", df_old.columns.tolist())
            if not df_old.empty:
                print("First row:", df_old.iloc[0].to_dict())
        except Exception as exc2:
            print(f"CSV Error (sep=','): {exc2}")


if __name__ == "__main__":
    inspect_history()
