with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
    if 'def watchdog_ghost_loop' in text:
        start = text.find('def watchdog_ghost_loop')
        with open('watchdog_snippet.txt', 'w', encoding='utf-8') as outf:
            outf.write(text[start+1000:start+3000])
