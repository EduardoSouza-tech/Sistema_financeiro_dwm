"""
Script para re-criptografar senhas de certificados digitais.

Este script permite:
1. Verificar certificados com senhas em formato inválido
2. Re-criptografar senhas com a FERNET_KEY atual
3. Corrigir certificados salvos antes da criptografia existir

Uso:
    python recriptografar_certificados.py

Pré-requisitos:
    - FERNET_KEY configurada no ambiente (.env ou export)
    - Acesso ao banco de dados
    - Senha em texto plano de cada certificado

Autor: Sistema Financeiro DWM
Data: 19 de Fevereiro de 2026
"""

import os
import sys
from cryptography.fernet import Fernet

# Adiciona path do sistema
sys.path.append(os.path.dirname(__file__))

# Importa módulos do sistema
from database_postgresql import get_db_connection
from relatorios.nfe.nfe_api import criptografar_senha

def verificar_fernet_key():
    """Verifica se FERNET_KEY está configurada."""
    chave_str = os.environ.get('FERNET_KEY', '')
    if not chave_str:
        print("=" * 70)
        print("❌ ERRO: FERNET_KEY não configurada no ambiente")
        print("=" * 70)
        print()
        print("A variável FERNET_KEY é necessária para criptografar senhas.")
        print()
        print("📋 Como configurar:")
        print()
        print("  Opção 1 - Arquivo .env (local):")
        print("    Adicione no arquivo .env:")
        print("    FERNET_KEY=u2izhbz5QoGb2bkfh3dT5ckGADuGcRnEwFTCZ-LY-r0=")
        print()
        print("  Opção 2 - Variável temporária (terminal):")
        print("    export FERNET_KEY='u2izhbz5QoGb2bkfh3dT5ckGADuGcRnEwFTCZ-LY-r0='")
        print("    python recriptografar_certificados.py")
        print()
        print("  Opção 3 - Railway (produção):")
        print("    1. Acesse railway.app → Variables")
        print("    2. Adicione: FERNET_KEY = u2izhbz5QoGb2bkfh3dT5ckGADuGcRnEwFTCZ-LY-r0=")
        print()
        return None
    
    return chave_str.encode('utf-8')


