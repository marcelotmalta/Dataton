# services/student_service.py
"""
Serviço para operações relacionadas a estudantes
"""
from fastapi import HTTPException
from app.utils.helpers import sanitize_for_json


class StudentService:
    """Gerencia operações de busca e consulta de estudantes"""
    
    # Campos retornados no histórico
    HISTORY_FIELDS = [
        'ANO', 'FASE', 'IAN', 'IDA', 'IEG', 'IAA', 
        'IPS', 'IPP', 'IPV', 'DEFA'
    ]
    
    def __init__(self, model_service):
        self.model_service = model_service
    
    def _get_student_matches(self, name: str):
        """
        Busca registros do estudante no DataFrame.
        
        Args:
            name: Nome do estudante (busca exata ou parcial)
            
        Returns:
            DataFrame com registros encontrados
            
        Raises:
            HTTPException: Se dados não disponíveis ou estudante não encontrado
        """
        df = self.model_service.df_base
        
        if df is None:
            raise HTTPException(status_code=503, detail="Data not available")
        
        if "NOME" not in df.columns:
            raise HTTPException(
                status_code=404, 
                detail="Student name column 'NOME' not available"
            )
        
        # Tentar match exato primeiro
        matches = df[df["NOME"].str.fullmatch(name, case=False, na=False)]
        
        # Se não encontrar, tentar busca parcial
        if matches.empty:
            matches = df[df["NOME"].str.contains(name, case=False, na=False)]
            if matches.empty:
                raise HTTPException(status_code=404, detail="Student not found")
        
        return matches
    
    def _build_historico(self, matches):
        """
        Constrói lista de histórico ordenada por ANO ascendente.
        
        Args:
            matches: DataFrame com registros do estudante
            
        Returns:
            Lista de dicionários com dados históricos
        """
        historico = []
        for _, row in matches.iterrows():
            item = {}
            for f in self.HISTORY_FIELDS:
                item[f] = row.get(f)
            historico.append(item)
        
        # Ordenar por ANO ascendente para facilitar gráficos
        historico.sort(key=lambda x: (x.get('ANO') or 0, x.get('FASE') or 0))
        return historico
    
    def search_student_by_name(self, name: str):
        """
        Busca estudante por nome e retorna histórico
        
        Args:
            name: Nome do estudante (busca exata ou parcial)
            
        Returns:
            Dicionário com nome e histórico do estudante
            
        Raises:
            HTTPException: Se dados não disponíveis ou estudante não encontrado
        """
        matches = self._get_student_matches(name)
        first_match = matches.iloc[0]
        historico = self._build_historico(matches)
        
        return sanitize_for_json({
            "nome": first_match.get("NOME"),
            "historico": historico
        })
    
    def get_student_history(self, name: str):
        """
        Retorna apenas o histórico de um aluno (usado pelo prediction_service).
        
        Args:
            name: Nome exato ou parcial do aluno
            
        Returns:
            Lista de dicionários com o histórico, ou lista vazia se não encontrado
        """
        try:
            matches = self._get_student_matches(name)
            return self._build_historico(matches)
        except HTTPException:
            return []
