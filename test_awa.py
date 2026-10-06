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

def test_awa(url):
    print(f"\n--- Probando URL AWA: {url} ---")
    
    # 1. Matar AWA
    # 1. Matar AWA y Chrome (por si acaso)
    run_adb(["shell", "am", "force-stop", "fm.awa.liverpool"])
    run_adb(["shell", "am", "force-stop", "com.android.chrome"])
    time.sleep(2)
    
    # 2. Inyectar link SIN forzar el paquete, dejando que el sistema decida (como un clic real)
    run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url])
    
    # 3. Esperar que cargue
    print("Esperando 15 segundos... SI VES EL DIÁLOGO DE 'ABRIR CON', POR FAVOR TOCA 'AWA' Y LUEGO 'SIEMPRE' EN LA PANTALLA DEL CELULAR.")
    time.sleep(15)
    
    # 4. Extraer XML
    print("Extrayendo UI de la pantalla...")
    run_adb(["shell", "uiautomator", "dump", "/sdcard/dump_awa.xml"])
    out = run_adb(["shell", "cat", "/sdcard/dump_awa.xml"], capture=True)
    
    if "Abrir con" in out or "android:id/resolver_list" in out:
        print("¡Detectado diálogo de 'Abrir con'! Seleccionando AWA (240, 714) y Siempre (408, 860)...")
        run_adb(["shell", "input", "tap", "240", "714"])
        time.sleep(1.5)
        run_adb(["shell", "input", "tap", "408", "860"])
        print("Esperando 6s a que AWA cargue...")
        time.sleep(6)
        run_adb(["shell", "uiautomator", "dump", "/sdcard/dump_awa.xml"])
        out = run_adb(["shell", "cat", "/sdcard/dump_awa.xml"], capture=True)
    if not out:
        print("Error: No se pudo obtener el XML.")
        return
        
    out = re.sub(r"<\?xml.*?\?>", "", out)
    try:
        root = ET.fromstring(out.encode("utf-8", "ignore"))
    except Exception as e:
        print("Error parseando XML:", e)
        return
        return
        
    btn_play = None
    fallback_song = None
    
    print("Buscando botones en AWA:")
    for node in root.iter("node"):
        desc = (node.get("content-desc") or "").lower()
        text_n = (node.get("text") or "").lower()
        res_id = (node.get("resource-id") or "")
        bounds = node.get("bounds", "")
        
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if not m: continue
        x1, y1, x2, y2 = map(int, m.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        if cy > 750: continue # Ignorar mini reproductor (si lo hay)
            
        # Para AWA, vamos a buscar palabras o ids típicos
        if "play" in res_id.lower() or "shuffle" in res_id.lower() or "reproducir" in desc or "play" in desc or "reproducir" in text_n or "play" in text_n:
            print(f" -> Posible botón: Texto='{text_n}', Desc='{desc}', ID='{res_id}' en X:{cx} Y:{cy}")
            if not btn_play:
                btn_play = (cx, cy)
                
    if btn_play:
        print(f"¡Presionando en {btn_play}!")
        run_adb(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])])
        print("¡Éxito! Toque enviado.")
    else:
        print("No se encontró ningún botón obvio. Guardando 'debug_awa.xml' para análisis...")
        with open("debug_awa.xml", "w", encoding="utf-8") as f:
            f.write(out)

if __name__ == "__main__":
    test_url = "https://mf.awa.fm/4xjDbdd"
    test_awa(test_url)
