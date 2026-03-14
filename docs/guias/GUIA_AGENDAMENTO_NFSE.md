# 📅 Guia de Agendamento Automático - Busca NFS-e

## 🎯 Objetivo

Configurar busca automática diária de NFS-e via Ambiente Nacional para todos os certificados cadastrados no sistema.

---

## 📋 Pré-requisitos

1. ✅ Script `agendar_busca_nfse.py` criado
2. ✅ Certificados digitais cadastrados no sistema
3. ✅ Ambiente Nacional configurado e funcional
4. ✅ Conexão com banco de dados ativa

---

## 🪟 Windows - Task Scheduler

### **Método 1: Interface Gráfica**

1. Abrir **Agendador de Tarefas** (Task Scheduler)
   - Pressione `Win + R` → digite `taskschd.msc` → Enter

2. Criar Nova Tarefa
   - Painel direito → **Criar Tarefa Básica...**

3. **Nome e Descrição**
   ```
   Nome: Busca Automática NFS-e
   Descrição: Busca diária de NFS-e via Ambiente Nacional
   ```

4. **Gatilho (Trigger)**
   - Escolher: **Diário**
   - Horário: `02:00` (2h da manhã)
   - Recorrente: **Todos os dias**

5. **Ação**
   - Escolher: **Iniciar um programa**
   - Programa/script:
     ```
     C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\.venv\Scripts\python.exe
     ```
   - Argumentos:
     ```
     agendar_busca_nfse.py
     ```
   - Iniciar em (pasta):
     ```
     C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm
     ```

6. **Configurações Avançadas**
   - ☑️ Executar com privilégios mais altos
   - ☑️ Executar estando o usuário conectado ou não
   - ☑️ Executar o mais breve possível após perder uma inicialização agendada

7. **Finalizar** → Salvar

### **Método 2: PowerShell (Automático)**

Criar arquivo `criar_agendamento.ps1`:

```powershell
# Criar tarefa agendada para busca automática de NFS-e

$action = New-ScheduledTaskAction `
    -Execute "C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\.venv\Scripts\python.exe" `
    -Argument "agendar_busca_nfse.py" `
    -WorkingDirectory "C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm"

$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName "Busca Automática NFS-e" `
    -Description "Busca diária de NFS-e via Ambiente Nacional" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User $env:USERNAME `
    -RunLevel Highest

Write-Host "✅ Tarefa agendada criada com sucesso!" -ForegroundColor Green
```

Executar:
```powershell
powershell -ExecutionPolicy Bypass -File criar_agendamento.ps1
```

---

## 🐧 Linux - Cron

### **Configurar Cron Job**

1. Abrir editor de cron:
   ```bash
   crontab -e
   ```

2. Adicionar linha:
   ```cron
   # Busca automática NFS-e - Todos os dias às 2h
   0 2 * * * cd /app/Sistema_financeiro_dwm && /app/.venv/bin/python agendar_busca_nfse.py >> logs/busca_nfse_automatica.log 2>&1
   ```

3. Salvar e sair (`:wq` no vim / `Ctrl+O` e `Ctrl+X` no nano)

4. Verificar cron instalado:
   ```bash
   crontab -l
   ```

### **Sintaxe do Cron**

```
┌───────────── minuto (0-59)
│ ┌───────────── hora (0-23)
│ │ ┌───────────── dia do mês (1-31)
│ │ │ ┌───────────── mês (1-12)
│ │ │ │ ┌───────────── dia da semana (0-6, 0=domingo)
│ │ │ │ │
0 2 * * *  comando
```

### **Exemplos de Agendamento**

```cron
# Todos os dias às 2h
0 2 * * * /caminho/script.py

# A cada 6 horas
0 */6 * * * /caminho/script.py

# Segunda a Sexta às 8h
0 8 * * 1-5 /caminho/script.py

# Primeiro dia de cada mês às 3h
0 3 1 * * /caminho/script.py
```

---

## 🐳 Docker

### **Docker Compose com Cron**

Adicionar ao `docker-compose.yml`:

```yaml
services:
  busca-nfse-scheduler:
    build: .
    container_name: nfse-scheduler
    restart: unless-stopped
    environment:
      - TZ=America/Sao_Paulo
    volumes:
      - ./Sistema_financeiro_dwm:/app
      - ./logs:/app/logs
      - ./storage:/app/storage
    command: >
      sh -c "
        echo '0 2 * * * cd /app && python agendar_busca_nfse.py >> logs/busca_nfse_automatica.log 2>&1' | crontab - &&
        crond -f -l 2
      "
```

---

## ☁️ Railway / Heroku (Cloud)

### **Heroku Scheduler**

1. Instalar addon:
   ```bash
   heroku addons:create scheduler:standard
   ```

2. Abrir dashboard:
   ```bash
   heroku addons:open scheduler
   ```

3. Adicionar job:
   - Comando: `python agendar_busca_nfse.py`
   - Frequência: **Daily** às **02:00 UTC**

### **Railway Cron Jobs**

Adicionar ao `railway.toml`:

```toml
[[crons]]
  schedule = "0 2 * * *"
  command = "python agendar_busca_nfse.py"
