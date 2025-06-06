# diagnostico_periodo.py
import requests
import pandas as pd
from datetime import datetime, timedelta

# Definir indicadores para teste
INDICATORS_TEST = {
    'ipca': {'id': 433, 'name': 'Inflação (IPCA)'},
    'pib': {'id': 4380, 'name': 'PIB Real'},
    'selic': {'id': 11, 'name': 'Taxa SELIC'},
    'selic_meta': {'id': 4189, 'name': 'Meta SELIC'}
}

def verificar_disponibilidade_dados():
    """Verifica disponibilidade de dados para cada indicador"""
    base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    
    # Definir período de 10 anos
    end_date = datetime.now().strftime('%d/%m/%Y')
    start_date = (datetime.now() - timedelta(days=365 * 10)).strftime('%d/%m/%Y')
    
    print(f"🔍 DIAGNÓSTICO DE DADOS - PERÍODO DE 10 ANOS")
    print(f"📅 Verificando dados de {start_date} até {end_date}")
    print("=" * 60)
    
    for indicator, info in INDICATORS_TEST.items():
        serie_id = info['id']
        name = info['name']
        
        print(f"\n📊 {name} (Série {serie_id}):")
        
        try:
            # Fazer requisição SEM filtro de data primeiro
            url_total = f"{base_url}.{serie_id}/dados?formato=json"
            response_total = requests.get(url_total, timeout=30)
            response_total.raise_for_status()
            data_total = response_total.json()
            
            if data_total:
                df_total = pd.DataFrame(data_total)
                df_total['data'] = pd.to_datetime(df_total['data'], format='%d/%m/%Y')
                
                primeiro_registro = df_total['data'].min()
                ultimo_registro = df_total['data'].max()
                total_registros = len(df_total)
                anos_disponivel = (ultimo_registro - primeiro_registro).days / 365
                
                print(f"   📈 Total de registros disponíveis: {total_registros}")
                print(f"   📅 Período completo: {primeiro_registro.strftime('%d/%m/%Y')} a {ultimo_registro.strftime('%d/%m/%Y')}")
                print(f"   ⏱️  Anos de dados disponíveis: {anos_disponivel:.1f}")
                
                # Fazer requisição COM filtro de 10 anos
                url_filtered = f"{base_url}.{serie_id}/dados?formato=json&dataInicial={start_date}&dataFinal={end_date}"
                response_filtered = requests.get(url_filtered, timeout=30)
                
                if response_filtered.status_code == 200:
                    data_filtered = response_filtered.json()
                    if data_filtered:
                        registros_10_anos = len(data_filtered)
                        print(f"   🎯 Registros últimos 10 anos: {registros_10_anos}")
                        
                        # Verificar se conseguimos os 10 anos completos
                        if anos_disponivel >= 10:
                            print(f"   ✅ DADOS COMPLETOS: 10 anos disponíveis")
                        else:
                            print(f"   ⚠️  DADOS LIMITADOS: Apenas {anos_disponivel:.1f} anos disponíveis")
                    else:
                        print(f"   ❌ Nenhum dado retornado para os últimos 10 anos")
                else:
                    print(f"   ❌ Erro na requisição filtrada: {response_filtered.status_code}")
                    
                # Teste com 5 anos para comparação
                start_5y = (datetime.now() - timedelta(days=365 * 5)).strftime('%d/%m/%Y')
                url_5y = f"{base_url}.{serie_id}/dados?formato=json&dataInicial={start_5y}&dataFinal={end_date}"
                response_5y = requests.get(url_5y, timeout=30)
                
                if response_5y.status_code == 200:
                    data_5y = response_5y.json()
                    if data_5y:
                        registros_5_anos = len(data_5y)
                        print(f"   📊 Registros últimos 5 anos: {registros_5_anos}")
                        
            else:
                print(f"   ❌ Nenhum dado disponível para esta série")
                
        except Exception as e:
            print(f"   ❌ Erro na consulta: {str(e)}")
        
        print("-" * 40)
    
    print(f"\n{'='*60}")
    print("🎯 RECOMENDAÇÃO:")
    print("Execute este diagnóstico para identificar limitações específicas.")

if __name__ == "__main__":
    verificar_disponibilidade_dados()