"""
Módulo de API e orquestração de NF-e

Este módulo é responsável por:
- Orquestrar busca, processamento e armazenamento
- Integração com banco de dados
- Gerenciamento de certificados
- Funções de alto nível para o sistema
- Exportação de dados

Autor: Sistema Financeiro DWM
Data: Janeiro 2026
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cryptography.fernet import Fernet

# Adiciona path do sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Importações
if __name__ == '__main__':
    # Modo teste: import direto
    import nfe_busca
    import nfe_processor
    import nfe_storage
else:
    # Modo produção: import relativo
    from . import nfe_busca, nfe_processor, nfe_storage

# Importação condicional do banco
try:
    from database_postgresql import obter_conexao
    DATABASE_AVAILABLE = True
except (ImportError, ValueError) as e:
    DATABASE_AVAILABLE = False
    if __name__ != '__main__':
        raise


# ============================================================================
# CRIPTOGRAFIA DE SENHAS
# ============================================================================

def gerar_chave_criptografia() -> bytes:
    """
    Gera uma chave Fernet para criptografar senhas de certificados.
    Esta chave deve ser armazenada de forma segura (variável ambiente).
    """
    return Fernet.generate_key()


def criptografar_senha(senha: str, chave: bytes) -> str:
    """Criptografa a senha do certificado usando Fernet."""
    f = Fernet(chave)
    senha_bytes = senha.encode('utf-8')
    senha_cripto = f.encrypt(senha_bytes)
    return senha_cripto.decode('utf-8')


def descriptografar_senha(senha_cripto: str, chave: bytes) -> str:
    """Descriptografa a senha do certificado."""
    f = Fernet(chave)
    senha_cripto_bytes = senha_cripto.encode('utf-8')
    senha_bytes = f.decrypt(senha_cripto_bytes)
    return senha_bytes.decode('utf-8')


# ============================================================================
# GERENCIAMENTO DE CERTIFICADOS
# ============================================================================

def salvar_certificado(empresa_id: int, cnpj: str, nome_certificado: str,
                      pfx_base64: str, senha: str, cuf: int, 
                      ambiente: str = 'producao',
                      valido_de: datetime = None, valido_ate: datetime = None,
                      chave_cripto: bytes = None, usuario_id: int = None) -> Dict[str, any]:
    """
    Salva um certificado digital no banco.
    
    Args:
        empresa_id: ID da empresa
        cnpj: CNPJ do certificado
        nome_certificado: Nome/descrição do certificado
        pfx_base64: Conteúdo do .pfx em base64
        senha: Senha do certificado (será criptografada)
        cuf: Código UF
        ambiente: 'producao' ou 'homologacao'
        valido_de: Data inicial de validade
        valido_ate: Data final de validade
        chave_cripto: Chave Fernet para criptografia (usar variável ambiente)
        usuario_id: ID do usuário que cadastrou
        
    Returns:
        Dict com sucesso e id do certificado
    """
    conn = None
    try:
        # Valida certificado
        try:
            cert = nfe_busca.CertificadoA1(pfx_base64=pfx_base64, senha=senha)
            
            if not cert.esta_valido():
                return {
                    'sucesso': False,
                    'erro': 'Certificado fora do prazo de validade'
                }
            
            # Extrai validades se não fornecidas
            if not valido_de:
                valido_de = cert.cert_data['valido_de']
            if not valido_ate:
                valido_ate = cert.cert_data['valido_ate']
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': f'Certificado inválido: {str(e)}'
            }
        
        # Criptografa senha
        if not chave_cripto:
            chave_cripto = os.environ.get('FERNET_KEY', '').encode('utf-8')
            if not chave_cripto:
                return {
                    'sucesso': False,
                    'erro': 'Chave de criptografia não configurada (FERNET_KEY)'
                }
        
        senha_cripto = criptografar_senha(senha, chave_cripto)
        
        # Salva no banco
        conn = obter_conexao()
        cursor = conn.cursor()
        
        sql = """
            INSERT INTO certificados_digitais 
            (empresa_id, cnpj, nome_certificado, pfx_base64, senha_pfx, 
             cuf, ambiente, valido_de, valido_ate, criado_por, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id
        """
        
        cursor.execute(sql, (
            empresa_id, cnpj, nome_certificado, pfx_base64, senha_cripto,
            cuf, ambiente, valido_de, valido_ate, usuario_id
        ))
        
        certificado_id = cursor.fetchone()[0]
        conn.commit()
        
        return {
            'sucesso': True,
            'certificado_id': certificado_id,
            'valido_de': valido_de,
            'valido_ate': valido_ate
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        return {
            'sucesso': False,
            'erro': f'Erro ao salvar certificado: {str(e)}'
        }
    finally:
        if conn:
            conn.close()


def obter_certificado(certificado_id: int, chave_cripto: bytes = None) -> Optional[nfe_busca.CertificadoA1]:
    """
    Carrega certificado do banco e retorna objeto CertificadoA1.
    
    Args:
        certificado_id: ID do certificado
        chave_cripto: Chave Fernet (usa variável ambiente se não fornecida)
        
    Returns:
        Objeto CertificadoA1 ou None
    """
    conn = None
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pfx_base64, senha_pfx, ativo
            FROM certificados_digitais
            WHERE id = %s
        """, (certificado_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        pfx_base64, senha_cripto, ativo = row
        
        if not ativo:
            return None
        
        # Descriptografa senha
        if not chave_cripto:
            chave_cripto = os.environ.get('FERNET_KEY', '').encode('utf-8')
        
        senha = descriptografar_senha(senha_cripto, chave_cripto)
        
        # Cria certificado
        cert = nfe_busca.CertificadoA1(pfx_base64=pfx_base64, senha=senha)
        
        return cert
        
    except Exception as e:
        print(f"Erro ao obter certificado: {e}")
        return None
    finally:
        if conn:
            conn.close()


# ============================================================================
# BUSCA E PROCESSAMENTO DE DOCUMENTOS
# ============================================================================

def buscar_e_processar_novos_documentos(certificado_id: int, usuario_id: int = None,
                                       limite_docs: int = 100) -> Dict[str, any]:
    """
    Busca novos documentos na SEFAZ e processa.
    
    Fluxo:
    1. Carrega certificado
    2. Consulta último NSU no banco
    3. Busca novos documentos na SEFAZ
    4. Processa cada documento
    5. Salva XML no storage
    6. Salva dados no banco
    7. Atualiza NSU do certificado
    
    Args:
        certificado_id: ID do certificado
        usuario_id: ID do usuário (para auditoria)
        limite_docs: Máximo de documentos a processar
        
    Returns:
        Dict com estatísticas da busca
    """
    conn = None
    try:
        # Carrega certificado
        cert = obter_certificado(certificado_id)
        if not cert:
            return {'sucesso': False, 'erro': 'Certificado não encontrado ou inválido'}
        
        # Busca dados do certificado no banco
        conn = obter_conexao()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT empresa_id, cnpj, ultimo_nsu, cuf, ambiente
            FROM certificados_digitais
            WHERE id = %s
        """, (certificado_id,))
        
        row = cursor.fetchone()
        if not row:
            return {'sucesso': False, 'erro': 'Certificado não encontrado'}
        
        empresa_id, cnpj, ultimo_nsu, cuf, ambiente = row
        
        # Busca documentos na SEFAZ
        resultado_busca = nfe_busca.baixar_documentos_dfe(
            certificado=cert,
            cnpj=cnpj,
            cuf=cuf,
            ultimo_nsu=ultimo_nsu or '000000000000000',
            ambiente=ambiente
        )
        
        if not resultado_busca['sucesso']:
            return {
                'sucesso': False,
                'erro': f"Erro SEFAZ: {resultado_busca.get('erro', 'Desconhecido')}"
            }
        
        # Estatísticas
        stats = {
            'total_baixados': 0,
            'nfes_processadas': 0,
            'ctes_processados': 0,
            'eventos_processados': 0,
            'erros': 0,
            'documentos_detalhes': []
        }
        
        documentos = resultado_busca.get('documentos', [])
        novo_nsu = resultado_busca.get('ultNSU', ultimo_nsu)
        
        # Processa cada documento
        for doc in documentos[:limite_docs]:
            nsu = doc['nsu']
            schema = doc['schema']
            xml_content = doc.get('xml')
            
            if not xml_content:
                stats['erros'] += 1
                continue
            
            # Detecta schema
            schema_info = nfe_processor.detectar_schema_nfe(xml_content)
            
            if not schema_info['sucesso']:
                stats['erros'] += 1
                continue
            
            # Processa de acordo com o tipo
            if schema_info['categoria'] == 'NFe':
                resultado_proc = _processar_nfe(
                    empresa_id, certificado_id, cnpj, nsu, schema, 
                    xml_content, usuario_id, cursor
                )
                if resultado_proc['sucesso']:
                    stats['nfes_processadas'] += 1
                else:
                    stats['erros'] += 1
                
                stats['documentos_detalhes'].append(resultado_proc)
                
            elif schema_info['categoria'] == 'Evento':
                resultado_proc = _processar_evento(
                    empresa_id, certificado_id, nsu, schema,
                    xml_content, usuario_id, cursor
                )
                if resultado_proc['sucesso']:
                    stats['eventos_processados'] += 1
                else:
                    stats['erros'] += 1
            
            stats['total_baixados'] += 1
        
        # Atualiza NSU do certificado
        cursor.execute("""
            UPDATE certificados_digitais
            SET ultimo_nsu = %s,
                max_nsu = %s,
                data_ultima_busca = NOW(),
                atualizado_em = NOW(),
                atualizado_por = %s
            WHERE id = %s
        """, (novo_nsu, resultado_busca.get('maxNSU'), usuario_id, certificado_id))
        
        conn.commit()
        
        stats['sucesso'] = True
        stats['novo_nsu'] = novo_nsu
        stats['max_nsu'] = resultado_busca.get('maxNSU')
        
        return stats
        
    except Exception as e:
        if conn:
            conn.rollback()
        return {
            'sucesso': False,
            'erro': f'Erro ao buscar documentos: {str(e)}'
        }
    finally:
        if conn:
            conn.close()


def _processar_nfe(empresa_id: int, certificado_id: int, cnpj_empresa: str,
                  nsu: str, schema: str, xml_content: str, 
                  usuario_id: int, cursor) -> Dict[str, any]:
    """Processa uma NF-e e salva no banco."""
    try:
        # Extrai dados
        dados = nfe_processor.extrair_dados_nfe(xml_content, cnpj_empresa)
        
        if not dados['sucesso']:
            return {'sucesso': False, 'erro': dados['erro']}
        
        chave = dados['chave']
        
        # Salva XML no storage
        resultado_storage = nfe_storage.salvar_xml_nfe(
            cnpj_certificado=cnpj_empresa,
            chave=chave,
            xml_content=xml_content,
            tipo_xml=dados.get('tipo_xml', 'procNFe'),
            data_emissao=dados.get('data_emissao')
        )
        
        if not resultado_storage['sucesso']:
            return {'sucesso': False, 'erro': 'Erro ao salvar XML'}
        
        # Salva log no banco
        cursor.execute("""
            INSERT INTO documentos_fiscais_log 
            (empresa_id, certificado_id, nsu, chave, tipo_documento, schema_name,
             numero_documento, serie, valor_total, cnpj_emitente, nome_emitente,
             cnpj_destinatario, nome_destinatario, data_emissao, 
             caminho_xml, tamanho_bytes, hash_md5, busca_por, processado)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (certificado_id, nsu) DO NOTHING
        """, (
            empresa_id, certificado_id, nsu, chave, 'NFe', schema,
            dados.get('numero'), dados.get('serie'), dados.get('valor_total'),
            dados.get('cnpj_emitente'), dados.get('nome_emitente'),
            dados.get('cnpj_destinatario'), dados.get('nome_destinatario'),
            dados.get('data_emissao'),
            resultado_storage['caminho'], resultado_storage['tamanho'],
            resultado_storage['hash_md5'], usuario_id
        ))
        
        # Atualiza contadores do certificado
        cursor.execute("""
            UPDATE certificados_digitais
            SET total_documentos_baixados = total_documentos_baixados + 1,
                total_nfes = total_nfes + 1
            WHERE id = %s
        """, (certificado_id,))
        
        return {
            'sucesso': True,
            'chave': chave,
            'numero': dados.get('numero'),
            'valor': dados.get('valor_total'),
            'direção': dados.get('direcao')
        }
        
    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}


def _processar_evento(empresa_id: int, certificado_id: int, nsu: str, 
                     schema: str, xml_content: str, usuario_id: int, cursor) -> Dict[str, any]:
    """Processa um evento de NF-e."""
    try:
        # Extrai dados do evento
        dados = nfe_processor.extrair_dados_nfe(xml_content, '')  # CNPJ não importa para evento
        
        if not dados['sucesso']:
            return {'sucesso': False, 'erro': dados['erro']}
        
        chave = dados.get('chave')
        
        # Salva log
        cursor.execute("""
            INSERT INTO documentos_fiscais_log 
            (empresa_id, certificado_id, nsu, chave, tipo_documento, schema_name,
             busca_por, processado)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (certificado_id, nsu) DO NOTHING
        """, (
            empresa_id, certificado_id, nsu, chave, 'Evento', schema,
            usuario_id
        ))
        
        # Atualiza contadores
        cursor.execute("""
            UPDATE certificados_digitais
            SET total_documentos_baixados = total_documentos_baixados + 1,
                total_eventos = total_eventos + 1
            WHERE id = %s
        """, (certificado_id,))
        
        return {'sucesso': True, 'tipo': 'Evento'}
        
    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}


# ============================================================================
# CONSULTAS E EXPORTAÇÃO
# ============================================================================

def listar_documentos_periodo(empresa_id: int, data_inicio: datetime, 
                             data_fim: datetime, tipo: str = None) -> List[Dict]:
    """
    Lista documentos fiscais em um período.
    
    Args:
        empresa_id: ID da empresa
        data_inicio: Data inicial
        data_fim: Data final
        tipo: Filtro por tipo ('NFe', 'CTe', 'Evento') ou None para todos
        
    Returns:
        Lista de documentos
    """
    conn = None
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        sql = """
            SELECT 
                id, nsu, chave, tipo_documento, numero_documento, serie,
                valor_total, cnpj_emitente, nome_emitente,
                cnpj_destinatario, nome_destinatario, data_emissao,
                caminho_xml, data_busca
            FROM documentos_fiscais_log
            WHERE empresa_id = %s
              AND data_busca BETWEEN %s AND %s
        """
        
        params = [empresa_id, data_inicio, data_fim]
        
        if tipo:
            sql += " AND tipo_documento = %s"
            params.append(tipo)
        
        sql += " ORDER BY data_busca DESC"
        
        cursor.execute(sql, params)
        
        rows = cursor.fetchall()
        
        documentos = []
        for row in rows:
            documentos.append({
                'id': row[0],
                'nsu': row[1],
                'chave': row[2],
                'tipo': row[3],
                'numero': row[4],
                'serie': row[5],
                'valor': float(row[6]) if row[6] else 0.0,
                'emitente_cnpj': row[7],
                'emitente_nome': row[8],
                'destinatario_cnpj': row[9],
                'destinatario_nome': row[10],
                'data_emissao': row[11],
                'caminho_xml': row[12],
                'data_busca': row[13]
            })
        
        return documentos
        
    except Exception as e:
        print(f"Erro ao listar documentos: {e}")
        return []
    finally:
        if conn:
            conn.close()


def obter_estatisticas_empresa(empresa_id: int) -> Dict[str, any]:
    """
    Retorna estatísticas de documentos de uma empresa.
    
    Args:
        empresa_id: ID da empresa
        
    Returns:
        Dict com estatísticas
    """
    conn = None
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        # Total de documentos
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN tipo_documento = 'NFe' THEN 1 END) as total_nfes,
                COUNT(CASE WHEN tipo_documento = 'CTe' THEN 1 END) as total_ctes,
                COUNT(CASE WHEN tipo_documento = 'Evento' THEN 1 END) as total_eventos,
                SUM(CASE WHEN tipo_documento = 'NFe' THEN valor_total ELSE 0 END) as valor_total_nfes
            FROM documentos_fiscais_log
            WHERE empresa_id = %s
        """, (empresa_id,))
        
        row = cursor.fetchone()
        
        stats = {
            'total_documentos': row[0] or 0,
            'total_nfes': row[1] or 0,
            'total_ctes': row[2] or 0,
            'total_eventos': row[3] or 0,
            'valor_total_nfes': float(row[4]) if row[4] else 0.0
        }
        
        # Certificados ativos
        cursor.execute("""
            SELECT COUNT(*)
            FROM certificados_digitais
            WHERE empresa_id = %s AND ativo = TRUE
        """, (empresa_id,))
        
        stats['certificados_ativos'] = cursor.fetchone()[0]
        
        return stats
        
    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        return {}
    finally:
        if conn:
            conn.close()


# ============================================================================
# TESTE
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("TESTE: Módulo NF-e API")
    print("=" * 70)
    
    print("\n✓ Funções de alto nível definidas:")
    print("  - salvar_certificado()")
    print("  - obter_certificado()")
    print("  - buscar_e_processar_novos_documentos()")
    print("  - listar_documentos_periodo()")
    print("  - obter_estatisticas_empresa()")
    
    print("\n✓ Funções de criptografia:")
    print("  - gerar_chave_criptografia()")
    print("  - criptografar_senha()")
    print("  - descriptografar_senha()")
    
    # Teste de criptografia (não precisa de banco)
    print("\n" + "-" * 70)
    print("Teste de criptografia de senha:")
    chave = gerar_chave_criptografia()
    senha_original = "SenhaSecreta123"
    
    senha_cripto = criptografar_senha(senha_original, chave)
    senha_decripto = descriptografar_senha(senha_cripto, chave)
    
    print(f"  Senha original:         {senha_original}")
    print(f"  Senha criptografada:    {senha_cripto[:40]}...")
    print(f"  Senha descriptografada: {senha_decripto}")
    print(f"  ✓ Criptografia OK: {senha_original == senha_decripto}")
    
    print("\n" + "=" * 70)
    print("✓ Módulo de API pronto!")
    print("\n💡 Este módulo orquestra busca, processamento e armazenamento.")
    print("💡 Para uso real, configure DATABASE_URL e FERNET_KEY.")
    print("=" * 70)