```

---

## 📊 Monitoramento

### **Verificar Logs**

**Windows:**
```powershell
Get-Content logs\busca_nfse_automatica.log -Tail 50 -Wait
```

**Linux:**
```bash
tail -f logs/busca_nfse_automatica.log
```

### **Verificar Última Execução**

**Windows (Task Scheduler):**
1. Abrir Task Scheduler
2. Biblioteca do Agendador de Tarefas
3. Buscar "Busca Automática NFS-e"
4. Aba **Histórico**

**Linux (Cron):**
```bash
grep CRON /var/log/syslog | grep agendar_busca_nfse
```

---

## 🔧 Testes

### **Executar Manualmente**

**Windows:**
```powershell
cd "C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm"
.\.venv\Scripts\python.exe agendar_busca_nfse.py
```

**Linux:**
```bash
cd /app/Sistema_financeiro_dwm
source .venv/bin/activate
python agendar_busca_nfse.py
```

### **Verificar Certificados Cadastrados**

```sql
SELECT 
    c.nome_amigavel,
    c.cnpj_extraido,
    c.ativo,
    c.validade_fim,
    e.razao_social
FROM nfse_certificados c
LEFT JOIN empresas e ON e.id = c.empresa_id
WHERE c.ativo = TRUE;
```

---

## ⚙️ Personalização

### **Alterar Horário de Execução**

Editar no Task Scheduler (Windows) ou crontab (Linux) conforme necessário.

**Recomendações:**
- **Madrugada (2h-4h):** Menos carga no servidor
- **Após horário comercial (19h-21h):** Captura notas do dia
- **Múltiplas execuções:** Ex: 2h e 14h (cobrir manhã e tarde)

### **Limitar Documentos por Execução**

Editar `agendar_busca_nfse.py`, linha ~174:

```python
max_documentos=100  # Alterar conforme necessário
```

### **Ambiente (Produção/Homologação)**

Editar `agendar_busca_nfse.py`, linha ~173:

```python
ambiente='producao'  # Ou 'homologacao' para testes
```

---

## 🚨 Troubleshooting

### **Erro: Certificado não encontrado**

**Solução:** Verificar se certificados estão cadastrados:
```sql
SELECT COUNT(*) FROM nfse_certificados WHERE ativo = TRUE;
```

### **Erro: Permissão negada**

**Windows:** Executar Task Scheduler como Administrador

**Linux:** Verificar permissões:
```bash
chmod +x agendar_busca_nfse.py
```

### **Erro: Banco de dados não conecta**

**Solução:** Verificar `database_postgresql.py`:
- Host, porta, usuário, senha corretos
- Conexão de rede permitida
- Banco PostgreSQL rodando

### **Script não executa**

**Verificar:**
1. ✅ Python instalado e no PATH
2. ✅ Virtual environment ativado
3. ✅ Dependências instaladas (`pip install -r requirements.txt`)
4. ✅ Caminho absoluto correto no agendamento

---

## 📧 Notificações (Opcional)

### **Enviar Email ao Concluir**

Adicionar ao final de `executar_busca_automatica()`:

```python
# Enviar notificação por email
from email.mime.text import MIMEText
import smtplib

msg = MIMEText(f"""
Busca automática de NFS-e concluída!

Total de NFS-e: {total_nfse}
Certificados processados: {total_sucesso}/{total_processados}
Erros: {total_erros}

Veja logs completos em: logs/busca_nfse_automatica.log
""")

msg['Subject'] = f'✅ Busca NFS-e - {total_nfse} notas obtidas'
msg['From'] = 'sistema@empresa.com.br'
msg['To'] = 'admin@empresa.com.br'

smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('usuario', 'senha')
smtp.send_message(msg)
smtp.quit()
```

---

## ✅ Checklist de Implantação

- [ ] Script `agendar_busca_nfse.py` criado
- [ ] Pasta `logs/` criada
- [ ] Certificados cadastrados no sistema
- [ ] Teste manual executado com sucesso
- [ ] Agendamento configurado (Task Scheduler/Cron)
- [ ] Verificar logs após primeira execução
- [ ] Confirmar NFS-e sendo salvas no banco
- [ ] Monitorar por 1 semana

---

## 📚 Referências

- Documentação Ambiente Nacional: https://adn.nfse.gov.br/docs
- Task Scheduler: https://docs.microsoft.com/pt-br/windows/win32/taskschd
- Crontab Guru: https://crontab.guru
- Python Schedule: https://schedule.readthedocs.io

---

**Última atualização:** 2026-02-15  
**Autor:** Sistema Financeiro DWM