def listar_certificados():
    """Lista todos os certificados ativos."""
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, 
                empresa_id, 
                nome_certificado, 
                cnpj, 
                senha_pfx,
                LENGTH(senha_pfx) as tamanho_senha,
                valido_ate,
                ativo
            FROM certificados_digitais
            WHERE ativo = TRUE
            ORDER BY empresa_id, id
        """)
        
        return cursor.fetchall()


def diagnosticar_certificado(senha_pfx):
    """Analisa o formato da senha do certificado."""
    tamanho = len(senha_pfx)
    
    # Tokens Fernet têm >= 72 caracteres (geralmente ~112-120)
    if tamanho >= 72:
        return {
            'status': 'criptografado',
            'emoji': '✅',
            'descricao': 'Formato Fernet válido'
        }
    elif tamanho >= 20 and tamanho < 72:
        return {
            'status': 'suspeito',
            'emoji': '⚠️',
            'descricao': 'Formato suspeito (token Fernet curto ou corrompido)'
        }
    else:
        return {
            'status': 'texto_plano',
            'emoji': '❌',
            'descricao': 'Provavelmente em texto plano'
        }


def recriptografar_certificados():
    """Re-criptografa todos os certificados com a FERNET_KEY atual."""
    
    print("=" * 70)
    print(" 🔐 RE-CRIPTOGRAFIA DE CERTIFICADOS DIGITAIS")
    print("=" * 70)
    print()
    
    # Verifica FERNET_KEY
    chave = verificar_fernet_key()
    if not chave:
        return
    
    print(f"✅ FERNET_KEY carregada ({len(chave)} bytes)")
    print()
    
    # Lista certificados
    certificados = listar_certificados()
    
    if not certificados:
        print("ℹ️  Nenhum certificado ativo encontrado no banco de dados")
        print()
        print("💡 Cadastre certificados em: Relatórios Fiscais > 🔐 Certificados Digitais")
        return
    
    print(f"📄 {len(certificados)} certificado(s) ativo(s) encontrado(s)")
    print()
    
    # Analisa cada certificado
    certificados_problema = []
    
    print("─" * 70)
    print("DIAGNÓSTICO")
    print("─" * 70)
    
    for cert in certificados:
        cert_id, empresa_id, nome, cnpj, senha_pfx, tamanho, validade, ativo = cert
        
        diagnostico = diagnosticar_certificado(senha_pfx)
        
        print(f"{diagnostico['emoji']} ID {cert_id} | Empresa {empresa_id} | {nome[:30]}")
        print(f"   CNPJ: {cnpj} | Senha: {tamanho} chars | {diagnostico['descricao']}")
        
        if diagnostico['status'] != 'criptografado':
            certificados_problema.append(cert)
    
    print("─" * 70)
    print()
    
    if not certificados_problema:
        print("✅ Todos os certificados já estão em formato criptografado!")
        print()
        print("💡 Se ainda há erro ao buscar documentos, verifique se a FERNET_KEY")
        print("   é a MESMA usada quando os certificados foram cadastrados.")
        return
    
    # Solicita confirmação
    print(f"⚠️  Encontrados {len(certificados_problema)} certificado(s) com problemas")
    print()
    print("📋 Este script irá:")
    print("   1. Solicitar a senha EM TEXTO PLANO de cada certificado problemático")
    print("   2. Criptografar a senha com a FERNET_KEY atual")
    print("   3. Atualizar o banco de dados")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - Você precisará digitar a senha correta de cada certificado")
    print("   - Senhas incorretas farão a busca de documentos falhar")
    print("   - Não há como recuperar senhas perdidas")
    print()
    
    confirma = input("Deseja continuar? (digite 'SIM' para confirmar): ").strip()
    if confirma != 'SIM':
        print()
        print("❌ Operação cancelada")
        return
    
    print()
    print("=" * 70)
    print("PROCESSAMENTO")
    print("=" * 70)
    print()
    
    # Processa cada certificado
    sucesso = 0
    erros = 0
    
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        for cert in certificados_problema:
            cert_id, empresa_id, nome, cnpj, senha_antiga, tamanho, validade, ativo = cert
            
            print("─" * 70)
            print(f"🔐 Certificado ID: {cert_id}")
            print(f"   Empresa: {empresa_id}")
            print(f"   Nome: {nome}")
            print(f"   CNPJ: {cnpj}")
            print(f"   Validade: {validade.strftime('%d/%m/%Y') if validade else 'N/A'}")
            print(f"   Senha atual: {tamanho} chars")
            print()
            
            # Solicita senha em texto plano
            senha_texto = input("   Digite a senha do certificado (.pfx): ").strip()
            
            if not senha_texto:
                print("   ❌ Senha vazia, pulando certificado...")
                erros += 1
                continue
            
            try:
                # Criptografa
                senha_nova = criptografar_senha(senha_texto, chave)
                print(f"   ✅ Senha criptografada com sucesso ({len(senha_nova)} chars)")
                
                # Atualiza no banco
                cursor.execute("""
                    UPDATE certificados_digitais
                    SET senha_pfx = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (senha_nova, cert_id))
                
                conn.commit()
                print("   💾 Salvo no banco de dados!")
                sucesso += 1
                
            except Exception as e:
                print(f"   ❌ Erro: {type(e).__name__}: {str(e)}")
                conn.rollback()
                erros += 1
            
            print()
    
    # Resumo
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print()
    print(f"✅ Certificados re-criptografados: {sucesso}")
    print(f"❌ Erros: {erros}")
    print()
    
    if sucesso > 0:
        print("🎉 Processo concluído com sucesso!")
        print()
        print("📋 Próximos passos:")
        print("   1. Teste a busca de documentos em: Relatórios Fiscais > Buscar Documentos")
        print("   2. Verifique os logs do sistema para confirmar descriptografia")
        print("   3. Se ainda houver erro, verifique se FERNET_KEY está no Railway")
    else:
        print("⚠️  Nenhum certificado foi re-criptografado")
        print()
        print("💡 Verifique:")
        print("   - As senhas digitadas estavam corretas?")
        print("   - Houve algum erro de conexão com o banco?")
    print()


if __name__ == '__main__':
    try:
        recriptografar_certificados()
    except KeyboardInterrupt:
        print("\n\n❌ Operação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRO CRÍTICO: {type(e).__name__}")
        print(f"Detalhes: {str(e)}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())
        sys.exit(1)
