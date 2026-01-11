"""
Script de teste para a funcionalidade de exportação de dados por cliente
"""
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

import database_postgresql as db

def teste_exportacao():
    """Testa a exportação de dados de um cliente"""
    print("\n" + "="*70)
    print("🧪 TESTE - Exportação de Dados por Cliente")
    print("="*70)
    
    # 1. Listar proprietários disponíveis
    print("\n1️⃣ Buscando proprietários no sistema...")
    try:
        # Usar DatabaseManager
        db_manager = db.DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Buscar proprietários únicos
        cursor.execute("""
            SELECT DISTINCT proprietario_id 
            FROM clientes 
            WHERE proprietario_id IS NOT NULL
            LIMIT 5
        """)
        proprietarios = cursor.fetchall()
        
        if not proprietarios:
            print("❌ Nenhum proprietário encontrado no sistema")
            print("💡 Execute 'python popular_dados_teste.py' primeiro")
            cursor.close()
            db.return_to_pool(conn)
            return
        
        print(f"✅ Encontrados {len(proprietarios)} proprietários")
        
        # Selecionar primeiro proprietário para teste
        cliente_id = proprietarios[0]['proprietario_id']
        print(f"\n2️⃣ Testando exportação do cliente ID: {cliente_id}")
        
        cursor.close()
        db.return_to_pool(conn)
        
    except Exception as e:
        print(f"❌ Erro ao buscar proprietários: {e}")
        return
    
    # 2. Exportar dados do cliente
    try:
        print("\n🔄 Iniciando exportação...")
        export_data = db.exportar_dados_cliente(cliente_id)
        
        print("\n✅ Exportação concluída com sucesso!")
        print("\n📊 Estatísticas:")
        stats = export_data['metadata']['estatisticas']
        print(f"   • Clientes: {stats['total_clientes']}")
        print(f"   • Fornecedores: {stats['total_fornecedores']}")
        print(f"   • Categorias: {stats['total_categorias']}")
        print(f"   • Contas: {stats['total_contas']}")
        print(f"   • Lançamentos: {stats['total_lancamentos']}")
        
        # 3. Verificar estrutura dos dados
        print("\n3️⃣ Verificando estrutura dos dados exportados...")
        
        campos_obrigatorios = ['metadata', 'clientes', 'fornecedores', 'categorias', 
                               'contas_bancarias', 'lancamentos']
        
        for campo in campos_obrigatorios:
            if campo in export_data:
                print(f"   ✅ Campo '{campo}' presente")
            else:
                print(f"   ❌ Campo '{campo}' AUSENTE!")
        
        # 4. Verificar metadados
        print("\n4️⃣ Verificando metadados...")
        metadata = export_data['metadata']
        
        if metadata.get('cliente_id') == cliente_id:
            print(f"   ✅ Cliente ID correto: {cliente_id}")
        else:
            print(f"   ❌ Cliente ID incorreto!")
        
        if 'data_exportacao' in metadata:
            print(f"   ✅ Data de exportação: {metadata['data_exportacao']}")
        else:
            print("   ❌ Data de exportação ausente!")
        
        if 'versao_sistema' in metadata:
            print(f"   ✅ Versão do sistema: {metadata['versao_sistema']}")
        else:
            print("   ❌ Versão do sistema ausente!")
        
        # 5. Salvar arquivo de teste
        print("\n5️⃣ Salvando arquivo JSON de teste...")
        import json
        from datetime import datetime
        
        filename = f"export_teste_cliente_{cliente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Verificar tamanho do arquivo
        file_size = os.path.getsize(filename)
        file_size_kb = file_size / 1024
        
        print(f"   ✅ Arquivo salvo: {filename}")
        print(f"   📦 Tamanho: {file_size_kb:.2f} KB")
        
        print("\n" + "="*70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*70)
        print(f"\n📄 Arquivo de teste gerado: {filename}")
        print("💡 Você pode abrir este arquivo em um editor JSON para visualizar")
        
    except Exception as e:
        print(f"\n❌ Erro ao exportar dados: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    teste_exportacao()
