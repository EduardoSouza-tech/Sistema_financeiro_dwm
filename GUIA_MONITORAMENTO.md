# 📊 GUIA DE MONITORAMENTO

## 🎯 Visão Geral

O sistema possui monitoramento completo com **logging estruturado** e **Sentry** para rastreamento de erros em produção.

---

## 📝 LOGGING ESTRUTURADO

### Configuração

O sistema usa logging estruturado com múltiplos níveis e destinos:

```python
from logger_config import setup_logging, get_logger

# Configurar logger
logger = setup_logging(
    app_name='sistema_financeiro',
    log_level='INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    enable_json=False  # True para formato JSON (produção)
)
```

### Níveis de Log

| Nível | Uso | Exemplo |
|-------|-----|---------|
| **DEBUG** | Informações detalhadas para debugging | `logger.debug("Query executada: SELECT * FROM users")` |
| **INFO** | Operações normais do sistema | `logger.info("Usuário logado", extra={'user_id': 123})` |
| **WARNING** | Algo inesperado mas não crítico | `logger.warning("Cache próximo do limite")` |
| **ERROR** | Erro que precisa atenção | `logger.error("Falha ao processar pagamento", exc_info=True)` |
| **CRITICAL** | Erro grave que afeta o sistema | `logger.critical("Banco de dados inacessível")` |

### Arquivos de Log

O sistema gera 4 tipos de logs:

```
logs/
├── sistema_financeiro.log           # Log geral (rotativo, 10MB, 5 backups)
├── sistema_financeiro_errors.log    # Apenas erros (rotativo, 10MB, 10 backups)
├── sistema_financeiro_access.log    # Log de acesso/auditoria (diário, 30 dias)
└── ...
```

### Uso Básico

```python
from logger_config import get_logger

logger = get_logger()

# Logs simples
logger.info("Operação concluída")
logger.error("Erro ao salvar dados")

# Logs com contexto
logger.info(
    "Usuário criado",
    extra={
        'user_id': 123,
        'email': 'usuario@exemplo.com',
        'ip': '192.168.1.1'
    }
)

# Log de exceção com traceback
try:
    resultado = 1 / 0
except Exception as e:
    logger.error("Erro na divisão", exc_info=True)
```

### Log de Requisições (Auditoria)

```python
from logger_config import log_request

@app.before_request
def audit_request():
    log_request(
        request,
        user_id=session.get('usuario_id'),
        proprietario_id=session.get('proprietario_id')
    )
```

### Log de Erros Detalhado

```python
from logger_config import log_error

try:
    processar_pagamento()
except Exception as e:
    log_error(
        error=e,
        request=request,
        user_id=usuario_id,
        context={'valor': 100.0, 'metodo': 'PIX'}
    )
```

---

## 🔔 SENTRY - MONITORAMENTO EM PRODUÇÃO

### Configuração

#### 1. Obter DSN do Sentry

