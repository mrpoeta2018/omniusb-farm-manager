import re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

# Fix inject_manual_playlist indentation
content = content.replace('\ndef inject_manual_playlist(self):\n', '\n    def inject_manual_playlist(self):\n')

# Check for other functions that might have been unindented in patch_others.py
content = content.replace('\ndef inject_manual_ytmusic(self):', '\n    def inject_manual_ytmusic(self):')
content = content.replace('\ndef inject_manual_awa(self):', '\n    def inject_manual_awa(self):')
content = content.replace('\ndef inject_manual_pandora(self):', '\n    def inject_manual_pandora(self):')
content = content.replace('\ndef inject_manual_audiomack(self):', '\n    def inject_manual_audiomack(self):')
content = content.replace('\ndef inject_manual_applemusic(self):', '\n    def inject_manual_applemusic(self):')
content = content.replace('\ndef inject_manual_tidal(self):', '\n    def inject_manual_tidal(self):')
content = content.replace('\ndef inject_manual_youtube(self):', '\n    def inject_manual_youtube(self):')

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Indentation fixed.")
