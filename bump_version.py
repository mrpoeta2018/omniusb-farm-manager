import json
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\version.json'
with open(path, 'r', encoding='utf-8') as f: data = json.load(f)

data['version'] = '5.2.0'
data['notes'] = 'Update 5.2.0: Plantillas de Farming, Escudos Anti-Choques completos, Goteo Humano inteligente y Toques Fantasmas silenciosos.'

with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
print("Version updated to 5.2.0")
