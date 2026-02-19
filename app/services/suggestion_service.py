# services/suggestion_service.py
"""
Serviço de geração de recomendações pedagógicas.
Gera ações sugeridas e mensagens para família e professores
baseadas em DEFA e score de risco.
"""
from typing import Dict, Any

from app.config import DEFA_LARGE_THRESHOLD
from app.utils.helpers import risk_tier_from_score


class SuggestionService:
    """Gera ações sugeridas e mensagens de intervenção pedagógica"""

    def generate_suggestions(
        self,
        defa_int: int,
        risk_score: float,
        pred_label: str,
        student_name: str = None
    ) -> Dict[str, Any]:
        """
        Gera ações sugeridas e mensagens baseadas em DEFA e risco.

        Args:
            defa_int: Valor inteiro de DEFA
            risk_score: Score de risco calculado
            pred_label: Label da predição
            student_name: Nome do estudante (opcional)

        Returns:
            Dicionário com ação sugerida e mensagens
        """
        suggested_action = "Manutenção do Desempenho"
        suggested_messages = {"family": "", "professor": ""}

        nome = student_name or "O aluno"

        if defa_int < 0:
            suggested_action, suggested_messages = self._handle_negative_defa(
                defa_int, suggested_messages
            )
        elif defa_int > 0:
            suggested_action, suggested_messages = self._handle_positive_defa(
                defa_int, risk_score, nome, suggested_messages
            )
        else:
            suggested_action, suggested_messages = self._handle_zero_defa(
                risk_score, pred_label, suggested_messages
            )

        return {
            "suggested_action": suggested_action,
            "suggested_messages": suggested_messages
        }

    def _handle_negative_defa(
        self, defa_int: int, messages: Dict[str, str]
    ) -> tuple:
        """DEFA negativo = problema (defasagem)"""
        if defa_int <= -DEFA_LARGE_THRESHOLD:
            action = "Recuperação Intensiva (grave)"
            messages["family"] = (
                f"Detectamos defasagem grave (DEFA={defa_int}). "
                "Requer reunião imediata com coordenação."
            )
            messages["professor"] = (
                "Acionar plano de intervenção intensiva, "
                "tutorias diárias, contato família."
            )
        else:
            action = "Recuperação de Aprendizagem"
            messages["family"] = (
                f"Detectamos defasagem (DEFA={defa_int}). "
                "Recomendamos plano de recuperação de curto prazo."
            )
            messages["professor"] = (
                "Atividades focalizadas e monitoramento."
            )
        return action, messages

    def _handle_positive_defa(
        self, defa_int: int, risk_score: float,
        nome: str, messages: Dict[str, str]
    ) -> tuple:
        """DEFA positivo = aluno adiantado"""
        if defa_int >= DEFA_LARGE_THRESHOLD:
            action = "Aprofundamento / Enriquecimento (alto)"
            messages["family"] = (
                f"{nome} está adiantado (DEFA={defa_int}). "
                "Sugerimos aprofundamento/possível aceleração."
            )
            messages["professor"] = (
                "Projetos de aprofundamento, mentorias, avaliar aceleração."
            )
        else:
            action = "Enriquecimento Curricular (moderado)"
            messages["family"] = (
                f"{nome} está ligeiramente adiantado (DEFA={defa_int}). "
                "Sugerimos atividades de extensão."
            )
            messages["professor"] = (
                "Desafios adicionais e monitorar engajamento."
            )

        # Se modelo indica alto risco apesar de estar adiantado, flag review
        if risk_score is not None and risk_score >= 0.75:
            action += " + Revisão"
            messages["family"] += (
                " (Nota: modelo indica risco; revisar caso.)"
            )
            messages["professor"] += " (Rever indicador de risco.)"

        return action, messages

    def _handle_zero_defa(
        self, risk_score: float, pred_label: str,
        messages: Dict[str, str]
    ) -> tuple:
        """DEFA = 0: seguir risk_score ou monitoramento padrão"""
        if risk_score is not None:
            tier = risk_tier_from_score(risk_score)

            if tier == "Crítico":
                action = "Intervenção Psicopedagógica"
                messages["family"] = (
                    "Detectamos risco crítico. "
                    "Agendar apoio psicopedagógico urgente."
                )
                messages["professor"] = (
                    "Priorizar acompanhamento intensivo e "
                    "comunicação com a família."
                )
            elif tier == "Alto":
                action = "Acompanhamento Intensivo"
                messages["family"] = (
                    "Sinais de risco. Recomendamos tutoria "
                    "1-2x/semana por 4 semanas."
                )
                messages["professor"] = (
                    "Planejar recuperação focalizada e monitorar semanalmente."
                )
            elif (isinstance(pred_label, str) and
                  pred_label.strip().lower() in ("topázio", "topazio")):
                action = "Enriquecimento Curricular"
                messages["family"] = (
                    "Bom desempenho — sugerimos atividades de aprofundamento."
                )
                messages["professor"] = "Oferecer desafios e extensão."
            else:
                action = "Monitoramento e Micro-intervenção"
                messages["family"] = (
                    "Acompanhamento de rotina; entraremos em contato "
                    "se houver piora."
                )
                messages["professor"] = (
                    "Monitorar evolução e aplicar micro-intervenção se necessário."
                )
        else:
            # Sem modelo disponível
            action = "Monitoramento"
            messages["family"] = (
                "Sem modelo disponível: faremos revisão por DEFA e "
                "acompanhamento de rotina."
            )
            messages["professor"] = (
                "Monitorar presença e desempenho; reportar casos de atenção."
            )

        return action, messages
