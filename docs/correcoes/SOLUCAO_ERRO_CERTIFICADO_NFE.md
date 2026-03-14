# 🔐 Solução: Erro ao Buscar Documentos NF-e/CT-e

**Data:** 19 de Fevereiro de 2026  
**Erro:** "Certificado não encontrado ou senha em formato inválido"  
**Status:** 🔧 Em Resolução

---

## 📋 Diagnóstico do Problema

### Sintoma
Ao clicar em **"🔍 Buscar Documentos"** em **"📑 Relatórios Fiscais - NF-e e CT-e"**, o sistema retorna:

```
❌ Erro: Certificado não encontrado ou senha em formato inválido. 
Por favor, recadastre o certificado na aba "🔐 Certificados Digitais".
```

**MESMO** tendo o certificado cadastrado corretamente.

### Causa Raiz

A senha do certificado digital é **criptografada** usando **Fernet (criptografia simétrica)** com uma chave armazenada na variável de ambiente `FERNET_KEY`.

**O problema ocorre quando:**

1. ❌ **FERNET_KEY não configurada** no ambiente de produção (Railway)
2. ❌ **FERNET_KEY diferente** entre ambiente local e Railway
3. ❌ **Certificado salvo ANTES** da criptografia estar implementada (senha em texto plano)
4. ❌ **Chave corrompida** no banco de dados

### Fluxo de Criptografia

```
┌─────────────────────────────────────────────────────────────┐
│ CADASTRO (Frontend → Backend)                               │
├─────────────────────────────────────────────────────────────┤
│ 1. Usuário digita senha: "minhaSenha123"                    │
│ 2. Backend criptografa com FERNET_KEY do ambiente:          │
│    → senha_cripto = "gAAAAABl..." (112 chars)                │
│ 3. Salva no banco: certificados_digitais.senha_pfx          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ BUSCA DE DOCUMENTOS (Backend → SEFAZ)                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Backend lê senha_pfx do banco: "gAAAAABl..." (112 chars) │
│ 2. Backend tenta descriptografar com FERNET_KEY:            │
│    → Se chave correta: "minhaSenha123" ✅                     │
│    → Se chave errada/ausente: ERRO ❌                         │
│ 3. Usa senha para conectar com SEFAZ                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Melhorias Implementadas (Diagnóstico)

### Logging Detalhado

Adicionado logging extensivo em `relatorios/nfe/nfe_api.py`:

```python
# Ao salvar certificado:
[CERTIFICADO] FERNET_KEY para salvar: ✅ Presente (44 chars)
[CERTIFICADO] Criptografando senha de 12 caracteres...
[CERTIFICADO] ✅ Senha criptografada: 112 chars

# Ao recuperar certificado:
[CERT] FERNET_KEY lida do ambiente: SIM (44 chars)
[CERT] Descriptografando senha (tamanho senha_cripto: 112 chars)...
[CERT] ✅ Senha descriptografada com sucesso

# Erro detectado:
[CERT] ❌ Senha em formato inválido: Senha do certificado em formato inválido...
[CERT] Tamanho da senha_cripto recebida: 15 chars  # ⚠️ Muito curto!
[CERT] Possíveis causas:
[CERT]   1. Certificado salvo ANTES da criptografia estar implementada
[CERT]   2. FERNET_KEY diferente entre salvar e recuperar
[CERT]   3. Senha corrompida no banco de dados
```

---

## ✅ Soluções

### Solução 1: Configurar FERNET_KEY no Railway (RECOMENDADO)

#### Passo 1: Obter a chave atual

A chave local está em `.env`:

```bash
FERNET_KEY=u2izhbz5QoGb2bkfh3dT5ckGADuGcRnEwFTCZ-LY-r0=
```

#### Passo 2: Adicionar no Railway

1. Acesse o projeto no Railway: https://railway.app
2. Navegue até **Variables**
3. Adicione nova variável:
   - **Nome:** `FERNET_KEY`
   - **Valor:** `u2izhbz5QoGb2bkfh3dT5ckGADuGcRnEwFTCZ-LY-r0=`
4. Clique em **Add** e depois **Deploy**

#### Passo 3: Verificar logs

Após deploy, os logs devem mostrar:

```
[CERT] FERNET_KEY lida do ambiente: SIM (44 chars) ✅
```

Se mostrar:

```
[CERT] FERNET_KEY lida do ambiente: NÃO (vazia) ❌
```

Significa que a variável **não foi configurada** ou **não carregou**.

---

### Solução 2: Re-cadastrar Certificados

Se a FERNET_KEY foi alterada ou certificados foram salvos sem criptografia:

#### Passo 1: Desativar certificado antigo

1. Acesse: **📑 Relatórios Fiscais - NF-e e CT-e**
2. Vá na aba: **🔐 Certificados Digitais**
3. Localize o certificado problemático
4. Clique em **🗑️ Desativar**

#### Passo 2: Cadastrar novo certificado

1. Clique em **➕ Cadastrar Certificado**
2. Selecione o arquivo `.pfx`
3. Digite a senha
4. Sistema detectará automaticamente a UF
5. Clique em **💾 Salvar Certificado**

**Agora:** Com a nova implementação, a senha será criptografada com a FERNET_KEY correta.

---

### Solução 3: Script de Re-criptografia (Avançado)

Para re-criptografar certificados existentes sem recadastrar:

#### Arquivo: `recriptografar_certificados.py`

```python
"""
Script para re-criptografar senhas de certificados digitais.

Uso:
1. Certifique-se que FERNET_KEY está configurada
2. Execute: python recriptografar_certificados.py
"""

