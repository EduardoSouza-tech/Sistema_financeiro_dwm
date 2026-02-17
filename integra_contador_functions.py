"""
Módulo Integra Contador - API SERPRO
Funções para integração com a API Integra Contador do SERPRO
"""

import requests
import json
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Credenciais da API
CONSUMER_KEY = "K8VXrizTyJpB9mL0D1kE8TfvdXUa"
CONSUMER_SECRET = "f9lpZ_R2Ht1XIIlIBNf_7fRzpRsa"
BASE_URL = "https://gateway.apiserpro.serpro.gov.br/integra-contador/v1"
TOKEN_URL = "https://gateway.apiserpro.serpro.gov.br/integra-contador/v1/token"

# Cache do token
_token_cache = {
    'token': None,
    'expires_at': None
}


def obter_token():
    """
    Obtém token de acesso Bearer para a API do SERPRO.
    Implementa cache do token para evitar requisições desnecessárias.
    """
    try:
        # Verificar se há token em cache válido
        if _token_cache['token'] and _token_cache['expires_at']:
            if datetime.now() < _token_cache['expires_at']:
                logger.info("Usando token em cache")
                return _token_cache['token']
        
        # Gerar novo token
        auth_string = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            raise Exception("Token não retornado pela API")
        
        # Calcular expiração (normalmente 3600 segundos - 1 hora)
        expires_in = token_data.get('expires_in', 3600)
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # -60s de margem
        
        # Atualizar cache
        _token_cache['token'] = access_token
        _token_cache['expires_at'] = expires_at
        
        logger.info(f"Novo token obtido, expira em {expires_in}s")
        return access_token
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao obter token: {str(e)}")
        raise Exception(f"Erro ao obter token de acesso: {str(e)}")
    except Exception as e:
        logger.error(f"Erro inesperado ao obter token: {str(e)}")
        raise


def enviar_requisicao(tipo_operacao, payload):
    """
    Envia requisição para a API Integra Contador.
    
    Args:
        tipo_operacao: Tipo de operação (Apoiar, Consultar, Declarar, Emitir, Monitorar)
        payload: Dicionário com os dados da requisição
    
    Returns:
        Dicionário com a resposta da API
    """
    try:
        # Validar tipo de operação
        tipos_validos = ['Apoiar', 'Consultar', 'Declarar', 'Emitir', 'Monitorar']
        if tipo_operacao not in tipos_validos:
            raise ValueError(f"Tipo de operação inválido: {tipo_operacao}")
        
        # Obter token
        token = obter_token()
        
        # Construir URL
        url = f"{BASE_URL}/{tipo_operacao}"
        
        # Preparar headers
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Validar e preparar payload
        if not isinstance(payload, dict):
            raise ValueError("Payload deve ser um dicionário")
        
        # Escapar o campo 'dados' se necessário
        if 'pedidoDados' in payload and 'dados' in payload['pedidoDados']:
            dados = payload['pedidoDados']['dados']
            # Se dados é um dict, converter para JSON escaped string
            if isinstance(dados, dict):
                payload['pedidoDados']['dados'] = json.dumps(dados, ensure_ascii=False)
        
        # Enviar requisição
        logger.info(f"Enviando requisição para {tipo_operacao}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        # Log da resposta
        logger.info(f"Status Code: {response.status_code}")
        logger.debug(f"Response: {response.text}")
        
        # Tentar parsear como JSON
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {
                'raw_response': response.text,
                'status_code': response.status_code
            }
        
        # Verificar se houve erro
        if response.status_code >= 400:
            error_msg = response_data.get('message', response_data.get('error', 'Erro desconhecido'))
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code,
                'response': response_data
            }
        
        return {
            'success': True,
            'data': response_data,
            'status_code': response.status_code
        }
        
    except ValueError as e:
        logger.error(f"Erro de validação: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    except requests.exceptions.Timeout:
        logger.error("Timeout na requisição")
        return {
            'success': False,
            'error': 'Tempo de requisição excedido (timeout)'
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {str(e)}")
        return {
            'success': False,
            'error': f'Erro na comunicação com a API: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return {
            'success': False,
            'error': f'Erro inesperado: {str(e)}'
        }


def validar_payload(payload):
    """
    Valida estrutura do payload antes de enviar.
    
    Args:
        payload: Dicionário com os dados a validar
    
    Returns:
        Tupla (bool, str) - (válido, mensagem_erro)
    """
    required_fields = ['contratante', 'autorPedidoDados', 'contribuinte', 'pedidoDados']
    
    for field in required_fields:
        if field not in payload:
            return False, f"Campo obrigatório ausente: {field}"
    
    # Validar contratante
    if 'numero' not in payload['contratante'] or 'tipo' not in payload['contratante']:
        return False, "Contratante incompleto: faltam 'numero' ou 'tipo'"
    
    if len(payload['contratante']['numero']) != 14:
        return False, "CNPJ do contratante deve ter 14 dígitos"
    
    # Validar autorPedidoDados
    if 'numero' not in payload['autorPedidoDados'] or 'tipo' not in payload['autorPedidoDados']:
        return False, "Autor do pedido incompleto: faltam 'numero' ou 'tipo'"
    
    autor_tipo = int(payload['autorPedidoDados']['tipo'])
    autor_numero = payload['autorPedidoDados']['numero']
    if autor_tipo == 1 and len(autor_numero) != 11:
        return False, "CPF do autor deve ter 11 dígitos"
    if autor_tipo == 2 and len(autor_numero) != 14:
        return False, "CNPJ do autor deve ter 14 dígitos"
    
    # Validar contribuinte
    if 'numero' not in payload['contribuinte'] or 'tipo' not in payload['contribuinte']:
        return False, "Contribuinte incompleto: faltam 'numero' ou 'tipo'"
    
    contrib_tipo = int(payload['contribuinte']['tipo'])
    contrib_numero = payload['contribuinte']['numero']
    if contrib_tipo == 1 and len(contrib_numero) != 11:
        return False, "CPF do contribuinte deve ter 11 dígitos"
    if contrib_tipo == 2 and len(contrib_numero) != 14:
        return False, "CNPJ do contribuinte deve ter 14 dígitos"
    
    # Validar pedidoDados
    pedido_fields = ['idSistema', 'idServico', 'versaoSistema', 'dados']
    for field in pedido_fields:
        if field not in payload['pedidoDados']:
            return False, f"Campo obrigatório no pedidoDados: {field}"
    
    return True, "Payload válido"


def testar_conexao():
    """
    Testa a conexão com a API obtendo um token.
    
    Returns:
        Dicionário com o resultado do teste
    """
    try:
        token = obter_token()
        return {
            'success': True,
            'message': 'Conexão com API estabelecida com sucesso',
            'token_preview': f"{token[:20]}..."
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
