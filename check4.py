with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'def _is_spotify_playing' in line:
            start = i
            break
    lines = f.readlines()
    for i in range(start, start + 30):
        print(f'{i}: {lines[i-start-1].strip().encode("ascii", "ignore").decode()}')
