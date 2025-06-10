# Arquivo: ml_models.py - VERSÃO FINAL LIMPA
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
import logging

logger = logging.getLogger(__name__)

class EconomicPredictor:
    def __init__(self):
        self.db_manager = None
        self.model_dir = 'models'
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def _get_db_manager(self):
        """Importação lazy do DatabaseManager"""
        if self.db_manager is None:
            try:
                from database.manager import DatabaseManager
                self.db_manager = DatabaseManager()
            except ImportError:
                try:
                    from database_manager import DatabaseManager
                    self.db_manager = DatabaseManager()
                except ImportError:
                    raise ImportError("Não foi possível importar DatabaseManager")
        return self.db_manager
    
    def prepare_data(self, target_indicator, window_size=6):
        """Prepara dados de forma simples"""
        try:
            db_manager = self._get_db_manager()
            target_data = db_manager.load_data(target_indicator)
            
            if target_data is None or target_data.empty:
                print(f"❌ Sem dados para {target_indicator}")
                return None, None, None
            
            # Limpar e ordenar
            df = target_data[['date', 'value']].copy()
            df = df.sort_values('date').reset_index(drop=True)
            df = df.drop_duplicates(subset=['date'], keep='last')
            
            # Criar features essenciais
            for i in range(1, window_size + 1):
                df[f'lag_{i}'] = df['value'].shift(i)
            
            df['ma_3'] = df['value'].rolling(window=3, min_periods=1).mean()
            df['ma_6'] = df['value'].rolling(window=6, min_periods=1).mean()
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter
            
            # Remover NaN
            df = df.dropna()
            
            if len(df) < 20:
                print(f"❌ Dados insuficientes: {len(df)}")
                return None, None, None
            
            # Separar features e target
            feature_columns = [col for col in df.columns if col not in ['date', 'value']]
            X = df[feature_columns]
            y = df['value']
            dates = df['date']
            
            print(f"✅ Dados prontos: {len(df)} registros, {len(feature_columns)} features")
            return X, y, dates
            
        except Exception as e:
            print(f"❌ Erro prepare_data: {e}")
            return None, None, None
    
    def train_model(self, target_indicator, model_type='random_forest', test_size=0.2):
        """Treina modelo de forma simples"""
        try:
            print(f"🚀 Treinando {target_indicator}...")
            
            X, y, dates = self.prepare_data(target_indicator)
            if X is None:
                return None
            
            # Divisão simples
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            # Escalonamento
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Modelo simples
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train_scaled, y_train)
            
            # Métricas básicas
            y_pred_test = model.predict(X_test_scaled)
            r2 = r2_score(y_test, y_pred_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            mae = np.mean(np.abs(y_test - y_pred_test))
            
            metrics = {
                'r2': r2,
                'rmse': rmse,
                'mae': mae,
                'samples_train': len(y_train),
                'samples_test': len(y_test)
            }
            
            print(f"✅ R²: {r2:.4f}, RMSE: {rmse:.4f}")
            
            # Salvar modelo
            model_data = {
                'model': model,
                'scaler': scaler,
                'feature_columns': list(X.columns),
                'target_indicator': target_indicator,
                'metrics': metrics
            }
            
            model_path = f"{self.model_dir}/{target_indicator}_random_forest_model.pkl"
            joblib.dump(model_data, model_path)
            print(f"✅ Modelo salvo: {model_path}")
            
            return metrics
            
        except Exception as e:
            print(f"❌ Erro no treinamento: {e}")
            logger.error(f"Erro train_model: {e}", exc_info=True)
            return None
    
    def predict_future(self, target_indicator, steps=6):
        """Previsão simples e robusta"""
        try:
            print(f"🔮 Prevendo {target_indicator}...")
            
            # Carregar modelo
            model_path = f"{self.model_dir}/{target_indicator}_random_forest_model.pkl"
            if not os.path.exists(model_path):
                print(f"❌ Modelo não encontrado: {model_path}")
                return None
            
            model_data = joblib.load(model_path)
            model = model_data['model']
            scaler = model_data['scaler']
            feature_columns = model_data['feature_columns']
            
            # Preparar dados históricos
            X, y, dates = self.prepare_data(target_indicator)
            if X is None:
                return None
            
            # Alinhar features
            for feature in feature_columns:
                if feature not in X.columns:
                    X[feature] = 0  # Valor padrão
            
            X_aligned = X[feature_columns]
            
            # Gerar previsões
            predictions = []
            prediction_dates = []
            base_date = dates.iloc[-1]
            
            # Usar última linha como base
            base_features = X_aligned.iloc[-1:].copy()
            
            for step in range(steps):
                # Escalar e prever
                scaled = scaler.transform(base_features)
                pred = model.predict(scaled)[0]
                predictions.append(pred)
                
                # Próxima data
                next_date = base_date + pd.DateOffset(months=step+1)
                prediction_dates.append(next_date)
            
            # Resultado
            future_df = pd.DataFrame({
                'date': prediction_dates,
                'value': predictions
            })
            
            print(f"✅ {steps} previsões geradas!")
            return future_df
            
        except Exception as e:
            print(f"❌ Erro na previsão: {e}")
            logger.error(f"Erro predict_future: {e}", exc_info=True)
            return None
    
    def get_feature_importance(self, target_indicator):
        """Análise de importância das features"""
        try:
            # Carregar modelo
            model_path = f"{self.model_dir}/{target_indicator}_random_forest_model.pkl"
            if not os.path.exists(model_path):
                print(f"❌ Modelo não encontrado para análise: {model_path}")
                return None
            
            model_data = joblib.load(model_path)
            model = model_data['model']
            feature_columns = model_data['feature_columns']
            
            # Random Forest tem feature_importances_
            if hasattr(model, 'feature_importances_'):
                importance_df = pd.DataFrame({
                    'feature': feature_columns,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                print(f"✅ Análise de importância calculada para {target_indicator}")
                return importance_df
            else:
                print(f"⚠️ Modelo não suporta análise de importância")
                return None
            
        except Exception as e:
            print(f"❌ Erro na análise de importância: {e}")
            return None