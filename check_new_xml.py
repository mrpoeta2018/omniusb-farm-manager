import xml.etree.ElementTree as ET
import re

with open('dump_new.xml', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

content = re.sub(r'<\?xml.*?\?>', '', content)
root = ET.fromstring(content)

for node in root.iter('node'):
    desc = (node.get('content-desc') or '').lower()
    text = (node.get('text') or '').lower()
    cls = node.get('class')
    bounds = node.get('bounds')
    if 'agregar' in desc or 'play' in desc or 'reproducir' in desc or 'aleatorio' in desc or 'button' in cls.lower():
        print(f"[{cls}] TEXT: '{text}' | DESC: '{desc}' | BOUNDS: {bounds}")
