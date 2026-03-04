# tests/test_model_service.py
"""
Testes unitários para ModelService — cobrindo branches de carregamento de modelos,
extração de bundles, inversão de mapas, heurística de bundle binário e estatísticas.
"""
import os
import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app.services.model_service import ModelService


# ────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────

@pytest.fixture
def svc():
    return ModelService()


# ────────────────────────────────────────────
# _invert_class_map
# ────────────────────────────────────────────

class TestInvertClassMap:
    def test_none_map(self):
        assert ModelService._invert_class_map(None) is None

    def test_empty_map(self):
        assert ModelService._invert_class_map({}) is None

    def test_normal_map(self):
        mapa = {"Quartzo": 0, "Topázio": 1}
        inv = ModelService._invert_class_map(mapa)
        assert inv == {0: "Quartzo", 1: "Topázio"}

    def test_inverted_already(self):
        """Quando chaves são int e valores são str."""
        mapa = {0: "Quartzo", 1: "Topázio"}
        inv = ModelService._invert_class_map(mapa)
        # Tenta int(v) primeiro: int("Quartzo") falha, cai para int(k) = 0
        assert inv is not None
        assert 0 in inv
        assert 1 in inv

    def test_non_castable_entries(self):
        """Entradas que não podem ser convertidas."""
        mapa = {"abc": "xyz"}
        result = ModelService._invert_class_map(mapa)
        assert result is None


# ────────────────────────────────────────────
# _extract_loaded_bundle
# ────────────────────────────────────────────

class TestExtractLoadedBundle:
    def test_dict_with_modelo(self, svc):
        loaded = {
            "modelo": MagicMock(),
            "features": ["IAN", "IDA"],
            "mapa_classes": {"Quartzo": 0},
            "versao": "v1",
            "imputer": MagicMock(),
            "scaler": MagicMock(),
        }
        bundle = svc._extract_loaded_bundle(loaded)
        assert bundle["model"] is not None
        assert bundle["features"] == ["IAN", "IDA"]
        assert bundle["version"] == "v1"

    def test_dict_with_model_key(self, svc):
        loaded = {"model": MagicMock(), "features_list": ["X"]}
        bundle = svc._extract_loaded_bundle(loaded)
        assert bundle["model"] is not None
        assert bundle["features"] == ["X"]

    def test_dict_with_pipeline_key(self, svc):
        loaded = {"pipeline": MagicMock()}
        bundle = svc._extract_loaded_bundle(loaded)
        assert bundle["model"] is not None

    def test_non_dict_object(self, svc):
        model = MagicMock()
        model.predict = MagicMock()
        bundle = svc._extract_loaded_bundle(model)
        assert bundle["model"] is model
        assert bundle["features"] is None
        assert bundle["version"] == "unknown"

    def test_dict_with_mapa_pedras(self, svc):
        loaded = {"modelo": MagicMock(), "mapa_pedras": {"Quartzo": 0, "Topázio": 1}}
        bundle = svc._extract_loaded_bundle(loaded)
        assert bundle["mapa_classes_inv"] is not None


# ────────────────────────────────────────────
# _bundle_is_risk
# ────────────────────────────────────────────

class TestBundleIsRisk:
    def test_risk_bundle(self):
        bundle = {"mapa_classes_inv": {0: "Não Crítico", 1: "Crítico"}}
        assert ModelService._bundle_is_risk(bundle) is True

    def test_non_risk_bundle(self):
        bundle = {"mapa_classes_inv": {0: "Quartzo", 1: "Topázio"}}
        assert ModelService._bundle_is_risk(bundle) is False

    def test_no_map(self):
        bundle = {"mapa_classes_inv": None}
        assert ModelService._bundle_is_risk(bundle) is False

    def test_empty_map(self):
        bundle = {"mapa_classes_inv": {}}
        assert ModelService._bundle_is_risk(bundle) is False


# ────────────────────────────────────────────
# _load_bundle
# ────────────────────────────────────────────

class TestLoadBundle:
    def test_file_not_found(self, svc):
        result = svc._load_bundle("/nonexistent/path.pkl", "test")
        assert result is None

    @patch("app.services.model_service.joblib.load")
    @patch("app.services.model_service.os.path.exists", return_value=True)
    def test_load_success(self, mock_exists, mock_joblib, svc):
        mock_joblib.return_value = {
            "modelo": MagicMock(),
            "features": ["IAN"],
            "mapa_classes": {"A": 0},
            "versao": "v2",
        }
        result = svc._load_bundle("fake.pkl", "test")
        assert result is not None
        assert result["version"] == "v2"

    @patch("app.services.model_service.joblib.load", side_effect=Exception("corrupt"))
    @patch("app.services.model_service.os.path.exists", return_value=True)
    def test_load_corrupted(self, mock_exists, mock_joblib, svc):
        result = svc._load_bundle("corrupt.pkl", "test")
        assert result is None


