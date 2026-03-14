data = open('web_server.py', 'rb').read()

START = 549707
END   = 550669

# Verify what we're replacing
print("Replacing:")
print(repr(data[START:END]))
print()

new_block = (
    b"        # Validar ordem das datas (apenas se ambas fornecidas)\r\n"
    b"        from datetime import datetime\r\n"
    b"        if data.get('data_inicial') and data.get('data_final'):\r\n"
    b"            try:\r\n"
    b"                dt_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d')\r\n"
    b"                dt_final = datetime.strptime(data['data_final'], '%Y-%m-%d')\r\n"
    b"                if dt_final < dt_inicial:\r\n"
    b"                    return jsonify({\r\n"
    b"                        'success': False,\r\n"
    b"                        'error': 'Data final deve ser maior que data inicial'\r\n"
    b"                    }), 400\r\n"
    b"            except ValueError as e:\r\n"
    b"                return jsonify({\r\n"
    b"                    'success': False,\r\n"
    b"                    'error': f'Formato de data invalido: {e}'\r\n"
    b"                }), 400\r\n"
    b"        \r\n"
)

result = data[:START] + new_block + data[END:]
open('web_server.py', 'wb').write(result)
print("OK: replaced")
print("New block:")
print(new_block.decode('utf-8'))
