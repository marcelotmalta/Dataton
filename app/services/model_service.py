# services/model_service.py
"""
Serviço para gerenciamento do modelo de Machine Learning
"""
import os
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.impute import SimpleImputer
from app.config import logger, DEFAULT_CSV


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

    def load_model(self, model_uri: str = None):
        """
        Carrega o modelo do registro do MLflow.

        Args:
            model_uri: URI do modelo no formato models:/<name>/<version>.
        """
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
        model_uri = model_uri or os.environ.get("MODEL_URI", "models:/xgb_pedra_conceito_model/latest")

        try:
            self.model_pipeline = mlflow.sklearn.load_model(model_uri)
            client = mlflow.tracking.MlflowClient()
            model_name, model_version_str = model_uri.split('/')[1], model_uri.split('/')[-1]

            if model_version_str == "latest":
                latest_versions = client.get_latest_versions(model_name, stages=["None"])
                if latest_versions:
                    self.model_version = latest_versions[0].version
                else:
                    self.model_version = "latest"
            else:
                self.model_version = model_version_str
            
            self.features_list = ["IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV",
                "FASE", "DEFA", "consistencia_acad"
            ]
            mapa_pedras = {'Quartzo': 0, 'Ágata': 1, 'Ametista': 2, 'Topázio': 3}
            
            self.imputer = SimpleImputer(strategy='median')
            
            if self.df_base is not None:
                X = self.df_base[self.features_list]
                self.imputer.fit(X)
                logger.info("Imputer fitted with data from df_base.")

            inv = {int(v): str(k) for k, v in mapa_pedras.items()}
            self.mapa_classes_inv = inv
            
            logger.info(f"Loaded model from MLflow: {model_uri} version={self.model_version}")

        except Exception as e:
            self.model_pipeline = None
            self.imputer = None
            self.scaler = None
            self.features_list = None
            self.mapa_classes_inv = None
            self.model_version = "none"
            logger.exception("Error loading model from MLflow: %s", e)

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
