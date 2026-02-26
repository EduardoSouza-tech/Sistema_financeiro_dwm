"""
Aplicação Flask standalone para Consulta de NFS-e (Nota Fiscal de Serviço Eletrônica)
🔥 MICROSERVIÇO DE BUSCA PESADA 🔥

OBJETIVO:
Este serviço é dedicado EXCLUSIVAMENTE a operações de busca pesadas e demoradas:
- ✅ Busca NFS-e via Ambiente Nacional (REST API)
- ✅ Busca NFS-e via SOAP Municipal
- 🚧 Busca NF-e via SEFAZ (em desenvolvimento)
- 🚧 Busca CT-e via SEFAZ (em desenvolvimento)

SEPARAÇÃO DE RESPONSABILIDADES:
┌─────────────────────────────────────────────────────────────┐
│ ERP Financeiro (web_server.py)                              │
│ • Interface HTML/JS                                         │
│ • Upload/gestão de certificados                             │
│ • Listagem de notas (consulta banco local)                  │
│ • Exportação Excel/XML (dados já baixados)                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Busca de Notas (app_nfse.py) - ESTE SERVIÇO                │
│ • 🔥 Busca pesada NFS-e (Ambiente Nacional)                 │
│ • 🔥 Busca pesada NFS-e (SOAP Municipal)                    │
│ • 🔥 Busca pesada NF-e (futuro)                             │
│ • 🔥 Busca pesada CT-e (futuro)                             │
└─────────────────────────────────────────────────────────────┘

Provedores NFS-e suportados:
- GINFES (500+ municípios)
- ISS.NET (200+ municípios)
- BETHA (1000+ municípios)
- e-ISS (150+ municípios)
- WebISS (50+ municípios)
- SimplISS (300+ municípios)
"""
import os
import sys
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# ⚠️ IMPORTS AJUSTADOS - Removendo funções antigas
# Importing only database and service layers (não usar buscar_nfse_por_periodo antigo)
from nfse_database import NFSeDatabase
from nfse_service import NFSeService, descobrir_provedor, testar_conexao

# As funções corretas de busca serão importadas dentro das rotas:
# - buscar_nfse_ambiente_nacional (nfse_functions.py)
# - buscar_nfse_periodo (nfse_functions.py)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar app Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# CORS para permitir chamadas do frontend principal
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get('FRONTEND_URL', '*'),
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuração do banco
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL não configurada!")
    sys.exit(1)

logger.info("✅ DATABASE_URL configurada")
logger.info("✅ Microserviço de busca inicializado (modo stateless)")


def get_db_connection():
    """Retorna conexão com banco de dados"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        raise


def get_empresa_id_from_token(token):
    """Extrai empresa_id do token JWT (simplificado)"""
    # TODO: Implementar validação JWT completa
    empresa_id = request.headers.get('X-Empresa-ID', '1')
    return int(empresa_id)


def require_auth(f):
    """Decorator simples de autenticação"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 401
        
        # TODO: Validar token JWT
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function


# ==================== ROTAS DA API ====================

