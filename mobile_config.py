"""
Detecção Simples de Dispositivos Mobile para Web Responsiva
"""
from flask import request
import re

# ============================================================================
# DETECÇÃO DE DISPOSITIVOS MOBILE
# ============================================================================

# Regex para detectar User-Agents mobile comuns
MOBILE_USER_AGENTS = [
    r'Android',
    r'webOS',
    r'iPhone',
    r'iPad',
    r'iPod',
    r'BlackBerry',
    r'IEMobile',
    r'Opera Mini',
    r'Mobile',
    r'mobile',
    r'CriOS'  # Chrome no iOS
]

MOBILE_PATTERN = re.compile('|'.join(MOBILE_USER_AGENTS), re.IGNORECASE)


def is_mobile_device():
    """
    Detecta se a requisição vem de um dispositivo mobile
    
    Returns:
        bool: True se for mobile, False caso contrário
    """
    user_agent = request.headers.get('User-Agent', '')
    
    # Verificar User-Agent
    if MOBILE_PATTERN.search(user_agent):
        return True
    
    # Verificar header específico (alguns apps mobile podem enviar)
    if request.headers.get('X-Mobile-App'):
        return True
    
    return False


def is_mobile_app():
    """
    Detecta se a requisição vem de um navegador mobile
    
    Returns:
        bool: True se for mobile, False caso contrário
    """
    return is_mobile_device()


def get_device_info():
    """
    Retorna informações detalhadas sobre o dispositivo
    
    Returns:
        dict: Informações do dispositivo
    """
    user_agent = request.headers.get('User-Agent', '')
    
    device_info = {
        'is_mobile': is_mobile_device(),
        'user_agent': user_agent,
        'platform': None,
        'os': None,
        'browser': None
    }
    
    # Detectar plataforma
    if 'Android' in user_agent:
        device_info['platform'] = 'android'
        device_info['os'] = 'Android'
    elif any(x in user_agent for x in ['iPhone', 'iPad', 'iPod']):
        device_info['platform'] = 'ios'
        device_info['os'] = 'iOS'
    elif 'Windows' in user_agent:
        device_info['os'] = 'Windows'
    elif 'Mac' in user_agent:
        device_info['os'] = 'macOS'
    elif 'Linux' in user_agent:
        device_info['os'] = 'Linux'
    
    # Detectar browser
    if 'Chrome' in user_agent and 'Safari' in user_agent:
        device_info['browser'] = 'Chrome'
    elif 'Safari' in user_agent:
        device_info['browser'] = 'Safari'
    elif 'Firefox' in user_agent:
        device_info['browser'] = 'Firefox'
    elif 'Edge' in user_agent:
        device_info['browser'] = 'Edge'
    
    return device_info


# ============================================================================
# UTILITÁRIOS SIMPLES
# ============================================================================

def get_viewport_meta():
    """
    Retorna meta tag viewport para páginas mobile-friendly
    
    Returns:
        str: Meta tag HTML
    """
    return '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'


def add_mobile_class():
    """
    Retorna classe CSS para body em dispositivos mobile
    
    Returns:
        str: Classe CSS 'mobile' ou ''
    """
    return 'mobile' if is_mobile_device() else ''
