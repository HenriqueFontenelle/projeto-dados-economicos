#!/bin/bash
# run_tests.sh - Script para executar testes do sistema

echo "🧪 Sistema de Testes Automatizados - Dados Econômicos"
echo "=================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se Python está disponível
if ! command -v python &> /dev/null; then
    log_error "Python não encontrado. Instale Python 3.7+ para continuar."
    exit 1
fi

# Verificar se o arquivo de teste existe
if [ ! -f "test_system.py" ]; then
    log_error "Arquivo test_system.py não encontrado!"
    exit 1
fi

log_info "Verificando dependências..."

# Verificar dependências principais
python -c "import pandas, numpy, sklearn, streamlit, requests, sqlalchemy" 2>/dev/null
if [ $? -ne 0 ]; then
    log_warning "Algumas dependências podem estar faltando. Execute: pip install -r requirements.txt"
fi

log_success "Dependências verificadas!"

# Menu de opções
echo ""
echo "Escolha o tipo de teste:"
echo "1) 🏥 Testes de Saúde do Sistema"
echo "2) 🗃️  Testes de Banco de Dados"
echo "3) 📊 Testes de Coleta de Dados"
echo "4) 🤖 Testes de Machine Learning"
echo "5) 📋 Testes de Relatórios"
echo "6) 🔗 Testes de Integração"
echo "7) 🚀 TODOS OS TESTES"
echo "8) 📈 Teste Rápido (Health + ML)"

read -p "Digite sua escolha (1-8): " choice

case $choice in
    1)
        log_info "Executando testes de saúde do sistema..."
        python test_system.py --module health --verbose
        ;;
    2)
        log_info "Executando testes de banco de dados..."
        python test_system.py --module database --verbose
        ;;
    3)
        log_info "Executando testes de coleta de dados..."
        python test_system.py --module collector --verbose
        ;;
    4)
        log_info "Executando testes de machine learning..."
        python test_system.py --module ml --verbose
        ;;
    5)
        log_info "Executando testes de relatórios..."
        python test_system.py --module reports --verbose
        ;;
    6)
        log_info "Executando testes de integração..."
        python test_system.py --module integration --verbose
        ;;
    7)
        log_info "Executando TODOS os testes..."
        python test_system.py --verbose
        ;;
    8)
        log_info "Executando teste rápido..."
        python test_system.py --module health
        python test_system.py --module ml
        ;;
    *)
        log_error "Escolha inválida!"
        exit 1
        ;;
esac

# Verificar resultado
if [ $? -eq 0 ]; then
    log_success "Testes concluídos com sucesso!"
    echo ""
    echo "💡 Dicas:"
    echo "- Execute testes regularmente para detectar problemas cedo"
    echo "- Use 'python test_system.py --help' para mais opções"
    echo "- Considere integrar com CI/CD para testes automáticos"
else
    log_error "Alguns testes falharam. Verifique os logs acima."
    exit 1
fi