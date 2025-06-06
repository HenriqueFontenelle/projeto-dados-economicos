# config.py - Configuração centralizada do sistema
import os
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime, timedelta

@dataclass
class DatabaseConfig:
    """Configurações do banco de dados"""
    db_path: str = "data/economic_data.db"
    table_prefix: str = "bcb_"
    backup_enabled: bool = True
    backup_frequency_days: int = 7

@dataclass
class DataCollectionConfig:
    """Configurações para coleta de dados"""
    default_years: int = 10  # Aumentado para 10 anos
    max_retries: int = 3
    request_timeout: int = 30
    delay_between_requests: float = 0.5  # Delay em segundos entre requisições
    batch_size: int = 1000  # Tamanho do batch para processamento
    
    # URLs das APIs
    bcb_base_url: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    
    # Mapeamento completo de indicadores BCB
    indicators: Dict[str, Dict] = None
    
    def __post_init__(self):
        if self.indicators is None:
            self.indicators = {
                'ipca': {
                    'series_id': 433,
                    'name': 'Inflação (IPCA)',
                    'unit': '%',
                    'frequency': 'monthly',
                    'description': 'Índice Nacional de Preços ao Consumidor Amplo'
                },
                'pib': {
                    'series_id': 4380,
                    'name': 'PIB Real',
                    'unit': 'Índice',
                    'frequency': 'quarterly',
                    'description': 'Produto Interno Bruto a preços constantes'
                },
                'divida_pib': {
                    'series_id': 13761,
                    'name': 'Dívida/PIB',
                    'unit': '%',
                    'frequency': 'monthly',
                    'description': 'Dívida Líquida do Setor Público/PIB'
                },
                'selic': {
                    'series_id': 11,
                    'name': 'Taxa SELIC Diária',
                    'unit': '% a.a.',
                    'frequency': 'daily',
                    'description': 'Taxa de juros - Over/Selic - Taxa acumulada no mês'
                },
                'selic_meta': {
                    'series_id': 4189,
                    'name': 'Meta da Taxa SELIC',
                    'unit': '% a.a.',
                    'frequency': 'irregular',
                    'description': 'Taxa de juros - Meta Selic definida pelo Copom'
                },
                'transacoes': {
                    'series_id': 22707,
                    'name': 'Saldo em Transações Correntes',
                    'unit': 'US$ milhões',
                    'frequency': 'monthly',
                    'description': 'Balanço de Pagamentos - Saldo em Transações Correntes'
                },
                'resultado_primario': {
                    'series_id': 7547,
                    'name': 'Resultado Primário',
                    'unit': 'R$ milhões',
                    'frequency': 'monthly',
                    'description': 'Indicadores Fiscais - Resultado Primário do Governo Central'
                },
                # Novos indicadores para análise mais completa
                'igpm': {
                    'series_id': 189,
                    'name': 'IGP-M',
                    'unit': '%',
                    'frequency': 'monthly',
                    'description': 'Índice Geral de Preços do Mercado'
                },
                'inpc': {
                    'series_id': 188,
                    'name': 'INPC',
                    'unit': '%',
                    'frequency': 'monthly',
                    'description': 'Índice Nacional de Preços ao Consumidor'
                },
                'cambio_usd': {
                    'series_id': 1,
                    'name': 'Taxa de Câmbio USD',
                    'unit': 'R$/US$',
                    'frequency': 'daily',
                    'description': 'Taxa de câmbio - R$ / US$ - comercial - compra'
                },
                'reservas_internacionais': {
                    'series_id': 3546,
                    'name': 'Reservas Internacionais',
                    'unit': 'US$ milhões',
                    'frequency': 'daily',
                    'description': 'Reservas Internacionais - Total'
                }
            }

@dataclass
class MLConfig:
    """Configurações para Machine Learning"""
    models_dir: str = "models"
    reports_dir: str = "reports"
    plots_dir: str = "plots"
    
    # Configurações de modelos
    default_test_size: float = 0.2
    cross_validation_folds: int = 5
    random_state: int = 42
    
    # Configurações de features
    max_lag_periods: int = 12  # Máximo de períodos de lag
    min_data_points: int = 36  # Mínimo de pontos para treinar modelo
    
    # Modelos disponíveis
    available_models: List[str] = None
    
    def __post_init__(self):
        if self.available_models is None:
            self.available_models = [
                'linear_regression',
                'ridge_regression', 
                'lasso_regression',
                'random_forest',
                'gradient_boosting',
                'xgboost',
                'lstm'  # Para implementação futura
            ]

