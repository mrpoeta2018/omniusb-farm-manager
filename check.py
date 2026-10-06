with open('app_clean.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"Tidal", "AWA"', '"Tidal"')
text = text.replace('"Apple Music", "Tidal"', '"Apple Music", "Tidal", "AWA"')

with open('app_clean.py', 'w', encoding='utf-8') as f:
    f.write(text)
