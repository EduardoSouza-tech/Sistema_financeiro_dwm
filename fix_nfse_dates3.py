data = open('web_server.py', 'rb').read()

# The target block starts before "# Validar campos" around byte ~549860
# and the specific "Datas inicial e final" is at 549911
# Let's find the full block start
start_marker = b"        # Validar campos obrigat\xef\xbf\xbdrios\r\n        if not data.get('data_inicial') or not data.get('data_final'):\r\n            return jsonify({\r\n                'success': False,\r\n                'error': 'Datas inicial e final s\xef\xbf\xbdo obrigat\xef\xbf\xbdrias'\r\n            }), 400\r\n        \r\n        # Validar ordem das datas\r\n        from datetime import datetime\r\n        try:\r\n            dt_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d')\r\n            dt_final = datetime.strptime(data['data_final'], '%Y-%m-%d')\r\n            \r\n            if dt_final < dt_inicial:\r\n                return jsonify({\r\n                    'success': False,\r\n                    'error': 'Data final deve ser maior que data inicial'\r\n                }), 400\r\n                \r\n        except ValueError as e:\r\n            return jsonify({\r\n                'success': False,\r\n                'error': f'Formato de data inv\xef\xbf\xbdlido: {e}'\r\n            }), 400\r\n"

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
)

if start_marker in data:
    result = data.replace(start_marker, new_block, 1)
    open('web_server.py', 'wb').write(result)
    print("OK: replaced mandatory date validation in buscar_nfse")
else:
    print("NOT FOUND — showing context at ~549840:")
    print(repr(data[549840:550200]))
