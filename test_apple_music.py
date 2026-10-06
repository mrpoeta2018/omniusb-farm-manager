import subprocess
import time
import re
import xml.etree.ElementTree as ET

def run_adb(cmd_args):
    cmd = ["platform-tools/adb.exe", "-s", "L0S600VE38262"] + cmd_args
    print(">", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    return res.stdout

def test_apple_music(url):
    print(f"\n--- Probando URL: {url} ---")
    # 1. Forzar cierre para empezar limpio
    run_adb(["shell", "am", "force-stop", "com.apple.android.music"])
    time.sleep(2)
    
    # 2. Abrir la playlist con Intent
    run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url, "com.apple.android.music"])
    print("Esperando 10 segundos para que cargue la lista...")
    time.sleep(10)
    
    # 3. Extraer XML de la pantalla
    print("Extrayendo UI de la pantalla...")
    run_adb(["shell", "uiautomator", "dump", "/sdcard/dump_am.xml"])
    out = run_adb(["shell", "cat", "/sdcard/dump_am.xml"])
    if not out:
        print("No se pudo obtener el XML.")
        return
        
    out = re.sub(r"<\?xml.*?\?>", "", out)
    try:
        root = ET.fromstring(out)
    except Exception as e:
        print("Error parseando XML:", e)
        return
        
    # 4. Buscar botón de Reproducir / Aleatorio
    btn_play = None
    fallback_song = None
    
    for node in root.iter("node"):
        desc = (node.get("content-desc") or "").lower()
        text_n = (node.get("text") or "").lower()
        res_id = (node.get("resource-id") or "")
        bounds = node.get("bounds", "")
        
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if not m: continue
        x1, y1, x2, y2 = map(int, m.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        # Ignorar el mini-reproductor de abajo (Y > 700 en la pantalla del celular L1 PRO)
        if cy > 750:
            continue
            
        # Si encontramos una fila de canción (para el caso de links de 1 sola canción)
        if "collection_list_item" in res_id or "list_item_track" in res_id:
            if fallback_song is None:
                fallback_song = (cx, cy)
            
        # Buscar el botón principal de Play o Shuffle (Playlists/Albums)
        if "play_button" in res_id or "shuffle_button" in res_id or any(k in desc or k in text_n for k in ["reproducir", "play", "aleatorio", "shuffle"]):
            print(f"¡Encontrado botón principal! Texto: '{text_n}', Desc: '{desc}', ID: '{res_id}' en X:{cx} Y:{cy}")
            btn_play = (cx, cy)
            break
            
    if btn_play:
        print(f"Presionando botón principal en {btn_play}...")
        run_adb(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])])
        print("¡Éxito! Reproducción iniciada.")
    elif fallback_song:
        print(f"No hay botón global. Tocando directamente la canción en {fallback_song}...")
        run_adb(["shell", "input", "tap", str(fallback_song[0]), str(fallback_song[1])])
        print("¡Éxito! Canción iniciada directamente.")
    else:
        print("No se encontró ningún botón ni canción en la pantalla.")
        print("Guardando el XML como 'debug_apple_music.xml' para inspeccionarlo...")
        with open("debug_apple_music.xml", "w", encoding="utf-8") as f:
            f.write(out)
            
if __name__ == "__main__":
    # Playlist de prueba (Global Hits de Apple Music)
    test_url = "https://music.apple.com/ar/song/evitando-lo-malo-feat-brahy-dream-fulfilled-prod-dianarg/1690515640"
    test_apple_music(test_url)
