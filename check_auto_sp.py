with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
    start = text.find('def _trigger_auto_spotify')
    if start != -1:
        print(text[start:start+1500])
