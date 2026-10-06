import os, re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

# For Spotify auto trigger
content = re.sub(
    r'(def _trigger_auto_spotify.*?)(self\._inject_playlist_to_single\(dev\[\'serial\'\], current\))',
    r'\1import random\n                    rnd_url = random.choice(target_list)\n                    self._inject_playlist_to_single(dev["serial"], rnd_url)',
    content, flags=re.DOTALL
)

# For YT Music auto trigger
content = re.sub(
    r'(def _trigger_auto_yt_music.*?)(self\._inject_youtube_to_single\(dev\[\'serial\'\], current\))',
    r'\1import random\n                    rnd_url = random.choice(target_list)\n                    self._inject_youtube_to_single(dev["serial"], rnd_url)',
    content, flags=re.DOTALL
)

# For YT Video auto trigger
content = re.sub(
    r'(def _trigger_auto_yt_video.*?)(self\._inject_youtube_to_single\(dev\[\'serial\'\], current\))',
    r'\1import random\n                    rnd_url = random.choice(target_list)\n                    self._inject_youtube_to_single(dev["serial"], rnd_url)',
    content, flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Auto-Rotador actualizado: Distribución aleatoria por dispositivo activada.")
