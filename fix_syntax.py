import re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

# I will replace the entire clear_yt_music_cache function up to threading.Thread(target=_clear, daemon=True).start()
# to ensure it's completely clean.

start_idx = content.find("def clear_yt_music_cache(self):")
end_idx = content.find("def install_custom_apk(self, apk_filename, display_name):", start_idx)

new_func = '''def clear_yt_music_cache(self):
        from tkinter import messagebox
        if not messagebox.askyesno("PELIGRO: Borrado de Datos", "Este boton NO es para liberar memoria.\\n\\nVa a hacer un Hard Reset (Borrar todos los datos) de YouTube Music en los celulares.\\nCerrara las cuentas y borrara configuraciones.\\n\\nSolo usalo si la app esta rota.\\n\\n¿Continuar?"):
            return
            
        devices = self.get_selected_devices()
        if not devices:
            self.log_msg(" Selecciona dispositivos en la pestana principal primero.", "warn")
            return
            
        def _clear():
            self.log_msg(f" Limpiando Cach de YT Music en {len(devices)} dispositivos...", "warn")
            for dev in devices:
                self.adb.run_command(["shell", "pm", "clear", "com.google.android.apps.youtube.music"], dev['serial'])
            self.after(0, lambda: self.log_msg(" Limpieza de Cach de YT Music completada.", "info"))
            
        import threading
        threading.Thread(target=_clear, daemon=True).start()

    '''

content = content[:start_idx] + new_func + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Syntax error fixed.")
