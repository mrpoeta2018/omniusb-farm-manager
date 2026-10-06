import xml.etree.ElementTree as ET
import re

try:
    with open('dump_4908.xml', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    content = re.sub(r'<\?xml.*?\?>', '', content)
    root = ET.fromstring(content)
    
    for node in root.iter('node'):
        bounds = node.get('bounds')
        if not bounds: continue
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            # Search around y1=500 to 650
            if 500 <= y1 <= 650:
                cls = node.get('class')
                desc = (node.get('content-desc') or '')
                text = (node.get('text') or '')
                print(f"[{cls}] TEXT: '{text}' | DESC: '{desc}' | BOUNDS: {bounds}")
except Exception as e:
    print(f"Error parsing XML: {e}")