import os
import sys
from cryptography.fernet import Fernet

# Importa módulos do sistema
sys.path.append(os.path.dirname(__file__))
from database_postgresql import get_db_connection
from relatorios.nfe.nfe_api import criptografar_senha

def recriptografar_certificados():
    """Re-criptografa todos os certificados com a FERNET_KEY atual."""
    
    # Verifica FERNET_KEY
    chave_str = os.environ.get('FERNET_KEY', '')
    if not chave_str:
        print("❌ FERNET_KEY não configurada no ambiente")
        print("💡 Defina no .env ou export FERNET_KEY='...'")
        return
    
    chave = chave_str.encode('utf-8')
    print(f"✅ FERNET_KEY carregada ({len(chave_str)} chars)")
    
    # Solicita senha em texto plano para re-criptografar
    print("\n⚠️  Este script irá re-criptografar as senhas de certificados")
    print("📋 Você precisará fornecer a senha em TEXTO PLANO de cada certificado")
    print()
    
    confirma = input("Deseja continuar? (sim/nao): ").strip().lower()
    if confirma != 'sim':
        print("❌ Operação cancelada")
        return
    
    # Busca certificados
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, empresa_id, nome_certificado, cnpj, senha_pfx
            FROM certificados_digitais
            WHERE ativo = TRUE
            ORDER BY empresa_id, id
        """)
        
        certificados = cursor.fetchall()
        
        if not certificados:
            print("ℹ️  Nenhum certificado ativo encontrado")
            return
        
        print(f"\n📄 {len(certificados)} certificado(s) encontrado(s)\n")
        
        for cert in certificados:
            cert_id, empresa_id, nome, cnpj, senha_antiga = cert
            
            print("─" * 70)
            print(f"🔐 Certificado ID: {cert_id}")
            print(f"   Empresa ID: {empresa_id}")
            print(f"   Nome: {nome}")
            print(f"   CNPJ: {cnpj}")
            print(f"   Senha atual (tamanho): {len(senha_antiga)} chars")
            
            # Verifica se já está em formato Fernet (>= 50 chars)
            if len(senha_antiga) >= 50:
                print("   Status: ✅ JÁ CRIPTOGRAFADA")
                resposta = input("   Re-criptografar mesmo assim? (s/n): ").strip().lower()
                if resposta != 's':
                    print("   ⏭️  Pulando...")
                    continue
            else:
                print("   Status: ⚠️  POSSIVELMENTE EM TEXTO PLANO")
            
            # Solicita senha em texto plano
            senha_texto = input("   Digite a senha do certificado: ").strip()
            
            if not senha_texto:
                print("   ❌ Senha vazia, pulando...")
                continue
            
            try:
                # Criptografa
                senha_nova = criptografar_senha(senha_texto, chave)
                print(f"   ✅ Nova senha criptografada ({len(senha_nova)} chars)")
                
                # Atualiza no banco
                cursor.execute("""
                    UPDATE certificados_digitais
                    SET senha_pfx = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (senha_nova, cert_id))
                
                conn.commit()
                print("   💾 Salvo no banco com sucesso!")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                conn.rollback()
        
        print("\n" + "="*70)
        print("✅ Processo concluído!")
        print("💡 Teste a busca de documentos agora")

if __name__ == '__main__':
    recriptografar_certificados()
```

#### Uso:

```bash
# Local (com .env)
python recriptografar_certificados.py

