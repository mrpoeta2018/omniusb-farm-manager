with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
    if 'def watchdog_ghost_loop' in text:
        start = text.find('def watchdog_ghost_loop')
        print(text[start:start+1000])
