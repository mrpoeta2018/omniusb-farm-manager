import time
import subprocess
import re
import xml.etree.ElementTree as ET

def run_adb(cmd_args, capture=False):
    full_cmd = ["platform-tools/adb.exe", "-s", "L0S600VE38262"] + cmd_args
    if capture:
        return subprocess.run(full_cmd, capture_output=True, text=True, errors="ignore").stdout
    else:
        print(f"> {' '.join(full_cmd)}")
        subprocess.run(full_cmd)

def test_tidal(url):
    print(f"\n--- Probando URL Tidal: {url} ---")
    
    # 1. Matar Tidal si estaba abierto
    run_adb(["shell", "am", "force-stop", "com.aspiro.tidal"])
    time.sleep(2)
    
    # 2. Inyectar link
    run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url, "com.aspiro.tidal"])
    
    # 3. Esperar que cargue
    print("Esperando 12 segundos para que cargue la lista en Tidal...")
    time.sleep(12)
    
    # 4. Extraer XML
    print("Extrayendo UI de la pantalla...")
    run_adb(["shell", "uiautomator", "dump", "/sdcard/dump_tidal.xml"])
    out = run_adb(["shell", "cat", "/sdcard/dump_tidal.xml"], capture=True)
    
    if not out:
        print("Error: No se pudo obtener el XML.")
        return
        
    # Limpiar XML y parsear
    out = re.sub(r"<\?xml.*?\?>", "", out)
    try:
        root = ET.fromstring(out.encode("utf-8", "ignore"))
    except Exception as e:
        print("Error parseando XML:", e)
        return
        
    btn_play = None
    fallback_song = None
    
    print("Elementos encontrados en Tidal:")
    for node in root.iter("node"):
        desc = (node.get("content-desc") or "").lower()
        text_n = (node.get("text") or "").lower()
        res_id = (node.get("resource-id") or "")
        bounds = node.get("bounds", "")
        
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if not m: continue
        x1, y1, x2, y2 = map(int, m.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        # Ignorar mini-reproductor abajo
        if cy > 750: continue
            
        # Detectar botones comunes
        if res_id == "com.aspiro.tidal:id/playButton" or res_id == "com.aspiro.tidal:id/shufflePlayButton" or "reproducir" == text_n or "aleatorio" == text_n:
            print(f" -> ¡Botón CORRECTO!: Texto='{text_n}', Desc='{desc}', ID='{res_id}' en X:{cx} Y:{cy}")
            if not btn_play:
                btn_play = (cx, cy)
                
    if btn_play:
        print(f"¡Encontrado botón principal! Presionando en {btn_play}...")
        run_adb(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])])
        print("¡Éxito! Reproducción iniciada en Tidal.")
    else:
        print("No se encontró ningún botón obvio. Guardando 'debug_tidal.xml' para análisis...")
        with open("debug_tidal.xml", "w", encoding="utf-8") as f:
            f.write(out)

if __name__ == "__main__":
    test_url = "https://tidal.com/playlist/dcc69455-aad1-42c5-b73f-6da9ff39643d"
    test_tidal(test_url)
