# 🔐 AÇÃO URGENTE: Recadastrar Certificado Digital

**⏱️ Tempo:** 2 minutos  
**🎯 Objetivo:** Corrigir erro "Senha em formato inválido" na busca de documentos NF-e/CT-e

---

## ❌ Problema Atual

```
ERROR: [CERT] Descriptografando senha (tamanho senha_cripto: 9 chars)...
ERROR: [CERT] ❌ Senha em formato inválido
ERROR: Certificado não encontrado ou senha em formato inválido
```

**Causa:** Certificado ID 2 foi salvo com senha em **texto plano** (9 chars) antes do sistema de criptografia Fernet existir.

---

## ✅ Solução em 3 Passos

### 1️⃣ Desativar Certificado Antigo (30 segundos)

```
Relatórios Fiscais > 🔐 Certificados Digitais > Certificado ID 2 > 🗑️ Desativar
```

### 2️⃣ Cadastrar Novo (1 minuto)

```
🔐 Certificados Digitais > ➕ Cadastrar Certificado
```

1. **Selecionar arquivo:** Mesmo `.pfx` anterior
2. **Digitar senha:** Mesma senha anterior
3. **UF:** Detectada automaticamente ✨ (verde)
4. **Salvar**

### 3️⃣ Testar Busca (30 segundos)

```
📄 Documentos NF-e/CT-e > Selecionar novo certificado > 🔍 Buscar Documentos
```

**Resultado esperado:**
```
[CERT] ✅ Senha descriptografada com sucesso
✅ Busca concluída! X documentos encontrados
```

---

## 🔍 Como Saber se Deu Certo?

### Logs ANTES (❌ Errado):
```
[CERT] Descriptografando senha (tamanho senha_cripto: 9 chars)...
ERROR: [CERT] ❌ Senha em formato inválido
```

### Logs DEPOIS (✅ Correto):
```
[CERTIFICADO] ✅ Senha criptografada: 112 chars
[CERT] Descriptografando senha (tamanho senha_cripto: 112 chars)...
[CERT] ✅ Senha descriptografada com sucesso
```

---

## 📊 Diferença

| Item | ❌ Texto Plano | ✅ Criptografado |
|------|---------------|-----------------|
| Tamanho | 9 chars | ~112 chars |
| Segurança | Baixa | Alta |
| Compatível | Não | Sim |
| Busca funciona | Não | Sim |

---

## ⚠️ IMPORTANTE

- Use o **mesmo arquivo .pfx** e **mesma senha**
- Sistema agora criptografa automaticamente com Fernet
- Certificados antigos (texto plano) **não são compatíveis**

---

**Próximo:** Após recadastrar, **recarregue a página** e teste a busca novamente.

📚 **Documentação completa:** `SOLUCAO_ERRO_CERTIFICADO_NFE.md`
