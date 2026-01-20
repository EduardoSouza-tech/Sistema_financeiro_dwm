"""
Pagination helper - Sistema de paginação para endpoints
"""

from flask import request, jsonify
from typing import Tuple, Dict, Any, List


def paginate_query(query_func, page=None, per_page=None, max_per_page=100):
    """
    Aplica paginação a uma query
    
    Args:
        query_func: Função que executa a query e retorna (items, total_count)
        page: Número da página (começa em 1)
        per_page: Items por página
        max_per_page: Máximo de items por página permitidos
        
    Returns:
        dict com items, pagination info
        
    Exemplo:
        def get_items(offset, limit):
            cursor.execute("SELECT * FROM items LIMIT %s OFFSET %s", (limit, offset))
            items = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) FROM items")
            total = cursor.fetchone()[0]
            return items, total
            
        result = paginate_query(get_items, page=1, per_page=20)
    """
    # Obter parâmetros da request se não fornecidos
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 50, type=int)
    
    # Validações
    page = max(1, page)  # Mínimo página 1
    per_page = min(max(1, per_page), max_per_page)  # Entre 1 e max_per_page
    
    # Calcular offset
    offset = (page - 1) * per_page
    
    # Executar query
    items, total_count = query_func(offset, per_page)
    
    # Calcular metadados de paginação
    total_pages = (total_count + per_page - 1) // per_page  # Arredonda para cima
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'next_page': page + 1 if has_next else None,
            'prev_page': page - 1 if has_prev else None
        }
    }


def get_pagination_params(default_per_page=50, max_per_page=100):
    """
    Extrai parâmetros de paginação da request
    
    Returns:
        tuple: (page, per_page, offset, limit)
        
    Exemplo:
        page, per_page, offset, limit = get_pagination_params()
        cursor.execute("SELECT * FROM items LIMIT %s OFFSET %s", (limit, offset))
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', default_per_page, type=int)
    
    # Validações
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    
    offset = (page - 1) * per_page
    limit = per_page
    
    return page, per_page, offset, limit


def build_pagination_response(items: List[Any], total_count: int, page: int, per_page: int) -> Dict:
    """
    Constrói resposta com paginação
    
    Args:
        items: Lista de items da página atual
        total_count: Total de items (todas as páginas)
        page: Número da página atual
        per_page: Items por página
        
    Returns:
        dict com items e metadata de paginação
    """
    total_pages = (total_count + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        'success': True,
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'next_page': page + 1 if has_next else None,
            'prev_page': page - 1 if has_prev else None
        }
    }


def get_sort_params(allowed_fields, default_field='id', default_order='asc'):
    """
    Extrai parâmetros de ordenação da request
    
    Args:
        allowed_fields: Lista de campos permitidos para ordenação
        default_field: Campo padrão se não especificado
        default_order: Ordem padrão ('asc' ou 'desc')
        
    Returns:
        tuple: (sort_field, sort_order)
        
    Exemplo:
        sort_field, sort_order = get_sort_params(['nome', 'data', 'valor'])
        # ?sort_by=nome&order=desc
    """
    sort_field = request.args.get('sort_by', default_field)
    sort_order = request.args.get('order', default_order).lower()
    
    # Validações
    if sort_field not in allowed_fields:
        sort_field = default_field
    
    if sort_order not in ['asc', 'desc']:
        sort_order = default_order
    
    return sort_field, sort_order


def get_filter_params(allowed_filters):
    """
    Extrai parâmetros de filtro da request
    
    Args:
        allowed_filters: Dict com filtros permitidos e suas validações
        
    Returns:
        dict com filtros aplicados
        
    Exemplo:
        filters = get_filter_params({
            'status': ['ativo', 'inativo'],
            'tipo': ['receita', 'despesa'],
            'data_inicio': 'date',
            'data_fim': 'date'
        })
    """
    filters = {}
    
    for param, validation in allowed_filters.items():
        value = request.args.get(param)
        
        if value is not None:
            # Validar valor
            if isinstance(validation, list):
                # Lista de valores permitidos
                if value in validation:
                    filters[param] = value
            elif validation == 'date':
                # Validação de data
                filters[param] = value  # TODO: Validar formato de data
            elif validation == 'int':
                # Validação de inteiro
                try:
                    filters[param] = int(value)
                except ValueError:
                    pass
            elif validation == 'float':
                # Validação de float
                try:
                    filters[param] = float(value)
                except ValueError:
                    pass
            else:
                # Sem validação, aceitar como está
                filters[param] = value
    
    return filters


# Exemplo de uso completo:
"""
from app.utils.pagination_helper import paginate_query, get_pagination_params, build_pagination_response

@app.route('/api/items')
def get_items():
    page, per_page, offset, limit = get_pagination_params(default_per_page=20)
    
    # Query com paginação
    cursor.execute(
        "SELECT * FROM items ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset)
    )
    items = cursor.fetchall()
    
    # Contar total
    cursor.execute("SELECT COUNT(*) FROM items")
    total_count = cursor.fetchone()[0]
    
    # Construir resposta
    return jsonify(build_pagination_response(items, total_count, page, per_page))
"""
