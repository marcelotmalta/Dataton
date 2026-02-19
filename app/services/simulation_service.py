# services/simulation_service.py
"""
Serviço de simulação contrafactual.
Permite testar cenários "e se?" para avaliar o impacto
de mudanças em indicadores na predição de um aluno.
"""
import numpy as np
from fastapi import HTTPException
from typing import Dict, Any

from app.utils.helpers import sanitize_for_json


class SimulationService:
    """Executa simulações contrafactuais sobre predições de alunos"""

    def __init__(self, model_service, prediction_service):
        self.model_service = model_service
        self.prediction_service = prediction_service

    def _get_latest_student_data(self, student_name: str) -> tuple:
        """
        Busca o registro mais recente de um aluno.

        Args:
            student_name: Nome do estudante

        Returns:
            Tupla (nome_real, dados_originais)

        Raises:
            HTTPException: Se dados indisponíveis ou aluno não encontrado
        """
        df = self.model_service.df_base

        if df is None:
            raise HTTPException(status_code=503, detail="Data not available")

        # Match exato primeiro
        matches = df[df["NOME"].str.fullmatch(student_name, case=False, na=False)]
        if matches.empty:
            matches = df[df["NOME"].str.contains(student_name, case=False, na=False)]
            if matches.empty:
                raise HTTPException(status_code=404, detail="Student not found")

        real_name = matches.iloc[0]["NOME"]
        student_records = matches[matches["NOME"] == real_name]

        # Pegar registro mais recente
        if "ANO" in student_records.columns:
            latest = student_records.sort_values("ANO", ascending=False).iloc[0]
        else:
            latest = student_records.iloc[0]

        # Extrair dados numéricos
        original_data = {}
        for col in ["IAN", "IDA", "IEG", "IAA", "IPS", "IPP", "IPV", "FASE", "DEFA"]:
            val = latest.get(col)
            if val is not None:
                try:
                    if not np.isnan(float(val)):
                        original_data[col] = float(val)
                    else:
                        original_data[col] = None
                except (TypeError, ValueError):
                    original_data[col] = None
            else:
                original_data[col] = None

        return real_name, original_data

    def _run_prediction(self, input_data: dict) -> tuple:
        """
        Executa predição completa a partir de dados de entrada.

        Args:
            input_data: Dicionário com métricas do aluno

        Returns:
            Tupla (label_predito, risk_score)
        """
        df_pred = self.prediction_service.prepare_features(input_data.copy())
        probs, pred_idx = self.prediction_service.make_prediction(df_pred)
        risk = self.prediction_service.calculate_risk_score(probs)

        # Mapear label
        pred_label = str(pred_idx) if pred_idx is not None else "unknown"
        if self.model_service.mapa_classes_inv and pred_idx is not None:
            pred_label = self.model_service.mapa_classes_inv.get(
                int(pred_idx), str(pred_idx)
            )

        return pred_label, risk

    def simulate_scenario(
        self,
        student_name: str,
        changes: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Simulação contrafactual: testa como mudanças em indicadores
        afetariam a predição do aluno.

        Permite ao coordenador testar cenários como:
        "Se este aluno melhorar o IEG em 1 ponto, ele sai da categoria Quartzo?"

        Args:
            student_name: Nome do estudante
            changes: Dicionário com mudanças propostas (ex: {"IEG": 6.0})

        Returns:
            Dicionário com predição original vs simulada e análise de impacto
        """
        real_name, original_data = self._get_latest_student_data(student_name)

        # Predição original
        original_input = original_data.copy()
        original_input["NOME"] = real_name
        pred_label_orig, risk_orig = self._run_prediction(original_input)

        # Predição simulada (aplicar mudanças)
        simulated_input = original_input.copy()
        original_values = {}
        for key, new_val in changes.items():
            if key in simulated_input:
                original_values[key] = simulated_input[key]
                simulated_input[key] = float(new_val)

        pred_label_sim, risk_sim = self._run_prediction(simulated_input)

        # Calcular delta de risco
        delta_risk = None
        if risk_orig is not None and risk_sim is not None:
            delta_risk = round(risk_sim - risk_orig, 4)

        # Avaliar impacto
        impacto = _evaluate_impact(
            pred_label_orig, pred_label_sim,
            risk_orig, risk_sim
        )

        return sanitize_for_json({
            "nome": real_name,
            "original_prediction": pred_label_orig,
            "simulated_prediction": pred_label_sim,
            "original_risk": round(risk_orig, 4) if risk_orig is not None else None,
            "simulated_risk": round(risk_sim, 4) if risk_sim is not None else None,
            "delta_risk": delta_risk,
            "impacto": impacto,
            "changes_applied": changes,
            "original_values": original_values
        })


def _evaluate_impact(
    orig_label: str,
    sim_label: str,
    orig_risk: float,
    sim_risk: float
) -> str:
    """Avalia o impacto de uma simulação contrafactual"""
    parts = []

    if orig_label != sim_label:
        parts.append(
            f"Mudança de categoria: {orig_label} → {sim_label}."
        )
    else:
        parts.append(f"A categoria se mantém: {orig_label}.")

    if orig_risk is not None and sim_risk is not None:
        delta = sim_risk - orig_risk
        if abs(delta) < 0.01:
            parts.append("Impacto no risco: mínimo.")
        elif delta < 0:
            parts.append(f"Risco reduzido em {abs(delta):.2%}. Intervenção recomendada.")
        else:
            parts.append(f"Risco aumentou em {delta:.2%}.")

    return " ".join(parts)
