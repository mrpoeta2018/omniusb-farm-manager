with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'def _trigger_auto_spotify' in line or 'def _trigger_auto_yt' in line:
            print(f'{i}: {line.strip()}')
