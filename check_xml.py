import xml.etree.ElementTree as ET
import re

try:
    with open('dump_4908.xml', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Strip the XML declaration
    content = re.sub(r'<\?xml.*?\?>', '', content)
    root = ET.fromstring(content)
    
    for node in root.iter('node'):
        desc = (node.get('content-desc') or '').lower()
        text = (node.get('text') or '').lower()
        cls = node.get('class')
        bounds = node.get('bounds')
        if any(kw in desc for kw in ['play', 'reproducir', 'aleatorio', 'mezclar']) or any(kw in text for kw in ['play', 'reproducir', 'aleatorio', 'mezclar']) or 'button' in str(cls).lower():
            print(f"[{cls}] TEXT: '{text}' | DESC: '{desc}' | BOUNDS: {bounds}")
except Exception as e:
    print(f"Error parsing XML: {e}")
