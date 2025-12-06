from database import DatabaseManager
from models import StatusLancamento

db = DatabaseManager()
lancs = db.listar_lancamentos()
print(f'Total: {len(lancs)}')

pagos = [l for l in lancs if l.status == StatusLancamento.PAGO]
print(f'Pagos: {len(pagos)}')

if pagos:
    primeiro = pagos[0]
    print(f'\nPrimeiro lançamento pago:')
    print(f'  Descrição: {primeiro.descricao}')
    print(f'  Tipo data_pagamento: {type(primeiro.data_pagamento)}')
    print(f'  Valor: {primeiro.data_pagamento}')
    print(f'  Tem método .date()?: {hasattr(primeiro.data_pagamento, "date")}')
