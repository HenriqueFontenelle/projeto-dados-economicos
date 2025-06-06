# utils/session_manager.py
import streamlit as st
from datetime import datetime

class SessionManager:
    """Gerenciador de sessão da aplicação"""
    
    def initialize_session(self):
        """Inicializa variáveis de sessão"""
        
        # Página atual
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'
        
        # Dados de sessão
        if 'session_start' not in st.session_state:
            st.session_state.session_start = datetime.now()
        
        # Cache de dados
        if 'cached_data' not in st.session_state:
            st.session_state.cached_data = {}
        
        # Histórico de ações
        if 'action_history' not in st.session_state:
            st.session_state.action_history = []
        
        # Status de módulos
        if 'module_status' not in st.session_state:
            st.session_state.module_status = {
                'data_collection': 'ready',
                'dashboard': 'ready', 
                'ml': 'ready',
                'reports': 'ready'
            }
    
    def log_action(self, action: str, details: dict = None):
        """Registra ação do usuário"""
        entry = {
            'timestamp': datetime.now(),
            'action': action,
            'details': details or {}
        }
        
        st.session_state.action_history.append(entry)
        
        # Manter apenas últimas 50 ações
        if len(st.session_state.action_history) > 50:
            st.session_state.action_history = st.session_state.action_history[-50:]