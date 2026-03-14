data = open('web_server.py', 'rb').read()

# Find the specific block in buscar_nfse route (should be around byte position for def buscar_nfse)
idx = data.find(b"def buscar_nfse():")
print(f"buscar_nfse() at byte: {idx}")

# Look for the mandatory date validation after buscar_nfse
search = b"Datas inicial e final s"
pos = idx
while True:
    pos = data.find(search, pos)
    if pos == -1:
        print("Not found (Datas inicial e final s...)")
        break
    print(f"Found at byte {pos}:")
    print(repr(data[pos:pos+200]))
    print()
    pos += 1
