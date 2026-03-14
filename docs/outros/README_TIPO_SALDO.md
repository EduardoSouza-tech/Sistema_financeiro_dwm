# Adicionar Campo Credor/Devedor em Contas Bancárias

## 📋 Resumo das Alterações

Foi implementado um novo campo **"Tipo de Saldo Inicial"** no cadastro de contas bancárias que permite indicar se o saldo inicial é:

- **💰 Credor (Positivo)**: A conta tem saldo positivo (você tem dinheiro)
- **⚠️ Devedor (Negativo)**: A conta tem saldo negativo (você deve dinheiro, exemplo: cheque especial)

## ✅ Alterações Realizadas

### 1. Banco de Dados
- Adicionada coluna `tipo_saldo_inicial` na tabela `contas_bancarias`
- Valores aceitos: `'credor'` ou `'devedor'`
- Valor padrão: `'credor'`

### 2. Backend (Python)
- **database_postgresql.py**: 
  - Atualizado model `ContaBancaria` com novo atributo
  - Atualizado métodos `adicionar_conta`, `listar_contas` e `atualizar_conta`
  
- **web_server.py**:
  - Atualizado endpoints `/api/contas` para aceitar e retornar o novo campo
  - Adicionada migração automática na inicialização

### 3. Frontend (JavaScript)
- **static/modals.js**:
  - Adicionado campo de seleção no formulário de conta
  - Implementada validação obrigatória
  - Ajuste automático do sinal do saldo:
    - Devedor + valor positivo → converte para negativo
    - Credor + valor negativo → converte para positivo

## 🚀 Como Testar

### 1. Executar Migração do Banco de Dados

A migração será executada automaticamente ao iniciar o servidor. Mas se preferir executar manualmente:

```powershell
# Opção 1: Iniciar o servidor (migração automática)
cd "C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm"
python web_server.py

# Opção 2: Executar migração standalone
python migration_tipo_saldo_inicial.py
```

### 2. Testar no Frontend

1. Inicie o servidor web
2. Acesse o sistema no navegador
3. Vá em **Contas Bancárias** → **Nova Conta**
4. Preencha os dados:
   - Banco, Agência, Conta
   - Saldo Inicial (ex: 5500,00)
   - **Tipo de Saldo**: 
     - Selecione **Credor** se a conta tem dinheiro
     - Selecione **Devedor** se a conta está negativa
5. Clique em **Salvar**

### 3. Exemplos de Uso

**Exemplo 1: Conta com saldo positivo**
```
Banco: Banco do Brasil
Agência: 1234-5
Conta: 67890-1
Saldo Inicial: R$ 5.500,00
Tipo: 💰 Credor (Positivo)

→ Salvo no banco: saldo_inicial = 5500.00, tipo_saldo_inicial = 'credor'
```

**Exemplo 2: Conta com cheque especial (negativo)**
```
Banco: Itaú
Agência: 9876
Conta: 54321-0
Saldo Inicial: R$ 1.200,00 (digitado positivo)
Tipo: ⚠️ Devedor (Negativo)

→ Salvo no banco: saldo_inicial = -1200.00, tipo_saldo_inicial = 'devedor'
```

## 🔧 Arquivos Modificados

| Arquivo | Alterações |
|---------|-----------|
| `database_postgresql.py` | ✅ Adicionada coluna na tabela<br>✅ Atualizado model ContaBancaria<br>✅ Atualizado métodos CRUD |
| `web_server.py` | ✅ Atualizado endpoints API<br>✅ Adicionada migração automática |
| `static/modals.js` | ✅ Adicionado campo select<br>✅ Validação e ajuste de sinal |
| `migration_tipo_saldo_inicial.py` | ✅ Script de migração criado |

## 📝 Arquivos Criados

- ✅ `migration_tipo_saldo_inicial.py` - Migração do banco de dados
- ✅ `add_tipo_saldo_column.py` - Script auxiliar de migração
- ✅ `add_tipo_saldo_column.sql` - SQL da migração
- ✅ `README_TIPO_SALDO.md` - Esta documentação

## ⚠️ Observações Importantes

1. **Contas existentes**: Todas as contas já cadastradas receberão automaticamente `tipo_saldo_inicial = 'credor'` (valor padrão)

2. **Validação**: O campo é obrigatório ao criar/editar uma conta

3. **Ajuste automático**: O sistema ajusta automaticamente o sinal do saldo:
   - Se você selecionar "Devedor" e digitar um valor positivo, o sistema converte para negativo
   - Se você selecionar "Credor" e digitar um valor negativo, o sistema converte para positivo

4. **Uso futuro**: Este campo será usado no cálculo de saldos ao importar extratos bancários OFX

## 🐛 Solução de Problemas

### Erro: "Coluna tipo_saldo_inicial não existe"

Execute a migração manualmente:

```powershell
cd "C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm"
python migration_tipo_saldo_inicial.py
```

### Erro: "Campo tipo_saldo_inicial é obrigatório"

Certifique-se de selecionar uma opção no dropdown antes de salvar a conta.

### Campo não aparece no formulário

1. Limpe o cache do navegador (Ctrl + Shift + Delete)
2. Recarregue a página (Ctrl + F5)
3. Verifique se o arquivo `static/modals.js` foi atualizado corretamente

## ✅ Checklist de Implementação

- [x] Adicionar coluna no banco de dados
- [x] Atualizar model ContaBancaria
- [x] Atualizar métodos CRUD (adicionar, listar, atualizar)
- [x] Atualizar endpoints da API
- [x] Adicionar campo no formulário frontend
- [x] Implementar validação
- [x] Implementar ajuste automático de sinal
- [x] Criar migração automática
- [x] Documentar alterações

## 📞 Suporte

Se encontrar algum problema:
1. Verifique os logs do servidor
2. Verifique o console do navegador (F12)
3. Execute a migração manualmente
4. Verifique se todos os arquivos foram salvos corretamente

---

**Data de Implementação**: 2024
**Status**: ✅ Concluído
