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
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cryptography.fernet import Fernet

# Logger
logger = logging.getLogger(__name__)

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
    from database_postgresql import get_db_connection
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
    """
    Descriptografa a senha do certificado.
    
    Se a senha tiver menos de 50 chars, assume que está em texto plano
    (certificados cadastrados antes da criptografia ser implementada)
    e retorna diretamente sem tentar descriptografar.
    
    Raises:
        ValueError: Se a senha não puder ser descriptografada
    """
    # Tokens Fernet têm pelo menos 72 caracteres base64-encoded.
    # Senhas curtas foram salvas em texto plano — usa diretamente.
    if len(senha_cripto) < 50:
        logger.warning(
            f"[CERT] ⚠️ Senha com {len(senha_cripto)} chars parece texto plano. "
            "Usando diretamente (sem descriptografia). "
            "Recomendado: recadastrar o certificado para criptografar a senha."
        )
        return senha_cripto
    
    try:
        f = Fernet(chave)
        senha_cripto_bytes = senha_cripto.encode('utf-8')
        senha_bytes = f.decrypt(senha_cripto_bytes)
        return senha_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(
            f"Erro ao descriptografar senha do certificado: {str(e)}. "
            "O certificado pode ter sido cadastrado com uma chave diferente. "
            "Por favor, recadastre o certificado."
        )


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
        
        # Criptografa senha (se FERNET_KEY configurada; caso contrário, salva em texto plano)
        if not chave_cripto:
            chave_cripto_str = os.environ.get('FERNET_KEY', '')
            logger.info(f"[CERTIFICADO] FERNET_KEY para salvar: {'✅ Presente (' + str(len(chave_cripto_str)) + ' chars)' if chave_cripto_str else '⚠️ Ausente - salvando senha em texto plano'}")
            chave_cripto = chave_cripto_str.encode('utf-8') if chave_cripto_str else None
        
        if chave_cripto:
            logger.info(f"[CERTIFICADO] Criptografando senha de {len(senha)} caracteres...")
            senha_cripto = criptografar_senha(senha, chave_cripto)
            logger.info(f"[CERTIFICADO] ✅ Senha criptografada: {len(senha_cripto)} chars")
        else:
            senha_cripto = senha
            logger.warning(f"[CERTIFICADO] ⚠️ FERNET_KEY ausente: senha salva em texto plano ({len(senha)} chars). Configure FERNET_KEY para maior segurança.")
        
        # Salva no banco
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # Busca qualquer certificado da empresa (ativo ou não), pelo CNPJ normalizado ou pelo empresa_id
            # Normaliza CNPJ para comparação (remove máscara)
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
            
            cursor.execute("""
                SELECT id FROM certificados_digitais
                WHERE empresa_id = %s
                  AND (
                    REGEXP_REPLACE(cnpj, '[^0-9]', '', 'g') = %s
                    OR cnpj = %s
                  )
                ORDER BY id
                LIMIT 1
            """, (empresa_id, cnpj_limpo, cnpj))
            
            resultado = cursor.fetchone()
            
            # Se não encontrou por CNPJ, pega qualquer cert da empresa (o mais antigo)
            if not resultado:
                cursor.execute("""
                    SELECT id FROM certificados_digitais
                    WHERE empresa_id = %s
                    ORDER BY id
                    LIMIT 1
                """, (empresa_id,))
                resultado = cursor.fetchone()
            
            logger.info(f"[CERTIFICADO] Resultado da busca: {resultado}, tipo: {type(resultado)}")
            
            if resultado:
                # Atualiza certificado existente
                # Suporta tanto tupla quanto dict (RealDictCursor)
                if isinstance(resultado, dict):
                    certificado_id = resultado['id']
                else:
                    certificado_id = resultado[0]
                    
                logger.info(f"[CERTIFICADO] Atualizando certificado existente ID {certificado_id}")
                cursor.execute("""
                    UPDATE certificados_digitais
                    SET nome_certificado = %s,
                        cnpj = %s,
                        pfx_base64 = %s,
                        senha_pfx = %s,
                        cuf = %s,
                        ambiente = %s,
                        valido_de = %s,
                        valido_ate = %s,
                        ativo = TRUE
                    WHERE id = %s
                """, (nome_certificado, cnpj_limpo, pfx_base64, senha_cripto, cuf, ambiente,
                      valido_de, valido_ate, certificado_id))
            else:
                # Nenhum cert encontrado: insere novo
                logger.info(f"[CERTIFICADO] Inserindo novo certificado para empresa {empresa_id}")
                
                # Insere novo certificado (sem desativar outros — usuário deve desativar manualmente)
                cursor.execute("""
                    INSERT INTO certificados_digitais 
                    (empresa_id, cnpj, nome_certificado, pfx_base64, senha_pfx, 
                     cuf, ambiente, valido_de, valido_ate, criado_por, ativo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                """, (empresa_id, cnpj_limpo, nome_certificado, pfx_base64, senha_cripto,
                      cuf, ambiente, valido_de, valido_ate, usuario_id))
                
                resultado_insert = cursor.fetchone()
                if isinstance(resultado_insert, dict):
                    certificado_id = resultado_insert['id']
                else:
                    certificado_id = resultado_insert[0]
                    
                logger.info(f"[CERTIFICADO] Novo certificado criado com ID {certificado_id}")
            
            conn.commit()
        
        return {
            'sucesso': True,
            'certificado_id': certificado_id,
            'valido_de': valido_de.isoformat() if hasattr(valido_de, 'isoformat') else str(valido_de),
            'valido_ate': valido_ate.isoformat() if hasattr(valido_ate, 'isoformat') else str(valido_ate)
        }
        
    except Exception as e:
        logger.error(f"[CERTIFICADO] Erro ao salvar certificado: {type(e).__name__}")
        logger.error(f"[CERTIFICADO] Detalhes: {repr(e)}")
        logger.error(f"[CERTIFICADO] Traceback:\n{traceback.format_exc()}")
        return {
            'sucesso': False,
            'erro': f'Erro ao salvar certificado: {type(e).__name__}: {str(e)}'
        }


