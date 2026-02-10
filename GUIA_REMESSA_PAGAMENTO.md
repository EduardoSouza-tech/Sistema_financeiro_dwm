# 🏦 Guia Rápido - Remessa de Pagamentos Sicredi

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Configuração Inicial](#configuração-inicial)
3. [Como Gerar uma Remessa](#como-gerar-uma-remessa)
4. [Consultar Histórico](#consultar-histórico)
5. [Download de Arquivos](#download-de-arquivos)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### O que é Remessa de Pagamento?
Sistema para geração de arquivos CNAB 240 (padrão Sicredi - código 748) para pagamentos em lote através do banco.

### Tipos de Pagamento Suportados:
- 💳 **TED** - Transferências bancárias
- 💰 **PIX** - Pagamentos instantâneos
- 📄 **Boleto** - Pagamento de boletos
- 📊 **Tributo** - Pagamento de impostos/taxas

---

## ⚙️ Configuração Inicial

### 1. Acessar o Módulo
1. Faça login no sistema
2. Abra o menu **💰 Financeiro**
3. Clique em **📤 Remessa Pagamentos**

### 2. Configurar Convênio Sicredi (Primeira Vez)

Na primeira vez, você precisa configurar os dados do convênio bancário:

1. Clique no botão **⚙️ Configuração Sicredi** (canto superior direito)
2. Preencha os dados:

```
┌─────────────────────────────────────────┐
│  ⚙️ Configuração Sicredi                │
├─────────────────────────────────────────┤
│ Código Beneficiário: [__________]       │
│ Código Convênio:     [__________]       │
│ Agência:             [____]             │
│ Conta:               [__________]       │
│                                          │
│  [Cancelar]  [💾 Salvar Configuração]   │
└─────────────────────────────────────────┘
```

3. Clique em **💾 Salvar Configuração**

> ⚠️ **Importante**: Esses dados são fornecidos pelo banco Sicredi. Se não tiver, entre em contato com seu gerente.

---

## 📤 Como Gerar uma Remessa

### Passo 1: Visualizar Contas Pendentes

A tela inicial mostra automaticamente:

```
┌──────────────────────────────────────────────────────┐
│  📊 Estatísticas                                      │
├──────────────────────────────────────────────────────┤
│  Total Pendente: R$ 15.850,00                        │
│  TED: 5 (R$ 8.500,00)                                │
│  PIX: 3 (R$ 4.350,00)                                │
│  Boleto: 2 (R$ 3.000,00)                             │
└──────────────────────────────────────────────────────┘
```

### Passo 2: Aplicar Filtros (Opcional)

Use os filtros para refinar a seleção:

- **📅 Período**: Data início e fim
- **💳 Tipo**: TED, PIX, Boleto, Tributo
- **📆 Vencimento**: Vencidas, Vencendo hoje, Próximos 7 dias, etc.

### Passo 3: Selecionar Contas

Na tabela de contas pendentes:

1. Marque a checkbox de cada conta que deseja incluir
2. ✅ Aparecerá: "X contas selecionadas - Total: R$ X.XXX,XX"

### Passo 4: Gerar Arquivo CNAB

1. Clique no botão **🚀 Gerar Remessa**
2. Aguarde o processamento (~2 segundos)
3. Arquivo será gerado automaticamente

### Resultado:

```
✅ Remessa #523 gerada com sucesso!
📄 Arquivo: REM_SICREDI_20260210_001523.txt
💰 Total: R$ 15.850,00
📋 Itens: 10
🔒 Hash: a3f8b9c2d4e5f6...
```

---

## 📚 Consultar Histórico

### Ver Remessas Anteriores

1. Role para baixo até **📋 Histórico de Remessas**
2. A tabela mostra todas as remessas geradas:

| # | Data/Hora | Arquivo | Itens | Total | Status | Ações |
|---|-----------|---------|-------|-------|--------|-------|
| 523 | 10/02/2026 14:30 | REM_SICREDI_20260210_001523.txt | 10 | R$ 15.850,00 | ✅ Gerado | 📥 👁️ |
| 522 | 09/02/2026 10:15 | REM_SICREDI_20260209_001522.txt | 8 | R$ 12.300,00 | ✅ Gerado | 📥 👁️ |

### Ações Disponíveis:

- **📥 Download** - Baixar arquivo CNAB
- **👁️ Detalhes** - Ver itens incluídos na remessa

---

## 💾 Download de Arquivos

### Como baixar uma remessa:

1. No histórico, clique no botão **📥 Download**
2. Arquivo CNAB será baixado automaticamente
3. Nome do arquivo: `REM_SICREDI_YYYYMMDD_NNNNNN.txt`

### O que fazer com o arquivo:

1. ✅ Acesse o Internet Banking do Sicredi
2. ✅ Vá em: **Pagamentos** → **Importar Remessa**
3. ✅ Faça upload do arquivo `.txt` baixado
4. ✅ Confirme os pagamentos no banco
5. ✅ Aguarde processamento (geralmente 1 dia útil)

---

## 🔍 Ver Detalhes de uma Remessa

### Abrir Modal de Detalhes:

1. Clique no botão **👁️ Detalhes** no histórico
2. Modal mostra informações completas:

```
┌─────────────────────────────────────────────────────┐
│  📋 Detalhes da Remessa #523                        │
├─────────────────────────────────────────────────────┤
│  📄 Arquivo: REM_SICREDI_20260210_001523.txt        │
│  📅 Gerado em: 10/02/2026 às 14:30:25               │
│  💰 Valor Total: R$ 15.850,00                       │
│  📋 Quantidade: 10 itens                            │
│  🔒 Hash: a3f8b9c2d4e5f6a7b8c9d0e1f2...            │
├─────────────────────────────────────────────────────┤
│  Itens Incluídos:                                   │
│                                                      │
│  1. Fornecedor ABC - TED                            │
│     R$ 2.500,00 - Venc: 12/02/2026                  │
│                                                      │
│  2. Fornecedor XYZ - PIX                            │
│     R$ 1.350,00 - Venc: 11/02/2026                  │
│                                                      │
│  [... 8 itens restantes ...]                        │
│                                                      │
│  [Fechar]  [📥 Download]                            │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 Interface - Elementos Visuais

### Cards de Estatísticas:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 💳 TED          │  │ 💰 PIX          │  │ 📄 Boleto       │
│                 │  │                 │  │                 │
│ 5 pendentes     │  │ 3 pendentes     │  │ 2 pendentes     │
│ R$ 8.500,00     │  │ R$ 4.350,00     │  │ R$ 3.000,00     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Status Visuais:

- 🟢 **Verde** - Itens selecionados
- 🔵 **Azul** - Status normal
- 🟡 **Amarelo** - Vencendo em breve
- 🔴 **Vermelho** - Vencido
- ⚪ **Cinza** - Cancelado

---

## 🔧 Troubleshooting

### ❌ Erro: "Configuração Sicredi não encontrada"

**Solução:**
1. Configure os dados do convênio primeiro
2. Clique em **⚙️ Configuração Sicredi**
3. Preencha todos os campos
4. Salve a configuração

---

### ❌ Erro: "Nenhuma conta selecionada"

**Solução:**
1. Marque pelo menos 1 checkbox na tabela
2. Verifique se há contas disponíveis nos filtros
3. Tente limpar os filtros

---

### ❌ Erro: "Dados bancários inválidos"

**Solução:**
1. Verifique se o fornecedor tem dados bancários completos:
   - Banco
   - Agência
   - Conta
   - Tipo de conta
   - CPF/CNPJ
2. Edite o cadastro do fornecedor
3. Tente novamente

---

### ❌ Remessa não aparece no histórico

**Solução:**
1. Recarregue a página (F5)
2. Verifique se a geração foi bem-sucedida
3. Procure por mensagem de erro no topo da tela

---

### ⚠️ Arquivo não é aceito pelo banco

**Solução:**
1. Verifique se os dados do convênio estão corretos
2. Confirme código do banco: **748 (Sicredi)**
3. Layout: **CNAB 240**
4. Entre em contato com suporte do banco

---

## 📊 Fluxo Completo

```
1. Cadastrar Fornecedores
   └─> Com dados bancários completos
       ├─> Banco, Agência, Conta
       ├─> CPF/CNPJ
       └─> Tipo de Conta

2. Lançar Contas a Pagar
   └─> Com tipo de pagamento definido
       ├─> TED
       ├─> PIX
       ├─> Boleto
       └─> Tributo

3. Configurar Sicredi (1x)
   └─> Dados do convênio bancário

4. Gerar Remessa
   └─> Selecionar contas pendentes
       └─> Gerar arquivo CNAB 240

5. Download do Arquivo
   └─> Baixar .txt

6. Upload no Banco
   └─> Internet Banking Sicredi
       └─> Confirmar pagamentos

7. Processamento
   └─> Banco processa (1 dia útil)
       └─> Pagamentos realizados ✅
```

---

## 📝 Notas Importantes

### ✅ Boas Práticas:

1. **Sempre revise** as contas selecionadas antes de gerar
2. **Guarde os arquivos** CNAB para auditoria
3. **Confira no banco** se os pagamentos foram processados
4. **Comunique fornecedores** sobre a data de pagamento
5. **Mantenha dados atualizados** - banco, agência, conta

### ⚠️ Atenções:

1. Remessas **não podem ser editadas** depois de geradas
2. Cada remessa tem **sequencial único**
3. Arquivos têm **hash de integridade** (SHA-256)
4. Sistema registra **data/hora exata** de cada geração
5. Todas as ações são **auditadas**

---

## 🔐 Permissões Necessárias

| Ação | Permissão | Descrição |
|------|-----------|-----------|
| Visualizar | `remessa_view` | Ver tela e histórico |
| Criar | `remessa_criar` | Gerar novas remessas |
| Configurar | `remessa_config` | Editar config Sicredi |
| Processar Retorno | `remessa_processar` | Processar arquivos retorno |
| Excluir | `remessa_excluir` | Excluir remessas |

> 💡 **Dica**: Configure permissões em **Configurações** → **Grupos de Usuários**

---

## 📞 Suporte

### Precisa de ajuda?

- 📧 Email: suporte@seudominio.com
- 📱 WhatsApp: (XX) XXXXX-XXXX
- 🌐 Portal: https://suporte.seudominio.com

### Informações Úteis:

- **Banco**: Sicredi (código 748)
- **Layout**: CNAB 240 versão 103
- **Tipos suportados**: TED, PIX, Boleto, Tributo
- **Formato arquivo**: .txt (ASCII)
- **Tamanho linha**: 240 caracteres

---

## 🚀 Versão

- **Módulo**: Remessa de Pagamento Sicredi
- **Versão**: 1.0.0
- **Data**: 10/02/2026
- **Desenvolvido para**: Sistema Financeiro DWM

---

**✅ Sistema pronto para uso!** 🎉

Para mais informações técnicas, consulte: `DOCS_REMESSA_PAGAMENTO_COMPLETO.md`
