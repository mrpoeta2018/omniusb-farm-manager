path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
import re
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
for match in re.finditer(r'self\.([a-zA-Z0-9_]+)\s*=\s*ctk\.CTkButton[^>]+?Inyectar', content):
    print(match.group(1))
