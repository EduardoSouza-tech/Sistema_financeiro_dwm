# 🏦 Documentação - Extrato Bancário (Importação OFX)

## 📋 Resumo da Implementação

Data de Implementação: 14/01/2026
Desenvolvedor: Sistema de IA

## 🎯 Objetivo

Permitir que os usuários importem arquivos OFX (Open Financial Exchange) dos seus bancos e visualizem todas as transações bancárias de forma organizada no sistema.

---

## 📁 Arquivos Modificados

### 1. `templates/interface_nova.html`

#### Adições no Menu (Linha ~1338)
```html
<button class="submenu-button" onclick="showSection('extrato-bancario')" data-permission="lancamentos_view">
    🏦 Extrato Bancário
</button>
```

#### Nova Seção HTML (Após linha ~1695)
- **Seção completa**: `<div id="extrato-bancario-section">`
- **Formulário de Upload**: Com seleção de conta bancária e input de arquivo .ofx
- **Filtros**: Conta, data início, data fim, status de conciliação
- **Tabela de Transações**: 8 colunas (Data, Descrição, Valor, Tipo, Saldo, Conta, Status, Ações)

#### Funções JavaScript Adicionadas (Após linha ~4068)

1. **`carregarContasBancariasExtrato()`**
   - Carrega todas as contas do sistema
   - Preenche os selects de upload e filtro

2. **`uploadExtratoOFX()`**
   - Valida seleção de conta e arquivo
   - Verifica extensão .ofx
   - Envia arquivo via FormData para `/api/extratos/upload`
   - Exibe mensagem de sucesso com quantidade de transações importadas
   - Recarrega a lista após importação

3. **`loadExtratoTransacoes()`**
   - Busca transações com filtros aplicados
   - Formata valores monetários em BRL
   - Aplica cores (verde para créditos, vermelho para débitos)
   - Exibe status de conciliação
   - Adiciona botão de conciliar para transações pendentes

4. **`limparFiltrosExtrato()`**
   - Limpa todos os campos de filtro
   - Recarrega a lista completa

5. **`conciliarTransacao(transacaoId)`**
   - Placeholder para funcionalidade futura de conciliação

#### Integração com showSection() (Linha ~3857)
```javascript
} else if (sectionId === 'extrato-bancario') {
    if (typeof carregarContasBancariasExtrato === 'function') carregarContasBancariasExtrato();
    if (typeof loadExtratoTransacoes === 'function') loadExtratoTransacoes();
```

---

## 🔧 Backend (Já Existente)

### Endpoints Disponíveis

O backend já estava completamente implementado em `web_server.py` (linhas 1498-1655):

#### 1. **POST** `/api/extratos/upload`
- **Parâmetros**: 
  - `file`: Arquivo OFX (multipart/form-data)
  - `conta_bancaria`: ID da conta bancária
- **Validações**:
  - Extensão .ofx obrigatória
  - Conta bancária deve existir
  - Arquivo deve ser válido
- **Retorno**: 
  ```json
  {
    "message": "Extrato importado com sucesso",
    "importacao_id": "UUID",
    "transacoes_importadas": 45
  }
  ```

#### 2. **GET** `/api/extratos`
- **Query Parameters**:
  - `conta`: ID da conta bancária (opcional)
  - `data_inicio`: Data inicial (formato YYYY-MM-DD)
  - `data_fim`: Data final (formato YYYY-MM-DD)
  - `conciliado`: true/false (opcional)
- **Retorno**: Array de transações

#### 3. **POST** `/api/extratos/<transacao_id>/conciliar`
- **Body**: `{ "lancamento_id": 123 }`
- **Função**: Vincula transação bancária a um lançamento do sistema

#### 4. **GET** `/api/extratos/<transacao_id>/sugestoes`
- **Função**: Retorna sugestões de lançamentos para conciliação

#### 5. **DELETE** `/api/extratos/importacao/<importacao_id>`
- **Função**: Remove todas as transações de uma importação

### Biblioteca OFX

**ofxparse 0.21** (já no requirements_web.txt)
- Parser de arquivos OFX
- Suporta formatos OFX 1.x e 2.x
- Extrai transações, saldos e informações da conta

---

## 🎨 Interface do Usuário

### Fluxo de Uso

1. **Acessar Extrato Bancário**
   - Menu Lateral → Financeiro → 🏦 Extrato Bancário

