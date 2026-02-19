# services/history_service.py
"""
Serviço para análise de trajetória histórica de estudantes.
Implementa Variação Interanual do INDE e cruzamento IPV × IDA.
"""
import numpy as np
from fastapi import HTTPException
from typing import Dict, Any, List, Optional

from app.config import logger, TRAJECTORY_STABLE_DELTA
from app.utils.helpers import sanitize_for_json


class HistoryService:
    """Analisa trajetória histórica e evolução interanual de estudantes"""

    INDICATOR_FIELDS = ['INDE', 'IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'DEFA']

    def __init__(self, model_service):
        self.model_service = model_service

    def _get_student_records(self, name: str):
        """
        Busca todos os registros de um aluno ordenados por ano.

        Args:
            name: Nome do estudante

        Returns:
            DataFrame com registros do aluno ordenados por ANO

        Raises:
            HTTPException: Se dados indisponíveis ou aluno não encontrado
        """
        df = self.model_service.df_base

        if df is None:
            raise HTTPException(status_code=503, detail="Data not available")

        if "NOME" not in df.columns or "ANO" not in df.columns:
            raise HTTPException(
                status_code=404,
                detail="Required columns (NOME, ANO) not available"
            )

        # Match exato primeiro
        matches = df[df["NOME"].str.fullmatch(name, case=False, na=False)]

        # Busca parcial se necessário
        if matches.empty:
            matches = df[df["NOME"].str.contains(name, case=False, na=False)]
            if matches.empty:
                raise HTTPException(status_code=404, detail="Student not found")

        # Filtrar pelo primeiro nome encontrado e ordenar por ano
        student_name = matches.iloc[0]["NOME"]
        student_records = matches[matches["NOME"] == student_name].sort_values("ANO")

        return student_name, student_records

    def get_student_trajectory(self, name: str) -> Dict[str, Any]:
        """
        Calcula a trajetória interanual do INDE de um aluno.

        Analisa a inclinação da curva do INDE ao longo dos anos,
        identificando se a trajetória é ascendente, estável ou descendente.

        Args:
            name: Nome do estudante

        Returns:
            Dicionário com análise de trajetória incluindo:
            - anos: lista de anos com registros
            - inde_values: valores do INDE por ano
            - deltas: variações entre anos consecutivos
            - tendencia: classificação (ascendente/estável/descendente)
            - inclinacao: coeficiente angular da regressão linear
            - indicadores_por_ano: todos os indicadores por ano
        """
        student_name, records = self._get_student_records(name)

        anos = records["ANO"].tolist()
        inde_values = []
        indicadores_por_ano = []

        for _, row in records.iterrows():
            inde_val = row.get("INDE")
            inde_values.append(float(inde_val) if inde_val is not None and not _is_nan(inde_val) else None)

            ano_data = {"ANO": row.get("ANO")}
            for field in self.INDICATOR_FIELDS:
                val = row.get(field)
                if val is not None and not _is_nan(val):
                    ano_data[field] = float(val)
                else:
                    ano_data[field] = None
            ano_data["FASE"] = row.get("FASE")
            indicadores_por_ano.append(ano_data)

        # Calcular deltas entre anos consecutivos
        deltas = []
        valid_inde = [(a, v) for a, v in zip(anos, inde_values) if v is not None]

        for i in range(1, len(valid_inde)):
            delta = valid_inde[i][1] - valid_inde[i - 1][1]
            deltas.append(round(delta, 4))

        # Calcular tendência via regressão linear
        inclinacao = 0.0
        tendencia = "insuficiente"  # dados insuficientes

        if len(valid_inde) >= 2:
            x = np.array([v[0] for v in valid_inde], dtype=float)
            y = np.array([v[1] for v in valid_inde], dtype=float)

            # Regressão linear simples: y = a*x + b
            x_mean = x.mean()
            y_mean = y.mean()
            numerator = ((x - x_mean) * (y - y_mean)).sum()
            denominator = ((x - x_mean) ** 2).sum()

            if denominator > 0:
                inclinacao = float(numerator / denominator)
            else:
                inclinacao = 0.0

            # Classificar tendência
            if abs(inclinacao) < TRAJECTORY_STABLE_DELTA:
                tendencia = "estável"
            elif inclinacao > 0:
                tendencia = "ascendente"
            else:
                tendencia = "descendente"

        return sanitize_for_json({
            "nome": student_name,
            "anos": anos,
            "inde_values": inde_values,
            "deltas": deltas,
            "tendencia": tendencia,
            "inclinacao": round(inclinacao, 4),
            "num_registros": len(anos),
            "indicadores_por_ano": indicadores_por_ano
        })

    def cross_ipv_ida(self, name: str) -> Dict[str, Any]:
        """
        Cruzamento IPV × IDA histórico para diagnóstico de tipo de queda.

        Identifica se a queda no desempenho é:
        - Técnica (IDA caiu, IPV manteve) → problema acadêmico
        - De maturidade (IPV caiu, IDA manteve) → problema comportamental
        - Combinada (ambos caíram) → risco amplo

        Args:
            name: Nome do estudante

        Returns:
            Dicionário com análise de cruzamento IPV × IDA
        """
        student_name, records = self._get_student_records(name)

        if len(records) < 2:
            return sanitize_for_json({
                "nome": student_name,
                "analise_disponivel": False,
                "motivo": "Histórico insuficiente (necessário mínimo 2 anos)",
                "tipo_queda": None,
                "detalhes": None
            })

        # Extrair séries temporais de IPV e IDA
        anos = records["ANO"].tolist()
        ipv_values = []
        ida_values = []

        for _, row in records.iterrows():
            ipv = row.get("IPV")
            ida = row.get("IDA")
            ipv_values.append(float(ipv) if ipv is not None and not _is_nan(ipv) else None)
            ida_values.append(float(ida) if ida is not None and not _is_nan(ida) else None)

        # Calcular variações do último período disponível
        valid_pairs = []
        for i in range(len(anos)):
            if ipv_values[i] is not None and ida_values[i] is not None:
                valid_pairs.append((anos[i], ipv_values[i], ida_values[i]))

        if len(valid_pairs) < 2:
            return sanitize_for_json({
                "nome": student_name,
                "analise_disponivel": False,
                "motivo": "Dados de IPV/IDA insuficientes para comparação",
                "tipo_queda": None,
                "detalhes": None
            })

        # Comparar último com penúltimo período
        prev = valid_pairs[-2]
        curr = valid_pairs[-1]

        delta_ipv = curr[1] - prev[1]
        delta_ida = curr[2] - prev[2]

        threshold = TRAJECTORY_STABLE_DELTA

        ida_caiu = delta_ida < -threshold
        ipv_caiu = delta_ipv < -threshold
        ida_manteve = abs(delta_ida) <= threshold
        ipv_manteve = abs(delta_ipv) <= threshold

        # Diagnóstico
        if ida_caiu and ipv_manteve:
            tipo_queda = "técnica"
            descricao = (
                "Queda no desempenho acadêmico (IDA) com manutenção do Ponto de Virada (IPV). "
                "Indica dificuldade técnica/acadêmica, não comportamental."
            )
        elif ipv_caiu and ida_manteve:
            tipo_queda = "maturidade"
            descricao = (
                "Queda no Ponto de Virada (IPV) com manutenção do desempenho (IDA). "
                "Indica perda de maturidade ou engajamento comportamental."
            )
        elif ida_caiu and ipv_caiu:
            tipo_queda = "combinada"
            descricao = (
                "Queda simultânea em IDA e IPV. "
                "Risco amplo: tanto o desempenho técnico quanto o comportamental estão em declínio."
            )
        elif not ida_caiu and not ipv_caiu:
            tipo_queda = "nenhuma"
            descricao = "Não há queda significativa detectada em IDA ou IPV."
        else:
            tipo_queda = "atípica"
            descricao = "Padrão atípico de variação."

        return sanitize_for_json({
            "nome": student_name,
            "analise_disponivel": True,
            "tipo_queda": tipo_queda,
            "descricao": descricao,
            "detalhes": {
                "periodo_anterior": {
                    "ano": prev[0], "IPV": prev[1], "IDA": prev[2]
                },
                "periodo_atual": {
                    "ano": curr[0], "IPV": curr[1], "IDA": curr[2]
                },
                "delta_ipv": round(delta_ipv, 4),
                "delta_ida": round(delta_ida, 4)
            }
        })


def _is_nan(value) -> bool:
    """Verifica se um valor é NaN de forma segura"""
    try:
        return np.isnan(float(value))
    except (TypeError, ValueError):
        return False
