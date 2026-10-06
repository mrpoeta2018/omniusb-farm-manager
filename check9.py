with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'def inject_manual_youtube(self):' in line:
            start = i
            break
    lines = f.readlines()
    for i in range(start, start + 45):
        print(f'{i}: {lines[i-start-1].strip().encode("ascii", "ignore").decode()}')
