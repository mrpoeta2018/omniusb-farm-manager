import re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

# 1. Update Spotify Popup
old_popup = "1. Limpiar la cach"
if "1. Limpiar la cach" in content:
    content = content.replace("1. Limpiar la cach", "1. Cerrar la app forzosamente")
elif "1. Limpiar la cache" in content:
    content = content.replace("1. Limpiar la cache", "1. Cerrar la app forzosamente")

# 2. Add confirmation to clear_yt_music_cache
old_clear_func = '''def clear_yt_music_cache(self):
        devices = self.get_selected_devices()
        if not devices:
            self.log_msg(" Selecciona dispositivos en la pestaña principal primero.", "warn")
            return'''

new_clear_func = '''def clear_yt_music_cache(self):
        from tkinter import messagebox
        if not messagebox.askyesno("⚠️ PELIGRO: Borrado de Datos", 
            "Este botón NO es para liberar memoria.\\n\\n"
            "Va a hacer un 'Hard Reset' (Borrar todos los datos) de YouTube Music en los celulares.\\n"
            "- Cerrará las sesiones/cuentas.\\n"
            "- Borrará todas las configuraciones.\\n\\n"
            "Solo úsalo si la app está completamente rota y necesitas reinstalarla.\\n\\n"
            "¿Estás ABSOLUTAMENTE SEGURO de querer continuar?"):
            return
            
        devices = self.get_selected_devices()
        if not devices:
            self.log_msg(" Selecciona dispositivos en la pestaña principal primero.", "warn")
            return'''

if "Este botón NO es para liberar memoria" not in content:
    # Need to regex it because encoding issues might make exact match fail
    content = re.sub(r'def clear_yt_music_cache\(self\):\s+devices = self\.get_selected_devices\(\)\s+if not devices:\s+self\.log_msg\([^\)]+\)\s+return', new_clear_func, content)

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Popup texts updated.")
