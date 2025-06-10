@echo off
echo 🧪 Sistema de Testes Automatizados - Dados Econômicos
echo ==================================================

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado! Instale Python 3.7+ para continuar.
    pause
    exit /b 1
)

echo Verificando arquivo de teste...
if not exist "test_system.py" (
    echo ❌ Arquivo test_system.py não encontrado!
    pause
    exit /b 1
)

echo.
echo Escolha o tipo de teste:
echo 1) 🏥 Testes de Saúde do Sistema
echo 2) 🗃️  Testes de Banco de Dados  
echo 3) 📊 Testes de Coleta de Dados
echo 4) 🤖 Testes de Machine Learning
echo 5) 📋 Testes de Relatórios
echo 6) 🔗 Testes de Integração
echo 7) 🚀 TODOS OS TESTES
echo 8) 📈 Teste Rápido (Health + ML)

set /p choice=Digite sua escolha (1-8): 

if "%choice%"=="1" python test_system.py --module health --verbose
if "%choice%"=="2" python test_system.py --module database --verbose
if "%choice%"=="3" python test_system.py --module collector --verbose
if "%choice%"=="4" python test_system.py --module ml --verbose
if "%choice%"=="5" python test_system.py --module reports --verbose
if "%choice%"=="6" python test_system.py --module integration --verbose
if "%choice%"=="7" python test_system.py --verbose
if "%choice%"=="8" (
    python test_system.py --module health
    python test_system.py --module ml
)

if errorlevel 1 (
    echo ❌ Alguns testes falharam. Verifique os logs acima.
    pause
    exit /b 1
) else (
    echo ✅ Testes concluídos com sucesso!
    pause
)