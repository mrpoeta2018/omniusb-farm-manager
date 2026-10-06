path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()
for i, line in enumerate(lines):
    if 'Inyectar' in line and 'CTkButton' in line:
        print(f'L{i+1}: {line.strip()}')
    elif 'def _inject_playlist_to_active' in line or 'def _inject_youtube_to_active' in line:
        print(f'L{i+1}: {line.strip()}')
