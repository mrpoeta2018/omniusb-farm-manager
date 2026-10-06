    def build_accounts_tab(self):
        self.tab_accounts.grid_columnconfigure(0, weight=1)
        self.tab_accounts.grid_columnconfigure(1, weight=1)
        self.tab_accounts.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Controles
        left_frame = ctk.CTkScrollableFrame(self.tab_accounts, fg_color="#1E293B", corner_radius=8)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(left_frame, text="👤 Creador de Cuentas Automático", font=("Arial", 16, "bold"), text_color="#F59E0B").pack(pady=10)

        # Selector Múltiple de Celulares
        ctk.CTkLabel(left_frame, text="📱 Seleccionar Celular(es):", font=("Arial", 12)).pack(pady=(10, 2))
        
        self.acc_devices_frame = ctk.CTkScrollableFrame(left_frame, width=250, height=120)
        self.acc_devices_frame.pack(pady=5, fill="x", padx=30)
        self.acc_device_vars = {} # serial -> ctk.BooleanVar
        
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=2)
        
        def _sel_all():
            for var in self.acc_device_vars.values(): var.set(True)
        def _sel_none():
            for var in self.acc_device_vars.values(): var.set(False)
            
        ctk.CTkButton(btn_frame, text="Todos", width=120, command=_sel_all).pack(side="left")
        ctk.CTkButton(btn_frame, text="Ninguno", width=120, command=_sel_none).pack(side="right")

        def _open_scrcpy_accounts():
            selected = [s for s, v in self.acc_device_vars.items() if v.get()]
            if not selected:
                messagebox.showwarning("Aviso", "Selecciona al menos un celular.")
                return
            for serial in selected:
                self.launch_scrcpy(serial)

        ctk.CTkButton(left_frame, text="👀 Ver Pantallas (Scrcpy)", width=250, fg_color="#10B981", text_color="white", command=_open_scrcpy_accounts).pack(pady=5)


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

        # Artistas a seguir
        ctk.CTkLabel(left_frame, text="🎸 Artistas a seguir (separados por coma):", font=("Arial", 11)).pack(pady=(10, 2))
        self.acc_artists_entry = ctk.CTkTextbox(left_frame, width=250, height=60)
        self.acc_artists_entry.pack(pady=2)
        self.acc_artists_entry.insert("1.0", "Bad Bunny, Feid, Karol G, Drake")

        # Botones de Acción
        ctk.CTkLabel(left_frame, text="⚡ Controles de Automatización", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        self.btn_scan_acc = ctk.CTkButton(left_frame, text="🔍 0. Escanear Sesiones (Pre-Check)", fg_color="#3B82F6", hover_color="#2563EB", command=self.start_spotify_scan_sessions, height=35)
        self.btn_scan_acc.pack(pady=5, fill="x", padx=30)
        
        self.btn_start_acc = ctk.CTkButton(left_frame, text="🌐 1. Abrir Registro Chrome (Visible)", fg_color="#10B981", hover_color="#059669", command=self.start_spotify_account_creation, height=35)
        # self.btn_start_acc.pack(pady=5, fill="x", padx=30)
        
        self.btn_login_acc = ctk.CTkButton(left_frame, text="🚀 2. Iniciar Sesión App (Auto A Ciegas)", fg_color="#F59E0B", hover_color="#D97706", command=self.start_spotify_login, height=35)
        # self.btn_login_acc.pack(pady=5, fill="x", padx=30)
        
        self.acc_slow_mode_var = ctk.BooleanVar(value=False)
        self.chk_slow_mode = ctk.CTkCheckBox(left_frame, text="🐢 Modo Lento (Para celulares lentos)", variable=self.acc_slow_mode_var)
        self.chk_slow_mode.pack(pady=5, padx=30, anchor="w")
        
        self.btn_google_login = ctk.CTkButton(left_frame, text="🤖 3. Login Automático (Vía Google)", fg_color="#10B981", hover_color="#059669", command=self.start_spotify_google_login, height=35)
        self.btn_google_login.pack(pady=5, fill="x", padx=30)
        
        self.btn_signup_acc = ctk.CTkButton(left_frame, text="✨ 4. Crear Cuenta en App (A Ciegas)", fg_color="#D946EF", hover_color="#C026D3", command=self.start_spotify_app_signup, height=35)
        self.btn_signup_acc.pack(pady=5, fill="x", padx=30)
        self.btn_follow_artists = ctk.CTkButton(left_frame, text="🎨 5. Seguir Artistas (Opcional)", fg_color="#EC4899", hover_color="#DB2777", command=self.start_spotify_follow_artists, height=35)
        self.btn_follow_artists.pack(pady=5, fill="x", padx=30)
        
        self.btn_logout_acc = ctk.CTkButton(left_frame, text="🚪 6. Cerrar Sesión (A Ciegas)", fg_color="#8B5CF6", hover_color="#7C3AED", command=self.start_spotify_logout, height=35)
        self.btn_logout_acc.pack(pady=5, fill="x", padx=30)
        
        self.btn_stop_signup = ctk.CTkButton(left_frame, text="🛑 Detener Proceso", fg_color="#EF4444", hover_color="#DC2626", command=self.stop_spotify_signup, height=35, state="disabled")
        self.btn_stop_signup.pack(pady=5, fill="x", padx=30)
        self.stop_signup = False

        
        # Redundancias por si falla uiautomator
        manual_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        manual_frame.pack(pady=10)
        ctk.CTkButton(manual_frame, text="📧 Escribir Correo", width=120, fg_color="#F59E0B", command=self.manual_type_email).pack(side="left", padx=5)
        ctk.CTkButton(manual_frame, text="🔑 Escribir Clave", width=120, fg_color="#F59E0B", command=self.manual_type_password).pack(side="left", padx=5)

        # Panel Derecho: Logs
        right_frame = ctk.CTkFrame(self.tab_accounts, fg_color="#0F172A", corner_radius=8)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Registro del Proceso en Vivo", font=("Arial", 14, "bold"), text_color="#FCD34D").pack(pady=10)
        self.acc_log_box = ctk.CTkTextbox(right_frame, height=500)
        self.acc_log_box.pack(padx=10, fill="both", expand=True, pady=5)
        
        self.update_account_creator_devices()

    def update_account_creator_devices(self):
        if not hasattr(self, 'acc_devices_frame'): return
        devices = getattr(self, 'scanned_devices', [])
        serials = [dev['serial'] for dev in devices]
        
        # Guardar selecciones actuales
        old_selections = {s: v.get() for s, v in self.acc_device_vars.items()}
        
        # Limpiar
        for widget in self.acc_devices_frame.winfo_children():
            widget.destroy()
        self.acc_device_vars.clear()
        if not hasattr(self, 'acc_device_checkboxes'): self.acc_device_checkboxes = {}
        self.acc_device_checkboxes.clear()
        
        if not serials:
            ctk.CTkLabel(self.acc_devices_frame, text="No hay celulares detectados").pack(pady=5)
            return
            
        for serial in serials:
            was_selected = old_selections.get(serial, True)
            var = ctk.BooleanVar(value=was_selected)
            self.acc_device_vars[serial] = var
            cb = ctk.CTkCheckBox(self.acc_devices_frame, text=serial, variable=var)
            self.acc_device_checkboxes[serial] = cb
            cb.pack(pady=2, anchor="w", padx=10)

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

    def find_and_click_by_text(self, serial, target_texts, do_swipe=False):
        import xml.etree.ElementTree as ET
        import re
        import os
        import time

        for attempt in range(2 if do_swipe else 1):
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dump_{serial}.xml")
            
            self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path], serial)
            if not os.path.exists(local_path):
                continue
            
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
            
            if do_swipe and attempt == 0:
                self.acc_log(f" [{serial}] No se encontró texto. Deslizando hacia abajo...", "info")
                self.adb.run_command(["shell", "input", "swipe", "500", "1500", "500", "500"], serial)
                time.sleep(2)
                
        return False

    def start_spotify_account_creation(self):
        selected = [s for s, v in self.acc_device_vars.items() if v.get()]
        if not selected:
            self.acc_log("Selecciona al menos un celular", "warn")
            import tkinter.messagebox as mb
            mb.showwarning("Atencin", "Debes seleccionar al menos un celular.")
            return
            
        self.btn_start_acc.configure(state="disabled", text=" Registrando...")
        for serial in selected:
            import threading
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


    def _save_account_memory(self, serial, email, source="Blind"):
        import datetime
        import os
        try:
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cuentas_Creadas.txt")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(filename, "a", encoding="utf-8") as file:
                file.write(f"[{now}] Dispositivo: {serial} | Correo: {email} | Tipo: {source}\n")
        except Exception as e:
            self.log_msg(f"Error guardando memoria: {e}", "error")


    def start_spotify_scan_sessions(self):
        selected = [s for s, v in self.acc_device_vars.items() if v.get()]
        if not selected:
            self.acc_log("Selecciona al menos un celular", "warn")
            return
            
        self.btn_scan_acc.configure(state="disabled", text="⏳ Escaneando...")
        import threading
        threading.Thread(target=self._master_scan_sessions_thread, args=(selected,), daemon=True).start()

    def _force_portrait(self, serial):
        self.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
        self.adb.run_command(["shell", "settings", "put", "system", "user_rotation", "0"], serial)
        # TRUCO SECRETO ANDROID: Forzar refresco de configuración para que gire al instante
        self.adb.run_command(["shell", "am", "broadcast", "-a", "android.intent.action.CONFIGURATION_CHANGED"], serial)

    def _master_scan_sessions_thread(self, selected):
        import time
        import re
        self.acc_log(f"=== INICIANDO ESCANEO DE SESIONES ({len(selected)} Dispositivos) ===")
        
        # Blanquear
        for s in selected:
            if hasattr(self, 'acc_device_checkboxes') and s in self.acc_device_checkboxes:
                self.after(0, lambda dev=s: self.acc_device_checkboxes[dev].configure(text_color="white"))
                
        for idx, serial in enumerate(selected):
            self.acc_log(f"--- [Escaner {idx+1}/{len(selected)}] {serial} ---", "info")
            self._force_portrait(serial)
            self.adb.run_command(["shell", "am", "start", "-n", "com.spotify.music/com.spotify.music.MainActivity"], serial)
            time.sleep(5)
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            out, _, _ = self.adb.run_command(["shell", "cat", "/sdcard/window_dump.xml"], serial)
            
            out = out.lower() if isinstance(out, str) else ""
            if "inicio, pesta" in out or "buscar, pesta" in out or "tu biblioteca" in out or "permitir actividad en segundo plano" in out or "ahora no" in out or "home" in out:
                self.acc_log(f" [{serial}] ✅ CON SESIÓN ACTIVA. (Desmarcando)", "success")
                if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                    self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                if hasattr(self, 'acc_device_vars') and serial in self.acc_device_vars:
                    self.after(0, lambda s=serial: self.acc_device_vars[s].set(False))
                
                # Cerrar popup si existe
                if "ahora no" in out:
                    match = re.search(r'text="ahora no".*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', out)
                    if match:
                        ax1, ay1, ax2, ay2 = map(int, match.groups())
                        self.adb.run_command(["shell", "input", "tap", str((ax1 + ax2) // 2), str((ay1 + ay2) // 2)], serial)
            else:
                self.acc_log(f" [{serial}] ❌ SIN SESIÓN. (Marcando para crear)", "warn")
                if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                    self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ❌", text_color="#EF4444"))
                if hasattr(self, 'acc_device_vars') and serial in self.acc_device_vars:
                    self.after(0, lambda s=serial: self.acc_device_vars[s].set(True))
                    
        self.after(0, lambda: self.btn_scan_acc.configure(state="normal", text="🔍 0. Escanear Sesiones (Pre-Check)"))
        self.acc_log("=== ESCANEO FINALIZADO ===", "success")

    def start_spotify_google_login(self):
        selected = [s for s, v in self.acc_device_vars.items() if v.get()]
        if not selected:
            self.acc_log("Selecciona al menos un celular", "warn")
            return
            
        import tkinter.messagebox as mb
        if not mb.askyesno("Confirmación", "¿Ya pasaste el 'Escáner de Sesiones'?\n\nEs muy recomendable escanear antes para que se desmarquen automáticamente los que ya tienen cuenta.\n\n¿Deseas continuar con los dispositivos seleccionados?"):
            return

        self.btn_google_login.configure(state="disabled", text="⏳ Iniciando Login Google...")
        if hasattr(self, 'btn_stop_signup'):
            self.btn_stop_signup.configure(state="normal")
        self.stop_signup = False
        
        import threading
        threading.Thread(target=self._master_google_login_thread, args=(selected,), daemon=True).start()
        
    def _master_google_login_thread(self, selected):
        import time
        self.acc_log(f"=== INICIANDO LOGIN GOOGLE SECUENCIAL ({len(selected)} Dispositivos) ===")
        
        for s in selected:
            if hasattr(self, 'acc_device_checkboxes') and s in self.acc_device_checkboxes:
                self.after(0, lambda dev=s: self.acc_device_checkboxes[dev].configure(text_color="white"))
                
        for idx, serial in enumerate(selected):
            if getattr(self, 'stop_signup', False):
                self.acc_log("⛔ Proceso cancelado por el usuario.", "error")
                break
                
            self.acc_log(f"--- [Dispositivo {idx+1}/{len(selected)}] {serial} ---", "info")
            
            try:
                self._spotify_google_login_thread(serial)
            except Exception as e:
                self.acc_log(f"Error en {serial}: {e}", "error")
            
            time.sleep(3)
            
        self.after(0, lambda: self.btn_google_login.configure(state="normal", text="🤖 3. Login Automático (Vía Google)"))
        self.acc_log("=== LOGIN GOOGLE FINALIZADO ===", "success")

    def start_kick_google_login(self):
        if not hasattr(self, 'engine') or not self.engine.active_devices:
            self.acc_log(" [Error] No hay dispositivos activos.", "error")
            return
            
        selected = [dev for dev in self.engine.active_devices if dev['serial'] in self.acc_device_checkboxes and self.acc_device_checkboxes[dev['serial']].get()]
        if not selected:
            # If no accounts are selected, just do all active devices
            selected = self.engine.active_devices
            
        self.acc_log(f" [Kick] Iniciando Verificación/Login en {len(selected)} dispositivos...", "info")
        import threading
        threading.Thread(target=self._master_kick_google_login_thread, args=(selected,), daemon=True).start()

    def _master_kick_google_login_thread(self, selected):
        import time
        import xml.etree.ElementTree as ET
        for i, dev in enumerate(selected):
            s = dev['serial']
            self.acc_log(f" [{s[-4:]}] Verificando sesión actual de Kick...", "info")
            self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], s)
            time.sleep(1)
            self.adb.run_command(["shell", "am", "start", "-n", "com.kick.mobile/com.kick.mobile.MainActivity"], s)
            time.sleep(10)
            
            needs_login = False
            for attempt in range(3):
                root = getattr(self, 'pull_and_parse', lambda x: None)(s)
                if root is None:
                    needs_login = True
                    break
                    
                texts = [n.get("text", "").lower() for n in root.iter("node")]
                
                # Si vemos los botones de login directo, cortamos y logueamos.
                if any("log in" in t or "iniciar" in t or "inicia" in t or "sign up" in t for t in texts):
                    needs_login = True
                    break
                    
                # Si vemos el men principal de alguien logueado ("creadores destacados", "siguiendo")
                # Y NO estamos viendo la palabra "cargando..." o "conectndose al chat..." (tpico de un stream)
                if any("creadores destacados" in t or "siguiendo" in t for t in texts) and not any("conectndose al chat" in t or "cargando" in t for t in texts):
                    needs_login = False
                    break
                    
                # Si llegamos aqu, o es un stream reanudado o un pop-up raro.
                # Le damos Atrs (una sola vez) para intentar minimizar el stream y volver al men.
                self.acc_log(f" [{s[-4:]}] Posible stream reanudado. Forzando regreso al men...", "info")
                self.adb.run_command(["shell", "input", "keyevent", "4"], s)
                time.sleep(3)
                
            # Si despus de los intentos no determinamos nada claro, forzamos login por si acaso.
            # En la prctica, el break maneja los casos claros.
                
            if needs_login:
                self.acc_log(f" [{s[-4:]}] Kick cerrado. Iniciando Auto-Login...", "warn")
                success = self._kick_google_login_thread(s)
                if not success:
                    self.acc_log(f" [{s[-4:]}] Falló login de Kick.", "error")
            else:
                self.acc_log(f" [{s[-4:]}] ✅ Sesión confirmada en Kick. Omitiendo...", "success")
                if hasattr(self, 'acc_device_checkboxes') and s in self.acc_device_checkboxes:
                    self.after(0, lambda s=s: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
            time.sleep(2)
        self.acc_log(" [Kick] Proceso de Verificación/Login Terminado.", "success")

    def _kick_google_login_thread(self, serial):
        import time
        import json
        import os
        
        # Cargar memoria de correos
        mem_file = "kick_email_memory.json"
        email_memory = {}
        if os.path.exists(mem_file):
            try:
                with open(mem_file, "r") as mf:
                    email_memory = json.load(mf)
            except: pass
            
        is_slow = getattr(self, "acc_slow_mode_var", type('obj',(object,),{'get':lambda:False})()).get()
        def s_sleep(base_time):
            total = base_time * 2.5 if is_slow else base_time
            time.sleep(total)

        try:
            self.acc_log(f" [{serial[-4:]}] Iniciando Login con Google en KICK...", "info")
            
            self._force_portrait(serial)
            self.acc_log(f" [{serial[-4:]}] Limpiando Kick para Iniciar Sesin...", "warn")
            
            # Orden inteligente: Probar primero el índice que funcionó la vez pasada, luego los demás
            last_working_index = email_memory.get(serial, 0)
            indices_to_try = [last_working_index] + [i for i in range(5) if i != last_working_index]
            
            for email_index in indices_to_try:
                if getattr(self, 'stop_signup', False): break
                
                self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], serial)
                self.adb.run_command(["shell", "pm", "clear", "com.kick.mobile"], serial)
                s_sleep(2)
                self.adb.run_command(["shell", "am", "start", "-n", "com.kick.mobile/com.kick.mobile.MainActivity"], serial)
                
                self.acc_log(f" [{serial[-4:]}] Esperando 20 segundos a que Kick cargue...", "info")
                s_sleep(20) # 20 SEGUNDOS COMO PIDIO EL USUARIO
                
                # Iniciar Sesion (Barra superior)
                click_login = self.find_and_click_by_text(serial, ["iniciar sesi", "log in"], do_swipe=False)
                if not click_login:
                    self.acc_log(f" [{serial[-4:]}] ❌ No se encontro boton 'Iniciar sesion'. Reintentando...", "error")
                    continue # No hacemos toque ciego para evitar ir a la Play Store
                    
                s_sleep(8)
                
                # --- NUEVO: Ocultar teclado si aparece ---
                # Kick enfoca automticamente el campo de texto y saca el teclado, tapando el botn de Google.
                try:
                    stdout, _, _ = self.adb.run_command(["shell", "dumpsys", "input_method"], serial)
                    if "mInputShown=true" in stdout:
                        self.acc_log(f" [{serial[-4:]}] Teclado detectado tapando la pantalla. Ocultando...", "info")
                        self.adb.run_command(["shell", "input", "keyevent", "4"], serial)
                        time.sleep(2)
                except Exception as e:
                    self.acc_log(f" [{serial[-4:]}] Error checkeando teclado: {e}", "error")
                # ---------------------------------------
                
                # Continuar con Google
                click_google = self.find_and_click_by_text(serial, ["continuar con google", "continue with google", "google"], do_swipe=False)
                if not click_google:
                    self.acc_log(f" [{serial[-4:]}] ❌ No se encontro boton 'Google'. Reintentando...", "error")
                    continue
                    
                s_sleep(12)
                
                # Seleccionar cuenta Gmail por índice
                # Hacemos tap directo porque buscar texto siempre le da clic al primer correo de la lista.
                self.acc_log(f" [{serial[-4:]}] Seleccionando correo en el índice {email_index}...", "info")
                y_offset = 310 + (email_index * 80)
                self.adb.run_command(["shell", "input", "tap", "240", str(y_offset)], serial)
                
                self.acc_log(f" [{serial[-4:]}] Esperando 40s a que procese el inicio de sesión...", "info")
                s_sleep(40) # Aumentado a 40s porque Kick demora mucho en autenticar el correo
                
                # Omitir pantalla de Onboarding ("Cuéntanos un poco sobre ti" -> "Tal vez después")
                click_onboarding = self.find_and_click_by_text(serial, ["tal vez despu", "maybe later", "omitir", "skip"], do_swipe=False)
                if click_onboarding:
                    self.acc_log(f" [{serial[-4:]}] Pantalla de bienvenida saltada ('Tal vez después')...", "info")
                    s_sleep(5)
                
                # VERIFICACION FINAL (Segundo check)
                self.acc_log(f" [{serial[-4:]}] Realizando segundo check para confirmar inicio de sesion...", "info")
                root2 = getattr(self, 'pull_and_parse', lambda x: None)(serial)
                if root2 is not None:
                    texts2 = [n.get("text", "").lower() for n in root2.iter("node")]
                    if any("creadores destacados" in t or "tu cuenta" in t or "siguiendo" in t or "explorar" in t for t in texts2) and not any("log in" in t or "iniciar sesi" in t for t in texts2):
                        self.acc_log(f" [{serial[-4:]}] ✅ KICK CONFIRMADO LOGUEADO CON EXITO.", "success")
                        
                        # Guardar en memoria
                        email_memory[serial] = email_index
                        try:
                            with open(mem_file, "w") as mf:
                                json.dump(email_memory, mf)
                        except: pass
                        
                        if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                            self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                        return True
                    else:
                        self.acc_log(f" [{serial[-4:]}] ⚠️ Falló la verificación de sesión. Intentando otro correo...", "warn")
                        
            self.acc_log(f" [{serial[-4:]}] ❌ Fallo Login en Kick tras 5 intentos.", "error")
            return False
            
        except Exception as e:
            self.acc_log(f" [{serial[-4:]}] Error en Kick Login: {e}", "error")
            return False

    def _spotify_google_login_thread(self, serial):
        import time
        import re
        
        is_slow = getattr(self, "acc_slow_mode_var", type('obj',(object,),{'get':lambda:False})()).get()
        def s_sleep(base_time):
            total = base_time * 2.5 if is_slow else base_time
            slept = 0
            while slept < total:
                if getattr(self, 'stop_signup', False):
                    raise Exception('PROCESO DETENIDO_POR_EL_USUARIO')
                time.sleep(0.5)
                slept += 0.5

        try:
            self.acc_log(f" [{serial}] Iniciando proceso de Login con Google...", "info")
            
            # --- SMART PRE-CHECK (PROTECCION DE CUENTA) ---
            self.acc_log(f" [{serial}] Verificando si ya tiene cuenta activa...", "info")
            self._force_portrait(serial)
            self.adb.run_command(["shell", "am", "start", "-n", "com.spotify.music/com.spotify.music.MainActivity"], serial)
            s_sleep(4.0)
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            out_check, _, _ = self.adb.run_command(["shell", "cat", "/sdcard/window_dump.xml"], serial)
            out_check = out_check.lower() if isinstance(out_check, str) else ""
            if "inicio, pesta" in out_check or "buscar, pesta" in out_check or "tu biblioteca" in out_check or "permitir actividad en segundo plano" in out_check or "ahora no" in out_check:
                self.acc_log(f" [{serial}] 🛡️ ¡LA CUENTA YA ESTÁ LOGUEADA! Saltando para no borrarla.", "success")
                if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                    self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                return True
            self.acc_log(f" [{serial}] No hay cuenta activa. Procediendo a limpiar y loguear...", "info")
            # ----------------------------------------------
            
            # Vamos a iterar hasta 5 veces (por si hay 5 correos)
            for email_index in range(5):
                self.adb.run_command(["shell", "am", "force-stop", "com.spotify.music"], serial)
                s_sleep(1)
                self.adb.run_command(["shell", "pm", "clear", "com.spotify.music"], serial)
                s_sleep(1)
                self.adb.run_command(["shell", "am", "start", "-n", "com.spotify.music/com.spotify.music.MainActivity"], serial)
                s_sleep(6)
                
                # Clic "Iniciar sesion"
                click_login = self.find_and_click_by_text(serial, ["Iniciar sesión", "Log in", "Iniciar sesi"], do_swipe=True)
                if not click_login:
                    self.acc_log(f" [{serial}] No se vio 'Iniciar sesión', toque de respaldo...", "warn")
                    # Toque en la zona baja inferior (donde suele estar en pantallas grandes)
                    self.adb.run_command(["shell", "input", "tap", "540", "1800"], serial)
                s_sleep(3)
                
                # Clic "Google"
                click_google = self.find_and_click_by_text(serial, ["Google", "Continuar con Google"], do_swipe=True)
                if not click_google:
                    self.acc_log(f" [{serial}] No se vio 'Google', toque de respaldo...", "warn")
                    self.adb.run_command(["shell", "input", "tap", "540", "1200"], serial)
                
                s_sleep(8) # Dar tiempo a que google cargue
                
                # Volcar UI para encontrar los correos y tocar el indice actual
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
                xml_out, _, _ = self.adb.run_command(["shell", "cat", "/sdcard/window_dump.xml"], serial)
                
                # Encontrar todos los resource-id="com.google.android.gms:id/account_name"
                matches = re.findall(r'text="([^"]+)" resource-id="com\.google\.android\.gms:id/account_name".*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_out)
                
                if not matches:
                    self.acc_log(f" [{serial}] No se detectaron cuentas de Google en la pantalla. Operación abortada.", "error")
                    break
                    
                if email_index >= len(matches):
                    self.acc_log(f" [{serial}] Todos los {len(matches)} correos de Google fallaron.", "error")
                    if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                        self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ❌", text_color="#EF4444"))
                    break
                    
                target_email = matches[email_index][0]
                x1, y1, x2, y2 = map(int, matches[email_index][1:])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                self.acc_log(f" [{serial}] Probando correo #{email_index + 1}: {target_email}", "info")
                self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                
                # Esperar 12 segundos a ver si entra a Spotify
                s_sleep(12)
                
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
                check_out, _, _ = self.adb.run_command(["shell", "cat", "/sdcard/window_dump.xml"], serial)
                
                if "Inicio, Pesta" in check_out or "Buscar, Pesta" in check_out or "Tu biblioteca, Pesta" in check_out or "Permitir actividad en segundo plano" in check_out or "Ahora no" in check_out:
                    self.acc_log(f" [{serial}] LOGIN CON GOOGLE EXITOSO! ({target_email})", "success")
                    # Quitar el giro y forzar vertical al final
                    self.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
                    self.adb.run_command(["shell", "settings", "put", "system", "user_rotation", "0"], serial)
                    if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                        self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                    self._save_account_memory(serial, target_email, "Google Auto")
                    
                    if "Ahora no" in check_out:
                        match = re.search(r'text="Ahora no".*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', check_out)
                        if match:
                            ax1, ay1, ax2, ay2 = map(int, match.groups())
                            acx = (ax1 + ax2) // 2
                            acy = (ay1 + ay2) // 2
                            self.adb.run_command(["shell", "input", "tap", str(acx), str(acy)], serial)
                            s_sleep(2)

                    # Lanzar cancion para empezar a farmear
                    if hasattr(self, 'playlist_textbox'):
                        playlists = [p.strip() for p in self.playlist_textbox.get("1.0", "end").strip().split(chr(10)) if p.strip()]
                        tracks = [t.strip() for t in getattr(self, 'tracks_textbox', type('obj', (object,), {'get': lambda *a: ''})()).get("1.0", "end").strip().split(chr(10)) if t.strip()]
                        target = playlists if playlists else tracks
                        if target:
                            import random
                            self._inject_playlist_to_single(serial, random.choice(target))
                    return
                else:
                    self.acc_log(f" [{serial}] El correo {target_email} falló o no está listo. Intentando el siguiente...", "warn")
                    
        except Exception as e:
            self.acc_log(f" [{serial}] Error en Login Google: {str(e)}", "error")

    def start_spotify_login(self):
        selected = [s for s, v in self.acc_device_vars.items() if v.get()]
        if not selected:
            self.acc_log("Selecciona al menos un celular", "warn")
            return
            
        self.btn_login_acc.configure(state="disabled", text="⏳ Iniciando sesión...")
        for s in selected:
            threading.Thread(target=self._spotify_login_thread, args=(s,), daemon=True).start()


    def start_spotify_logout(self):
        selected = [s for s, v in self.acc_device_vars.items() if v.get()]
        if not selected:
            self.acc_log("Selecciona al menos un celular", "warn")
            return
            
        self.btn_logout_acc.configure(state="disabled", text=" 🚪 Cerrando Sesión...")
        if hasattr(self, 'btn_stop_signup'):
            self.btn_stop_signup.configure(state="normal")
        self.stop_signup = False
        
        import threading
        threading.Thread(target=self._master_logout_thread, args=(selected,), daemon=True).start()

    def _master_logout_thread(self, selected):
        import time
        total_devices = len(selected)
        success_count = 0
        
        self.acc_log(f"=== INICIANDO CIERRE DE SESIÓN ({total_devices} Dispositivos) ===")
        
        # Reset colors
        for s in selected:
            if hasattr(self, 'acc_device_checkboxes') and s in self.acc_device_checkboxes:
                self.after(0, lambda dev=s: self.acc_device_checkboxes[dev].configure(text_color="white"))
                
        for idx, serial in enumerate(selected):
            if getattr(self, 'stop_signup', False):
                self.acc_log(" ⛔ Proceso cancelado por el usuario.", "error")
                break
                
            self.acc_log(f"--- [Dispositivo {idx+1}/{total_devices}] {serial} ---", "info")
            try:
                res = self._spotify_logout_thread(serial)
                if res:
                    success_count += 1
                    if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                        self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text_color="#10B981"))
                else:
                    if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                        self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text_color="#EF4444"))
            except Exception as e:
                self.acc_log(f"Error crítico en {serial}: {e}", "error")
                
            time.sleep(2)
            
        self.acc_log("=== REPORTE CIERRE SESIÓN ===")
        self.acc_log(f"Procesados: {total_devices}")
        self.acc_log(f"Exitosos: {success_count}", "success")
        
        self.after(0, lambda: self.btn_logout_acc.configure(state="normal", text=" 🚪 6. Cerrar Sesión (A Ciegas)"))
        if hasattr(self, 'btn_stop_signup'):
            self.after(0, lambda: self.btn_stop_signup.configure(state="disabled"))

    def pull_and_parse(self, serial):
        import xml.etree.ElementTree as ET
        self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump.xml"], serial)
        self.adb.run_command(["pull", "/sdcard/dump.xml", "dump.xml"], serial)
        try:
            with open("dump.xml", "r", encoding="utf-8", errors="ignore") as f:
                return ET.fromstring(f.read())
        except:
            return None

    def _spotify_logout_thread(self, serial):
        self.acc_log(f"Iniciando cierre de sesión en {serial}...")

        import time
        self.acc_log("Retrocediendo al Inicio (Back button)...")
        for i in range(10):
            root = self.pull_and_parse(serial)
            if root is not None:
                texts = [node.get('content-desc', '').lower() for node in root.iter('node')]
                if any('ir a perfil y configuraci' in t for t in texts):
                    break
            self.adb.run_command(["shell", "input", "keyevent", "4"], serial)
            time.sleep(1.5)

        self.acc_log("1. Abriendo Perfil...")
        for i in range(5):
            self.adb.run_command(["shell", "input", "tap", "40", "60"], serial)
            time.sleep(2)
            root = self.pull_and_parse(serial)
            if root is not None:
                texts = [node.get('text', '').lower() + node.get('content-desc', '').lower() for node in root.iter('node')]
                if any('configuraci' in t and 'privacidad' in t for t in texts):
                    break

        self.acc_log("2. Entrando a Configuracion...")
        self.find_and_click_by_text(serial, ["Configuración y privacidad", "Configuracion y privacidad", "Settings and privacy"])
        time.sleep(3)

        self.acc_log("3. Scrolleando al fondo...")
        for _ in range(7):
            self.adb.run_command(["shell", "input", "swipe", "240", "700", "240", "200", "1000"], serial)
            time.sleep(1)

        self.acc_log("4. Tap Cerrar Sesion...")
        if not self.find_and_click_by_text(serial, ["Cerrar sesi", "Log out"]):
            self.adb.run_command(["shell", "input", "tap", "240", "660"], serial)
        time.sleep(2)

        self.acc_log("5. Confirmando...")
        self.adb.run_command(["shell", "input", "tap", "350", "550"], serial)
        time.sleep(3)
        
        self.acc_log(f" ✅ Sesión cerrada en {serial}.", "success")
        return True

    def stop_spotify_signup(self):
        self.stop_signup = True
        self.acc_log("🛑 Detención solicitada. Terminando dispositivo actual...", "warn")

    def start_spotify_app_signup(self):
        selected = [s for s, v in self.acc_device_vars.items() if v.get()]
        if not selected:
            self.acc_log("Selecciona al menos un celular", "warn")
            return
            
        self.btn_signup_acc.configure(state="disabled", text="⏳ Procesando Cola...")
        if hasattr(self, 'btn_stop_signup'):
            self.btn_stop_signup.configure(state="normal")
        self.stop_signup = False
        
        prefix = self.acc_email_prefix_entry.get().strip()
        domain = self.acc_email_domain_entry.get().strip()
        pwd = self.acc_password_entry.get().strip()
        artists = self.acc_artists_entry.get("1.0", "end-1c").strip()
        
        is_slow = getattr(self, 'acc_slow_mode_var', None) and self.acc_slow_mode_var.get()
        import threading
        threading.Thread(target=self._master_signup_thread, args=(selected, prefix, domain, pwd, artists, is_slow), daemon=True).start()

    def _master_signup_thread(self, selected, prefix, domain, pwd, artists, is_slow=False):
        import time
        import random
        total_devices = len(selected)
        success_count = 0
        failed_count = 0
        
        self.acc_log(f"=== INICIANDO COLA SECUENCIAL ({total_devices} Dispositivos) ===")
        
        # Resetear colores de los checkboxes seleccionados a blanco antes de empezar
        for s in selected:
            if hasattr(self, 'acc_device_checkboxes') and s in self.acc_device_checkboxes:
                self.after(0, lambda dev=s: self.acc_device_checkboxes[dev].configure(text_color="white"))
        
        for idx, serial in enumerate(selected):
            if getattr(self, 'stop_signup', False):
                self.acc_log("⛔ Proceso cancelado por el usuario.", "error")
                break
                
            self.acc_log(f"--- [Dispositivo {idx+1}/{total_devices}] {serial} ---", "info")
            max_retries = 2
            success = False
            for attempt in range(1, max_retries + 1):
                if getattr(self, 'stop_signup', False):
                    break
                    
                self.acc_log(f"Intento {attempt}/{max_retries} para {serial}")
                rnd_num = random.randint(10000, 99999)
                email = f"{prefix}{rnd_num}@{domain}"
                
                self._cleanup_background_apps(serial)
                self.adb.run_command(["shell", "am", "force-stop", "com.spotify.music"], serial)
                time.sleep(2)
                
                try:
                    res = self._spotify_app_signup_thread(serial, email, pwd, artists, is_slow)
                    if res:
                        success = True
                        break
                    else:
                        self.acc_log(f"Fallo en intento {attempt} para {serial}", "warn")
                except Exception as e:
                    self.acc_log(f"Error en {serial}: {e}", "error")
                    
                time.sleep(3)
                
            if success:
                success_count += 1
                if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                    self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text_color="#10B981"))
            else:
                failed_count += 1
                self.acc_log(f"❌ {serial} saltado tras {max_retries} intentos.", "error")
                
            time.sleep(3)
            
        self.acc_log("=== REPORTE FINAL ===")
        self.acc_log(f"Procesados: {total_devices}")
        self.acc_log(f"Exitosos: {success_count}", "success")
        self.acc_log(f"Fallidos: {failed_count}", "error")
        
        self.after(0, lambda: self.btn_signup_acc.configure(state="normal", text="✨ 3. Crear Cuenta en App (A Ciegas)"))
        if hasattr(self, 'btn_stop_signup'):
            self.after(0, lambda: self.btn_stop_signup.configure(state="disabled"))

    def start_spotify_follow_artists(self):
        selected = [s for s, v in self.acc_device_vars.items() if v.get()]
        if not selected:
            self.acc_log("Selecciona al menos un celular", "warn")
            return
            
        artists = self.acc_artists_entry.get("1.0", "end-1c").strip()
        if not artists:
            self.acc_log("Por favor, ingresa al menos un artista en la caja de texto.", "warn")
            return
            
        self.btn_follow_artists.configure(state="disabled", text="⏳ Siguiendo Artistas...")
        if hasattr(self, 'btn_stop_signup'):
            self.btn_stop_signup.configure(state="normal")
        self.stop_signup = False
        
        import threading
        threading.Thread(target=self._master_artists_thread, args=(selected, artists), daemon=True).start()

    def _master_artists_thread(self, selected, artists):
        import time
        total_devices = len(selected)
        success_count = 0
        
        self.acc_log(f"=== INICIANDO SEGUIMIENTO DE ARTISTAS ({total_devices} Dispositivos) ===")
        
        for idx, serial in enumerate(selected):
            if getattr(self, 'stop_signup', False):
                self.acc_log("⛔ Proceso cancelado por el usuario.", "error")
                break
                
            self.acc_log(f"--- [Dispositivo {idx+1}/{total_devices}] {serial} ---", "info")
            try:
                res = self._spotify_follow_artists_thread(serial, artists)
                if res:
                    success_count += 1
            except Exception as e:
                self.acc_log(f"Error crítico en {serial}: {e}", "error")
                
            time.sleep(2)
            
        self.acc_log("=== REPORTE ARTISTAS ===")
        self.acc_log(f"Procesados: {total_devices}")
        self.acc_log(f"Exitosos: {success_count}", "success")
        
        self.after(0, lambda: self.btn_follow_artists.configure(state="normal", text="🎨 5. Seguir Artistas (Opcional)"))
        if hasattr(self, 'btn_stop_signup'):
            self.after(0, lambda: self.btn_stop_signup.configure(state="disabled"))

    def _spotify_follow_artists_thread(self, serial, artists):
        import time
        import os
        artist_list = [a.strip() for a in artists.split(",") if a.strip()]
        self.acc_log(f"Procediendo a seguir a {len(artist_list)} artistas...")
        for art in artist_list:
            if getattr(self, 'stop_signup', False): return False
            self.acc_log(f"Buscando a: {art}")
            
            search_clicked = self.find_and_click_by_text(serial, ["Busca artistas", "Search artists", "Buscar"])
            if not search_clicked:
                self.adb.run_command(["shell", "input", "tap", "360", "200"], serial)
            time.sleep(1)
            
            self.adb.run_command(["shell", "input", "text", f'"{art}"'], serial)
            s_sleep(2.5)
            
            self.adb.run_command(["shell", "input", "tap", "360", "350"], serial) # Tap 1st result
            time.sleep(1)
            
            self.adb.run_command(["shell", "input", "tap", "650", "200"], serial) # X to clear
            time.sleep(1)
            
        self.acc_log("Artistas seleccionados. Pulsando Listo/Siguiente...")
        self.find_and_click_by_text(serial, ["Listo", "Siguiente", "Next", "Done"])
        time.sleep(2)
        self.acc_log(f"✅ Artistas seguidos en {serial}.", "success")
        return True


    def _spotify_app_signup_thread(self, serial, email, pwd, artists="", is_slow=False):
        import time
        import os
        
        def s_sleep(base_time):
            import time
            total = base_time * 2.5 if is_slow else base_time
            slept = 0
            while slept < total:
                if getattr(self, 'stop_signup', False):
                    raise Exception('PROCESO DETENIDO_POR_EL_USUARIO')
                time.sleep(0.5)
                slept += 0.5
            
        try:
            self.acc_log(f"🚀 Iniciando Registro App en {serial} (A Ciegas)", "success")
            self.acc_log(f"Correo Nuevo: {email}")
            self.acc_log(f"Clave: {pwd}")
            
            
            self.acc_log("Abriendo app de Spotify...")
            self.adb.run_command(["shell", "am", "start", "-n", "com.spotify.music/com.spotify.music.MainActivity"], serial)
            self.acc_log(f"Esperando {15 if is_slow else 6}s a que cargue la app...")
            s_sleep(6.0)
            
            self.acc_log("Verificando si ya hay una sesión iniciada...")
            local_path_check = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dump_check_{serial}.xml")
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path_check], serial)
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(local_path_check)
                root = tree.getroot()
                if os.path.exists(local_path_check): os.remove(local_path_check)
                p_text = " ".join([n.get("text", "") for n in root.iter()]).lower()
                p_desc = " ".join([n.get("content-desc", "") for n in root.iter()]).lower()
                full_text = p_text + " " + p_desc
                if "inicio" in full_text or "tu biblioteca" in full_text or "home" in full_text or "your library" in full_text or "permitir actividad en segundo plano" in full_text or "ahora no" in full_text:
                    self.acc_log(f" [{serial}] YA ESTABA LOGUEADO. Saltando.", "success")
                    if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                        self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                    self._save_account_memory(serial, "Desconocido (Ya estaba logueado)", "A ciegas/Pre-check")
                    if "ahora no" in full_text:
                        match = re.search(r'text="ahora no".*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', full_text)
                        if match:
                            ax1, ay1, ax2, ay2 = map(int, match.groups())
                            self.adb.run_command(["shell", "input", "tap", str((ax1 + ax2) // 2), str((ay1 + ay2) // 2)], serial)
                    return True
            except:
                pass
            
            self.acc_log("Buscando botón 'Registrarte gratis'...")
            click_ok = self.find_and_click_by_text(serial, ["Registrarte gratis", "Regístrate gratis", "Registrate gratis", "Sign up free", "Registrarse", "Sign up"])
            if not click_ok:
                self.acc_log("Pulsando coordenadas de 'Registrarte gratis'...", "warn")
                self.adb.run_command(["shell", "input", "tap", "540", "1600"], serial)
            s_sleep(4.0)
            
            self.acc_log("Ingresando correo...")
            self.adb.run_command(["shell", "input", "tap", "540", "500"], serial)
            time.sleep(0.5)
            self.adb.run_command(["shell", "input", "text", email], serial)
            s_sleep(1.5)
            
            self.acc_log("Avanzando (Siguiente)...")
            self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # Enter
            s_sleep(1.0)
            # Búsqueda exacta del botón Siguiente
            click_ok = self.find_and_click_by_text(serial, ["Siguiente", "Next"])
            if not click_ok:
                self.acc_log("No se vio Siguiente, toque ciego de respaldo...")
                self.adb.run_command(["shell", "input", "tap", "540", "850"], serial)
            
            self.acc_log(f"Esperando {20 if is_slow else 8}s a que cargue la pantalla de contraseña...")
            s_sleep(8.0)
            
            self.acc_log("Ingresando contraseña...")
            self.adb.run_command(["shell", "input", "tap", "540", "500"], serial)
            time.sleep(0.5)
            self.adb.run_command(["shell", "input", "text", pwd], serial)
            s_sleep(1.0)
            
            self.acc_log("Avanzando (Siguiente)...")
            self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # Enter
            s_sleep(1.0)
            click_ok2 = self.find_and_click_by_text(serial, ["Siguiente", "Next"])
            if not click_ok2:
                self.adb.run_command(["shell", "input", "tap", "540", "850"], serial)
            s_sleep(4.0)
            
            # --- FASE AUTOMÁTICA EXTRA: FECHA, GÉNERO Y NOMBRE ---
            
            self.acc_log("Buscando rueda del Año (Dinámico)...")
            import xml.etree.ElementTree as ET
            import re
            import os
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dump_{serial}.xml")
            self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path], serial)
            try:
                tree = ET.parse(local_path)
                root = tree.getroot()
                if os.path.exists(local_path): os.remove(local_path)
                cx, cy = None, None
                for node in root.iter():
                    text = node.get("text", "")
                    if re.search(r"201[0-9]|202[0-9]", text):
                        bounds = node.get("bounds", "")
                        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                        if m:
                            x1, y1, x2, y2 = map(int, m.groups())
                            cx = int((x1 + x2) / 2)
                            cy = int((y1 + y2) / 2)
                            break
                if cx:
                    # Tocamos ligeramente por debajo del primer año encontrado para acertar en la zona verde central
                    self.adb.run_command(["shell", "input", "tap", str(cx), str(cy + 80)], serial)
                else:
                    self.adb.run_command(["shell", "input", "tap", "850", "850"], serial)
            except:
                self.adb.run_command(["shell", "input", "tap", "850", "850"], serial)
                
            s_sleep(1.0)
            
            import random
            random_year = random.randint(1966, 2008)
            self.acc_log(f"Escribiendo año final aleatorio ({random_year})...")
            self.adb.run_command(["shell", "input", "text", str(random_year)], serial)
            s_sleep(random.uniform(1.0, 2.5))
            
            self.acc_log("Pulsando chulito (Enter) para ocultar teclado...")
            self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # Enter / Done para ocultar teclado
            s_sleep(1.5)
            
            self.acc_log("Avanzando a Género...")
            click_ok3 = self.find_and_click_by_text(serial, ["Siguiente", "Next"])
            if not click_ok3:
                self.adb.run_command(["shell", "input", "tap", "540", "850"], serial)
            s_sleep(4.0)

            self.acc_log("Buscando opción de Género (Aleatorio)...")
            import random
            genders = [
                ["Masculino", "Hombre", "Male"],
                ["Femenino", "Mujer", "Female"],
                ["No binario", "Non-binary", "Non binary"],
                ["Otro", "Other"],
                ["Prefiero no decirlo", "Prefer not to say"]
            ]
            selected_gender = random.choice(genders)
            click_ok4 = self.find_and_click_by_text(serial, selected_gender)
            if not click_ok4:
                self.acc_log("Toque ciego para Género...", "warn")
                self.adb.run_command(["shell", "input", "tap", "540", "500"], serial)
            
            self.acc_log("Esperando que cargue la selección...")
            s_sleep(random.uniform(2.5, 3.5))
            
            # A veces hay que dar a Siguiente
            self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # Ocultar teclado/confirmar
            s_sleep(1.0)
            self.find_and_click_by_text(serial, ["Siguiente", "Next"])
            
            self.acc_log(f"Esperando {12 if is_slow else 5}s para la pantalla de Nombre...")
            s_sleep(5.0) # Tiempo de carga largo

            self.acc_log("Omitiendo tipeo de nombre (usando el pre-asignado por Spotify)...")
            s_sleep(1.0)
            
            self.acc_log("Escaneando Checkboxes y Botón en Pantalla...")
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dump_{serial}.xml")
            self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path], serial)
            import xml.etree.ElementTree as ET
            import re
            import os
            
            btn_crear_cx = None
            btn_crear_cy = None
            try:
                tree = ET.parse(local_path)
                root = tree.getroot()
                if os.path.exists(local_path): os.remove(local_path)
                checkboxes_marcados = 0
                
                for node in root.iter():
                    text = node.get("text", "")
                    content_desc = node.get("content-desc", "")
                    checkable = node.get("checkable", "false")
                    checked = node.get("checked", "false")
                    bounds = node.get("bounds", "")
                    
                    # 1. Analizar checkboxes
                    if checkable == "true" and checked == "false":
                        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                        if m:
                            x1, y1, x2, y2 = map(int, m.groups())
                            cx = int((x1 + x2) / 2)
                            cy = int((y1 + y2) / 2)
                            self.acc_log(f"Marcando checkbox en X={cx}, Y={cy}...")
                            self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                            s_sleep(1.0)
                            checkboxes_marcados += 1
                            
                    # 2. Analizar Botón de Crear Cuenta (evitando el título de arriba)
                    lower_text = text.lower() + " " + content_desc.lower()
                    if "crear cuenta" in lower_text or "create account" in lower_text:
                        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                        if m:
                            _, y1, _, y2 = map(int, m.groups())
                            cy = int((y1 + y2) / 2)
                            if cy > 300: # Ignorar el título que está arriba
                                btn_crear_cx = int((int(m.group(1)) + int(m.group(3))) / 2)
                                btn_crear_cy = cy

                if checkboxes_marcados > 0:
                    self.acc_log(f"Se marcaron {checkboxes_marcados} casillas dinámicamente.")
                else:
                    self.acc_log("No se detectaron casillas sin marcar.")
            except Exception as e:
                self.acc_log(f"Fallo al escanear XML: {e}", "warn")
            
            s_sleep(1.0)
            self.acc_log("Pulsando Crear cuenta...")
            if btn_crear_cx and btn_crear_cy:
                self.acc_log(f"Encontrado botón seguro en X={btn_crear_cx}, Y={btn_crear_cy}. Pulsando...")
                self.adb.run_command(["shell", "input", "tap", str(btn_crear_cx), str(btn_crear_cy)], serial)
            else:
                self.acc_log("No se ubicó botón seguro, usando Tap Ciego...")
                self.adb.run_command(["shell", "input", "tap", "540", "1100"], serial)
            
            s_sleep(6.0) # Esperar a ver si cambia a Captcha
            
            # Validación Final
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial)
            self.adb.run_command(["pull", "/sdcard/window_dump.xml", local_path], serial)
            try:
                tree = ET.parse(local_path)
                root = tree.getroot()
                if os.path.exists(local_path): os.remove(local_path)
                pantalla_texto = " ".join([n.get("text", "") for n in root.iter()]).lower()
                if "como te llamas" in pantalla_texto or "what's your name" in pantalla_texto or "crear cuenta" in pantalla_texto:
                    self.acc_log(" [ERROR] El bot sigue en la pantalla de Nombre. Algo impidio crear la cuenta.", "error")
                    if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                        self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ❌", text_color="#EF4444"))
                    return False
                elif "captcha" in pantalla_texto or "robot" in pantalla_texto or "proteger tu cuenta" in pantalla_texto:
                    self.acc_log(" Detectado Captcha. Deteniendo proceso para resolucion manual.", "warn")
                    return True
                else:
                    self.acc_log(" ✅ Formulario completado. Si sale Captcha, por favor resuélvelo manual.", "success")
                    self.acc_log(" 💡 NOTA: Usa el botón '4. Seguir Artistas' cuando la cuenta ya esté limpia.", "warn")
                    # Quitar el giro y forzar vertical al final
                    self.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
                    self.adb.run_command(["shell", "settings", "put", "system", "user_rotation", "0"], serial)
                    if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                        self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                    self._save_account_memory(serial, email, "Creada a Ciegas")
                    return True

            except:
                self.acc_log("✅ Proceso automático asume éxito (no se pudo verificar). Listo en Captcha.", "success")
                # Quitar el giro y forzar vertical al final
                self.adb.run_command(["shell", "settings", "put", "system", "accelerometer_rotation", "0"], serial)
                self.adb.run_command(["shell", "settings", "put", "system", "user_rotation", "0"], serial)
                if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                    self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ✅", text_color="#10B981"))
                self._save_account_memory(serial, email, "Creada a Ciegas (Verificación fallida)")
                return True

            
            
        except Exception as e:
            self.acc_log(f"Falla en el registro App: {str(e)}", "error")
            if hasattr(self, 'acc_device_checkboxes') and serial in self.acc_device_checkboxes:
                self.after(0, lambda s=serial: self.acc_device_checkboxes[s].configure(text=f"{s} ❌", text_color="#EF4444"))
            return False
