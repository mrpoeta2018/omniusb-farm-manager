import sys
import os
import time
import io
import random

# Forzar UTF-8 en la consola para evitar errores de caracteres
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_log(msg):
    try:
        with open("DEBUG_STARTUP.txt", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except: pass
    print(f"[*] {msg}")

def speak(text):
    print(f"[VOZ] {text}")
    # Opcional: usar SAPI en Windows si est disponible
    try:
        import threading
        def _say():
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
            except: pass
        threading.Thread(target=_say, daemon=True).start()
    except: pass

# --- TEST DE VIDA INMEDIATO ---
print("\n" + "="*40)
print("OMNIUSB: INICIANDO MOTOR PYTHON...")
print("="*40)
print(f"[*] Carpeta: {os.getcwd()}")
print(f"[*] Python: {sys.version}")

try:
    import subprocess
    import traceback
    
    def log_error_and_die(err_msg):
        with open("LOG_CRITICO.txt", "w", encoding="utf-8") as f:
            f.write(f"=== ERROR CRÍTICO ===\n{err_msg}\n")
            traceback.print_exc(file=f)
        print(f"\n[X] ERROR: {err_msg}")
        input("\nPresiona ENTER para ver el error completo...")
        sys.exit(1)

    print("[*] Cargando librerías críticas...")
    import customtkinter as ctk
    import json
    import threading
    from tkinter import messagebox
    import requests
    
    print("[*] Cargando módulos internos...")
    from adb_manager import ADBManager
    from gnirehtet_runner import GnirehtetRunner
    from rotation_engine import RotationEngine
    from proxy_tester import ProxyTester
    from updater import check_for_updates_async, download_update, get_local_version
    from license_manager import get_hardware_id, validate_license
    from inventory_tool import InventoryWindow

except Exception as e:
    print(f"\n[!] FALLO CRÍTICO EN CARGA: {e}")
    traceback.print_exc()
    input("\nPresiona ENTER para cerrar...")
    sys.exit(1)

print("[*] Configurando interfaz visual...")
try:
    # Forzar modo oscuro directo evita que el módulo 'darkdetect' falle en PCs sin monitor (Headless/VPS)
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    # Forzar el escalado evita que Windows intente leer la resolución de un monitor inexistente
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)
except Exception as e:
    print(f"[!] Error de tema visual (ignorado): {e}")

_ACCESS_PASSWORD = "Androide10"

class LicenseValidationWindow(ctk.CTkToplevel):
    def __init__(self, master, on_success_callback):
        super().__init__(master)
        self.title("🔒 OmniUSB - Activación de Licencia")
        self.geometry("500x380")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(False, False)
        
        self.on_success = on_success_callback
        self.hwid = get_hardware_id()
        
        # UI
        ctk.CTkLabel(self, text="Verificación de Licencia", font=("Arial", 22, "bold"), text_color="#3B82F6").pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Software v4.1 - Protegido por HWID", font=("Arial", 12)).pack(pady=5)
        
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(padx=30, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="🔑 Tu Código de Máquina (HWID):", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        h_entry = ctk.CTkEntry(frame, width=200, justify="center")
        h_entry.pack(pady=5)
        h_entry.insert(0, self.hwid)
        h_entry.configure(state="readonly")
        
        ctk.CTkLabel(frame, text="🗝️ Introduce tu Licencia de Alquiler:", font=("Arial", 12, "bold")).pack(pady=(15, 0))
        self.key_entry = ctk.CTkEntry(frame, width=300, justify="center", placeholder_text="Ej: LIC-PABLO-1X9A")
        self.key_entry.pack(pady=5)
        
        self.status_lbl = ctk.CTkLabel(frame, text="", font=("Arial", 12))
        self.status_lbl.pack(pady=5)
        
        self.btn = ctk.CTkButton(self, text="Verificar y Entrar", fg_color="#10B981", height=40, font=("Arial", 14, "bold"), command=self.do_verify)
        self.btn.pack(pady=20, padx=30, fill="x")

    def on_close(self):
        sys.exit(0)

    def do_verify(self):
        k = self.key_entry.get().strip()
        if not k:
            self.status_lbl.configure(text="❌ Escribe una licencia.", text_color="red")
            return
            
        self.btn.configure(text="Comprobando...", state="disabled")
        self.status_lbl.configure(text="Conectando al servidor central...", text_color="yellow")
        
        def _check():
            ok, msg = validate_license(k, self.hwid)
            if not self.winfo_exists(): return
            
            self.btn.configure(text="Verificar y Entrar", state="normal")
            if ok:
                self.status_lbl.configure(text=msg, text_color="green")
                self.after(500, lambda: self.on_success(k))
            else:
                self.status_lbl.configure(text=msg, text_color="red")
                
        threading.Thread(target=_check, daemon=True).start()


class ReporteGlobalWindow(ctk.CTkToplevel):
    def __init__(self, master, adb, engine):
        super().__init__(master)
        self.title("🩺 Diagnóstico Global del Lote Activo")
        self.geometry("500x400")
        self.attributes("-topmost", True)
        
        self.adb = adb
        self.engine = engine
        
        ctk.CTkLabel(self, text="Verificando Conexiones en Curso...", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.log_box = ctk.CTkTextbox(self, width=450, height=300)
        self.log_box.pack(pady=10)
        
        threading.Thread(target=self.run_report, daemon=True).start()

    def run_report(self):
        activos = self.engine.active_devices.copy()
        if not activos:
            self.log_box.insert("end", "⚠️ No hay ningún celular activo en este momento.")
            return
            
        self.log_box.insert("end", f"[*] Escaneando salida de {len(activos)} celulares...\n\n")
        
        for dev in activos:
            s = dev['serial']
            cfg, ip = self.adb.get_real_ip(s)
            state = "🟢 OK" if "MUERTO" not in ip and "SIN" not in ip else "🔴 FALLA"
            self.log_box.insert("end", f"{state} | {s}\n   └─ {cfg}\n   └─ {ip}\n\n")
            self.log_box.see("end")

class ProxyTesterWindow(ctk.CTkToplevel):
    def __init__(self, master, proxies, callback_finish):
        super().__init__(master)
        self.title("🔍 Probador Láser de Proxies")
        self.geometry("600x450")
        self.attributes("-topmost", True)
        self.proxies = proxies
        self.callback_finish = callback_finish
        
        ctk.CTkLabel(self, text="Escaneando Proxies en Paralelo...", font=("Arial", 16, "bold")).pack(pady=10)
        self.progress = ctk.CTkProgressBar(self, width=500)
        self.progress.pack(pady=10)
        self.progress.set(0.0)
        
        self.status = ctk.CTkLabel(self, text="Verificando 0 / 0")
        self.status.pack(pady=5)
        
        self.log_box = ctk.CTkTextbox(self, width=550, height=250)
        self.log_box.pack(pady=10)
        
        threading.Thread(target=self.run_test, daemon=True).start()
        
    def add_log(self, text, color="white"):
        def _do():
            if not self.winfo_exists(): return
            self.log_box.insert("end", text + "\n")
            self.log_box.see("end")
        self.after(0, _do)

    def log_update(self, c, total, p, is_alive):
        def _do():
            if not self.winfo_exists(): return
            self.progress.set(c / total)
            self.status.configure(text=f"Verificados {c} de {total}")
            res = "🟢 VIVO" if is_alive else "🔴 MUERTO"
            self.log_box.insert("end", f"{res} | {p}\n")
            self.log_box.see("end")
        self.after(0, _do)
        
    def run_test(self):
        def _final(results):
            def _do():
                if not self.winfo_exists(): return
                a = len(results["alive"])
                d = len(results["dead"])
                self.log_box.insert("end", f"\n--- PRUEBA FINALIZADA ---\n✅ Vivos: {a}\n💥 Muertos: {d}\nLimpiando lista automáticamente en 3 segundos...\n")
                self.log_box.see("end")
            self.after(0, _do)
            time.sleep(3)
            self.after(0, lambda: self.callback_finish(results["alive"]))
            self.after(0, self.destroy)
            
        ProxyTester.test_proxies_async(self.proxies, self.log_update, _final)

class PanicProgressWindow(ctk.CTkToplevel):
    def __init__(self, master, engine, runner, adb):
        super().__init__(master)
        self.title("🧹 Limpieza Global en Progreso...")
        self.geometry("550x450")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.master = master
        self.engine = engine
        self.runner = runner
        self.adb = adb
        
        ctk.CTkLabel(self, text="EJECUTANDO PROTOCOLO PANIC", text_color="red", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=10)
        self.progress.set(0.0)
        
        self.status_box = ctk.CTkTextbox(self, width=450, height=200)
        self.status_box.pack(pady=10)
        self.status_box.insert("end", "[X] Escaneando procesos...\n")
        
        threading.Thread(target=self.run_cleanup, daemon=True).start()

    def log(self, text):
        def _do():
            if not self.winfo_exists(): return
            self.status_box.insert("end", text + "\n")
            self.status_box.see("end")
        self.after(0, _do)

    def do_nothing(self): pass
        
    def run_cleanup(self):
        time.sleep(1)
        self.progress.set(0.2)
        
        self.log("[✓] Deteniendo motor rotante...")
        self.engine.stop_rotation()
        time.sleep(1)
        
        self.progress.set(0.4)
        self.log("[✓] Deteniendo todos los Gnirehtet del PC...")
        self.runner.kill_all_gnirehtet()
        
        try:
            self.log("[✓] Destruyendo servidores NodeProxy...")
            self.engine.pm.stop_all()
        except: pass
        self.progress.set(0.6)
        
        devices = self.adb.list_devices()
        total = len(devices)
        if total == 0:
            self.progress.set(0.9)
        else:
            self.log(f"[✓] Apagando Wi-Fi en todos los celulares preventivamente...")
            for dev in devices:
                self.adb.run_command(["shell", "svc", "wifi", "disable"], dev['serial'])
                
            self.log(f"[✓] Verificando red 1 por 1 en {total} celulares...")
            success_count = 0
            failed_devices = []
            
            for i, dev in enumerate(devices):
                s = dev['serial']
                self.log(f"\n-> Limpiando y probando {s} ({i+1}/{total})...")
                
                self.runner.stop(s)
                self.adb.run_command(["shell", "am", "start", "-a", "com.genymobile.gnirehtet.STOP", "-n", "com.genymobile.gnirehtet/.GnirehtetActivity"], s)
                self.adb.run_command(["uninstall", "com.genymobile.gnirehtet"], s)
                self.adb.clear_global_proxy(s)
                self.adb.run_command(["shell", "settings", "put", "global", "captive_portal_mode", "0"], s)
                self.adb.run_command(["shell", "settings", "put", "global", "captive_portal_detection_enabled", "0"], s)
                self.adb.run_command(["reverse", "--remove-all"], s)
                
                self.adb.run_command(["shell", "svc", "wifi", "enable"], s)
                
                internet_ok = False
                for attempt in range(5):
                    time.sleep(2)
                    stdout, stderr, code = self.adb.run_command(["shell", "ping", "-c", "1", "-W", "2", "8.8.8.8"], s)
                    if code == 0:
                        internet_ok = True
                        break
                        
                if internet_ok:
                    self.log(f"   [✅] INTERNET OK. Abriendo Google...")
                    self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "https://www.google.com"], s)
                    time.sleep(2)
                    success_count += 1
                else:
                    self.log(f"   [❌] FALLO. No se pudo conectar a Internet.")
                    failed_devices.append(s)
                    
                self.adb.run_command(["shell", "svc", "wifi", "disable"], s)
                
                p = 0.6 + (0.3 * ((i+1)/total))
                self.after(0, lambda val=p: self.progress.set(val) if self.winfo_exists() else None)

        self.after(0, lambda: self.progress.set(1.0) if self.winfo_exists() else None)
        self.log(f"\n✅ ¡PANIC COMPLETADO! Se probaron {total} celulares.")
        self.log(f"🟢 Exitosos: {success_count} | 🔴 Fallidos: {len(failed_devices)}")
        if failed_devices:
            self.log(f"Revisar manual: {', '.join(failed_devices)}")
        self.log("⚠️ NOTA: El Wi-Fi quedó APAGADO. Actívalo manualmente.")
        
        self.after(0, lambda: self.master.log_msg("Protocolo a prueba de fallos finalizado.", "warn"))
        self.after(0, lambda: self.master.status_lbl.configure(text="Estado: LIMPIO 🧽"))
        self.after(0, lambda: self.master.start_btn.configure(state="normal"))
        self.after(0, lambda: self.master.pause_btn.configure(state="disabled", text="⏸️ PAUSAR"))
        self.after(0, lambda: self.master.clean_btn.configure(state="normal"))
        
        # Restore close button and auto-destroy after 3 seconds
        self.after(0, lambda: self.protocol("WM_DELETE_WINDOW", self.destroy))
        def _add_btn():
            if not self.winfo_exists(): return
            btn = ctk.CTkButton(self, text="Cerrar Ventana", command=self.destroy, fg_color="#EF4444")
            btn.pack(pady=10)
        self.after(0, _add_btn)
        self.after(3000, self.destroy)

class ScanProgressWindow(ctk.CTkToplevel):
    def __init__(self, master, adb_manager, finish_cb):
        super().__init__(master)
        self.title("🔍 Escaneando Dispositivos")
        self.geometry("500x350")
        self.attributes("-topmost", True)
        
        self.master = master
        self.adb = adb_manager
        self.finish_cb = finish_cb
        
        ctk.CTkLabel(self, text="RECONOCIENDO HARDWARE", text_color="#F59E0B", font=("Arial", 16, "bold")).pack(pady=15)
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0.1)
        self.progress.pack(pady=10)
        
        self.status_lbl = ctk.CTkLabel(self, text="Enviando señales ADB...")
        self.status_lbl.pack(pady=5)
        
        self.tip_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.tip_frame.pack(fill="x", padx=25, pady=20)
        self.tip_lbl = ctk.CTkLabel(self.tip_frame, text=self.master.tips[0], wraplength=450)
        self.tip_lbl.pack(pady=10)
        
        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        self.progress.set(0.3)
        self.after(500, lambda: self.status_lbl.configure(text="Esperando respuesta de hubs USB..."))
        devs = self.adb.list_devices() # This also fetches models now
        self.progress.set(0.8)
        self.after(500, lambda: self.status_lbl.configure(text=f"¡Encontrados {len(devs)} teléfonos!"))
        time.sleep(1)
        self.after(0, self.finish_cb, devs)
        self.destroy()

class SetupProgressWindow(ctk.CTkToplevel):
    def __init__(self, master, devices, proxies, b_size, mins, tunnel_disabled=False):
        super().__init__(master)
        self.title("🚀 Iniciando Granja de Proxies")
        self.geometry("600x480")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        self.master = master
        self.devices = devices
        self.proxies = proxies
        self.b_size = b_size
        self.mins = mins
        self.tunnel_disabled = tunnel_disabled
        
        if tunnel_disabled:
            ctk.CTkLabel(self, text="MODO SOLO BOT (WIFI ACTIVO)", text_color="#38BDF8", font=("Arial", 18, "bold")).pack(pady=15)
        else:
            ctk.CTkLabel(self, text="MODO ARRANQUE ACTIVO", text_color="#3B82F6", font=("Arial", 18, "bold")).pack(pady=15)
        
        self.progress = ctk.CTkProgressBar(self, width=500)
        self.progress.pack(pady=10)
        self.progress.set(0.05)
        
        self.status_lbl = ctk.CTkLabel(self, text="Inicializando componentes...", font=("Arial", 12, "italic"))
        self.status_lbl.pack(pady=5)
        
        self.log_box = ctk.CTkTextbox(self, width=550, height=200)
        self.log_box.pack(pady=10)
        
        self.tip_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.tip_frame.pack(fill="x", padx=25, pady=10)
        self.tip_lbl = ctk.CTkLabel(self.tip_frame, text=self.master.tips[0], wraplength=500)
        self.tip_lbl.pack(pady=10)
        
        self.disable_master_buttons()
        threading.Thread(target=self.run_setup, daemon=True).start()
        threading.Thread(target=self.rotate_tips, daemon=True).start()

    def do_nothing(self): pass

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def disable_master_buttons(self):
        self.master.start_btn.configure(state="disabled")
        self.master.scan_btn.configure(state="disabled")
        self.master.install_btn.configure(state="disabled")
        self.master.clean_btn.configure(state="disabled")

    def enable_master_buttons(self):
        self.master.start_btn.configure(state="disabled") # starts stays off while running
        self.master.pause_btn.configure(state="normal")
        self.master.scan_btn.configure(state="normal") 
        self.master.clean_btn.configure(state="normal")

    def rotate_tips(self):
        while self.winfo_exists():
            time.sleep(6)
            if self.winfo_exists():
                self.after(0, lambda: self.tip_lbl.configure(text=random.choice(self.master.tips)))

    def run_setup(self):
        self.log("[*] Paso 1: Iniciando y validando dependencias...")
        self.status_lbl.configure(text="Iniciando entorno local (Previene errores de red)...")
        if not self.tunnel_disabled:
            self.master.engine.pm.download_if_missing()
        self.progress.set(0.2)
        time.sleep(1)
        
        if self.tunnel_disabled:
            self.log("[*] Paso 2: (Saltado) Modo Solo Bot activado. Manteniendo Wi-Fi activo.")
            self.progress.set(0.5)
            self.log("[*] Paso 3: Configurando Rotación Lógica...")
            self.status_lbl.configure(text="Iniciando motores lógicos...")
        else:
            self.log("[*] Paso 2: Desactivando Wi-Fi escalonadamente (Previene saturación del Hub USB)...")
            threads = []
            total = len(self.devices)
            for i, d in enumerate(self.devices):
                def _kill(serial=d['serial']):
                    self.master.adb.run_command(["shell", "svc", "wifi", "disable"], serial)
                    self.master.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
                t = threading.Thread(target=_kill)
                t.start()
                threads.append(t)
                self.progress.set(0.2 + (0.3 * ((i+1)/total)))
                self.status_lbl.configure(text=f"Desconectando Wi-Fi (Protegiendo Hardware) {i+1}/{total}...")
            
            for t in threads: t.join()
            self.log("[✓] Hardware seguro: Wi-Fi bloqueado en todos los dispositivos.")
            
            self.log("[*] Paso 3: Configurando Túneles y Proxies (Pausando para no crashear ADB)...")
            self.status_lbl.configure(text="Inyectando túneles ADB Reverse de forma segura...")
        
        self.progress.set(0.6)
        
        # Start rotation on main thread via after
        playlists_raw = self.master.playlist_textbox.get("1.0", "end").strip().split('\n')
        playlists = [p.strip() for p in playlists_raw if p.strip()]
        
        self.after(0, lambda: self.master.engine.start_rotation(
            self.devices, self.proxies, self.b_size, self.mins, 
            self.master.infinite_var.get(), self.master.stealth_var.get(), playlists, tunnel_disabled=self.tunnel_disabled
        ))
        
        self.progress.set(0.9)
        time.sleep(2)
        self.progress.set(1.0)
        self.log("\n✅ ¡SISTEMA OPERATIVO Y PROTEGIDO!")
        self.status_lbl.configure(text="Lanzamiento completado con éxito.")
        
        self.enable_master_buttons()
        # Restore close button and add button
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        btn = ctk.CTkButton(self, text="Perfecto, Continuar", command=self.destroy, fg_color="#10B981")
        btn.pack(pady=10)
        self.after(4000, self.destroy)

