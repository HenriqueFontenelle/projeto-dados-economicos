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
        e estatísticas em tempo real. **Agora com suporte a até 10 anos de dados históricos!**
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
        
        # ✅ CONVERTER time_period para months (0 = todo período)
        months = time_period if time_period > 0 else 0
        
        # Mostrar gráficos
        if selected_indicators:
            if len(selected_indicators) == 1:
                self._render_single_indicator(selected_indicators[0], months, chart_type)
            else:
                self._render_multiple_indicators(selected_indicators, months, chart_type)
            
            # Estatísticas comparativas
            self._render_statistics(selected_indicators, months)
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
        
        # ✅ PERÍODO DE TEMPO EXPANDIDO PARA 10 ANOS
        period_options = {
            3: "Últimos 3 meses",
            6: "Últimos 6 meses", 
            12: "Último ano",
            24: "Últimos 2 anos",
            36: "Últimos 3 anos",
            60: "Últimos 5 anos",
            120: "Últimos 10 anos",
            0: "Todo o período disponível"  # Opção para todos os dados
        }
        
        time_period = st.sidebar.selectbox(
            "Período",
            options=list(period_options.keys()),
            index=3,  # Padrão: 2 anos
            format_func=lambda x: period_options[x]
        )
        st.session_state.time_period = time_period
        
        # Tipo de gráfico
        chart_type = st.sidebar.selectbox(
            "Tipo de Gráfico",
            options=['line', 'area', 'bar'],
            format_func=lambda x: {'line': '📈 Linha', 'area': '📊 Área', 'bar': '📊 Barras'}[x]
        )
        st.session_state.chart_type = chart_type
        
        # ✅ OPÇÕES AVANÇADAS MELHORADAS
        with st.sidebar.expander("🔧 Opções Avançadas"):
            show_trend = st.checkbox("Mostrar linha de tendência", value=True)
            show_stats = st.checkbox("Mostrar estatísticas", value=True)
            normalize_data = st.checkbox("Normalizar dados", value=False)
            
            # ✅ NOVA OPÇÃO: Agregação para períodos longos
            if time_period >= 60:  # Para períodos de 5+ anos
                aggregation = st.selectbox(
                    "Agregação de dados",
                    options=['none', 'monthly', 'quarterly', 'yearly'],
                    index=1,  # Padrão: mensal
                    format_func=lambda x: {
                        'none': 'Todos os pontos',
                        'monthly': 'Média mensal',
                        'quarterly': 'Média trimestral', 
                        'yearly': 'Média anual'
                    }[x]
                )
            else:
                aggregation = 'none'
            
            st.session_state.update({
                'show_trend': show_trend,
                'show_stats': show_stats,
                'normalize_data': normalize_data,
                'aggregation': aggregation
            })
    
    def _render_single_indicator(self, indicator: str, months: int, chart_type: str):
        """Renderiza visualização para um único indicador"""
        
        data = self._load_indicator_data(indicator, months)
        if data is None or data.empty:
            st.error(f"Não há dados disponíveis para {self.indicator_names.get(indicator, indicator)}")
            return
        
        # ✅ MOSTRAR INFORMAÇÕES DO PERÍODO
        period_info = self._get_period_info(data, months)
        st.subheader(f"📈 {self.indicator_names.get(indicator, indicator)} - {period_info}")
        
        # ✅ ADICIONAR INFO SOBRE AGREGAÇÃO
        aggregation = st.session_state.get('aggregation', 'none')
        if aggregation != 'none':
            st.info(f"ℹ️ Dados agregados por {aggregation} para melhor visualização")
        
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
        
        # ✅ ADICIONAR ESTATÍSTICAS HISTÓRICAS PARA PERÍODOS LONGOS
        if months >= 60:  # Para 5+ anos, mostrar análise histórica
            self._render_historical_analysis(data, indicator)
        
        # Tabela de dados recentes
        if st.session_state.get('show_stats', True):
            with st.expander("📋 Dados Recentes"):
                recent_data = data.tail(10).sort_values('date', ascending=False)
                recent_data['date'] = recent_data['date'].dt.strftime('%d/%m/%Y')
                st.dataframe(recent_data[['date', 'value']], use_container_width=True)


    def _get_period_info(self, data: pd.DataFrame, months: int) -> str:
        """Retorna informação sobre o período dos dados"""
        
        if months == 0:
            return "Todo o período disponível"
        
        start_date = data['date'].min().strftime('%m/%Y')
        end_date = data['date'].max().strftime('%m/%Y')
        total_points = len(data)
        
        return f"{start_date} a {end_date} ({total_points} pontos)"

    def _render_historical_analysis(self, data: pd.DataFrame, indicator: str):
        """Renderiza análise histórica para períodos longos"""
        
        st.markdown("#### 📊 Análise Histórica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Estatísticas por ano
            data_yearly = data.copy()
            data_yearly['year'] = data_yearly['date'].dt.year
            yearly_stats = data_yearly.groupby('year')['value'].agg([
                'mean', 'min', 'max', 'std'
            ]).round(4)
            
            st.markdown("**📅 Estatísticas Anuais:**")
            st.dataframe(yearly_stats, use_container_width=True)
        
        with col2:
            # Volatilidade por período
            data_monthly = data.copy()
            data_monthly['month'] = data_monthly['date'].dt.to_period('M')
            monthly_vol = data_monthly.groupby('month')['value'].std()
            
            avg_volatility = monthly_vol.mean()
            max_volatility = monthly_vol.max()
            
            st.markdown("**📈 Análise de Volatilidade:**")
            st.metric("Volatilidade Média", f"{avg_volatility:.4f}")
            st.metric("Volatilidade Máxima", f"{max_volatility:.4f}")
            
            # Período de maior/menor valor
            max_idx = data['value'].idxmax()
            min_idx = data['value'].idxmin()
            
            st.markdown("**🏆 Extremos Históricos:**")
            st.write(f"Maior valor: {data.loc[max_idx, 'value']:.4f} em {data.loc[max_idx, 'date'].strftime('%m/%Y')}")
            st.write(f"Menor valor: {data.loc[min_idx, 'value']:.4f} em {data.loc[min_idx, 'date'].strftime('%m/%Y')}")


    
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
            # ✅ CARREGAR TODOS OS DADOS SE months = 0
            if months == 0:
                # Carregar todo o período disponível
                data = self.db_manager.load_data(indicator)
            else:
                # Carregar período específico
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30 * months)
                
                data = self.db_manager.load_data(
                    indicator,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            
            if data is not None and not data.empty:
                # Garantir que a coluna date seja datetime
                data['date'] = pd.to_datetime(data['date'])
                data = data.sort_values('date')
                
                # ✅ APLICAR AGREGAÇÃO SE NECESSÁRIO
                aggregation = st.session_state.get('aggregation', 'none')
                if aggregation != 'none':
                    data = self._aggregate_data(data, aggregation)
                
                return data
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados de {indicator}: {e}")
            st.error(f"🐛 Debug: Erro ao carregar {indicator}: {e}")
        
        return None
    

    def _aggregate_data(self, data: pd.DataFrame, aggregation: str) -> pd.DataFrame:
        """Agrega dados por período para facilitar visualização de séries longas"""
        
        if data is None or data.empty:
            return data
        
        try:
            # Definir frequência de agregação
            freq_map = {
                'monthly': 'M',
                'quarterly': 'Q', 
                'yearly': 'Y'
            }
            
            freq = freq_map.get(aggregation, 'M')
            
            # Configurar data como índice
            data_copy = data.copy()
            data_copy.set_index('date', inplace=True)
            
            # Agregar por média
            aggregated = data_copy.resample(freq)['value'].agg([
                ('value', 'mean'),
                ('min_value', 'min'),
                ('max_value', 'max'),
                ('count', 'count')
            ]).reset_index()
            
            # Manter apenas registros com dados suficientes
            aggregated = aggregated[aggregated['count'] > 0]
            
            # Retornar formato original
            result = aggregated[['date', 'value']].copy()
            result['aggregation'] = aggregation
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na agregação: {e}")
            return data
    
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