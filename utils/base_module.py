# utils/base_module.py
from abc import ABC, abstractmethod
import streamlit as st

class BaseModule(ABC):
    """Classe base para todos os módulos da aplicação"""
    
    @abstractmethod
    def render(self):
        """Método principal para renderizar o módulo"""
        pass
    
    def _show_error(self, message: str, details: str = None):
        """Mostra erro padronizado"""
        st.error(f"❌ {message}")
        if details:
            with st.expander("Detalhes do erro"):
                st.code(details)
    
    def _show_success(self, message: str):
        """Mostra sucesso padronizado"""
        st.success(f"✅ {message}")
    
    def _show_warning(self, message: str):
        """Mostra aviso padronizado"""
        st.warning(f"⚠️ {message}")