1. Criar conta em [sentry.io](https://sentry.io)
2. Criar novo projeto (Python/Flask)
3. Copiar o DSN fornecido

#### 2. Configurar variável de ambiente

```bash
# Railway
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx

# Local (.env)
export SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

#### 3. Inicializar no código

```python
from sentry_config import init_sentry

# Inicializar Sentry
SENTRY_ENABLED = init_sentry(
    environment='production',  # production, staging, development
    traces_sample_rate=0.1     # 10% das transações (performance monitoring)
)
```

### Recursos do Sentry

#### 1. Captura Automática de Erros

Todos os erros não tratados são automaticamente enviados ao Sentry:

```python
# Erro será capturado automaticamente
def processar_dados():
    resultado = 1 / 0  # ZeroDivisionError → Sentry
```

#### 2. Captura Manual de Exceções

```python
from sentry_config import capture_exception

try:
    processar_pagamento()
except Exception as e:
    capture_exception(
        error=e,
        context={
            'operacao': 'pagamento',
            'valor': 100.0,
            'metodo': 'PIX'
        },
        level='error'  # fatal, error, warning, info, debug
    )
```

#### 3. Contexto do Usuário

```python
from sentry_config import set_user_context, clear_user_context

# Após login
set_user_context(
    user_id=123,
    email='usuario@exemplo.com',
    username='João Silva',
    proprietario_id=1
)

# Após logout
clear_user_context()
```

#### 4. Breadcrumbs (Rastros)

```python
from sentry_config import add_breadcrumb

# Adicionar breadcrumb antes de operação
add_breadcrumb('Iniciando processamento de pagamento', category='payment')
add_breadcrumb('Validando dados do cartão', category='payment', level='info')
add_breadcrumb('Conectando ao gateway', category='payment', data={'gateway': 'Stripe'})

# Se houver erro, Sentry mostrará todos os breadcrumbs
```

#### 5. Performance Monitoring

```python
from sentry_config import measure_performance

@measure_performance('database.query')
def buscar_lancamentos():
    # Operação será medida no Sentry
    return db.query(...)
```

#### 6. Transações Personalizadas

```python
from sentry_config import set_transaction_name

@app.route('/api/lancamentos', methods=['POST'])
def criar_lancamento():
    set_transaction_name('POST /api/lancamentos')
    # ...
```

### Dashboard do Sentry

O Sentry fornece:

- **Issues** - Erros agrupados por tipo
- **Performance** - Tempo de resposta de APIs
- **Releases** - Tracking de deploys
- **Alerts** - Notificações por email/Slack
- **Trends** - Análise de tendências

---

## 🔍 MONITORAMENTO EM DESENVOLVIMENTO

### Logs Console (Coloridos)

```bash
# Executar com logs coloridos
python web_server.py

# Saída:
# 2026-01-14 10:30:15 | INFO | sistema_financeiro | Servidor iniciado
# 2026-01-14 10:30:20 | WARNING | sistema_financeiro | Cache cheio
# 2026-01-14 10:30:25 | ERROR | sistema_financeiro | Erro ao conectar
```

### Logs JSON (Produção)

```bash
# Ativar logs em JSON
LOG_LEVEL=INFO python web_server.py

# Saída JSON (fácil para parsing):
# {"timestamp": "2026-01-14T10:30:15", "level": "INFO", "message": "Servidor iniciado"}
```

---

## 📊 MÉTRICAS E ALERTAS

### Configurar Alertas no Sentry

1. **Issues → Alerts → Create Alert Rule**
2. Configurar condições:
   - "When an issue is first seen"
   - "When an issue exceeds 10 events in 1h"
   - "When error rate exceeds 5% in 1h"
3. Adicionar ações:
   - Email
   - Slack
   - PagerDuty

### Monitorar Performance

```python
# No Sentry, você verá:
# - Tempo médio de resposta de cada endpoint
# - Queries lentas do banco
# - Operações que consomem mais tempo
```

---

## 🚨 TRATAMENTO DE ERROS

### Handler Global de Erros

```python
@app.errorhandler(Exception)
def handle_exception(e):
    # Log local
    logger.critical(f"Exceção não tratada: {e}", exc_info=True)
    
    # Enviar para Sentry
    if SENTRY_ENABLED:
        capture_exception(e, context={
            'path': request.path,
            'user_id': session.get('usuario_id')
        })
    
    return jsonify({'error': 'Erro interno'}), 500
```

### Erros Específicos

```python
@app.route('/api/pagamento', methods=['POST'])
def processar_pagamento():
    try:
        # Processar pagamento
        gateway.processar()
        logger.info("Pagamento processado com sucesso")
        return jsonify({'sucesso': True})
        
    except GatewayException as e:
        # Erro esperado do gateway
        logger.warning(f"Pagamento rejeitado: {e}")
        capture_exception(e, level='warning')
        return jsonify({'erro': 'Pagamento rejeitado'}), 400
        
    except Exception as e:
        # Erro inesperado
        logger.error(f"Erro ao processar pagamento: {e}", exc_info=True)
        capture_exception(e, level='error')
        return jsonify({'erro': 'Erro interno'}), 500
```

---

## 📈 ANÁLISE DE LOGS

### Pesquisar Logs

```bash
# Buscar por erro específico
grep "ERROR" logs/sistema_financeiro.log

# Buscar logs de usuário específico
grep "user_id.*123" logs/sistema_financeiro_access.log

# Últimos 100 erros
tail -100 logs/sistema_financeiro_errors.log
```

### Análise com Ferramentas

```bash
# Contar erros por tipo
cat logs/sistema_financeiro_errors.log | grep -o "ERROR.*" | sort | uniq -c

# Ver erros das últimas 24h
find logs/ -name "*.log" -mtime -1 -exec grep "ERROR" {} \;
```

---

## 🎯 CHECKLIST DE MONITORAMENTO

### Desenvolvimento

- [ ] Logs coloridos ativos
- [ ] Nível DEBUG para debugging
- [ ] Console mostrando requisições

### Staging

- [ ] Logs em JSON
- [ ] Nível INFO
- [ ] Sentry configurado
- [ ] Alertas para erros críticos

### Produção

- [ ] Logs estruturados em JSON
- [ ] Rotação de logs configurada
- [ ] Sentry ativo com alertas
- [ ] Performance monitoring (10% sample)
- [ ] Contexto de usuário configurado
- [ ] Dados sensíveis filtrados

---

## 📚 Variáveis de Ambiente

```bash
# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_JSON=false              # true para formato JSON

# Sentry
SENTRY_DSN=https://...      # DSN do Sentry
SENTRY_ENVIRONMENT=production  # production, staging, development
SENTRY_TRACES_SAMPLE_RATE=0.1  # Taxa de amostragem (0.0 a 1.0)
```

---

**Monitoramento completo para garantir estabilidade e rastreabilidade! 🚀**
