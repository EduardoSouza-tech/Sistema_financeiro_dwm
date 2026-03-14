# 🛡️ Guia de Branch Protection Rules

## Status Atual
- ✅ CI/CD implementado com GitHub Actions
- ✅ 100% cobertura de testes
- ⏳ **Branch protection rules**: Precisa ser configurado manualmente no GitHub

---

## 📋 O que são Branch Protection Rules?

Branch Protection Rules são regras que protegem branches importantes (como `main` e `develop`) contra:
- Commits diretos sem revisão
- Merges de PRs com testes falhando
- Alterações não revisadas no código

---

## 🔧 Como Configurar no GitHub

### Passo 1: Acessar Configurações do Repositório

1. Acesse: https://github.com/EduardoSouza-tech/Sistema_financeiro_dwm
2. Clique em **Settings** (⚙️)
3. No menu lateral, clique em **Branches** (🌿)

### Passo 2: Adicionar Regra de Proteção

1. Clique no botão **"Add branch protection rule"**
2. No campo **"Branch name pattern"**, digite: `main`

### Passo 3: Configurar Regras Recomendadas

Marque as seguintes opções:

#### ✅ Require a pull request before merging
- **Descrição**: Exige que todas as alterações passem por um Pull Request
- **Recomendação**: ✅ ATIVAR
- Sub-opções:
  - ✅ **Require approvals**: 1 aprovação mínima
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**
  - ✅ **Require review from Code Owners** (se tiver CODEOWNERS)

#### ✅ Require status checks to pass before merging
- **Descrição**: Exige que os testes do CI/CD passem antes do merge
- **Recomendação**: ✅ ATIVAR
- **Status checks obrigatórios**:
  - `🔬 Testes Unitários (3.10)`
  - `🔬 Testes Unitários (3.11)`
  - `🔬 Testes Unitários (3.12)`
  - `🔍 Análise de Código`
  - `🔒 Verificação de Segurança`
  - `📊 Status Final`

#### ✅ Require branches to be up to date before merging
- **Descrição**: Exige que o branch esteja atualizado com main antes do merge
- **Recomendação**: ✅ ATIVAR

#### ✅ Require conversation resolution before merging
- **Descrição**: Exige que todos os comentários sejam resolvidos
- **Recomendação**: ✅ ATIVAR

#### ✅ Require signed commits
- **Descrição**: Exige commits assinados com GPG
- **Recomendação**: ⏸️ OPCIONAL (requer configuração de GPG)

#### ✅ Require linear history
- **Descrição**: Não permite merge commits, apenas rebase/squash
- **Recomendação**: ⏸️ OPCIONAL (depende do workflow da equipe)

#### ✅ Include administrators
- **Descrição**: Aplica as regras mesmo para administradores
- **Recomendação**: ✅ ATIVAR (boa prática)

#### ✅ Restrict who can push to matching branches
- **Descrição**: Limita quem pode fazer push direto
- **Recomendação**: ⏸️ OPCIONAL (para equipes maiores)

#### ✅ Allow force pushes
- **Descrição**: Permite git push --force
- **Recomendação**: ❌ DESATIVAR (perigoso)

#### ✅ Allow deletions
- **Descrição**: Permite deletar o branch
- **Recomendação**: ❌ DESATIVAR (perigoso)

### Passo 4: Salvar Configurações

1. Role até o final da página
2. Clique em **"Create"** ou **"Save changes"**

---

## 🎯 Configuração Mínima Recomendada

Para começar, configure pelo menos:

```yaml
Branch: main

Regras Essenciais:
✅ Require a pull request before merging (1 approval)
✅ Require status checks to pass before merging
   - 🔬 Testes Unitários (3.10, 3.11, 3.12)
   - 🔍 Análise de Código
   - 🔒 Verificação de Segurança
✅ Require conversation resolution before merging
✅ Include administrators
❌ Allow force pushes: DESATIVADO
❌ Allow deletions: DESATIVADO
```

---

## 📊 Configuração Avançada (Opcional)

### Para o Branch `develop`:

Repita o processo acima criando uma regra para o branch `develop` com as mesmas configurações (ou ligeiramente mais flexível).

### CODEOWNERS File

Crie um arquivo `.github/CODEOWNERS` para definir responsáveis por áreas do código:

```
# Sintaxe: pattern @username

# Arquivos de configuração
*.yml @EduardoSouza-tech
*.yaml @EduardoSouza-tech
*.json @EduardoSouza-tech

# Backend
/app/ @EduardoSouza-tech
/tests/ @EduardoSouza-tech

# Banco de dados
database*.py @EduardoSouza-tech
migration*.py @EduardoSouza-tech

# Documentação
*.md @EduardoSouza-tech
```

---

## 🔄 Workflow após Configuração

Após configurar branch protection, o fluxo de trabalho será:

1. **Criar branch**: `git checkout -b feature/nova-funcionalidade`
2. **Fazer alterações**: Código + testes
3. **Commit & Push**: `git push origin feature/nova-funcionalidade`
4. **Abrir Pull Request**: No GitHub
5. **CI/CD executa**: Aguardar todos os jobs passarem ✅
6. **Code Review**: Aguardar aprovação de 1 revisor
7. **Merge**: Só é possível se tudo estiver verde

---

## 🚫 O que NÃO será mais possível após configuração

- ❌ `git push origin main` (push direto bloqueado)
- ❌ Merge de PR com testes falhando
- ❌ Merge sem aprovação de revisor
- ❌ `git push --force origin main` (force push bloqueado)

---

## ✅ Verificar Configuração

Após configurar, teste:

1. Tente fazer push direto para main:
   ```bash
   git checkout main
   echo "test" > test.txt
   git add test.txt
   git commit -m "test"
   git push origin main
   ```
   **Esperado**: ❌ Erro de permissão

2. Crie um PR e verifique se os checks aparecem automaticamente

---

## 📚 Recursos Adicionais

- [Documentação Oficial GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Best Practices](https://github.com/topics/branch-protection)

---

## 🎉 Próximos Passos

Após configurar branch protection:

1. ✅ Testar criando um PR de teste
2. ✅ Verificar que CI/CD executa automaticamente
3. ✅ Confirmar que merge só é possível com testes passando
4. ✅ Documentar o novo workflow para a equipe
