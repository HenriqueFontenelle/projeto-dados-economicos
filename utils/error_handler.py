# utils/error_handler.py
import streamlit as st
import logging
import traceback
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Manipulador de erros da aplicação"""
    
    @contextmanager
    def error_boundary(self):
        """Context manager para capturar e tratar erros"""
        try:
            yield
        except Exception as e:
            self.handle_error(e)
    
    def handle_error(self, error: Exception, context: str = ""):
        """Trata erro de forma padronizada"""
        
        error_msg = str(error)
        error_type = type(error).__name__
        
        # Log do erro
        logger.error(f"Erro {context}: {error_type} - {error_msg}", exc_info=True)
        
        # Mostrar erro para usuário
        st.error(f"❌ Ocorreu um erro: {error_type}")
        
        with st.expander("Detalhes do erro"):
            st.code(f"""
Contexto: {context}
Tipo: {error_type}
Mensagem: {error_msg}

Trace:
{traceback.format_exc()}
            """)
        
        # Sugestões de solução
        self._show_error_suggestions(error_type)
    
    def _show_error_suggestions(self, error_type: str):
        """Mostra sugestões baseadas no tipo de erro"""
        
        suggestions = {
            'ConnectionError': [
                "Verifique sua conexão com a internet",
                "Confirme se a API do BCB está funcionando",
                "Tente novamente em alguns minutos"
            ],
            'KeyError': [
                "Verifique se todos os dados necessários estão disponíveis",
                "Tente coletar dados novamente",
                "Confirme se o indicador selecionado existe"
            ],
            'ValueError': [
                "Verifique se os parâmetros estão corretos",
                "Confirme se há dados suficientes para análise",
                "Tente ajustar as configurações"
            ]
        }
        
        if error_type in suggestions:
            st.info("💡 **Possíveis soluções:**")
            for suggestion in suggestions[error_type]:
                st.markdown(f"• {suggestion}")