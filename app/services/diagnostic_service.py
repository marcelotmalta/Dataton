# services/diagnostic_service.py
"""
Serviço de diagnóstico automatizado para suporte à decisão pedagógica.
Cruza indicadores de desempenho com trajetória histórica para gerar
diagnósticos e intervenções recomendadas.
"""
from typing import Dict, Any, List
from fastapi import HTTPException

from app.config import (
    logger,
    THRESHOLD_LOW_ACADEMIC,
    THRESHOLD_LOW_ENGAGEMENT,
    THRESHOLD_LOW_PSYCHO
)
from app.utils.helpers import sanitize_for_json


class DiagnosticService:
    """Gera diagnósticos automatizados e recomendações de intervenção"""

    def __init__(self, model_service, history_service):
        self.model_service = model_service
        self.history_service = history_service

    def _get_latest_record(self, name: str) -> Dict[str, Any]:
        """
        Obtém o registro mais recente de um aluno.

        Args:
            name: Nome do estudante

        Returns:
            Dicionário com os dados do registro mais recente
        """
        df = self.model_service.df_base

        if df is None:
            raise HTTPException(status_code=503, detail="Data not available")

        # Match exato primeiro
        matches = df[df["NOME"].str.fullmatch(name, case=False, na=False)]

        if matches.empty:
            matches = df[df["NOME"].str.contains(name, case=False, na=False)]
            if matches.empty:
                raise HTTPException(status_code=404, detail="Student not found")

        student_name = matches.iloc[0]["NOME"]
        student_records = matches[matches["NOME"] == student_name]

        # Pegar registro mais recente (maior ANO)
        if "ANO" in student_records.columns:
            latest = student_records.sort_values("ANO", ascending=False).iloc[0]
        else:
            latest = student_records.iloc[0]

        return latest.to_dict(), student_name

    def _diagnose_academic(self, record: Dict) -> List[Dict]:
        """
        Diagnóstico de Gargalo Acadêmico (baixo IDA/IAN).

        Intervenção: Aulas de nivelamento e reforço em contraturno.
        """
        diagnostics = []
        indicadores = []
        ida = record.get("IDA")
        ian = record.get("IAN")

        ida_low = ida is not None and _safe_float(ida) < THRESHOLD_LOW_ACADEMIC
        ian_low = ian is not None and _safe_float(ian) < THRESHOLD_LOW_ACADEMIC

        if ida_low:
            indicadores.append(f"IDA={_safe_float(ida):.2f}")
        if ian_low:
            indicadores.append(f"IAN={_safe_float(ian):.2f}")

        if indicadores:
            # Determinar gravidade
            values = []
            if ida_low:
                values.append(_safe_float(ida))
            if ian_low:
                values.append(_safe_float(ian))

            min_val = min(values)
            if min_val < 3.0:
                gravidade = "grave"
            elif min_val < 4.0:
                gravidade = "moderado"
            else:
                gravidade = "leve"

            diagnostics.append({
                "tipo": "academico",
                "gravidade": gravidade,
                "indicadores_afetados": indicadores,
                "intervencoes": [
                    "Aulas de nivelamento em contraturno",
                    "Reforço escolar individualizado",
                    "Monitoramento quinzenal de progresso acadêmico"
                ]
            })

        return diagnostics

    def _diagnose_engagement(self, record: Dict) -> List[Dict]:
        """
        Diagnóstico de Risco de Desengajamento (baixo IEG).

        Intervenção: Entrevista com serviço social e inclusão
        em atividades extracurriculares de liderança.
        """
        diagnostics = []
        ieg = record.get("IEG")

        if ieg is not None and _safe_float(ieg) < THRESHOLD_LOW_ENGAGEMENT:
            val = _safe_float(ieg)

            if val < 3.0:
                gravidade = "grave"
            elif val < 4.0:
                gravidade = "moderado"
            else:
                gravidade = "leve"

            diagnostics.append({
                "tipo": "desengajamento",
                "gravidade": gravidade,
                "indicadores_afetados": [f"IEG={val:.2f}"],
                "intervencoes": [
                    "Entrevista com o serviço social",
                    "Inclusão em atividades extracurriculares de liderança",
                    "Programa de mentoria entre pares",
                    "Acompanhamento semanal de frequência e participação"
                ]
            })

        return diagnostics

    def _diagnose_psychosocial(self, record: Dict) -> List[Dict]:
        """
        Diagnóstico de Vulnerabilidade Psicossocial (baixo IPS/IAA).

        Intervenção: Plano de acompanhamento com psicólogos
        e mentorias de autoeficácia.
        """
        diagnostics = []
        indicadores = []
        ips = record.get("IPS")
        iaa = record.get("IAA")

        ips_low = ips is not None and _safe_float(ips) < THRESHOLD_LOW_PSYCHO
        iaa_low = iaa is not None and _safe_float(iaa) < THRESHOLD_LOW_PSYCHO

        if ips_low:
            indicadores.append(f"IPS={_safe_float(ips):.2f}")
        if iaa_low:
            indicadores.append(f"IAA={_safe_float(iaa):.2f}")

        if indicadores:
            values = []
            if ips_low:
                values.append(_safe_float(ips))
            if iaa_low:
                values.append(_safe_float(iaa))

            min_val = min(values)
            if min_val < 3.0:
                gravidade = "grave"
            elif min_val < 4.0:
                gravidade = "moderado"
            else:
                gravidade = "leve"

            diagnostics.append({
                "tipo": "psicossocial",
                "gravidade": gravidade,
                "indicadores_afetados": indicadores,
                "intervencoes": [
                    "Plano de acompanhamento com psicólogos",
                    "Mentorias de autoeficácia",
                    "Inclusão em grupos de apoio socioemocional",
                    "Comunicação ativa com a família"
                ]
            })

        return diagnostics

    def diagnose_student(self, name: str) -> Dict[str, Any]:
        """
        Executa diagnóstico completo de um estudante, combinando:
        - Indicadores atuais (IDA, IAN, IEG, IPS, IAA)
        - Trajetória histórica (tendência do INDE)
        - Cruzamento IPV × IDA

        Args:
            name: Nome do estudante

        Returns:
            Dicionário com análise profunda e diagnósticos
        """
        record, student_name = self._get_latest_record(name)

        # Coletar diagnósticos
        all_diagnostics = []
        all_diagnostics.extend(self._diagnose_academic(record))
        all_diagnostics.extend(self._diagnose_engagement(record))
        all_diagnostics.extend(self._diagnose_psychosocial(record))

        # Obter trajetória
        try:
            trajectory = self.history_service.get_student_trajectory(name)
        except HTTPException:
            trajectory = None

        # Obter cruzamento IPV × IDA
        try:
            cross = self.history_service.cross_ipv_ida(name)
        except HTTPException:
            cross = None

        # Enriquecer diagnósticos com dados de trajetória
        if trajectory and trajectory.get("tendencia") == "descendente":
            # Se trajetória é descendente, aumentar gravidade dos diagnósticos
            for diag in all_diagnostics:
                if diag["gravidade"] == "leve":
                    diag["gravidade"] = "moderado"
                    diag["intervencoes"].append(
                        "⚠️ Trajetória descendente detectada — intensificar acompanhamento"
                    )

        # Se cruzamento IPV×IDA indica queda, adicionar contexto
        if cross and cross.get("tipo_queda") in ("técnica", "maturidade", "combinada"):
            tipo = cross["tipo_queda"]
            for diag in all_diagnostics:
                if tipo == "técnica" and diag["tipo"] == "academico":
                    diag["intervencoes"].append(
                        "📊 Cruzamento IPV×IDA confirma queda técnica — foco em reforço acadêmico"
                    )
                elif tipo == "maturidade" and diag["tipo"] in ("desengajamento", "psicossocial"):
                    diag["intervencoes"].append(
                        "🧠 Cruzamento IPV×IDA confirma queda de maturidade — foco em acompanhamento comportamental"
                    )

        # Gerar resumo textual
        resumo = _generate_summary(student_name, all_diagnostics, trajectory, cross)

        # Buscar histórico completo
        try:
            from app.services.student_service import StudentService
            student_svc = StudentService(self.model_service)
            historico_data = student_svc.search_student_by_name(name)
            historico = historico_data.get("historico", [])
        except Exception:
            historico = []

        return sanitize_for_json({
            "nome": student_name,
            "historico": historico,
            "trajetoria": trajectory,
            "cruzamento_ipv_ida": cross,
            "diagnosticos": all_diagnostics,
            "resumo": resumo
        })


