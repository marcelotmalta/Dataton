# utils/helpers.py
"""
Funções auxiliares reutilizáveis
"""
import numpy as np
from typing import Dict, Any, List


def sanitize_for_json(obj):
    """
    Sanitiza objetos para serialização JSON, tratando NaN e Inf
    """
    if isinstance(obj, float):
        return None if np.isnan(obj) or np.isinf(obj) else obj
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) or np.isinf(obj) else float(obj)
    return obj


def risk_tier_from_score(p: float) -> str:
    """
    Classifica o nível de risco baseado no score de probabilidade
    
    Args:
        p: Score de risco (0-1)
        
    Returns:
        Classificação do risco: Crítico, Alto, Moderado ou Baixo
    """
    if p >= 0.75:
        return "Crítico"
    if p >= 0.50:
        return "Alto"
    if p >= 0.25:
        return "Moderado"
    return "Baixo"


def estimate_top_drivers(x_row: Dict[str, Any], features: List[str], app_state) -> List[Dict]:
    """
    Estima os principais fatores (drivers) que contribuem para a predição
    
    Args:
        x_row: Dicionário com os valores das features
        features: Lista de nomes das features
        app_state: Estado da aplicação com modelo e estatísticas
        
    Returns:
        Lista com os top 2 drivers e suas contribuições
    """
    contributions = []
    importances = None
    
    # Tentar obter importâncias das features do modelo
    try:
        clf = app_state.model_pipeline
        if hasattr(clf, "feature_importances_") and getattr(app_state, "features_list", None):
            importances = dict(zip(app_state.features_list, clf.feature_importances_))
    except Exception:
        importances = None
    
    med = getattr(app_state, "feature_medians", None)
    std = getattr(app_state, "feature_stds", None)
    
    for f in features:
        val = x_row.get(f, None)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            continue
        
        try:
            if med is not None and std is not None and f in med.index:
                z = (float(val) - float(med.loc[f])) / float(std.loc[f])
            else:
                z = float(val)
        except Exception:
            z = 0.0
        
        imp = importances.get(f, 0.0) if importances else 1.0
        score = abs(z) * float(imp)
        contributions.append((f, float(score), float(z), float(imp)))
    
    contributions.sort(key=lambda x: x[1], reverse=True)
    
    top = []
    for f, score, z, imp in contributions[:2]:
        top.append({
            "feature": f,
            "score": round(score, 6),
            "z": round(z, 3),
            "importance": round(float(imp), 6)
        })
    
    return top
