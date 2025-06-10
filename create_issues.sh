#!/bin/bash

echo "🚀 Criando Issues do Projeto de Dados Econômicos..."

# Issue 1: Bug Análise de Importância
echo "📝 Criando Issue #1: Bug Análise de Importância..."
gh issue create \
  --title "🐛 [BUG] Análise de Importância de Features Não Funciona" \
  --body "## 🐛 Problema
A função \`get_feature_importance()\` no módulo \`ml_models.py\` retorna \`None\` ao tentar analisar importância das features para o indicador IPCA.

## 🔍 Sintomas
- Interface mostra: \`⚠️ Não foi possível calcular importância das features\`
- Função retorna \`None\` em vez do DataFrame esperado
- Sistema de ML treina normalmente, mas análise falha

## 📊 Impacto
- **Criticidade:** Alta
- **Módulos afetados:** Machine Learning, Interface Streamlit
- **Funcionalidade perdida:** Análise de quais variáveis mais influenciam previsões

## 🔧 Investigação Necessária
- [ ] Verificar estrutura do modelo salvo
- [ ] Analisar função \`get_feature_importance()\`
- [ ] Testar com diferentes indicadores
- [ ] Verificar compatibilidade Random Forest

## 📋 Critérios de Aceitação
- [ ] \`get_feature_importance()\` retorna DataFrame válido
- [ ] Interface mostra ranking de importância
- [ ] Funciona para todos os indicadores treinados
- [ ] Log de sucesso: \`✅ Análise de importância calculada\`" \
  --label "bug,machine-learning,high-priority"

# Issue 2: Bug Expanders Aninhados
echo "📝 Criando Issue #2: Bug Expanders Aninhados..."
gh issue create \
  --title "🐛 [BUG] Expanders Aninhados Quebram Interface de Relatórios" \
  --body "## 🐛 Problema
Interface de relatórios apresenta erro: \`Expanders may not be nested inside other expanders\` ao tentar gerar relatórios.

## 🔍 Localização
- **Arquivo:** \`modules/reports_module.py\`
- **Linha:** ~371
- **Função:** \`_display_report_results()\`

## 📊 Impacto
- Sistema de relatórios completamente inoperante
- Usuários não conseguem gerar análises automáticas
- Erro bloqueia fluxo completo de geração de insights

## 🔧 Causa Raiz
\`\`\`python
# PROBLEMA: Expander dentro de expander
with st.expander(f\"🔍 {indicator_name}\"):
    # ... código ...
    with st.expander(\"📈 Dados Técnicos\"):  # ← ERRO AQUI
        # ... conteúdo ...
\`\`\`

## 💡 Solução Proposta
Substituir expander interno por \`st.subheader()\` ou \`st.markdown()\`

## 📋 Critérios de Aceitação
- [ ] Relatórios geram sem erros de interface
- [ ] Informações técnicas ainda visíveis
- [ ] Layout mantém usabilidade
- [ ] Compatibilidade com Streamlit Cloud" \
  --label "bug,streamlit,reports,medium-priority"

# Issue 3: Bug Métricas Faltando
echo "📝 Criando Issue #3: Bug Métricas MAE/MSE..."
gh issue create \
  --title "🐛 [BUG] Métricas MAE e MSE Faltando no Treinamento" \
  --body "## 🐛 Problema
Interface de ML apresenta erros \`KeyError: 'mae'\` e \`KeyError: 'mse'\` durante exibição de métricas de treinamento.

## 🔍 Detalhes Técnicos
- **Erro 1:** \`st.metric(\"MAE\", f\"{metrics['mae']:.4f}\")\` → KeyError
- **Erro 2:** \`st.metric(\"MSE\", f\"{metrics['mse']:.6f}\")\` → KeyError
- **Causa:** \`ml_models.py\` retorna apenas R² e RMSE

## 📊 Impacto
- Treinamento funciona, mas interface quebra na exibição
- Usuários não veem métricas completas
- Experiência de usuário prejudicada

## 🔧 Solução
Adicionar cálculo de MAE e MSE no retorno de métricas

## 📋 Critérios de Aceitação
- [ ] Interface exibe todas as métricas sem erro
- [ ] MAE e MSE calculados corretamente
- [ ] Compatibilidade mantida com código existente" \
  --label "bug,machine-learning,interface,low-priority"

# Issue 4: Feature Testes Automatizados
echo "📝 Criando Issue #4: Feature Testes Automatizados..."
gh issue create \
  --title "🚀 [FEATURE] Implementar Sistema de Testes Automatizados" \
  --body "## 🎯 Objetivo
Implementar suite completa de testes automatizados para garantir qualidade e robustez do sistema de análise econômica.

## 💡 Motivação
- Detectar problemas antes que afetem usuários
- Facilitar manutenção e evolução do código
- Preparar sistema para CI/CD
- Documentar comportamento esperado

## 📋 Funcionalidades Requeridas

### 🏥 Testes de Saúde do Sistema
- [ ] Verificar dependências instaladas
- [ ] Validar estrutura de arquivos
- [ ] Testar criação de diretórios

### 🗃️ Testes de Banco de Dados
- [ ] Conexão SQLite
- [ ] Criação de tabelas
- [ ] Persistência de dados

### 🤖 Testes de Machine Learning
- [ ] Preparação de dados
- [ ] Treinamento de modelos
- [ ] Geração de previsões
- [ ] Análise de importância

### 📋 Testes de Relatórios
- [ ] Geração de estrutura
- [ ] Exportação JSON/HTML

### 🔗 Testes de Integração
- [ ] Fluxo completo end-to-end

## 📊 Métricas de Sucesso
- [ ] Cobertura de 6 módulos principais
- [ ] 20+ testes individuais
- [ ] Execução em < 2 minutos
- [ ] Scripts multiplataforma funcionando" \
  --label "enhancement,testing,ci-cd,high-priority"

# Issue 5: Refactor Simplificação ML
echo "📝 Criando Issue #5: Refactor Simplificação ML..."
gh issue create \
  --title "♻️ [REFACTOR] Simplificar Módulo ML para Maior Robustez" \
  --body "## 🎯 Objetivo
Refatorar módulo de Machine Learning de múltiplos algoritmos para foco em Random Forest, aumentando robustez e simplicidade.

## 🔍 Problemas Atuais
- **Complexidade excessiva:** 5 algoritmos diferentes causam bugs
- **Manutenção difícil:** Cada algoritmo tem peculiaridades
- **Random Forest superior:** Performa melhor que outros na maioria dos casos
- **Debugging complexo:** Muitos pontos de falha

## 📊 Refatoração Proposta
Manter apenas RandomForestRegressor com configuração otimizada

## 📋 Benefícios Esperados
- [ ] Redução de 80% na complexidade do código
- [ ] Eliminação de bugs relacionados a algoritmos específicos
- [ ] Manutenção mais fácil
- [ ] Performance consistente
- [ ] Feature importance nativa
- [ ] Paralelização automática" \
  --label "refactor,machine-learning,optimization"

# Issue 6: Documentação Técnica
echo "📝 Criando Issue #6: Documentação Técnica..."
gh issue create \
  --title "📚 [DOCS] Criar Documentação Técnica Completa" \
  --body "## 🎯 Objetivo
Criar documentação técnica abrangente do sistema, incluindo histórico de desenvolvimento, arquitetura e guias de uso.

## 📋 Documentos Necessários

### 📖 DOCUMENTATION.md
- [ ] Histórico completo de desenvolvimento
- [ ] Problemas identificados e soluções
- [ ] Arquitetura detalhada do sistema
- [ ] Algoritmos de ML explicados
- [ ] Uso de Inteligência Artificial
- [ ] Processo de treinamento
- [ ] Guia de testes automatizados

### 🚀 QUICK_TEST_GUIDE.md
- [ ] Comandos essenciais
- [ ] Checklist pré-teste
- [ ] Interpretação de resultados

### 📋 README.md
- [ ] Visão geral do projeto
- [ ] Instruções de instalação
- [ ] Links para demo e documentação

## 📊 Critérios de Qualidade
- [ ] Linguagem técnica mas acessível
- [ ] Exemplos práticos e código
- [ ] Diagramas de arquitetura" \
  --label "documentation,enhancement"

echo "✅ Todas as issues foram criadas com sucesso!"
echo "🔗 Ver issues: gh issue list"