# Ou definindo FERNET_KEY manualmente:
export FERNET_KEY='u2izhbz5QoGb2bkfh3dT5ckGADuGcRnEwFTCZ-LY-r0='
python recriptografar_certificados.py
```

---

## 🧪 Como Testar

### Teste 1: Verificar Logs

1. Acesse os logs do Railway ou execute localmente
2. Tente buscar documentos
3. Observe as mensagens:

```
✅ BOM - Chave presente:
[CERT] FERNET_KEY lida do ambiente: SIM (44 chars)
[CERT] ✅ Senha descriptografada com sucesso

❌ RUIM - Chave ausente:
[CERT] FERNET_KEY lida do ambiente: NÃO (vazia)
[CERT] ❌ FERNET_KEY não configurada no ambiente

❌ RUIM - Senha inválida:
[CERT] Senha em formato inválido: Senha do certificado em formato inválido...
[CERT] Tamanho da senha_cripto recebida: 15 chars
```

### Teste 2: Buscar Documentos

1. Acesse: **📑 Relatórios Fiscais - NF-e e CT-e**
2. Selecione um certificado
3. Clique em **🔍 Buscar Documentos**
4. Resultado esperado:
   - ✅ **Sucesso:** "Busca concluída! X documentos encontrados"
   - ❌ **Erro:** Verifique logs conforme Teste 1

### Teste 3: Cadastro de Novo Certificado

1. Cadastre um certificado novo
2. Observe os logs:
   ```
   [CERTIFICADO] FERNET_KEY para salvar: ✅ Presente (44 chars)
   [CERTIFICADO] ✅ Senha criptografada: 112 chars
   ```
3. Tente buscar documentos com esse certificado novo

---

## 📊 Checklist de Verificação

Marque cada item ANTES de considerar o problema resolvido:

- [ ] **FERNET_KEY configurada** no Railway
- [ ] **Logs mostram:** `FERNET_KEY lida do ambiente: SIM (44 chars)`
- [ ] **Certificado cadastrado** após configurar FERNET_KEY
- [ ] **Busca de documentos funciona** sem erro de senha
- [ ] **Logs mostram:** `✅ Senha descriptografada com sucesso`

---

## 🔒 Segurança da FERNET_KEY

### O que é?

- **Fernet:** Criptografia simétrica (mesma chave para criptografar e descriptografar)
- **Comprimento:** 44 caracteres base64 (32 bytes entropy)
- **Geração:** `Fernet.generate_key()` do módulo `cryptography`

### Boas Práticas

✅ **FAZER:**
- Armazenar em variáveis de ambiente (.env local, Railway Variables)
- Usar a MESMA chave em todos os ambientes que compartilham o banco
- Fazer backup seguro da chave
- Rotacionar chave periodicamente (com re-criptografia)

❌ **NÃO FAZER:**
- Commitar a chave no Git
- Usar chaves diferentes entre desenvolvimento e produção
- Compartilhar a chave publicamente
- Perder a chave (senhas se tornam irrecuperáveis)

---

## 🆘 Ajuda Adicional

### Problema: FERNET_KEY configurada mas ainda dá erro

**Causa provável:** Certificados foram salvos com chave diferente

**Solução:**
1. Re-cadastre os certificados (Solução 2)
2. OU use script de re-criptografia (Solução 3)

### Problema: Não sei a senha do certificado

**Causa:** Empresa não forneceu ou perdeu a senha

**Solução:**
1. Entre em contato com a empresa certificadora (AC)
2. Pode ser necessário emitir novo certificado
3. Se for certificado de teste (homologação), AC geralmente fornece senha

### Problema: FERNET_KEY sumiu ou corrompeu

**Causa:** Variável de ambiente foi alterada/deletada

**Impacto:** ❌ TODAS as senhas se tornam irrecuperáveis

**Solução:**
1. Restaurar backup da chave (se houver)
2. OU re-cadastrar TODOS os certificados com Solução 2

---

## 📝 Próximos Passos

1. ✅ **Implementar logging detalhado** (CONCLUÍDO)
2. ⏳ **Configurar FERNET_KEY no Railway** (PENDENTE - usuário)
3. ⏳ **Testar busca de documentos** (PENDENTE - após config)
4. 📋 **Criar script de re-criptografia** (OPCIONAL - se necessário)
5. 📄 **Documentar no README** (PENDENTE)

---

**Última Atualização:** 19 de Fevereiro de 2026  
**Autor:** Sistema Financeiro DWM  
**Status:** 🔧 Em Implementação
