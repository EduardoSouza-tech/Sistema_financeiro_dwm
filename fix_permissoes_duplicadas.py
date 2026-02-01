#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir nomes de permissões duplicadas
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import DatabaseManager

def main():
    print("="*80)
    print("🔧 CORREÇÃO: Permissões Duplicadas")
    print("="*80)
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        print("\n📝 Atualizando nomes das permissões...")
        
        # Atualizar permissões de Agenda (adicionar "(Agenda)")
        updates_agenda = [
            ("agenda_create", "Criar Eventos (Agenda)"),
            ("agenda_edit", "Editar Eventos (Agenda)"),
            ("agenda_delete", "Excluir Eventos (Agenda)")
        ]
        
        for codigo, novo_nome in updates_agenda:
            cursor.execute("""
                UPDATE permissoes 
                SET nome = %s 
                WHERE codigo = %s
            """, (novo_nome, codigo))
            print(f"   ✓ {codigo} → {novo_nome}")
        
        # Atualizar permissões de Eventos Operacionais (adicionar "Operacionais")
        updates_eventos = [
            ("eventos_view", "Ver Eventos Operacionais"),
            ("eventos_create", "Criar Eventos Operacionais"),
            ("eventos_edit", "Editar Eventos Operacionais"),
            ("eventos_delete", "Excluir Eventos Operacionais")
        ]
        
        for codigo, novo_nome in updates_eventos:
            cursor.execute("""
                UPDATE permissoes 
                SET nome = %s 
                WHERE codigo = %s
            """, (novo_nome, codigo))
            print(f"   ✓ {codigo} → {novo_nome}")
        
        conn.commit()
        
        print("\n✅ Permissões atualizadas com sucesso!")
        
        # Verificar resultado
        cursor.execute("""
            SELECT codigo, nome 
            FROM permissoes 
            WHERE codigo IN ('agenda_create', 'agenda_edit', 'agenda_delete',
                            'eventos_view', 'eventos_create', 'eventos_edit', 'eventos_delete')
            ORDER BY codigo
        """)
        
        print("\n📊 Permissões após correção:")
        for row in cursor.fetchall():
            print(f"   {row['codigo']:20} → {row['nome']}")
        
        print("\n" + "="*80)
        print("✅ CORREÇÃO CONCLUÍDA!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
