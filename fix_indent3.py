import re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

content = content.replace('\ndef build_traffic_tab(self):', '\n    def build_traffic_tab(self):')

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Indentation fixed at build_traffic_tab.")
