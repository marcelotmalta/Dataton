import sys
import os
import streamlit as st

# Adiciona o diretório raiz ao sys.path para permitir importações do pacote 'app'
# Isso resolve o erro "ImportError: attempted relative import with no known parent package"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import PAGE_CONFIG, PEDRA_STYLES
from app.client import get_prediction

# Configuração da Página
st.set_page_config(**PAGE_CONFIG)

def render_sidebar():
    """Renderiza a sidebar com o formulário e retorna o payload caso submetido."""
    st.sidebar.header("📝 Dados do Aluno")
    
    with st.sidebar.form(key='student_form'):
        # Dados Acadêmicos
        st.subheader("Indicadores Acadêmicos")
        ian = st.slider("IAN - Adequação de Nível", 0.0, 10.0, 5.0, 0.1, help="Indicador de Adequação ao Nível")
        ida = st.slider("IDA - Desempenho Acadêmico", 0.0, 10.0, 5.0, 0.1, help="Indicador de Desempenho Acadêmico")
        ieg = st.slider("IEG - Engajamento", 0.0, 10.0, 5.0, 0.1, help="Indicador de Engajamento")
        
        # Dados Psicossociais
        st.subheader("Indicadores Psicossociais")
        iaa = st.slider("IAA - Autoavaliação", 0.0, 10.0, 5.0, 0.1, help="Indicador de Autoavaliação")
        ips = st.slider("IPS - Psicossocial", 0.0, 10.0, 5.0, 0.1, help="Indicador Psicossocial")
        
        # Dados Psicopedagógicos
        st.subheader("Indicadores Psicopedagógicos")
        ipp = st.slider("IPP - Psicopedagógico", 0.0, 10.0, 5.0, 0.1, help="Indicador Psicopedagógico")
        ipv = st.slider("IPV - Ponto de Virada", 0.0, 10.0, 5.0, 0.1, help="Indicador de Ponto de Virada")
        
        # Dados de Contexto
        st.subheader("Contexto Escolar")
        fase = st.number_input("Fase", min_value=0, max_value=9, value=0, step=1)
        
        defa_options = {
            "Atrasado (-2 anos)": -2,
            "Atrasado (-1 ano)": -1,
            "No Prazo (0)": 0,
            "Adiantado (+1 ano)": 1,
            "Adiantado (+2 anos)": 2
        }
        defa_label = st.selectbox("Defasagem (DEFA)", list(defa_options.keys()), index=2)
        defa_value = defa_options[defa_label]
        
        submit_button = st.form_submit_button(label='🔍 Analisar Aluno')
        
        if submit_button:
            return {
                "IAN": ian,
                "IDA": ida,
                "IEG": ieg,
                "IAA": iaa,
                "IPS": ips,
                "IPP": ipp,
                "IPV": ipv,
                "FASE": float(fase),
                "DEFA": float(defa_value)
            }
    return None

def render_results(data):
    """Renderiza os resultados da predição."""
    pedra_map = PEDRA_STYLES
    
    pedra = data.get("pedra_conceito", "Desconhecido")
    confianca = data.get("confidence", 0.0)
    sugestoes = data.get("sugestoes_pedagogicas", [])
    
    style = pedra_map.get(pedra, {"color": "gray", "icon": "❓"})
    
    # Colunas para o Header do Resultado
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="background-color: {style['color']}; padding: 20px; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h1 style='margin:0; font-size: 50px;'>{style['icon']}</h1>
            <h2 style='margin:10px 0 0 0;'>{pedra}</h2>
            <p style='margin:5px 0 0 0; opacity: 0.9;'>Confiança: {confianca:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.subheader("📋 Plano de Ação Recomendado")
        if sugestoes:
            for item in sugestoes:
                st.info(f"**{item['perfil']}**: {item['acao']}")
        else:
            st.success("Nenhuma intervenção crítica identificada para este perfil.")

def main():
    # Título e Descrição
    st.title("💎 Diagnóstico Pedagógico - Datathon")
    st.markdown("""
    Este painel permite simular a classificação de alunos e receber sugestões de intervenção pedagógica
    baseadas no modelo de Machine Learning da escola.
    """)
    
    # Render Sidebar & Handle Submission
    payload = render_sidebar()
    
    if payload:
        with st.spinner('Consultando o Oráculo...'):
            data = get_prediction(payload)
            if data:
                render_results(data)

if __name__ == "__main__":
    main()