def _safe_float(value) -> float:
    """Converte um valor para float de forma segura"""
    try:
        import numpy as np
        v = float(value)
        if np.isnan(v) or np.isinf(v):
            return 0.0
        return v
    except (TypeError, ValueError):
        return 0.0


def _generate_summary(
    name: str,
    diagnostics: List[Dict],
    trajectory: Dict,
    cross: Dict
) -> str:
    """Gera um resumo textual do diagnóstico"""
    parts = [f"Análise profunda de {name}:"]

    if not diagnostics:
        parts.append("✅ Nenhum problema significativo identificado nos indicadores atuais.")
    else:
        graves = [d for d in diagnostics if d["gravidade"] == "grave"]
        moderados = [d for d in diagnostics if d["gravidade"] == "moderado"]
        leves = [d for d in diagnostics if d["gravidade"] == "leve"]

        if graves:
            tipos = ", ".join(d["tipo"] for d in graves)
            parts.append(f"🔴 {len(graves)} diagnóstico(s) GRAVE(s): {tipos}.")
        if moderados:
            tipos = ", ".join(d["tipo"] for d in moderados)
            parts.append(f"🟡 {len(moderados)} diagnóstico(s) MODERADO(s): {tipos}.")
        if leves:
            tipos = ", ".join(d["tipo"] for d in leves)
            parts.append(f"🟢 {len(leves)} diagnóstico(s) LEVE(s): {tipos}.")

    if trajectory:
        tend = trajectory.get("tendencia", "insuficiente")
        if tend == "descendente":
            parts.append(f"📉 Trajetória DESCENDENTE (inclinação: {trajectory.get('inclinacao', 0):.3f}).")
        elif tend == "ascendente":
            parts.append(f"📈 Trajetória ASCENDENTE (inclinação: {trajectory.get('inclinacao', 0):.3f}).")
        elif tend == "estável":
            parts.append("➡️ Trajetória estável.")

    if cross and cross.get("tipo_queda") and cross["tipo_queda"] != "nenhuma":
        parts.append(f"🔍 Cruzamento IPV×IDA: queda {cross['tipo_queda']}.")

    return " ".join(parts)
