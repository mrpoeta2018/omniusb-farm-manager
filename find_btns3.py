path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
import re
with open(path, 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()
for i, line in enumerate(lines):
    if 'command=self.inject_spotify' in line or 'command=self._inject_playlist_to_active' in line or 'CTkButton' in line and ('Spotify' in line or 'YouTube' in line):
        print(f"L{i}: {line.strip().encode('ascii', 'ignore').decode()}")
