"""
Blueprint para rotas de Kits de Equipamentos
Extraído do web_server.py como parte da Fase 2 de otimização
"""
from flask import Blueprint, request, jsonify
import random
import time

# Importar banco de dados
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import database_postgresql as db

kits_bp = Blueprint('kits', __name__)

@kits_bp.route('/kits', methods=['GET', 'POST'])
def kits():
    """Gerenciar kits (GET e POST)"""
    if request.method == 'GET':
        print("=" * 80)
        print("🔥 REQUISIÇÃO RECEBIDA: /api/kits")
        print("=" * 80)
        try:
            print("📡 Obtendo conexão com banco...")
            # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
            with db.get_db_connection(empresa_id=1) as conn:
                cursor = conn.cursor()
                
                print("🔍 Verificando se tabela kits existe...")
                # Verificar se a tabela existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'kits'
                    ) as existe
                """)
                result = cursor.fetchone()
                tabela_existe = result['existe'] if isinstance(result, dict) else (result[0] if result else False)
                
                if not tabela_existe:
                    print("⚠️ Tabela kits não existe - criando...")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS kits (
                            id SERIAL PRIMARY KEY,
                            nome VARCHAR(255) NOT NULL,
                            descricao TEXT,
                            empresa_id INTEGER,
                            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    print("✅ Tabela kits criada com sucesso")
                
                cursor.execute("""
                    SELECT id, nome, descricao, preco
                    FROM kits
                    ORDER BY nome
                """)
                
                rows = cursor.fetchall()
                
                print(f"🔍 Total de kits encontrados: {len(rows)}")
                
                # Converter para dicionários
                kits_lista = []
                for row in rows:
                    if isinstance(row, dict):
                        kits_lista.append({
                            'id': row['id'],
                            'nome': row['nome'],
                            'descricao': row.get('descricao', ''),
                            'preco': float(row.get('preco', 0)) if row.get('preco') else 0
                        })
                        print(f"  ✅ Kit: {row['nome']} (ID: {row['id']}) - R$ {row.get('preco', 0)}")
                    else:
                        kits_lista.append({
                            'id': row[0],
                            'nome': row[1],
                            'descricao': row[2] if len(row) > 2 and row[2] else '',
                            'preco': float(row[3]) if len(row) > 3 and row[3] else 0
                        })
                        print(f"  ✅ Kit: {row[1]} (ID: {row[0]}) - R$ {row[3] if len(row) > 3 else 0}")
                
                cursor.close()
            # Conexão automaticamente retorna ao pool aqui
            
            print(f"✅ Retornando {len(kits_lista)} kits")
            return jsonify({'success': True, 'data': kits_lista})
        except Exception as e:
            print(f"❌ Erro ao listar kits: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # POST
        print("=" * 80)
        print("🔥 REQUISIÇÃO RECEBIDA: POST /api/kits")
        print("=" * 80)
        try:
            data = request.json
            print(f"📦 Dados recebidos: {data}")
            
            # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
            with db.get_db_connection(empresa_id=1) as conn:
                cursor = conn.cursor()
                
                # Gerar código único para o kit (timestamp + random)
                codigo = f"KIT-{int(time.time())}-{random.randint(1000, 9999)}"
                
                print(f"🔢 Código gerado: {codigo}")
                
                # Preço do kit
                preco = float(data.get('preco', 0.00))
                itens = data.get('itens', '')
                
                print(f"💰 Preço: R$ {preco:.2f}")
                print(f"📦 Itens: {itens}")
                
                # Concatenar itens na descrição se houver
                descricao_completa = data.get('descricao', '')
                if itens:
                    descricao_completa += f"\n\nItens incluídos:\n{itens}"
                
                cursor.execute("""
                    INSERT INTO kits (codigo, nome, descricao, empresa_id, preco)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (codigo, data['nome'], descricao_completa, 1, preco))
                
                result = cursor.fetchone()
                kit_id = result['id'] if isinstance(result, dict) else result[0]
                
                conn.commit()
                cursor.close()
            # Conexão automaticamente retorna ao pool aqui
            
            print(f"✅ Kit criado com ID: {kit_id} e código: {codigo}")
            return jsonify({'success': True, 'message': 'Kit criado com sucesso', 'id': kit_id, 'codigo': codigo}), 201
        except Exception as e:
            print(f"❌ Erro ao criar kit: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@kits_bp.route('/kits/<int:kit_id>', methods=['PUT', 'DELETE'])
def kit_detalhes(kit_id):
    """Atualizar ou excluir kit"""
    if request.method == 'PUT':
        print("=" * 80)
        print(f"🔥 REQUISIÇÃO RECEBIDA: PUT /api/kits/{kit_id}")
        print("=" * 80)
        try:
            data = request.json
            print(f"📦 Dados recebidos: {data}")
            
            # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
            with db.get_db_connection(empresa_id=1) as conn:
                cursor = conn.cursor()
                
                # Processar descrição e itens
                descricao_base = data.get('descricao', '')
                itens = data.get('itens', '')
                preco = float(data.get('preco', 0.00))
                
                # Concatenar itens na descrição se houver
                descricao_completa = descricao_base
                if itens:
                    descricao_completa += f"\n\nItens incluídos:\n{itens}"
                
                print(f"💰 Preço: R$ {preco}")
                print(f"📦 Descrição completa: {descricao_completa[:100]}...")
                
                cursor.execute("""
                    UPDATE kits 
                    SET nome = %s, descricao = %s, preco = %s
                    WHERE id = %s
                """, (data['nome'], descricao_completa, preco, kit_id))
                
                if cursor.rowcount == 0:
                    cursor.close()
                    return jsonify({'error': 'Kit não encontrado'}), 404
                
                conn.commit()
                cursor.close()
            # Conexão automaticamente retorna ao pool aqui
            
            print(f"✅ Kit {kit_id} atualizado com sucesso")
            return jsonify({'success': True, 'message': 'Kit atualizado com sucesso'})
        except Exception as e:
            print(f"❌ Erro ao atualizar kit: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    else:  # DELETE
        print("=" * 80)
        print(f"🔥 REQUISIÇÃO RECEBIDA: DELETE /api/kits/{kit_id}")
        print("=" * 80)
        try:
            # USAR CONTEXT MANAGER - conexão sempre retorna ao pool
            with db.get_db_connection(empresa_id=1) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM kits WHERE id = %s", (kit_id,))
                
                if cursor.rowcount == 0:
                    cursor.close()
                    return jsonify({'error': 'Kit não encontrado'}), 404
                
                conn.commit()
                cursor.close()
            # Conexão automaticamente retorna ao pool aqui
            
            print(f"✅ Kit {kit_id} excluído com sucesso")
            return jsonify({'success': True, 'message': 'Kit excluído com sucesso'})
        except Exception as e:
            print(f"❌ Erro ao excluir kit: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
