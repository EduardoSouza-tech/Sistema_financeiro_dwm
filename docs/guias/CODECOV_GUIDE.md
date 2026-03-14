# 📊 Guia de Configuração do Codecov

## Status Atual
- ✅ codecov.yml configurado
- ✅ Workflow atualizado para enviar cobertura
- ⏳ **Conta Codecov**: Precisa ser configurada manualmente

---

## 🎯 O que é Codecov?

**Codecov** é uma ferramenta que:
- 📊 Visualiza cobertura de código graficamente
- 📈 Rastreia evolução da cobertura ao longo do tempo
- 💬 Comenta automaticamente em PRs com mudanças na cobertura
- 🎖️ Gera badges de cobertura para o README
- 🔍 Mostra quais linhas não estão cobertas

---

## 🔧 Como Configurar

### Passo 1: Criar Conta no Codecov

1. Acesse: https://about.codecov.io/sign-up/
2. Clique em **"Sign up with GitHub"**
3. Autorize o Codecov a acessar seu GitHub
4. Selecione **Free plan** (suficiente para projetos open source)

### Passo 2: Adicionar Repositório

1. No dashboard do Codecov, clique em **"Add new repository"**
2. Procure por: `Sistema_financeiro_dwm`
3. Clique em **"Setup repo"**
4. Codecov fornecerá um **CODECOV_TOKEN**

### Passo 3: Adicionar Token ao GitHub

1. Vá para: https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm/settings/secrets/actions
2. Clique em **"New repository secret"**
3. Preencha:
   - **Name**: `CODECOV_TOKEN`
   - **Secret**: Cole o token fornecido pelo Codecov
4. Clique em **"Add secret"**

### Passo 4: Verificar Integração

1. Faça um push para o repositório (já foi feito com commit 2dac5b7)
2. GitHub Actions executará e enviará cobertura para Codecov
3. Acesse: https://app.codecov.io/gh/EduardoSouza-tech/Sistema_financeiro_dwm
4. Você verá o relatório de cobertura com gráficos

---

## 📊 Arquivos Configurados

### 1. codecov.yml (Raiz do Projeto)

```yaml
codecov:
  require_ci_to_pass: yes
  notify:
    wait_for_ci: yes

coverage:
  precision: 2
  round: down
  range: "70...100"
  status:
    project:
      default:
        target: 95%          # Meta de cobertura geral
        threshold: 2%         # Tolerância de queda
        if_ci_failed: error
    patch:
      default:
        target: 90%          # Meta para novo código
        threshold: 5%

comment:
  layout: "reach,diff,flags,tree,files"
  behavior: default
  require_changes: no

ignore:
  - "tests/"              # Não medir cobertura dos testes
  - "**/__pycache__/"
  - "htmlcov/"
  - "migration*.py"       # Scripts de migração
```

### 2. .github/workflows/tests.yml

Já configurado para enviar cobertura:

```yaml
- name: 📤 Upload para Codecov
  uses: codecov/codecov-action@v3
  if: matrix.python-version == '3.12'
  with:
    file: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: false
```

---

## 🎖️ Adicionar Badge ao README

Após configurar, adicione o badge ao README.md:

```markdown
[![codecov](https://codecov.io/gh/EduardoSouza-tech/Sistema_financeiro_dwm/branch/main/graph/badge.svg)](https://codecov.io/gh/EduardoSouza-tech/Sistema_financeiro_dwm)
```

Este badge mostrará a porcentagem de cobertura em tempo real.

---

## 💬 Comentários Automáticos em PRs

Codecov comentará automaticamente em cada Pull Request com:

```
# Codecov Report
Merging #123 will increase coverage by 2.5%

## Coverage Diff
                main      #123    +/-
=========================================
+ Coverage    96.0%    98.5%   +2.5%
=========================================
  Files           3        3            
  Lines          150      160      +10
=========================================
+ Hits           144      158      +14
+ Misses           6        2       -4

📊 View full report at Codecov
```

