# config.py
"""
Configurações centralizadas da aplicação
"""
import pathlib
import logging

# ---------- Logging ----------
LOG_LEVEL = logging.INFO
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("student_performance_api")

# ---------- Paths ----------
BASE_DIR = pathlib.Path(__file__).resolve().parent
# Data/Model relative to project root (one level up from app/)
DEFAULT_CSV = BASE_DIR.parent / "data" / "df_Base_final.csv"
DEFAULT_MODEL = BASE_DIR.parent / "models" / "modelo_pedra_conceito_xgb_2025.pkl"
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# ---------- CORS ----------
ALLOWED_ORIGINS = ["*"]  # ajuste em produção

# ---------- DEFA Thresholds ----------
DEFA_LARGE_THRESHOLD = 2
DEFA_MEDIUM_VALUE = 1
