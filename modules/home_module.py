# modules/home_module.py
import streamlit as st
from config import config
from utils.base_module import BaseModule

class HomeModule(BaseModule):
    """Módulo da página inicial"""
    
    def render(self):
        # Header da Squad7
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1f4e79 0%, #2e86ab 100%); 
                    padding: 20px; 
                    border-radius: 10px; 
                    margin-bottom: 30px; 
                    text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.5em; font-weight: bold;">
                🚀 Squad7 - MDS 2025-1
            </h1>
            <h3 style="color: #e8f4fd; margin: 10px 0 0 0; font-weight: normal;">
                Sistema de Análise Econômica - Banco Central do Brasil
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.title("🎯 Projeto Desenvolvido pela Squad7")
        
        st.info("""
        👥 **Squad7 - MDS 2025-1**  
        🧑‍💼 **Scrum Master:** Rafael  
        🎯 **Disciplina:** Métodos de Desenvolvimento de Software  
        📅 **Período:** 2025-1  
        🏆 **Versão:** 2.0.0 - Arquitetura Modular
        """)
        
        st.markdown("""
        Este sistema foi desenvolvido pela **Squad7** na disciplina **MDS 2025-1**,
        com orientação do **Scrum Master Rafael**.
        """)
        
        # Funcionalidades
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 Funcionalidades Principais
            
            - **Coleta Automatizada**: 10 anos de dados do BCB
            - **Dashboard Interativo**: Visualizações avançadas
            - **Machine Learning**: Modelos preditivos
            - **Relatórios com IA**: Análises inteligentes
            """)
        
        with col2:
            st.markdown("""
            ### 🚀 Novidades da Versão 2.0
            
            - ✅ Estrutura modular para equipes
            - ✅ Coleta robusta de 10 anos de dados
            - ✅ Relatórios automáticos com IA
            - ✅ Análise preditiva avançada
            """)
        
        # Métricas
        st.markdown("### 📈 Status do Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Indicadores", len(config.data_collection.indicators))
        with col2:
            st.metric("Modelos ML", len(config.ml.available_models))
        with col3:
            st.metric("Anos de Dados", config.data_collection.default_years)
        with col4:
            st.metric("Relatórios", len(config.reports.report_types))
        
        # Footer
        st.markdown("---")
        st.markdown("**🎓 Desenvolvido pela Squad7 - MDS 2025-1 com orientação do Scrum Master Rafael**")