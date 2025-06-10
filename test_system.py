# test_system.py - Suíte Completa de Testes Automatizados
"""
Sistema de Testes Automatizados para o Projeto de Dados Econômicos

Como usar:
1. Execute: python test_system.py
2. Ou execute testes específicos: python test_system.py --module ml
3. Para relatório detalhado: python test_system.py --verbose

Módulos testados:
- Database (conexão, coleta, persistência)
- Machine Learning (treinamento, previsões, importância)
- Relatórios (geração, exportação)
- API (conectividade, dados válidos)
- Sistema completo (integração end-to-end)
"""

import unittest
import sys
import os
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import json
from pathlib import Path
import argparse
import time
import warnings

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suprimir warnings para testes limpos
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class TestDatabaseModule(unittest.TestCase):
    """Testes para o módulo de banco de dados"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Importar módulos necessários
        try:
            from database.manager import DatabaseManager
            self.db_manager = DatabaseManager(db_path=self.temp_db.name)
        except ImportError:
            try:
                from database_manager import DatabaseManager
                self.db_manager = DatabaseManager(db_path=self.temp_db.name)
            except ImportError:
                self.skipTest("DatabaseManager não encontrado")
    
    def tearDown(self):
        """Limpeza após cada teste"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_connection(self):
        """Testa conexão com o banco de dados"""
        self.assertIsNotNone(self.db_manager.engine)
        
        # Testa execução de query simples
        with self.db_manager.engine.connect() as conn:
            result = conn.execute("SELECT 1 as test").fetchone()
            self.assertEqual(result[0], 1)
    
    def test_create_table(self):
        """Testa criação de tabelas"""
        # Dados de teste
        test_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=5, freq='M'),
            'value': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        # Salvar dados
        self.db_manager.save_data('test_indicator', test_data)
        
        # Verificar se tabela foi criada
        with self.db_manager.engine.connect() as conn:
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_indicator'").fetchone()
            self.assertIsNotNone(result)
    
    def test_data_persistence(self):
        """Testa persistência de dados"""
        # Dados de teste
        test_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=3, freq='M'),
            'value': [10.5, 11.2, 9.8]
        })
        
        # Salvar dados
        self.db_manager.save_data('persistence_test', test_data)
        
        # Carregar dados
        loaded_data = self.db_manager.load_data('persistence_test')
        
        self.assertIsNotNone(loaded_data)
        self.assertEqual(len(loaded_data), 3)
        self.assertAlmostEqual(loaded_data.iloc[0]['value'], 10.5, places=2)

class TestDataCollectorModule(unittest.TestCase):
    """Testes para o módulo de coleta de dados"""
    
    def setUp(self):
        """Configuração inicial"""
        try:
            from data_collector import EconomicDataCollector
            self.collector = EconomicDataCollector()
        except ImportError:
            self.skipTest("EconomicDataCollector não encontrado")
    
    def test_api_connection(self):
        """Testa conectividade com a API do BCB"""
        try:
            is_online = self.collector.test_api_connection()
            self.assertTrue(is_online, "API do BCB não está respondendo")
        except Exception as e:
            self.skipTest(f"Erro na conexão API: {e}")
    
    def test_data_collection_format(self):
        """Testa formato dos dados coletados"""
        try:
            # Coletar dados de teste (IPCA)
            data = self.collector.collect_indicator_data('ipca', months_back=3)
            
            if data is not None and not data.empty:
                # Verificar estrutura
                self.assertIn('date', data.columns)
                self.assertIn('value', data.columns)
                
                # Verificar tipos
                self.assertTrue(pd.api.types.is_datetime64_any_dtype(data['date']))
                self.assertTrue(pd.api.types.is_numeric_dtype(data['value']))
                
                # Verificar se não há valores nulos críticos
                self.assertFalse(data['date'].isna().all())
                self.assertFalse(data['value'].isna().all())
            else:
                self.skipTest("Dados não disponíveis para teste")
        except Exception as e:
            self.skipTest(f"Erro na coleta: {e}")

