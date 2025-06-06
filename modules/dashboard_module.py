# modules/dashboard_module.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import config, get_indicator_display_names
from database_manager import DatabaseManager
from utils.base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class DashboardModule(BaseModule):
    """Módulo do dashboard econômico"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.indicator_names = get_indicator_display_names()
    
    def render(self):
        st.title("📊 Dashboard Econômico - Dados do Banco Central")
        
        st.markdown("""
        Visualize e analise os principais indicadores econômicos brasileiros com gráficos interativos
        e estatísticas em tempo real.
        """)
        
        # Verificar se há dados disponíveis
        available_indicators = self._get_available_indicators()
        
        if not available_indicators:
            st.warning("⚠️ Nenhum dado encontrado. Por favor, execute a coleta de dados primeiro.")
            if st.button("🔄 Ir para Coleta de Dados"):
                st.session_state.current_page = 'data_collection'
                st.rerun()
            return
        
        # Sidebar com controles
        self._render_sidebar(available_indicators)
        
        # Conteúdo principal
        selected_indicators = st.session_state.get('selected_indicators', list(available_indicators.keys())[:3])
        time_period = st.session_state.get('time_period', 24)
        chart_type = st.session_state.get('chart_type', 'line')
        
        # Mostrar gráficos
        if selected_indicators:
            if len(selected_indicators) == 1:
                self._render_single_indicator(selected_indicators[0], time_period, chart_type)
            else:
                self._render_multiple_indicators(selected_indicators, time_period, chart_type)
            
            # Estatísticas comparativas
            self._render_statistics(selected_indicators, time_period)
        else:
            st.info("Selecione pelo menos um indicador na barra lateral.")
    
    def _get_available_indicators(self) -> dict:
        """Verifica quais indicadores têm dados disponíveis"""
        available = {}
        
        for indicator, info in config.data_collection.indicators.items():
            try:
                data = self.db_manager.load_data(indicator)
                if data is not None and not data.empty:
                    available[indicator] = info['name']
            except Exception as e:
                logger.warning(f"Erro ao verificar dados de {indicator}: {e}")
        
        return available
    
    def _render_sidebar(self, available_indicators: dict):
        """Renderiza controles da sidebar"""
        st.sidebar.subheader("⚙️ Configurações do Dashboard")
        
        # Seleção de indicadores
        selected_indicators = st.sidebar.multiselect(
            "Indicadores para visualizar",
            options=list(available_indicators.keys()),
            default=list(available_indicators.keys())[:3],
            format_func=lambda x: available_indicators.get(x, x)
        )
        st.session_state.selected_indicators = selected_indicators
        
        # Período de tempo
        time_period = st.sidebar.selectbox(
            "Período",
            options=[6, 12, 24, 36, 60],
            index=1,
            format_func=lambda x: f"Últimos {x} meses"
        )
        st.session_state.time_period = time_period
        
        # Tipo de gráfico
        chart_type = st.sidebar.selectbox(
            "Tipo de Gráfico",
            options=['line', 'area', 'bar'],
            format_func=lambda x: {'line': '📈 Linha', 'area': '📊 Área', 'bar': '📊 Barras'}[x]
        )
        st.session_state.chart_type = chart_type
        
        # Opções avançadas
        with st.sidebar.expander("🔧 Opções Avançadas"):
            show_trend = st.checkbox("Mostrar linha de tendência", value=True)
            show_stats = st.checkbox("Mostrar estatísticas", value=True)
            normalize_data = st.checkbox("Normalizar dados", value=False)
            
            st.session_state.update({
                'show_trend': show_trend,
                'show_stats': show_stats,
                'normalize_data': normalize_data
            })
    
    def _render_single_indicator(self, indicator: str, months: int, chart_type: str):
        """Renderiza visualização para um único indicador"""
        
        data = self._load_indicator_data(indicator, months)
        if data is None or data.empty:
            st.error(f"Não há dados disponíveis para {self.indicator_names.get(indicator, indicator)}")
            return
        
        st.subheader(f"📈 {self.indicator_names.get(indicator, indicator)}")
        
        # Gráfico principal
        fig = self._create_chart(data, indicator, chart_type)
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        current_value = data['value'].iloc[-1]
        previous_value = data['value'].iloc[-2] if len(data) > 1 else current_value
        change = current_value - previous_value
        change_pct = (change / previous_value * 100) if previous_value != 0 else 0
        
        with col1:
            st.metric("Valor Atual", f"{current_value:.4f}", f"{change:+.4f}")
        with col2:
            st.metric("Variação %", f"{change_pct:+.2f}%")
        with col3:
            st.metric("Máximo", f"{data['value'].max():.4f}")
        with col4:
            st.metric("Mínimo", f"{data['value'].min():.4f}")
        
        # Tabela de dados recentes
        if st.session_state.get('show_stats', True):
            with st.expander("📋 Dados Recentes"):
                recent_data = data.tail(10).sort_values('date', ascending=False)
                recent_data['date'] = recent_data['date'].dt.strftime('%d/%m/%Y')
                st.dataframe(recent_data[['date', 'value']], use_container_width=True)
    
    def _render_multiple_indicators(self, indicators: list, months: int, chart_type: str):
        """Renderiza visualização para múltiplos indicadores"""
        
        st.subheader(f"📊 Comparação de Indicadores ({len(indicators)} selecionados)")
        
        # Carregar dados de todos os indicadores
        all_data = {}
        for indicator in indicators:
            data = self._load_indicator_data(indicator, months)
            if data is not None and not data.empty:
                all_data[indicator] = data
        
        if not all_data:
            st.error("Nenhum dado disponível para os indicadores selecionados")
            return
        
        # Criar gráfico combinado
        fig = go.Figure()
        
        for indicator, data in all_data.items():
            # Normalizar dados se solicitado
            values = data['value']
            if st.session_state.get('normalize_data', False):
                values = (values - values.min()) / (values.max() - values.min())
            
            if chart_type == 'line':
                fig.add_trace(go.Scatter(
                    x=data['date'],
                    y=values,
                    name=self.indicator_names.get(indicator, indicator),
                    mode='lines'
                ))
            elif chart_type == 'area':
                fig.add_trace(go.Scatter(
                    x=data['date'],
                    y=values,
                    name=self.indicator_names.get(indicator, indicator),
                    fill='tonexty' if len(fig.data) > 0 else 'tozeroy'
                ))
        
        fig.update_layout(
            title="Evolução Comparativa dos Indicadores",
            xaxis_title="Data",
            yaxis_title="Valor" + (" (Normalizado)" if st.session_state.get('normalize_data') else ""),
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Resumo estatístico
        self._render_comparison_summary(all_data)
    
    def _render_comparison_summary(self, all_data: dict):
        """Renderiza resumo comparativo"""
        
        st.subheader("📊 Resumo Comparativo")
        
        summary_data = []
        for indicator, data in all_data.items():
            values = data['value']
            summary_data.append({
                'Indicador': self.indicator_names.get(indicator, indicator),
                'Último Valor': f"{values.iloc[-1]:.4f}",
                'Média': f"{values.mean():.4f}",
                'Desvio Padrão': f"{values.std():.4f}",
                'Mínimo': f"{values.min():.4f}",
                'Máximo': f"{values.max():.4f}",
                'Variação %': f"{((values.iloc[-1] / values.iloc[0] - 1) * 100):+.2f}%" if len(values) > 1 else "N/A"
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
    
    def _render_statistics(self, indicators: list, months: int):
        """Renderiza seção de estatísticas"""
        
        if not st.session_state.get('show_stats', True):
            return
        
        st.subheader("📈 Análise Estatística")
        
        # Carregar dados
        all_data = {}
        for indicator in indicators:
            data = self._load_indicator_data(indicator, months)
            if data is not None and not data.empty:
                all_data[indicator] = data['value']
        
        if len(all_data) < 2:
            return
        
        # Criar DataFrame combinado
        combined_df = pd.DataFrame(all_data)
        
        # Matriz de correlação
        if len(combined_df.columns) > 1:
            st.markdown("#### 🔗 Matriz de Correlação")
            
            corr_matrix = combined_df.corr()
            
            fig = px.imshow(
                corr_matrix,
                labels=dict(x="Indicador", y="Indicador", color="Correlação"),
                x=[self.indicator_names.get(col, col) for col in corr_matrix.columns],
                y=[self.indicator_names.get(col, col) for col in corr_matrix.index],
                color_continuous_scale='RdBu',
                aspect='auto'
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _load_indicator_data(self, indicator: str, months: int) -> pd.DataFrame:
        """Carrega dados de um indicador para o período especificado"""
        
        try:
            # Calcular data de início
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # Carregar dados
            data = self.db_manager.load_data(
                indicator,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if data is not None and not data.empty:
                data = data.sort_values('date')
                return data
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados de {indicator}: {e}")
        
        return None
    
    def _create_chart(self, data: pd.DataFrame, indicator: str, chart_type: str):
        """Cria gráfico para um indicador"""
        
        if chart_type == 'line':
            fig = px.line(
                data, 
                x='date', 
                y='value',
                title=f'Evolução de {self.indicator_names.get(indicator, indicator)}',
                labels={'date': 'Data', 'value': 'Valor'}
            )
        elif chart_type == 'area':
            fig = px.area(
                data, 
                x='date', 
                y='value',
                title=f'Evolução de {self.indicator_names.get(indicator, indicator)}',
                labels={'date': 'Data', 'value': 'Valor'}
            )
        else:  # bar
            fig = px.bar(
                data.tail(20), 
                x='date', 
                y='value',
                title=f'Últimos 20 valores - {self.indicator_names.get(indicator, indicator)}',
                labels={'date': 'Data', 'value': 'Valor'}
            )
        
        # Adicionar linha de tendência se solicitado
        if st.session_state.get('show_trend', True) and chart_type in ['line', 'area']:
            fig.add_trace(
                px.scatter(data, x='date', y='value', trendline='ols').data[1]
            )
        
        fig.update_layout(height=400)
        return fig