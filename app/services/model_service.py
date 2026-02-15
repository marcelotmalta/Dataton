# services/model_service.py
"""
Serviço para gerenciamento do modelo de Machine Learning
"""
import os
from typing import Any, Dict, Optional

import joblib
import pandas as pd
from app.config import (
    logger,
    DEFAULT_CSV,
    DEFAULT_MODEL,
    DEFAULT_MODEL_MULTICLASS,
    DEFAULT_MODEL_RISK,
)


class ModelService:
    """Gerencia carregamento e estado do modelo de ML"""
    
    def __init__(self):
        self.df_base = None
        # Modelo principal (multiclasse / fallback)
        self.model_pipeline = None
        self.imputer = None
        self.scaler = None
        self.features_list = None
        self.mapa_classes_inv = None
        self.model_version = "none"
        # Modelo de risco (binário)
        self.model_pipeline_risk = None
        self.imputer_risk = None
        self.scaler_risk = None
        self.features_list_risk = None
        self.mapa_classes_inv_risk = None
        self.model_version_risk = "none"
        self.feature_medians = None
        self.feature_stds = None

    @staticmethod
    def _invert_class_map(mapa: Optional[Dict[Any, Any]]) -> Optional[Dict[int, str]]:
        """Inverte um mapa de classes, aceitando chaves/valores em formatos mistos."""
        inv = {}
        if not mapa:
            return None

        for k, v in mapa.items():
            try:
                inv[int(v)] = str(k)
            except Exception:
                try:
                    inv[int(k)] = str(v)
                except Exception:
                    continue

        return inv or None

    def _extract_loaded_bundle(self, loaded: Any) -> Dict[str, Any]:
        """
        Extrai artefatos do objeto carregado via joblib.
        Aceita dict serializado (preferencial) ou estimador direto.
        """
        if isinstance(loaded, dict):
            model = (
                loaded.get("modelo")
                or loaded.get("model")
                or loaded.get("pipeline")
            )
            # Fallback extremo: se não houver chave padrão e o dict for "modelo puro"
            if model is None and hasattr(loaded, "predict"):
                model = loaded

            features = loaded.get("features") or loaded.get("features_list")
            mapa = (
                loaded.get("mapa_classes")
                or loaded.get("mapa_pedras")
                or loaded.get("map_classes")
            )
            version = loaded.get("versao") or loaded.get("version") or "unknown"
            imputer = loaded.get("imputer")
            scaler = loaded.get("scaler")
        else:
            model = loaded
            features = None
            mapa = None
            version = "unknown"
            imputer = None
            scaler = None

        return {
            "model": model,
            "imputer": imputer,
            "scaler": scaler,
            "features": features,
            "mapa_classes_inv": self._invert_class_map(mapa),
            "version": version,
        }

    def _load_bundle(self, model_path: str, label: str) -> Optional[Dict[str, Any]]:
        """Carrega um artefato de modelo e retorna seus componentes normalizados."""
        try:
            if not os.path.exists(model_path):
                logger.warning("No %s model joblib found at %s", label, model_path)
                return None

            loaded = joblib.load(model_path)
            bundle = self._extract_loaded_bundle(loaded)
            logger.info(
                "Loaded %s model joblib: %s version=%s",
                label,
                model_path,
                bundle["version"],
            )
            return bundle
        except Exception as e:
            logger.exception("Error loading %s model joblib: %s", label, e)
            return None
    
    def load_data(self, csv_path: str = None):
        """
        Carrega o CSV com dados base dos estudantes
        
        Args:
            csv_path: Caminho para o arquivo CSV (usa DEFAULT_CSV se não fornecido)
        """
        csv_path = csv_path or os.environ.get("DF_CSV_PATH", str(DEFAULT_CSV))
        
        try:
            if os.path.exists(csv_path):
                self.df_base = pd.read_csv(csv_path)
                logger.info(f"Loaded CSV: {csv_path} shape={self.df_base.shape}")
            else:
                self.df_base = None
                logger.warning(f"No CSV found at {csv_path} (continuing without df_base)")
        except Exception as e:
            self.df_base = None
            logger.exception("Error loading CSV: %s", e)
    
    def load_models(self, multiclass_path: str = None, risk_path: str = None):
        """
        Carrega modelos multiclasse (Pedras) e binário (Risco Crítico).
        
        Args:
            multiclass_path: Caminho para modelo multiclasse
            risk_path: Caminho para modelo binário de risco
        """
        legacy_single_path = os.environ.get("MODEL_JOBLIB_PATH")
        multiclass_path = (
            multiclass_path
            or os.environ.get("MODEL_MULTICLASS_JOBLIB_PATH")
            or legacy_single_path
            or str(DEFAULT_MODEL_MULTICLASS or DEFAULT_MODEL)
        )
        risk_path = (
            risk_path
            or os.environ.get("MODEL_RISK_JOBLIB_PATH")
            or str(DEFAULT_MODEL_RISK)
        )

        multi_bundle = self._load_bundle(multiclass_path, "multiclass")
        risk_bundle = self._load_bundle(risk_path, "risk")

        # Caso legacy: MODEL_JOBLIB_PATH pode apontar para o artefato binário.
        if risk_bundle is None and multi_bundle is not None and self._bundle_is_risk(multi_bundle):
            risk_bundle = multi_bundle
            logger.info(
                "Using multiclass/legacy artifact as risk fallback (path=%s).",
                multiclass_path,
            )

        if multi_bundle is not None:
            self.model_pipeline = multi_bundle["model"]
            self.imputer = multi_bundle["imputer"]
            self.scaler = multi_bundle["scaler"]
            self.features_list = multi_bundle["features"]
            self.mapa_classes_inv = multi_bundle["mapa_classes_inv"]
            self.model_version = multi_bundle["version"]
        elif risk_bundle is not None:
            # Fallback para manter API funcional mesmo sem artefato multiclasse.
            self.model_pipeline = risk_bundle["model"]
            self.imputer = risk_bundle["imputer"]
            self.scaler = risk_bundle["scaler"]
            self.features_list = risk_bundle["features"]
            self.mapa_classes_inv = risk_bundle["mapa_classes_inv"]
            self.model_version = risk_bundle["version"]
            logger.warning(
                "Multiclass model unavailable; using risk model as primary fallback."
            )
        else:
            self.model_pipeline = None
            self.imputer = None
            self.scaler = None
            self.features_list = None
            self.mapa_classes_inv = None
            self.model_version = "none"

        if risk_bundle is not None:
            self.model_pipeline_risk = risk_bundle["model"]
            self.imputer_risk = risk_bundle["imputer"]
            self.scaler_risk = risk_bundle["scaler"]
            self.features_list_risk = risk_bundle["features"]
            self.mapa_classes_inv_risk = risk_bundle["mapa_classes_inv"]
            self.model_version_risk = risk_bundle["version"]
        else:
            self.model_pipeline_risk = None
            self.imputer_risk = None
            self.scaler_risk = None
            self.features_list_risk = None
            self.mapa_classes_inv_risk = None
            self.model_version_risk = "none"

    @staticmethod
    def _bundle_is_risk(bundle: Dict[str, Any]) -> bool:
        """Heurística simples para detectar artefato binário de risco."""
        mapa_inv = bundle.get("mapa_classes_inv") or {}
        normalized = {
            str(v).strip().lower().replace("í", "i").replace("á", "a")
            for v in mapa_inv.values()
        }
        return "critico" in normalized

    def load_model(self, model_path: str = None):
        """
        Compatibilidade retroativa: carrega o caminho informado como multiclasse.
        """
        self.load_models(multiclass_path=model_path)
    
    def compute_feature_statistics(self):
        """
        Calcula medianas e desvios padrão das features para heurística de drivers
        """
        try:
            feature_union = set(self.features_list or [])
            feature_union.update(self.features_list_risk or [])

            if self.df_base is not None and feature_union:
                df_stats = self.df_base.copy()

                if (
                    "consistencia_acad" in feature_union
                    and "consistencia_acad" not in df_stats.columns
                    and {"IDA", "IEG"}.issubset(df_stats.columns)
                ):
                    df_stats["consistencia_acad"] = df_stats["IDA"] / (df_stats["IEG"] + 0.1)

                feats = [f for f in feature_union if f in df_stats.columns]
                if feats:
                    self.feature_medians = df_stats[feats].median()
                    self.feature_stds = df_stats[feats].std().replace(0, 1.0)
                    logger.info("Computed medians/stds for top-driver heuristic.")
                else:
                    self.feature_medians = None
                    self.feature_stds = None
            else:
                self.feature_medians = None
                self.feature_stds = None
        except Exception as e:
            self.feature_medians = None
            self.feature_stds = None
            logger.exception("Error computing medians/stds: %s", e)
    
    def initialize(self):
        """
        Inicializa o serviço carregando dados e modelo
        """
        self.load_data()
        self.load_models()
        self.compute_feature_statistics()