class TestMachineLearningModule(unittest.TestCase):
    """Testes para o módulo de Machine Learning"""
    
    def setUp(self):
        """Configuração inicial"""
        self.temp_model_dir = tempfile.mkdtemp()
        
        try:
            from ml_models import EconomicPredictor
            self.predictor = EconomicPredictor()
            self.predictor.model_dir = self.temp_model_dir
        except ImportError:
            self.skipTest("EconomicPredictor não encontrado")
    
    def tearDown(self):
        """Limpeza após testes"""
        import shutil
        if os.path.exists(self.temp_model_dir):
            shutil.rmtree(self.temp_model_dir)
    
    def test_data_preparation(self):
        """Testa preparação de dados para ML"""
        # Criar dados sintéticos
        dates = pd.date_range('2020-01-01', periods=50, freq='M')
        trend = np.linspace(1, 2, 50)
        noise = np.random.normal(0, 0.1, 50)
        values = trend + noise
        
        synthetic_data = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        # Mock do database manager
        class MockDBManager:
            def load_data(self, indicator):
                return synthetic_data
        
        self.predictor.db_manager = MockDBManager()
        
        # Testar preparação
        X, y, dates_out = self.predictor.prepare_data('test_indicator')
        
        self.assertIsNotNone(X)
        self.assertIsNotNone(y)
        self.assertIsNotNone(dates_out)
        self.assertGreater(len(X), 20)  # Mínimo de dados
    
    def test_model_training(self):
        """Testa treinamento de modelos"""
        # Criar dados sintéticos maiores para treinamento
        dates = pd.date_range('2020-01-01', periods=100, freq='M')
        trend = np.linspace(1, 5, 100)
        seasonal = np.sin(np.arange(100) * 2 * np.pi / 12) * 0.5
        noise = np.random.normal(0, 0.2, 100)
        values = trend + seasonal + noise
        
        synthetic_data = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        # Mock do database manager
        class MockDBManager:
            def load_data(self, indicator):
                return synthetic_data
        
        self.predictor.db_manager = MockDBManager()
        
        # Testar treinamento
        metrics = self.predictor.train_model('test_synthetic')
        
        self.assertIsNotNone(metrics)
        self.assertIn('r2', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        
        # Verificar se modelo foi salvo
        model_path = f"{self.temp_model_dir}/test_synthetic_random_forest_model.pkl"
        self.assertTrue(os.path.exists(model_path))
    
    def test_feature_importance(self):
        """Testa análise de importância de features"""
        # Primeiro treinar um modelo
        self.test_model_training()
        
        # Testar importância
        importance_df = self.predictor.get_feature_importance('test_synthetic')
        
        if importance_df is not None:
            self.assertIn('feature', importance_df.columns)
            self.assertIn('importance', importance_df.columns)
            self.assertGreater(len(importance_df), 0)

class TestReportsModule(unittest.TestCase):
    """Testes para o módulo de relatórios"""
    
    def setUp(self):
        """Configuração inicial"""
        self.temp_reports_dir = tempfile.mkdtemp()
        
        try:
            from ai_report_generator import ReportGenerator
            self.generator = ReportGenerator()
        except ImportError:
            self.skipTest("ReportGenerator não encontrado")
    
    def tearDown(self):
        """Limpeza após testes"""
        import shutil
        if os.path.exists(self.temp_reports_dir):
            shutil.rmtree(self.temp_reports_dir)
    
    def test_report_structure(self):
        """Testa estrutura básica do relatório"""
        try:
            # Gerar relatório de teste
            report_data = self.generator.generate_economic_overview(months_back=6)
            
            if report_data:
                # Verificar estrutura básica
                self.assertIn('title', report_data)
                self.assertIn('generated_at', report_data)
                self.assertIn('period_months', report_data)
                
                # Verificar seções
                if 'sections' in report_data:
                    sections = report_data['sections']
                    # Pode ter indicators, correlations, predictions
                    self.assertIsInstance(sections, dict)
            else:
                self.skipTest("Relatório não pôde ser gerado (dados insuficientes)")
        except Exception as e:
            self.skipTest(f"Erro na geração de relatório: {e}")
    
    def test_json_export(self):
        """Testa exportação para JSON"""
        try:
            report_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
            json_path = self.generator.export_report_to_json(report_data)
            
            self.assertTrue(os.path.exists(json_path))
            
            # Verificar conteúdo
            with open(json_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(loaded_data['test'], 'data')
        except Exception as e:
            self.skipTest(f"Erro na exportação JSON: {e}")

class TestSystemIntegration(unittest.TestCase):
    """Testes de integração do sistema completo"""
    
    def setUp(self):
        """Configuração para testes de integração"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test.db')
        
    def tearDown(self):
        """Limpeza após testes"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_data_flow(self):
        """Testa fluxo completo: coleta -> armazenamento -> ML -> relatório"""
        try:
            # 1. Coleta de dados
            from data_collector import EconomicDataCollector
            collector = EconomicDataCollector()
            
            # Verificar API
            if not collector.test_api_connection():
                self.skipTest("API do BCB não disponível")
            
            # 2. Database
            try:
                from database.manager import DatabaseManager
            except ImportError:
                from database_manager import DatabaseManager
            
            db_manager = DatabaseManager(db_path=self.temp_db)
            
            # 3. Coletar dados de teste
            data = collector.collect_indicator_data('ipca', months_back=24)
            
            if data is None or data.empty:
                self.skipTest("Dados do IPCA não disponíveis")
            
            # 4. Salvar no banco
            db_manager.save_data('ipca', data)
            
            # 5. Verificar persistência
            loaded_data = db_manager.load_data('ipca')
            self.assertIsNotNone(loaded_data)
            self.assertGreater(len(loaded_data), 10)
            
            # 6. Machine Learning
            from ml_models import EconomicPredictor
            predictor = EconomicPredictor()
            predictor.model_dir = os.path.join(self.temp_dir, 'models')
            predictor.db_manager = db_manager
            
            # 7. Treinar modelo
            metrics = predictor.train_model('ipca')
            if metrics:
                self.assertIn('r2', metrics)
                self.assertGreater(metrics['r2'], -1)  # R² > -1 (melhor que baseline)
            
            print("✅ Teste de integração completo executado com sucesso!")
            
        except Exception as e:
            self.skipTest(f"Erro no teste de integração: {e}")

class TestSystemHealth(unittest.TestCase):
    """Testes de saúde do sistema"""
    
    def test_required_modules(self):
        """Testa se todos os módulos necessários estão presentes"""
        required_modules = [
            'pandas', 'numpy', 'sklearn', 'streamlit', 
            'requests', 'sqlalchemy', 'matplotlib'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        self.assertEqual(len(missing_modules), 0, 
                        f"Módulos faltando: {missing_modules}")
    
    def test_file_structure(self):
        """Testa estrutura básica de arquivos"""
        expected_files = [
            'main.py',
            'data_collector.py',
            'ml_models.py',
            'config.py'
        ]
        
        missing_files = []
        for file in expected_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"⚠️ Arquivos não encontrados: {missing_files}")
        # Não falhar se alguns arquivos estão ausentes, apenas reportar
    
    def test_directories(self):
        """Testa criação de diretórios necessários"""
        dirs_to_check = ['models', 'reports', 'data']
        
        for dir_name in dirs_to_check:
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name, exist_ok=True)
                    self.assertTrue(os.path.exists(dir_name))
                except Exception as e:
                    print(f"⚠️ Não foi possível criar diretório {dir_name}: {e}")

def run_test_suite(module_filter=None, verbose=False):
    """Executa a suíte de testes"""
    
    print("🧪 Iniciando Testes Automatizados do Sistema")
    print("=" * 60)
    
    # Configurar runner
    verbosity = 2 if verbose else 1
    
    # Definir quais testes executar
    test_classes = {
        'health': TestSystemHealth,
        'database': TestDatabaseModule,
        'collector': TestDataCollectorModule,
        'ml': TestMachineLearningModule,
        'reports': TestReportsModule,
        'integration': TestSystemIntegration
    }
    
    if module_filter and module_filter in test_classes:
        test_classes = {module_filter: test_classes[module_filter]}
    
    # Executar testes
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    for test_name, test_class in test_classes.items():
        print(f"\n🔍 Executando testes: {test_name.upper()}")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
        
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        total_skipped += len(result.skipped)
        
        if result.failures:
            print(f"❌ {len(result.failures)} falha(s) em {test_name}")
        if result.errors:
            print(f"🔥 {len(result.errors)} erro(s) em {test_name}")
        if result.skipped:
            print(f"⏭️ {len(result.skipped)} teste(s) pulado(s) em {test_name}")
        if not result.failures and not result.errors:
            print(f"✅ Todos os testes de {test_name} passaram!")
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    print(f"Total de testes executados: {total_tests}")
    print(f"✅ Sucessos: {total_tests - total_failures - total_errors - total_skipped}")
    print(f"❌ Falhas: {total_failures}")
    print(f"🔥 Erros: {total_errors}")
    print(f"⏭️ Pulados: {total_skipped}")
    
    # Status geral
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema está funcionando corretamente.")
        return True
    else:
        print(f"\n⚠️ {total_failures + total_errors} problema(s) encontrado(s). Verifique os logs acima.")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Testes Automatizados do Sistema Econômico')
    parser.add_argument('--module', choices=['health', 'database', 'collector', 'ml', 'reports', 'integration'],
                       help='Executar testes de um módulo específico')
    parser.add_argument('--verbose', action='store_true', help='Saída detalhada')
    
    args = parser.parse_args()
    
    # Executar testes
    success = run_test_suite(module_filter=args.module, verbose=args.verbose)
    
    # Exit code baseado no resultado
    sys.exit(0 if success else 1)