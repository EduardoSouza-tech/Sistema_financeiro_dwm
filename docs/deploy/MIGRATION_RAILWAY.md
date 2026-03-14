# 🚀 Aplicar Migration no Railway

## Problema
As tabelas `funcoes_evento` e `evento_funcionarios` não existem no banco de dados do Railway.

## Erro
```
relation "funcoes_evento" does not exist
```

## Solução

Execute o seguinte comando no Railway CLI ou no painel web:

```bash
python aplicar_migration_evento_funcionarios.py
```

### Alternativa: Executar SQL Diretamente

Se preferir, execute o SQL diretamente no banco PostgreSQL do Railway:

1. Acesse o Railway Dashboard
2. Vá para o banco de dados PostgreSQL
3. Abra o Query Editor
4. Copie e cole o conteúdo do arquivo `migration_evento_funcionarios.sql`
5. Execute

## O que a Migration Faz

- ✅ Cria tabela `funcoes_evento` (Motorista, Fotógrafo, etc.)
- ✅ Cria tabela `evento_funcionarios` (alocação de equipe)
- ✅ Insere 11 funções padrão
- ✅ Cria índices para performance
- ✅ Adiciona constraints de integridade

## Verificação

Após aplicar, teste no frontend:
1. Acesse 🎉 Eventos Operacionais
2. Clique em "👥 Alocar Equipe" em qualquer evento
3. Deve carregar lista de funcionários e funções