@dataclass
class ReportConfig:
    """Configurações para geração de relatórios"""
    template_dir: str = "templates"
    output_dir: str = "reports"
    
    # Configurações de IA para relatórios
    ai_analysis_enabled: bool = True
    max_insights_per_indicator: int = 5
    confidence_threshold: float = 0.7
    
    # Tipos de relatório disponíveis
    report_types: List[str] = None
    
    def __post_init__(self):
        if self.report_types is None:
            self.report_types = [
                'economic_overview',
                'monetary_policy_analysis', 
                'inflation_forecast',
                'fiscal_health',
                'external_sector',
                'custom_analysis'
            ]

@dataclass
class AppConfig:
    """Configuração principal da aplicação"""
    # Versão do sistema
    version: str = "2.0.0"
    debug_mode: bool = False
    
    # Configurações de módulos
    database: DatabaseConfig = None
    data_collection: DataCollectionConfig = None
    ml: MLConfig = None
    reports: ReportConfig = None
    
    # Configurações do Streamlit
    page_title: str = "Sistema de Análise Econômica - BCB"
    page_icon: str = "📊"
    layout: str = "wide"
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.data_collection is None:
            self.data_collection = DataCollectionConfig()
        if self.ml is None:
            self.ml = MLConfig()
        if self.reports is None:
            self.reports = ReportConfig()
        
        # Criar diretórios necessários
        self._create_directories()
    
    def _create_directories(self):
        """Cria os diretórios necessários para o funcionamento do sistema"""
        directories = [
            os.path.dirname(self.database.db_path),
            self.ml.models_dir,
            self.ml.reports_dir,
            self.ml.plots_dir,
            self.reports.template_dir,
            self.reports.output_dir
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

# Instância global de configuração
config = AppConfig()

# Funções utilitárias
def get_indicator_info(indicator_key: str) -> Dict:
    """
    Retorna informações sobre um indicador específico
    
    Args:
        indicator_key: Chave do indicador (ex: 'ipca', 'selic')
    
    Returns:
        Dict com informações do indicador
    """
    return config.data_collection.indicators.get(indicator_key, {})

def get_available_indicators() -> List[str]:
    """
    Retorna lista de indicadores disponíveis
    
    Returns:
        Lista com chaves dos indicadores
    """
    return list(config.data_collection.indicators.keys())

def get_indicator_display_names() -> Dict[str, str]:
    """
    Retorna mapeamento de chaves para nomes de exibição
    
    Returns:
        Dict mapeando chave -> nome para exibição
    """
    return {
        key: info.get('name', key) 
        for key, info in config.data_collection.indicators.items()
    }

def get_date_range(years: int = None) -> tuple:
    """
    Calcula range de datas para coleta
    
    Args:
        years: Número de anos retroativos (opcional)
    
    Returns:
        Tuple (start_date, end_date) em formato string DD/MM/AAAA
    """
    if years is None:
        years = config.data_collection.default_years
    
    end_date = datetime.now().strftime('%d/%m/%Y')
    start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%d/%m/%Y')
    
    return start_date, end_date

# Validação de configuração
def validate_config() -> List[str]:
    """
    Valida a configuração do sistema
    
    Returns:
        Lista de erros encontrados (vazia se tudo OK)
    """
    errors = []
    
    # Validar configurações básicas
    if config.data_collection.default_years <= 0:
        errors.append("default_years deve ser maior que 0")
    
    if config.ml.min_data_points <= 0:
        errors.append("min_data_points deve ser maior que 0")
    
    if not (0 < config.ml.default_test_size < 1):
        errors.append("default_test_size deve estar entre 0 e 1")
    
    # Validar URLs
    if not config.data_collection.bcb_base_url.startswith('http'):
        errors.append("bcb_base_url deve ser uma URL válida")
    
    return errors

if __name__ == "__main__":
    # Teste da configuração
    errors = validate_config()
    if errors:
        print("Erros de configuração encontrados:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuração válida!")
        print(f"Versão: {config.version}")
        print(f"Indicadores disponíveis: {len(get_available_indicators())}")
        print(f"Modelos ML disponíveis: {len(config.ml.available_models)}")