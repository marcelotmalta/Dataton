# services/student_service.py
"""
Serviço para operações relacionadas a estudantes
"""
from fastapi import HTTPException
from app.utils.helpers import sanitize_for_json


class StudentService:
    """Gerencia operações de busca e consulta de estudantes"""
    
    def __init__(self, model_service):
        self.model_service = model_service
    
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
        
        first_match = matches.iloc[0]
        
        # Campos esperados pelo frontend
        fields_to_return = [
            'ANO', 'FASE', 'IAN', 'IDA', 'IEG', 'IAA', 
            'IPS', 'IPP', 'IPV', 'DEFA'
        ]
        
        historico = []
        for _, row in matches.iterrows():
            item = {}
            for f in fields_to_return:
                item[f] = row.get(f)
            historico.append(item)
        
        return sanitize_for_json({
            "nome": first_match.get("NOME"),
            "historico": historico
        })
