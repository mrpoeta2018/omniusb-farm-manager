import subprocess
import xml.etree.ElementTree as ET
import re
import time
import sys

def run_adb(cmd):
    res = subprocess.run(["adb", "shell"] + cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return res.stdout

def get_nodes():
    run_adb(["uiautomator", "dump", "/sdcard/omni_dump.xml"])
    xml_data = run_adb(["cat", "/sdcard/omni_dump.xml"])
    if not xml_data or "<?xml" not in xml_data: return None
    xml_data = re.sub(r"<\?xml.*?\?>", "", xml_data)
    try:
        return ET.fromstring(xml_data.encode("utf-8", "ignore"))
    except:
        return None

print("=======================================")
print("  TEST AVANZADO: LIKE, GUARDAR, COMENTAR")
print("=======================================")

print("\n1. Tomando radiografía inicial de la pantalla...")
root = get_nodes()
if not root:
    print("❌ Error al leer la pantalla. Asegúrate de tener solo 1 celular conectado.")
    sys.exit()

btn_like, btn_save, btn_comment = None, None, None
is_ad = False

for node in root.iter("node"):
    text = (node.get("text") or "").lower()
    desc = (node.get("content-desc") or "").lower()
    bounds = node.get("bounds", "")
    
    if "patrocinado" in text or "anuncio" in text or "visitar" in text or "instalar" in text or "sponsored" in text or text == "ad":
        is_ad = True
    
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not m: continue
    cx, cy = (int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2
    
    # Buscar Like
    if "me gusta" in desc or "like" in desc:
        if "no me gusta" not in desc and "dislike" not in desc:
            btn_like = "ALREADY_LIKED" if ("quitar" in desc or "deshacer" in desc) else (cx, cy)
            
    # Buscar Guardar
    if "guardar" in desc or "save" in desc:
        btn_save = (cx, cy)
    elif "guardado" in desc or "saved" in desc:
        btn_save = "ALREADY_SAVED"
        
    # Buscar Comentarios
    if "comentarios" in desc or "comentar" in desc:
        if "inhabilit" in desc or "desactiv" in desc:
            btn_comment = "DISABLED"
        else:
            btn_comment = (cx, cy)

if is_ad:
    print("🚨 ES PUBLICIDAD! Acción: Deslizar y salir.")
    run_adb(["input", "swipe", "240", "850", "240", "100", "400"])
    sys.exit()

# LIKE
if btn_like == "ALREADY_LIKED":
    print("👍 LIKE: El video ya tiene el corazón puesto.")
elif btn_like:
    print(f"❤️ LIKE: Dando like en {btn_like}...")
    run_adb(["input", "tap", str(btn_like[0]), str(btn_like[1])])
    time.sleep(1)

# GUARDAR
if btn_save == "ALREADY_SAVED":
    print("💾 GUARDAR: El video ya estaba guardado en listas.")
elif btn_save:
    print(f"💾 GUARDAR: Tocando botón guardar en {btn_save}...")
    run_adb(["input", "tap", str(btn_save[0]), str(btn_save[1])])
    time.sleep(1)

# COMENTAR
if btn_comment == "DISABLED":
    print("💬 COMENTARIOS: Están desactivados para este video.")
elif btn_comment:
    print(f"💬 COMENTARIOS: Abriendo panel en {btn_comment}...")
    run_adb(["input", "tap", str(btn_comment[0]), str(btn_comment[1])])
    time.sleep(2)
    
    print("   -> Buscando caja de texto para escribir...")
    root2 = get_nodes()
    textbox = None
    btn_send = None
    if root2:
        for node in root2.iter("node"):
            text = (node.get("text") or "").lower()
            desc = (node.get("content-desc") or "").lower()
            if ("agrega" in text or "comenta" in text or "aade" in text) and "inhabilit" not in text:
                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                if m: textbox = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
            if "enviar" in desc or "send" in desc or "publicar" in desc or "comentar" == desc:
                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                if m: btn_send = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)

    if textbox:
        print(f"   -> Tocando caja de texto en {textbox} (abriendo teclado)...")
        run_adb(["input", "tap", str(textbox[0]), str(textbox[1])])
        time.sleep(1)
        print("   -> Escribiendo mensaje: 'DIOS te ama ..'")
        run_adb(["input", "text", "DIOS\ te\ ama\ .."])
        time.sleep(1)
        
        # Intentar tocar botón de enviar
        if btn_send:
            print(f"   -> Tocando botón enviar en {btn_send}...")
            run_adb(["input", "tap", str(btn_send[0]), str(btn_send[1])])
        else:
            print("   -> Usando tecla ENTER para enviar...")
            run_adb(["input", "keyevent", "66"]) # ENTER
            
        time.sleep(1)
        print("   -> Saliendo del teclado (Back)...")
        run_adb(["input", "keyevent", "4"])
    else:
        print("   -> No se encontró la caja para escribir el comentario.")
        
    print("   -> Cerrando panel de comentarios (Back)...")
    run_adb(["input", "keyevent", "4"])

print("\n🚀 FLUJO COMPLETO TERMINADO. Deslizando al siguiente...")
run_adb(["input", "swipe", "240", "850", "240", "100", "400"])
print("=======================================")
