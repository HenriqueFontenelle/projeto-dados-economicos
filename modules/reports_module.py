# modules/reports_module.py - VERSÃO CORRIGIDA
import streamlit as st
from ai_report_generator import ReportGenerator, generate_quick_report
from config import config
from utils.base_module import BaseModule
import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ReportsModule(BaseModule):
    """Módulo para geração de relatórios com IA"""
    
    def render(self):
        st.title("📋 Relatórios Econômicos com Inteligência Artificial")
        
        st.markdown("""
        Esta seção utiliza **Inteligência Artificial** para gerar análises automáticas dos indicadores econômicos,
        incluindo detecção de tendências, correlações e previsões futuras.
        
        **🆕 Novidades v2.0:**
        - Análise automática de tendências
        - Detecção de outliers e anomalias  
        - Correlações entre indicadores
        - Insights contextualizados por IA
        - Resumo executivo automático
        """)
        
        # Tipos de relatório disponíveis
        st.subheader("📊 Tipos de Relatório Disponíveis")
        
        report_type = st.selectbox(
            "Selecione o tipo de relatório",
            config.reports.report_types,
            format_func=self._format_report_type,
            help="Diferentes tipos de análise econômica"
        )
        
        # Configurações do relatório
        self._render_report_config(report_type)
        
        # Botão para gerar relatório
        if st.button("🚀 Gerar Relatório com IA", use_container_width=True, type="primary"):
            months_back = st.session_state.get('months_back', 12)
            include_predictions = st.session_state.get('include_predictions', True)
            include_correlations = st.session_state.get('include_correlations', True)
            
            self._generate_report(report_type, months_back, include_predictions, include_correlations)
        
        st.markdown("---")
        
        # Mostrar relatórios anteriores
        self._show_previous_reports()
    
    def _render_report_config(self, report_type: str):
        """Renderiza configurações do relatório"""
        
        st.subheader("⚙️ Configurações do Relatório")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            months_back = st.slider(
                "Período de análise (meses)",
                min_value=3,
                max_value=24,
                value=12,
                help="Quantos meses retroativos analisar"
            )
            st.session_state.months_back = months_back
        
        with col2:
            include_predictions = st.checkbox(
                "Incluir previsões",
                value=True,
                help="Adicionar análise preditiva ao relatório"
            )
            st.session_state.include_predictions = include_predictions
        
        with col3:
            include_correlations = st.checkbox(
                "Incluir correlações",
                value=True,
                help="Analisar correlações entre indicadores"
            )
            st.session_state.include_correlations = include_correlations
        
        # Configurações avançadas específicas por tipo
        with st.expander("🔧 Configurações Avançadas"):
            
            if report_type == 'monetary_policy_analysis':
                st.markdown("**Análise de Política Monetária:**")
                focus_indicators = st.multiselect(
                    "Indicadores de foco",
                    ['ipca', 'selic', 'selic_meta', 'igpm'],
                    default=['ipca', 'selic', 'selic_meta'],
                    help="Indicadores principais para análise monetária"
                )
                st.session_state.focus_indicators = focus_indicators
            
            elif report_type == 'inflation_forecast':
                st.markdown("**Previsão de Inflação:**")
                inflation_horizon = st.slider(
                    "Horizonte de previsão (meses)",
                    3, 18, 12,
                    help="Quantos meses prever a inflação"
                )
                st.session_state.inflation_horizon = inflation_horizon
            
            elif report_type == 'fiscal_health':
                st.markdown("**Saúde Fiscal:**")
                fiscal_indicators = st.multiselect(
                    "Indicadores fiscais",
                    ['divida_pib', 'resultado_primario'],
                    default=['divida_pib', 'resultado_primario'],
                    help="Indicadores para análise fiscal"
                )
                st.session_state.fiscal_indicators = fiscal_indicators
            
            elif report_type == 'external_sector':
                st.markdown("**Setor Externo:**")
                external_indicators = st.multiselect(
                    "Indicadores externos",
                    ['cambio_usd', 'transacoes', 'reservas_internacionais'],
                    default=['cambio_usd', 'transacoes'],
                    help="Indicadores do setor externo"
                )
                st.session_state.external_indicators = external_indicators
            
            # Configurações gerais de IA
            st.markdown("**Configurações de IA:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                confidence_threshold = st.slider(
                    "Threshold de confiança",
                    min_value=0.1,
                    max_value=1.0,
                    value=config.reports.confidence_threshold,
                    step=0.1,
                    help="Nível mínimo de confiança para insights"
                )
                st.session_state.confidence_threshold = confidence_threshold
            
            with col2:
                max_insights = st.slider(
                    "Máximo de insights por indicador",
                    min_value=1,
                    max_value=10,
                    value=config.reports.max_insights_per_indicator,
                    help="Quantos insights gerar por indicador"
                )
                st.session_state.max_insights = max_insights
    
    def _format_report_type(self, report_type: str) -> str:
        """Formata nome do tipo de relatório para exibição"""
        mapping = {
            'economic_overview': '🌍 Panorama Econômico Geral',
            'monetary_policy_analysis': '🏦 Análise de Política Monetária',
            'inflation_forecast': '📈 Previsão de Inflação',
            'fiscal_health': '💰 Saúde Fiscal',
            'external_sector': '🌐 Setor Externo',
            'custom_analysis': '🔧 Análise Personalizada'
        }
        return mapping.get(report_type, report_type.title())
    
    def _generate_report(self, report_type: str, months_back: int, include_predictions: bool, include_correlations: bool):
        """Gera relatório com IA"""
        
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Inicializando gerador de relatórios...")
                progress_bar.progress(0.1)
                
                generator = ReportGenerator()
                
                status_text.text("📊 Coletando e analisando dados...")
                progress_bar.progress(0.3)
                
                # Gerar relatório baseado no tipo
                if report_type == 'economic_overview':
                    report_data = generator.generate_economic_overview(months_back)
                else:
                    # Para outros tipos, usar overview como base e personalizar
                    report_data = generator.generate_economic_overview(months_back)
                    report_data['report_type'] = report_type
                    report_data['title'] = self._get_report_title(report_type)
                    
                    # Personalizar baseado no tipo
                    report_data = self._customize_report_by_type(report_data, report_type)
                
                progress_bar.progress(0.7)
                status_text.text("🎨 Criando visualizações...")
                
                # Criar visualizações
                html_path = generator.create_visual_report(report_data)
                
                progress_bar.progress(0.9)
                status_text.text("💾 Salvando relatório...")
                
                # Exportar dados
                json_path = generator.export_report_to_json(report_data)
                
                progress_bar.progress(1.0)
                status_text.text("✅ Relatório gerado com sucesso!")
                
                # Limpar progress após 2 segundos
                import time
                time.sleep(2)
                progress_container.empty()
                
                # Mostrar resultados
                self._display_report_results(report_data, html_path, json_path)
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar relatório: {e}")
                logger.error(f"Erro na geração de relatório: {e}", exc_info=True)
                
                # Sugestões de solução
                with st.expander("💡 Possíveis soluções"):
                    st.markdown("""
                    - Verifique se há dados coletados para o período
                    - Tente reduzir o período de análise
                    - Execute a coleta de dados primeiro
                    - Verifique se há modelos ML treinados (para previsões)
                    """)
    
    def _get_report_title(self, report_type: str) -> str:
        """Retorna título personalizado por tipo de relatório"""
        titles = {
            'monetary_policy_analysis': 'Análise de Política Monetária Brasileira',
            'inflation_forecast': 'Relatório de Previsão de Inflação',
            'fiscal_health': 'Análise da Saúde Fiscal do Brasil',
            'external_sector': 'Relatório do Setor Externo',
            'custom_analysis': 'Análise Econômica Personalizada'
        }
        return titles.get(report_type, 'Relatório Econômico')
    
    def _customize_report_by_type(self, report_data: dict, report_type: str) -> dict:
        """Personaliza relatório baseado no tipo"""
        
        if report_type == 'monetary_policy_analysis':
            # Focar em indicadores monetários
            focus_indicators = st.session_state.get('focus_indicators', ['ipca', 'selic'])
            
            # Filtrar apenas indicadores monetários
            if 'sections' in report_data and 'indicators' in report_data['sections']:
                filtered_indicators = {
                    k: v for k, v in report_data['sections']['indicators'].items() 
                    if k in focus_indicators
                }
                report_data['sections']['indicators'] = filtered_indicators
        
        elif report_type == 'inflation_forecast':
            # Focar apenas em inflação
            if 'sections' in report_data and 'indicators' in report_data['sections']:
                inflation_indicators = {
                    k: v for k, v in report_data['sections']['indicators'].items() 
                    if k in ['ipca', 'igpm', 'inpc']
                }
                report_data['sections']['indicators'] = inflation_indicators
        
        elif report_type == 'fiscal_health':
            # Focar em indicadores fiscais
            fiscal_indicators = st.session_state.get('fiscal_indicators', ['divida_pib', 'resultado_primario'])
            
            if 'sections' in report_data and 'indicators' in report_data['sections']:
                filtered_indicators = {
                    k: v for k, v in report_data['sections']['indicators'].items() 
                    if k in fiscal_indicators
                }
                report_data['sections']['indicators'] = filtered_indicators
        
        elif report_type == 'external_sector':
            # Focar em setor externo
            external_indicators = st.session_state.get('external_indicators', ['cambio_usd', 'transacoes'])
            
            if 'sections' in report_data and 'indicators' in report_data['sections']:
                filtered_indicators = {
                    k: v for k, v in report_data['sections']['indicators'].items() 
                    if k in external_indicators
                }
                report_data['sections']['indicators'] = filtered_indicators
        
        return report_data
    
    def _display_report_results(self, report_data: dict, html_path: str, json_path: str):
        """Exibe resultados do relatório gerado"""
        
        st.success("🎉 Relatório gerado com sucesso!")
        
        # Downloads
        col1, col2 = st.columns(2)
        
        with col1:
            with open(html_path, 'rb') as f:
                st.download_button(
                    "📊 Baixar Visualizações (HTML)",
                    data=f.read(),
                    file_name=f"relatorio_visual_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                    mime="text/html",
                    use_container_width=True
                )
        
        with col2:
            with open(json_path, 'rb') as f:
                st.download_button(
                    "📄 Baixar Dados (JSON)",
                    data=f.read(),
                    file_name=f"relatorio_dados_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        # Resumo Executivo
        if 'executive_summary' in report_data:
            st.subheader("📋 Resumo Executivo")
            
            for point in report_data['executive_summary']:
                st.markdown(f"• {point}")
        
        # Detalhes dos indicadores
        if 'sections' in report_data and 'indicators' in report_data['sections']:
            st.subheader("📊 Análise Detalhada dos Indicadores")
            
            indicators_data = report_data['sections']['indicators']
            
            for indicator, data in indicators_data.items():
                with st.expander(f"🔍 {data.get('name', indicator)}"):
                    
                    # Métricas principais
                    if data.get('last_value') is not None:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            change_pct = data['trend_analysis'].get('recent_change_pct', 0)
                            st.metric(
                                "Último Valor",
                                f"{data['last_value']:.4f}",
                                delta=f"{change_pct:+.2f}%"
                            )
                        
                        with col2:
                            trend = data['trend_analysis']['trend']
                            trend_emoji = "📈" if trend == "ascending" else "📉" if trend == "descending" else "➡️"
                            st.metric("Tendência", f"{trend_emoji} {trend.title()}")
                        
                        with col3:
                            confidence = data['trend_analysis'].get('confidence', 0)
                            confidence_color = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
                            st.metric("Confiança", f"{confidence_color} {confidence:.2f}")
                    
                    # Insights da IA
                    if data.get('insights'):
                        st.markdown("**💡 Insights da IA:**")
                        for i, insight in enumerate(data['insights'], 1):
                            st.markdown(f"{i}. {insight}")
                    
                    # Dados técnicos - REMOVIDO O EXPANDER ANINHADO
                    if 'trend_analysis' in data:
                        ta = data['trend_analysis']
                        
                        st.markdown("**📈 Dados Técnicos:**")
                        st.write(f"**Volatilidade:** {ta.get('volatility', 0):.2f}%")
                        st.write(f"**Período analisado:** {ta.get('period_days', 0)} dias")
                        st.write(f"**Slope:** {ta.get('slope', 0):.6f}")
        
        # Correlações
        if 'sections' in report_data and 'correlations' in report_data['sections']:
            correlations = report_data['sections']['correlations']
            
            if correlations:
                st.subheader("🔗 Correlações Identificadas")
                
                for corr_key, corr_data in correlations.items():
                    indicators = corr_key.split('_')
                    correlation_value = corr_data['correlation']
                    strength = corr_data['strength']
                    direction = corr_data['direction']
                    
                    # Emojis baseados na força e direção
                    direction_emoji = "📈" if direction == "positive" else "📉"
                    
                    if strength == "very_strong":
                        strength_emoji = "🔴"
                        strength_text = "muito forte"
                    elif strength == "strong":
                        strength_emoji = "🟠"
                        strength_text = "forte"
                    elif strength == "moderate":
                        strength_emoji = "🟡"
                        strength_text = "moderada"
                    else:
                        strength_emoji = "🟢"
                        strength_text = "fraca"
                    
                    st.markdown(
                        f"{direction_emoji} {strength_emoji} **{indicators[0].upper()} vs {indicators[1].upper()}**: "
                        f"Correlação {direction} {strength_text} ({correlation_value:.3f})"
                    )
        
        # Previsões (se disponíveis)
        if 'sections' in report_data and 'predictions' in report_data['sections']:
            predictions = report_data['sections']['predictions']
            
            if predictions:
                st.subheader("🔮 Previsões")
                
                for indicator, pred_data in predictions.items():
                    trend_forecast = pred_data.get('trend_forecast', 'estável')
                    trend_emoji = "📈" if trend_forecast == "ascending" else "📉" if trend_forecast == "descending" else "➡️"
                    
                    st.markdown(f"{trend_emoji} **{indicator.upper()}**: Tendência {trend_forecast} prevista")
        
        # Metadados do relatório
        st.subheader("ℹ️ Informações do Relatório")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Título:** {report_data.get('title', 'N/A')}")
            st.write(f"**Tipo:** {report_data.get('report_type', 'economic_overview')}")
        
        with col2:
            st.write(f"**Gerado em:** {report_data.get('generated_at', 'N/A')}")
            st.write(f"**Período:** {report_data.get('period_months', 'N/A')} meses")
    
    def _show_previous_reports(self):
        """Mostra relatórios anteriores gerados"""
        st.subheader("📁 Relatórios Anteriores")
        
        # Listar arquivos de relatório no diretório
        reports_dir = Path(config.reports.output_dir)
        
        if reports_dir.exists():
            html_files = list(reports_dir.glob("relatorio_economico_*.html"))
            json_files = list(reports_dir.glob("relatorio_dados_*.json"))
            
            if html_files or json_files:
                # Mostrar últimos 5 relatórios
                for html_file in sorted(html_files, reverse=True)[:5]:
                    timestamp_parts = html_file.stem.split('_')[-2:]
                    if len(timestamp_parts) == 2:
                        date_part, time_part = timestamp_parts
                        try:
                            date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}"
                            
                            with st.expander(f"📊 Relatório de {date_str}"):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    if html_file.exists():
                                        st.download_button(
                                            "📊 Baixar HTML",
                                            data=html_file.read_bytes(),
                                            file_name=html_file.name,
                                            mime="text/html",
                                            use_container_width=True
                                        )
                                
                                with col2:
                                    json_file = reports_dir / html_file.name.replace('relatorio_economico_', 'relatorio_dados_').replace('.html', '.json')
                                    if json_file.exists():
                                        st.download_button(
                                            "📄 Baixar JSON",
                                            data=json_file.read_bytes(),
                                            file_name=json_file.name,
                                            mime="application/json",
                                            use_container_width=True
                                        )
                                
                                with col3:
                                    # Mostrar preview do resumo (se possível)
                                    if json_file.exists():
                                        try:
                                            with open(json_file, 'r', encoding='utf-8') as f:
                                                report_data = json.load(f)
                                            
                                            if 'executive_summary' in report_data:
                                                st.write("**Preview:**")
                                                summary = report_data['executive_summary']
                                                if summary:
                                                    st.caption(summary[0][:100] + "..." if len(summary[0]) > 100 else summary[0])
                                        except:
                                            st.caption("Preview não disponível")
                        except:
                            continue
            else:
                st.info("📄 Nenhum relatório anterior encontrado. Gere seu primeiro relatório!")
                
                # Dicas para primeiro uso
                with st.expander("💡 Dicas para seu primeiro relatório"):
                    st.markdown("""
                    ### 🚀 Como começar:
                    
                    1. **Primeiro passo**: Execute a coleta de dados (se ainda não fez)
                    2. **Escolha o tipo**: Para começar, recomendamos "Panorama Econômico Geral"
                    3. **Configure o período**: 12 meses é um bom período inicial
                    4. **Gere o relatório**: Clique em "Gerar Relatório com IA"
                    
                    ### 📊 Tipos recomendados por caso de uso:
                    
                    - **Análise geral**: Panorama Econômico Geral
                    - **Foco em inflação**: Previsão de Inflação
                    - **Política monetária**: Análise de Política Monetária
                    - **Situação fiscal**: Saúde Fiscal
                    - **Economia externa**: Setor Externo
                    """)
        else:
            st.info("📂 Diretório de relatórios não encontrado.")
            
            if st.button("📁 Criar Diretório de Relatórios"):
                reports_dir.mkdir(parents=True, exist_ok=True)
                st.success("✅ Diretório criado com sucesso!")
                st.rerun()