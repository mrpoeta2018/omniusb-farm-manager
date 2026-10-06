import re
with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Change range(15) to range(25) in delayed_play
text = re.sub(r'# 1\. Espera inicial \(15 seg\) con doble inyeccion para telefonos lentos\s*for i in range\(15\):', '# 1. Espera inicial (25 seg) con doble inyeccion para telefonos lentos\n            for i in range(25):', text)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Increased Spotify wait time to 25 seconds.')
