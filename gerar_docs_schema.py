"""
Gera documentação Markdown a partir do schema JSON extraído
Este script processa o schema_database.json e cria SCHEMA_DATABASE.md
"""
import json
from datetime import datetime

def carregar_schema():
    """Carrega o schema do arquivo JSON"""
    try:
        with open('schema_database.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Arquivo schema_database.json não encontrado")
        print("   Execute primeiro: extrair_schema.py")
        return None

def gerar_markdown(schema_info):
    """Gera documentação em Markdown do schema"""
    
    print("📝 Gerando documentação Markdown...")
    
    markdown = f"""# 📊 Schema do Banco de Dados - Sistema Financeiro

**Data de Extração**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}  
**Database**: PostgreSQL (Railway)  
**Total de Tabelas**: {len(schema_info['tabelas'])}

---

## 📋 Índice Geral

"""
    
    # Índice com estatísticas
    for idx, tabela in enumerate(sorted(schema_info['tabelas'], key=lambda x: x['nome']), 1):
        total_colunas = len(tabela['colunas'])
        total_fks = len(tabela['foreign_keys'])
        markdown += f"{idx}. **[{tabela['nome']}](#{tabela['nome'].replace('_', '-')})** ({total_colunas} colunas, {total_fks} FKs)\n"
    
    markdown += "\n---\n\n## 📈 Estatísticas Gerais\n\n"
    
    # Estatísticas globais
    total_colunas = sum(len(t['colunas']) for t in schema_info['tabelas'])
    total_fks = sum(len(t['foreign_keys']) for t in schema_info['tabelas'])
    total_indexes = sum(len(t['indexes']) for t in schema_info['tabelas'])
    total_constraints = sum(len(t['constraints']) for t in schema_info['tabelas'])
    
    markdown += f"- 📊 **Total de Tabelas**: {len(schema_info['tabelas'])}\n"
    markdown += f"- 📊 **Total de Colunas**: {total_colunas}\n"
    markdown += f"- 🔗 **Total de Foreign Keys**: {total_fks}\n"
    markdown += f"- 📇 **Total de Indexes**: {total_indexes}\n"
    markdown += f"- 🔐 **Total de Constraints**: {total_constraints}\n\n"
    
    # Top 5 tabelas mais complexas
    tabelas_ordenadas = sorted(schema_info['tabelas'], key=lambda x: len(x['colunas']), reverse=True)[:5]
    markdown += "### 🏆 Top 5 Tabelas Mais Complexas\n\n"
    for i, tabela in enumerate(tabelas_ordenadas, 1):
        markdown += f"{i}. `{tabela['nome']}` - {len(tabela['colunas'])} colunas\n"
    
    markdown += "\n---\n\n"
    
    # Detalhes de cada tabela
    for tabela in sorted(schema_info['tabelas'], key=lambda x: x['nome']):
        markdown += f"## 📦 `{tabela['nome']}`\n\n"
        
        # Estatísticas da tabela
        total_colunas = len(tabela['colunas'])
        total_fks = len(tabela['foreign_keys'])
        total_indexes = len(tabela['indexes'])
        total_constraints = len(tabela['constraints'])
        
        # Identificar primary key
        pk_cols = [c['coluna'] for c in tabela['constraints'] if c['tipo'] == 'PRIMARY KEY']
        pk_info = f"`{pk_cols[0]}`" if pk_cols else "❌ Sem PK"
        
        markdown += f"**📊 Estatísticas**:\n"
        markdown += f"- Colunas: {total_colunas}\n"
        markdown += f"- Primary Key: {pk_info}\n"
        markdown += f"- Foreign Keys: {total_fks}\n"
        markdown += f"- Indexes: {total_indexes}\n"
        markdown += f"- Constraints: {total_constraints}\n\n"
        
        # Colunas
        markdown += "### 📋 Colunas\n\n"
        markdown += "| # | Coluna | Tipo | Tamanho | Nullable | Default | Observações |\n"
        markdown += "|---|--------|------|---------|----------|---------|-------------|\n"
        
        for idx, col in enumerate(tabela['colunas'], 1):
            nullable = "✅" if col['nullable'] else "❌"
            tamanho = str(col['tamanho']) if col['tamanho'] else "-"
            default = col['default'] if col['default'] else "-"
            
            # Truncar default se for muito longo
            if len(str(default)) > 40:
                default = str(default)[:37] + "..."
            
            # Identificar se é PK ou FK
            obs = []
            if col['nome'] in pk_cols:
                obs.append("🔑 PK")
            
            fk_refs = [f for f in tabela['foreign_keys'] if f['coluna'] == col['nome']]
            if fk_refs:
                obs.append(f"🔗 FK → `{fk_refs[0]['referencia_tabela']}.{fk_refs[0]['referencia_coluna']}`")
            
            obs_str = " ".join(obs) if obs else "-"
            
            markdown += f"| {idx} | **`{col['nome']}`** | `{col['tipo']}` | {tamanho} | {nullable} | `{default}` | {obs_str} |\n"
        
        markdown += "\n"
        
        # Constraints
        if tabela['constraints']:
            markdown += "### 🔐 Constraints\n\n"
            markdown += "| Constraint | Tipo | Coluna(s) |\n"
            markdown += "|------------|------|-----------|\n"
            
            for const in tabela['constraints']:
                tipo_emoji = {
                    'PRIMARY KEY': '🔑',
                    'UNIQUE': '🔒',
                    'CHECK': '✔️'
                }.get(const['tipo'], '📌')
                
                markdown += f"| `{const['nome']}` | {tipo_emoji} {const['tipo']} | `{const['coluna']}` |\n"
            
            markdown += "\n"
        
        # Foreign Keys com detalhes
        if tabela['foreign_keys']:
            markdown += "### 🔗 Relacionamentos (Foreign Keys)\n\n"
            markdown += "| Coluna Local | ➡️ Tabela Referenciada | Coluna Referenciada | Descrição |\n"
            markdown += "|--------------|------------------------|---------------------|------------|\n"
            
            for fk in tabela['foreign_keys']:
                descricao = f"Vincula {tabela['nome']} com {fk['referencia_tabela']}"
                markdown += f"| `{fk['coluna']}` | `{fk['referencia_tabela']}` | `{fk['referencia_coluna']}` | {descricao} |\n"
            
            markdown += "\n"
        
        # Indexes
        if tabela['indexes']:
            markdown += "### 📇 Indexes\n\n"
            markdown += "| Nome do Index | Coluna | Tipo | Performance |\n"
            markdown += "|---------------|--------|------|-------------|\n"
            
            for idx in tabela['indexes']:
                tipo = "🔒 Unique" if idx['unique'] else "📊 Non-Unique"
                perf = "🚀 Rápido" if idx['unique'] else "⚡ Otimizado"
                markdown += f"| `{idx['nome']}` | `{idx['coluna']}` | {tipo} | {perf} |\n"
            
            markdown += "\n"
        
        markdown += "---\n\n"
    
    # Diagrama de relacionamentos (Mermaid)
    markdown += "## 🔗 Diagrama de Relacionamentos\n\n"
    markdown += "```mermaid\nerDiagram\n"
    
    for tabela in schema_info['tabelas']:
        if tabela['foreign_keys']:
            for fk in tabela['foreign_keys']:
                markdown += f"    {fk['referencia_tabela']} ||--o{{ {tabela['nome']} : {fk['coluna']}\n"
    
    markdown += "```\n\n"
    
    # Análise de Qualidade do Schema
    markdown += "---\n\n## 🔍 Análise de Qualidade do Schema\n\n"
    
    # Verificar tabelas sem PK
    tabelas_sem_pk = [t['nome'] for t in schema_info['tabelas'] 
                      if not any(c['tipo'] == 'PRIMARY KEY' for c in t['constraints'])]
    
    if tabelas_sem_pk:
        markdown += "### ⚠️ Tabelas SEM Primary Key\n\n"
        for t in tabelas_sem_pk:
            markdown += f"- ❌ `{t}` - **CRÍTICO**: Adicionar Primary Key\n"
        markdown += "\n"
    
    # Verificar tabelas sem indexes (exceto PKs)
    tabelas_sem_index = [t['nome'] for t in schema_info['tabelas'] 
                         if len(t['indexes']) <= 1 and len(t['colunas']) > 5]
    
    if tabelas_sem_index:
        markdown += "### 📇 Tabelas com Poucos Indexes\n\n"
        markdown += "Considerar adicionar indexes em colunas frequentemente consultadas:\n\n"
        for t in tabelas_sem_index:
            markdown += f"- ⚠️ `{t}`\n"
        markdown += "\n"
    
    # Colunas comuns que deveriam ter indexes
    markdown += "### 💡 Recomendações de Indexes\n\n"
    markdown += "Colunas que geralmente beneficiam de indexes:\n\n"
    
    colunas_recomendar_index = ['empresa_id', 'cliente_id', 'fornecedor_id', 'contrato_id', 'data_criacao', 'data_vencimento', 'status']
    
    for tabela in schema_info['tabelas']:
        colunas_tabela = [c['nome'] for c in tabela['colunas']]
        indexes_existentes = [i['coluna'] for i in tabela['indexes']]
        
        sugestoes = [col for col in colunas_recomendar_index 
                    if col in colunas_tabela and col not in indexes_existentes]
        
        if sugestoes:
            markdown += f"- **`{tabela['nome']}`**: {', '.join(f'`{s}`' for s in sugestoes)}\n"
    
    markdown += "\n"
    
    # Rodapé
    markdown += "---\n\n"
    markdown += f"**Gerado automaticamente em**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}  \n"
    markdown += "**Ferramenta**: Script de extração do schema (Fase 3)  \n"
    markdown += "**Propósito**: Documentação técnica para desenvolvimento e manutenção\n"
    
    # Salvar arquivo
    output_file = 'SCHEMA_DATABASE.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Documentação Markdown gerada: {output_file}")
    print(f"📄 Total de linhas: {len(markdown.splitlines())}")
    
    return output_file

if __name__ == "__main__":
    schema = carregar_schema()
    if schema:
        gerar_markdown(schema)
        print("🎉 Documentação gerada com sucesso!")