---

## 📈 Recursos do Dashboard

### 1. Sunburst Graph
Visualização circular da cobertura por arquivo/módulo

### 2. File Tree
Árvore de arquivos com % de cobertura de cada um

### 3. Commit Graph
Evolução da cobertura ao longo dos commits

### 4. Pull Request Impact
Análise de como cada PR afeta a cobertura

### 5. Coverage Trend
Gráfico de linha mostrando tendência da cobertura

---

## 🔍 Análise de Código no Codecov

O Codecov permite navegar pelo código e ver:
- ✅ Linhas cobertas (verde)
- ❌ Linhas não cobertas (vermelho)
- ⚠️ Linhas parcialmente cobertas (amarelo)

---

## ⚙️ Configurações Avançadas

### Configurar Status Checks

No GitHub, vá em Settings > Branches > Branch protection rules:

1. Adicione **"codecov/project"** aos status checks obrigatórios
2. Isso impedirá merge se a cobertura cair abaixo da meta (95%)

### Configurar Notificações

Em `codecov.yml`, adicione:

```yaml
comment:
  behavior: default
  require_changes: yes    # Só comenta se houver mudanças
  require_base: yes       # Só comenta se houver base para comparar
  require_head: yes       # Só comenta se houver head válido

slack:
  notify:
    - "#builds"           # Canal Slack para notificações
```

### Flags para Diferentes Tipos de Teste

```yaml
flags:
  unittests:
    paths:
      - tests/test_*.py
  integration:
    paths:
      - tests/test_blueprints_integration.py
```

---

## 🎯 Metas de Cobertura Configuradas

| Métrica | Meta | Tolerância |
|---------|------|------------|
| **Cobertura Geral** | 95% | ±2% |
| **Novo Código (Patch)** | 90% | ±5% |

### O que isso significa?

1. **Cobertura Geral (95%)**: O projeto como um todo deve manter 95% de cobertura
   - Se cair para 93% (95% - 2%), o build falha
   
2. **Patch (90%)**: Código novo em PRs deve ter pelo menos 90% de cobertura
   - Permite que código legado tenha menor cobertura
   - Força que código novo seja bem testado

---

## 🚀 Próximos Passos

Após configurar o Codecov:

1. ✅ Verificar primeiro relatório após push
2. ✅ Adicionar badge ao README.md
3. ✅ Criar um PR de teste para ver comentários automáticos
4. ✅ Configurar status check obrigatório
5. ✅ Compartilhar dashboard com a equipe

---

## 📚 Recursos Úteis

- [Documentação Oficial](https://docs.codecov.com/docs)
- [Codecov GitHub Action](https://github.com/codecov/codecov-action)
- [Exemplo de codecov.yml](https://docs.codecov.com/docs/codecov-yaml)
- [Status Checks](https://docs.codecov.com/docs/commit-status)

---

## 🎉 Situação Atual do Projeto

### ✅ Cobertura Conquistada

- **date_helpers.py**: 100% (83/83 linhas)
- **money_formatters.py**: 100% (76/76 linhas)
- **Testes**: 110 testes passando em 1.82s

### 📊 Estatísticas

```
Total de Testes: 110
├── date_helpers: 49 testes
├── money_formatters: 61 testes
└── Tempo médio: 1.82s

Cobertura:
├── date_helpers.py: 100% ✅
├── money_formatters.py: 100% ✅
└── validators.py: 18% ⏸️ (não é prioridade no momento)
```

---

## 🔥 Dica Pro

Use o **Codecov Browser Extension** para ver cobertura diretamente no GitHub:

1. Chrome: https://chrome.google.com/webstore/detail/codecov/gedikamndpbemklijjkncpnolildpbgo
2. Firefox: https://addons.mozilla.org/en-US/firefox/addon/codecov/

Isso mostra a cobertura de cada arquivo diretamente na interface do GitHub!
