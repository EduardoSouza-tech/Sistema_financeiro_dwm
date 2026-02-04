"""
Script para recalcular as margens de todos os eventos existentes
Executa: python corrigir_margens_eventos.py
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import DatabasePostgreSQL

def recalcular_margens():
    """Recalcula a margem de todos os eventos"""
    try:
        db = DatabasePostgreSQL()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("🔄 Buscando todos os eventos...")
        
        # Buscar todos os eventos
        cursor.execute("""
            SELECT id, nome_evento, valor_liquido_nf, custo_evento, margem
            FROM eventos
            ORDER BY id
        """)
        
        eventos = cursor.fetchall()
        total = len(eventos)
        
        print(f"📊 Encontrados {total} evento(s)\n")
        
        if total == 0:
            print("⚠️  Nenhum evento encontrado")
            cursor.close()
            return
        
        atualizados = 0
        
        for evento in eventos:
            evento_id = evento['id']
            nome = evento['nome_evento']
            valor_liquido = evento['valor_liquido_nf'] if evento['valor_liquido_nf'] else 0
            custo = evento['custo_evento'] if evento['custo_evento'] else 0
            margem_antiga = evento['margem'] if evento['margem'] else 0
            
            # Calcular nova margem
            margem_nova = float(valor_liquido) - float(custo)
            
            # Verificar se precisa atualizar
            if abs(float(margem_antiga) - margem_nova) > 0.01:  # Diferença maior que 1 centavo
                print(f"🔧 Evento #{evento_id}: {nome}")
                print(f"   Valor Líquido: R$ {valor_liquido:,.2f}")
                print(f"   Custo: R$ {custo:,.2f}")
                print(f"   Margem Antiga: R$ {float(margem_antiga):,.2f}")
                print(f"   Margem Nova: R$ {margem_nova:,.2f}")
                
                # Atualizar margem
                cursor.execute("""
                    UPDATE eventos
                    SET margem = %s
                    WHERE id = %s
                """, (margem_nova, evento_id))
                
                atualizados += 1
                print(f"   ✅ Margem atualizada!\n")
            else:
                print(f"✓ Evento #{evento_id}: {nome} - Margem já está correta")
        
        conn.commit()
        cursor.close()
        
        print("\n" + "="*60)
        print(f"✅ Processo concluído!")
        print(f"   Total de eventos: {total}")
        print(f"   Margens atualizadas: {atualizados}")
        print(f"   Já corretas: {total - atualizados}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Erro ao recalcular margens: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Iniciando recálculo de margens dos eventos...\n")
    recalcular_margens()
