path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
idx = content.find('def inject_manual_playlist')
print(content[idx:idx+1500].encode('ascii', 'ignore').decode())
