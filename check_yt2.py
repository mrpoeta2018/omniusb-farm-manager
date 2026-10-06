with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
    idx = text.find("self._action_start('youtube')")
    start = max(0, idx-500)
    print(text[start:idx+500])
