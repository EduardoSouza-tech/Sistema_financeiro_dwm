#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO: NFS-e Database Layer
Sistema de persistência para NFS-e (Nota Fiscal de Serviço Eletrônica)

Gerencia todas as operações de banco de dados relacionadas a:
- Configurações de municípios
- NFS-e baixadas
- RPS (Recibos Provisórios)
- Controle NSU

Autor: Sistema Financeiro DWM
Data: 2026-02-13
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NFSeDatabase:
    """
    Classe para gerenciar operações de banco de dados do sistema NFS-e
    """
    
    def __init__(self, connection_params: Dict[str, str]):
        """
        Inicializa conexão com banco de dados PostgreSQL
        
        Args:
            connection_params: Dict com host, database, user, password, port
        """
        self.connection_params = connection_params
        self.conn = None
        
        # Debug: Log dos parâmetros (sem mostrar senha completa)
        debug_params = connection_params.copy()
        if 'password' in debug_params:
            debug_params['password'] = '***' + str(debug_params['password'])[-4:] if debug_params.get('password') else 'None'
        logger.debug(f"[NFSeDatabase.__init__] connection_params: {debug_params}")
    
    def conectar(self) -> bool:
        """Estabelece conexão com banco de dados"""
        try:
            logger.debug(f"[NFSeDatabase.conectar] Tentando conectar com {len(self.connection_params)} parâmetros")
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info("✅ Conectado ao banco de dados NFS-e")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            logger.error(f"❌ Parâmetros usados: {list(self.connection_params.keys())}")
            return False
    
    def desconectar(self):
        """Fecha conexão com banco de dados"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Desconectado do banco de dados")
    
    def __enter__(self):
        """Context manager: entrada"""
        if not self.conectar():
            raise ConnectionError("Falha ao conectar ao banco de dados NFS-e")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: saída"""
        self.desconectar()
    
    # ========================================================================
    # CONFIGURAÇÕES DE MUNICÍPIOS
    # ========================================================================
    
    def adicionar_config_nfse(self, config: Dict) -> Optional[int]:
        """
        Adiciona configuração de município
        
        Args:
            config: Dict com dados da configuração
            
        Returns:
            ID da configuração criada ou None em caso de erro
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                INSERT INTO nfse_config (
                    empresa_id, cnpj_cpf, provedor, codigo_municipio, nome_municipio,
                    uf, inscricao_municipal, url_customizada, ativo
                ) VALUES (
                    %(empresa_id)s, %(cnpj_cpf)s, %(provedor)s, %(codigo_municipio)s,
                    %(nome_municipio)s, %(uf)s, %(inscricao_municipal)s,
                    %(url_customizada)s, %(ativo)s
                )
                ON CONFLICT (empresa_id, codigo_municipio) 
                DO UPDATE SET
                    provedor = EXCLUDED.provedor,
                    nome_municipio = EXCLUDED.nome_municipio,
                    uf = EXCLUDED.uf,
                    inscricao_municipal = EXCLUDED.inscricao_municipal,
                    url_customizada = EXCLUDED.url_customizada,
                    ativo = EXCLUDED.ativo,
                    atualizado_em = CURRENT_TIMESTAMP
                RETURNING id
                """
                cursor.execute(sql, config)
                config_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"✅ Configuração salva: {config['nome_municipio']} (ID: {config_id})")
                return config_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao adicionar config: {e}")
            return None
    
    def atualizar_config_nfse(self, config: Dict) -> bool:
        """
        Atualiza configuração de município por ID
        
        Args:
            config: Dict com dados da configuração (deve incluir 'id')
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            if 'id' not in config:
                logger.error("❌ ID da configuração não fornecido")
                return False
                
            with self.conn.cursor() as cursor:
                sql = """
                UPDATE nfse_config SET
                    cnpj_cpf = %(cnpj_cpf)s,
                    provedor = %(provedor)s,
                    codigo_municipio = %(codigo_municipio)s,
                    nome_municipio = %(nome_municipio)s,
                    uf = %(uf)s,
                    inscricao_municipal = %(inscricao_municipal)s,
                    url_customizada = %(url_customizada)s,
                    ativo = %(ativo)s,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = %(id)s AND empresa_id = %(empresa_id)s
                """
                cursor.execute(sql, config)
                rows_affected = cursor.rowcount
                self.conn.commit()
                
                if rows_affected > 0:
                    logger.info(f"✅ Configuração atualizada: ID {config['id']}")
                    return True
                else:
                    logger.warning(f"⚠️ Nenhuma configuração atualizada: ID {config['id']}")
                    return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao atualizar config: {e}")
            return False
    
    def get_config_nfse(self, empresa_id: int, codigo_municipio: Optional[str] = None) -> List[Dict]:
        """
        Busca configurações de municípios
        
        Args:
            empresa_id: ID da empresa
            codigo_municipio: Código do município (opcional, None = todos)
            
        Returns:
            Lista de configurações
        """
        if not self.conn:
            logger.error("❌ [get_config_nfse] Conexão não estabelecida!")
            return []
            
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if codigo_municipio:
                    sql = """
                    SELECT * FROM nfse_config 
                    WHERE empresa_id = %s AND codigo_municipio = %s
                    """
                    cursor.execute(sql, (empresa_id, codigo_municipio))
                else:
                    sql = """
                    SELECT * FROM nfse_config 
                    WHERE empresa_id = %s
                    ORDER BY nome_municipio
                    """
                    cursor.execute(sql, (empresa_id,))
                
                configs = [dict(row) for row in cursor.fetchall()]
                logger.debug(f"[get_config_nfse] Encontradas {len(configs)} configurações")
                return configs
        except Exception as e:
            logger.error(f"❌ Erro ao buscar configs: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []
    
    def atualizar_status_conexao(self, config_id: int, status: str, mensagem: Optional[str] = None):
        """
        Atualiza status de conexão de uma configuração
        
        Args:
            config_id: ID da configuração
            status: OK, ERRO, NAO_TESTADO
            mensagem: Mensagem de erro (opcional)
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                UPDATE nfse_config 
                SET status_conexao = %s,
                    mensagem_erro = %s,
                    testado_em = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                cursor.execute(sql, (status, mensagem, config_id))
                self.conn.commit()
                logger.info(f"✅ Status atualizado: Config {config_id} -> {status}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao atualizar status: {e}")
    
    def excluir_config(self, config_id: int) -> bool:
        """
        Exclui configuração de município
        
        Args:
            config_id: ID da configuração
            
        Returns:
            True se excluído com sucesso
        """
        try:
            with self.conn.cursor() as cursor:
                sql = "DELETE FROM nfse_config WHERE id = %s"
                cursor.execute(sql, (config_id,))
                self.conn.commit()
                logger.info(f"✅ Configuração excluída: ID {config_id}")
                return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao excluir config: {e}")
            return False
    
    # ========================================================================
    # NFS-e BAIXADAS
    # ========================================================================
    
    def salvar_nfse(self, nfse: Dict) -> Optional[int]:
        """
        Salva NFS-e no banco de dados
        
        Args:
            nfse: Dict com dados da NFS-e
            
        Returns:
            ID da NFS-e salva ou None em caso de erro
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                INSERT INTO nfse_baixadas (
                    numero_nfse, empresa_id, cnpj_prestador, cnpj_tomador,
                    razao_social_tomador, data_emissao, data_competencia,
                    valor_servico, valor_deducoes, valor_iss, aliquota_iss,
                    valor_liquido, codigo_servico, discriminacao, provedor,
                    codigo_municipio, nome_municipio, uf, situacao,
                    numero_rps, serie_rps, protocolo, codigo_verificacao,
                    xml_content, xml_path
                ) VALUES (
                    %(numero_nfse)s, %(empresa_id)s, %(cnpj_prestador)s,
                    %(cnpj_tomador)s, %(razao_social_tomador)s, %(data_emissao)s,
                    %(data_competencia)s, %(valor_servico)s, %(valor_deducoes)s,
                    %(valor_iss)s, %(aliquota_iss)s, %(valor_liquido)s,
                    %(codigo_servico)s, %(discriminacao)s, %(provedor)s,
                    %(codigo_municipio)s, %(nome_municipio)s, %(uf)s,
                    %(situacao)s, %(numero_rps)s, %(serie_rps)s,
                    %(protocolo)s, %(codigo_verificacao)s, %(xml)s, %(xml_path)s
                )
                ON CONFLICT (numero_nfse, codigo_municipio) 
                DO UPDATE SET
                    situacao = EXCLUDED.situacao,
                    xml_content = EXCLUDED.xml_content,
                    atualizado_em = CURRENT_TIMESTAMP
                RETURNING id
                """
                cursor.execute(sql, nfse)
                nfse_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"✅ NFS-e salva: {nfse['numero_nfse']} (ID: {nfse_id})")
                return nfse_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao salvar NFS-e: {e}")
            return None
    
    def buscar_nfse_periodo(
        self, 
        empresa_id: int, 
        data_inicial: date, 
        data_final: date,
        codigo_municipio: Optional[str] = None,
        situacao: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca NFS-e por período
        
        Args:
            empresa_id: ID da empresa
            data_inicial: Data inicial
            data_final: Data final
            codigo_municipio: Código do município (opcional)
            situacao: NORMAL, CANCELADA, SUBSTITUIDA (opcional)
            
        Returns:
            Lista de NFS-e
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                sql = """
                SELECT * FROM nfse_baixadas
                WHERE empresa_id = %s
                AND data_competencia BETWEEN %s AND %s
                """
                params = [empresa_id, data_inicial, data_final]
                
                if codigo_municipio:
                    sql += " AND codigo_municipio = %s"
                    params.append(codigo_municipio)
                
                if situacao:
                    sql += " AND situacao = %s"
                    params.append(situacao)
                
                sql += " ORDER BY data_emissao DESC"
                
                cursor.execute(sql, tuple(params))
                nfses = [dict(row) for row in cursor.fetchall()]
                logger.info(f"✅ Encontradas {len(nfses)} NFS-e")
                return nfses
        except Exception as e:
            logger.error(f"❌ Erro ao buscar NFS-e: {e}")
            return []
    
    def get_nfse_by_id(self, nfse_id: int) -> Optional[Dict]:
        """
        Busca NFS-e por ID
        
        Args:
            nfse_id: ID da NFS-e
            
        Returns:
            Dict com dados da NFS-e ou None
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                sql = "SELECT * FROM nfse_baixadas WHERE id = %s"
                cursor.execute(sql, (nfse_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar NFS-e: {e}")
            return None
    
    def get_nfse_by_numero(self, numero_nfse: str, codigo_municipio: str) -> Optional[Dict]:
        """
        Busca NFS-e por número e município
        
        Args:
            numero_nfse: Número da NFS-e
            codigo_municipio: Código do município
            
        Returns:
            Dict com dados da NFS-e ou None
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                sql = """
                SELECT * FROM nfse_baixadas 
                WHERE numero_nfse = %s AND codigo_municipio = %s
                """
                cursor.execute(sql, (numero_nfse, codigo_municipio))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar NFS-e: {e}")
            return None
    
    def cancelar_nfse(self, nfse_id: int, motivo: str) -> bool:
        """
        Marca NFS-e como cancelada
        
        Args:
            nfse_id: ID da NFS-e
            motivo: Motivo do cancelamento
            
        Returns:
            True se cancelado com sucesso
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                UPDATE nfse_baixadas 
                SET situacao = 'CANCELADA',
                    data_cancelamento = CURRENT_TIMESTAMP,
                    motivo_cancelamento = %s
                WHERE id = %s
                """
                cursor.execute(sql, (motivo, nfse_id))
                self.conn.commit()
                logger.info(f"✅ NFS-e cancelada: ID {nfse_id}")
                return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao cancelar NFS-e: {e}")
            return False
    
    def get_resumo_mensal(self, empresa_id: int, ano: int, mes: int) -> Dict:
        """
        Retorna resumo mensal de NFS-e
        
        Args:
            empresa_id: ID da empresa
            ano: Ano
            mes: Mês (1-12)
            
        Returns:
            Dict com totais
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                sql = """
                SELECT 
                    COUNT(*) as total_notas,
                    COUNT(DISTINCT codigo_municipio) as total_municipios,
                    COALESCE(SUM(valor_servico), 0) as valor_total,
                    COALESCE(SUM(valor_iss), 0) as iss_total
                FROM nfse_baixadas
                WHERE empresa_id = %s
                AND EXTRACT(YEAR FROM data_competencia) = %s
                AND EXTRACT(MONTH FROM data_competencia) = %s
                AND situacao = 'NORMAL'
                """
                cursor.execute(sql, (empresa_id, ano, mes))
                row = cursor.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            logger.error(f"❌ Erro ao buscar resumo: {e}")
            return {}
    
    # ========================================================================
    # RPS (Recibos Provisórios de Serviços)
    # ========================================================================
    
    def salvar_rps(self, rps: Dict) -> Optional[int]:
        """
        Salva RPS no banco de dados
        
        Args:
            rps: Dict com dados do RPS
            
        Returns:
            ID do RPS salvo ou None em caso de erro
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                INSERT INTO rps (
                    numero_rps, serie_rps, empresa_id, cnpj_prestador,
                    cnpj_tomador, data_emissao, valor_servico, discriminacao,
                    status, codigo_municipio, lote_id, protocolo, xml_rps
                ) VALUES (
                    %(numero_rps)s, %(serie_rps)s, %(empresa_id)s,
                    %(cnpj_prestador)s, %(cnpj_tomador)s, %(data_emissao)s,
                    %(valor_servico)s, %(discriminacao)s, %(status)s,
                    %(codigo_municipio)s, %(lote_id)s, %(protocolo)s, %(xml_rps)s
                )
                ON CONFLICT (numero_rps, serie_rps, cnpj_prestador)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    protocolo = EXCLUDED.protocolo,
                    atualizado_em = CURRENT_TIMESTAMP
                RETURNING id
                """
                cursor.execute(sql, rps)
                rps_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"✅ RPS salvo: {rps['numero_rps']} (ID: {rps_id})")
                return rps_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao salvar RPS: {e}")
            return None
    
    def get_rps_pendentes(self, empresa_id: int) -> List[Dict]:
        """
        Busca RPS pendentes de conversão
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            Lista de RPS pendentes
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                sql = """
                SELECT * FROM rps
                WHERE empresa_id = %s AND status = 'PENDENTE'
                ORDER BY criado_em ASC
                """
                cursor.execute(sql, (empresa_id,))
                rps_list = [dict(row) for row in cursor.fetchall()]
                return rps_list
        except Exception as e:
            logger.error(f"❌ Erro ao buscar RPS pendentes: {e}")
            return []
    
    def atualizar_status_rps(self, rps_id: int, status: str, numero_nfse: Optional[str] = None):
        """
        Atualiza status de um RPS
        
        Args:
            rps_id: ID do RPS
            status: Novo status (CONVERTIDO, ERRO, etc)
            numero_nfse: Número da NFS-e gerada (se convertido)
        """
        try:
            with self.conn.cursor() as cursor:
                if status == 'CONVERTIDO':
                    sql = """
                    UPDATE rps 
                    SET status = %s, numero_nfse = %s, convertido_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """
                    cursor.execute(sql, (status, numero_nfse, rps_id))
                else:
                    sql = "UPDATE rps SET status = %s WHERE id = %s"
                    cursor.execute(sql, (status, rps_id))
                
                self.conn.commit()
                logger.info(f"✅ Status RPS atualizado: {rps_id} -> {status}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao atualizar RPS: {e}")
    
    # ========================================================================
    # NSU (Controle de Sincronização)
    # ========================================================================
    
    def get_last_nsu(self, empresa_id: int, informante: str, codigo_municipio: Optional[str] = None) -> int:
        """
        Retorna último NSU processado
        
        Args:
            empresa_id: ID da empresa
            informante: CNPJ/CPF
            codigo_municipio: Código do município (None = todos)
            
        Returns:
            Último NSU (0 se nunca processado)
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                SELECT ult_nsu FROM nsu_nfse
                WHERE empresa_id = %s AND informante = %s
                AND (codigo_municipio = %s OR (codigo_municipio IS NULL AND %s IS NULL))
                """
                cursor.execute(sql, (empresa_id, informante, codigo_municipio, codigo_municipio))
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"❌ Erro ao buscar NSU: {e}")
            return 0
    
    def atualizar_nsu(self, empresa_id: int, informante: str, novo_nsu: int, codigo_municipio: Optional[str] = None):
        """
        Atualiza último NSU processado
        
        Args:
            empresa_id: ID da empresa
            informante: CNPJ/CPF
            novo_nsu: Novo NSU
            codigo_municipio: Código do município (None = todos)
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                INSERT INTO nsu_nfse (empresa_id, informante, codigo_municipio, ult_nsu)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (empresa_id, informante, codigo_municipio)
                DO UPDATE SET ult_nsu = EXCLUDED.ult_nsu, atualizado_em = CURRENT_TIMESTAMP
                """
                cursor.execute(sql, (empresa_id, informante, codigo_municipio, novo_nsu))
                self.conn.commit()
                logger.info(f"✅ NSU atualizado: {novo_nsu}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao atualizar NSU: {e}")
    
    # ========================================================================
    # AUDITORIA
    # ========================================================================
    
    def registrar_auditoria(self, empresa_id: int, usuario_id: int, operacao: str, detalhes: Dict, ip_address: str):
        """
        Registra operação no log de auditoria
        
        Args:
            empresa_id: ID da empresa
            usuario_id: ID do usuário
            operacao: Tipo de operação
            detalhes: Detalhes em formato JSON
            ip_address: IP do usuário
        """
        try:
            with self.conn.cursor() as cursor:
                sql = """
                INSERT INTO nfse_audit_log (empresa_id, usuario_id, operacao, detalhes, ip_address)
                VALUES (%s, %s, %s, %s::jsonb, %s)
                """
                import json
                cursor.execute(sql, (empresa_id, usuario_id, operacao, json.dumps(detalhes), ip_address))
                self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao registrar auditoria: {e}")

    # ========================================================================
    # CERTIFICADOS DIGITAIS A1
    # ========================================================================

    def salvar_certificado(self, empresa_id, pfx_data, senha_certificado, info_cert):
        """Salva ou atualiza certificado digital A1 da empresa"""
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Desativar outros certificados da empresa
                cursor.execute(
                    "UPDATE nfse_certificados SET ativo = FALSE WHERE empresa_id = %s AND ativo = TRUE",
                    (empresa_id,)
                )
                
                import base64
                senha_b64 = base64.b64encode(senha_certificado.encode()).decode()
                
                sql = """
                INSERT INTO nfse_certificados 
                    (empresa_id, pfx_data, senha_certificado, cnpj_extraido, razao_social, 
                     emitente, serial_number, validade_inicio, validade_fim,
                     codigo_municipio, nome_municipio, uf, ativo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id
                """
                cursor.execute(sql, (
                    empresa_id,
                    psycopg2.Binary(pfx_data),
                    senha_b64,
                    info_cert.get('cnpj'),
                    info_cert.get('razao_social'),
                    info_cert.get('emitente'),
                    info_cert.get('serial_number'),
                    info_cert.get('validade_inicio'),
                    info_cert.get('validade_fim'),
                    info_cert.get('codigo_municipio'),
                    info_cert.get('nome_municipio'),
                    info_cert.get('uf')
                ))
                cert_id = cursor.fetchone()['id']
                self.conn.commit()
                
                logger.info(f"✅ Certificado salvo ID={cert_id} empresa={empresa_id}")
                return cert_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao salvar certificado: {e}")
            raise

    def get_certificado_ativo(self, empresa_id):
        """Retorna o certificado ativo da empresa (sem o binário do pfx)"""
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """
                SELECT id, empresa_id, cnpj_extraido, razao_social, emitente, 
                       serial_number, validade_inicio, validade_fim,
                       codigo_municipio, nome_municipio, uf, ativo, criado_em
                FROM nfse_certificados 
                WHERE empresa_id = %s AND ativo = TRUE 
                ORDER BY criado_em DESC LIMIT 1
                """
                cursor.execute(sql, (empresa_id,))
                cert = cursor.fetchone()
                if cert:
                    # Converter datas para string
                    for campo in ['validade_inicio', 'validade_fim', 'criado_em']:
                        if cert.get(campo):
                            cert[campo] = cert[campo].isoformat()
                return cert
        except Exception as e:
            logger.error(f"❌ Erro ao buscar certificado: {e}")
            return None

    def get_certificado_pfx(self, empresa_id):
        """Retorna o certificado com dados PFX (para uso em SOAP)"""
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """
                SELECT id, pfx_data, senha_certificado, cnpj_extraido
                FROM nfse_certificados 
                WHERE empresa_id = %s AND ativo = TRUE 
                ORDER BY criado_em DESC LIMIT 1
                """
                cursor.execute(sql, (empresa_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Erro ao buscar PFX: {e}")
            return None

    def excluir_certificado(self, cert_id):
        """Exclui um certificado"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM nfse_certificados WHERE id = %s", (cert_id,))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao excluir certificado: {e}")
            raise

    # ========================================================================
    # CONTROLE DE NSU (Ambiente Nacional)
    # ========================================================================
    
    def get_last_nsu_nfse(self, cnpj_informante: str) -> Optional[int]:
        """
        Recupera último NSU processado para um CNPJ no Ambiente Nacional
        
        Args:
            cnpj_informante: CNPJ do informante (certificado)
        
        Returns:
            int: Último NSU processado ou None se não encontrado
        """
        try:
            with self.conn.cursor() as cursor:
                # Verifica se tabela existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'nsu_nfse'
                    )
                """)
                tabela_existe = cursor.fetchone()[0]
                
                if not tabela_existe:
                    logger.warning("⚠️ Tabela nsu_nfse não existe, criando...")
                    self._criar_tabela_nsu()
                    return None
                
                # Busca último NSU
                sql = """
                SELECT ultimo_nsu 
                FROM nsu_nfse 
                WHERE cnpj_informante = %s
                ORDER BY atualizado_em DESC 
                LIMIT 1
                """
                cursor.execute(sql, (cnpj_informante,))
                resultado = cursor.fetchone()
                
                if resultado:
                    logger.debug(f"📍 Último NSU para {cnpj_informante}: {resultado[0]}")
                    return resultado[0]
                else:
                    logger.debug(f"📍 Nenhum NSU registrado para {cnpj_informante}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erro ao buscar último NSU: {e}")
            return None
    
    def set_last_nsu_nfse(self, cnpj_informante: str, nsu: int) -> bool:
        """
        Atualiza último NSU processado para um CNPJ
        
        Args:
            cnpj_informante: CNPJ do informante
            nsu: Número do NSU processado
        
        Returns:
            bool: True se sucesso
        """
        try:
            with self.conn.cursor() as cursor:
                # Verifica se tabela existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'nsu_nfse'
                    )
                """)
                tabela_existe = cursor.fetchone()[0]
                
                if not tabela_existe:
                    logger.warning("⚠️ Tabela nsu_nfse não existe, criando...")
                    self._criar_tabela_nsu()
                
                # Upsert (INSERT ... ON CONFLICT UPDATE)
                sql = """
                INSERT INTO nsu_nfse (cnpj_informante, ultimo_nsu, atualizado_em)
                VALUES (%s, %s, NOW())
                ON CONFLICT (cnpj_informante) 
                DO UPDATE SET 
                    ultimo_nsu = EXCLUDED.ultimo_nsu,
                    atualizado_em = NOW()
                """
                cursor.execute(sql, (cnpj_informante, nsu))
                self.conn.commit()
                
                logger.debug(f"💾 NSU atualizado para {cnpj_informante}: {nsu}")
                return True
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao atualizar NSU: {e}")
            return False
    
    def _criar_tabela_nsu(self):
        """Cria tabela nsu_nfse se não existir"""
        try:
            with self.conn.cursor() as cursor:
                sql = """
                CREATE TABLE IF NOT EXISTS nsu_nfse (
                    id SERIAL PRIMARY KEY,
                    cnpj_informante VARCHAR(14) NOT NULL UNIQUE,
                    ultimo_nsu BIGINT NOT NULL DEFAULT 0,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_nsu_nfse_cnpj 
                ON nsu_nfse(cnpj_informante);
                """
                cursor.execute(sql)
                self.conn.commit()
                logger.info("✅ Tabela nsu_nfse criada com sucesso")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao criar tabela nsu_nfse: {e}")
            raise


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configuração de exemplo (ajustar conforme necessário)
    conn_params = {
        'host': 'localhost',
        'database': 'sistema_financeiro',
        'user': 'postgres',
        'password': 'senha',
        'port': 5432
    }
    
    # Usar context manager
    with NFSeDatabase(conn_params) as db:
        # Exemplo: Buscar configurações
        configs = db.get_config_nfse(empresa_id=1)
        print(f"Configurações encontradas: {len(configs)}")
        
        # Exemplo: Buscar NFS-e do mês atual
        from datetime import date
        hoje = date.today()
        primeiro_dia = date(hoje.year, hoje.month, 1)
        nfses = db.buscar_nfse_periodo(
            empresa_id=1,
            data_inicial=primeiro_dia,
            data_final=hoje
        )
        print(f"NFS-e encontradas: {len(nfses)}")
