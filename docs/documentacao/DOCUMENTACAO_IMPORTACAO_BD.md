# Documentação: Sistema de Importação Inteligente de Banco de Dados

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Funcionalidades](#funcionalidades)
4. [Fluxo de Importação](#fluxo-de-importação)
5. [Mapeamento Automático](#mapeamento-automático)
6. [Sistema de Rollback](#sistema-de-rollback)
7. [API Endpoints](#api-endpoints)
8. [Interface Administrativa](#interface-administrativa)
9. [Segurança](#segurança)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Sistema inteligente para importação de dados de bancos PostgreSQL externos para o sistema financeiro. Oferece:

- **Mapeamento Automático**: Algoritmo inteligente sugere correspondências entre tabelas
- **Mapeamento Manual**: Administrador pode ajustar/corrigir mapeamentos
- **Validação**: Preview antes da importação
- **Rollback Completo**: Sistema reversível com backup automático
- **Auditoria**: Log completo de todas as operações
- **Multi-tenant Safe**: Respeita isolamento de empresas

### Casos de Uso

1. **Migração de Cliente**: Importar dados quando cliente contrata o sistema
2. **Consolidação**: Unificar dados de múltiplas bases
3. **Backup Restore**: Restaurar dados de backups externos
4. **Integração**: Sincronizar com sistemas legados

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                  Interface Web (admin_import.html)          │
├─────────────────────────────────────────────────────────────┤
│                   API Routes (import_routes.py)             │
├─────────────────────────────────────────────────────────────┤
│            Import Manager (database_import_manager.py)      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Schema       │  │ Mapping      │  │ Backup          │  │
│  │ Analyzer     │  │ Engine       │  │ Manager         │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              Banco de Dados (PostgreSQL)                    │
│  ┌──────────────────┐  ┌───────────────────────────────┐  │
│  │ Banco Interno    │  │ Banco Externo (Cliente)       │  │
│  │ (erp_financeiro) │  │ (Conexão Temporária)          │  │
│  └──────────────────┘  └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Tabelas do Sistema

#### 1. **import_historico**
Registro de todas as importações

```sql
CREATE TABLE import_historico (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    banco_origem VARCHAR(255),
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INTEGER,
    status VARCHAR(50) DEFAULT 'em_andamento',
    total_registros INTEGER DEFAULT 0,
    registros_importados INTEGER DEFAULT 0,
    registros_erro INTEGER DEFAULT 0,
    tempo_execucao INTEGER,
    hash_dados VARCHAR(64),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

**Campos**:
- `status`: `preparando`, `em_andamento`, `concluido`, `concluido_com_erros`, `erro`, `revertido`
- `hash_dados`: Hash MD5 dos dados para detecção de duplicatas

#### 2. **import_mapeamento_tabelas**
Mapeamento entre tabelas

```sql
CREATE TABLE import_mapeamento_tabelas (
    id SERIAL PRIMARY KEY,
    import_id INTEGER NOT NULL,
    tabela_origem VARCHAR(255) NOT NULL,
    tabela_destino VARCHAR(255) NOT NULL,
    condicao_importacao TEXT,
    ordem_execucao INTEGER DEFAULT 0,
    ativo BOOLEAN DEFAULT true,
    FOREIGN KEY (import_id) REFERENCES import_historico(id) ON DELETE CASCADE
);
```

#### 3. **import_mapeamento_colunas**
Mapeamento entre colunas

```sql
CREATE TABLE import_mapeamento_colunas (
    id SERIAL PRIMARY KEY,
    mapeamento_tabela_id INTEGER NOT NULL,
    coluna_origem VARCHAR(255) NOT NULL,
    coluna_destino VARCHAR(255) NOT NULL,
    tipo_transformacao VARCHAR(50),
    valor_padrao TEXT,
    obrigatorio BOOLEAN DEFAULT false,
    FOREIGN KEY (mapeamento_tabela_id) REFERENCES import_mapeamento_tabelas(id) ON DELETE CASCADE
);
```

**Transformações Suportadas**:
- `uppercase`: Converter para maiúsculas
- `lowercase`: Converter para minúsculas
- `date_format`: Reformatar datas
- `currency`: Formatar valores monetários
- `custom_sql`: Expressão SQL customizada

#### 4. **import_backup**
Snapshot de dados antes da importação

```sql
CREATE TABLE import_backup (
    id SERIAL PRIMARY KEY,
    import_id INTEGER NOT NULL,
    tabela VARCHAR(255) NOT NULL,
    registro_id INTEGER NOT NULL,
    dados_antigos JSONB,
    operacao VARCHAR(20) NOT NULL,
    data_backup TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (import_id) REFERENCES import_historico(id) ON DELETE CASCADE
);
```

**Operações**:
- `INSERT`: Novo registro criado
- `UPDATE`: Registro existente atualizado
- `DELETE`: Registro deletado

#### 5. **import_log_erros**
Log de erros durante importação

```sql
CREATE TABLE import_log_erros (
    id SERIAL PRIMARY KEY,
    import_id INTEGER NOT NULL,
    tabela VARCHAR(255),
    registro JSONB,
    erro TEXT,
    data_erro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (import_id) REFERENCES import_historico(id) ON DELETE CASCADE
);
```

---

## ⚙️ Funcionalidades

### 1. Análise de Schema

**Função**: `get_external_database_schema()`

Analisa banco externo e retorna:
- Lista de todas as tabelas
- Colunas de cada tabela com tipos
- Total de registros por tabela
- Constraints e índices

**Exemplo de Retorno**:
```json
{
  "clientes": {
    "columns": [
      {
        "column_name": "id",
        "data_type": "integer",
        "is_nullable": "NO",
        "column_default": "nextval('clientes_id_seq')"
      },
      {
        "column_name": "nome",
        "data_type": "character varying",
        "is_nullable": "NO",
        "column_default": null
      }
    ],
    "total_registros": 1250
  }
}
```

### 2. Mapeamento Automático

**Algoritmo de Similaridade**

```python
def _calculate_table_similarity(ext_name, ext_info, int_name, int_info):
    score = 0.0
    
    # 40% - Similaridade de nome (Levenshtein)
    name_similarity = _string_similarity(ext_name, int_name)
    score += name_similarity * 0.4
    
    # 60% - Colunas em comum
    ext_cols = {col['column_name'].lower() for col in ext_info['columns']}
    int_cols = {col['column_name'].lower() for col in int_info['columns']}
    
    common_cols = len(ext_cols & int_cols)
    total_cols = len(ext_cols | int_cols)
    column_similarity = common_cols / total_cols
    score += column_similarity * 0.6
    
    return score
```

**Níveis de Confiança**:
- **>80%**: Verde - Altamente confiável
- **50-80%**: Amarelo - Revisar recomendado
- **<50%**: Vermelho - Requer ajuste manual

**Exemplo de Sugestão**:
```json
{
  "tabela_origem": "customer",
  "tabela_destino": "clientes",
  "score_similaridade": 85.5,
  "total_registros": 1250,
  "colunas_origem": 12,
  "colunas_destino": 15,
  "mapeamento_colunas": [
    {
      "coluna_origem": "customer_name",
      "coluna_destino": "nome",
      "score": 78.3,
      "tipo_origem": "varchar",
      "tipo_destino": "varchar",
      "compativel": true
    }
  ]
}
```

### 3. Validação de Dados

Antes da importação, o sistema valida:
- **Tipos de dados**: Compatibilidade entre origem/destino
- **Constraints**: NOT NULL, UNIQUE, FOREIGN KEY
- **Valores**: Range, formato, enumerações
- **Duplicatas**: Detecção por chaves primárias

### 4. Execução da Importação

**Processo**:
1. Criar registro em `import_historico`
2. Para cada tabela no mapeamento:
   - Buscar dados da origem
   - Para cada registro:
     - Criar backup se registro existe
     - Aplicar transformações
     - Inserir/atualizar no destino
     - Registrar erro se falhar
3. Atualizar estatísticas
4. Commit ou Rollback

**Ordem de Execução**:
Tabelas são processadas na ordem definida em `ordem_execucao`, respeitando dependências de Foreign Keys.

### 5. Sistema de Rollback

**Estratégias de Backup**:

1. **Snapshot Completo**: Copia estado atual antes da importação
2. **Backup Incremental**: Registra apenas alterações
3. **Backup Seletivo**: Apenas tabelas modificadas

**Processo de Rollback**:
```python
def rollback_import(import_id):
    # Buscar todos os backups
    backups = fetch_backups(import_id)
    
    # Processar em ordem reversa
    for backup in reversed(backups):
        if backup.operacao == 'INSERT':
            # Deletar registro inserido
            delete_record(backup.tabela, backup.registro_id)
        elif backup.operacao == 'UPDATE':
            # Restaurar dados antigos
            restore_record(backup.tabela, backup.dados_antigos)
        elif backup.operacao == 'DELETE':
            # Re-inserir registro deletado
            insert_record(backup.tabela, backup.dados_antigos)
    
    # Marcar como revertido
    update_status(import_id, 'revertido')
```

---

## 📊 Fluxo de Importação

### Fluxo Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CONFIGURAÇÃO                                             │
│    - Conectar banco externo                                 │
│    - Obter schema                                          │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ANÁLISE                                                  │
│    - Comparar schemas                                       │
│    - Gerar sugestões automáticas                          │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. MAPEAMENTO                                               │
│    - Revisar sugestões                                      │
│    - Ajustar mapeamentos                                    │
│    - Definir transformações                                 │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. VALIDAÇÃO                                                │
│    - Validar tipos                                          │
│    - Verificar constraints                                  │
│    - Testar conexões                                        │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. BACKUP                                                   │
│    - Criar snapshot                                         │
│    - Gerar hash dos dados                                  │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. IMPORTAÇÃO                                               │
│    - Executar por tabela                                    │
│    - Aplicar transformações                                 │
│    - Registrar progresso                                    │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. FINALIZAÇÃO                                              │
│    - Consolidar estatísticas                                │
│    - Gerar relatório                                        │
│    - Enviar notificação                                     │
└─────────────────────────────────────────────────────────────┘
```

### Estados da Importação

```
preparando → em_andamento → concluido
                          ↓
                     concluido_com_erros
                          ↓
                        erro
                          ↓
                      revertido
```

---

## 🔗 API Endpoints

### 1. Obter Schema Externo

```http
POST /api/admin/import/schema/externo
Content-Type: application/json

{
  "host": "cliente.postgres.database.azure.com",
  "port": 5432,
  "database": "cliente_producao",
  "user": "admin",
  "password": "senha_segura"
}
```

**Response 200**:
```json
{
  "success": true,
  "schema": {...},
  "total_tabelas": 25,
  "total_registros": 150000
}
```

### 2. Obter Schema Interno

```http
GET /api/admin/import/schema/interno
```

**Response 200**:
```json
{
  "success": true,
  "schema": {...},
  "total_tabelas": 30
}
```

### 3. Gerar Sugestões de Mapeamento

```http
POST /api/admin/import/sugestao-mapeamento
Content-Type: application/json

{
  "schema_externo": {...},
  "schema_interno": {...}
}
```

**Response 200**:
```json
{
  "success": true,
  "sugestoes": [
    {
      "tabela_origem": "customers",
      "tabela_destino": "clientes",
      "score_similaridade": 92.5,
      "total_registros": 1500,
      "mapeamento_colunas": [...]
    }
  ],
  "total_mapeamentos": 15
}
```

### 4. Criar Importação

```http
POST /api/admin/import/criar
Content-Type: application/json

{
  "nome": "Importação Cliente ABC - Janeiro 2026",
  "descricao": "Migração completa do sistema antigo",
  "banco_origem": "cliente_abc_old",
  "mapeamentos": [...]
}
```

**Response 201**:
```json
{
  "success": true,
  "import_id": 42,
  "message": "Importação criada com sucesso"
}
```

### 5. Executar Importação

```http
POST /api/admin/import/executar/42
Content-Type: application/json

{
  "db_config": {...}
}
```

**Response 200**:
```json
{
  "success": true,
  "registros_importados": 148523,
  "registros_erro": 15,
  "erros": [...]
}
```

### 6. Listar Importações

```http
GET /api/admin/import/listar
```

**Response 200**:
```json
{
  "success": true,
  "imports": [
    {
      "id": 42,
      "nome": "Importação Cliente ABC",
      "status": "concluido",
      "data_importacao": "2026-01-26T10:30:00",
      "registros_importados": 148523,
      "tempo_execucao": 320
    }
  ]
}
```

### 7. Detalhes da Importação

```http
GET /api/admin/import/detalhes/42
```

**Response 200**:
```json
{
  "success": true,
  "import": {...},
  "mapeamentos": [...],
  "erros": [...]
}
```

### 8. Reverter Importação

```http
POST /api/admin/import/reverter/42
```

**Response 200**:
```json
{
  "success": true,
  "message": "Importação revertida com sucesso"
}
```

### 9. Deletar Importação

```http
DELETE /api/admin/import/deletar/42
```

**Response 200**:
```json
{
  "success": true,
  "message": "Importação deletada com sucesso"
}
```

---

## 🖥️ Interface Administrativa

### Página: `/admin/import`

#### Aba 1: Nova Importação

**Seção 1 - Configuração do Banco**
- Host, Porta, Database, Usuário, Senha
- Botão "Testar Conexão"
- Feedback visual de sucesso/erro

**Seção 2 - Análise do Schema**
- Tabelas detectadas
- Total de registros
- Comparação com schema interno

**Seção 3 - Mapeamento Automático**
- Botão "Gerar Mapeamento"
- Tabela com sugestões
- Score de similaridade colorido
- Botões para ver/editar/remover

**Seção 4 - Execução**
- Nome da importação
- Descrição
- Botão "Executar"
- Barra de progresso em tempo real

#### Aba 2: Histórico

- Lista de todas as importações
- Filtros por status, data, usuário
- Ações: Ver detalhes, Reverter, Deletar
- Estatísticas por importação

#### Aba 3: Mapeamentos Salvos

- Mapeamentos reutilizáveis
- Editar mapeamentos existentes
- Duplicar mapeamentos
- Exportar/Importar configurações

---

## 🔒 Segurança

### Permissões

**Permissão Requerida**: `admin`

```python
@require_permission('admin')
def execute_import():
    # Apenas administradores podem importar
    pass
```

### Validações

1. **Autenticação**: Token de sessão obrigatório
2. **Autorização**: Permissão `admin` verificada
3. **Input Sanitization**: Escape de SQL injection
4. **Rate Limiting**: Limite de requisições por hora
5. **Audit Log**: Todas as operações registradas

### Dados Sensíveis

**Senhas de Banco**:
- Nunca armazenadas no banco
- Transmitidas apenas em HTTPS
- Criptografadas em memória
- Limpas após uso

---

## 🛠️ Troubleshooting

### Erro: "Tabela não encontrada"

**Causa**: Schema incorreto ou permissões
**Solução**: 
```sql
-- Verificar permissões
GRANT SELECT ON ALL TABLES IN SCHEMA public TO usuario_import;
```

### Erro: "Tipo de dado incompatível"

**Causa**: Mapeamento incorreto de tipos
**Solução**: Adicionar transformação no mapeamento
```json
{
  "tipo_transformacao": "cast_integer",
  "expressao_sql": "CAST(coluna AS INTEGER)"
}
```

### Importação Muito Lenta

**Otimizações**:
1. Aumentar `work_mem` do PostgreSQL
2. Desabilitar índices temporariamente
3. Usar `COPY` ao invés de `INSERT`
4. Processar em batches menores

### Rollback Falhou

**Diagnóstico**:
1. Verificar integridade dos backups
2. Checar constraints violadas
3. Validar foreign keys

**Recovery Manual**:
```sql
-- Restaurar de backup manual
SELECT * FROM import_backup WHERE import_id = 42;
```

---

## 📈 Métricas e Monitoramento

### Dashboard de Importação

**Métricas em Tempo Real**:
- Registros processados / Total
- Taxa de processamento (reg/s)
- Tempo estimado restante
- Memória utilizada
- Erros acumulados

### Alertas

**Condições de Alerta**:
- Taxa de erro > 5%
- Tempo de execução > 2x estimado
- Memória > 80% utilizada
- Conexão perdida com banco externo

---

## 🚀 Próximas Melhorias

1. **Importação Incremental**: Apenas novos/modificados
2. **Agendamento**: Importações programadas
3. **Webhook Notificação**: Callback quando concluir
4. **Preview de Dados**: Visualizar antes de importar
5. **Transformações Customizadas**: JavaScript/Python inline
6. **Multi-thread**: Paralelizar importação
7. **Compressão**: Otimizar backups grandes
8. **Export**: Exportar para outros formatos (CSV, JSON)

---

**Última Atualização**: 26/01/2026  
**Versão**: 1.0.0  
**Autor**: Sistema Financeiro DWM Team
