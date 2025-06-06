# modules/ml_module.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import joblib
from config import config, get_indicator_display_names
from database_manager import DatabaseManager
from ml_models import EconomicPredictor
from utils.base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class MLModule(BaseModule):
    """Módulo de Machine Learning para previsões econômicas"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.predictor = EconomicPredictor()
        self.indicator_names = get_indicator_display_names()
        self.models_dir = config.ml.models_dir
    
    def render(self):
        st.title("🤖 Machine Learning - Previsões Econômicas")
        
        st.markdown("""
        Utilize algoritmos de Machine Learning para criar modelos preditivos dos indicadores econômicos.
        **Novidade v2.0**: Agora com 7 tipos de modelos e análise avançada de features!
        """)
        
        # Verificar dados disponíveis
        available_indicators = self._get_available_indicators()
        
        if not available_indicators:
            st.warning("⚠️ Nenhum dado encontrado. Execute a coleta de dados primeiro.")
            if st.button("🔄 Ir para Coleta de Dados"):
                st.session_state.current_page = 'data_collection'
                st.rerun()
            return
        
        # Tabs para organizar funcionalidades
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Treinamento", 
            "📈 Previsões", 
            "🔍 Análise do Modelo", 
            "📊 Dados Históricos"
        ])
        
        with tab1:
            self._render_training_tab(available_indicators)
        
        with tab2:
            self._render_prediction_tab(available_indicators)
        
        with tab3:
            self._render_analysis_tab(available_indicators)
        
        with tab4:
            self._render_data_tab(available_indicators)
    
    def _get_available_indicators(self) -> dict:
        """Verifica indicadores com dados suficientes para ML"""
        available = {}
        
        for indicator, info in config.data_collection.indicators.items():
            try:
                data = self.db_manager.load_data(indicator)
                if data is not None and len(data) >= config.ml.min_data_points:
                    available[indicator] = info['name']
            except Exception as e:
                logger.warning(f"Erro ao verificar dados de {indicator}: {e}")
        
        return available
    
    def _render_training_tab(self, available_indicators: dict):
        """Tab de treinamento de modelos"""
        
        st.subheader("🎯 Treinamento de Modelos")
        
        # Configurações de treinamento
        col1, col2 = st.columns(2)
        
        with col1:
            selected_indicator = st.selectbox(
                "Indicador para treinar",
                options=list(available_indicators.keys()),
                format_func=lambda x: available_indicators[x],
                help="Escolha o indicador para criar modelo preditivo"
            )
        
        with col2:
            model_type = st.selectbox(
                "Algoritmo de ML",
                options=config.ml.available_models,
                format_func=self._format_model_name,
                help="Tipo de algoritmo para treinamento"
            )
        
        # Configurações avançadas
        with st.expander("⚙️ Configurações Avançadas"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                test_size = st.slider(
                    "Tamanho do conjunto de teste",
                    min_value=0.1,
                    max_value=0.4,
                    value=config.ml.default_test_size,
                    step=0.05,
                    help="Proporção dos dados para teste"
                )
            
            with col2:
                window_size = st.slider(
                    "Janela de features (lags)",
                    min_value=1,
                    max_value=config.ml.max_lag_periods,
                    value=6,
                    help="Quantos períodos passados usar como features"
                )
            
            with col3:
                cross_validation = st.checkbox(
                    "Validação cruzada",
                    value=True,
                    help="Usar validação cruzada temporal"
                )
        
        # Status do modelo atual
        self._show_model_status(selected_indicator, model_type)
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            train_button = st.button(
                "🚀 Treinar Modelo",
                use_container_width=True,
                help="Treinar novo modelo com configurações atuais"
            )
        
        with col2:
            retrain_button = st.button(
                "🔄 Retreinar",
                use_container_width=True,
                help="Retreinar modelo existente"
            )
        
        with col3:
            compare_button = st.button(
                "⚖️ Comparar Modelos",
                use_container_width=True,
                help="Comparar diferentes algoritmos"
            )
        
        # Executar ações
        if train_button:
            self._train_model(selected_indicator, model_type, test_size, window_size, cross_validation)
        
        elif retrain_button:
            self._train_model(selected_indicator, model_type, test_size, window_size, cross_validation, retrain=True)
        
        elif compare_button:
            self._compare_models(selected_indicator, test_size, window_size)
    
    def _render_prediction_tab(self, available_indicators: dict):
        """Tab de previsões"""
        
        st.subheader("📈 Geração de Previsões")
        
        # Seleção de modelo
        col1, col2 = st.columns(2)
        
        with col1:
            indicator = st.selectbox(
                "Indicador",
                options=list(available_indicators.keys()),
                format_func=lambda x: available_indicators[x],
                key="pred_indicator"
            )
        
        with col2:
            forecast_periods = st.slider(
                "Períodos para prever",
                min_value=1,
                max_value=24,
                value=6,
                help="Quantos meses prever no futuro"
            )
        
        # Verificar se há modelo treinado
        model_exists = self._check_model_exists(indicator)
        
        if not model_exists:
            st.warning(f"⚠️ Nenhum modelo treinado encontrado para {available_indicators[indicator]}")
            st.info("💡 Vá para a aba 'Treinamento' para criar um modelo primeiro.")
            return
        
        # Configurações de previsão
        with st.expander("🔧 Opções de Previsão"):
            show_confidence = st.checkbox("Mostrar intervalo de confiança", value=True)
            show_historical = st.slider("Meses históricos para comparação", 6, 24, 12)
        
        # Botão para gerar previsão
        if st.button("🎯 Gerar Previsão", use_container_width=True):
            self._generate_prediction(indicator, forecast_periods, show_confidence, show_historical)
    
    def _render_analysis_tab(self, available_indicators: dict):
        """Tab de análise de modelos"""
        
        st.subheader("🔍 Análise de Modelos")
        
        # Seleção de modelo para análise
        indicator = st.selectbox(
            "Modelo para analisar",
            options=list(available_indicators.keys()),
            format_func=lambda x: available_indicators[x],
            key="analysis_indicator"
        )
        
        if not self._check_model_exists(indicator):
            st.warning(f"⚠️ Nenhum modelo treinado para {available_indicators[indicator]}")
            return
        
        # Análises disponíveis
        analysis_type = st.radio(
            "Tipo de análise",
            options=[
                "feature_importance",
                "model_performance",
                "prediction_intervals",
                "residual_analysis"
            ],
            format_func=self._format_analysis_type,
            horizontal=True
        )
        
        # Executar análise selecionada
        if analysis_type == "feature_importance":
            self._show_feature_importance(indicator)
        elif analysis_type == "model_performance":
            self._show_model_performance(indicator)
        elif analysis_type == "prediction_intervals":
            self._show_prediction_intervals(indicator)
        elif analysis_type == "residual_analysis":
            self._show_residual_analysis(indicator)
    
    def _render_data_tab(self, available_indicators: dict):
        """Tab de dados históricos"""
        
        st.subheader("📊 Dados Históricos")
        
        # Seleção de indicador
        indicator = st.selectbox(
            "Indicador para visualizar",
            options=list(available_indicators.keys()),
            format_func=lambda x: available_indicators[x],
            key="data_indicator"
        )
        
        # Carregar dados
        data = self.db_manager.load_data(indicator)
        
        if data is None or data.empty:
            st.error("❌ Não foi possível carregar dados")
            return
        
        # Informações básicas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Registros", len(data))
        with col2:
            st.metric("Período", f"{(data['date'].max() - data['date'].min()).days} dias")
        with col3:
            st.metric("Último Valor", f"{data['value'].iloc[-1]:.4f}")
        with col4:
            st.metric("Média", f"{data['value'].mean():.4f}")
        
        # Análise temporal
        self._show_temporal_analysis(data, indicator)
        
        # Estatísticas descritivas
        with st.expander("📊 Estatísticas Descritivas"):
            st.dataframe(data['value'].describe())
        
        # Download de dados
        csv = data.to_csv(index=False)
        st.download_button(
            "📥 Baixar Dados (CSV)",
            csv,
            f"{indicator}_dados.csv",
            "text/csv"
        )
    
    def _show_model_status(self, indicator: str, model_type: str):
        """Mostra status do modelo atual"""
        
        model_path = f"{self.models_dir}/{indicator}_{model_type}_model.pkl"
        
        if os.path.exists(model_path):
            # Modelo existe
            mod_time = datetime.fromtimestamp(os.path.getmtime(model_path))
            st.success(f"✅ Modelo existente: treinado em {mod_time.strftime('%d/%m/%Y %H:%M')}")
            
            # Tentar carregar métricas
            try:
                metrics_path = f"{self.models_dir}/{indicator}_{model_type}_metrics.pkl"
                if os.path.exists(metrics_path):
                    metrics = joblib.load(metrics_path)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("R²", f"{metrics.get('r2', 0):.3f}")
                    with col2:
                        st.metric("RMSE", f"{metrics.get('rmse', 0):.4f}")
                    with col3:
                        st.metric("MAE", f"{metrics.get('mae', 0):.4f}")
                    with col4:
                        st.metric("MSE", f"{metrics.get('mse', 0):.6f}")
            except:
                pass
        else:
            st.info(f"ℹ️ Nenhum modelo {self._format_model_name(model_type)} encontrado para {self.indicator_names[indicator]}")
    
    def _train_model(self, indicator: str, model_type: str, test_size: float, window_size: int, cross_validation: bool, retrain: bool = False):
        """Treina modelo de ML"""
        
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Preparando dados para treinamento...")
                progress_bar.progress(0.1)
                
                # Verificar dados suficientes
                data = self.db_manager.load_data(indicator)
                if data is None or len(data) < config.ml.min_data_points:
                    st.error(f"❌ Dados insuficientes. Mínimo: {config.ml.min_data_points} registros")
                    return
                
                status_text.text("🤖 Treinando modelo de Machine Learning...")
                progress_bar.progress(0.3)
                
                # Treinar modelo
                metrics = self.predictor.train_model(
                    target_indicator=indicator,
                    model_type=model_type,
                    test_size=test_size
                )
                
                progress_bar.progress(0.8)
                
                if metrics:
                    # Salvar métricas
                    metrics_path = f"{self.models_dir}/{indicator}_{model_type}_metrics.pkl"
                    joblib.dump(metrics, metrics_path)
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Modelo treinado com sucesso!")
                    
                    # Mostrar resultados
                    st.success("🎉 Treinamento concluído!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("R² Score", f"{metrics['r2']:.4f}")
                    with col2:
                        st.metric("RMSE", f"{metrics['rmse']:.4f}")
                    with col3:
                        st.metric("MAE", f"{metrics['mae']:.4f}")
                    with col4:
                        st.metric("MSE", f"{metrics['mse']:.6f}")
                    
                    # Mostrar gráfico de predição vs real
                    prediction_plot_path = f"{self.models_dir}/{indicator}_prediction.png"
                    if os.path.exists(prediction_plot_path):
                        st.image(prediction_plot_path, caption="Previsão vs Valores Reais")
                
                else:
                    st.error("❌ Falha no treinamento do modelo")
                
            except Exception as e:
                st.error(f"❌ Erro durante treinamento: {e}")
                logger.error(f"Erro no treinamento: {e}", exc_info=True)
    
    def _generate_prediction(self, indicator: str, periods: int, show_confidence: bool, historical_months: int):
        """Gera previsões futuras"""
        
        try:
            with st.spinner("🔮 Gerando previsões..."):
                
                # Gerar previsão
                prediction = self.predictor.predict_future(indicator, steps=periods)
                
                if prediction is None:
                    st.error("❌ Falha ao gerar previsão")
                    return
                
                # Carregar dados históricos
                historical_data = self.db_manager.load_data(indicator)
                
                if historical_data is not None:
                    # Últimos N meses para comparação
                    cutoff_date = datetime.now() - timedelta(days=30 * historical_months)
                    recent_data = historical_data[historical_data['date'] >= cutoff_date].sort_values('date')
                    
                    # Criar gráfico
                    fig = go.Figure()
                    
                    # Dados históricos
                    fig.add_trace(go.Scatter(
                        x=recent_data['date'],
                        y=recent_data['value'],
                        mode='lines',
                        name='Histórico',
                        line=dict(color='blue')
                    ))
                    
                    # Previsões
                    fig.add_trace(go.Scatter(
                        x=prediction['date'],
                        y=prediction['value'],
                        mode='lines+markers',
                        name='Previsão',
                        line=dict(color='red', dash='dash')
                    ))
                    
                    # Intervalo de confiança (simplificado)
                    if show_confidence:
                        std_dev = recent_data['value'].std() * 0.5
                        upper_bound = prediction['value'] + std_dev
                        lower_bound = prediction['value'] - std_dev
                        
                        fig.add_trace(go.Scatter(
                            x=prediction['date'].tolist() + prediction['date'].iloc[::-1].tolist(),
                            y=upper_bound.tolist() + lower_bound.iloc[::-1].tolist(),
                            fill='toself',
                            fillcolor='rgba(255,0,0,0.2)',
                            line=dict(color='rgba(255,0,0,0)'),
                            name='Intervalo de Confiança'
                        ))
                    
                    fig.update_layout(
                        title=f'Previsão de {self.indicator_names[indicator]} - Próximos {periods} meses',
                        xaxis_title='Data',
                        yaxis_title='Valor',
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabela de previsões
                    st.subheader("📋 Valores Previstos")
                    display_pred = prediction.copy()
                    display_pred['date'] = display_pred['date'].dt.strftime('%d/%m/%Y')
                    st.dataframe(display_pred, use_container_width=True)
                    
                    # Análise de tendência
                    trend = "ascendente" if prediction['value'].iloc[-1] > prediction['value'].iloc[0] else "descendente"
                    variation = ((prediction['value'].iloc[-1] / prediction['value'].iloc[0]) - 1) * 100
                    
                    if trend == "ascendente":
                        st.success(f"📈 Tendência ascendente: +{variation:.2f}% no período")
                    else:
                        st.error(f"📉 Tendência descendente: {variation:.2f}% no período")
                
        except Exception as e:
            st.error(f"❌ Erro ao gerar previsão: {e}")
            logger.error(f"Erro na previsão: {e}", exc_info=True)
    
    def _show_feature_importance(self, indicator: str):
        """Mostra importância das features"""
        
        try:
            importance = self.predictor.get_feature_importance(indicator)
            
            if importance is not None:
                st.subheader("🎯 Importância das Features")
                
                # Gráfico de importância
                if 'importance' in importance.columns:
                    fig = px.bar(
                        importance.head(15),
                        x='importance',
                        y='feature',
                        orientation='h',
                        title='Top 15 Features Mais Importantes'
                    )
                else:
                    fig = px.bar(
                        importance.head(15),
                        x='coefficient',
                        y='feature',
                        orientation='h',
                        title='Coeficientes do Modelo'
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela completa
                with st.expander("📊 Tabela Completa"):
                    st.dataframe(importance)
            else:
                st.warning("⚠️ Não foi possível calcular importância das features")
                
        except Exception as e:
            st.error(f"❌ Erro ao analisar features: {e}")
    
    def _show_temporal_analysis(self, data: pd.DataFrame, indicator: str):
        """Mostra análise temporal dos dados"""
        
        # Gráfico principal
        fig = px.line(
            data,
            x='date',
            y='value',
            title=f'Série Temporal - {self.indicator_names[indicator]}'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise de decomposição (simplificada)
        if len(data) >= 24:
            st.subheader("📈 Análise de Tendência")
            
            # Médias móveis
            data['MA_3m'] = data['value'].rolling(window=3).mean()
            data['MA_6m'] = data['value'].rolling(window=6).mean()
            data['MA_12m'] = data['value'].rolling(window=12).mean()
            
            fig_ma = go.Figure()
            
            fig_ma.add_trace(go.Scatter(x=data['date'], y=data['value'], name='Original', opacity=0.7))
            fig_ma.add_trace(go.Scatter(x=data['date'], y=data['MA_3m'], name='Média 3m'))
            fig_ma.add_trace(go.Scatter(x=data['date'], y=data['MA_6m'], name='Média 6m'))
            fig_ma.add_trace(go.Scatter(x=data['date'], y=data['MA_12m'], name='Média 12m'))
            
            fig_ma.update_layout(title='Médias Móveis')
            st.plotly_chart(fig_ma, use_container_width=True)
    
    def _format_model_name(self, model_type: str) -> str:
        """Formata nome do modelo para exibição"""
        mapping = {
            'linear_regression': '📈 Regressão Linear',
            'ridge_regression': '🔵 Ridge Regression',
            'lasso_regression': '🔴 Lasso Regression',
            'random_forest': '🌲 Random Forest',
            'gradient_boosting': '⚡ Gradient Boosting',
            'xgboost': '🚀 XGBoost',
            'lstm': '🧠 LSTM Neural Network'
        }
        return mapping.get(model_type, model_type.title())
    
    def _format_analysis_type(self, analysis_type: str) -> str:
        """Formata tipo de análise para exibição"""
        mapping = {
            'feature_importance': '🎯 Importância Features',
            'model_performance': '📊 Performance',
            'prediction_intervals': '📈 Intervalos',
            'residual_analysis': '🔍 Resíduos'
        }
        return mapping.get(analysis_type, analysis_type.title())
    
    def _check_model_exists(self, indicator: str) -> bool:
        """Verifica se existe modelo treinado"""
        for model_type in config.ml.available_models:
            model_path = f"{self.models_dir}/{indicator}_{model_type}_model.pkl"
            if os.path.exists(model_path):
                return True
        return False
    
    def _compare_models(self, indicator: str, test_size: float, window_size: int):
        """Compara diferentes modelos"""
        st.info("🔄 Funcionalidade de comparação será implementada em breve...")
    
    def _show_model_performance(self, indicator: str):
        """Mostra performance do modelo"""
        st.info("📊 Análise de performance detalhada será implementada em breve...")
    
    def _show_prediction_intervals(self, indicator: str):
        """Mostra intervalos de predição"""
        st.info("📈 Análise de intervalos será implementada em breve...")
    
    def _show_residual_analysis(self, indicator: str):
        """Mostra análise de resíduos"""
        st.info("🔍 Análise de resíduos será implementada em breve...")