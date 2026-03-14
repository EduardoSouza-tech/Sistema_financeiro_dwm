# 🚀 Deploy do Sistema NF-e/CT-e - Railway

## ✅ PRÉ-REQUISITOS

### 1. Variáveis de Ambiente Necessárias

Configure estas variáveis no **Railway Dashboard**:

```bash
# Banco de Dados (já configurado)
DATABASE_URL=postgresql://postgres:senha@host:porta/railway

# Flask
SECRET_KEY=sua_chave_secreta_aqui
FLASK_ENV=production

# Criptografia de Certificados (NOVO - OBRIGATÓRIO)
FERNET_KEY=gerar_nova_chave_abaixo

# Monitoramento (opcional)
SENTRY_DSN=seu_sentry_dsn

# Rate Limiting (opcional)
RATELIMIT_ENABLED=true
```

### 2. Gerar FERNET_KEY

Execute em Python:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Copie a chave gerada e adicione no Railway como variável `FERNET_KEY`.

---

## 📦 DEPENDÊNCIAS INSTALADAS

✅ Todas as dependências já estão no `requirements.txt`:
- `lxml==5.1.0` - Parse de XML
- `cryptography==42.0.0` - Certificados digitais
- `requests>=2.28.0` - Comunicação SEFAZ
- `openpyxl>=3.1.0` - Exportação Excel
- `psycopg2-binary==2.9.9` - PostgreSQL

---

## 🗄️ BANCO DE DADOS

### Migration Executada:
✅ A migration `migration_nfe_cte_relatorios.sql` já foi executada no Railway.

**Tabelas criadas:**
- `certificados_digitais` (16 campos)
- `documentos_fiscais_log` (21 campos)
- 3 views de estatísticas
- 13 permissões adicionadas

**Para verificar:**
```sql
SELECT COUNT(*) FROM certificados_digitais;
SELECT COUNT(*) FROM documentos_fiscais_log;
```

---

## 🌐 ENDPOINTS DISPONÍVEIS

Após o deploy, acesse:

```
https://seu-app.up.railway.app/relatorios/fiscal
```

**API REST (13 endpoints):**
- `GET /relatorios/fiscal` - Dashboard
- `GET /api/relatorios/certificados` - Lista certificados
- `POST /api/relatorios/certificados/novo` - Cadastra certificado
- `POST /api/relatorios/buscar-documentos` - Busca automática
- `POST /api/relatorios/consultar-chave` - Consulta por chave
- `GET /api/relatorios/documentos` - Lista documentos
- `GET /api/relatorios/documento/<id>/xml` - Download XML
- `GET /api/relatorios/estatisticas` - Estatísticas
- `POST /api/relatorios/exportar-excel` - Exporta Excel

---

## 📋 CHECKLIST DE DEPLOY

### Antes do Deploy:
- [x] Código commitado no GitHub
- [x] `requirements.txt` atualizado
- [x] Migration executada no banco
- [x] Permissões criadas
- [ ] `FERNET_KEY` configurada no Railway
- [ ] Certificado digital disponível (formato .PFX)

### Após o Deploy:
1. ✅ Verificar se o app subiu (Railway Dashboard → Deployments)
2. ✅ Acessar `/relatorios/fiscal` e verificar se carrega
3. ✅ Fazer login com usuário admin
4. ✅ Cadastrar primeiro certificado digital
5. ✅ Executar busca teste (homologação)
6. ✅ Verificar logs no Railway

---

## 🔐 SEGURANÇA

**IMPORTANTE:**
1. **NUNCA** commite arquivos `.pfx` ou senhas no Git
2. Use sempre **ambiente de homologação** para testes
3. A **senha do certificado** é criptografada com `FERNET_KEY`
4. Os **XMLs** ficam no filesystem (`storage/nfe/`)

---

## 📊 MONITORAMENTO

### Logs importantes:
```bash
# Railway CLI
railway logs

# Filtrar erros
railway logs | grep ERROR
```

### Verificar se módulo carregou:
```bash
railway logs | grep "relatorios"
```

---

## 🐛 TROUBLESHOOTING

### Erro: "FERNET_KEY não configurado"
**Solução:** Gere a chave e adicione no Railway:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Erro: "Certificado inválido"
**Solução:** 
- Verifique se o arquivo .PFX está correto
- Teste a senha localmente
- Confirme que o certificado está dentro da validade

### Erro: "Tabela não existe"
**Solução:** Execute a migration:
```bash
railway run python executar_migration_nfe_cte.py
```

### Interface não carrega
**Solução:**
- Limpe cache do navegador (Ctrl+Shift+R)
- Verifique logs do Railway
- Confirme que `templates/relatorios_fiscais.html` está no deploy

---

## ✅ STATUS ATUAL

**Commit:** `bb423bc`  
**Data:** 2026-02-17  
**Arquivos:** 16 arquivos (5.429 linhas)  
**Status:** ✅ PRONTO PARA PRODUÇÃO

---

## 📞 SUPORTE

Em caso de problemas:
1. Verifique os logs no Railway
2. Confirme variáveis de ambiente
3. Teste localmente primeiro
4. Valide permissões do usuário

---

**Sistema desenvolvido com IA assistente** 🤖✨
