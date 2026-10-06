import re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

old_on_close = '''    def on_close(self):
        """Clean up all child processes before closing the window."""
        try:
            self.engine.stop_rotation()
            self.runner.kill_all_gnirehtet()
            self.engine.pm.stop_all()
        except Exception:
            pass
        self.destroy()'''

new_on_close = '''    def on_close(self):
        """Clean up all child processes before closing the window."""
        import customtkinter as ctk
        import threading
        import subprocess
        import os
        import time
        
        # Deshabilitar el boton de cierre para no cliquear dos veces
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Crear ventana modal de apagado
        shutdown_window = ctk.CTkToplevel(self)
        shutdown_window.title("Apagado Seguro")
        shutdown_window.geometry("400x150")
        shutdown_window.attributes("-topmost", True)
        shutdown_window.resizable(False, False)
        
        lbl = ctk.CTkLabel(shutdown_window, text="Iniciando apagado seguro...\\nPor favor espere.", font=("Arial", 14, "bold"))
        lbl.pack(pady=20)
        
        pbar = ctk.CTkProgressBar(shutdown_window, width=300)
        pbar.pack(pady=10)
        pbar.set(0)
        pbar.start()

        def _shutdown_task():
            try:
                # 1. Detener inyecciones automaticas
                lbl.configure(text="Deteniendo inyecciones automáticas...")
                self.engine.stop_rotation()
                time.sleep(1)
                
                # 2. Detener red
                lbl.configure(text="Desconectando túneles de red (Gnirehtet)...")
                self.runner.kill_all_gnirehtet()
                time.sleep(1)
                
                # 3. Detener procesos locales
                lbl.configure(text="Cerrando motores internos...")
                self.engine.pm.stop_all()
                time.sleep(1)
                
                # 4. Exterminio seguro de ADB para liberar puertos USB
                lbl.configure(text="Liberando puertos USB (Cerrando ADB)...")
                try: subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], creationflags=subprocess.CREATE_NO_WINDOW)
                except: pass
                try: subprocess.run(["taskkill", "/F", "/IM", "gnirehtet.exe"], creationflags=subprocess.CREATE_NO_WINDOW)
                except: pass
                time.sleep(1.5)
                
                lbl.configure(text="Apagado exitoso.\\nCerrando consola...")
                time.sleep(1)
            except Exception as e:
                pass
            
            # Cierre final
            os._exit(0)

        threading.Thread(target=_shutdown_task, daemon=True).start()'''

if old_on_close in content:
    content = content.replace(old_on_close, new_on_close)
    with open(path, 'w', encoding='utf-8') as f: f.write(content)
    print("on_close patched successfully.")
else:
    print("Could not find the exact old_on_close string.")
