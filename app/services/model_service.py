# services/model_service.py
"""
Serviço para gerenciamento do modelo de Machine Learning
"""
import os
import joblib
import pandas as pd
from app.config import logger, DEFAULT_CSV, DEFAULT_MODEL


class ModelService:
    """Gerencia carregamento e estado do modelo de ML"""
    
    def __init__(self):
        self.df_base = None
        self.model_pipeline = None
        self.imputer = None
        self.scaler = None
        self.features_list = None
        self.mapa_classes_inv = None
        self.model_version = "none"
        self.feature_medians = None
        self.feature_stds = None
    
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
    
    def load_model(self, model_path: str = None):
        """
        Carrega o modelo e artefatos relacionados
        
        Args:
            model_path: Caminho para o arquivo do modelo (usa DEFAULT_MODEL se não fornecido)
        """
        model_path = model_path or os.environ.get("MODEL_JOBLIB_PATH", str(DEFAULT_MODEL))
        
        try:
            if os.path.exists(model_path):
                loaded = joblib.load(model_path)
                
                # Ser permissivo com as chaves
                self.model_pipeline = (
                    loaded.get("modelo") or 
                    loaded.get("model") or 
                    loaded.get("pipeline") or 
                    loaded
                )
                self.imputer = loaded.get("imputer", None)
                self.scaler = loaded.get("scaler", None)
                self.features_list = (
                    loaded.get("features") or 
                    loaded.get("features_list") or 
                    None
                )
                
                mapa = (
                    loaded.get("mapa_classes") or 
                    loaded.get("mapa_pedras") or 
                    loaded.get("map_classes") or 
                    None
                )
                
                self.model_version = (
                    loaded.get("versao") or 
                    loaded.get("version") or 
                    "unknown"
                )
                
                # Inverter mapa de classes se possível
                inv = {}
                if mapa:
                    for k, v in mapa.items():
                        try:
                            inv[int(v)] = str(k)
                        except Exception:
                            try:
                                inv[int(k)] = str(v)
                            except Exception:
                                continue
                
                self.mapa_classes_inv = inv or None
                logger.info(f"Loaded model joblib: {model_path} version={self.model_version}")
            else:
                self.model_pipeline = None
                self.imputer = None
                self.scaler = None
                self.features_list = None
                self.mapa_classes_inv = None
                self.model_version = "none"
                logger.warning(f"No model joblib found at {model_path}")
        except Exception as e:
            self.model_pipeline = None
            self.mapa_classes_inv = None
            logger.exception("Error loading model joblib: %s", e)
    
    def compute_feature_statistics(self):
        """
        Calcula medianas e desvios padrão das features para heurística de drivers
        """
        try:
            if self.df_base is not None and self.features_list:
                feats = [f for f in self.features_list if f in self.df_base.columns]
                if feats:
                    self.feature_medians = self.df_base[feats].median()
                    self.feature_stds = self.df_base[feats].std().replace(0, 1.0)
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
        self.load_model()
        self.compute_feature_statistics()