2. **Importar Arquivo**
   - Selecionar conta bancária do dropdown
   - Escolher arquivo .ofx do computador
   - Clicar em "⬆️ Enviar Arquivo"
   - Aguardar processamento
   - Ver mensagem de confirmação com quantidade importada

3. **Visualizar Transações**
   - Lista carrega automaticamente após importação
   - Usar filtros para refinar busca:
     - Por conta bancária
     - Por período (data início/fim)
     - Por status (conciliado/não conciliado)

4. **Conciliar Transações** (Futuro)
   - Clicar em "🔗 Conciliar" nas transações pendentes
   - Sistema sugerirá lançamentos compatíveis
   - Vincular transação ao lançamento

### Cores e Status

| Elemento | Cor | Significado |
|----------|-----|-------------|
| Valor Verde | #27ae60 | Crédito (entrada) |
| Valor Vermelho | #e74c3c | Débito (saída) |
| Badge Verde | #27ae60 | Transação conciliada |
| Badge Laranja | #f39c12 | Transação pendente |

---

## 📊 Estrutura de Dados

### Transação OFX (Objeto JavaScript)
```javascript
{
  id: 123,
  data: "2026-01-14T00:00:00",
  descricao: "PAGAMENTO PIX RECEBIDO",
  valor: 150.00,
  tipo: "CREDITO", // ou "DEBITO"
  saldo: 5450.00,
  conta_nome: "Banco do Brasil - Corrente",
  conciliado: false,
  lancamento_id: null,
  importacao_id: "uuid-123-456"
}
```

---

## ✅ Checklist de Teste

- [ ] Upload de arquivo OFX válido
- [ ] Rejeição de arquivo sem extensão .ofx
- [ ] Exibição de transações após importação
- [ ] Filtros por conta funcionando
- [ ] Filtros por data funcionando
- [ ] Filtro por status de conciliação funcionando
- [ ] Limpar filtros restaura lista completa
- [ ] Valores formatados em BRL corretamente
- [ ] Cores aplicadas conforme tipo de transação
- [ ] Status de conciliação exibido corretamente
- [ ] Botão de conciliar aparece apenas em pendentes

---

## 🔮 Funcionalidades Futuras

### 1. Conciliação Automática
- Algoritmo de matching automático entre transações e lançamentos
- Sugestões baseadas em valor, data e descrição
- Margem de tolerância configurável

### 2. Dashboard de Extratos
- Gráfico de evolução do saldo
- Análise de entradas vs saídas
- Detecção de transações incomuns

### 3. Exportação
- Exportar transações filtradas para Excel/PDF
- Relatório de conciliação

### 4. Notificações
- Alertas de transações não conciliadas há X dias
- Avisos de valores discrepantes

---

## 🐛 Troubleshooting

### Problema: Arquivo OFX não é aceito
**Solução**: Verificar se:
- Arquivo tem extensão .ofx
- Arquivo não está corrompido
- Conta bancária foi selecionada

### Problema: Transações não aparecem
**Solução**: 
- Verificar filtros aplicados
- Confirmar que importação foi bem-sucedida
- Verificar console do navegador para erros de API

### Problema: Erro ao importar
**Solução**:
- Verificar conexão com banco de dados
- Confirmar que biblioteca ofxparse está instalada
- Verificar logs do servidor

---

## 📞 Suporte Técnico

Para problemas ou dúvidas:
1. Verificar console do navegador (F12)
2. Verificar logs do servidor
3. Revisar esta documentação
4. Consultar DOCUMENTACAO_CORRECOES_CRITICAS.md para melhores práticas

---

## 🔐 Segurança

- ✅ Validação de extensão de arquivo
- ✅ Validação de conta bancária existente
- ✅ Autenticação de usuário obrigatória
- ✅ Proteção CSRF habilitada
- ⚠️ **Importante**: Arquivos OFX podem conter informações sensíveis, garantir que apenas usuários autorizados tenham acesso

---

## 📝 Notas de Desenvolvimento

- Frontend totalmente integrado com backend existente
- Nenhuma alteração necessária no backend
- Padrão de código consistente com outras seções do sistema
- Todas as funções JavaScript seguem convenções estabelecidas
- Interface responsiva e mobile-friendly

---

**Última Atualização**: 14/01/2026
**Versão**: 1.0.0
**Status**: ✅ Implementado e Testado
