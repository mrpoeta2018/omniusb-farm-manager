with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i in range(1216, 1225):
        print(f'{i}: {lines[i].strip().encode("ascii", "ignore").decode()}')
