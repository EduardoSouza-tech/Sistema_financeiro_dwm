"""
Teste REAL com ofxparse para verificar como ele retorna datas com timezone
"""

# Criar arquivo OFX de teste
ofx_content = """<?xml version="1.0" encoding="UTF-8"?>
<OFX>
    <SIGNONMSGSRSV1>
        <SONRS>
            <STATUS>
                <CODE>0</CODE>
                <SEVERITY>INFO</SEVERITY>
            </STATUS>
            <DTSERVER>20260224120000[-3:GMT]</DTSERVER>
            <LANGUAGE>POR</LANGUAGE>
        </SONRS>
    </SIGNONMSGSRSV1>
    <BANKMSGSRSV1>
        <STMTTRNRS>
            <TRNUID>1</TRNUID>
            <STATUS>
                <CODE>0</CODE>
                <SEVERITY>INFO</SEVERITY>
            </STATUS>
            <STMTRS>
                <CURDEF>BRL</CURDEF>
                <BANKACCTFROM>
                    <BANKID>001</BANKID>
                    <ACCTID>12345</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
                <BANKTRANLIST>
                    <DTSTART>20260201000000[-3:GMT]</DTSTART>
                    <DTEND>20260228000000[-3:GMT]</DTEND>
                    <STMTTRN>
                        <TRNTYPE>CREDIT</TRNTYPE>
                        <DTPOSTED>20260223000000[-3:GMT]</DTPOSTED>
                        <TRNAMT>5279.00</TRNAMT>
                        <FITID>21230742427</FITID>
                        <REFNUM>21230742427</REFNUM>
                        <MEMO>RECEBIMENTO PIX-PIX_CRED  35696831000124 CAIO J H TENORIO</MEMO>
                    </STMTTRN>
                </BANKTRANLIST>
                <LEDGERBAL>
                    <BALAMT>10000.00</BALAMT>
                    <DTASOF>20260224120000[-3:GMT]</DTASOF>
                </LEDGERBAL>
            </STMTRS>
        </STMTTRNRS>
    </BANKMSGSRSV1>
</OFX>"""

import os
import io
from datetime import datetime, timezone, timedelta

print("="*80)
print("TESTE REAL COM OFXPARSE")
print("="*80)
print()

# Salvar arquivo temporário
test_file_path = "test_ofx_timezone.ofx"
with open(test_file_path, 'w', encoding='utf-8') as f:
    f.write(ofx_content)

print(f"1. Arquivo OFX criado: {test_file_path}")
print()

try:
    import ofxparse
    
    # Parse do arquivo
    with open(test_file_path, 'rb') as f:
        ofx = ofxparse.OfxParser.parse(f)
    
    print("2. RESULTADO DO PARSE:")
    print()
    
    for account in ofx.accounts:
        print(f"   Conta: {account.account_id}")
        print(f"   Número de transações: {len(account.statement.transactions)}")
        print()
        
        for trans in account.statement.transactions:
            print(f"3. TRANSAÇÃO DO OFX:")
            print(f"   Descrição: {trans.memo}")
            print(f"   Valor: {trans.amount}")
            print()
            
            print(f"4. ANÁLISE DA DATA (trans.date):")
            print(f"   Tipo: {type(trans.date)}")
            print(f"   Valor: {trans.date}")
            print(f"   repr(): {repr(trans.date)}")
            print()
            
            if hasattr(trans.date, 'tzinfo'):
                print(f"   tzinfo: {trans.date.tzinfo}")
                print(f"   É timezone-aware: {trans.date.tzinfo is not None}")
                print()
            
            # O que o código atual faz
            print(f"5. CÓDIGO ATUAL (trans.date.date()):")
            if hasattr(trans.date, 'date'):
                result_current = trans.date.date()
                print(f"   Resultado: {result_current}")
                print(f"   Formatado: {result_current.strftime('%d/%m/%Y')}")
                print(f"   ❌ MOSTRA: 22/02/2026 (ERRADO!)" if result_current.day == 22 else f"   ✅ MOSTRA: {result_current.day}/02/2026")
            print()
            
            # Solução 1: converter para timezone Brasil antes de .date()
            print(f"6. SOLUÇÃO 1 (converter para GMT-3 antes de .date()):")
            if hasattr(trans.date, 'astimezone'):
                tz_brasil = timezone(timedelta(hours=-3))
                dt_brasil = trans.date.astimezone(tz_brasil)
                result_solution1 = dt_brasil.date()
                print(f"   datetime em GMT-3: {dt_brasil}")
                print(f"   .date(): {result_solution1}")
                print(f"   Formatado: {result_solution1.strftime('%d/%m/%Y')}")
                print(f"   ✅ CORRETO!" if result_solution1.day == 23 else f"   ❌ ERRO")
            print()
            
            # Solução 2: usar apenas a string da data (ignorar hora/timezone)
            print(f"7. SOLUÇÃO 2 (extrair ano/mês/dia direto):")
            if hasattr(trans.date, 'year'):
                from datetime import date
                result_solution2 = date(trans.date.year, trans.date.month, trans.date.day)
                print(f"   date(year={trans.date.year}, month={trans.date.month}, day={trans.date.day})")
                print(f"   Resultado: {result_solution2}")
                print(f"   Formatado: {result_solution2.strftime('%d/%m/%Y')}")
                print(f"   ✅ CORRETO!" if result_solution2.day == 23 else f"   ❌ ERRO")
            print()
    
except ImportError:
    print("❌ ERRO: ofxparse não está instalado!")
    print("   Instale com: pip install ofxparse")
except Exception as e:
    print(f"❌ ERRO ao processar OFX: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Limpar arquivo de teste
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
        print(f"\n8. Arquivo de teste removido: {test_file_path}")

print()
print("="*80)
print("CONCLUSÃO:")
print("="*80)
print()
print("Se o teste mostrou 22/02 com código atual e 23/02 com solução,")
print("então o bug está confirmado e precisa ser corrigido!")
print()
