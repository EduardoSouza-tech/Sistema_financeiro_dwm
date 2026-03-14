data = open('web_server.py', 'rb').read()

# The buscar_nfse PDF block fix is at ~552240
# The wrong replacements are at ~570654 (excluir_nfse) and ~576320 (apagar_todas_nfse)
# Revert only those two by replacing _db_params_pdf back to db_params after byte 560000

split_point = 560000
before = data[:split_point]
after = data[split_point:]

wrong_str = b'NFSeDatabase(_db_params_pdf)'
right_str = b'NFSeDatabase(db_params)'

count = after.count(wrong_str)
print(f'Reverting {count} wrong replacements after byte {split_point}')
after_fixed = after.replace(wrong_str, right_str)

result = before + after_fixed
open('web_server.py', 'wb').write(result)

# Verify
final = open('web_server.py', 'rb').read()
remaining = final.count(b'NFSeDatabase(_db_params_pdf)')
print(f'Remaining _db_params_pdf occurrences: {remaining} (should be 1)')
print('Done')
