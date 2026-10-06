with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
    start = text.find('def inject_manual_youtube')
    if start != -1:
        with open('yt_snippet.txt', 'w', encoding='utf-8') as o:
            o.write(text[start:start+1500])
