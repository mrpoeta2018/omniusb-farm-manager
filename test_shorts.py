import subprocess
import xml.etree.ElementTree as ET
import re

def run_adb(cmd):
    res = subprocess.run(["adb", "shell"] + cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return res.stdout

print("📸 Tomando radiografía de la pantalla (XML)... Espera unos segundos.")
run_adb(["uiautomator", "dump", "/sdcard/test_shorts.xml"])
xml_data = run_adb(["cat", "/sdcard/test_shorts.xml"])

if not xml_data or "<?xml" not in xml_data:
    print("❌ Error al leer la pantalla. Asegúrate de tener solo 1 celular conectado para esta prueba.")
    exit()

xml_data = re.sub(r"<\?xml.*?\?>", "", xml_data)
try:
    root = ET.fromstring(xml_data.encode("utf-8", "ignore"))
except Exception as e:
    print(f"❌ Error procesando el XML: {e}")
    exit()

btn_like = None
is_ad = False
botones_detectados = []

for node in root.iter("node"):
    text = (node.get("text") or "").lower()
    desc = (node.get("content-desc") or "").lower()
    bounds = node.get("bounds", "")
    
    # Rastrear cualquier cosa que parezca un botón para información adicional
    if desc: botones_detectados.append(desc)
    
    # Detectar si hay indicadores de publicidad
    if "patrocinado" in text or "anuncio" in text or "visitar" in text or "instalar" in text or "sponsored" in text or "ad" == text:
        is_ad = True
        
    # Detectar el botón de Like
    if "me gusta" in desc or "like" in desc:
        # Evitar el botón de "No me gusta"
        if "no me gusta" in desc or "dislike" in desc:
            continue
            
        if "deshacer" in desc or "quitar" in desc or "remove" in desc:
            btn_like = "ALREADY_LIKED"
        elif btn_like is None:
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if m:
                x1, y1, x2, y2 = map(int, m.groups())
                cx, cy = (x1+x2)//2, (y1+y2)//2
                btn_like = (cx, cy, desc)

print("\n=============================================")
print("           RESULTADOS DEL ESCÁNER            ")
print("=============================================\n")

if is_ad:
    print("🚨 ¡ANUNCIO / PUBLICIDAD DETECTADO!")
    print("   -> Acción de nuestro futuro bot: NO TOCAR EL CENTRO. Solo deslizar arriba.\n")
else:
    print("✅ Es un Short normal (No se detectó publicidad).\n")

if isinstance(btn_like, tuple):
    print(f"🎯 Botón LIKE encontrado en: X={btn_like[0]}, Y={btn_like[1]}")
    print(f"📝 Descripción leída: '{btn_like[2]}'")
    print(f"👉 Acción de nuestro futuro bot: input tap {btn_like[0]} {btn_like[1]}\n")
elif btn_like == "ALREADY_LIKED":
    print("👍 El video YA TIENE LIKE (Corazón rojo).")
    print("   -> Acción de nuestro futuro bot: No hacer nada, solo deslizar.\n")
else:
    print("❓ No se encontró el botón de Like visible.")
    print("   -> (Normalmente pasa si es un anuncio que bloquea la botonera lateral).\n")

print("=============================================")
