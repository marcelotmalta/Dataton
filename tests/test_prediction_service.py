# tests/test_prediction_service.py
"""
Testes unitários para PredictionService — cobrindo branches não atingidos
pelos testes de integração existentes (calculate_risk_score, generate_suggestions,
_normalize_label, _class_index_by_label, _map_prediction_label,
_build_probabilities_map, make_prediction fallback, _manual_imputation_fallback,
predict_score with student_service).
"""
import numpy as np
import pandas as pd
import pytest

from unittest.mock import MagicMock, patch
from app.services.prediction_service import PredictionService
from app.models import StudentMetrics


# ────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────

@pytest.fixture
def mock_model_service():
    """Model service minimal mock."""
    ms = MagicMock()
    ms.model_pipeline = None
    ms.model_pipeline_risk = None
    ms.imputer = None
    ms.scaler = None
    ms.imputer_risk = None
    ms.scaler_risk = None
    ms.features_list = ["IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "FASE", "consistencia_acad"]
    ms.features_list_risk = None
    ms.mapa_classes_inv = {0: "Quartzo", 1: "Ágata", 2: "Ametista", 3: "Topázio"}
    ms.mapa_classes_inv_risk = {0: "Não Crítico", 1: "Crítico"}
    ms.feature_medians = None
    ms.feature_stds = None
    ms.model_version = "test-v1"
    ms.model_version_risk = "test-risk-v1"
    return ms


@pytest.fixture
def service(mock_model_service):
    return PredictionService(mock_model_service)


# ────────────────────────────────────────────
# _normalize_label
# ────────────────────────────────────────────

class TestNormalizeLabel:
    def test_with_string(self):
        assert PredictionService._normalize_label("Crítico") == "critico"

    def test_with_accented_string(self):
        assert PredictionService._normalize_label("Topázio") == "topazio"

    def test_with_non_string(self):
        assert PredictionService._normalize_label(123) == ""
        assert PredictionService._normalize_label(None) == ""

    def test_with_whitespace(self):
        assert PredictionService._normalize_label("  Alto  ") == "alto"


# ────────────────────────────────────────────
# _class_index_by_label
# ────────────────────────────────────────────

class TestClassIndexByLabel:
    def test_empty_map(self, service):
        assert service._class_index_by_label(None, {"Critico"}) is None
        assert service._class_index_by_label({}, {"Critico"}) is None

    def test_finds_matching_class(self, service):
        mapa = {0: "Não Crítico", 1: "Crítico"}
        result = service._class_index_by_label(mapa, {"Critico", "Crítico"})
        assert result == 1

    def test_no_match(self, service):
        mapa = {0: "Quartzo", 1: "Ágata"}
        result = service._class_index_by_label(mapa, {"Critico"})
        assert result is None

    def test_non_castable_idx(self, service):
        mapa = {"abc": "Crítico"}
        result = service._class_index_by_label(mapa, {"Critico", "Crítico"})
        assert result is None  # "abc" cannot be cast to int


# ────────────────────────────────────────────
# _map_prediction_label
# ────────────────────────────────────────────

class TestMapPredictionLabel:
    def test_none_idx(self):
        assert PredictionService._map_prediction_label(None, {}) == "unknown"

    def test_with_class_map(self):
        mapa = {0: "Quartzo", 1: "Topázio"}
        assert PredictionService._map_prediction_label(1, mapa) == "Topázio"

    def test_missing_idx_in_map(self):
        mapa = {0: "Quartzo"}
        assert PredictionService._map_prediction_label(5, mapa) == "5"

    def test_no_class_map(self):
        assert PredictionService._map_prediction_label(2, None) == "2"
        assert PredictionService._map_prediction_label(2, {}) == "2"

    def test_non_castable_pred(self):
        """Se pred_idx gera exceção no int(), retorna str."""
        mapa = {0: "X"}
        assert PredictionService._map_prediction_label("abc", mapa) == "abc"


# ────────────────────────────────────────────
# _build_probabilities_map
# ────────────────────────────────────────────

class TestBuildProbabilitiesMap:
    def test_none_probs(self):
        result = PredictionService._build_probabilities_map(None, {0: "A"})
        assert result == {}

    def test_with_class_map(self):
        probs = [0.3, 0.7]
        mapa = {0: "Quartzo", 1: "Topázio"}
        result = PredictionService._build_probabilities_map(probs, mapa)
        assert result == {"Quartzo": 0.3, "Topázio": 0.7}

    def test_without_class_map(self):
        probs = [0.5, 0.5]
        result = PredictionService._build_probabilities_map(probs, None)
        assert result == {"Class_0": 0.5, "Class_1": 0.5}


# ────────────────────────────────────────────
# calculate_risk_score
# ────────────────────────────────────────────

class TestCalculateRiskScore:
    def test_no_probs_at_all(self, service):
        """Sem qualquer probabilidade → None."""
        assert service.calculate_risk_score() is None

    def test_binary_with_critico_map(self, service):
        risk_probs = np.array([0.3, 0.7])
        risk_map = {0: "Não Crítico", 1: "Crítico"}
        result = service.calculate_risk_score(risk_probs=risk_probs, risk_map_inv=risk_map)
        assert abs(result - 0.7) < 1e-6

    def test_binary_without_map_two_classes(self, service):
        """Binário sem mapa → pega índice 1."""
        result = service.calculate_risk_score(risk_probs=np.array([0.4, 0.6]))
        assert abs(result - 0.6) < 1e-6

    def test_binary_without_map_one_class(self, service):
        """Binário 1 classe → pega índice 0."""
        result = service.calculate_risk_score(risk_probs=np.array([0.8]))
        assert abs(result - 0.8) < 1e-6

    def test_fallback_quartzo(self, service):
        """Sem modelo binário, fallback para Quartzo no multiclasse."""
        fallback_probs = np.array([0.1, 0.2, 0.3, 0.4])
        fallback_map = {0: "Quartzo", 1: "Ágata", 2: "Ametista", 3: "Topázio"}
        result = service.calculate_risk_score(
            fallback_probs=fallback_probs,
            fallback_map_inv=fallback_map,
        )
        assert abs(result - 0.1) < 1e-6  # Quartzo é index 0

    def test_fallback_weighted_average(self, service):
        """Sem Quartzo no mapa → média ponderada."""
        fallback_probs = np.array([0.5, 0.3, 0.2])
        fallback_map = {0: "A", 1: "B", 2: "C"}  # Nenhum Quartzo
        result = service.calculate_risk_score(
            fallback_probs=fallback_probs,
            fallback_map_inv=fallback_map,
        )
        assert result is not None
        assert 0 <= result <= 1

    def test_fallback_single_class(self, service):
        """Multiclasse com 1 classe."""
        result = service.calculate_risk_score(
            fallback_probs=np.array([0.9]),
            fallback_map_inv={0: "X"},
        )
        assert abs(result - 0.9) < 1e-6

    def test_fallback_no_probs(self, service):
        """fallback_probs None → None."""
        result = service.calculate_risk_score(risk_probs=None, fallback_probs=None)
        assert result is None


# ────────────────────────────────────────────
# generate_suggestions
# ────────────────────────────────────────────

class TestGenerateSuggestions:
    def test_defa_negative_large(self, service):
        result = service.generate_suggestions(defa_int=-3, risk_score=0.5, pred_label="Quartzo")
        assert "Recuperação Intensiva" in result["suggested_action"]
        assert result["suggested_messages"]["family"] != ""
        assert result["suggested_messages"]["professor"] != ""

    def test_defa_negative_moderate(self, service):
        result = service.generate_suggestions(defa_int=-1, risk_score=0.3, pred_label="Ágata")
        assert "Recuperação de Aprendizagem" in result["suggested_action"]

    def test_defa_positive_large(self, service):
        result = service.generate_suggestions(defa_int=3, risk_score=0.1, pred_label="Topázio")
        assert "Aprofundamento" in result["suggested_action"]

    def test_defa_positive_moderate(self, service):
        result = service.generate_suggestions(defa_int=1, risk_score=0.1, pred_label="Topázio")
        assert "Enriquecimento" in result["suggested_action"]

    def test_defa_positive_with_high_risk(self, service):
        """DEFA positivo mas modelo indica risco alto → flag review."""
        result = service.generate_suggestions(defa_int=3, risk_score=0.8, pred_label="Topázio")
        assert "Revisão" in result["suggested_action"]

    def test_defa_zero_critico(self, service):
        result = service.generate_suggestions(defa_int=0, risk_score=0.9, pred_label="Quartzo")
        assert "Psicopedagógica" in result["suggested_action"]

    def test_defa_zero_alto(self, service):
        result = service.generate_suggestions(defa_int=0, risk_score=0.6, pred_label="Ágata")
        assert "Acompanhamento Intensivo" in result["suggested_action"]

    def test_defa_zero_topazio(self, service):
        result = service.generate_suggestions(defa_int=0, risk_score=0.2, pred_label="Topázio")
        assert "Enriquecimento" in result["suggested_action"]

    def test_defa_zero_moderate_risk(self, service):
        result = service.generate_suggestions(defa_int=0, risk_score=0.3, pred_label="Ametista")
        assert "Monitoramento" in result["suggested_action"]

    def test_defa_zero_no_risk(self, service):
        result = service.generate_suggestions(defa_int=0, risk_score=None, pred_label="Quartzo")
        assert result["suggested_action"] == "Monitoramento"
        assert "Sem modelo" in result["suggested_messages"]["family"]

    def test_student_name_in_messages(self, service):
        result = service.generate_suggestions(
            defa_int=3, risk_score=0.1, pred_label="Topázio", student_name="João"
        )
        assert "João" in result["suggested_messages"]["family"]


# ────────────────────────────────────────────
# make_prediction
# ────────────────────────────────────────────

class TestMakePrediction:
    def test_model_none(self, service):
        probs, pred = service.make_prediction(pd.DataFrame(), model=None)
        assert probs is None
        assert pred is None

    def test_model_with_feature_names(self, service):
        """Modelo com feature_names_in_ usa predição direta."""
        model = MagicMock()
        model.feature_names_in_ = ["IAN", "IDA"]
        model.predict_proba.return_value = np.array([[0.3, 0.7]])
        model.predict.return_value = np.array([1])

        df = pd.DataFrame([{"IAN": 5.0, "IDA": 6.0}])
        probs, pred = service.make_prediction(df, model=model)
        assert pred == 1
        np.testing.assert_allclose(probs, [0.3, 0.7])

    def test_model_without_feature_names_no_imputer(self, service):
        """Modelo sem feature_names_in_ → fallback com imputation manual."""
        model = MagicMock(spec=["predict_proba", "predict"])
        model.predict_proba.return_value = np.array([[0.2, 0.8]])
        model.predict.return_value = np.array([1])

        df = pd.DataFrame([{"IAN": 5.0}])
        probs, pred = service.make_prediction(df, model=model)
        assert pred == 1

    def test_model_with_imputer_feature_names(self, service):
        """Modelo cai no fallback; imputer tem feature_names_in_."""
        model = MagicMock(spec=["predict_proba", "predict"])
        model.predict_proba.return_value = np.array([[0.4, 0.6]])
        model.predict.return_value = np.array([0])

        imputer = MagicMock()
        imputer.feature_names_in_ = np.array(["IAN"])
        imputer.transform.return_value = np.array([[5.0]])

        df = pd.DataFrame([{"IAN": 5.0}])
        probs, pred = service.make_prediction(df, model=model, imputer=imputer)
        assert pred == 0

    def test_model_with_imputer_no_feature_names(self, service):
        """Imputer sem feature_names_in_ → transform com values."""
        model = MagicMock(spec=["predict_proba", "predict"])
        model.predict_proba.return_value = np.array([[0.1, 0.9]])
        model.predict.return_value = np.array([1])

        imputer = MagicMock(spec=["transform"])
        imputer.transform.return_value = np.array([[5.0]])

        df = pd.DataFrame([{"IAN": 5.0}])
        probs, pred = service.make_prediction(df, model=model, imputer=imputer)
        assert pred == 1

    def test_model_with_scaler(self, service):
        """Scaler é aplicado após imputer."""
        model = MagicMock(spec=["predict_proba", "predict"])
        model.predict_proba.return_value = np.array([[0.5, 0.5]])
        model.predict.return_value = np.array([0])

        scaler = MagicMock()
        scaler.transform.return_value = np.array([[0.0]])

        df = pd.DataFrame([{"IAN": 5.0}])
        probs, pred = service.make_prediction(df, model=model, scaler=scaler)
        assert pred == 0
        scaler.transform.assert_called_once()

    def test_imputer_transform_fails_falls_to_manual(self, service):
        """Imputer transform falha → cai no _manual_imputation_fallback."""
        model = MagicMock(spec=["predict_proba", "predict"])
        model.predict_proba.return_value = np.array([[0.6, 0.4]])
        model.predict.return_value = np.array([0])

        imputer = MagicMock()
        imputer.feature_names_in_ = np.array(["IAN"])
        imputer.transform.side_effect = ValueError("bad imputer")
        imputer.statistics_ = [5.0]

        df = pd.DataFrame([{"IAN": np.nan}])
        probs, pred = service.make_prediction(df, model=model, imputer=imputer)
        assert pred == 0

    def test_total_failure_raises_http(self, service):
        """Todos os caminhos falham → HTTPException 500."""
        model = MagicMock(spec=["predict_proba", "predict"])
        model.predict_proba.side_effect = Exception("total fail")
        model.predict.side_effect = Exception("total fail")

        df = pd.DataFrame([{"IAN": 5.0}])
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            service.make_prediction(df, model=model)
        assert exc_info.value.status_code == 500


# ────────────────────────────────────────────
# _manual_imputation_fallback
# ────────────────────────────────────────────

class TestManualImputationFallback:
    def test_no_imputer(self, service):
        df = pd.DataFrame([{"A": np.nan, "B": 2.0}])
        result = service._manual_imputation_fallback(df)
        # NaN should become 0.0
        assert result[0][0] == 0.0
        assert result[0][1] == 2.0

    def test_with_imputer_statistics(self, service):
        imputer = MagicMock()
        imputer.feature_names_in_ = np.array(["A", "B"])
        imputer.statistics_ = [1.5, 3.0]

        df = pd.DataFrame([{"A": np.nan, "B": np.nan}])
        result = service._manual_imputation_fallback(df, imputer=imputer)
        # Should be filled by statistics
        assert result[0][0] == 1.5
        assert result[0][1] == 3.0

    def test_with_feature_medians(self, service, mock_model_service):
        mock_model_service.feature_medians = pd.Series({"X": 4.0, "Y": 6.0})

        df = pd.DataFrame([{"X": np.nan, "Y": np.nan}])
        result = service._manual_imputation_fallback(df)
        assert result[0][0] == 4.0
        assert result[0][1] == 6.0

    def test_imputer_with_bad_stats(self, service):
        """statistics_ com valor não finito."""
        imputer = MagicMock(spec=["feature_names_in_", "statistics_"])
        imputer.feature_names_in_ = np.array(["A"])
        imputer.statistics_ = [np.inf]

        df = pd.DataFrame([{"A": np.nan}])
        result = service._manual_imputation_fallback(df, imputer=imputer)
        assert result[0][0] == 0.0  # inf is skipped, falls to fillna(0)


# ────────────────────────────────────────────
# prepare_features
# ────────────────────────────────────────────

class TestPrepareFeatures:
    def test_creates_consistencia_acad(self, service):
        data = {"IDA": 8.0, "IEG": 4.0}
        df = service.prepare_features(data)
        expected = 8.0 / (4.0 + 0.1)
        assert abs(df["consistencia_acad"].iloc[0] - expected) < 1e-6

    def test_no_ida_ieg(self, service):
        data = {}
        df = service.prepare_features(data)
        assert df["consistencia_acad"].iloc[0] == 0.0

    def test_custom_features(self, service):
        data = {"IAN": 5.0, "IDA": 6.0}
        df = service.prepare_features(data, features=["IAN", "IDA"])
        assert list(df.columns) == ["IAN", "IDA"]


# ────────────────────────────────────────────
# predict_score (integration-like with mocks)
# ────────────────────────────────────────────

class TestPredictScoreUnit:
    def test_both_models_none_returns_fallback(self, service, mock_model_service):
        """Sem nenhum modelo → HTTPException."""
        mock_model_service.model_pipeline = None
        mock_model_service.model_pipeline_risk = None

        metrics = StudentMetrics(IAN=5, IDA=5, IEG=5, IAA=5, IPS=5, IPP=5, IPV=5, FASE=1, DEFA=0)
        # No models → should still work (both pred_idx are None but no error raised)
        result = service.predict_score(metrics)
        assert result["prediction"] == "unknown"

    def test_with_multiclass_model(self, service, mock_model_service):
        model = MagicMock()
        model.feature_names_in_ = mock_model_service.features_list
        model.predict_proba.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
        model.predict.return_value = np.array([3])
        mock_model_service.model_pipeline = model

        metrics = StudentMetrics(IAN=5, IDA=5, IEG=5, IAA=5, IPS=5, IPP=5, IPV=5, FASE=1, DEFA=0)
        result = service.predict_score(metrics)
        assert result["prediction"] == "Topázio"
        assert "probabilities" in result
        assert "historico" in result
        assert isinstance(result["historico"], list)

    def test_with_student_service(self, service, mock_model_service):
        """predict_score passes student_service to get history."""
        model = MagicMock()
        model.feature_names_in_ = mock_model_service.features_list
        model.predict_proba.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
        model.predict.return_value = np.array([3])
        mock_model_service.model_pipeline = model

        student_svc = MagicMock()
        student_svc.get_student_history.return_value = [
            {"ANO": 2023, "FASE": 1, "IAN": 5.0}
        ]

        metrics = StudentMetrics(
            IAN=5, IDA=5, IEG=5, IAA=5, IPS=5, IPP=5, IPV=5,
            FASE=1, DEFA=0, NOME="Teste"
        )
        result = service.predict_score(metrics, student_service=student_svc)
        assert len(result["historico"]) == 1
        student_svc.get_student_history.assert_called_once_with("Teste")

    def test_student_service_exception_is_caught(self, service, mock_model_service):
        """Se student_service falha, historico fica vazio."""
        model = MagicMock()
        model.feature_names_in_ = mock_model_service.features_list
        model.predict_proba.return_value = np.array([[0.5, 0.5]])
        model.predict.return_value = np.array([0])
        mock_model_service.model_pipeline = model

        student_svc = MagicMock()
        student_svc.get_student_history.side_effect = RuntimeError("boom")

        metrics = StudentMetrics(
            IAN=5, IDA=5, IEG=5, IAA=5, IPS=5, IPP=5, IPV=5,
            FASE=1, DEFA=0, NOME="Teste"
        )
        result = service.predict_score(metrics, student_service=student_svc)
        assert result["historico"] == []

    def test_with_risk_model_only(self, service, mock_model_service):
        """Sem multiclasse, só modelo de risco."""
        mock_model_service.model_pipeline = None

        risk_model = MagicMock()
        risk_model.feature_names_in_ = mock_model_service.features_list
        risk_model.predict_proba.return_value = np.array([[0.3, 0.7]])
        risk_model.predict.return_value = np.array([1])
        mock_model_service.model_pipeline_risk = risk_model

        metrics = StudentMetrics(IAN=5, IDA=5, IEG=5, IAA=5, IPS=5, IPP=5, IPV=5, FASE=1, DEFA=0)
        result = service.predict_score(metrics)
        assert result["prediction"] == "Crítico"
        assert result["risk_score"] is not None

    def test_multiclass_error_fallback_to_risk(self, service, mock_model_service):
        """Multiclasse falha mas risco funciona."""
        multi = MagicMock()
        multi.feature_names_in_ = mock_model_service.features_list
        multi.predict_proba.side_effect = Exception("fail")
        multi.predict.side_effect = Exception("fail")
        mock_model_service.model_pipeline = multi

        risk_model = MagicMock()
        risk_model.feature_names_in_ = mock_model_service.features_list
        risk_model.predict_proba.return_value = np.array([[0.2, 0.8]])
        risk_model.predict.return_value = np.array([1])
        mock_model_service.model_pipeline_risk = risk_model

        metrics = StudentMetrics(IAN=5, IDA=5, IEG=5, IAA=5, IPS=5, IPP=5, IPV=5, FASE=1, DEFA=-3)
        result = service.predict_score(metrics)
        assert result["prediction"] == "Crítico"

    def test_defa_parsing_edge_case(self, service, mock_model_service):
        """DEFA com valor não numérico → default 0."""
        mock_model_service.model_pipeline = None
        mock_model_service.model_pipeline_risk = None

        metrics = StudentMetrics(IAN=5, IDA=5, IEG=5, IAA=5, IPS=5, IPP=5, IPV=5, FASE=1)
        result = service.predict_score(metrics)
        assert result["defa_int"] == 0
