import streamlit as st
import sys
from pathlib import Path

st.set_page_config(page_title="Sistema BCB v2.0 - SEM CACHE", layout="wide")

# Path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# SIDEBAR
st.sidebar.title("🏛️ Sistema BCB v2.0")
st.sidebar.markdown("**ARQUIVO TOTALMENTE NOVO**")
st.sidebar.markdown("---")

# Navegação
page = st.sidebar.selectbox(
    "Navegação:", 
    ["🏠 Página Inicial", "📥 Coleta de Dados", "📊 Dashboard", "🤖 Machine Learning", "📋 Relatórios"]
)

# Status
st.sidebar.markdown("---")
try:
    from config import config
    st.sidebar.success("✅ Sistema Online")
    st.sidebar.info(f"v{config.version}")
except:
    st.sidebar.warning("Config pendente")

# CONTEÚDO
try:
    if page == "🏠 Página Inicial":
        from modules.home_module import HomeModule
        module = HomeModule()
        module.render()

    elif page == "📥 Coleta de Dados":
        from modules.data_collection_module import DataCollectionModule
        module = DataCollectionModule()
        module.render()

    elif page == "📊 Dashboard":
        from modules.dashboard_module import DashboardModule
        module = DashboardModule()
        module.render()

    elif page == "🤖 Machine Learning":
        from modules.ml_module import MLModule
        module = MLModule()
        module.render()

    elif page == "📋 Relatórios":
        from modules.reports_module import ReportsModule
        module = ReportsModule()
        module.render()

except Exception as e:
    st.error("⚠️ Módulo indisponível")
    with st.expander("Detalhes"):
        st.code(str(e))

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Sistema Econômico BCB v2.0")

# forçar atualização.

