with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('self.adb.run_command(["shell", "am", "kill-all"], serial)', '# Removed am kill-all')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Removed am kill-all')