def obter_certificado(certificado_id: int, chave_cripto: bytes = None) -> Optional[nfe_busca.CertificadoA1]:
    """
    Carrega certificado do banco e retorna objeto CertificadoA1.
    
    Args:
        certificado_id: ID do certificado
        chave_cripto: Chave Fernet (usa variável ambiente se não fornecida)
        
    Returns:
        Objeto CertificadoA1 ou None
    """
    try:
        logger.info(f"[CERT] Obtendo certificado ID {certificado_id}")
        
        # Primeiro busca os dados para saber a empresa_id
        # Como não sabemos a empresa aqui, precisamos buscar sem RLS
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT pfx_base64, senha_pfx, ativo
                FROM certificados_digitais
                WHERE id = %s
            """, (certificado_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.error(f"[CERT] Certificado ID {certificado_id} não encontrado no banco")
                return None
            
            pfx_base64  = row['pfx_base64']
            senha_cripto = row['senha_pfx']
            ativo        = row['ativo']
            logger.info(f"[CERT] Certificado encontrado, ativo={ativo}")
            
            if not ativo:
                logger.warning(f"[CERT] Certificado ID {certificado_id} está inativo — acesse '🏢 Dados da Empresa' para reativar")
                return None

            senha_len = len(senha_cripto) if senha_cripto else 0
            logger.info(f"[CERT] Processando senha (tamanho: {senha_len} chars)...")

            # Verifica disponibilidade da chave
            if not chave_cripto:
                chave_cripto_str = os.environ.get('FERNET_KEY', '')
                chave_cripto = chave_cripto_str.encode('utf-8') if chave_cripto_str else None
                logger.info(f"[CERT] FERNET_KEY: {'SIM (' + str(len(chave_cripto_str)) + ' chars)' if chave_cripto_str else 'AUSENTE'}")

            # Senhas curtas (< 50 chars) OU sem FERNET_KEY → texto plano
            if senha_len < 50 or not chave_cripto:
                if not chave_cripto and senha_len >= 50:
                    logger.warning(f"[CERT] ⚠️ FERNET_KEY ausente e senha >= 50 chars — tentando como texto plano")
                else:
                    logger.warning(f"[CERT] Senha texto plano ({senha_len} chars) — usando diretamente")
                senha = senha_cripto
            else:
                try:
                    senha = descriptografar_senha(senha_cripto, chave_cripto)
                    logger.info("[CERT] ✅ Senha Fernet descriptografada com sucesso")
                except ValueError as ve:
                    logger.error(f"[CERT] ❌ Falha ao descriptografar senha: {ve}")
                    logger.error(f"[CERT]   Tamanho senha_cripto: {senha_len} chars")
                    logger.error("[CERT]   Possível causa: FERNET_KEY diferente entre salvar e recuperar")
                    logger.error("[CERT]   SOLUÇÃO: Recadastre o certificado em '🏢 Dados da Empresa e Certificado Digital'")
                    return None
                except Exception as e:
                    logger.error(f"[CERT] ❌ Erro inesperado descriptografando senha: {type(e).__name__}: {e}")
                    return None
            
            # Cria certificado
            logger.info(f"[CERT] Criando objeto CertificadoA1 (pfx_len={len(pfx_base64)}, senha_len={len(senha)})...")
            try:
                cert = nfe_busca.CertificadoA1(pfx_base64=pfx_base64, senha=senha)
            except Exception as cert_err:
                logger.error(f"[CERT] ❌ Falha ao criar CertificadoA1: {type(cert_err).__name__}: {cert_err}")
                logger.error(f"[CERT]   Provável causa: senha incorreta para o PFX")
                logger.error(f"[CERT]   Traceback: {traceback.format_exc()}")
                return None
            
            logger.info(f"[CERT] Certificado ID {certificado_id} carregado com sucesso")
            if cert.cert_data:
                logger.info(
                    f"[CERT] Subject: {cert.cert_data.get('subject', 'N/A')}"
                )
                logger.info(
                    f"[CERT] CNPJ extraído do PFX: {cert.cert_data.get('cnpj', 'NÃO ENCONTRADO')}"
                )
                logger.info(
                    f"[CERT] Válido até: {cert.cert_data.get('valido_ate', 'N/A')}"
                )
            return cert
        
    except ValueError:
        # Já tratado acima, apenas re-lança
        return None
    except Exception as e:
        logger.error(f"[CERT] Erro ao obter certificado ID {certificado_id}: {type(e).__name__}: {str(e)}")
        logger.error(f"[CERT] Traceback: {traceback.format_exc()}")
        return None


# ============================================================================
# BUSCA E PROCESSAMENTO DE DOCUMENTOS
# ============================================================================

def buscar_e_processar_novos_documentos(certificado_id: int, usuario_id: int = None) -> Dict[str, any]:
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
        
    Returns:
        Dict com estatísticas da busca
    """
    try:
        # Carrega certificado
        cert = obter_certificado(certificado_id)
        if not cert:
            return {
                'sucesso': False, 
                'erro': 'Certificado não encontrado ou senha inválida. Acesse "🏢 Dados da Empresa e Certificado Digital" para cadastrar ou atualizar o certificado.'
            }
        
        # Busca dados do certificado no banco (allow_global pois buscamos cert diretamente)
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT empresa_id, cnpj, ultimo_nsu, cuf, ambiente
                FROM certificados_digitais
                WHERE id = %s
            """, (certificado_id,))
            
            row = cursor.fetchone()
            if not row:
                return {'sucesso': False, 'erro': 'Certificado não encontrado'}
            
            empresa_id  = row['empresa_id']
            cnpj        = row['cnpj']
            ultimo_nsu  = row['ultimo_nsu']
            cuf         = row['cuf']
            ambiente    = row['ambiente']

        # ── Valida CNPJ: o CNPJ no SOAP DEVE ser o mesmo gravado no PFX ──────
        # A SEFAZ autentica via mTLS usando o certificado; se o CNPJ no <CNPJ>
        # do XML diferir do CNPJ do certificado → NullReferenceException.
        cnpj_cert = cert.cert_data.get('cnpj') if cert.cert_data else None
        cnpj_banco = ''.join(filter(str.isdigit, str(cnpj or '')))

        if cnpj_cert:
            if cnpj_cert != cnpj_banco:
                logger.warning(
                    f"[SEFAZ] ⚠️ CNPJ DIVERGENTE: banco={cnpj_banco!r} vs certificado={cnpj_cert!r}. "
                    "Usando o CNPJ do certificado (obrigatório para autenticação mTLS)."
                )
            else:
                logger.info(f"[SEFAZ] ✅ CNPJ confirmado (banco == certificado): {cnpj_cert}")
            cnpj_soap = cnpj_cert   # Sempre usa o CNPJ gravado no PFX
        else:
            logger.warning(
                f"[SEFAZ] ⚠️ Não foi possível extrair CNPJ do certificado. "
                f"Usando CNPJ do banco: {cnpj_banco!r}"
            )
            cnpj_soap = cnpj_banco

        logger.info(
            f"[SEFAZ] Iniciando busca: empresa_id={empresa_id}, "
            f"cnpj_soap={cnpj_soap!r}, cuf={cuf!r}, ambiente={ambiente!r}, "
            f"ultimo_nsu={ultimo_nsu!r}"
        )

        # Busca documentos na SEFAZ
        resultado_busca = nfe_busca.baixar_documentos_dfe(
            certificado=cert,
            cnpj=cnpj_soap,
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
        
        # Processa cada documento usando uma conexão com empresa_id
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            
            # Processa todos os documentos retornados pela SEFAZ (sem limite artificial)
            for doc in documentos:
                nsu = doc['nsu']
                schema = doc['schema']
                xml_content = doc.get('xml')
                
                if not xml_content:
                    stats['erros'] += 1
                    stats['documentos_detalhes'].append({
                        'sucesso': False, 'nsu': nsu, 'schema': schema,
                        'erro': 'XML vazio ou erro ao descomprimir'
                    })
                    continue
                
                # Detecta schema
                schema_info = nfe_processor.detectar_schema_nfe(xml_content)
                
                if not schema_info['sucesso']:
                    stats['erros'] += 1
                    stats['documentos_detalhes'].append({
                        'sucesso': False, 'nsu': nsu, 'schema': schema,
                        'erro': schema_info.get('erro', 'Erro ao detectar schema')
                    })
                    continue
                
                # Processa de acordo com o tipo
                if schema_info['categoria'] == 'NFe':
                    resultado_proc = _processar_nfe(
                        empresa_id, certificado_id, cnpj, nsu, schema, 
                        xml_content, usuario_id, cursor
                    )
                    resultado_proc.setdefault('nsu', nsu)
                    resultado_proc.setdefault('schema', schema)
                    if resultado_proc['sucesso']:
                        stats['nfes_processadas'] += 1
                    else:
                        stats['erros'] += 1
                    
                    stats['documentos_detalhes'].append(resultado_proc)
                    
                elif schema_info['categoria'] == 'CTe':
                    resultado_proc = _processar_cte(
                        empresa_id, certificado_id, cnpj, nsu, schema,
                        xml_content, usuario_id, cursor
                    )
                    resultado_proc.setdefault('nsu', nsu)
                    resultado_proc.setdefault('schema', schema)
                    if resultado_proc['sucesso']:
                        stats['ctes_processados'] += 1
                    else:
                        stats['erros'] += 1
                    
                    stats['documentos_detalhes'].append(resultado_proc)
                    
                elif schema_info['categoria'] == 'Evento':
                    resultado_proc = _processar_evento(
                        empresa_id, certificado_id, nsu, schema,
                        xml_content, usuario_id, cursor
                    )
                    resultado_proc.setdefault('nsu', nsu)
                    resultado_proc.setdefault('schema', schema)
                    if resultado_proc['sucesso']:
                        stats['eventos_processados'] += 1
                    else:
                        stats['erros'] += 1
                    stats['documentos_detalhes'].append(resultado_proc)
                
                else:
                    stats['erros'] += 1
                    stats['documentos_detalhes'].append({
                        'sucesso': False, 'nsu': nsu, 'schema': schema,
                        'erro': f'Tipo não suportado: {schema_info.get("categoria", "?")} ({schema_info.get("tag_raiz", "??")})'
                    })
                
                stats['total_baixados'] += 1
            
            # Atualiza NSU do certificado
            cursor.execute("""
                UPDATE certificados_digitais
                SET ultimo_nsu = %s,
                    max_nsu = %s,
                    data_ultima_busca = NOW()
                WHERE id = %s
            """, (novo_nsu, resultado_busca.get('maxNSU'), certificado_id))
            
            conn.commit()
        
        stats['sucesso'] = True
        stats['novo_nsu'] = novo_nsu
        stats['max_nsu'] = resultado_busca.get('maxNSU')
        
        return stats
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao buscar documentos: {str(e)}'
        }


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


def _processar_cte(empresa_id: int, certificado_id: int, cnpj_empresa: str,
                  nsu: str, schema: str, xml_content: str,
                  usuario_id: int, cursor) -> Dict[str, any]:
    """Processa um CT-e e salva no banco."""
    try:
        # Extrai dados
        dados = nfe_processor.extrair_dados_nfe(xml_content, cnpj_empresa)
        
        if not dados['sucesso']:
            return {'sucesso': False, 'erro': dados['erro']}
        
        chave = dados.get('chave', '')
        
        # Salva XML no storage (reutiliza o storage de NF-e)
        resultado_storage = nfe_storage.salvar_xml_nfe(
            cnpj_certificado=cnpj_empresa,
            chave=chave,
            xml_content=xml_content,
            tipo_xml=dados.get('tipo_xml', 'procCTe'),
            data_emissao=dados.get('data_emissao')
        )
        
        if not resultado_storage['sucesso']:
            return {'sucesso': False, 'erro': 'Erro ao salvar XML do CT-e'}
        
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
            empresa_id, certificado_id, nsu, chave, 'CTe', schema,
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
                total_ctes = total_ctes + 1
            WHERE id = %s
        """, (certificado_id,))
        
        return {
            'sucesso': True,
            'chave': chave,
            'numero': dados.get('numero'),
            'valor': dados.get('valor_total'),
            'direção': dados.get('direcao'),
            'tipo': 'CTe'
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
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
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
                    'id':                row['id'],
                    'nsu':               row['nsu'],
                    'chave':             row['chave'],
                    'tipo':              row['tipo_documento'],
                    'numero':            row['numero_documento'],
                    'serie':             row['serie'],
                    'valor':             float(row['valor_total']) if row['valor_total'] else 0.0,
                    'emitente_cnpj':     row['cnpj_emitente'],
                    'emitente_nome':     row['nome_emitente'],
                    'destinatario_cnpj': row['cnpj_destinatario'],
                    'destinatario_nome': row['nome_destinatario'],
                    'data_emissao':      row['data_emissao'],
                    'caminho_xml':       row['caminho_xml'],
                    'data_busca':        row['data_busca']
                })
            
            return documentos
        
    except Exception as e:
        print(f"Erro ao listar documentos: {e}")
        return []


def obter_estatisticas_empresa(empresa_id: int) -> Dict[str, any]:
    """
    Retorna estatísticas de documentos de uma empresa.
    
    Args:
        empresa_id: ID da empresa
        
    Returns:
        Dict com estatísticas
    """
    try:
        with get_db_connection(empresa_id=empresa_id) as conn:
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
                'total_documentos': row['total'] or 0,
                'total_nfes':       row['total_nfes'] or 0,
                'total_ctes':       row['total_ctes'] or 0,
                'total_eventos':    row['total_eventos'] or 0,
                'valor_total_nfes': float(row['valor_total_nfes']) if row['valor_total_nfes'] else 0.0
            }

            # Certificados ativos
            cursor.execute("""
                SELECT COUNT(*) AS total_certs
                FROM certificados_digitais
                WHERE empresa_id = %s AND ativo = TRUE
            """, (empresa_id,))

            stats['certificados_ativos'] = cursor.fetchone()['total_certs']
            
            return stats
        
    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        return {}


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