@app.route('/health')
def health_check():
    """Health check para Railway"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'service': 'nfse-consulta',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route('/')
def index():
    """Página inicial"""
    return render_template('nfse_dashboard.html')


@app.route('/api/nfse/config', methods=['GET'])
@require_auth
def listar_configuracoes():
    """
    ⚠️ REDIRECIONAMENTO
    Configurações devem ser gerenciadas no ERP Financeiro.
    """
    return jsonify({
        'success': False,
        'error': 'Use o endpoint /api/nfse/config no ERP Financeiro'
    }), 301


@app.route('/api/nfse/config', methods=['POST'])
@require_auth
def criar_configuracao():
    """
    ⚠️ REDIRECIONAMENTO
    Configurações devem ser gerenciadas no ERP Financeiro.
    """
    return jsonify({
        'success': False,
        'error': 'Use o endpoint /api/nfse/config no ERP Financeiro'
    }), 301


@app.route('/api/nfse/config/<int:config_id>', methods=['PUT'])
@require_auth
def atualizar_configuracao(config_id):
    """
    ⚠️ REDIRECIONAMENTO
    Configurações devem ser gerenciadas no ERP Financeiro.
    """
    return jsonify({
        'success': False,
        'error': 'Use o endpoint /api/nfse/config no ERP Financeiro'
    }), 301


@app.route('/api/nfse/config/<int:config_id>', methods=['DELETE'])
@require_auth
def deletar_configuracao(config_id):
    """
    ⚠️ REDIRECIONAMENTO
    Configurações devem ser gerenciadas no ERP Financeiro.
    """
    return jsonify({
        'success': False,
        'error': 'Use o endpoint /api/nfse/config no ERP Financeiro'
    }), 301


@app.route('/api/nfse/buscar', methods=['POST'])
@require_auth
def buscar_nfse():
    """
    🔥 BUSCA PESADA DE NFS-e
    Processa busca via Ambiente Nacional (REST) ou SOAP Municipal
    Esta é a operação principal do microserviço (pode demorar vários minutos)
    """
    try:
        logger.info("🚀 Iniciando busca pesada de NFS-e no microserviço")
        
        empresa_id = get_empresa_id_from_token(request.headers.get('Authorization'))
        data = request.json
        
        # Validar campos obrigatórios
        if not data.get('data_inicial') or not data.get('data_final'):
            return jsonify({
                'success': False,
                'error': 'Datas inicial e final são obrigatórias'
            }), 400
        
        # Obter CNPJ da empresa
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT cnpj FROM empresas WHERE id = %s", (empresa_id,))
            empresa = cursor.fetchone()
            cursor.close()
        
        if not empresa:
            return jsonify({
                'success': False,
                'error': 'Empresa não encontrada'
            }), 404
        
        cnpj_prestador = empresa['cnpj'].replace('.', '').replace('/', '').replace('-', '')
        
        # Buscar certificado da empresa
        from nfse_functions import get_certificado_para_soap
        from database_postgresql import get_nfse_db_params
        
        db_params = get_nfse_db_params()
        cert_data = get_certificado_para_soap(db_params, empresa_id)
        
        if cert_data:
            import tempfile
            pfx_bytes, cert_senha = cert_data
            temp_cert = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
            temp_cert.write(pfx_bytes)
            temp_cert.close()
            certificado_path = temp_cert.name
            certificado_senha = cert_senha
        else:
            certificado_path = os.getenv('CERTIFICADO_A1_PATH', '/app/certificados/certificado.pfx')
            certificado_senha = os.getenv('CERTIFICADO_A1_SENHA', '')
            
            if not os.path.exists(certificado_path):
                return jsonify({
                    'success': False,
                    'error': 'Certificado A1 não configurado'
                }), 400
        
        # Converter datas
        data_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d').date()
        data_final = datetime.strptime(data['data_final'], '%Y-%m-%d').date()
        
        codigos_municipios = data.get('codigos_municipios')
        metodo = data.get('metodo', 'ambiente_nacional')  # Padrão: Ambiente Nacional
        
        logger.info(f"Método escolhido: {metodo}")
        logger.info(f"Período: {data_inicial} a {data_final}")
        
        # ========== ROTEAMENTO DE BUSCA ==========
        if metodo == 'ambiente_nacional':
            # 🌐 BUSCA VIA AMBIENTE NACIONAL (API REST)
            from nfse_functions import buscar_nfse_ambiente_nacional
            
            logger.info("🌐 Usando Ambiente Nacional (API REST)")
            
            resultado = buscar_nfse_ambiente_nacional(
                db_params=db_params,
                empresa_id=empresa_id,
                cnpj_informante=cnpj_prestador,
                certificado_path=certificado_path,
                certificado_senha=certificado_senha,
                ambiente=data.get('ambiente', 'producao'),
                busca_completa=data.get('busca_completa', False),
                max_documentos=data.get('max_documentos', 50)
            )
        else:
            # 📡 BUSCA VIA SOAP MUNICIPAL
            from nfse_functions import buscar_nfse_periodo
            
            logger.info("📡 Usando APIs SOAP municipais")
            
            resultado = buscar_nfse_periodo(
                db_params=db_params,
                empresa_id=empresa_id,
                cnpj_prestador=cnpj_prestador,
                data_inicial=data_inicial,
                data_final=data_final,
                certificado_path=certificado_path,
                certificado_senha=certificado_senha,
                codigos_municipios=codigos_municipios
            )
        
        # Limpar certificado temporário
        if cert_data and os.path.exists(certificado_path):
            try:
                os.unlink(certificado_path)
            except:
                pass
        
        # Log de auditoria
        from nfse_functions import registrar_operacao
        registrar_operacao(
            db_params=db_params,
            empresa_id=empresa_id,
            usuario_id=1,  # TODO: pegar do token
            operacao='BUSCA_PESADA',
            detalhes={
                'metodo': metodo,
                'data_inicial': data['data_inicial'],
                'data_final': data['data_final'],
                'total_nfse': resultado.get('total_nfse', 0)
            },
            ip_address=request.remote_addr
        )
        
        logger.info(f"✅ Busca concluída: {resultado.get('total_nfse', 0)} NFS-e encontradas")
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar NFS-e: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nfse/consultar', methods=['POST'])
@require_auth
def consultar_nfse():
    """
    ⚠️ REDIRECIONAMENTO
    Consultas ao banco local devem ser feitas no ERP Financeiro.
    Esta rota existe apenas para compatibilidade.
    """
    return jsonify({
        'success': False,
        'error': 'Use o endpoint /api/nfse/consultar no ERP Financeiro para consultas locais'
    }), 301




# ==================== ROTAS REMOVIDAS ====================
# As seguintes rotas foram movidas para web_server.py (ERP Financeiro):
# - GET  /api/nfse (listar)
# - GET  /api/nfse/<id> (detalhes)
# - DELETE /api/nfse/<id> (deletar)
# - GET  /api/nfse/<id>/pdf (download PDF)
# - GET  /api/nfse/<id>/xml (download XML)
# - GET  /api/nfse/estatisticas
# - POST /api/nfse/resumo-mensal
# - POST /api/nfse/export/excel
# - POST /api/nfse/certificado/upload
# - GET  /api/nfse/certificado
# 
# Motivo: Essas operações são leves e devem ficar no ERP principal.
# Este microserviço foca APENAS em buscas pesadas (Ambiente Nacional, SOAP, SEFAZ).


# ==================== NF-E (PLACEHOLDER) ====================
def listar_provedores():
    """Lista provedores NFS-e disponíveis"""
    from nfse_service import PROVEDORES_NFSE
    
    provedores = [
        {
            'codigo': codigo,
            'nome': info['nome'],
            'padrao_abrasf': info['padrao_abrasf'],
            'municipios_estimados': info.get('municipios_estimados', 'N/A')
        }
        for codigo, info in PROVEDORES_NFSE.items()
    ]
    
    return jsonify({
        'success': True,
        'provedores': provedores
    })


# ==================== NF-E (PLACEHOLDER) ====================

@app.route('/api/nfe/buscar', methods=['POST'])
@require_auth
def buscar_nfe():
    """
    🔥 BUSCA PESADA DE NF-e
    TODO: Implementar busca via SEFAZ/inutilizacao/consulta
    """
    return jsonify({
        'success': False,
        'error': 'Funcionalidade em desenvolvimento'
    }), 501


# ==================== CT-E (PLACEHOLDER) ====================

@app.route('/api/cte/buscar', methods=['POST'])
@require_auth
def buscar_cte():
    """
    🔥 BUSCA PESADA DE CT-e
    TODO: Implementar busca via SEFAZ
    """
    return jsonify({
        'success': False,
        'error': 'Funcionalidade em desenvolvimento'
    }), 501


@app.route('/api/nfse/testar-conexao', methods=['POST'])
@require_auth
def testar_conexao_municipio():
    """Testa conexão com webservice do município"""
    try:
        data = request.json
        
        codigo_municipio = data.get('codigo_municipio')
        provedor = data.get('provedor')
        url_webservice = data.get('url_webservice')
        
        if not all([codigo_municipio, provedor]):
            return jsonify({'error': 'Parâmetros incompletos'}), 400
        
        resultado = testar_conexao(
            codigo_municipio=codigo_municipio,
            provedor=provedor,
            url_webservice=url_webservice
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    logger.info(f"🚀 Iniciando serviço NFS-e na porta {port}")
    logger.info(f"📊 Ambiente: {'PRODUÇÃO' if not debug else 'DESENVOLVIMENTO'}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
