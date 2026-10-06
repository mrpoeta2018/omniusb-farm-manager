with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
    start = text.find('def _trigger_auto_spotify')
    if start != -1:
        with open('out_sp.txt', 'w', encoding='utf-8') as o:
            o.write(text[start:start+1500])