class ProxyAssignmentWindow(ctk.CTkToplevel):
    def __init__(self, master, devices, proxies):
        super().__init__(master)
        self.title("🎯 Mapeado Manual de Proxies")
        self.geometry("800x600")
        self.attributes("-topmost", True)
        
        self.master = master
        self.devices = devices
        self.proxies = proxies # Formatted list
        self.entries = {} # serial -> StringVar
        
        ctk.CTkLabel(self, text="ASIGNACIÓN DISPOSITIVO <-> PROXY", font=("Arial", 20, "bold"), text_color="#3B82F6").pack(pady=20)
        
        # Scrollable area
        self.scroll = ctk.CTkScrollableFrame(self, width=750, height=400)
        self.scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        for dev in self.devices:
            s = dev['serial']
            row = ctk.CTkFrame(self.scroll, fg_color="#1E1E1E", corner_radius=5)
            row.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(row, text=f"{dev.get('model','Phone')} ({s})", width=250, anchor="w").pack(side="left", padx=10)
            
            p_var = ctk.StringVar(value=self.master.engine.custom_mapping.get(s, ""))
            self.entries[s] = p_var
            
            combo = ctk.CTkComboBox(row, values=["(Automático)"] + self.proxies, variable=p_var, width=400)
            combo.pack(side="left", padx=10, pady=5)

        # Buttons
        btn_fr = ctk.CTkFrame(self, fg_color="transparent")
        btn_fr.pack(pady=20)
        
        ctk.CTkButton(btn_fr, text="🎲 Mapeado Automático (1 a 1)", command=self.auto_map, fg_color="#6366F1").pack(side="left", padx=10)
        ctk.CTkButton(btn_fr, text="💾 Guardar Mapeado", command=self.save_map, fg_color="#10B981").pack(side="left", padx=10)
        ctk.CTkButton(btn_fr, text="❌ Limpiar Todo", command=self.clear_map, fg_color="#EF4444").pack(side="left", padx=10)

    def auto_map(self):
        for i, s in enumerate(self.entries.keys()):
            if i < len(self.proxies):
                self.entries[s].set(self.proxies[i])
            else:
                self.entries[s].set("(Automático)")

    def clear_map(self):
        for var in self.entries.values():
            var.set("(Automático)")

    def save_map(self):
        new_map = {}
        for s, var in self.entries.items():
            val = var.get()
            if val and val != "(Automático)":
                new_map[s] = val
        self.master.engine.custom_mapping = new_map
        self.master.log_msg(f"🎯 Mapeado guardado: {len(new_map)} dispositivos asignados manualmente.")
        self.destroy()

class ProxyFarmApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OmniUSB Director 🌍 [Stealth Proxy Edition]")
        self.geometry("1200x900")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print("[*] Iniciando ADB y Gnirehtet...")
        debug_log("Creando instancia ProxyFarmApp")
        speak("Cargando componentes de red")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.adb = ADBManager(os.path.join(base_dir, "platform-tools", "adb.exe"))
        self.runner = GnirehtetRunner(executable_path=os.path.join(base_dir, "gnirehtet.exe"))
        debug_log("Motores ADB/Runner listos")
        self.engine = RotationEngine(self.adb, self.runner, self.on_update_callback if hasattr(self, "on_update_callback") else self.on_engine_update, app_instance=self)
        
        self.no_proxy_strikes = 0
        self.scanned_devices = []  # Stores last scan results
        self.device_selections = {}  # serial -> BooleanVar (checkbox state)
        self.is_compact = False  # Compact mode state
        self.bot_enabled = ctk.BooleanVar(value=False)
        self.bot_interval = ctk.StringVar(value="5")
        self.device_locks = {} # serial -> timestamp (until when is it busy)

        # Master Rotation State
        self.master_mode = ctk.StringVar(value="spotify") # "spotify", "youtube", "mixed"
        self.master_mode.trace_add("write", lambda *args: self.update_ui_state())
        self.mixed_turn = "spotify"

        self.media_rotation_active = ctk.BooleanVar(value=True) # Media Injection On/Off
        
        # Obsolete network rotation state
        self.network_rotation_enabled = ctk.BooleanVar(value=False)
        self.network_rotation_enabled.trace_add("write", lambda *args: self.update_ui_state())

        # Interval states
        self.playlist_interval = ctk.StringVar(value="60") # in minutes
        self.next_injection_time = time.time()
        
        self.youtube_drip_var = ctk.BooleanVar(value=True) # Human Drip Mode
        
        # Anti-Bot Shield (Watchdog & Ghost)
        self.watchdog_enabled = ctk.BooleanVar(value=True)
        self.ghost_enabled = ctk.BooleanVar(value=True)

        # Handle window close: cleanup all processes
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=5, padx=10)
        title = ctk.CTkLabel(self.header_frame, text="🛸 OmniUSB Panel Central", font=("Arial", 22, "bold"))
        title.pack(side="left", padx=10)
        self.compact_btn = ctk.CTkButton(self.header_frame, text="📏 Compacto", width=100, height=28, command=self.toggle_compact, fg_color="#374151", hover_color="#4B5563")
        self.compact_btn.pack(side="left", padx=10)
        self.status_lbl = ctk.CTkLabel(self.header_frame, text="Estado: ESPERANDO... 🌙", text_color="yellow")
        self.status_lbl.pack(side="right", padx=10)
        
        self.tabview = ctk.CTkTabview(self, width=1150, height=800)
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        self.tab_ctrl = self.tabview.add("🎛️ Panel de Control")
        self.tab_traf = self.tabview.add("📊 Tráfico de Datos en Vivo")
        self.tab_extras = self.tabview.add("🎸 Plataformas Extra")
        self.tab_accounts = self.tabview.add("👤 Creador de Cuentas")
        
        self.batch_size_sync_id = None
        self.tips = [
            "💡 Consejo: Activa 'Modo Sigilo (Goteo)' si usas proxies móviles para evitar baneos simultáneos.",
            "💡 Consejo: Revisa la luz de salud. Si está Naranja, el sistema se estabilizará solo.",
            "💡 Consejo: Entra a WhatsApp o Instagram directo desde el celular usando SCRCPY ('Pantalla')."
        ]

        self.last_ip_check = {}
        self.device_health = {}
        self.health_fail_count = {}

        # Iniciar visible para evitar error de "ventana escondida" en algunas PCs
        print("[*] Cargando Interfaz Principal...")
        # self.withdraw() # Comentado para estabilidad
        self.check_saved_license_and_boot()

    def check_saved_license_and_boot(self):
        debug_log("Saltando comprobación de licencia a petición del usuario...")
        self.after(0, self._finalize_boot, "FREE_VERSION")

    def _show_license_window(self):
        LicenseValidationWindow(self, self._finalize_boot)

    def bind_tooltip(self, widget, text):
        import tkinter as tk
        def on_enter(e):
            widget.tooltip_window = tk.Toplevel(widget)
            widget.tooltip_window.wm_overrideredirect(True)
            # Posicionar el tooltip un poco a la derecha y abajo del cursor
            widget.tooltip_window.wm_geometry(f"+{e.x_root + 15}+{e.y_root + 15}")
            widget.tooltip_window.attributes("-topmost", True)
            
            # Usar un Frame de tkinter nativo o un label nativo para que se adapte al Toplevel limpio,
            # pero como es Toplevel, CTkLabel funciona perfectamente.
            label = ctk.CTkLabel(widget.tooltip_window, text=text, font=("Arial", 12, "bold"), fg_color="#1E293B", text_color="#38BDF8", corner_radius=6)
            # El padding en CTkLabel se maneja en el pack o pasándole height/width, pero padx/pady en pack funciona.
            label.pack(padx=10, pady=5)
            
        def on_leave(e):
            if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
                widget.tooltip_window.destroy()
                widget.tooltip_window = None
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def lock_device(self, serial, duration_seconds=40):
        self.device_locks[serial] = time.time() + duration_seconds

    def is_device_locked(self, serial):
        if serial not in self.device_locks:
            return False
        return time.time() < self.device_locks[serial]

    def _finalize_boot(self, valid_key):
        debug_log("Finalizando arranque...")
        speak("Acceso concedido. Abriendo panel de control.")
        # Guardar clave válida
        try:
            doc = {}
            if os.path.exists("config.json"):
                with open("config.json", "r") as f: doc = json.load(f)
            doc["license_key"] = valid_key
            with open("config.json", "w") as f: json.dump(doc, f)
        except: pass
        self.build_control_tab()
        self.build_traffic_tab()
        self.build_extras_tab()
        self.build_accounts_tab()

        self.deiconify()
        print("[+] ¡Interfaz Abierta con Éxito!")
        self.log_msg("✅ Sistema iniciado. Bienvenido.")
        
        self.load_config()
        self.tips = [
            "💡 TIP: Asegúrate de usar cables USB de buena calidad para los 40 móviles.",
            "💡 TIP: Si un teléfono falla, revisa que no tenga un aviso de 'Permitir depuración' en pantalla.",
            "💡 TIP: El icono de llave 🔑 debe aparecer en la barra de estado de los celulares.",
            "💡 TIP: No desconectes el HUB USB mientras el túnel esté activo.",
            "💡 TIP: Puedes ver el consumo de cada móvil en la pestaña 'Tráfico en Vivo'."
        ]
        
        self.device_ui_map = {} # serial -> {ip_lbl, timer_lbl, traffic_lbl, health_lbl}
        self.device_health = {} # serial -> {status: "ok"|"warning"|"dead"|"offline", reason: str}
        self.health_fail_count = {} # serial -> consecutive failure count
        self.last_ip_check = {} # serial -> timestamp
        self.update_bar = None  # Update notification bar
        self.update_timer()
        self.update_traffic()
        self._check_updates()
        threading.Thread(target=self.media_bot_loop, daemon=True).start()
        threading.Thread(target=self.media_rotator_loop, daemon=True).start()
        threading.Thread(target=self.watchdog_ghost_loop, daemon=True).start()

    def toggle_compact(self):
        """Alterna entre modo completo y modo bolsillo (solo controles)."""
        if self.is_compact:
            # Restaurar modo completo
            self.is_compact = False
            ctk.set_widget_scaling(1.0)
            self.geometry("1200x900")
            self.compact_btn.configure(text="📏 Bolsillo")
            self._right_container.grid(row=1, column=1, pady=10, padx=10, sticky="nsew")
            self.log_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
            self.proxy_textbox.configure(height=120)
            self.tab_ctrl.grid_columnconfigure(1, weight=2)
        else:
            # Modo bolsillo: solo columna de controles, sin log ni tarjetas
            self.is_compact = True
            ctk.set_widget_scaling(0.77)
            self.geometry("480x700")
            self.compact_btn.configure(text="📐 Completo")
            self._right_container.grid_remove()
            self.log_frame.grid_remove()
            self.proxy_textbox.configure(height=50)
            self.tab_ctrl.grid_columnconfigure(1, weight=0)

    def _check_updates(self):
        """Check for updates in background on startup."""
        def _on_result(has_update, remote_info):
            if has_update and remote_info:
                self.after(0, self._show_update_bar, remote_info)
        check_for_updates_async(_on_result)

    def _show_update_bar(self, remote_info):
        """Show a subtle update notification bar at the top."""
        local = get_local_version()
        self.update_bar = ctk.CTkFrame(self, fg_color="#065F46", corner_radius=0, height=36)
        self.update_bar.pack(fill="x", before=self.tabview)
        ctk.CTkLabel(self.update_bar, text=f"🆕 Nueva versión {remote_info.get('version', '?')} disponible (actual: {local.get('version', '?')})", font=("Arial", 12, "bold")).pack(side="left", padx=15)
        download_url = remote_info.get("download_url", "")
        if download_url:
            ctk.CTkButton(self.update_bar, text="⬇️ Actualizar", width=120, height=26, fg_color="#10B981",
                          command=lambda: self._do_update(download_url)).pack(side="right", padx=10, pady=5)
        ctk.CTkButton(self.update_bar, text="✕", width=30, height=26, fg_color="transparent",
                      command=self.update_bar.destroy).pack(side="right", padx=5, pady=5)

    def _do_update(self, url):
        """Download and install update."""
        self.log_msg("⬇️ Descargando actualización...", "warn")
        def _progress(msg):
            self.after(0, lambda: self.log_msg(f"  {msg}"))
        def _done(success, msg):
            if success:
                self.after(0, lambda: self.log_msg(f"✅ {msg}"))
                self.after(0, lambda: messagebox.showinfo("Actualización", f"{msg}\nCierra y vuelve a abrir START_APP.bat"))
            else:
                self.after(0, lambda: self.log_msg(f"❌ {msg}", "error"))
        download_update(url, _progress, _done)

    def on_close(self):
        """Clean up all child processes before closing the window."""
        try:
            self.engine.stop_rotation()
            self.runner.kill_all_gnirehtet()
            self.engine.pm.stop_all()
        except Exception:
            pass
        self.destroy()

    def media_bot_loop(self):
        import random
        device_states = {} # serial -> {"next_action_time": float, "songs_played": int}
        
        while True:
            time.sleep(2)
            try:
                if not self.bot_enabled.get():
                    device_states.clear()
                    continue
            except Exception:
                break
                
            devices = self.adb.list_devices()
            current_time = time.time()
            
            for dev in devices:
                try:
                    if not self.bot_enabled.get(): break
                except Exception: break
                
                s = dev['serial']
                if s not in device_states:
                    device_states[s] = {
                        "next_action_time": current_time + random.uniform(30, 210), # Random initial offset
                        "songs_played": random.randint(0, 4)
                    }
                    
                state = device_states[s]
                
                # Check DND semaphore
                if self.is_device_locked(s):
                    continue
                
                if current_time >= state["next_action_time"]:
                    try:
                        self.adb.run_command(["shell", "input", "keyevent", "87"], s)
                    except: pass
                    
                    state["songs_played"] += 1
                    
                    # Decidir si la próxima es salto rápido o canción entera
                    if state["songs_played"] >= random.randint(6, 8):
                        # Impaciente: Escucha entre 40 y 60 segundos
                        state["next_action_time"] = current_time + random.uniform(40, 60)
                        state["songs_played"] = 0
                    else:
                        # Canción completa: ~3.5 minutos (200 - 220 segundos)
                        state["next_action_time"] = current_time + random.uniform(200, 220)

    def update_live_status(self):
        try:
            if not hasattr(self, 'media_rotation_active'): return
            if not self.media_rotation_active.get():
                self.live_status_var.set("Estado: ⏸️ INYECCIÓN AUTOMÁTICA APAGADA")
                return
                
            mode = self.master_mode.get()
            mode_str = mode
            if mode == "spotify": mode_str = "🟢 SOLO SPOTIFY"
            elif mode == "yt_music": mode_str = "🟣 SOLO YT MUSIC"
            elif mode == "yt_video": mode_str = "🔴 SOLO YT VIDEO"
            elif mode == "mixed": 
                # Add sub-state if mixed
                sub = getattr(self, '_last_mixed_mode', None)
                if sub == "spotify": mode_str = "🟡 MIXTO -> 🟢 Spotify"
                elif sub == "yt_music": mode_str = "🟡 MIXTO -> 🟣 YT Music"
                elif sub == "yt_video": mode_str = "🟡 MIXTO -> 🔴 YT Video"
                else: mode_str = "🟡 MODO MIXTO"
            
            shield_active = self.watchdog_enabled.get() or self.ghost_enabled.get() or self.bot_enabled.get()
            shield_str = "🛡️ ON" if shield_active else "⚠️ OFF"
            
            if getattr(self, 'is_injecting', False):
                self.live_status_var.set(f"Estado: {mode_str} | Próxima inyección: ⏳ INYECTANDO... | Escudo: {shield_str}")
            else:
                remaining = int(self.next_injection_time - time.time())
                if remaining < 0: remaining = 0
                mins, secs = divmod(remaining, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                self.live_status_var.set(f"Estado: {mode_str} | Próxima inyección: ⏱️ {time_str} | Escudo: {shield_str}")
        except:
            pass

    def media_rotator_loop(self):
        import random
        while True:
            time.sleep(1)
            self.update_live_status()
            
            try:
                if not hasattr(self, 'media_rotation_active'): continue
                if not self.media_rotation_active.get(): continue
                
                # Check if it's time to inject
                if time.time() >= self.next_injection_time and not getattr(self, 'is_injecting', False):
                    self.is_injecting = True
                    
                    mode = self.master_mode.get()
                    active_mode = mode
                    
                    if mode == "mixed":
                        self._last_mixed_mode = "mixed_simultaneous"
                        self._trigger_auto_mixed()
                    elif mode == "spotify":
                        self._trigger_auto_spotify()
                    elif mode == "yt_music":
                        self._trigger_auto_yt_music()
                    elif mode == "yt_video":
                        self._trigger_auto_yt_video()
                        
                    # Finalize injection after 42 seconds to allow devices to fully load
                    self.after(42000, self._finalize_injection)
                        
            except Exception as e:
                pass

    def _finalize_injection(self):
        try:
            interval_minutes = float(self.playlist_interval.get())
        except ValueError:
            interval_minutes = 60.0
            
        self.next_injection_time = time.time() + (interval_minutes * 60)
        self.is_injecting = False

    def _trigger_auto_spotify(self):
        playlists = [p.strip() for p in self.playlist_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
        if playlists:
            if not hasattr(self, 'rot_index_spotify'): self.rot_index_spotify = 0
            self.rot_index_spotify = self.rot_index_spotify % len(playlists)
            current = playlists[self.rot_index_spotify]
            self.rot_index_spotify += 1
            
            self.after(0, lambda p=current: self.log_msg(f"🎧 [AUTO] Inyectando Spotify: {p[:30]}...", "info"))
            self._inject_playlist_to_active(current)

    def _trigger_auto_yt_music(self):
        urls = [p.strip() for p in self.ytmusic_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
        if urls:
            if not hasattr(self, 'rot_index_ytmusic'): self.rot_index_ytmusic = 0
            self.rot_index_ytmusic = self.rot_index_ytmusic % len(urls)
            current = urls[self.rot_index_ytmusic]
            self.rot_index_ytmusic += 1
            
            self.after(0, lambda u=current: self.log_msg(f"🟣 [AUTO] Inyectando YT Music: {u[:30]}...", "info"))
            self._inject_youtube_to_active(current)
            
    def _trigger_auto_yt_video(self):
        urls = [p.strip() for p in self.youtube_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
        if urls:
            if not hasattr(self, 'rot_index_ytvideo'): self.rot_index_ytvideo = 0
            self.rot_index_ytvideo = self.rot_index_ytvideo % len(urls)
            current = urls[self.rot_index_ytvideo]
            self.rot_index_ytvideo += 1
            
            if self.youtube_drip_var.get():
                if hasattr(self, 'engine') and self.engine.active_devices:
                    import random
                    dev = random.choice(self.engine.active_devices)
                    self.after(0, lambda d=dev['serial'][-4:], u=current: self.log_msg(f"💧 Goteo YT Video en {d}: {u[:30]}...", "info"))
                    self._inject_youtube_to_single(dev['serial'], current)
            else:
                self.after(0, lambda u=current: self.log_msg(f"🔴 [AUTO] Inyectando YT Video Masivo: {u[:30]}...", "info"))
                self._inject_youtube_to_active(current)

    def _trigger_auto_mixed(self):
        playlists_raw = self.playlist_textbox.get("1.0", "end").strip().split('\n')
        spot_urls = [p.strip() for p in playlists_raw if p.strip()]
        
        ytm_raw = self.ytmusic_textbox.get("1.0", "end").strip().split('\n')
        ytm_urls = [p.strip() for p in ytm_raw if p.strip()]
        
        yt_raw = self.youtube_textbox.get("1.0", "end").strip().split('\n')
        yt_urls = [p.strip() for p in yt_raw if p.strip()]
        
        awa_urls = [p.strip() for p in (self.awa_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'awa_textbox') else []) if p.strip()]
        sc_urls = [p.strip() for p in (self.sc_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'sc_textbox') else []) if p.strip()]
        pan_urls = [p.strip() for p in (self.pan_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'pan_textbox') else []) if p.strip()]
        am_urls = [p.strip() for p in (self.am_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'am_textbox') else []) if p.strip()]
        apl_urls = [p.strip() for p in (self.apl_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'apl_textbox') else []) if p.strip()]
        
        active_pools = []
        if spot_urls and (not hasattr(self, 'use_spotify') or self.use_spotify.get()): active_pools.append(("spotify", spot_urls))
        if ytm_urls and (not hasattr(self, 'use_ytmusic') or self.use_ytmusic.get()): active_pools.append(("yt_music", ytm_urls))
        if yt_urls and (not hasattr(self, 'use_ytvideo') or self.use_ytvideo.get()): active_pools.append(("yt_video", yt_urls))
        if awa_urls and (not hasattr(self, 'use_awa') or self.use_awa.get()): active_pools.append(("awa", awa_urls, "fm.awa.app"))
        if sc_urls and (not hasattr(self, 'use_sc') or self.use_sc.get()): active_pools.append(("soundcloud", sc_urls, "com.soundcloud.android"))
        if pan_urls and (not hasattr(self, 'use_pan') or self.use_pan.get()): active_pools.append(("pandora", pan_urls, "com.pandora.android"))
        if am_urls and (not hasattr(self, 'use_am') or self.use_am.get()): active_pools.append(("audiomack", am_urls, "com.audiomack"))
        if apl_urls and (not hasattr(self, 'use_apl') or self.use_apl.get()): active_pools.append(("applemusic", apl_urls, "com.apple.android.music"))
        
        if len(active_pools) < 2:
            self.log_msg("⚠️ [AUTO MIXTO] Necesitas tener al menos DOS cajas activadas y con enlaces.", "warn")
            return
            
        if hasattr(self, 'engine') and self.engine.active_devices:
            self.log_msg(f"⚖️ [AUTO MIXTO] Dividiendo la granja en {len(active_pools)} plataformas...", "info")
            import random
            
            def _mass_inject():
                # Randomize devices so they don't always get the same platform on every rotation
                devices = list(self.engine.active_devices)
                random.shuffle(devices)
                
                for i, dev in enumerate(devices):
                    pool_data = active_pools[i % len(active_pools)]
                    pool_type = pool_data[0]
                    pool_urls = pool_data[1]
                    
                    if pool_type == "spotify":
                        if not hasattr(self, 'rot_index_spotify'): self.rot_index_spotify = 0
                        self.rot_index_spotify = self.rot_index_spotify % len(pool_urls)
                        rnd_url = pool_urls[self.rot_index_spotify]
                        self.rot_index_spotify += 1
                        self._inject_playlist_to_single(dev['serial'], rnd_url)
                    elif pool_type == "yt_music":
                        if not hasattr(self, 'rot_index_ytmusic'): self.rot_index_ytmusic = 0
                        self.rot_index_ytmusic = self.rot_index_ytmusic % len(pool_urls)
                        rnd_url = pool_urls[self.rot_index_ytmusic]
                        self.rot_index_ytmusic += 1
                        self._inject_youtube_to_single(dev['serial'], rnd_url)
                    elif pool_type == "yt_video":
                        if not hasattr(self, 'rot_index_ytvideo'): self.rot_index_ytvideo = 0
                        self.rot_index_ytvideo = self.rot_index_ytvideo % len(pool_urls)
                        rnd_url = pool_urls[self.rot_index_ytvideo]
                        self.rot_index_ytvideo += 1
                        self._inject_youtube_to_single(dev['serial'], rnd_url)
                    else:
                        package = pool_data[2]
                        rnd_url = random.choice(pool_urls)
                        self._inject_generic_audio_to_single(dev['serial'], rnd_url, package)
                        
                    time.sleep(1.5)
            threading.Thread(target=_mass_inject, daemon=True).start()

    def inject_manual_playlist(self):
        # Reset the automatic timer to prevent collisions
        try:
            interval_minutes = float(self.playlist_interval.get())
        except ValueError:
            interval_minutes = 60.0
        self.next_injection_time = time.time() + (interval_minutes * 60)
        self.mixed_turn = "youtube" # If mixed, next one should be youtube
        
        playlists_raw = self.playlist_textbox.get("1.0", "end").strip().split('\n')
        playlists = [p.strip() for p in playlists_raw if p.strip()]
        if not playlists:
            self.log_msg("⚠️ No hay listas de Spotify para inyectar", "warn")
            return
            
        if hasattr(self, 'engine') and self.engine.active_devices:
            self.log_msg("🎧 [MANUAL] Inyectando Playlists de Spotify...", "info")
            import random
            def _mass_inject():
                for dev in self.engine.active_devices:
                    rnd_url = random.choice(playlists)
                    self._inject_playlist_to_single(dev['serial'], rnd_url)
                    time.sleep(1.5)
            threading.Thread(target=_mass_inject, daemon=True).start()
        else:
            self.log_msg("⚠️ El túnel no está iniciado.", "warn")

    def inject_manual_ytmusic(self):
        try:
            interval_minutes = float(self.playlist_interval.get())
        except ValueError:
            interval_minutes = 60.0
        self.next_injection_time = time.time() + (interval_minutes * 60)
        
        urls_raw = self.ytmusic_textbox.get("1.0", "end").strip().split('\n')
        urls = [p.strip() for p in urls_raw if p.strip()]
        if not urls:
            self.log_msg("⚠️ No hay listas de YT Music para inyectar", "warn")
            return
            
        if hasattr(self, 'engine') and self.engine.active_devices:
            self.log_msg("🟣 [MANUAL] Inyectando YT Music Masivo...", "info")
            import random
            
            def _mass_inject():
                for dev in self.engine.active_devices:
                    rnd_url = random.choice(urls)
                    self._inject_youtube_to_single(dev['serial'], rnd_url)
                    time.sleep(1.5)
            threading.Thread(target=_mass_inject, daemon=True).start()
        else:
            self.log_msg("⚠️ El túnel no está iniciado.", "warn")

    def inject_manual_youtube(self):
        # Reset the automatic timer to prevent collisions
        try:
            interval_minutes = float(self.playlist_interval.get())
        except ValueError:
            interval_minutes = 60.0
        self.next_injection_time = time.time() + (interval_minutes * 60)
        self.mixed_turn = "spotify" # If mixed, next one should be spotify
        
        urls_raw = self.youtube_textbox.get("1.0", "end").strip().split('\n')
        urls = [p.strip() for p in urls_raw if p.strip()]
        if not urls:
            self.log_msg("⚠️ No hay listas de YouTube para inyectar", "warn")
            return
            
        if hasattr(self, 'engine') and self.engine.active_devices:
            self.log_msg(f"📺 [MANUAL] Inyectando YouTube Masivo...", "info")
            import random
            def _mass_inject():
                for dev in self.engine.active_devices:
                    rnd_url = random.choice(urls)
                    self._inject_youtube_to_single(dev['serial'], rnd_url)
                    time.sleep(1.5)
            threading.Thread(target=_mass_inject, daemon=True).start()
        else:
            self.log_msg("⚠️ El túnel no está iniciado.", "warn")

    def inject_manual_mixed(self):
        # Reset the automatic timer to prevent collisions
        try:
            interval_minutes = float(self.playlist_interval.get())
        except ValueError:
            interval_minutes = 60.0
        self.next_injection_time = time.time() + (interval_minutes * 60)
        
        playlists_raw = self.playlist_textbox.get("1.0", "end").strip().split('\n')
        spot_urls = [p.strip() for p in playlists_raw if p.strip()]
        
        ytm_raw = self.ytmusic_textbox.get("1.0", "end").strip().split('\n')
        ytm_urls = [p.strip() for p in ytm_raw if p.strip()]
        
        yt_raw = self.youtube_textbox.get("1.0", "end").strip().split('\n')
        yt_urls = [p.strip() for p in yt_raw if p.strip()]
        
        awa_urls = [p.strip() for p in (self.awa_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'awa_textbox') else []) if p.strip()]
        sc_urls = [p.strip() for p in (self.sc_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'sc_textbox') else []) if p.strip()]
        pan_urls = [p.strip() for p in (self.pan_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'pan_textbox') else []) if p.strip()]
        am_urls = [p.strip() for p in (self.am_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'am_textbox') else []) if p.strip()]
        apl_urls = [p.strip() for p in (self.apl_textbox.get("1.0", "end").strip().split('\n') if hasattr(self, 'apl_textbox') else []) if p.strip()]
        
        active_pools = []
        if spot_urls and (not hasattr(self, 'use_spotify') or self.use_spotify.get()): active_pools.append(("spotify", spot_urls))
        if ytm_urls and (not hasattr(self, 'use_ytmusic') or self.use_ytmusic.get()): active_pools.append(("yt_music", ytm_urls))
        if yt_urls and (not hasattr(self, 'use_ytvideo') or self.use_ytvideo.get()): active_pools.append(("yt_video", yt_urls))
        if awa_urls and (not hasattr(self, 'use_awa') or self.use_awa.get()): active_pools.append(("awa", awa_urls, "fm.awa.app"))
        if sc_urls and (not hasattr(self, 'use_sc') or self.use_sc.get()): active_pools.append(("soundcloud", sc_urls, "com.soundcloud.android"))
        if pan_urls and (not hasattr(self, 'use_pan') or self.use_pan.get()): active_pools.append(("pandora", pan_urls, "com.pandora.android"))
        if am_urls and (not hasattr(self, 'use_am') or self.use_am.get()): active_pools.append(("audiomack", am_urls, "com.audiomack"))
        if apl_urls and (not hasattr(self, 'use_apl') or self.use_apl.get()): active_pools.append(("applemusic", apl_urls, "com.apple.android.music"))
        
        if len(active_pools) < 2:
            self.log_msg("⚠️ Para el Modo Mixto, necesitas tener al menos DOS cajas activadas y con enlaces.", "warn")
            return
            
        if hasattr(self, 'engine') and self.engine.active_devices:
            self.log_msg(f"⚖️ [MANUAL MIXTO] Dividiendo la granja en {len(active_pools)} plataformas...", "info")
            import random
            
            def _mass_inject():
                # Randomize devices so they don't always get the same platform on every rotation
                devices = list(self.engine.active_devices)
                random.shuffle(devices)
                
                for i, dev in enumerate(devices):
                    pool_data = active_pools[i % len(active_pools)]
                    pool_type = pool_data[0]
                    pool_urls = pool_data[1]
                    rnd_url = random.choice(pool_urls)
                    
                    if pool_type == "spotify":
                        self._inject_playlist_to_single(dev['serial'], rnd_url)
                    elif pool_type in ("yt_music", "yt_video"):
                        self._inject_youtube_to_single(dev['serial'], rnd_url)
                    else:
                        package = pool_data[2]
                        self._inject_generic_audio_to_single(dev['serial'], rnd_url, package)
                        
                    time.sleep(1.5)
            threading.Thread(target=_mass_inject, daemon=True).start()
        else:
            self.log_msg("⚠️ El túnel no está iniciado.", "warn")

    def _inject_playlist_to_single(self, serial, playlist_url):
        self.lock_device(serial, 40)
        
        if "?si=" in playlist_url: playlist_url = playlist_url.split("?si=")[0]
        
        # NUEVO: Convertir URL web de Spotify a URI nativo para forzar la apertura de la app (evita que Chrome intercepte)
        if "open.spotify.com" in playlist_url:
            import re
            match = re.search(r'/(playlist|album|track|artist)/([a-zA-Z0-9]+)', playlist_url)
            if match:
                type_ = match.group(1)
                id_ = match.group(2)
                # Formato secreto que fuerza autoplay en algunos dispositivos: spotify:playlist:ID:play
                playlist_url = f"spotify:{type_}:{id_}:play"
                
        safe_url = f"'{playlist_url}'"
        # Despertar pantalla
        self.adb.run_command(["shell", "input", "keyevent", "224"], serial)
        # Apagar YouTube y YT Music por si acaso para evitar conflictos de audio
        self.adb.run_command(["shell", "am", "force-stop", "com.google.android.youtube"], serial)
        self.adb.run_command(["shell", "am", "force-stop", "com.google.android.apps.youtube.music"], serial)
        # Nota: NO hacemos force-stop a Spotify porque destruye el MediaSession y evita que el botón Play/Next funcione.
        time.sleep(2.0)
        
        # Iniciar Spotify con la URL
        self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url], serial)
        
        def delayed_play(s=serial):
            # Aumentar la paciencia a 15 segundos para proxies lentos (carga inicial)
            time.sleep(15)
            # El comando PLAY (126) ha demostrado ser el 100% efectivo sin necesidad de tocar la pantalla.
            self.adb.run_command(["shell", "input", "keyevent", "126"], s)
            
            # Redundancia: segundo intento de Play por si no agarró a la primera
            time.sleep(5)
            self.adb.run_command(["shell", "input", "keyevent", "126"], s)
            
            # NUEVO: Esperar 60 segundos adicionales para saltar cualquier anuncio largo de Spotify
            # Esto fuerza a que inicie la primera canción real
            time.sleep(60)
            self.adb.run_command(["shell", "input", "keyevent", "87"], s)
        threading.Thread(target=delayed_play, daemon=True).start()

    def _inject_playlist_to_active(self, playlist_url):
        if not hasattr(self, 'engine') or not getattr(self.engine, 'active_devices', []):
            return
            
        def _mass_inject():
            for dev in self.engine.active_devices:
                self._inject_playlist_to_single(dev['serial'], playlist_url)
                time.sleep(1.5)
        threading.Thread(target=_mass_inject, daemon=True).start()

    def update_playlist_ui(self, *args):
        pass

    def update_playlist_combo(self, *args):
        pass

    def clear_yt_music_cache(self):
        devices = self.get_selected_devices()
        if not devices:
            self.log_msg("⚠️ Selecciona dispositivos en la pestaña principal primero.", "warn")
            return
            
        def _clear():
            self.log_msg(f"🧹 Limpiando Caché de YT Music en {len(devices)} dispositivos...", "warn")
            for dev in devices:
                self.adb.run_command(["shell", "pm", "clear", "com.google.android.apps.youtube.music"], dev['serial'])
            self.after(0, lambda: self.log_msg("✅ Limpieza de Caché de YT Music completada.", "info"))
            
        threading.Thread(target=_clear, daemon=True).start()

    def install_custom_apk(self, apk_filename, display_name):
        devices = self.get_selected_devices()
        if not devices:
            self.log_msg(f"⚠️ Selecciona dispositivos primero para instalar {display_name}.", "warn")
            return
            
        import os
        folder_name = apk_filename.replace(".apk", "")
        is_split = False
        target_path = apk_filename
        
        if not os.path.exists(apk_filename):
            if os.path.isdir(folder_name):
                is_split = True
                target_path = folder_name
            else:
                self.log_msg(f"❌ No se encontró el archivo o carpeta para '{apk_filename}' en la carpeta del bot.", "error")
                self.log_msg(f"💡 Por favor descarga el APK/XAPK de {display_name}.", "info")
                return
                
        def _install():
            self.log_msg(f"📦 Instalando {display_name} en {len(devices)} dispositivos (esto puede tardar)...", "info")
            for dev in devices:
                self.log_msg(f"⏳ Instalando en {dev['serial']}...", "info")
                if is_split:
                    apk_files = [os.path.join(target_path, f) for f in os.listdir(target_path) if f.endswith(".apk")]
                    if apk_files:
                        self.adb.run_command(["install-multiple", "-r", "-g"] + apk_files, dev['serial'], retries=1, timeout=120)
                    else:
                        self.log_msg(f"❌ No se encontraron archivos APK dentro de la carpeta '{target_path}'.", "error")
                else:
                    self.adb.run_command(["install", "-r", "-g", apk_filename], dev['serial'], retries=1, timeout=120)
            self.after(0, lambda: self.log_msg(f"✅ Instalación de {display_name} completada.", "info"))
            
        threading.Thread(target=_install, daemon=True).start()

    def uninstall_custom_apk(self, package_name, display_name):
        devices = self.get_selected_devices()
        if not devices:
            self.log_msg(f"⚠️ Selecciona dispositivos primero para desinstalar {display_name}.", "warn")
            return
            
        def _uninstall():
            self.log_msg(f"🗑️ Desinstalando {display_name} de {len(devices)} dispositivos...", "info")
            for dev in devices:
                self.log_msg(f"⏳ Desinstalando de {dev['serial']}...", "info")
                self.adb.run_command(["uninstall", package_name], dev['serial'], retries=1, timeout=60)
            self.after(0, lambda: self.log_msg(f"✅ Desinstalación de {display_name} completada.", "info"))
            
        threading.Thread(target=_uninstall, daemon=True).start()

    def _inject_generic_audio_to_single(self, serial, url, package_name):
        self.lock_device(serial, 40)
        safe_url = f"'{url}'"
        
        self.adb.run_command(["shell", "input", "keyevent", "224"], serial)
        self.adb.run_command(["shell", "am", "force-stop", package_name], serial)
        time.sleep(2.0)
        
        self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url], serial)
        
        def delayed_play(s=serial):
            time.sleep(15)
            self.adb.run_command(["shell", "input", "keyevent", "126"], s)
            time.sleep(5)
            self.adb.run_command(["shell", "input", "keyevent", "126"], s)
            
            # 60s delay to skip initial long ads
            time.sleep(60)
            self.adb.run_command(["shell", "input", "keyevent", "87"], s)
            
        threading.Thread(target=delayed_play, daemon=True).start()

    def _inject_mass_generic(self, textbox, name, package):
        if not hasattr(self, 'engine') or not self.engine.active_devices:
            self.log_msg("⚠️ El túnel no está iniciado.", "warn")
            return
            
        urls_raw = textbox.get("1.0", "end").strip().split('\n')
        urls = [u.strip() for u in urls_raw if u.strip()]
        if not urls:
            self.log_msg(f"⚠️ No hay enlaces en la caja de {name}.", "warn")
            return
            
        self.log_msg(f"▶️ Inyectando {name} (Manual)...", "info")
        import random
        def _mass():
            for dev in self.engine.active_devices:
                rnd_url = random.choice(urls)
                self._inject_generic_audio_to_single(dev['serial'], rnd_url, package)
                time.sleep(1.5)
        threading.Thread(target=_mass, daemon=True).start()

    def inject_manual_awa(self): self._inject_mass_generic(self.awa_textbox, "AWA", "fm.awa.app")
    def inject_manual_pan(self): self._inject_mass_generic(self.pan_textbox, "Pandora", "com.pandora.android")
    def inject_manual_am(self): self._inject_mass_generic(self.am_textbox, "Audiomack", "com.audiomack")
    def inject_manual_apl(self): self._inject_mass_generic(self.apl_textbox, "Apple Music", "com.apple.android.music")

    def _inject_youtube_to_single(self, serial, url):
        self.lock_device(serial, 40)
        
        # 1. Limpiar parámetros de rastreo que causan error de "Sin conexión" en la app
        if "&si=" in url: url = url.split("&si=")[0]
        if "?si=" in url: url = url.split("?si=")[0]
            
        # 2. Forzar Auto-Play y Aleatorio (cambiar playlist por watch)
        if "/playlist?list=" in url:
            url = url.replace("/playlist?list=", "/watch?list=")
            # Agregar el parámetro secreto de shuffle para YouTube
            if "&shuffle=" not in url:
                url += "&shuffle=1"
                
        safe_url = f"'{url}'"
        
        # 3. Detect target app & Logic
        is_web_mode = getattr(self, 'youtube_web_var', None) and self.youtube_web_var.get()
        
        if is_web_mode:
            target_app = "com.android.chrome"
        else:
            target_app = "com.google.android.youtube"
            if "music.youtube.com" in url:
                target_app = "com.google.android.apps.youtube.music"
            
        # 4. Wake screen
        self.adb.run_command(["shell", "input", "keyevent", "224"], serial)
        
        # 5. Force stop the correct app to prevent buffer lock
        self.adb.run_command(["shell", "am", "force-stop", target_app], serial)
        time.sleep(3.0) # Dar más tiempo a liberar memoria y red
        
        # 6. Launch URL
        if is_web_mode:
            # Forzar apertura en Chrome
            self.adb.run_command(["shell", "am", "start", "-n", "com.android.chrome/com.google.android.apps.chrome.Main", "-d", safe_url], serial)
        else:
            # Usamos SOLO el comando genérico seguro para no asfixiar la app nativa con dobles intents
            self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "-f", "0x14000000"], serial)
        
        def delayed_youtube_play(s=serial):
            # Dar 28 segundos para que el proxy cargue toda la interfaz y buffer
            time.sleep(28)
            
            # Use KEYCODE_MEDIA_PLAY (126) instead of KEYCODE_MEDIA_PLAY_PAUSE (85)
            # This ensures it ONLY plays. If it's already auto-playing, it won't pause it.
            self.adb.run_command(["shell", "input", "keyevent", "126"], s)
            
            # Redundancia: A veces el primer clic es ignorado si la app sigue cargando
            time.sleep(6)
            self.adb.run_command(["shell", "input", "keyevent", "126"], s)
            
            # NUEVO: Adelantar inmediatamente para destrabar popups o pantallas estancadas
            # PERO SOLO si es YT Music o una lista. Si es un video individual normal, no adelantamos para no perderlo.
            if target_app == "com.google.android.apps.youtube.music" or "/watch?list=" in url:
                time.sleep(4)
                self.adb.run_command(["shell", "input", "keyevent", "87"], s)
            
        threading.Thread(target=delayed_youtube_play, daemon=True).start()


    def _inject_youtube_to_active(self, url):
        if not hasattr(self, 'engine') or not self.engine.active_devices:
            return
            
        def _mass_inject():
            for dev in self.engine.active_devices:
                self._inject_youtube_to_single(dev['serial'], url)
                time.sleep(1.5) # Stagger mass injection too
        threading.Thread(target=_mass_inject, daemon=True).start()

    def update_youtube_ui(self, *args):
        try:
            self.yt_interval_entry.configure(state="normal" if self.youtube_mode.get() == "auto" else "disabled")
            self.youtube_combo.configure(state="normal")
            self.youtube_inject_btn.configure(state="normal")
        except:
            pass

    def update_youtube_combo(self, *args):
        try:
            urls_raw = self.youtube_textbox.get("1.0", "end").strip().split('\n')
            urls = [p.strip() for p in urls_raw if p.strip()]
            if urls:
                combo_vals = ["🔀 Distribuir Aleatoriamente"] + urls
                self.youtube_combo.configure(values=combo_vals)
                if self.youtube_combo.get() not in combo_vals:
                    self.youtube_combo.set(combo_vals[0])
            else:
                self.youtube_combo.configure(values=["Seleccionar URL..."])
                self.youtube_combo.set("Seleccionar URL...")
        except:
            pass

    def build_control_tab(self):
        self.tab_ctrl.grid_columnconfigure(0, weight=1)
        self.tab_ctrl.grid_columnconfigure(1, weight=2)
        self.tab_ctrl.grid_rowconfigure(1, weight=1)

        # left controls
        frame = ctk.CTkScrollableFrame(self.tab_ctrl)
        frame.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")

        ctk.CTkLabel(frame, text="⏱️ Dinámica de Rotación", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.network_rot_switch = ctk.CTkSwitch(frame, text="⚠️ Habilitar Rotación de Internet por Lotes (Obsoleto)", variable=self.network_rotation_enabled, text_color="#F59E0B", font=("Arial", 11, "bold"))
        self.network_rot_switch.pack(pady=(0, 10))
        
        ctk.CTkLabel(frame, text="Dispositivos Encendidos a la vez:", font=("Arial", 11)).pack()
        self.batch_entry = ctk.CTkEntry(frame, placeholder_text="Ej: 10")
        self.batch_entry.pack(pady=2, padx=10, fill="x")
        self.batch_entry.insert(0, "10")
        
        ctk.CTkLabel(frame, text="Minutos activos antes de apagar WiFi y Rotar:", font=("Arial", 11)).pack(pady=(10,0))
        self.mins_entry = ctk.CTkEntry(frame, placeholder_text="Ej: 360 para 6 horas")
        self.mins_entry.pack(pady=2, padx=10, fill="x")
        self.mins_entry.insert(0, "360")
        
        checks_frame = ctk.CTkFrame(frame, fg_color="transparent")
        checks_frame.pack(pady=10)
        self.infinite_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(checks_frame, text="🔄 Rotar Infinito", variable=self.infinite_var).pack(side="left", padx=5)
        self.stealth_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(checks_frame, text="🕵️ Modo Sigilo (Goteo)", variable=self.stealth_var).pack(side="left", padx=5)
        
        # Proxies
        prx_frame = ctk.CTkFrame(frame, fg_color="transparent")
        prx_frame.pack(fill="x", pady=(10, 5))
        
        self.no_proxy_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(prx_frame, text="🔌 Modo Sin Proxy (Internet del PC)", variable=self.no_proxy_var, font=("Arial", 11, "bold"), text_color="#10B981").pack(side="left", padx=10)
        
        self.bot_only_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(prx_frame, text="📡 Modo Solo Bot (WiFi Celular)", variable=self.bot_only_var, font=("Arial", 11, "bold"), text_color="#38BDF8").pack(side="left", padx=5)
        
        self.test_btn = ctk.CTkButton(prx_frame, text="🧪 Probador", width=80, fg_color="#3B82F6", command=self.test_proxies)
        self.test_btn.pack(side="right", padx=10)

        self.proxy_textbox = ctk.CTkTextbox(frame, height=120)
        self.proxy_textbox.pack(pady=5, padx=10, fill="x")
        self.proxy_textbox.insert("1.0", "# IP:PORT:USER:PASS o similar\n")
        
        # The Bot Humanoide was moved to build_traffic_tab
        # Actions
        ctk.CTkLabel(frame, text="⚙️ Controles de Mando", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        
        scan_frame = ctk.CTkFrame(frame, fg_color="transparent")
        scan_frame.pack(fill="x", pady=5)
        
        self.scan_btn = ctk.CTkButton(scan_frame, text="🔍 1. Escanear", command=self.scan_devices)
        self.scan_btn.pack(side="left", padx=10, expand=True, fill="x")
        self.bind_tooltip(self.scan_btn, "Actualiza la lista de dispositivos conectados y listos para trabajar.")
        
        self.reset_adb_btn = ctk.CTkButton(scan_frame, text="🔌 Reset USB", command=self.restart_adb_server, fg_color="#EF4444")
        self.reset_adb_btn.pack(side="right", padx=(0, 10), expand=True, fill="x")
        self.bind_tooltip(self.reset_adb_btn, "PÁNICO: Reinicia el motor USB para revivir celulares invisibles sin reiniciar la PC.")
        
        self.install_btn = ctk.CTkButton(frame, text="📥 2. Instalar PKG (Gnirehtet)", command=self.install_gnirehtet, fg_color="green")
        self.install_btn.pack(pady=5, padx=10, fill="x")
        self.bind_tooltip(self.install_btn, "Instala la app de enrutamiento en los celulares para que reciban internet.")

        self.assign_btn = ctk.CTkButton(frame, text="🎯 ASIGNAR PROXYS MANUAL", command=self.assign_proxies, fg_color="#6366F1", font=("Arial", 13, "bold"))
        self.assign_btn.pack(pady=5, padx=10, fill="x")
        self.bind_tooltip(self.assign_btn, "Aplica manualmente las IPs ingresadas a los celulares uno por uno.")

        self.inventory_btn = ctk.CTkButton(frame, text="📦 VER MAPA FÍSICO (HUBs)", command=self.show_inventory, fg_color="#8B5CF6", font=("Arial", 13, "bold"))
        self.inventory_btn.pack(pady=5, padx=10, fill="x")
        self.bind_tooltip(self.inventory_btn, "Muestra el puerto USB exacto de cada celular para hallar los desconectados.")

        self.start_btn = ctk.CTkButton(frame, text="🚀 3. CREAR TÚNEL CENTRAL", command=self.attempt_start, height=40)
        self.start_btn.pack(pady=10, padx=10, fill="x")
        self.bind_tooltip(self.start_btn, "INICIA LA MAGIA: Pasa internet a todos los celulares e inyecta música/video.")
        
        self.pause_btn = ctk.CTkButton(frame, text="⏸️ PAUSAR (Editar Num/Hora)", command=self.toggle_pause, state="disabled", fg_color="#F59E0B")
        self.pause_btn.pack(pady=5, padx=10, fill="x")
        self.bind_tooltip(self.pause_btn, "Pausa la rotación y la música temporalmente sin apagar el internet.")

        self.repair_btn = ctk.CTkButton(frame, text="🔧 REPARAR CAÍDOS", command=self.repair_failed_devices, state="disabled", fg_color="#8B5CF6", font=("Arial", 12, "bold"))
        self.repair_btn.pack(pady=5, padx=10, fill="x")
        self.bind_tooltip(self.repair_btn, "Intenta reconectar y estabilizar aquellos dispositivos que tengan falla roja.")
        
        self.clean_btn = ctk.CTkButton(frame, text="🧹 PANIC: LIMPIEZA TOTAL (40 Disp)", command=self.panic_clean, fg_color="darkred")
        self.clean_btn.pack(pady=20, padx=10, fill="x")
        self.bind_tooltip(self.clean_btn, "Detiene todo, corta el internet y borra el caché de apps en TODOS los celulares.")

        # Instaladores masivos (Movidos desde Extras)
        inst_frame = ctk.CTkFrame(frame, fg_color="#1E293B", corner_radius=8)
        inst_frame.pack(fill="x", padx=10, pady=(10, 20))
        ctk.CTkLabel(inst_frame, text="📦 Instaladores Masivos de APKs", font=("Arial", 14, "bold"), text_color="#F59E0B").pack(pady=5)
        
        btn_frame = ctk.CTkFrame(inst_frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        
        platforms = [
            ("🎵 AWA", "awa.apk", "#D946EF"),
            ("📻 Pandora", "pandora.apk", "#0EA5E9"),
            ("🎧 Audiomack", "audiomack.apk", "#F59E0B"),
            ("🍎 Apple Music", "applemusic.apk", "#EF4444"),
            ("🌊 Tidal", "tidal.apk", "#06B6D4")
        ]
        
        for name, apk, color in platforms:
            ctk.CTkButton(btn_frame, text=name, width=120, fg_color=color, command=lambda a=apk, n=name: self.install_custom_apk(a, n)).pack(side="left", padx=5)

        # Desinstaladores masivos
        ctk.CTkLabel(inst_frame, text="🗑️ Desinstaladores Masivos", font=("Arial", 12, "bold"), text_color="#EF4444").pack(pady=(10, 2))
        
        unbtn_frame = ctk.CTkFrame(inst_frame, fg_color="transparent")
        unbtn_frame.pack(pady=(0, 10))
        
        uninstall_platforms = [
            ("❌ AWA", "fm.awa.app", "#991B1B"),
            ("❌ Pandora", "com.pandora.android", "#991B1B"),
            ("❌ Audiomack", "com.audiomack", "#991B1B"),
            ("❌ Apple Music", "com.apple.android.music", "#991B1B"),
            ("❌ Tidal", "com.aspiro.tidal", "#991B1B")
        ]
        
        for name, pkg, color in uninstall_platforms:
            ctk.CTkButton(unbtn_frame, text=name, width=120, fg_color=color, hover_color="#7F1D1D", command=lambda p=pkg, n=name: self.uninstall_custom_apk(p, n)).pack(side="left", padx=5)

        # Right Cards
        self._right_container = ctk.CTkFrame(self.tab_ctrl, fg_color="transparent")
        self._right_container.grid(row=1, column=1, pady=10, padx=10, sticky="nsew")

        btn = ctk.CTkButton(self._right_container, text="🩺 Obtener Diagnóstico Global", height=30, command=self.run_global_report, fg_color="#059669")
        btn.pack(fill="x", pady=(0, 5))

        # Device selection toolbar
        sel_frame = ctk.CTkFrame(self._right_container, fg_color="#1A1A2E", corner_radius=8)
        sel_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(sel_frame, text="☑️ Todos", width=90, height=28, command=self.select_all_devices, fg_color="#10B981").pack(side="left", padx=5, pady=5)
        ctk.CTkButton(sel_frame, text="☐ Ninguno", width=90, height=28, command=self.deselect_all_devices, fg_color="#6B7280").pack(side="left", padx=5, pady=5)
        self.selection_count_lbl = ctk.CTkLabel(sel_frame, text="0 de 0 seleccionados", font=("Arial", 11, "bold"), text_color="#60A5FA")
        self.selection_count_lbl.pack(side="right", padx=10, pady=5)

        self.dev_frame = ctk.CTkScrollableFrame(self._right_container, label_text="Tarjetas de Dispositivos 📱")
        self.dev_frame.pack(fill="both", expand=True)
        self.device_widgets = []
        
        # Log
        self.log_frame = ctk.CTkTextbox(self.tab_ctrl, height=100)
        self.log_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
        self.log_frame.configure(state="disabled")

    def build_traffic_tab(self):
        # MODO MAESTRO
        master_frame = ctk.CTkFrame(self.tab_traf, fg_color="#1E293B", corner_radius=8)
        master_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(master_frame, text="⚙️ MODO DE OPERACIÓN MAESTRO", font=("Arial", 14, "bold"), text_color="#F59E0B").pack(pady=5)
        
        rb_frame = ctk.CTkFrame(master_frame, fg_color="transparent")
        rb_frame.pack(pady=5)
        
        ctk.CTkRadioButton(rb_frame, text="🟢 SOLO SPOTIFY", variable=self.master_mode, value="spotify", font=("Arial", 12, "bold"), text_color="#10B981").pack(side="left", padx=10)
        ctk.CTkRadioButton(rb_frame, text="🟣 SOLO YT MUSIC", variable=self.master_mode, value="yt_music", font=("Arial", 12, "bold"), text_color="#C026D3").pack(side="left", padx=10)
        ctk.CTkRadioButton(rb_frame, text="🔴 SOLO YT VIDEO", variable=self.master_mode, value="yt_video", font=("Arial", 12, "bold"), text_color="#EF4444").pack(side="left", padx=10)
        ctk.CTkRadioButton(rb_frame, text="🟡 MIXTO (Rotativo)", variable=self.master_mode, value="mixed", font=("Arial", 12, "bold"), text_color="#F59E0B").pack(side="left", padx=10)

        # Cajas de URLs
        url_frame = ctk.CTkFrame(self.tab_traf, fg_color="transparent")
        url_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Caja 1: Spotify
        spot_frame = ctk.CTkFrame(url_frame, fg_color="#064E3B", corner_radius=8) # Dark green
        spot_frame.pack(side="left", fill="both", expand=True, padx=(0, 2))
        self.use_spotify = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(spot_frame, text="🟢 Spotify (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_spotify).pack(anchor="w", padx=10, pady=(5, 0))
        self.playlist_textbox = ctk.CTkTextbox(spot_frame, height=160)
        self.playlist_textbox.pack(padx=5, pady=2, fill="x")
        
        spot_btn_frame = ctk.CTkFrame(spot_frame, fg_color="transparent")
        spot_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(spot_btn_frame, text="💾", width=30, height=24, fg_color="#F59E0B", command=self.save_config).pack(side="left", padx=(0, 5))
        ctk.CTkButton(spot_btn_frame, text="🗑️", width=30, height=24, fg_color="#4B5563", command=lambda: self.playlist_textbox.delete("1.0", "end")).pack(side="left")

        # Caja 2: YT Music
        ytm_frame = ctk.CTkFrame(url_frame, fg_color="#4A044E", corner_radius=8) # Dark purple
        ytm_frame.pack(side="left", fill="both", expand=True, padx=2)
        self.use_ytmusic = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(ytm_frame, text="🟣 YT Music (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_ytmusic).pack(anchor="w", padx=10, pady=(5, 0))
        self.ytmusic_textbox = ctk.CTkTextbox(ytm_frame, height=160)
        self.ytmusic_textbox.pack(padx=5, pady=2, fill="x")
        
        ytm_btn_frame = ctk.CTkFrame(ytm_frame, fg_color="transparent")
        ytm_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(ytm_btn_frame, text="💾", width=30, height=24, fg_color="#F59E0B", command=self.save_config).pack(side="left", padx=(0, 5))
        ctk.CTkButton(ytm_btn_frame, text="🗑️", width=30, height=24, fg_color="#4B5563", command=lambda: self.ytmusic_textbox.delete("1.0", "end")).pack(side="left")

        # Caja 3: YT Video
        yt_frame = ctk.CTkFrame(url_frame, fg_color="#7F1D1D", corner_radius=8) # Dark red
        yt_frame.pack(side="right", fill="both", expand=True, padx=(2, 0))
        self.use_ytvideo = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(yt_frame, text="🔴 YT Video (Links):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_ytvideo).pack(anchor="w", padx=10, pady=(5, 0))
        self.youtube_textbox = ctk.CTkTextbox(yt_frame, height=160)
        self.youtube_textbox.pack(padx=5, pady=2, fill="x")
        
        yt_btn_frame = ctk.CTkFrame(yt_frame, fg_color="transparent")
        yt_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(yt_btn_frame, text="💾", width=30, height=24, fg_color="#F59E0B", command=self.save_config).pack(side="left", padx=(0, 5))
        ctk.CTkButton(yt_btn_frame, text="🗑️", width=30, height=24, fg_color="#4B5563", command=lambda: self.youtube_textbox.delete("1.0", "end")).pack(side="left")
        
        self.youtube_web_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(yt_frame, text="🌐 En Chrome", variable=self.youtube_web_var, text_color="white", font=("Arial", 10, "bold"), checkbox_height=18, checkbox_width=18).pack(pady=(0, 5), padx=5, anchor="w")

        # Controles y Anti-Bots
        ctrl_frame = ctk.CTkFrame(self.tab_traf, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Interruptor de rotación automática
        self.media_rot_switch = ctk.CTkSwitch(ctrl_frame, text="▶️ Inyección Automática", variable=self.media_rotation_active, progress_color="#10B981")
        self.media_rot_switch.pack(side="left", padx=10)
        
        ctk.CTkLabel(ctrl_frame, text="Rotar cada (Minutos):").pack(side="left", padx=5)
        self.pl_interval_entry = ctk.CTkEntry(ctrl_frame, textvariable=self.playlist_interval, width=50, justify="center")
        self.pl_interval_entry.pack(side="left", padx=5)
        
        ctk.CTkCheckBox(ctrl_frame, text="💧 Goteo Humano", variable=self.youtube_drip_var).pack(side="left", padx=(15, 5))
        
        # Inyectores manuales
        self.btn_manual_spotify = ctk.CTkButton(ctrl_frame, text="Spotify", width=55, fg_color="#10B981", command=self.inject_manual_playlist)
        self.btn_manual_spotify.pack(side="right", padx=2)
        
        self.btn_manual_ytmusic = ctk.CTkButton(ctrl_frame, text="YT Music", width=65, fg_color="#C026D3", command=self.inject_manual_ytmusic)
        self.btn_manual_ytmusic.pack(side="right", padx=2)
        
        self.btn_manual_youtube = ctk.CTkButton(ctrl_frame, text="YT Video", width=65, fg_color="#EF4444", command=self.inject_manual_youtube)
        self.btn_manual_youtube.pack(side="right", padx=2)
        
        self.btn_manual_mixed = ctk.CTkButton(ctrl_frame, text="Mixto", width=55, fg_color="#F59E0B", command=self.inject_manual_mixed)
        self.btn_manual_mixed.pack(side="right", padx=2)
        
        # Display Dashboard en vivo
        self.live_status_var = ctk.StringVar(value="Estado: ⏸️ ESPERANDO...")
        dashboard_frame = ctk.CTkFrame(self.tab_traf, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#38BDF8")
        dashboard_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.live_status_lbl = ctk.CTkLabel(dashboard_frame, textvariable=self.live_status_var, font=("Courier New", 14, "bold"), text_color="#38BDF8")
        self.live_status_lbl.pack(pady=8)
        
        # Inicializar el estado de la UI
        self.after(100, self.update_ui_state)

        # Shield
        shield_frame = ctk.CTkFrame(self.tab_traf, fg_color="#1E1E1E", border_width=1, border_color="#3B82F6", corner_radius=8)
        shield_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(shield_frame, text="🛡️ Escudo Anti-Bots", font=("Arial", 12, "bold"), text_color="#60A5FA").pack(side="left", padx=10, pady=5)
        
        ctk.CTkCheckBox(shield_frame, text="Auto-Reinicio", variable=self.watchdog_enabled, text_color="#94A3B8").pack(side="left", padx=(10, 5), pady=5)
        ctk.CTkCheckBox(shield_frame, text="Toques Fantasma", variable=self.ghost_enabled, text_color="#94A3B8").pack(side="left", padx=5, pady=5)
        
        btn_bot = ctk.CTkCheckBox(shield_frame, text="Saltos Impacientes", variable=self.bot_enabled, text_color="#10B981")
        btn_bot.pack(side="left", padx=5, pady=5)
        self.bind_tooltip(btn_bot, "Simula ser humano: escucha 5-7 canciones completas, luego salta impacientemente la 8va al minuto 1.")
        
        ctk.CTkButton(shield_frame, text="🧹 Limpiar Caché", fg_color="#B91C1C", width=110, command=self.clear_yt_music_cache).pack(side="right", padx=10, pady=5)

        # Toolbar with sorting buttons
        toolbar = ctk.CTkFrame(self.tab_traf, fg_color="#1A1A2E", corner_radius=8)
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(toolbar, text="Ordenar:", font=("Arial", 11), text_color="#94A3B8").pack(side="left", padx=(10, 5), pady=5)
        ctk.CTkButton(toolbar, text="🔤 Por Serial", width=120, height=28, command=lambda: self.sort_traffic("serial"), fg_color="#3B82F6").pack(side="left", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="🟢 Por Conexión", width=130, height=28, command=lambda: self.sort_traffic("connection"), fg_color="#10B981").pack(side="left", padx=5, pady=5)
        self.traf_sort_lbl = ctk.CTkLabel(toolbar, text="Sin ordenar", font=("Arial", 10), text_color="#64748B")
        self.traf_sort_lbl.pack(side="right", padx=10, pady=5)

        self.traf_frame = ctk.CTkScrollableFrame(self.tab_traf)
        self.traf_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        title = ctk.CTkLabel(self.traf_frame, text="Semáforo de Consumo en Tiempo Real", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        self.traf_widgets = {}  # serial -> label widget
        self.traf_data = {}  # serial -> {is_active, rx, tx, ip, text, color}
        self.traf_sort_mode = None  # None, "serial", "connection"

    def build_extras_tab(self):
        # Cajas de texto
        boxes_frame = ctk.CTkScrollableFrame(self.tab_extras, height=450)
        boxes_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # AWA
        awa_frame = ctk.CTkFrame(boxes_frame, fg_color="#4A044E", corner_radius=8)
        awa_frame.pack(fill="x", pady=5)
        self.use_awa = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(awa_frame, text="🎵 AWA (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_awa).pack(anchor="w", padx=10, pady=5)
        self.awa_textbox = ctk.CTkTextbox(awa_frame, height=80)
        self.awa_textbox.pack(padx=5, pady=2, fill="x")
        btn_awa = ctk.CTkButton(awa_frame, text="▶️ Inyectar AWA", fg_color="#D946EF", command=self.inject_manual_awa)
        btn_awa.pack(side="right", padx=5, pady=5)

        # Pandora
        pan_frame = ctk.CTkFrame(boxes_frame, fg_color="#0C4A6E", corner_radius=8)
        pan_frame.pack(fill="x", pady=5)
        self.use_pan = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(pan_frame, text="📻 Pandora (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_pan).pack(anchor="w", padx=10, pady=5)
        self.pan_textbox = ctk.CTkTextbox(pan_frame, height=80)
        self.pan_textbox.pack(padx=5, pady=2, fill="x")
        btn_pan = ctk.CTkButton(pan_frame, text="▶️ Inyectar Pandora", fg_color="#0EA5E9", command=self.inject_manual_pan)
        btn_pan.pack(side="right", padx=5, pady=5)

        # Audiomack
        am_frame = ctk.CTkFrame(boxes_frame, fg_color="#78350F", corner_radius=8)
        am_frame.pack(fill="x", pady=5)
        self.use_am = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(am_frame, text="🎧 Audiomack (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_am).pack(anchor="w", padx=10, pady=5)
        self.am_textbox = ctk.CTkTextbox(am_frame, height=80)
        self.am_textbox.pack(padx=5, pady=2, fill="x")
        btn_am = ctk.CTkButton(am_frame, text="▶️ Inyectar Audiomack", fg_color="#F59E0B", command=self.inject_manual_am)
        btn_am.pack(side="right", padx=5, pady=5)

        # Apple Music
        apl_frame = ctk.CTkFrame(boxes_frame, fg_color="#7F1D1D", corner_radius=8)
        apl_frame.pack(fill="x", pady=5)
        self.use_apl = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(apl_frame, text="🍎 Apple Music (Listas):", font=("Arial", 11, "bold"), text_color="white", variable=self.use_apl).pack(anchor="w", padx=10, pady=5)
        self.apl_textbox = ctk.CTkTextbox(apl_frame, height=80)
        self.apl_textbox.pack(padx=5, pady=2, fill="x")
        btn_apl = ctk.CTkButton(apl_frame, text="▶️ Inyectar Apple Music", fg_color="#EF4444", command=self.inject_manual_apl)
        btn_apl.pack(side="right", padx=5, pady=5)
        
        # Save button globally for this tab
        ctk.CTkButton(self.tab_extras, text="💾 Guardar Cambios de Enlaces", fg_color="#10B981", command=self.save_config).pack(pady=10)

    def update_ui_state(self, *args):
        if not hasattr(self, 'btn_manual_spotify'): return
        mode = self.master_mode.get()
        
        # Reset all to disabled by default
        self.btn_manual_spotify.configure(state="disabled", fg_color="#374151")
        self.btn_manual_ytmusic.configure(state="disabled", fg_color="#374151")
        self.btn_manual_youtube.configure(state="disabled", fg_color="#374151")
        
        if mode == "spotify":
            self.btn_manual_spotify.configure(state="normal", fg_color="#10B981")
        elif mode == "yt_music":
            self.btn_manual_ytmusic.configure(state="normal", fg_color="#C026D3")
        elif mode == "yt_video":
            self.btn_manual_youtube.configure(state="normal", fg_color="#EF4444")
        else: # mixed
            self.btn_manual_spotify.configure(state="normal", fg_color="#10B981")
            self.btn_manual_ytmusic.configure(state="normal", fg_color="#C026D3")
            self.btn_manual_youtube.configure(state="normal", fg_color="#EF4444")
            
        # Obsolete network rotation state
        if hasattr(self, 'network_rotation_enabled'):
            state = "normal" if self.network_rotation_enabled.get() else "disabled"
            color = "#FFFFFF" if self.network_rotation_enabled.get() else "#6B7280" # gris
            
            self.batch_entry.configure(state=state)
            self.mins_entry.configure(state=state)

    def log_msg(self, msg, type="info"):
        self.log_frame.configure(state="normal")
        sym = "🟢" if type == "info" else "🔴"
        if type == "warn": sym = "🟡"
        self.log_frame.insert("end", f"{sym} {msg}\n")
        self.log_frame.see("end")
        self.log_frame.configure(state="disabled")

    def restart_adb_server(self):
        def _task():
            self.log_msg("⚠️ Matando motor USB (ADB)... (Desconectará otras apps brevemente)", "warn")
            import subprocess
            self.adb.run_command(["kill-server"])
            subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            self.log_msg("🚀 Reviviendo motor USB...", "info")
            self.adb.run_command(["start-server"])
            time.sleep(2)
            self.log_msg("✅ Motor reiniciado. Escaneando celulares...", "info")
            self.scan_devices()
        threading.Thread(target=_task, daemon=True).start()

    def scan_devices(self):
        self.scan_btn.configure(state="disabled", text="🔍 Escaneando... (Espera)")
        ScanProgressWindow(self, self.adb, self._finish_scan)

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                import json
                data = json.load(f)
                if "batch" in data:
                    self.batch_entry.delete(0, "end")
                    self.batch_entry.insert(0, str(data["batch"]))
                if "mins" in data:
                    self.mins_entry.delete(0, "end")
                    self.mins_entry.insert(0, str(data["mins"]))
                if "proxies" in data:
                    self.proxy_textbox.delete("1.0", "end")
                    self.proxy_textbox.insert("1.0", data["proxies"].strip() + "\n")
                if "playlists" in data:
                    self.playlist_textbox.delete("1.0", "end")
                    self.playlist_textbox.insert("1.0", data["playlists"].strip() + "\n")
                if "master_mode" in data:
                    self.master_mode.set(data["master_mode"])
                if "playlist_interval" in data:
                    self.playlist_interval.set(data["playlist_interval"])
                if "youtube_playlists" in data:
                    self.youtube_textbox.delete("1.0", "end")
                    self.youtube_textbox.insert("1.0", data["youtube_playlists"].strip() + "\n")
                if "yt_music_playlists" in data:
                    if hasattr(self, 'ytmusic_textbox'):
                        self.ytmusic_textbox.delete("1.0", "end")
                        self.ytmusic_textbox.insert("1.0", data["yt_music_playlists"].strip() + "\n")
                if "youtube_drip" in data:
                    self.youtube_drip_var.set(data["youtube_drip"])
                if "watchdog_enabled" in data:
                    self.watchdog_enabled.set(data["watchdog_enabled"])
                if "ghost_enabled" in data:
                    self.ghost_enabled.set(data["ghost_enabled"])
                    
                if hasattr(self, 'awa_textbox') and "awa_playlists" in data:
                    self.awa_textbox.delete("1.0", "end")
                    self.awa_textbox.insert("1.0", data["awa_playlists"].strip() + "\n")
                if hasattr(self, 'sc_textbox') and "sc_playlists" in data:
                    self.sc_textbox.delete("1.0", "end")
                    self.sc_textbox.insert("1.0", data["sc_playlists"].strip() + "\n")
                if hasattr(self, 'pan_textbox') and "pan_playlists" in data:
                    self.pan_textbox.delete("1.0", "end")
                    self.pan_textbox.insert("1.0", data["pan_playlists"].strip() + "\n")
                if hasattr(self, 'am_textbox') and "am_playlists" in data:
                    self.am_textbox.delete("1.0", "end")
                    self.am_textbox.insert("1.0", data["am_playlists"].strip() + "\n")
                if hasattr(self, 'apl_textbox') and "apl_playlists" in data:
                    self.apl_textbox.delete("1.0", "end")
                    self.apl_textbox.insert("1.0", data["apl_playlists"].strip() + "\n")
                if hasattr(self, 'use_spotify') and "use_spotify" in data: self.use_spotify.set(data["use_spotify"])
                if hasattr(self, 'use_ytmusic') and "use_ytmusic" in data: self.use_ytmusic.set(data["use_ytmusic"])
                if hasattr(self, 'use_ytvideo') and "use_ytvideo" in data: self.use_ytvideo.set(data["use_ytvideo"])
                if hasattr(self, 'use_awa') and "use_awa" in data: self.use_awa.set(data["use_awa"])
                if hasattr(self, 'use_sc') and "use_sc" in data: self.use_sc.set(data["use_sc"])
                if hasattr(self, 'use_pan') and "use_pan" in data: self.use_pan.set(data["use_pan"])
                if hasattr(self, 'use_am') and "use_am" in data: self.use_am.set(data["use_am"])
                if hasattr(self, 'use_apl') and "use_apl" in data: self.use_apl.set(data["use_apl"])
                    
                self.infinite_var.set(data.get("infinite", True))
                self.stealth_var.set(data.get("stealth", True))
                self.no_proxy_var.set(data.get("no_proxy", False))
                if hasattr(self, 'bot_only_var'):
                    self.bot_only_var.set(data.get("bot_only", False))
        except:
            pass

    def save_config(self):
        try:
            ytm_text = ""
            if hasattr(self, 'ytmusic_textbox'):
                ytm_text = self.ytmusic_textbox.get("1.0", "end").strip()
                
            data = {
                "batch": self.batch_entry.get(),
                "mins": self.mins_entry.get(),
                "infinite": self.infinite_var.get(),
                "stealth": self.stealth_var.get(),
                "no_proxy": self.no_proxy_var.get(),
                "bot_only": getattr(self, 'bot_only_var', ctk.BooleanVar(value=False)).get(),
                "proxies": self.proxy_textbox.get("1.0", "end").strip(),
                "playlists": self.playlist_textbox.get("1.0", "end").strip(),
                "master_mode": self.master_mode.get(),
                "playlist_interval": self.playlist_interval.get(),
                "youtube_playlists": self.youtube_textbox.get("1.0", "end").strip(),
                "yt_music_playlists": ytm_text,
                "awa_playlists": self.awa_textbox.get("1.0", "end").strip() if hasattr(self, 'awa_textbox') else "",
                "sc_playlists": self.sc_textbox.get("1.0", "end").strip() if hasattr(self, 'sc_textbox') else "",
                "pan_playlists": self.pan_textbox.get("1.0", "end").strip() if hasattr(self, 'pan_textbox') else "",
                "am_playlists": self.am_textbox.get("1.0", "end").strip() if hasattr(self, 'am_textbox') else "",
                "apl_playlists": self.apl_textbox.get("1.0", "end").strip() if hasattr(self, 'apl_textbox') else "",
                "youtube_drip": self.youtube_drip_var.get(),
                "watchdog_enabled": self.watchdog_enabled.get(),
                "ghost_enabled": self.ghost_enabled.get(),
                "use_spotify": self.use_spotify.get() if hasattr(self, 'use_spotify') else True,
                "use_ytmusic": self.use_ytmusic.get() if hasattr(self, 'use_ytmusic') else True,
                "use_ytvideo": self.use_ytvideo.get() if hasattr(self, 'use_ytvideo') else True,
                "use_awa": self.use_awa.get() if hasattr(self, 'use_awa') else True,
                "use_sc": self.use_sc.get() if hasattr(self, 'use_sc') else True,
                "use_pan": self.use_pan.get() if hasattr(self, 'use_pan') else True,
                "use_am": self.use_am.get() if hasattr(self, 'use_am') else True,
                "use_apl": self.use_apl.get() if hasattr(self, 'use_apl') else True
            }
            import os, json
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"), "w") as f:
                json.dump(data, f)
        except:
            pass

    def show_inventory(self):
        InventoryWindow(self)

    def _finish_scan(self, devices):
        self.scanned_devices = devices
        pkg_missing = len([d for d in devices if not d.get('pkg_ok')])
        msg = f"Escaner completado: {len(devices)} conectados."
        if pkg_missing > 0:
            msg += f" ⚠️ {pkg_missing} requieren instalación de driver."
        else:
            msg += " ✅ Todos con driver OK."
        
        self.log_msg(msg)
        for w in self.device_widgets:
            w.destroy()
        self.device_widgets = []
        self.device_selections = {}
        for dev in devices:
            var = ctk.BooleanVar(value=True)
            var.trace_add("write", lambda *_: self.update_selection_count())
            self.device_selections[dev['serial']] = var
            self.create_device_card(dev)
        self.update_selection_count()
        self.update_account_creator_devices()
        self.scan_btn.configure(state="normal", text="🔍 1. Escanear Dispositivos")

    def create_device_card(self, dev):
        card = ctk.CTkFrame(self.dev_frame, fg_color="#1E1E1E", corner_radius=10, border_width=1, border_color="#333333")
        card.pack(fill="x", pady=8, padx=5)
        conn_type = "📶 WiFi" if dev['is_wifi'] else "🔌 USB"
        
        # Checkbox for device selection
        check_fr = ctk.CTkFrame(card, fg_color="transparent", width=40)
        check_fr.pack(side="left", padx=(10, 0), pady=10)
        sel_var = self.device_selections.get(dev['serial'])
        if sel_var:
            cb = ctk.CTkCheckBox(check_fr, text="", variable=sel_var, width=24, checkbox_width=22, checkbox_height=22)
            cb.pack()
        
        left_fr = ctk.CTkFrame(card, fg_color="transparent")
        left_fr.pack(side="left", padx=5, pady=10, fill="y")
        model_name = dev.get('model', 'Phone')
        title = ctk.CTkLabel(left_fr, text=f"{model_name}", font=("Arial", 16, "bold"))
        title.pack(anchor="w")
        # Driver status on left
        pkg_ok = dev.get('pkg_ok', False)
        status_color = "#10B981" if pkg_ok else "#EF4444"
        status_txt = "✅ Driver OK" if pkg_ok else "❌ Sin Driver"
        ctk.CTkLabel(left_fr, text=status_txt, text_color=status_color, font=("Arial", 11, "bold")).pack(anchor="w")
        ctk.CTkLabel(left_fr, text=f"{conn_type}", text_color="gray").pack(anchor="w")
        
        mid_fr = ctk.CTkFrame(card, fg_color="transparent")
        mid_fr.pack(side="left", padx=20, pady=10, fill="y", expand=True)
        # Timer
        timer_lbl = ctk.CTkLabel(mid_fr, text="⏳ Esperando...", font=("Arial", 11), text_color="#94A3B8")
        timer_lbl.pack(anchor="w")
        # IP Display
        ctk.CTkLabel(mid_fr, text="IP EXTERNA:", font=("Arial", 10), text_color="gray").pack(anchor="w")
        ip_val_lbl = ctk.CTkLabel(mid_fr, text="Detectando...", text_color="#22D3EE", font=("Arial", 15, "bold"))
        ip_val_lbl.pack(anchor="w")
        
        # Traffic on right
        right_info = ctk.CTkFrame(card, fg_color="transparent")
        right_info.pack(side="right", padx=15)
        traffic_lbl = ctk.CTkLabel(right_info, text="MB: 0.0↓ 0.0↑", font=("Courier New", 12))
        traffic_lbl.pack()
        # Health status indicator
        health_lbl = ctk.CTkLabel(right_info, text="⭕ Sin estado", font=("Arial", 10), text_color="#64748B")
        health_lbl.pack(pady=(5, 0))

        # Interaction buttons row
        actions_fr = ctk.CTkFrame(right_info, fg_color="transparent")
        actions_fr.pack(pady=(5, 0))
        serial = dev['serial']
        ctk.CTkButton(actions_fr, text="👁️", width=36, height=26, fg_color="#3B82F6",
                      command=lambda s=serial: self.launch_scrcpy(s),
                      font=("Arial", 13)).pack(side="left", padx=2)
        focus_btn = ctk.CTkButton(actions_fr, text="🎯", width=36, height=26, fg_color="#8B5CF6",
                      command=lambda s=serial: self.toggle_focus(s),
                      font=("Arial", 13))
        focus_btn.pack(side="left", padx=2)
        ctk.CTkButton(actions_fr, text="📋", width=36, height=26, fg_color="#059669",
                      command=lambda s=serial: self.paste_to_device(s),
                      font=("Arial", 13)).pack(side="left", padx=2)

        self.device_ui_map[dev['serial']] = {
            "card": card,
            "timer": timer_lbl,
            "ip": ip_val_lbl,
            "traffic": traffic_lbl,
            "health": health_lbl,
            "focus_btn": focus_btn
        }
        self.device_widgets.append(card)

    def select_all_devices(self):
        for var in self.device_selections.values():
            var.set(True)

    def deselect_all_devices(self):
        for var in self.device_selections.values():
            var.set(False)

    def update_selection_count(self):
        total = len(self.device_selections)
        selected = sum(1 for v in self.device_selections.values() if v.get())
        # Show count and hint about batch vs selected
        try:
            batch = int(self.batch_entry.get())
        except ValueError:
            batch = selected
        if selected > 0 and batch > selected:
            self.selection_count_lbl.configure(text=f"{selected} de {total} sel. (lote {batch} > sel., se usarán {selected})")
        elif selected > 0 and batch < selected:
            lotes = -(-selected // batch)  # ceil division
            self.selection_count_lbl.configure(text=f"{selected} de {total} sel. → {lotes} lotes de {batch}")
        else:
            self.selection_count_lbl.configure(text=f"{selected} de {total} seleccionados")

    def get_selected_devices(self):
        """Returns only the scanned devices whose checkbox is checked."""
        return [d for d in self.scanned_devices if self.device_selections.get(d['serial'], ctk.BooleanVar(value=False)).get()]

    def launch_scrcpy(self, serial):
        """Launch scrcpy to mirror device screen."""
        base = os.path.dirname(os.path.abspath(__file__))
        scrcpy_exe = os.path.join(base, "scrcpy", "scrcpy.exe")
        if not os.path.exists(scrcpy_exe):
            messagebox.showerror("scrcpy no encontrado",
                "scrcpy no está instalado.\n\nCierra la app y ejecuta START_APP.bat para que se descargue automáticamente.")
            return
        try:
            subprocess.Popen([scrcpy_exe, "-s", serial, "--window-title", f"📱 {serial}"],
                             cwd=os.path.join(base, "scrcpy"))
            self.log_msg(f"👁️ Pantalla abierta: {serial}")
        except Exception as e:
            self.log_msg(f"❌ Error al abrir pantalla: {e}", "error")

    def toggle_focus(self, serial):
        """Give full bandwidth to one device by pausing all others."""
        if not self.engine.running:
            messagebox.showinfo("Info", "El túnel debe estar activo para usar Focus.")
            return

        ui = self.device_ui_map.get(serial, {})
        focus_btn = ui.get("focus_btn")

        # Check if already in focus mode for this device
        if hasattr(self, '_focus_serial') and self._focus_serial == serial:
            # Restore all paused devices
            self.log_msg(f"↩️ Restaurando todos los dispositivos...")
            for paused_serial in self._focus_paused:
                self.runner.start(paused_serial)
            self._focus_serial = None
            self._focus_paused = []
            if focus_btn:
                focus_btn.configure(text="🎯", fg_color="#8B5CF6")
            self.log_msg(f"✅ Todos los dispositivos restaurados.")
            return

        # Enter focus mode: pause gnirehtet on all OTHER active devices
        active_serials = [d['serial'] for d in self.engine.active_devices]
        if serial not in active_serials:
            messagebox.showinfo("Info", f"El dispositivo {serial[-4:]} no está en el lote activo.")
            return

        others = [s for s in active_serials if s != serial]
        if not others:
            messagebox.showinfo("Info", "Solo hay 1 dispositivo activo, ya tiene todo el tráfico.")
            return

        self._focus_serial = serial
        self._focus_paused = others
        self.log_msg(f"🎯 FOCUS → {serial[-4:]} | Pausando {len(others)} dispositivo(s)...", "warn")

        def _do_focus():
            for other in others:
                self.runner.stop(other)
            self.after(0, lambda: self.log_msg(f"🎯 {serial[-4:]} tiene todo el ancho de banda. Clic 🎯 de nuevo para restaurar."))

        threading.Thread(target=_do_focus, daemon=True).start()
        if focus_btn:
            focus_btn.configure(text="↩️", fg_color="#EF4444")

    def paste_to_device(self, serial):
        """Open dialog to paste text to device via ADB."""
        dialog = ctk.CTkInputDialog(text=f"Texto a pegar en {serial[-8:]}:", title="📋 Pegar en Dispositivo")
        text = dialog.get_input()
        if text and text.strip():
            # Escape special characters for ADB shell input
            safe_text = text.replace("\\", "\\\\").replace("\"", "\\\"").replace("'", "\\'")
            safe_text = safe_text.replace(" ", "%s").replace("&", "\\&").replace(";", "\\;")
            safe_text = safe_text.replace("(", "\\(").replace(")", "\\)").replace("|", "\\|")

            def _paste():
                # Method 1: Try clipboard broadcast (needs Clipper or similar)
                self.adb.run_command(["shell", "input", "text", safe_text], serial)
                self.after(0, lambda: self.log_msg(f"📋 Texto enviado a {serial[-4:]}: \"{text[:30]}...\"" if len(text) > 30 else f"📋 Texto enviado a {serial[-4:]}: \"{text}\""))

            threading.Thread(target=_paste, daemon=True).start()

    def run_global_report(self):
        ReporteGlobalWindow(self, self.adb, self.engine)

    def test_proxies(self):
        raw_proxies = self.proxy_textbox.get("1.0", "end").strip().split('\n')
        proxies = [from_engine for from_engine in [p.strip() for p in raw_proxies if p.strip() and not p.startswith("#")] if from_engine]
        from rotation_engine import format_proxy
        formatted = [format_proxy(p) for p in proxies if format_proxy(p)]
        if not formatted:
            messagebox.showwarning("Vacío", "Pega proxies para probarlos primero.")
            return

        def _on_test_finish(alive_list):
            self.proxy_textbox.delete("1.0", "end")
            self.proxy_textbox.insert("end", "# Proxies Testeados (Limpios)\n")
            for p in alive_list:
                self.proxy_textbox.insert("end", p + "\n")
            self.log_msg(f"Test finalizado. {len(alive_list)} proxies guardados y limpios.")
            self.save_config()

        ProxyTesterWindow(self, formatted, _on_test_finish)

    def install_gnirehtet(self):
        devices = self.adb.list_devices()
        missing = [d for d in devices if not d.get('pkg_ok')]
        if not missing:
            messagebox.showinfo("Listo", "Todos los dispositivos ya tienen el driver instalado.")
            return
            
        def _installer():
            total = len(missing)
            self.log_msg(f"⚙️ Instalando driver en {total} dispositivos faltantes...", "warn")
            for i, dev in enumerate(missing):
                s = dev['serial']
                self.log_msg(f"📦 Instalando en {dev['model']} ({s})...")
                self.adb.install_apk(s, "gnirehtet.apk")
            self.log_msg(f"✅ ¡Instalación completada en {total} equipos!", "info")
            self.after(0, self.scan_devices) # Refresh to show green checks
            
        threading.Thread(target=_installer, daemon=True).start()

    def parse_inputs(self):
        try:
            if hasattr(self, 'network_rotation_enabled') and not self.network_rotation_enabled.get():
                return 9999, 999999.0
            b_size = int(self.batch_entry.get())
            mins = float(self.mins_entry.get())
            return b_size, mins
        except ValueError:
            messagebox.showerror("Error", "Lotes y minutos numéricos.")
            return None, None

    def attempt_start(self):
        # Check that devices are selected
        selected = self.get_selected_devices()
        if not selected:
            messagebox.showerror("⛔ Sin Dispositivos", "No hay dispositivos seleccionados.\nEscanea y marca los que quieras usar.")
            return

        raw_proxies = self.proxy_textbox.get("1.0", "end").strip().split('\n')
        proxies = [p.strip() for p in raw_proxies if p.strip() and not p.startswith("#")]
        
        bot_only = getattr(self, 'bot_only_var', ctk.BooleanVar(value=False)).get()
        
        if not proxies:
            if self.no_proxy_var.get() or bot_only:
                self.save_config()
                self.start_farm([], tunnel_disabled=bot_only)
            else:
                self.no_proxy_strikes += 1
                if self.no_proxy_strikes >= 3:
                    if messagebox.askyesno("Info", f"Iniciando {len(selected)} dispositivos sin proxies. ¿Seguro?"): self.start_farm([])
                else:
                    messagebox.showerror("⛔ Faltan Proxies", "No ingresaste los Proxies.\n\n(O marca la casilla 'Modo Sin Proxy' o 'Modo Solo Bot')")
        else:
            self.save_config()
            self.start_farm(proxies, tunnel_disabled=bot_only)

    def assign_proxies(self):
        devices = self.adb.list_devices()
        if not devices:
            messagebox.showwarning("Vacío", "Escanea dispositivos primero para poder mapearlos.")
            return
        raw_proxies = self.proxy_textbox.get("1.0", "end").strip().split('\n')
        from rotation_engine import format_proxy
        proxies = [format_proxy(p) for p in raw_proxies if format_proxy(p)]
        if not proxies:
            messagebox.showwarning("Vacío", "Pega proxies en la lista primero.")
            return
            
        ProxyAssignmentWindow(self, devices, proxies)

    def start_farm(self, proxies, tunnel_disabled=False):
        devices = self.get_selected_devices()
        b_size, mins = self.parse_inputs()
        
        if b_size is None:
            return
            
        if not devices:
            messagebox.showerror("Falla Fatal", "No hay dispositivos seleccionados. Escanea y marca los que quieras usar.")
            self.log_msg("Intento de inicio abortado: 0 celulares seleccionados.", "warn")
            self.start_btn.configure(state="normal")
            return
            
        self.save_config()
        if tunnel_disabled:
            self.log_msg(f"📡 Iniciando en MODO SOLO BOT (Wifi Nativo) con {len(devices)} dispositivos...")
        else:
            self.log_msg(f"▶️ Iniciando Secuencia con {len(devices)} dispositivos seleccionados...")
        SetupProgressWindow(self, devices, proxies, b_size, mins, tunnel_disabled=tunnel_disabled)
        self.no_proxy_strikes = 0
        self.batch_entry.configure(state="disabled")
        self.mins_entry.configure(state="disabled")

    def repair_failed_devices(self):
        """Find devices with failed health and attempt reconnection."""
        failed = [s for s, h in self.device_health.items() if h.get("status") in ("dead", "warning")]
        if not failed:
            messagebox.showinfo("Sin Fallos", "No hay dispositivos caídos para reparar.")
            return

        self.repair_btn.configure(state="disabled", text="🔧 Reparando...")
        self.log_msg(f"🔧 Iniciando reparación de {len(failed)} dispositivo(s)...", "warn")

        def _repair_thread():
            results = {"fixed": 0, "still_broken": 0}
            for serial in failed:
                self.log_msg(f"  🔄 Reconectando {serial}...")
                success, reason = self.engine.reconnect_device(serial)
                if success:
                    results["fixed"] += 1
                    self.log_msg(f"  ✅ {serial}: {reason}")
                    self.device_health[serial] = {"status": "ok", "reason": reason}
                    self.last_ip_check[serial] = 0  # Force fresh IP check on next cycle
                else:
                    results["still_broken"] += 1
                    self.log_msg(f"  ❌ {serial}: {reason}", "error")
                    self.device_health[serial] = {"status": "dead", "reason": reason}

            # Summary
            summary = f"🔧 Resultado: {results['fixed']} reparados"
            if results["still_broken"] > 0:
                summary += f", {results['still_broken']} siguen fallando"
                self.log_msg(summary, "warn")
            else:
                self.log_msg(summary)

            self.after(0, lambda: self.repair_btn.configure(state="normal", text="🔧 REPARAR CAÍDOS"))

        threading.Thread(target=_repair_thread, daemon=True).start()

    def panic_clean(self):
        PanicProgressWindow(self, self.engine, self.runner, self.adb)

    def toggle_pause(self):
        if not self.engine.running: return
        if not self.engine.paused:
            self.engine.paused = True
            self.pause_btn.configure(text="▶️ REANUDAR TÚNEL", fg_color="green")
            self.status_lbl.configure(text="Estado: PAUSADO ⏸️ — Puedes Escanear/Agregar dispositivos", text_color="orange")
            self.batch_entry.configure(state="normal")
            self.mins_entry.configure(state="normal")
            self.scan_btn.configure(state="normal")
            self.log_msg("⏸️ Túnel en Pausa. Puedes escanear, agregar/quitar dispositivos y editar configuraciones.", "warn")
        else:
            selected = self.get_selected_devices()
            if not selected:
                messagebox.showwarning("⚠️ Sin Selección", "No hay dispositivos seleccionados.\nMarca al menos uno antes de reanudar.")
                return

            b_size, mins = self.parse_inputs()
            if b_size is None: return

            # Re-read proxies in case user edited them during pause
            raw_proxies = self.proxy_textbox.get("1.0", "end").strip().split('\n')
            from rotation_engine import format_proxy
            new_proxies = [format_proxy(p) for p in raw_proxies if p.strip() and not p.startswith("#") and format_proxy(p)]

            # Update engine with new device list and config
            self.engine.all_devices = selected
            self.engine.batch_size = b_size
            self.engine.interval_minutes = mins
            if new_proxies:
                self.engine.proxies = new_proxies
            self.engine.current_batch_index = 0
            self.engine.next_rotation_time = 0  # Force immediate re-batch

            self.engine.paused = False
            self.pause_btn.configure(text="⏸️ PAUSAR (Editar Num/Hora)", fg_color="#F59E0B")
            self.batch_entry.configure(state="disabled")
            self.mins_entry.configure(state="disabled")
            self.save_config()
            self.log_msg(f"▶️ Reanudado con {len(selected)} dispositivos seleccionados. Aplicando cambios...")

    def on_engine_update(self, event_type):
        if event_type == "COMPLETED":
            self.log_msg("✅ Ciclo completado. Granja terminada.")
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.status_lbl.configure(text="Estado: COMPLETADO 🏁")

    def update_timer(self):
        if self.engine.running and not self.engine.paused:
            rem = int(self.engine.next_rotation_time - time.time())
            if rem > 0:
                m = rem // 60
                s = rem % 60
                self.status_lbl.configure(text=f"🔄 Lote {self.engine.current_batch_index + 1} ACTIVO | Cambio en: {m}m {s}s", text_color="lightgreen")
            else:
                self.status_lbl.configure(text="🔄 Cambiando de lote u Operando Stealth...", text_color="yellow")
        self.after(1000, self.update_timer)

    def update_traffic(self):
        if self.engine.running:
            devices = self.engine.all_devices.copy()
            active_serials = [d['serial'] for d in self.engine.active_devices]
            
            def _fetch():
                updates = {}
                threads = []
                
                def _fetch_one(serial, is_active):
                    rx_mb, tx_mb = 0.0, 0.0
                    external_ip = "---"
                    health = "offline"
                    health_reason = ""
                    if is_active:
                        # 1. Check tunnel interface (tun0 or vpn only, NOT rmnet)
                        has_tunnel = False
                        stdout, _, _ = self.adb.run_command(["shell", "cat", "/proc/net/dev"], serial)
                        for line in stdout.split('\n'):
                            if 'tun0:' in line or 'vpn' in line:
                                has_tunnel = True
                            # Traffic: collect from tun0, vpn, or rmnet
                            if 'tun0:' in line or 'vpn' in line or 'rmnet' in line:
                                try:
                                    p = line.split(':')[1].split()
                                    rx_mb += float(p[0]) / (1024 * 1024)
                                    tx_mb += float(p[8]) / (1024 * 1024)
                                except: pass
                        
                        if not has_tunnel:
                            health = "dead"
                            health_reason = "Sin túnel (tun0 ausente)"
                        
                        # 2. IP check from PC through local proxy port (every 60s)
                        last = self.last_ip_check.get(serial, 0)
                        if (time.time() - last) > 60:
                            port = self.engine.active_ports.get(serial)
                            if port:
                                try:
                                    import requests
                                    px = {"http": f"http://127.0.0.1:{port}", "https": f"http://127.0.0.1:{port}"}
                                    res = requests.get("https://api.ipify.org?format=json", proxies=px, timeout=6)
                                    ip = res.json().get("ip", "")
                                    if ip:
                                        external_ip = ip
                                        self.last_ip_check[serial] = time.time()
                                        health = "ok"
                                        health_reason = "Conexión OK"
                                        self.health_fail_count[serial] = 0
                                    else:
                                        raise Exception("empty")
                                except Exception:
                                    fails = self.health_fail_count.get(serial, 0) + 1
                                    self.health_fail_count[serial] = fails
                                    if fails >= 2:
                                        external_ip = "Sin respuesta"
                                        if has_tunnel:
                                            health = "warning"
                                            health_reason = "Proxy sin respuesta"
                                        else:
                                            health = "dead"
                                            health_reason = "Sin túnel ni internet"
                                    else:
                                        # First failure: keep previous state, don't alarm yet
                                        prev = self.device_health.get(serial, {})
                                        health = prev.get("status", "ok" if has_tunnel else "dead")
                                        health_reason = prev.get("reason", "Verificando...")
                                        ui = self.device_ui_map.get(serial)
                                        if ui: external_ip = ui['ip'].cget("text")
                                        self.last_ip_check[serial] = time.time()
                            else:
                                # No proxy port assigned: tunnel-only mode
                                if has_tunnel:
                                    health = "ok"
                                    health_reason = "Túnel directo (sin proxy)"
                                    external_ip = "Directo"
                                self.last_ip_check[serial] = time.time()
                        else:
                            # Between checks: keep current state
                            ui = self.device_ui_map.get(serial)
                            if ui: external_ip = ui['ip'].cget("text")
                            prev = self.device_health.get(serial, {})
                            if prev:
                                health = prev.get("status", "ok" if has_tunnel else "dead")
                                health_reason = prev.get("reason", "")
                            elif has_tunnel:
                                health = "ok"
                                health_reason = "Túnel activo"
                    
                    self.device_health[serial] = {"status": health, "reason": health_reason}
                    updates[serial] = (is_active, rx_mb, tx_mb, external_ip, health, health_reason)

                for dev in devices:
                    t = threading.Thread(target=_fetch_one, args=(dev['serial'], dev['serial'] in active_serials))
                    t.start()
                    threads.append(t)
                
                for t in threads: t.join()
                self.after(0, self._apply_traffic_updates, updates)
                
            threading.Thread(target=_fetch, daemon=True).start()
        self.after(5000, self.update_traffic)

    def _apply_traffic_updates(self, updates):
        now = time.time()
        rem_sec = max(0, int(self.engine.next_rotation_time - now))
        mins = rem_sec // 60
        secs = rem_sec % 60
        timer_text = f"⏳ Rotación: {mins:02d}:{secs:02d}"

        has_failed = False
        for serial, (is_active, rx, tx, ip, health, health_reason) in updates.items():
            ui = self.device_ui_map.get(serial)
            if ui:
                # 1. Update Timer & IP labels
                if is_active:
                    ui['timer'].configure(text=timer_text, text_color="#FCD34D")
                    if ip != "---":
                        ui['ip'].configure(text=ip)
                else:
                    ui['timer'].configure(text="🕒 En Espera...", text_color="#64748B")
                    ui['ip'].configure(text="Túnel Cerrado")
                
                # 2. Update Traffic info
                ui['traffic'].configure(text=f"MB: {rx:.1f}↓ {tx:.1f}↑")
                
                # 3. Health status display
                if is_active:
                    if health == "ok":
                        ui['health'].configure(text="🟢 OK", text_color="#10B981")
                        bg_color = "#064E3B"
                    elif health == "warning":
                        ui['health'].configure(text=f"🟡 {health_reason}", text_color="#F59E0B")
                        bg_color = "#78350F"
                        has_failed = True
                    elif health == "dead":
                        ui['health'].configure(text=f"🔴 {health_reason}", text_color="#EF4444")
                        bg_color = "#7F1D1D"
                        has_failed = True
                    else:
                        ui['health'].configure(text="⭕ Verificando...", text_color="#64748B")
                        bg_color = "#064E3B"
                else:
                    ui['health'].configure(text="💤 Inactivo", text_color="#475569")
                    bg_color = "#1E1E1E"
                
                ui['card'].configure(fg_color=bg_color)
            
            # 4. Global traffic list update
            if health == "ok":
                color = "#10B981"
                estado_txt = "🟢 OK"
            elif health == "warning":
                color = "#F59E0B"
                estado_txt = "🟡 LENTO"
            elif health == "dead" and is_active:
                color = "#EF4444"
                estado_txt = "🔴 CAÍDO"
            elif is_active:
                color = "#94A3B8"
                estado_txt = "⏳ CHECK"
            else:
                color = "gray"
                estado_txt = "🌙"
            text_disp = f"{estado_txt} │📱 {serial} │ {rx:.1f}MB↓ {tx:.1f}MB↑ │ IP: {ip}"

            self.traf_data[serial] = {
                "is_active": is_active, "rx": rx, "tx": tx, "ip": ip,
                "text": text_disp, "color": color
            }
            
            if serial not in self.traf_widgets:
                fr = ctk.CTkFrame(self.traf_frame)
                fr.pack(fill="x", pady=2)
                lbl = ctk.CTkLabel(fr, text=text_disp, font=("Arial", 12), text_color=color)
                lbl.pack(anchor="w", padx=5)
                self.traf_widgets[serial] = {"frame": fr, "label": lbl}
            else:
                self.traf_widgets[serial]["label"].configure(text=text_disp, text_color=color)

        # Enable repair button if there are failures
        if has_failed:
            self.repair_btn.configure(state="normal")
        else:
            self.repair_btn.configure(state="disabled")

        # Auto-apply current sort if one is active
        if self.traf_sort_mode:
            self.sort_traffic(self.traf_sort_mode)

    def sort_traffic(self, mode):
        """Reorder traffic widgets by serial or connection status."""
        self.traf_sort_mode = mode
        if not self.traf_data:
            return

        serials = list(self.traf_data.keys())
        if mode == "serial":
            serials.sort()
            self.traf_sort_lbl.configure(text="Ordenado: A → Z (Serial)")
        elif mode == "connection":
            serials.sort(key=lambda s: (not self.traf_data[s]["is_active"], s))
            self.traf_sort_lbl.configure(text="Ordenado: Activos primero")

        for serial in serials:
            w = self.traf_widgets.get(serial)
            if w:
                w["frame"].pack_forget()
                w["frame"].pack(fill="x", pady=2)

    def inject_spotify_playlist(self):
        url = self.spotify_entry.get().strip()
        if not url:
            messagebox.showwarning("Advertencia", "Pega un enlace de Spotify primero.")
            return
            
        devices = self.adb.list_devices()
        if not devices:
            messagebox.showwarning("Advertencia", "No hay dispositivos conectados.")
            return
            
        self.log_msg(f"🎧 Inyectando lista de Spotify en {len(devices)} celulares...", "warn")
        
        def _inject():
            for dev in devices:
                s = dev['serial']
                self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url], s)
                time.sleep(0.3)
            self.after(0, lambda: self.log_msg("✅ ¡Lista de Spotify inyectada! Revisa las pantallas.", "info"))
            self.after(0, lambda: messagebox.showinfo("Éxito", "La lista fue enviada a todos los celulares.\nRecuerda darle a 'Play' o al 'Corazón' tú mismo usando SCRCPY."))
            
        threading.Thread(target=_inject, daemon=True).start()
    def watchdog_ghost_loop(self):
        import random
        while True:
            time.sleep(60) # Wait 60 seconds before checking
            try:
                if not hasattr(self, 'engine') or not self.engine.active_devices:
                    continue
                    
                for dev in list(self.engine.active_devices):
                    serial = dev['serial']
                    
                    if self.is_device_locked(serial):
                        continue
                    
                    # Watchdog: Every 10 mins (approx 10% chance per minute to check app focus)
                    if self.watchdog_enabled.get() and random.randint(1, 10) == 1:
                        target_pkg = "com.spotify.music" if self.master_mode.get() == "spotify" else "com.google.android.youtube"
                        if self.master_mode.get() == "youtube":
                            if "music.youtube" in self.youtube_textbox.get("1.0", "end"):
                                target_pkg = "com.google.android.apps.youtube.music"
                        
                        # Check if target app is in foreground
                        out = self.adb.run_command(["shell", "dumpsys", "window", "windows", "|", "grep", "-E", "'mCurrentFocus|mFocusedApp'"], serial)
                        if out and target_pkg not in out:
                            self.log_msg(f"🛡️ Watchdog: {target_pkg} se cerró en {serial[-4:]}. Restaurando...", "warn")
                            # Trigger re-injection
                            if self.master_mode.get() == "spotify":
                                playlists = [p.strip() for p in self.playlist_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
                                if playlists: self._inject_playlist_to_single(serial, random.choice(playlists))
                            else:
                                urls = [p.strip() for p in self.youtube_textbox.get("1.0", "end").strip().split('\n') if p.strip()]
                                if urls: self._inject_youtube_to_single(serial, random.choice(urls))

                    # Ghost Touch: Random volume/scroll (aprox 1 o 2 veces al día por dispositivo)
                    # El loop corre cada 60s (1440 al día). Probabilidad 1/720 da ~2 veces al día.
                    if self.ghost_enabled.get() and random.randint(1, 720) == 1:
                        # 50% chance of volume change, 50% chance of swipe
                        if random.choice([True, False]):
                            # Bajar volumen 15 veces para asegurar el 0%
                            for _ in range(15):
                                self.adb.run_command(["shell", "input", "keyevent", "25"], serial)
                            time.sleep(0.5)
                            # Subir volumen de 2 a 3 veces (~12% a 18% máximo)
                            for _ in range(random.randint(2, 3)):
                                self.adb.run_command(["shell", "input", "keyevent", "24"], serial)
                        else:
                            # Random mini swipe
                            self.adb.run_command(["shell", "input", "swipe", "500", "1000", "500", "800", "200"], serial)
            except Exception as e:
                pass

    def build_accounts_tab(self):
        self.tab_accounts.grid_columnconfigure(0, weight=1)
        self.tab_accounts.grid_columnconfigure(1, weight=1)
        self.tab_accounts.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Controles
        left_frame = ctk.CTkFrame(self.tab_accounts, fg_color="#1E293B", corner_radius=8)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(left_frame, text="👤 Creador de Cuentas Automático", font=("Arial", 16, "bold"), text_color="#F59E0B").pack(pady=10)

        # Selector de Celular
        ctk.CTkLabel(left_frame, text="📱 Seleccionar Celular:", font=("Arial", 12)).pack(pady=(10, 2))
        self.account_device_combo = ctk.CTkComboBox(left_frame, values=["No hay celulares"], width=250)
        self.account_device_combo.pack(pady=5)

        # Prefijo del correo
        ctk.CTkLabel(left_frame, text="📧 Prefijo del Correo (Aleatorio):", font=("Arial", 11)).pack(pady=(10, 2))
        self.acc_email_prefix_entry = ctk.CTkEntry(left_frame, placeholder_text="Ej: user.farm", width=250)
        self.acc_email_prefix_entry.pack(pady=2)
        self.acc_email_prefix_entry.insert(0, "andro.bot")

        ctk.CTkLabel(left_frame, text="🌐 Dominio del Correo:", font=("Arial", 11)).pack(pady=(5, 2))
        self.acc_email_domain_entry = ctk.CTkEntry(left_frame, placeholder_text="gmail.com", width=250)
        self.acc_email_domain_entry.pack(pady=2)
        self.acc_email_domain_entry.insert(0, "gmail.com")

        # Contraseña
        ctk.CTkLabel(left_frame, text="🔑 Contraseña Inicial:", font=("Arial", 11)).pack(pady=(10, 2))
        self.acc_password_entry = ctk.CTkEntry(left_frame, placeholder_text="Ej: Androide10", width=250)
        self.acc_password_entry.pack(pady=2)
        self.acc_password_entry.insert(0, "Androide10")

        # Botones de Acción
        ctk.CTkLabel(left_frame, text="⚡ Controles de Automatización", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        self.btn_start_acc = ctk.CTkButton(left_frame, text="🌐 1. Abrir Registro Chrome (Visible)", fg_color="#10B981", hover_color="#059669", command=self.start_spotify_account_creation, height=35)
        self.btn_start_acc.pack(pady=5, fill="x", padx=30)
        
        self.btn_login_acc = ctk.CTkButton(left_frame, text="🚀 2. Iniciar Sesión App (Auto A Ciegas)", fg_color="#6366F1", hover_color="#4F46E5", command=self.start_spotify_login, height=35)
        self.btn_login_acc.pack(pady=5, fill="x", padx=30)
        
        # Redundancias por si falla uiautomator
        manual_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        manual_frame.pack(pady=10)
        ctk.CTkButton(manual_frame, text="📧 Escribir Correo", width=120, fg_color="#3B82F6", command=self.manual_type_email).pack(side="left", padx=5)
        ctk.CTkButton(manual_frame, text="🔑 Escribir Clave", width=120, fg_color="#F59E0B", command=self.manual_type_password).pack(side="left", padx=5)

        # Panel Derecho: Logs
        right_frame = ctk.CTkFrame(self.tab_accounts, fg_color="#0F172A", corner_radius=8)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Registro del Proceso en Vivo", font=("Arial", 14, "bold"), text_color="#38BDF8").pack(pady=10)
        self.acc_log_box = ctk.CTkTextbox(right_frame, height=500)
        self.acc_log_box.pack(padx=10, fill="both", expand=True, pady=5)
        
        self.update_account_creator_devices()

    def update_account_creator_devices(self):
        if not hasattr(self, 'account_device_combo'): return
        devices = getattr(self, 'scanned_devices', [])
        serials = [dev['serial'] for dev in devices]
        if serials:
            self.account_device_combo.configure(values=serials)
            if self.account_device_combo.get() not in serials:
                self.account_device_combo.set(serials[0])
        else:
            self.account_device_combo.configure(values=["No hay celulares"])
            self.account_device_combo.set("No hay celulares")

    def acc_log(self, text, level="info"):
        prefix = "ℹ️"
        if level == "error": prefix = "❌"
        elif level == "warn": prefix = "⚠️"
        elif level == "success": prefix = "✅"
        
        def _do():
            if hasattr(self, 'acc_log_box'):
                self.acc_log_box.insert("end", f"{prefix} {text}\n")
                self.acc_log_box.see("end")
        self.after(0, _do)

    def manual_type_email(self):
        serial = self.account_device_combo.get()
        if not serial or serial == "No hay celulares":
            self.acc_log("Selecciona un celular primero", "warn")
            return
        
        import random
        prefix = self.acc_email_prefix_entry.get().strip()
        domain = self.acc_email_domain_entry.get().strip()
        rnd_num = random.randint(100000, 999999)
        email = f"{prefix}{rnd_num}@{domain}"
        
        self.acc_log(f"Escribiendo correo manual: {email} en {serial}...")
        self.adb.run_command(["shell", "input", "text", email], serial)

    def manual_type_password(self):
        serial = self.account_device_combo.get()
        if not serial or serial == "No hay celulares":
            self.acc_log("Selecciona un celular primero", "warn")
            return
        pwd = self.acc_password_entry.get().strip()
        self.acc_log(f"Escribiendo contraseña manual: {pwd} en {serial}...")
        self.adb.run_command(["shell", "input", "text", pwd], serial)

    def find_and_click_by_text(self, serial, target_texts):
        self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dump_{serial}.xml")
        
        self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path], serial)
        if not os.path.exists(local_path):
            return False
            
        import xml.etree.ElementTree as ET
        import re
        
        try:
            tree = ET.parse(local_path)
            root = tree.getroot()
            os.remove(local_path)
            
            for node in root.iter():
                text_attr = node.get("text", "")
                desc_attr = node.get("content-desc", "")
                
                match = False
                for target in target_texts:
                    if target.lower() in text_attr.lower() or target.lower() in desc_attr.lower():
                        match = True
                        break
                        
                if match:
                    bounds = node.get("bounds", "")
                    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if m:
                        x1, y1, x2, y2 = map(int, m.groups())
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        self.acc_log(f"Encontrado botón '{text_attr}' en ({cx}, {cy}). Pulsando...")
                        self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                        return True
        except Exception as e:
            self.acc_log(f"Error al analizar pantalla: {str(e)}", "warn")
            if os.path.exists(local_path):
                os.remove(local_path)
        return False

    def start_spotify_account_creation(self):
        serial = self.account_device_combo.get()
        if not serial or serial == "No hay celulares":
            self.acc_log("Selecciona un celular primero", "warn")
            return
            
        self.btn_start_acc.configure(state="disabled", text="⏳ Registrando...")
        threading.Thread(target=self._spotify_account_creator_thread, args=(serial,), daemon=True).start()

    def _spotify_account_creator_thread(self, serial):
        import random
        
        try:
            prefix = self.acc_email_prefix_entry.get().strip()
            domain = self.acc_email_domain_entry.get().strip()
            pwd = self.acc_password_entry.get().strip()
            rnd_num = random.randint(100000, 999999)
            email = f"{prefix}{rnd_num}@{domain}"
            
            self.acc_log(f"🚀 Iniciando Registro en Chrome para {serial}", "success")
            self.acc_log(f"Correo: {email}")
            self.acc_log(f"Clave: {pwd}")
            
            # Bloquear la pantalla en vertical (Portrait) para que no gire de lado
            self.acc_log("Forzando orientación vertical (Portrait)...")
            self.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
            self.adb.run_command(["shell", "settings", "put", "system", "user_rotation", "0"], serial)
            time.sleep(1.0)
            
            # Abrir registro de Spotify en Chrome
            signup_url = "https://www.spotify.com/signup"
            self.acc_log("Abriendo Chrome en la página de registro...")
            self.adb.run_command(["shell", "am", "start", "-n", "com.android.chrome/com.google.android.apps.chrome.Main", "-d", f"'{signup_url}'"], serial)
            
            self.acc_log("✅ Navegador abierto con éxito.", "success")
            self.acc_log("💡 INSTRUCCIONES: Toca el campo de Correo en el navegador y pulsa el botón '📧 Escribir Correo' para rellenarlo instantáneamente sin escribir a mano.", "info")
            self.acc_log("💡 Del mismo modo, usa '🔑 Escribir Clave' cuando la página te pida la contraseña.", "info")
            
        except Exception as e:
            self.acc_log(f"Falla en el proceso: {str(e)}", "error")
            
        self.after(0, lambda: self.btn_start_acc.configure(state="normal", text="🌐 1. Abrir Registro Chrome (Visible)"))

    def start_spotify_login(self):
        serial = self.account_device_combo.get()
        if not serial or serial == "No hay celulares":
            self.acc_log("Selecciona un celular primero", "warn")
            return
            
        self.btn_login_acc.configure(state="disabled", text="⏳ Iniciando sesión...")
        threading.Thread(target=self._spotify_login_thread, args=(serial,), daemon=True).start()

    def _spotify_login_thread(self, serial):
        try:
            email_input = self.acc_email_prefix_entry.get().strip()
            domain = self.acc_email_domain_entry.get().strip()
            if "@" in email_input:
                email = email_input
            else:
                last_log = self.acc_log_box.get("1.0", "end")
                import re
                emails_found = re.findall(r"Correo:\s+([a-zA-Z0-9\._\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,4})", last_log)
                if emails_found:
                    email = emails_found[-1]
                else:
                    self.acc_log("No se detectó correo generado en el log, ingresando formato base...", "warn")
                    email = f"{email_input}@{domain}"
                    
            pwd = self.acc_password_entry.get().strip()
            
            self.acc_log(f"🔑 Iniciando Login Automático en {serial} (A Ciegas)", "success")
            self.acc_log(f"Correo: {email}")
            self.acc_log(f"Clave: {pwd}")
            
            # Bloquear orientación vertical
            self.acc_log("Forzando orientación vertical...")
            self.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
            self.adb.run_command(["shell", "settings", "put", "system", "user_rotation", "0"], serial)
            time.sleep(1.0)
            
            # 1. Abrir Spotify
            self.acc_log("Abriendo app de Spotify...")
            self.adb.run_command(["shell", "am", "start", "-n", "com.spotify.music/com.spotify.music.MainActivity"], serial)
            self.acc_log("Esperando 6s a que cargue la app...")
            time.sleep(6.0)
            
            # 2. Pulsar botón "Iniciar sesión"
            self.acc_log("Buscando botón 'Iniciar sesión'...")
            click_ok = self.find_and_click_by_text(serial, ["Iniciar sesión", "Log in", "Inicia sesión"])
            if not click_ok:
                self.acc_log("Pulsando coordenadas de 'Iniciar sesión'...", "warn")
                # Coordenadas comunes abajo (para 1080p, 720p se auto-escala bien)
                self.adb.run_command(["shell", "input", "tap", "540", "1820"], serial)
            time.sleep(4.0)
            
            # 3. Escribir Correo (se enfoca por defecto)
            self.acc_log("Ingresando correo...")
            self.adb.run_command(["shell", "input", "tap", "540", "500"], serial) # Clic respaldo para enfocar campo usuario
            time.sleep(0.5)
            self.adb.run_command(["shell", "input", "text", email], serial)
            time.sleep(1.0)
            
            # 4. Ir a Contraseña
            self.acc_log("Ingresando contraseña...")
            self.adb.run_command(["shell", "input", "keyevent", "61"], serial) # Tab
            time.sleep(0.5)
            self.adb.run_command(["shell", "input", "text", pwd], serial)
            time.sleep(1.0)
            
            # 5. Pulsar Enviar / Login
            self.acc_log("Enviando credenciales de acceso...")
            self.adb.run_command(["shell", "input", "keyevent", "61"], serial) # Tab (enfoca el botón de login)
            time.sleep(0.5)
            self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # Enter
            time.sleep(1.0)
            
            self.acc_log("✅ Comandos enviados. Si la cuenta es correcta, la pantalla se volverá visible en breve.", "success")
            
        except Exception as e:
            self.acc_log(f"Falla en login: {str(e)}", "error")
            
        self.after(0, lambda: self.btn_login_acc.configure(state="normal", text="🚀 2. Iniciar Sesión App (Auto A Ciegas)"))

if __name__ == "__main__":
    try:
        debug_log("Entrando a Main Loop")
        app = ProxyFarmApp()
        app.mainloop()
    except Exception as e:
        err = f"ERROR CRITICO EN ARRANQUE: {str(e)}"
        print(err)
        debug_log(err)
        speak("Se ha detectado un error critico. Revisa el archivo de registro.")
        with open("CRASH_REPORT.txt", "w") as f:
            traceback.print_exc(file=f)
