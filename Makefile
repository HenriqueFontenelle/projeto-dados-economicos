# Makefile - Comandos rápidos para testes

.PHONY: test test-fast test-ml test-db test-reports test-integration install-test-deps

# Instalar dependências de teste
install-test-deps:
	pip install -r requirements-test.txt

# Executar todos os testes
test:
	python test_system.py --verbose

# Teste rápido (apenas health e ML)
test-fast:
	python test_system.py --module health
	python test_system.py --module ml

# Testes específicos por módulo
test-health:
	python test_system.py --module health --verbose

test-db:
	python test_system.py --module database --verbose

test-ml:
	python test_system.py --module ml --verbose

test-reports:
	python test_system.py --module reports --verbose

test-integration:
	python test_system.py --module integration --verbose

# Testes com pytest (se disponível)
pytest:
	pytest test_system.py -v --cov=.

# Limpar arquivos temporários
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/