"""
Chama o endpoint da API para remover duplicatas [EXTRATO]
Usa a sessão autenticada do usuário
"""
import requests
import json

def limpar_duplicatas_via_api():
    """Chama endpoint admin para limpar duplicatas"""
    
    # URL da API no Railway
    api_url = "https://sistemafinanceirodwm-production.up.railway.app"
    endpoint = f"{api_url}/api/admin/limpar-duplicatas-extrato"
    
    print("="*80)
    print("🧹 LIMPANDO DUPLICATAS VIA API")
    print("="*80)
    print(f"\n📡 Endpoint: {endpoint}")
    
    # Nota: Você precisa estar autenticado como admin
    # O script pressupõe que você tem uma sessão ativa no navegador
    print("\n⚠️  IMPORTANTE:")
    print("   1. Abra o navegador")
    print("   2. Faça login como ADMIN no sistema")
    print("   3. Abra o Console do navegador (F12)")
    print("   4. Execute o seguinte código:\n")
    
    javascript_code = """
// Copie e cole este código no Console do navegador (F12)
fetch('""" + endpoint + """', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    credentials: 'include'  // Importante: inclui cookies da sessão
})
.then(response => response.json())
.then(data => {
    console.log('✅ RESPOSTA DA API:', data);
    
    if (data.success) {
        console.log('\\n' + '='.repeat(80));
        console.log('🎉 DUPLICATAS REMOVIDAS COM SUCESSO!');
        console.log('='.repeat(80));
        console.log(`📊 Total antes: ${data.total_antes?.toLocaleString()}`);
        console.log(`📊 Total depois: ${data.total_depois?.toLocaleString()}`);
        console.log(`🗑️  Removidos: ${data.removidas?.toLocaleString()} duplicatas`);
        
        if (data.saldo) {
            console.log(`\\n💰 SALDO ATUALIZADO:`);
            console.log(`   Banco: ${data.saldo.banco}`);
            console.log(`   Agência/Conta: ${data.saldo.agencia}/${data.saldo.conta}`);
            console.log(`   Saldo: R$ ${data.saldo.saldo_atual?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`);
        }
        
        console.log(`\\n💾 Backup salvo em: ${data.backup_table}`);
        console.log('\\n🔄 Recarregue a página para ver os dados atualizados!');
    } else {
        console.error('❌ ERRO:', data.error || data.message);
    }
})
.catch(error => {
    console.error('❌ Erro na requisição:', error);
});
"""
    
    print(javascript_code)
    print("\n" + "="*80)
    print("📋 INSTRUÇÕES:")
    print("="*80)
    print("1. Copie TODO o código acima (incluindo fetch e o bloco completo)")
    print("2. Abra o sistema no navegador")
    print("3. Faça login como ADMIN")
    print("4. Pressione F12 para abrir o Console")
    print("5. Cole o código no Console e pressione Enter")
    print("6. Aguarde a resposta")
    print("7. Recarregue a página para ver os dados atualizados")
    print("="*80)
    
    # Alternativa: criar arquivo HTML
    html_file = "limpar_duplicatas.html"
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Limpar Duplicatas [EXTRATO]</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        button {{
            background: #dc3545;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 20px;
        }}
        button:hover {{
            background: #c82333;
        }}
        button:disabled {{
            background: #6c757d;
            cursor: not-allowed;
        }}
        #resultado {{
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
        }}
        .success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
        .error {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }}
        .info {{
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧹 Limpar Duplicatas [EXTRATO]</h1>
        
        <div class="warning">
            <strong>⚠️ IMPORTANTE:</strong>
            <ul>
                <li>Você deve estar autenticado como <strong>ADMIN</strong></li>
                <li>Esta ação irá remover lançamentos duplicados</li>
                <li>Um backup será criado antes da remoção</li>
                <li>O processo é irreversível (mas pode ser restaurado do backup)</li>
            </ul>
        </div>
        
        <button id="btnLimpar" onclick="limparDuplicatas()">
            🗑️ Remover Duplicatas [EXTRATO]
        </button>
        
        <div id="resultado"></div>
    </div>
    
    <script>
        async function limparDuplicatas() {{
            const btn = document.getElementById('btnLimpar');
            const resultado = document.getElementById('resultado');
            
            btn.disabled = true;
            btn.textContent = '⏳ Processando...';
            resultado.innerHTML = '';
            resultado.className = '';
            
            try {{
                const response = await fetch('{endpoint}', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    credentials: 'include'
                }});
                
                const data = await response.json();
                
                if (data.success) {{
                    let msg = '✅ DUPLICATAS REMOVIDAS COM SUCESSO!\\n\\n';
                    msg += '═'.repeat(60) + '\\n';
                    msg += `📊 Total antes: ${{data.total_antes?.toLocaleString()}} lançamentos\\n`;
                    msg += `📊 Total depois: ${{data.total_depois?.toLocaleString()}} lançamentos\\n`;
                    msg += `🗑️  Removidos: ${{data.removidas?.toLocaleString()}} duplicatas\\n`;
                    
                    if (data.saldo) {{
                        msg += '\\n💰 SALDO ATUALIZADO:\\n';
                        msg += `   Banco: ${{data.saldo.banco}}\\n`;
                        msg += `   Agência/Conta: ${{data.saldo.agencia}}/${{data.saldo.conta}}\\n`;
                        msg += `   Saldo: R$ ${{data.saldo.saldo_atual?.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}\\n`;
                    }}
                    
                    msg += `\\n💾 Backup: ${{data.backup_table}}\\n`;
                    msg += '\\n🔄 Recarregue a página para ver os dados atualizados!';
                    
                    resultado.textContent = msg;
                    resultado.className = 'success';
                    
                    // Recarregar após 3 segundos
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 3000);
                    
                }} else {{
                    resultado.textContent = '❌ ERRO: ' + (data.error || data.message);
                    resultado.className = 'error';
                    btn.disabled = false;
                    btn.textContent = '🗑️ Remover Duplicatas [EXTRATO]';
                }}
                
            }} catch (error) {{
                resultado.textContent = '❌ Erro na requisição: ' + error.message;
                resultado.className = 'error';
                btn.disabled = false;
                btn.textContent = '🗑️ Remover Duplicatas [EXTRATO]';
            }}
        }}
    </script>
</body>
</html>
"""
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 Arquivo HTML criado: {html_file}")
    print(f"   Abra este arquivo no navegador após fazer login como admin!")

if __name__ == "__main__":
    limpar_duplicatas_via_api()
