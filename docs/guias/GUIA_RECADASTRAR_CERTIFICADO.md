# 🔐 Guia: Como Recadastrar Certificado Digital

## ⚠️ Quando recadastrar?

Você precisa recadastrar o certificado quando:
- Aparece mensagem "senha em formato inválido"
- Erro "Certificado não encontrado ou inválido" ao buscar documentos
- Alerta vermelho no card do certificado: "⚠️ ATENÇÃO: Certificado precisa ser recadastrado"

## 📋 Passo a passo

### 1️⃣ Acessar Relatórios Fiscais
- No menu lateral, clique em **📊 Relatórios**
- Clique em **📑 NF-e e CT-e - Documentos Fiscais**

### 2️⃣ Ir para Certificados
- Clique na aba **🔐 Certificados Digitais**
- Você verá a lista de certificados cadastrados

### 3️⃣ Desativar certificado antigo (opcional)
- Se o certificado antigo aparecer com alerta vermelho
- Clique no botão **❌ Desativar** no card do certificado
- Confirme a desativação

### 4️⃣ Cadastrar novo certificado
- Clique no botão **➕ Novo Certificado**
- No modal que abrir:

#### 📎 Passo 1: Selecionar arquivo .pfx
- Clique em "Escolher arquivo"
- Selecione seu certificado digital (.pfx ou .p12)

#### 🔑 Passo 2: Digitar senha
- Digite a senha do certificado
- **Aguarde**: O sistema vai extrair automaticamente os dados!

#### ✅ Passo 3: Verificar dados extraídos
Campos preenchidos automaticamente:
- **Nome do Certificado**: Nome da empresa (readonly - não editável)
- **CNPJ**: CNPJ do certificado (readonly)
- **Informações**: Mostra validade do certificado

Campos que você DEVE preencher/confirmar:
- **UF (Estado)**: Selecione o estado correto (padrão: MG)
- **Ambiente**: Escolha Produção ou Homologação

#### 💾 Passo 4: Salvar
- Clique em **💾 Salvar**
- Aguarde a confirmação: "Certificado cadastrado com sucesso!"

### 5️⃣ Testar busca automática
- Volte para a aba **🔍 Buscar Documentos**
- Selecione o certificado recém-cadastrado
- Clique em **🔄 Iniciar Busca Automática**
- Deve funcionar sem erros!

## 🔒 Segurança

**Por que preciso recadastrar?**

Certificados antigos foram salvos com senha em texto plano (inseguro). O sistema agora usa criptografia Fernet para proteger a senha. Ao recadastrar, a senha será criptografada corretamente.

## ❓ Problemas comuns

### "Senha em formato inválido"
- **Causa**: Certificado cadastrado antes da implementação da criptografia
- **Solução**: Recadastrar seguindo os passos acima

### "Certificado não aparece no select"
- **Causa**: Certificado está inativo ou senha inválida
- **Solução**: Recadastrar novo certificado

### "Erro ao extrair dados: Erro ao ler certificado"
- **Causa**: Senha incorreta ou arquivo .pfx corrompido
- **Solução**: Verificar se a senha está correta e tentar outro arquivo .pfx

## 💡 Dicas

1. **Mantenha a senha segura**: Anote a senha do certificado em local seguro
2. **Verifique a validade**: O sistema mostra a data de validade ao extrair os dados
3. **Use produção**: Certificados de homologação são apenas para testes
4. **Um certificado ativo**: O sistema desativa automaticamente os outros ao cadastrar um novo

## 📞 Suporte

Se após seguir todos os passos ainda tiver problemas:
1. Verifique os logs do servidor
2. Confirme que a variável `FERNET_KEY` está configurada no ambiente
3. Teste com outro arquivo .pfx válido

---

**Última atualização**: 2026-02-18  
**Versão do sistema**: Sistema Financeiro DWM v2.0
