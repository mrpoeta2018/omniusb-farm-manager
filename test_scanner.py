import time
import re
import xml.etree.ElementTree as ET
import subprocess
import sys

serial = '4908782458070605'
adb_path = r'C:\Users\poeta marzo\Desktop\omniusb-farm-manager-main\omniusb-farm-manager\platform-tools\adb.exe'

def run_adb(cmd, s):
    full_cmd = [adb_path, '-s', s] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return res.stdout

print(f"--- Probando Escaner en {serial} ---")

run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
out = run_adb(["shell", "cat", "/sdcard/window_dump.xml"], serial)

if not out or 'ERROR' in out:
    print("Error dumping UI!")
    sys.exit(1)

out = re.sub(r'<\?xml.*?\?>', '', out)
root = ET.fromstring(out.encode('utf-8', 'ignore'))

btn_agregar = None
btn_play = None
agregar_y2 = 0
first_track = None

for node in root.iter('node'):
    desc = (node.get('content-desc') or '').lower()
    text_node = (node.get('text') or '').lower()
    cls = node.get('class')
    bounds = node.get('bounds', '')
    
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
    if not match: continue
    x1, y1, x2, y2 = map(int, match.groups())
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    
    if 'agregar' in desc and 'playlist' in desc:
        btn_agregar = (cx, cy)
        agregar_y2 = y2
        
    is_play_kw = lambda s: any(kw in s for kw in ['reproducir playlist', 'play playlist', 'aleatorio', 'mezclar']) or s == 'reproducir' or s == 'play' or s == 'shuffle'
    if (is_play_kw(desc) or is_play_kw(text_node)) and 'agregar' not in desc and 'agregar' not in text_node:
        btn_play = (cx, cy)
        
    if agregar_y2 > 0 and cls == 'android.widget.TextView' and len(text_node.strip()) > 0 and y1 > agregar_y2:
        if not first_track:
            first_track = (cx, cy, text_node)

if btn_play:
    print(f"? Boton Verde Encontrado en {btn_play}!")
    run_adb(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])], serial)
elif first_track:
    print(f"? Boton Play oculto. Tocando primera cancion: '{first_track[2].title()}' en {first_track[0]}, {first_track[1]}...")
    run_adb(["shell", "input", "tap", str(first_track[0]), str(first_track[1])], serial)
else:
    print("? No se encontro ni el boton play ni la primera cancion.")
    
time.sleep(2)

# Check if playing
audio_state = run_adb(["shell", "dumpsys", "media_session"], serial)
if 'state=PlaybackState {state=3' in audio_state or 'state=3' in audio_state:
    print("?? EXITO: ¡El celular esta reproduciendo musica!")
else:
    print("?? Falla: El celular NO esta reproduciendo musica despues del toque.")

