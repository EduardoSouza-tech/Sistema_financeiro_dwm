#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT: Agendamento Automático de Busca NFS-e

Busca automática diária de NFS-e via Ambiente Nacional para
todos os certificados cadastrados no sistema.

Execução:
1. Manual:      python agendar_busca_nfse.py
2. Agendado:    Usar Task Scheduler (Windows) ou cron (Linux)

Autor: Sistema Financeiro DWM
Data: 2026-02-15
"""

import sys
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/busca_nfse_automatica.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar módulos do sistema
from database_postgresql import get_nfse_db_params
from nfse_functions import buscar_nfse_ambiente_nacional


def buscar_certificados():
    """
    Busca todos os certificados ativos no banco
    
    Returns:
        List[Dict]: Lista de certificados com dados necessários
    """
    try:
        from database_postgresql import get_db_connection
        import psycopg2.extras
        
        # Usar empresa_id=1 para buscar certificados globais
        # Ajustar conforme necessário para multi-empresa
        with get_db_connection(empresa_id=1) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            sql = """
            SELECT 
                c.id,
                c.empresa_id,
                c.cnpj_extraido,
                c.senha_certificado,
                c.pfx_data,
                c.nome_amigavel,
                e.razao_social as nome_empresa
            FROM nfse_certificados c
            LEFT JOIN empresas e ON e.id = c.empresa_id
            WHERE c.ativo = TRUE
            ORDER BY c.empresa_id, c.cnpj_extraido
            """
            
            cursor.execute(sql)
            certificados = cursor.fetchall()
            cursor.close()
            
            return certificados
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar certificados: {e}")
        return []


def salvar_certificado_temporario(pfx_data: bytes, cnpj: str) -> str:
    """
    Salva certificado PFX temporariamente para uso na busca
    
    Args:
        pfx_data: Dados binários do certificado
        cnpj: CNPJ do certificado
    
    Returns:
        str: Caminho do arquivo temporário
    """
    import tempfile
    
    # Criar pasta temp se não existir
    temp_dir = Path('temp_certs')
    temp_dir.mkdir(exist_ok=True)
    
    # Arquivo temporário com nome único
    temp_file = temp_dir / f"cert_{cnpj}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pfx"
    
    with open(temp_file, 'wb') as f:
        f.write(pfx_data)
    
    return str(temp_file)


def limpar_certificados_temporarios():
    """Remove certificados temporários antigos (> 1 dia)"""
    try:
        temp_dir = Path('temp_certs')
        if not temp_dir.exists():
            return
        
        limite = datetime.now() - timedelta(days=1)
        
        for arquivo in temp_dir.glob('cert_*.pfx'):
            if arquivo.stat().st_mtime < limite.timestamp():
                arquivo.unlink()
                logger.debug(f"🗑️ Removido certificado temporário: {arquivo.name}")
    
    except Exception as e:
        logger.warning(f"⚠️ Erro ao limpar certificados temporários: {e}")


def executar_busca_automatica():
    """
    Executa busca automática de NFS-e para todos os certificados
    """
    logger.info("=" * 70)
    logger.info("🤖 BUSCA AUTOMÁTICA DE NFS-e - INICIANDO")
    logger.info("=" * 70)
    logger.info(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"Método: Ambiente Nacional (API REST)")
    logger.info("=" * 70)
    
    # Limpar certificados temporários antigos
    limpar_certificados_temporarios()
    
    # Buscar certificados ativos
    certificados = buscar_certificados()
    
    if not certificados:
        logger.warning("⚠️ Nenhum certificado ativo encontrado")
        return
    
    logger.info(f"✅ Encontrados {len(certificados)} certificado(s) ativo(s)")
    
    # Parâmetros do banco
    db_params = get_nfse_db_params()
    
    # Estatísticas globais
    total_processados = 0
    total_sucesso = 0
    total_nfse = 0
    total_erros = 0
    
    # Processar cada certificado
    for cert in certificados:
        try:
            cnpj = cert['cnpj_extraido']
            empresa_id = cert['empresa_id']
            nome_empresa = cert.get('nome_empresa', 'Sem nome')
            nome_cert = cert.get('nome_amigavel', cnpj)
            
            logger.info("")
            logger.info("─" * 70)
            logger.info(f"📜 Processando: {nome_cert}")
            logger.info(f"   Empresa: {nome_empresa}")
            logger.info(f"   CNPJ: {cnpj}")
            logger.info("─" * 70)
            
            # Salvar certificado temporariamente
            cert_path = salvar_certificado_temporario(cert['pfx_data'], cnpj)
            cert_senha = cert['senha_certificado']
            
            # Executar busca via Ambiente Nacional
            # Busca incremental (apenas novos documentos desde última execução)
            resultado = buscar_nfse_ambiente_nacional(
                db_params=db_params,
                empresa_id=empresa_id,
                cnpj_informante=cnpj,
                certificado_path=cert_path,
                certificado_senha=cert_senha,
                ambiente='producao',
                busca_completa=False,  # Incremental
                max_documentos=100  # Limite por execução
            )
            
            # Remover certificado temporário
            try:
                Path(cert_path).unlink()
            except:
                pass
            
            # Contabilizar resultados
            total_processados += 1
            
            if resultado['sucesso']:
                total_sucesso += 1
                total_nfse += resultado['total_nfse']
                
                logger.info(f"✅ Concluído: {resultado['total_nfse']} NFS-e")
                logger.info(f"   Novas: {resultado['nfse_novas']} | Atualizadas: {resultado['nfse_atualizadas']}")
                logger.info(f"   Último NSU: {resultado['ultimo_nsu']}")
            else:
                total_erros += 1
                erros = ', '.join(resultado.get('erros', ['Erro desconhecido']))
                logger.error(f"❌ Erro ao processar certificado: {erros}")
        
        except Exception as e:
            total_processados += 1
            total_erros += 1
            logger.error(f"❌ Erro ao processar certificado {cert.get('cnpj_extraido', '?')}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Resumo final
    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 RESUMO DA EXECUÇÃO")
    logger.info("=" * 70)
    logger.info(f"Total de certificados: {len(certificados)}")
    logger.info(f"Processados: {total_processados}")
    logger.info(f"Sucesso: {total_sucesso}")
    logger.info(f"Erros: {total_erros}")
    logger.info(f"Total de NFS-e obtidas: {total_nfse}")
    logger.info("=" * 70)
    logger.info(f"🏁 Execução concluída: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        # Criar pasta de logs se não existir
        Path('logs').mkdir(exist_ok=True)
        
        # Executar busca automática
        executar_busca_automatica()
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Execução interrompida pelo usuário")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
