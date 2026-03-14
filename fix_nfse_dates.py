import re

data = open('web_server.py', 'rb').read()

# Remove mandatory date validation block and replace with optional check
old = (
    b"        # Validar campos obrigat\xef\xbf\xbdrios\r\n"
    b"        if not data.get('data_inicial') or not data.get('data_final'):\r\n"
    b"            return jsonify({\r\n"
    b"                'success': False,\r\n"
    b"                'error': 'Datas inicial e final s\xef\xbf\xbdo obrigat\xef\xbf\xbddrias'\r\n"
    b"            }), 400\r\n"
    b"        \r\n"
    b"        # Validar ordem das datas\r\n"
    b"        from datetime import datetime\r\n"
    b"        try:\r\n"
    b"            dt_inicial = datetime.strptime(data['data_inicial'], '%Y-%m-%d')\r\n"
    b"            dt_final = datetime.strptime(data['data_final'], '%Y-%m-%d')\r\n"
    b"            \r\n"
    b"            if dt_final < dt_inicial:\r\n"
    b"                return jsonify({\r\n"
    b"                    'success': False,\r\n"
    b"                    'error': 'Data final deve ser maior que data inicial'\r\n"
    b"                }), 400\r\n"
    b"                \r\n"
    b"        except ValueError as e:\r\n"
    b"            return jsonify({\r\n"
    b"                'success': False,\r\n"
    b"                'error': f'Formato de data inv\xef\xbf\xbdlido: {e}'\r\n"
    b"            }), 400\r\n"
)

new = (
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

if old in data:
    result = data.replace(old, new, 1)
    open('web_server.py', 'wb').write(result)
    print("OK: replaced web_server.py mandatory date validation")
else:
    print("NOT FOUND — trying with LF line endings...")
    old_lf = old.replace(b'\r\n', b'\n')
    if old_lf in data:
        new_lf = new.replace(b'\r\n', b'\n')
        result = data.replace(old_lf, new_lf, 1)
        open('web_server.py', 'wb').write(result)
        print("OK: replaced (LF variant)")
    else:
        # Show surrounding bytes for debugging
        idx = data.find(b"Validar campos obrigat")
        if idx >= 0:
            print("Found at byte", idx, "context:")
            print(repr(data[idx:idx+300]))
        else:
            print("ERROR: Could not find the target string at all")
