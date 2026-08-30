path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
import re
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
idx = content.find('def inject_manual_playlist')
if idx != -1:
    print(content[idx:idx+800].encode('ascii', 'ignore').decode())
