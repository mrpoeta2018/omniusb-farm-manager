with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
    if 'Adelantando pista' in text or 'MediaBot' in text or 'skip' in text:
        start = text.find('watchdog_ghost_loop')
        print(text[start:start+3500])
