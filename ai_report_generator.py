# ai_report_generator.py - Gerador de relatórios econômicos com análise de IA
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import config, get_indicator_display_names
from database_manager import DatabaseManager
from ml_models import EconomicPredictor

logger = logging.getLogger(__name__)

class EconomicAnalyzer:
    """
    Analisador econômico com capacidades de IA para geração de insights
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.predictor = EconomicPredictor()
        self.indicator_names = get_indicator_display_names()
        
    def analyze_trend(self, data: pd.DataFrame, indicator: str) -> Dict[str, Any]:
        """
        Analisa tendência de um indicador
        
        Args:
            data: DataFrame com dados do indicador
            indicator: Nome do indicador
        
        Returns:
            Dict com análise da tendência
        """
        if data.empty or len(data) < 3:
            return {"trend": "insufficient_data", "confidence": 0.0}
        
        # Calcular tendência usando regressão linear simples
        data_sorted = data.sort_values('date').copy()
        data_sorted['days'] = (data_sorted['date'] - data_sorted['date'].min()).dt.days
        
        # Regressão linear simples
        x = data_sorted['days'].values
        y = data_sorted['value'].values
        
        # Remover NaN
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]
        
        if len(x) < 2:
            return {"trend": "insufficient_data", "confidence": 0.0}
        
        # Calcular coeficiente angular
        slope = np.polyfit(x, y, 1)[0]
        
        # Calcular R²
        correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
        r_squared = correlation ** 2
        
        # Determinar tendência
        threshold = np.std(y) * 0.01  # 1% do desvio padrão como threshold
        
        if abs(slope) < threshold:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "ascending"
        else:
            trend_direction = "descending"
        
        # Calcular variação percentual
        if len(y) >= 2:
            recent_change = ((y[-1] - y[0]) / abs(y[0])) * 100 if y[0] != 0 else 0
        else:
            recent_change = 0
        
        # Calcular volatilidade
        volatility = np.std(y) / np.mean(y) * 100 if np.mean(y) != 0 else 0
        
        return {
            "trend": trend_direction,
            "slope": slope,
            "confidence": r_squared,
            "recent_change_pct": recent_change,
            "volatility": volatility,
            "period_days": len(x),
            "last_value": y[-1] if len(y) > 0 else None
        }
    
    def detect_outliers(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detecta outliers nos dados usando IQR
        
        Args:
            data: DataFrame com dados
        
        Returns:
            Lista de outliers detectados
        """
        if data.empty:
            return []
        
        values = data['value'].dropna()
        if len(values) < 4:
            return []
        
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = []
        for idx, row in data.iterrows():
            value = row['value']
            if pd.notna(value) and (value < lower_bound or value > upper_bound):
                outliers.append({
                    'date': row['date'],
                    'value': value,
                    'type': 'high' if value > upper_bound else 'low',
                    'deviation': abs(value - values.median()) / values.std()
                })
        
        return outliers
    
    def analyze_correlation(self, indicators: List[str], period_months: int = 12) -> Dict[str, Dict]:
        """
        Analisa correlação entre indicadores
        
        Args:
            indicators: Lista de indicadores para analisar
            period_months: Período em meses para análise
        
        Returns:
            Dict com análise de correlação
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * period_months)
        
        # Carregar dados
        data_dict = {}
        for indicator in indicators:
            data = self.db_manager.load_data(
                indicator, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            if data is not None and not data.empty:
                data_dict[indicator] = data.set_index('date')['value']
        
        if len(data_dict) < 2:
            return {}
        
        # Criar DataFrame combinado
        combined_df = pd.DataFrame(data_dict)
        combined_df = combined_df.fillna(method='ffill').fillna(method='bfill')
        
        # Calcular matriz de correlação
        correlation_matrix = combined_df.corr()
        
        # Analisar correlações significativas
        correlations = {}
        for i, ind1 in enumerate(indicators):
            for j, ind2 in enumerate(indicators):
                if i < j and ind1 in correlation_matrix.index and ind2 in correlation_matrix.columns:
                    corr_value = correlation_matrix.loc[ind1, ind2]
                    if abs(corr_value) > 0.3:  # Correlação moderada ou forte
                        correlations[f"{ind1}_{ind2}"] = {
                            'correlation': corr_value,
                            'strength': self._classify_correlation(abs(corr_value)),
                            'direction': 'positive' if corr_value > 0 else 'negative'
                        }
        
        return correlations
    
    def _classify_correlation(self, abs_corr: float) -> str:
        """Classifica força da correlação"""
        if abs_corr >= 0.8:
            return 'very_strong'
        elif abs_corr >= 0.6:
            return 'strong'
        elif abs_corr >= 0.4:
            return 'moderate'
        else:
            return 'weak'
    
    def generate_insights(self, indicator: str, data: pd.DataFrame) -> List[str]:
        """
        Gera insights baseados em IA para um indicador
        
        Args:
            indicator: Nome do indicador
            data: DataFrame com dados
        
        Returns:
            Lista de insights gerados
        """
        insights = []
        
        if data.empty:
            return ["Dados insuficientes para análise."]
        
        # Análise de tendência
        trend_analysis = self.analyze_trend(data, indicator)
        
        # Insight sobre tendência
        if trend_analysis["confidence"] > 0.5:
            if trend_analysis["trend"] == "ascending":
                insights.append(
                    f"O {self.indicator_names.get(indicator, indicator)} apresenta tendência de alta "
                    f"com variação de {trend_analysis['recent_change_pct']:.2f}% no período analisado."
                )
            elif trend_analysis["trend"] == "descending":
                insights.append(
                    f"O {self.indicator_names.get(indicator, indicator)} mostra tendência de queda "
                    f"com variação de {trend_analysis['recent_change_pct']:.2f}% no período analisado."
                )
            else:
                insights.append(
                    f"O {self.indicator_names.get(indicator, indicator)} mantém-se relativamente estável "
                    f"no período analisado."
                )
        
        # Insight sobre volatilidade
        volatility = trend_analysis.get("volatility", 0)
        if volatility > 10:
            insights.append(
                f"O indicador apresenta alta volatilidade ({volatility:.1f}%), "
                "indicando instabilidade nos valores."
            )
        elif volatility < 2:
            insights.append(
                f"O indicador mostra baixa volatilidade ({volatility:.1f}%), "
                "sugerindo comportamento estável."
            )
        
        # Análise de outliers
        outliers = self.detect_outliers(data)
        if outliers:
            if len(outliers) > len(data) * 0.1:  # Mais de 10% são outliers
                insights.append(
                    f"Detectados {len(outliers)} valores atípicos, "
                    "sugerindo eventos extraordinários no período."
                )
            else:
                last_outlier = max(outliers, key=lambda x: x['date'])
                insights.append(
                    f"Último valor atípico detectado em {last_outlier['date'].strftime('%d/%m/%Y')}: "
                    f"{last_outlier['value']:.2f} ({last_outlier['type']} extremo)."
                )
        
        # Análise específica por indicador
        indicator_insights = self._get_indicator_specific_insights(indicator, data, trend_analysis)
        insights.extend(indicator_insights)
        
        return insights[:config.reports.max_insights_per_indicator]
    
    def _get_indicator_specific_insights(self, indicator: str, data: pd.DataFrame, trend_analysis: Dict) -> List[str]:
        """
        Gera insights específicos por tipo de indicador
        
        Args:
            indicator: Nome do indicador
            data: DataFrame com dados
            trend_analysis: Análise de tendência
        
        Returns:
            Lista de insights específicos
        """
        insights = []
        last_value = trend_analysis.get("last_value")
        
        if indicator == 'ipca':
            if last_value is not None:
                if last_value > 6:
                    insights.append("A inflação está acima da meta superior (6%), indicando pressões inflacionárias.")
                elif last_value < 3:
                    insights.append("A inflação está abaixo da meta inferior (3%), podendo indicar desaceleração econômica.")
                else:
                    insights.append("A inflação está dentro da meta (3-6%), sinalizando estabilidade de preços.")
        
        elif indicator == 'selic':
            if last_value is not None:
                if trend_analysis["trend"] == "ascending":
                    insights.append("A elevação da taxa Selic indica política monetária contracionista para combater inflação.")
                elif trend_analysis["trend"] == "descending":
                    insights.append("A redução da taxa Selic sugere estímulo econômico e expectativa de inflação controlada.")
        
        elif indicator == 'pib':
            if trend_analysis["trend"] == "ascending":
                insights.append("O crescimento do PIB indica expansão da atividade econômica.")
            elif trend_analysis["trend"] == "descending":
                insights.append("A contração do PIB pode sinalizar desaceleração ou recessão econômica.")
        
        elif indicator == 'cambio_usd':
            if last_value is not None:
                recent_change = trend_analysis.get("recent_change_pct", 0)
                if abs(recent_change) > 10:
                    if recent_change > 0:
                        insights.append("A forte desvalorização do real pode pressionar a inflação e aumentar custos de importação.")
                    else:
                        insights.append("A valorização do real pode beneficiar importadores e reduzir pressões inflacionárias.")
        
        elif indicator == 'divida_pib':
            if last_value is not None:
                if last_value > 80:
                    insights.append("A relação Dívida/PIB elevada (>80%) pode limitar o espaço fiscal do governo.")
                elif trend_analysis["trend"] == "ascending":
                    insights.append("O crescimento da dívida pública requer atenção à sustentabilidade fiscal.")
        
        return insights


class ReportGenerator:
    """
    Gerador de relatórios econômicos com análise de IA
    """
    
    def __init__(self):
        self.analyzer = EconomicAnalyzer()
        self.predictor = EconomicPredictor()
        self.reports_dir = Path(config.reports.output_dir)
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_economic_overview(self, months_back: int = 12) -> Dict[str, Any]:
        """
        Gera visão geral da economia
        
        Args:
            months_back: Meses para análise retroativa
        
        Returns:
            Dict com relatório completo
        """
        report = {
            'title': 'Panorama Econômico Brasileiro',
            'generated_at': datetime.now(),
            'period_months': months_back,
            'sections': {}
        }
        
        # Indicadores principais para análise
        main_indicators = ['ipca', 'selic', 'pib', 'cambio_usd', 'divida_pib']
        
        # Seção 1: Análise de Indicadores Principais
        indicators_section = {}
        for indicator in main_indicators:
            data = self.analyzer.db_manager.load_data(indicator)
            if data is not None and not data.empty:
                # Últimos N meses
                cutoff_date = datetime.now() - timedelta(days=30 * months_back)
                recent_data = data[data['date'] >= cutoff_date]
                
                if not recent_data.empty:
                    trend_analysis = self.analyzer.analyze_trend(recent_data, indicator)
                    insights = self.analyzer.generate_insights(indicator, recent_data)
                    
                    indicators_section[indicator] = {
                        'name': self.analyzer.indicator_names.get(indicator, indicator),
                        'trend_analysis': trend_analysis,
                        'insights': insights,
                        'last_value': recent_data['value'].iloc[-1] if len(recent_data) > 0 else None,
                        'last_date': recent_data['date'].iloc[-1] if len(recent_data) > 0 else None
                    }
        
        report['sections']['indicators'] = indicators_section
        
        # Seção 2: Análise de Correlações
        correlations = self.analyzer.analyze_correlation(main_indicators, months_back)
        report['sections']['correlations'] = correlations
        
        # Seção 3: Previsões
        predictions_section = {}
        for indicator in ['ipca', 'selic', 'pib']:
            try:
                prediction = self.predictor.predict_future(indicator, steps=6)
                if prediction is not None:
                    predictions_section[indicator] = {
                        'forecast': prediction.to_dict('records'),
                        'trend_forecast': 'ascending' if prediction['value'].iloc[-1] > prediction['value'].iloc[0] else 'descending'
                    }
            except Exception as e:
                logger.warning(f"Erro ao gerar previsão para {indicator}: {e}")
        
        report['sections']['predictions'] = predictions_section
        
        # Seção 4: Resumo Executivo com IA
        executive_summary = self._generate_executive_summary(report)
        report['executive_summary'] = executive_summary
        
        return report
    
    def _generate_executive_summary(self, report: Dict[str, Any]) -> List[str]:
        """
        Gera resumo executivo baseado na análise
        
        Args:
            report: Relatório completo
        
        Returns:
            Lista de pontos do resumo executivo
        """
        summary = []
        
        indicators_data = report['sections'].get('indicators', {})
        
        # Análise da inflação
        if 'ipca' in indicators_data:
            ipca_data = indicators_data['ipca']
            trend = ipca_data['trend_analysis']['trend']
            last_value = ipca_data['last_value']
            
            if trend == 'ascending' and last_value and last_value > 5:
                summary.append("⚠️ INFLAÇÃO: Pressões inflacionárias crescentes requerem atenção da política monetária.")
            elif trend == 'descending' and last_value and last_value < 4:
                summary.append("✅ INFLAÇÃO: Tendência de desaceleração indica eficácia das políticas anti-inflacionárias.")
            else:
                summary.append("📊 INFLAÇÃO: Mantém-se em patamares controlados dentro do regime de metas.")
        
        # Análise da política monetária
        if 'selic' in indicators_data:
            selic_data = indicators_data['selic']
            selic_trend = selic_data['trend_analysis']['trend']
            
            if selic_trend == 'ascending':
                summary.append("📈 POLÍTICA MONETÁRIA: Ciclo de alta da Selic indica postura restritiva do BC.")
            elif selic_trend == 'descending':
                summary.append("📉 POLÍTICA MONETÁRIA: Redução da Selic sinaliza estímulo à atividade econômica.")
        
        # Análise da atividade econômica
        if 'pib' in indicators_data:
            pib_data = indicators_data['pib']
            pib_trend = pib_data['trend_analysis']['trend']
            
            if pib_trend == 'ascending':
                summary.append("🚀 ATIVIDADE ECONÔMICA: PIB em trajetória de crescimento indica recuperação.")
            elif pib_trend == 'descending':
                summary.append("⚠️ ATIVIDADE ECONÔMICA: Desaceleração do PIB requer atenção às políticas de estímulo.")
        
        # Análise do câmbio
        if 'cambio_usd' in indicators_data:
            cambio_data = indicators_data['cambio_usd']
            cambio_change = cambio_data['trend_analysis'].get('recent_change_pct', 0)
            
            if cambio_change > 15:
                summary.append("💱 CÂMBIO: Forte desvalorização do real pode pressionar inflação importada.")
            elif cambio_change < -10:
                summary.append("💱 CÂMBIO: Valorização do real beneficia controle inflacionário.")
        
        # Análise fiscal
        if 'divida_pib' in indicators_data:
            divida_data = indicators_data['divida_pib']
            divida_trend = divida_data['trend_analysis']['trend']
            
            if divida_trend == 'ascending':
                summary.append("📊 FISCAL: Crescimento da dívida pública requer atenção à sustentabilidade fiscal.")
        
        # Análise de correlações significativas
        correlations = report['sections'].get('correlations', {})
        strong_correlations = [k for k, v in correlations.items() if v['strength'] in ['strong', 'very_strong']]
        
        if strong_correlations:
            summary.append(f"🔗 CORRELAÇÕES: Identificadas {len(strong_correlations)} correlações fortes entre indicadores.")
        
        # Se não há pontos específicos, adicionar análise geral
        if not summary:
            summary.append("📊 CENÁRIO: Indicadores econômicos mostram comportamento dentro da normalidade histórica.")
        
        return summary

    def create_visual_report(self, report_data: Dict[str, Any]) -> str:
        """
        Cria relatório visual com gráficos
        
        Args:
            report_data: Dados do relatório
        
        Returns:
            Caminho do arquivo HTML gerado
        """
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        
        # Criar subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Inflação (IPCA)', 'Taxa SELIC', 'PIB Real', 'Câmbio USD'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        indicators_to_plot = ['ipca', 'selic', 'pib', 'cambio_usd']
        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        
        for i, indicator in enumerate(indicators_to_plot):
            data = self.analyzer.db_manager.load_data(indicator)
            if data is not None and not data.empty:
                row, col = positions[i]
                
                # Últimos 24 meses
                cutoff_date = datetime.now() - timedelta(days=730)
                recent_data = data[data['date'] >= cutoff_date].sort_values('date')
                
                if not recent_data.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=recent_data['date'],
                            y=recent_data['value'],
                            name=self.analyzer.indicator_names.get(indicator, indicator),
                            line=dict(width=2)
                        ),
                        row=row, col=col
                    )
        
        # Atualizar layout
        fig.update_layout(
            title_text="Painel de Indicadores Econômicos - Últimos 24 Meses",
            showlegend=False,
            height=800
        )
        
        # Salvar como HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_economico_{timestamp}.html"
        filepath = self.reports_dir / filename
        
        fig.write_html(str(filepath))
        
        return str(filepath)
    
    def export_report_to_json(self, report_data: Dict[str, Any]) -> str:
        """
        Exporta relatório para JSON
        
        Args:
            report_data: Dados do relatório
        
        Returns:
            Caminho do arquivo JSON
        """
        # Converter datetime para string para serialização JSON
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            return obj
        
        # Função recursiva para converter datetimes
        def convert_datetimes_recursive(data):
            if isinstance(data, dict):
                return {k: convert_datetimes_recursive(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_datetimes_recursive(item) for item in data]
            else:
                return convert_datetime(data)
        
        converted_data = convert_datetimes_recursive(report_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_dados_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)

# Função de conveniência
def generate_quick_report(months_back: int = 12) -> Tuple[Dict[str, Any], str, str]:
    """
    Gera relatório rápido com análise econômica
    
    Args:
        months_back: Meses para análise
    
    Returns:
        Tuple (dados_relatório, caminho_html, caminho_json)
    """
    generator = ReportGenerator()
    
    # Gerar relatório
    report_data = generator.generate_economic_overview(months_back)
    
    # Criar visualizações
    html_path = generator.create_visual_report(report_data)
    
    # Exportar dados
    json_path = generator.export_report_to_json(report_data)
    
    return report_data, html_path, json_path

if __name__ == "__main__":
    # Teste do gerador de relatórios
    print("🔄 Gerando relatório econômico com análise de IA...")
    
    try:
        report_data, html_file, json_file = generate_quick_report(6)
        
        print(f"✅ Relatório gerado com sucesso!")
        print(f"📊 Arquivo HTML: {html_file}")
        print(f"📄 Arquivo JSON: {json_file}")
        
        # Mostrar resumo executivo
        if 'executive_summary' in report_data:
            print(f"\n📋 Resumo Executivo:")
            for point in report_data['executive_summary']:
                print(f"  {point}")
    
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")
        logger.error(f"Erro na geração de relatório: {e}", exc_info=True)



