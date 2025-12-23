"""
Script para testar todos os endpoints do Menu Operacional
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def testar_endpoint(metodo, url, dados=None):
    """Testa um endpoint e exibe o resultado"""
    try:
        if metodo == "GET":
            response = requests.get(url)
        elif metodo == "POST":
            response = requests.post(url, json=dados)
        elif metodo == "PUT":
            response = requests.put(url, json=dados)
        elif metodo == "DELETE":
            response = requests.delete(url)
        
        print(f"✓ {metodo} {url.replace(BASE_URL, '')}")
        print(f"  Status: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            if isinstance(data, list):
                print(f"  Resultado: {len(data)} registros")
            else:
                print(f"  Resultado: {data}")
        else:
            print(f"  Erro: {response.text}")
        print()
        return response.json() if response.status_code in [200, 201] else None
    except Exception as e:
        print(f"✗ {metodo} {url.replace(BASE_URL, '')}")
        print(f"  Erro: {str(e)}")
        print()
        return None

def main():
    print("="*70)
    print("TESTE DO MENU OPERACIONAL - TODOS OS ENDPOINTS")
    print("="*70)
    print()
    
    # === CONTRATOS ===
    print("📋 TESTANDO CONTRATOS")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/contratos")
    
    contrato_data = {
        "numero": "CONT-001",
        "descricao": "Contrato de teste",
        "valor": 5000.00,
        "data_inicio": "2025-01-01",
        "status": "ativo"
    }
    contrato = testar_endpoint("POST", f"{BASE_URL}/api/contratos", contrato_data)
    
    if contrato and 'id' in contrato:
        contrato_id = contrato['id']
        contrato_data['descricao'] = "Contrato atualizado"
        testar_endpoint("PUT", f"{BASE_URL}/api/contratos/{contrato_id}", contrato_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/contratos/{contrato_id}")
    
    # === SESSÕES ===
    print("🎬 TESTANDO SESSÕES")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/sessoes")
    
    sessao_data = {
        "titulo": "Sessão de teste",
        "data_sessao": "2025-01-15",
        "duracao": 120,
        "valor": 300.00,
        "status": "agendada"
    }
    sessao = testar_endpoint("POST", f"{BASE_URL}/api/sessoes", sessao_data)
    
    if sessao and 'id' in sessao:
        sessao_id = sessao['id']
        sessao_data['titulo'] = "Sessão atualizada"
        testar_endpoint("PUT", f"{BASE_URL}/api/sessoes/{sessao_id}", sessao_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/sessoes/{sessao_id}")
    
    # === COMISSÕES ===
    print("💰 TESTANDO COMISSÕES")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/comissoes")
    
    comissao_data = {
        "descricao": "Comissão de teste",
        "valor": 150.00,
        "percentual": 10.0,
        "data_referencia": "2025-01-01",
        "status": "pendente",
        "beneficiario": "João Silva"
    }
    comissao = testar_endpoint("POST", f"{BASE_URL}/api/comissoes", comissao_data)
    
    if comissao and 'id' in comissao:
        comissao_id = comissao['id']
        comissao_data['status'] = "pago"
        testar_endpoint("PUT", f"{BASE_URL}/api/comissoes/{comissao_id}", comissao_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/comissoes/{comissao_id}")
    
    # === SESSÃO-EQUIPE ===
    print("👥 TESTANDO SESSÃO-EQUIPE")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/sessao-equipe")
    
    # === AGENDA ===
    print("📅 TESTANDO AGENDA")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/agenda")
    
    agenda_data = {
        "titulo": "Reunião de teste",
        "data_evento": "2025-01-20",
        "hora_inicio": "14:00",
        "hora_fim": "16:00",
        "tipo": "reuniao",
        "status": "agendado"
    }
    agenda = testar_endpoint("POST", f"{BASE_URL}/api/agenda", agenda_data)
    
    if agenda and 'id' in agenda:
        agenda_id = agenda['id']
        agenda_data['titulo'] = "Reunião atualizada"
        testar_endpoint("PUT", f"{BASE_URL}/api/agenda/{agenda_id}", agenda_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/agenda/{agenda_id}")
    
    # === PRODUTOS ===
    print("📦 TESTANDO PRODUTOS")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/estoque/produtos")
    
    produto_data = {
        "codigo": "PROD-001",
        "nome": "Produto de teste",
        "categoria": "Material",
        "unidade": "un",
        "quantidade": 10,
        "quantidade_minima": 5,
        "preco_custo": 50.00,
        "preco_venda": 100.00,
        "ativo": 1
    }
    produto = testar_endpoint("POST", f"{BASE_URL}/api/estoque/produtos", produto_data)
    
    if produto and 'id' in produto:
        produto_id = produto['id']
        produto_data['quantidade'] = 20
        testar_endpoint("PUT", f"{BASE_URL}/api/estoque/produtos/{produto_id}", produto_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/estoque/produtos/{produto_id}")
    
    # === KITS ===
    print("🎒 TESTANDO KITS")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/kits")
    
    kit_data = {
        "codigo": "KIT-001",
        "nome": "Kit de teste",
        "descricao": "Kit com vários itens",
        "preco": 500.00,
        "ativo": 1,
        "itens": []
    }
    kit = testar_endpoint("POST", f"{BASE_URL}/api/kits", kit_data)
    
    if kit and 'id' in kit:
        kit_id = kit['id']
        kit_data['preco'] = 550.00
        testar_endpoint("PUT", f"{BASE_URL}/api/kits/{kit_id}", kit_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/kits/{kit_id}")
    
    # === TAGS ===
    print("🏷️  TESTANDO TAGS")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/tags")
    
    tag_data = {
        "nome": "Tag de teste",
        "cor": "#ff5733",
        "descricao": "Descrição da tag"
    }
    tag = testar_endpoint("POST", f"{BASE_URL}/api/tags", tag_data)
    
    if tag and 'id' in tag:
        tag_id = tag['id']
        tag_data['cor'] = "#33ff57"
        testar_endpoint("PUT", f"{BASE_URL}/api/tags/{tag_id}", tag_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/tags/{tag_id}")
    
    # === TEMPLATES ===
    print("📝 TESTANDO TEMPLATES DE EQUIPE")
    print("-"*70)
    testar_endpoint("GET", f"{BASE_URL}/api/templates-equipe")
    
    template_data = {
        "nome": "Template de teste",
        "descricao": "Template para equipe",
        "conteudo": "Conteúdo do template",
        "tipo": "geral",
        "ativo": 1
    }
    template = testar_endpoint("POST", f"{BASE_URL}/api/templates-equipe", template_data)
    
    if template and 'id' in template:
        template_id = template['id']
        template_data['conteudo'] = "Conteúdo atualizado"
        testar_endpoint("PUT", f"{BASE_URL}/api/templates-equipe/{template_id}", template_data)
        testar_endpoint("DELETE", f"{BASE_URL}/api/templates-equipe/{template_id}")
    
    print("="*70)
    print("✅ TODOS OS TESTES CONCLUÍDOS!")
    print("="*70)

if __name__ == "__main__":
    main()
