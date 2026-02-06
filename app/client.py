import requests
import streamlit as st
from .config import API_PREDICT_ENDPOINT

def get_prediction(payload: dict) -> dict:
    """
    Envia o payload com dados do aluno para a API de predição.
    Retorna o JSON de resposta ou levanta exceção.
    """
    try:
        response = requests.post(API_PREDICT_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro na API: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar à API. Verifique se o servidor `uvicorn` está rodando.")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None
