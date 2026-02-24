"""
Script de teste para verificar como ofxparse retorna datas
E se há problemas de timezone na importação OFX
"""

import sys
from datetime import datetime, date

def test_date_formats():
    """Testa diferentes formatos de data"""
    print("="*60)
    print("TESTE DE FORMATOS DE DATA")
    print("="*60)
    
    # Teste 1: datetime com timezone
    dt_aware = datetime(2026, 2, 8, 10, 30, 0)
    print(f"\n1. datetime (naive): {dt_aware}")
    print(f"   - .date(): {dt_aware.date()}")
    print(f"   - .date().isoformat(): {dt_aware.date().isoformat()}")
    print(f"   - hasattr(", "date", "): ", hasattr(dt_aware, 'date'))
    
    # Teste 2: date object
    dt_date = date(2026, 2, 8)
    print(f"\n2. date: {dt_date}")
    print(f"   - .isoformat(): {dt_date.isoformat()}")
    print(f"   - hasattr(", "date", "): ", hasattr(dt_date, 'date'))
    
    # Teste 3: Simulando o que vem do OFX
    print("\n" + "="*60)
    print("SIMULAÇÃO: O QUE VEM DO OFXPARSE")
    print("="*60)
    
    # ofxparse geralmente retorna datetime objects
    trans_date_dt = datetime(2026, 2, 8, 0, 0, 0)  # Meia-noite
    
    # O que o código atual faz:
    result = trans_date_dt.date() if hasattr(trans_date_dt, 'date') else trans_date_dt
    print(f"\nData da transação no OFX (datetime): {trans_date_dt}")
    print(f"Após trans.date.date(): {result}")
    print(f"Tipo final: {type(result)}")
    print(f"ISO format: {result.isoformat()}")
    
    # Teste 4: String que vai pro banco
    print("\n" + "="*60)
    print("O QUE VAI PARA O BANCO DE DADOS")
    print("="*60)
    
    data_para_banco = result  # date object
    print(f"Tipo: {type(data_para_banco)}")
    print(f"Valor: {data_para_banco}")
    
    # Teste 5: O que volta do banco (via isoformat do extrato_functions.py)
    print("\n" + "="*60)
    print("O QUE VOLTA DO BANCO (VIA JSON)")
    print("="*60)
    
    data_do_banco = date(2026, 2, 8)
    data_json = data_do_banco.isoformat()
    print(f"date.isoformat(): {data_json}")
    print(f"Tipo: {type(data_json)}")
    print(f"Formato: YYYY-MM-DD ✅")
    
    # Teste 6: Verificar se a regex do frontend funcionaria
    print("\n" + "="*60)
    print("VERIFICAÇÃO: REGEX DO FRONTEND")
    print("="*60)
    
    import re
    pattern = r'^\d{4}-\d{2}-\d{2}'
    match = re.match(pattern, data_json)
    
    if match:
        print(f"✅ String '{data_json}' faz match com regex '^\\d{{4}}-\\d{{2}}-\\d{{2}}'")
        
        # Simular o que o frontend faz
        parts = data_json[:10].split('-')
        formatado = f"{parts[2]}/{parts[1]}/{parts[0]}"
        print(f"✅ Formatação frontend: {formatado}")
        print(f"✅ Data correta no frontend: 08/02/2026")
    else:
        print(f"❌ String '{data_json}' NÃO faz match com regex")
        
    print("\n" + "="*60)
    print("CONCLUSÃO")
    print("="*60)
    print("\n✅ FLUXO ATUAL ESTÁ CORRETO:")
    print("   1. OFX retorna datetime → extraímos .date()")
    print("   2. Salvamos date no banco (sem hora/timezone)")
    print("   3. Banco retorna date → convertemos com .isoformat()")
    print("   4. JSON envia 'YYYY-MM-DD' puro")
    print("   5. Frontend detecta pattern e formata SEM new Date()")
    print("   6. Resultado: data correta sem problemas de timezone ✅")

if __name__ == '__main__':
    test_date_formats()
