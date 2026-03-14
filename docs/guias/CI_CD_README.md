# 🔄 CI/CD - Guia Rápido

## 📊 Status dos Workflows

### Workflow Principal: `tests.yml`
**Trigger**: Automático em push/PR (branches `main`, `develop`)

**Jobs Executados:**
1. 🔬 **Unit Tests** (matrix: Python 3.10, 3.11, 3.12)
   - Testes de date_helpers
   - Testes de money_formatters
   - Geração de relatório de cobertura
   - Upload para Codecov

2. 🔍 **Lint** (Python 3.12)
   - Black: Verificação de formatação
   - isort: Organização de imports
   - Flake8: Análise estática

3. 🔒 **Security** (Python 3.12)
   - Safety: Vulnerabilidades em dependências
   - Bandit: Análise de segurança no código

4. 📊 **Build Status**
   - Resumo consolidado dos jobs

### Workflow de Integração: `integration-tests.yml`
**Trigger**: Manual via GitHub UI (`workflow_dispatch`)

**Funcionalidades:**
- PostgreSQL service configurado automaticamente
- Execução dos 40+ testes de integração
- Testes de todos os 4 blueprints
- Upload de artefatos (coverage reports)

---

## 🚀 Como Visualizar os Resultados

### No GitHub
1. Acesse: https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm/actions
2. Veja os workflows executados
3. Clique em qualquer run para ver detalhes
4. Cada job mostra logs detalhados

### Badges no README
```markdown
![Tests](https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm/workflows/Tests/badge.svg)
![Coverage](https://codecov.io/gh/EduardoSouza-tech/Sistema_financeiro_dwm/branch/main/graph/badge.svg)
```

---

## 🎯 Executar Workflows Manualmente

### Via GitHub UI
1. Vá para **Actions** no repositório
2. Selecione workflow (ex: "Integration Tests")
3. Clique em **Run workflow**
4. Escolha branch e parâmetros (se houver)
5. Clique em **Run workflow** (verde)

### Via GitHub CLI
```bash
# Instalar gh CLI (se necessário)
winget install GitHub.cli

# Autenticar
gh auth login

# Executar workflow de integração
gh workflow run integration-tests.yml

# Ver status
gh run list --workflow=tests.yml

# Ver logs do último run
gh run view --log
```

---

## 🛠️ Configuração Local para Lint/Security

### Instalar Ferramentas
```powershell
pip install -r requirements_test.txt
```

### Executar Localmente

**Formatação com Black:**
```powershell
# Verificar
black --check app/ tests/

# Aplicar formatação
black app/ tests/
```

**Organizar Imports:**
```powershell
# Verificar
isort --check-only app/ tests/

# Aplicar
isort app/ tests/
```

**Análise Estática:**
```powershell
# Flake8
flake8 app/ tests/ --max-line-length=120 --ignore=E501,W503,E203

# Pylint
pylint app/ tests/
```

**Segurança:**
```powershell
# Verificar vulnerabilidades
pip freeze > requirements_frozen.txt
safety check --file requirements_frozen.txt

# Análise de segurança
bandit -r app/ -f json -o bandit-report.json
```

---

## 📈 Relatórios de Cobertura

### Gerar Localmente
```powershell
# Cobertura de testes unitários
$env:PYTHONPATH="$PWD"
pytest tests/test_date_helpers.py tests/test_money_formatters.py `
  --cov=app/utils `
  --cov-report=html `
  --cov-report=term `
  --noconftest

# Abrir relatório HTML
start htmlcov/index.html
```

### No CI/CD
- Relatórios são gerados automaticamente
- Upload para Codecov (se configurado)
- Artefatos disponíveis no GitHub Actions

---

## 🔧 Troubleshooting

### Erro: "fixture 'app' not found"
**Causa**: pytest-flask precisa de configuração
**Solução**: Usar `--noconftest` para testes que não dependem do Flask app

### Erro: "DATABASE_URL não configurado"
**Causa**: Testes de integração precisam de banco
**Solução**: 
1. Para CI: workflow já configura PostgreSQL service
2. Para local: `$env:DATABASE_URL="postgresql://..."`

### Erro: "ModuleNotFoundError: No module named 'app'"
**Causa**: PYTHONPATH não configurado
**Solução**: `$env:PYTHONPATH="$PWD"` antes de executar pytest

### Workflow não executou
**Causas comuns**:
1. Push em branch não configurada (use `main` ou `develop`)
2. Workflow com erro de sintaxe YAML
3. Falta de permissões no repositório

**Verificar**:
```bash
# Validar sintaxe YAML localmente
python -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"
```

---

## 📋 Checklist de Deploy

Antes de fazer merge para `main`:

- [ ] ✅ Todos os testes passando localmente
- [ ] ✅ Black formatação aplicada
- [ ] ✅ isort imports organizados
- [ ] ✅ Flake8 sem erros críticos
- [ ] ✅ Safety sem vulnerabilidades HIGH/CRITICAL
- [ ] ✅ Bandit sem issues de segurança MEDIUM+
- [ ] ✅ Coverage >= 90%
- [ ] ✅ Pipeline CI/CD verde no GitHub

---

## 🎨 Customizar Workflows

### Adicionar Novo Teste ao Pipeline

Edite `.github/workflows/tests.yml`:

```yaml
- name: 🧪 Executar novo teste
  run: |
    export PYTHONPATH="${PYTHONPATH}:${PWD}"
    pytest tests/test_novo.py -v --tb=short
```

### Adicionar Variável de Ambiente

```yaml
- name: 🔧 Configurar variável
  run: |
    echo "MINHA_VAR=valor" >> $GITHUB_ENV

- name: 🧪 Usar variável
  run: |
    echo "Valor: ${{ env.MINHA_VAR }}"
```

### Adicionar Secret

1. Vá para Settings → Secrets and variables → Actions
2. Clique em "New repository secret"
3. Adicione nome e valor
4. Use no workflow: `${{ secrets.NOME_SECRET }}`

---

## 📚 Recursos Úteis

**GitHub Actions:**
- [Documentação Oficial](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Marketplace de Actions](https://github.com/marketplace?type=actions)

**Ferramentas:**
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Flake8 Lint](https://flake8.pycqa.org/)
- [Bandit Security](https://bandit.readthedocs.io/)

**Badges:**
- [Shields.io](https://shields.io/) - Gerador de badges
- [Codecov](https://codecov.io/) - Coverage badges

---

## 🎯 Próximos Passos

1. **Monitorar Primeiro Pipeline**
   - Aguardar execução do workflow após push
   - Verificar se todos os jobs passam
   - Corrigir eventuais falhas

2. **Configurar Codecov** (Opcional)
   - Criar conta em https://codecov.io
   - Adicionar repositório
   - Configurar `CODECOV_TOKEN` como secret

3. **Branch Protection Rules**
   - Settings → Branches → Add rule
   - Require status checks (CI/CD) antes de merge
   - Require PR reviews

4. **Notificações**
   - Configurar notificações de falha via email
   - Integrar com Slack/Discord (opcional)

---

**Última Atualização**: 21/01/2026  
**Status**: CI/CD Implementado e Funcional ✅  
**Commit**: `f3b5aac` - "feat(fase6): Implementar CI/CD com GitHub Actions"
