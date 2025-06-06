# modules/home_module.py
import streamlit as st
from config import config
from utils.base_module import BaseModule

class HomeModule(BaseModule):
    """Módulo da página inicial"""
    
    def render(self):
        st.title("🏛️ Sistema de Análise Econômica - Banco Central do Brasil")
        
        st.markdown("""
        ## Bem-vindo ao Sistema de Análise Econômica Avançado
        
        Este sistema foi desenvolvido para análise completa de indicadores econômicos do Brasil,
        utilizando dados oficiais do Banco Central e tecnologias de **Machine Learning** e **Inteligência Artificial**.
        """)
        
        # Cards com funcionalidades
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 Funcionalidades Principais
            
            - **Coleta Automatizada**: 10 anos de dados do BCB
            - **Dashboard Interativo**: Visualizações avançadas
            - **Machine Learning**: Modelos preditivos
            - **Relatórios com IA**: Análises inteligentes
            - **API Robusta**: Tratamento de erros avançado
            """)
        
        with col2:
            st.markdown("""
            ### 🚀 Novidades da Versão 2.0
            
            - ✅ Estrutura modular para equipes
            - ✅ Coleta robusta de 10 anos de dados
            - ✅ Relatórios automáticos com IA
            - ✅ Análise preditiva avançada
            - ✅ Sistema de correlações econômicas
            - ✅ Detecção automática de outliers
            """)
        
        # Métricas rápidas
        st.markdown("### 📈 Status Atual do Sistema")
        
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        
        with metrics_col1:
            st.metric("Indicadores", len(config.data_collection.indicators), "2 novos")
        
        with metrics_col2:
            st.metric("Modelos ML", len(config.ml.available_models), "3 novos")
        
        with metrics_col3:
            st.metric("Anos de Dados", config.data_collection.default_years, "5 a mais")
        
        with metrics_col4:
            st.metric("Tipos de Relatório", len(config.reports.report_types), "4 novos")
        
        st.markdown("---")
        
        # Guia de início rápido
        st.markdown("## 🚀 Guia de Início Rápido")
        
        st.markdown("""
        ### Para começar a usar o sistema:
        
        1. **📥 Coleta de Dados**: Vá para "Coleta de Dados" e atualize a base com os últimos 10 anos
        2. **📊 Dashboard**: Explore os indicadores no "Dashboard Econômico" 
        3. **🤖 Machine Learning**: Treine modelos e faça previsões
        4. **📋 Relatórios**: Gere análises automáticas com IA
        
        > **Dica**: O sistema agora suporta trabalho em equipe - cada módulo pode ser desenvolvido independentemente!
        """)
        
        # Informações técnicas
        with st.expander("ℹ️ Informações Técnicas"):
            st.markdown(f"""
            - **Versão**: {config.version}
            - **Ambiente**: {'Debug' if config.debug_mode else 'Produção'}
            - **Indicadores Disponíveis**: {', '.join(list(config.data_collection.indicators.keys())[:5])}...
            - **Modelos ML**: {', '.join(config.ml.available_models[:3])}...
            - **Tipos de Relatório**: {', '.join(config.reports.report_types[:3])}...
            """)