# ────────────────────────────────────────────
# load_data
# ────────────────────────────────────────────

class TestLoadData:
    @patch("app.services.model_service.os.path.exists", return_value=False)
    def test_csv_not_found(self, mock_exists, svc):
        svc.load_data("/nonexistent.csv")
        assert svc.df_base is None

    @patch("app.services.model_service.pd.read_csv", side_effect=Exception("bad csv"))
    @patch("app.services.model_service.os.path.exists", return_value=True)
    def test_csv_read_error(self, mock_exists, mock_csv, svc):
        svc.load_data("bad.csv")
        assert svc.df_base is None


# ────────────────────────────────────────────
# load_models edge cases
# ────────────────────────────────────────────

class TestLoadModels:
    @patch.object(ModelService, "_load_bundle", return_value=None)
    def test_no_models_available(self, mock_load, svc):
        svc.load_models("none1.pkl", "none2.pkl")
        assert svc.model_pipeline is None
        assert svc.model_pipeline_risk is None
        assert svc.model_version == "none"

    @patch.object(ModelService, "_load_bundle")
    def test_risk_fallback_when_multi_is_risk(self, mock_load, svc):
        """Multi bundle detectado como risco → usado como risk fallback."""
        risk_bundle = {
            "model": MagicMock(),
            "imputer": None,
            "scaler": None,
            "features": ["IAN"],
            "mapa_classes_inv": {0: "Não Crítico", 1: "Crítico"},
            "version": "risk-v1",
        }
        # First call = multiclass, second = risk (None)
        mock_load.side_effect = [risk_bundle, None]
        svc.load_models("multi.pkl", "risk.pkl")
        # Should use multi bundle as both main and risk
        assert svc.model_pipeline is not None
        assert svc.model_pipeline_risk is not None

    @patch.object(ModelService, "_load_bundle")
    def test_only_risk_model(self, mock_load, svc):
        """Só risk → usa como primary fallback."""
        risk_bundle = {
            "model": MagicMock(),
            "imputer": None,
            "scaler": None,
            "features": ["IAN"],
            "mapa_classes_inv": {0: "OK", 1: "Crítico"},
            "version": "risk-v1",
        }
        mock_load.side_effect = [None, risk_bundle]
        svc.load_models("multi.pkl", "risk.pkl")
        assert svc.model_pipeline is not None  # risk used as primary fallback
        assert svc.model_version == "risk-v1"


# ────────────────────────────────────────────
# compute_feature_statistics
# ────────────────────────────────────────────

class TestComputeFeatureStatistics:
    def test_no_data(self, svc):
        svc.df_base = None
        svc.features_list = ["IAN"]
        svc.features_list_risk = None
        svc.compute_feature_statistics()
        assert svc.feature_medians is None

    def test_with_data(self, svc):
        svc.df_base = pd.DataFrame({
            "IAN": [1.0, 2.0, 3.0],
            "IDA": [4.0, 5.0, 6.0],
            "IEG": [1.0, 1.0, 1.0],
        })
        svc.features_list = ["IAN", "IDA", "consistencia_acad"]
        svc.features_list_risk = None
        svc.compute_feature_statistics()
        assert svc.feature_medians is not None
        assert "IAN" in svc.feature_medians.index
        assert "consistencia_acad" in svc.feature_medians.index

    def test_no_features(self, svc):
        svc.df_base = pd.DataFrame({"IAN": [1, 2]})
        svc.features_list = None
        svc.features_list_risk = None
        svc.compute_feature_statistics()
        assert svc.feature_medians is None

    def test_features_not_in_df(self, svc):
        svc.df_base = pd.DataFrame({"X": [1, 2]})
        svc.features_list = ["MISSING_COL"]
        svc.features_list_risk = None
        svc.compute_feature_statistics()
        assert svc.feature_medians is None


# ────────────────────────────────────────────
# load_model (backward compat)
# ────────────────────────────────────────────

class TestLoadModelCompat:
    @patch.object(ModelService, "load_models")
    def test_calls_load_models(self, mock_load_models, svc):
        svc.load_model("some_path.pkl")
        mock_load_models.assert_called_once_with(multiclass_path="some_path.pkl")
