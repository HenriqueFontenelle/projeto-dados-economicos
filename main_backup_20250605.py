# main.py - Sistema BCB v2.0 Final
import streamlit as st
import sys
from pathlib import Path

# Configurar página
st.set_page_config(
    page_title="Sistema BCB v2.0", 
    page_icon="📊", 
    layout="wide"
)

# Path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# SIDEBAR
st.sidebar.title("🏛️ Sistema BCB v2.0")
st.sidebar.markdown("**Análise Econômica Avançada**")
st.sidebar.markdown("---")

# Verificar status dos módulos
modules_status = {}

try:
    from config import config
    st.sidebar.success("✅ Config")
    modules_status['config'] = True
except Exception as e:
    st.sidebar.error("❌ Config")
    modules_status['config'] = False

try:
    from modules.home_module import HomeModule
    st.sidebar.success("✅ HomeModule")
    modules_status['home'] = True
except Exception as e:
    st.sidebar.error("❌ HomeModule")
    modules_status['home'] = False

try:
    from utils.session_manager import SessionManager
    from utils.error_handler import ErrorHandler
    st.sidebar.success("✅ Utils")
    modules_status['utils'] = True
except Exception as e:
    st.sidebar.error("❌ Utils")
    modules_status['utils'] = False

# Navegação
st.sidebar.markdown("---")
st.sidebar.subheader("🧭 Navegação")

page = st.sidebar.radio(
    "Escolha:",
    ["🏠 Home", "📥 Dados", "📊 Dashboard", "🤖 ML", "📋 Relatórios"]
)

# Status adicional
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Status")

if modules_status.get('config'):
    st.sidebar.info(f"v{config.version}")
    st.sidebar.info(f"{len(config.data_collection.indicators)} indicadores")
else:
    st.sidebar.warning("Config não carregado")

# CONTEÚDO PRINCIPAL
if all(modules_status.values()):
    # Inicializar sessão
    session_manager = SessionManager()
    session_manager.initialize_session()
    
    if page == "🏠 Home":
        try:
            module = HomeModule()
            module.render()
        except Exception as e:
            st.error(f"Erro: {e}")
    
    else:
        st.title(page)
        st.success("🎉 Sistema v2.0 funcionando!")
        st.markdown(f"""
        ### {page}
        
        **Status:** ✅ Módulo pronto para implementação
        
        **Funcionalidades disponíveis:**
        - Estrutura modular para equipes
        - Configuração centralizada ({len(config.data_collection.indicators)} indicadores)
        - {len(config.ml.available_models)} modelos de ML
        - {len(config.reports.report_types)} tipos de relatórios
        """)
        
        if st.button(f"🚀 Implementar {page}"):
            st.info("Módulo será implementado na próxima versão!")

else:
    st.error("❌ Alguns módulos não carregaram")
    st.markdown("""
    ### Módulos em falta:
    
    Crie os arquivos que faltam conforme os status na sidebar.
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Sistema Modular v2.0")
