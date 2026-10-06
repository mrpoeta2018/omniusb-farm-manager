with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("split('\\\\n')", "split('\\n')")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed literal newline splits.')
