import xml.etree.ElementTree as ET
import re

try:
    with open('dump_4908.xml', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    content = re.sub(r'<\?xml.*?\?>', '', content)
    root = ET.fromstring(content)
    
    first_track = None
    agregar_y2 = 0
    
    # 1. Encontrar el boton agregar para tener una referencia Y
    for node in root.iter('node'):
        desc = (node.get('content-desc') or '').lower()
        if 'agregar' in desc and 'playlist' in desc:
            bounds = node.get('bounds')
            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
            if match:
                agregar_y2 = int(match.group(4))
                break
                
    # 2. Buscar el primer TextView con texto que este debajo de agregar_y2
    if agregar_y2 > 0:
        for node in root.iter('node'):
            cls = node.get('class')
            text = node.get('text') or ''
            if cls == 'android.widget.TextView' and len(text.strip()) > 0:
                bounds = node.get('bounds')
                match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                if match:
                    y1 = int(match.group(2))
                    if y1 > agregar_y2:
                        first_track = text
                        print(f"First track found: '{text}' at bounds {bounds}")
                        break
except Exception as e:
    print(f"Error: {e}")
