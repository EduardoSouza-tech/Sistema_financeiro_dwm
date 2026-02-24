"""
Teste para verificar como ofxparse lida com timezone
Data do OFX: 20260223000000[-3:GMT] = 23/02/2026 00:00:00 GMT-3
Data esperada no sistema: 23/02/2026
Data atual no sistema: 22/02/2026 (ERRADO!)
"""

from datetime import datetime, timezone, timedelta
import dateutil.parser

# Simulando o que o ofxparse faz
ofx_date_string = "20260223000000[-3:GMT]"

print("="*80)
print("ANÁLISE DO BUG DE TIMEZONE NO OFX")
print("="*80)
print()

# Formato do OFX
print("1. DATA NO ARQUIVO OFX:")
print(f"   {ofx_date_string}")
print(f"   Interpretação: 23/02/2026 às 00:00:00 no fuso GMT-3 (Brasil)")
print()

# Como o ofxparse interpreta
print("2. COMO O OFXPARSE PROCESSA:")
print()

# ofxparse converte para datetime com timezone
# 20260223000000[-3:GMT] = 2026-02-23 00:00:00 GMT-3

# Criar datetime exatamente como vem do OFX
dt_original = datetime(2026, 2, 23, 0, 0, 0)
tz_brasil = timezone(timedelta(hours=-3))
dt_com_tz = dt_original.replace(tzinfo=tz_brasil)

print(f"   datetime com timezone: {dt_com_tz}")
print(f"   ISO format: {dt_com_tz.isoformat()}")
print()

# O que acontece quando usamos .date()
dt_naive = dt_com_tz.replace(tzinfo=None)
date_only = dt_com_tz.date()

print("3. QUANDO FAZEMOS .date():")
print(f"   dt_com_tz.date(): {date_only}")
print(f"   Tipo: {type(date_only)}")
print(f"   Resultado: {date_only.strftime('%d/%m/%Y')}")
print()

# O problema pode estar na conversão para UTC
dt_utc = dt_com_tz.astimezone(timezone.utc)
print("4. SE CONVERTER PARA UTC:")
print(f"   UTC datetime: {dt_utc}")
print(f"   UTC date: {dt_utc.date()}")
print(f"   Diferença: {dt_utc.date() == date_only}")
print()

# Teste: se o datetime vier como naive mas representando UTC
dt_naive_utc = datetime(2026, 2, 23, 0, 0, 0)  # Naive, mas que o ofxparse pensa ser UTC
dt_brasil_from_utc = dt_naive_utc + timedelta(hours=-3)  # Subtrair 3 horas = 21:00 do dia 22

print("5. SIMULAÇÃO DO BUG (se ofxparse tratar GMT-3 como UTC):")
print(f"   Se 23/02 00:00 GMT-3 for tratado como UTC...")
print(f"   E ajustarmos para GMT-3: {dt_brasil_from_utc}")
print(f"   Data resultante: {dt_brasil_from_utc.date()}")
print(f"   Formatado: {dt_brasil_from_utc.date().strftime('%d/%m/%Y')}")
print(f"   ❌ ERRO! Mostra 22/02/2026 em vez de 23/02/2026")
print()

# Solução
print("6. PROBLEMA IDENTIFICADO:")
print("   ofxparse pode estar:")
print("   a) Ignorando o timezone [-3:GMT]")
print("   b) Convertendo incorretamente para datetime local")
print("   c) Retornando datetime 'aware' que quando fazemos .date() perde um dia")
print()

# Teste com datetime aware
dt_aware_gmt3 = datetime(2026, 2, 23, 0, 0, 0, tzinfo=timezone(timedelta(hours=-3)))
print("7. TESTE COM DATETIME AWARE:")
print(f"   datetime: {dt_aware_gmt3}")
print(f"   .date(): {dt_aware_gmt3.date()}")
print(f"   Correto! {dt_aware_gmt3.date().strftime('%d/%m/%Y')}")
print()

# Mas se o sistema está no timezone UTC
import os
print("8. TIMEZONE DO SISTEMA:")
print(f"   TZ atual: {os.environ.get('TZ', 'Não definido')}")
print()

# Se datetime.now() for chamado em ambiente UTC
dt_now_utc = datetime.now(timezone.utc)
print("9. SE O SERVIDOR ESTIVER EM UTC (Railway):")
print(f"   Server time (UTC): {dt_now_utc}")
print(f"   Brasil time (UTC-3): {dt_now_utc.astimezone(timezone(timedelta(hours=-3)))}")
print()

print("="*80)
print("CONCLUSÃO:")
print("="*80)
print()
print("O problema PODE ser:")
print("1. ofxparse retorna datetime com tzinfo")
print("2. Quando fazemos .date() em datetime 'aware', Python pode usar timezone local")
print("3. Se o servidor (Railway) está em UTC, ao fazer .date() pode estar")
print("   pegando a data no timezone UTC em vez do timezone original do OFX")
print()
print("SOLUÇÃO:")
print("Antes de fazer .date(), converter explicitamente para o timezone correto!")
print()
