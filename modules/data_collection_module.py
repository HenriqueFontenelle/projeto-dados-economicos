# modules/data_collection_module.py
import streamlit as st
from datetime import datetime
from data_collector import BCBDataCollector
from database_manager import DatabaseManager
from config import config, get_indicator_display_names
from utils.base_module import BaseModule
import logging

logger = logging.getLogger(__name__)

class DataCollectionModule(BaseModule):
    """Módulo para coleta de dados do BCB"""
    
    def render(self):
        st.title("📥 Coleta de Dados do Banco Central")
        
        st.markdown("""
        Este módulo permite coletar dados econômicos diretamente das APIs oficiais do Banco Central do Brasil.
        **Novidade**: Agora com coleta robusta de até **10 anos** de dados históricos!
        """)
        
        # Status da API
        self._show_api_status()
        
        # Configurações de coleta
        st.subheader("⚙️ Configurações de Coleta")
        
        col1, col2 = st.columns(2)
        
        with col1:
            years_to_collect = st.slider(
                "Anos de dados para coletar",
                min_value=1,
                max_value=15,
                value=config.data_collection.default_years,
                help="Quantos anos retroativos coletar (padrão: 10 anos)"
            )
        
        with col2:
            all_indicators = list(config.data_collection.indicators.keys())
            indicator_names = get_indicator_display_names()
            
            selected_indicators = st.multiselect(
                "Indicadores para coletar",
                options=all_indicators,
                default=all_indicators[:7],  # Primeiros 7 por padrão
                format_func=lambda x: indicator_names.get(x, x),
                help="Selecione quais indicadores coletar"
            )
        
        # Informações sobre os indicadores
        with st.expander("ℹ️ Informações dos Indicadores"):
            self._show_indicators_info(all_indicators)
        
        # Botões de ação
        st.markdown("### 🚀 Executar Coleta")
        
        button_col1, button_col2, button_col3 = st.columns(3)
        
        with button_col1:
            collect_all = st.button(
                "🔄 Coletar Todos",
                help="Coleta todos os indicadores selecionados",
                use_container_width=True
            )
        
        with button_col2:
            quick_update = st.button(
                "⚡ Atualização Rápida",
                help="Coleta apenas últimos 6 meses",
                use_container_width=True
            )
        
        with button_col3:
            test_api = st.button(
                "🔍 Testar API",
                help="Testa conectividade com API do BCB",
                use_container_width=True
            )
        
        # Executar ações
        if collect_all and selected_indicators:
            self._execute_collection(selected_indicators, years_to_collect)
        
        elif quick_update and selected_indicators:
            self._execute_collection(selected_indicators, 0.5)  # 6 meses
        
        elif test_api:
            self._test_api_connection()
        
        # Mostrar histórico de coletas
        self._show_collection_history()
    
    def _show_api_status(self):
        """Mostra status da API do BCB"""
        st.subheader("🌐 Status da Conexão")
        
        with st.container():
            try:
                collector = BCBDataCollector()
                api_ok = collector.check_api_status()
                
                if api_ok:
                    st.success("🟢 API do Banco Central está online e respondendo")
                    
                    # Mostrar estatísticas da última verificação
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", "Online", "✅")
                    with col2:
                        st.metric("Indicadores", len(config.data_collection.indicators))
                    with col3:
                        st.metric("Timeout", f"{config.data_collection.request_timeout}s")
                        
                else:
                    st.error("🔴 API do Banco Central não está respondendo")
                    st.warning("⚠️ Verifique sua conexão com a internet ou tente novamente em alguns minutos.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao verificar API: {e}")
    
    def _show_indicators_info(self, indicators: list):
        """Mostra informações detalhadas dos indicadores"""
        
        for indicator in indicators:
            info = config.data_collection.indicators.get(indicator, {})
            
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{info.get('name', indicator)}**")
                    st.caption(info.get('description', 'Sem descrição'))
                
                with col2:
                    st.write(f"**Unidade:** {info.get('unit', 'N/A')}")
                
                with col3:
                    st.write(f"**Frequência:** {info.get('frequency', 'N/A')}")
                
                st.markdown("---")
    
    def _execute_collection(self, indicators: list, years: float):
        """Executa coleta de dados"""
        
        # Container para progresso
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                collector = BCBDataCollector()
                db_manager = DatabaseManager()
                
                total_indicators = len(indicators)
                
                status_text.text("🔄 Iniciando coleta de dados...")
                
                # Verificar API antes de começar
                if not collector.check_api_status():
                    st.error("❌ API do BCB não está respondendo. Cancelando coleta.")
                    return
                
                progress_bar.progress(0.1)
                status_text.text("📊 Coletando dados dos indicadores...")
                
                # Coletar dados
                data_results = collector.collect_all_data(
                    last_n_years=int(years) if years >= 1 else None,
                    indicators=indicators
                )
                
                progress_bar.progress(0.7)
                status_text.text("💾 Salvando dados no banco...")
                
                # Salvar no banco
                saved_results = {}
                for i, (indicator, df) in enumerate(data_results.items()):
                    if df is not None and not df.empty:  # ✅ Verificação adicional
                        success = db_manager.save_data(indicator, df)  # ✅ ORDEM CORRETA
                        saved_results[indicator] = success
                    else:
                        saved_results[indicator] = False  # ✅ Marcar como falha
                    
                    progress_bar.progress(0.7 + (0.3 * (i + 1) / len(data_results)))
                
                progress_bar.progress(1.0)
                status_text.text("✅ Coleta concluída com sucesso!")
                
                # Mostrar resultados
                self._show_collection_results(data_results, saved_results, collector.get_collection_stats())
                
                # Atualizar sessão
                st.session_state.last_data_update = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Limpar progresso após 3 segundos
                import time
                time.sleep(2)
                progress_container.empty()
                
            except Exception as e:
                st.error(f"❌ Erro durante coleta: {e}")
                logger.error(f"Erro na coleta de dados: {e}", exc_info=True)
                
                # Mostrar sugestões de solução
                with st.expander("💡 Possíveis soluções"):
                    st.markdown("""
                    - Verifique sua conexão com a internet
                    - Tente com menos indicadores
                    - Reduza o período de coleta
                    - Aguarde alguns minutos e tente novamente
                    """)
    
    def _show_collection_results(self, data_results: dict, saved_results: dict, stats: dict):
        """Mostra resultados da coleta"""
        
        st.subheader("📊 Resultados da Coleta")
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Indicadores Coletados", len(data_results))
        with col2:
            st.metric("Total de Registros", stats.get('total_records', 0))
        with col3:
            success_requests = stats.get('successful_requests', 0)
            total_requests = stats.get('total_requests', 1)
            success_rate = (success_requests / total_requests) * 100
            st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
        with col4:
            success_count = sum(1 for v in saved_results.values() if v)
            st.metric("Salvos no Banco", f"{success_count}/{len(saved_results)}")
        
        # Alerta se houve problemas
        failed_indicators = [k for k, v in saved_results.items() if not v]
        if failed_indicators:
            st.warning(f"⚠️ {len(failed_indicators)} indicadores falharam ao salvar: {', '.join(failed_indicators)}")
        
        # Detalhes por indicador
        st.markdown("#### 📋 Detalhes por Indicador")
        
        indicator_names = get_indicator_display_names()
        
        for indicator, df in data_results.items():
            with st.expander(f"{indicator_names.get(indicator, indicator)} ({indicator})"):
                if df is not None and not df.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**📊 Estatísticas:**")
                        st.write(f"• Registros coletados: {len(df)}")
                        st.write(f"• Período: {df['date'].min().strftime('%d/%m/%Y')} a {df['date'].max().strftime('%d/%m/%Y')}")
                        st.write(f"• Valores válidos: {df['value'].notna().sum()}")
                        
                        if df['value'].notna().sum() > 0:
                            st.write(f"• Último valor: {df['value'].iloc[-1]:.4f}")
                            st.write(f"• Média do período: {df['value'].mean():.4f}")
                    
                    with col2:
                        st.write("**💾 Status do Banco:**")
                        if saved_results.get(indicator, False):
                            st.success("✅ Salvo com sucesso")
                        else:
                            st.error("❌ Erro ao salvar")
                        
                        # Informações do indicador
                        info = config.data_collection.indicators.get(indicator, {})
                        st.write(f"• Unidade: {info.get('unit', 'N/A')}")
                        st.write(f"• Frequência: {info.get('frequency', 'N/A')}")
                    
                    # Prévia dos dados
                    st.write("**👀 Últimos 5 registros:**")
                    preview_data = df.tail().sort_values('date', ascending=False).copy()
                    preview_data['date'] = preview_data['date'].dt.strftime('%d/%m/%Y')
                    st.dataframe(preview_data[['date', 'value']], use_container_width=True)
                    
                else:
                    st.error("❌ Nenhum dado coletado")
                    st.info("💡 Verifique se o indicador está disponível na API do BCB")
    
    def _test_api_connection(self):
        """Testa conexão com API"""
        
        test_container = st.container()
        
        with test_container:
            with st.spinner("🔍 Testando conexão com API do BCB..."):
                try:
                    collector = BCBDataCollector()
                    
                    # Teste básico de status
                    api_ok = collector.check_api_status()
                    
                    if api_ok:
                        st.success("✅ API está respondendo normalmente")
                        
                        # Teste de coleta de amostra
                        st.info("🧪 Testando coleta de dados de amostra...")
                        
                        sample_data = collector.get_data('ipca', '01/01/2024', '31/01/2024')
                        
                        if sample_data is not None and not sample_data.empty:
                            st.success(f"✅ Teste de coleta bem-sucedido: {len(sample_data)} registros obtidos")
                            
                            # Mostrar amostra
                            with st.expander("👀 Dados de teste coletados"):
                                st.dataframe(sample_data.head())
                        else:
                            st.warning("⚠️ API responde mas não retornou dados de teste")
                            st.info("💡 Isso pode ser normal se não houver dados para o período testado")
                        
                        # Teste de múltiplos indicadores
                        st.info("🔄 Testando coleta de múltiplos indicadores...")
                        
                        test_indicators = ['ipca', 'selic']
                        test_results = collector.collect_indicator_batch(
                            test_indicators, 
                            '01/01/2024', 
                            '31/01/2024'
                        )
                        
                        success_count = len([k for k, v in test_results.items() if v is not None])
                        st.success(f"✅ Teste de múltiplos indicadores: {success_count}/{len(test_indicators)} bem-sucedidos")
                        
                    else:
                        st.error("❌ API não está respondendo")
                        st.warning("⚠️ Possíveis causas:")
                        st.markdown("""
                        - Problemas temporários na API do BCB
                        - Conexão com internet instável
                        - Firewall bloqueando requisições
                        """)
                        
                except Exception as e:
                    st.error(f"❌ Erro no teste: {e}")
                    logger.error(f"Erro no teste de API: {e}", exc_info=True)
    
    def _show_collection_history(self):
        """Mostra histórico de coletas anteriores"""
        
        st.subheader("📋 Histórico de Coletas")
        
        # Informações da sessão atual
        last_update = st.session_state.get('last_data_update', 'Nenhuma coleta realizada nesta sessão')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Última atualização:** {last_update}")
        
        with col2:
            # Verificar dados no banco
            try:
                db_manager = DatabaseManager()
                
                # Contar registros por indicador
                indicator_counts = {}
                for indicator in config.data_collection.indicators.keys():
                    try:
                        data = db_manager.load_data(indicator)
                        if data is not None:
                            indicator_counts[indicator] = len(data)
                    except:
                        indicator_counts[indicator] = 0
                
                total_records = sum(indicator_counts.values())
                indicators_with_data = len([k for k, v in indicator_counts.items() if v > 0])
                
                st.metric("Total de Registros no Banco", total_records)
                st.metric("Indicadores com Dados", f"{indicators_with_data}/{len(config.data_collection.indicators)}")
                
            except Exception as e:
                st.warning(f"⚠️ Não foi possível verificar dados no banco: {e}")
        
        # Dicas para próximas coletas
        with st.expander("💡 Dicas para Coleta Eficiente"):
            st.markdown("""
            ### 🎯 Melhores Práticas:
            
            - **Primeira vez**: Colete todos os indicadores com 10 anos para ter base completa
            - **Atualizações**: Use "Atualização Rápida" para pegar apenas dados recentes
            - **Problemas de conexão**: Reduza o número de indicadores ou o período
            - **Dados específicos**: Selecione apenas os indicadores que você precisa
            
            ### ⏰ Frequência Recomendada:
            
            - **Dados diários** (Selic, Câmbio): Atualize semanalmente
            - **Dados mensais** (IPCA, Fiscal): Atualize mensalmente
            - **Dados trimestrais** (PIB): Atualize trimestralmente
            """)