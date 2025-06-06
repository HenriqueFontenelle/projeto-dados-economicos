# data_collector.py - Versão melhorada para coleta robusta de dados
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import config, get_date_range

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BCBDataCollector:
    """
    Coletor de dados robusto do Banco Central do Brasil
    
    Melhorias implementadas:
    - Coleta de 10 anos de dados por padrão
    - Tratamento robusto de erros
    - Coleta paralela para melhor performance
    - Validação de dados
    - Retry automático em caso de falhas
    - Logging detalhado
    """
    
    def __init__(self):
        self.base_url = config.data_collection.bcb_base_url
        self.indicators = config.data_collection.indicators
        self.max_retries = config.data_collection.max_retries
        self.timeout = config.data_collection.request_timeout
        self.delay = config.data_collection.delay_between_requests
        
        # Estatísticas de coleta
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_records': 0
        }
    
    def _make_request(self, url: str, retries: int = None) -> Optional[List[Dict]]:
        """
        Faz requisição HTTP com retry automático
        
        Args:
            url: URL para requisição
            retries: Número de tentativas (opcional)
        
        Returns:
            Dados JSON ou None em caso de erro
        """
        if retries is None:
            retries = self.max_retries
        
        self.stats['total_requests'] += 1
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"Tentativa {attempt + 1} para URL: {url}")
                
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if data:
                    self.stats['successful_requests'] += 1
                    return data
                else:
                    logger.warning(f"Resposta vazia para URL: {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro na tentativa {attempt + 1}: {e}")
                if attempt < retries:
                    time.sleep(self.delay * (attempt + 1))  # Backoff exponencial
                else:
                    logger.error(f"Falha após {retries + 1} tentativas para URL: {url}")
                    self.stats['failed_requests'] += 1
            
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON: {e}")
                self.stats['failed_requests'] += 1
                break
        
        return None
    
    def _validate_data(self, df: pd.DataFrame, indicator: str) -> bool:
        """
        Valida os dados coletados
        
        Args:
            df: DataFrame com os dados
            indicator: Nome do indicador
        
        Returns:
            True se dados são válidos
        """
        if df is None or df.empty:
            logger.warning(f"DataFrame vazio para {indicator}")
            return False
        
        required_columns = ['date', 'value']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Colunas obrigatórias ausentes para {indicator}: {missing_columns}")
            return False
        
        # Verificar se há valores válidos
        valid_values = df['value'].notna().sum()
        if valid_values == 0:
            logger.warning(f"Nenhum valor válido encontrado para {indicator}")
            return False
        
        # Verificar formato de datas
        try:
            pd.to_datetime(df['date'])
        except Exception as e:
            logger.error(f"Erro no formato de datas para {indicator}: {e}")
            return False
        
        logger.info(f"Dados válidos para {indicator}: {len(df)} registros, {valid_values} valores válidos")
        return True
    
    def get_data(self, indicator: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        Obtém dados de um indicador específico
        
        Args:
            indicator: Nome do indicador (chave do dicionário self.indicators)
            start_date: Data inicial (formato 'DD/MM/AAAA', opcional)
            end_date: Data final (formato 'DD/MM/AAAA', opcional)
        
        Returns:
            DataFrame com os dados do indicador ou None
        """
        if indicator not in self.indicators:
            logger.error(f"Indicador '{indicator}' não reconhecido")
            return None
        
        # Usar configuração padrão se datas não fornecidas
        if start_date is None or end_date is None:
            start_date, end_date = get_date_range()
        
        # Construir URL
        serie_id = self.indicators[indicator]['series_id']
        url = f"{self.base_url}.{serie_id}/dados?formato=json"
        url += f"&dataInicial={start_date}&dataFinal={end_date}"
        
        logger.info(f"Coletando dados para {indicator} (série {serie_id}) de {start_date} a {end_date}")
        
        # Fazer requisição
        data = self._make_request(url)
        
        if not data:
            logger.error(f"Falha ao obter dados para {indicator}")
            return None
        
        try:
            # Converter para DataFrame
            df = pd.DataFrame(data)
            
            # Renomear colunas para padrão
            df.rename(columns={
                'data': 'date',
                'valor': 'value'
            }, inplace=True)
            
            # Converter tipos de dados
            df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Adicionar metadados
            df['indicator'] = indicator
            df['series_id'] = serie_id
            df['collected_at'] = datetime.now()
            
            # Ordenar por data
            df = df.sort_values('date').reset_index(drop=True)
            
            # Validar dados
            if self._validate_data(df, indicator):
                self.stats['total_records'] += len(df)
                logger.info(f"Coletados {len(df)} registros para {indicator}")
                return df
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erro ao processar dados para {indicator}: {e}")
            return None
    
    def collect_indicator_batch(self, indicators: List[str], start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """
        Coleta dados para múltiplos indicadores em paralelo
        
        Args:
            indicators: Lista de indicadores
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            Dict com DataFrames para cada indicador
        """
        results = {}
        
        def collect_single(indicator):
            try:
                return indicator, self.get_data(indicator, start_date, end_date)
            except Exception as e:
                logger.error(f"Erro ao coletar {indicator}: {e}")
                return indicator, None
        
        # Usar ThreadPoolExecutor para coleta paralela
        with ThreadPoolExecutor(max_workers=3) as executor:  # Limitado para não sobrecarregar a API
            future_to_indicator = {
                executor.submit(collect_single, indicator): indicator 
                for indicator in indicators
            }
            
            for future in as_completed(future_to_indicator):
                indicator, df = future.result()
                if df is not None:
                    results[indicator] = df
                    logger.info(f"✓ Concluído: {indicator}")
                else:
                    logger.warning(f"✗ Falhou: {indicator}")
                
                # Pequeno delay entre conclusões
                time.sleep(self.delay)
        
        return results
    
    def collect_all_data(self, last_n_years: int = None, indicators: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Coleta dados de todos os indicadores ou lista específica
        
        Args:
            last_n_years: Número de anos retroativos (padrão: configuração)
            indicators: Lista específica de indicadores (opcional)
        
        Returns:
            Dict com DataFrames para cada indicador
        """
        # Usar configuração padrão se não especificado
        if last_n_years is None:
            last_n_years = config.data_collection.default_years
        
        # Usar todos os indicadores se não especificado
        if indicators is None:
            indicators = list(self.indicators.keys())
        
        # Calcular datas
        start_date, end_date = get_date_range(last_n_years)
        
        logger.info(f"Iniciando coleta de {len(indicators)} indicadores para {last_n_years} anos")
        logger.info(f"Período: {start_date} a {end_date}")
        
        # Resetar estatísticas
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_records': 0
        }
        
        start_time = time.time()
        
        # Coletar dados
        results = self.collect_indicator_batch(indicators, start_date, end_date)
        
        # Estatísticas finais
        duration = time.time() - start_time
        success_rate = (self.stats['successful_requests'] / max(self.stats['total_requests'], 1)) * 100
        
        logger.info(f"Coleta concluída em {duration:.2f}s")
        logger.info(f"Indicadores coletados: {len(results)}/{len(indicators)}")
        logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
        logger.info(f"Total de registros: {self.stats['total_records']}")
        
        return results
    
    def get_collection_stats(self) -> Dict:
        """
        Retorna estatísticas da última coleta
        
        Returns:
            Dict com estatísticas
        """
        return self.stats.copy()
    
    def check_api_status(self) -> bool:
        """
        Verifica se a API do BCB está respondendo
        
        Returns:
            True se API está OK
        """
        test_url = f"{self.base_url}.433/dados?formato=json&dataInicial=01/01/2024&dataFinal=01/01/2024"
        
        try:
            response = requests.get(test_url, timeout=10)
            response.raise_for_status()
            logger.info("API do BCB está respondendo normalmente")
            return True
        except Exception as e:
            logger.error(f"API do BCB não está respondendo: {e}")
            return False
    
    def get_available_periods(self, indicator: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Obtém o período disponível para um indicador
        
        Args:
            indicator: Nome do indicador
        
        Returns:
            Tuple (data_inicial, data_final) ou None
        """
        if indicator not in self.indicators:
            return None
        
        # Fazer requisição sem filtro de data para ver período completo
        serie_id = self.indicators[indicator]['series_id']
        url = f"{self.base_url}.{serie_id}/dados?formato=json"
        
        data = self._make_request(url)
        
        if data:
            try:
                df = pd.DataFrame(data)
                df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
                return df['data'].min(), df['data'].max()
            except Exception as e:
                logger.error(f"Erro ao obter período para {indicator}: {e}")
        
        return None

# Função de conveniência para uso em outros módulos
def quick_collect(indicators: List[str] = None, years: int = None) -> Dict[str, pd.DataFrame]:
    """
    Função de conveniência para coleta rápida de dados
    
    Args:
        indicators: Lista de indicadores (opcional, usa todos se não especificado)
        years: Número de anos (opcional, usa configuração padrão)
    
    Returns:
        Dict com DataFrames dos indicadores
    """
    collector = BCBDataCollector()
    return collector.collect_all_data(years, indicators)

if __name__ == "__main__":
    # Teste da classe melhorada
    collector = BCBDataCollector()
    
    # Verificar status da API
    if not collector.check_api_status():
        print("⚠️ API do BCB não está respondendo. Tentando mesmo assim...")
    
    # Teste com alguns indicadores principais por 2 anos (para não demorar muito)
    test_indicators = ['ipca', 'selic', 'pib']
    print(f"\n📊 Testando coleta de {test_indicators} por 2 anos...")
    
    data = collector.collect_all_data(last_n_years=2, indicators=test_indicators)
    
    # Exibir resultados
    print(f"\n📈 Resultados da coleta:")
    for indicator, df in data.items():
        if df is not None:
            info = collector.indicators[indicator]
            print(f"\n{info['name']} ({indicator}):")
            print(f"  • Período: {df['date'].min().strftime('%d/%m/%Y')} a {df['date'].max().strftime('%d/%m/%Y')}")
            print(f"  • Registros: {len(df)}")
            print(f"  • Valores válidos: {df['value'].notna().sum()}")
            print(f"  • Último valor: {df['value'].iloc[-1]:.4f} {info.get('unit', '')}")
    
    # Exibir estatísticas
    stats = collector.get_collection_stats()
    print(f"\n📊 Estatísticas da coleta:")
    print(f"  • Total de requisições: {stats['total_requests']}")
    print(f"  • Requisições bem-sucedidas: {stats['successful_requests']}")
    print(f"  • Requisições com falha: {stats['failed_requests']}")
    print(f"  • Total de registros coletados: {stats['total_records']}")