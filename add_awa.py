with open('core/injector.py', 'a', encoding='utf-8') as f:
    f.write('''
    # ─────────────────────────────────────────
    # INYECCIÓN AWA
    # ─────────────────────────────────────────

    def inject_awa(self, serial, url, drip_delay=0):
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        safe_url = f"'{url.strip()}'"

        self.log(f"[{serial[-4:]}] 🌸 Iniciando AWA → {url[:50]}...", "info")

        self.adb.run_command(["shell", "am", "force-stop", "fm.awa.liverpool"], serial)
        self.adb.run_command(["shell", "am", "force-stop", "com.android.chrome"], serial)
        self._cleanup_apps(serial, keep_pkg="fm.awa.liverpool")
        time.sleep(2)

        if self._is_cancelled(serial, token): return

        # Congelar animaciones para evitar bloqueo de UI Automator
        self.adb.run_command(["shell", "settings", "put", "global", "window_animation_scale", "0.0"], serial)
        self.adb.run_command(["shell", "settings", "put", "global", "transition_animation_scale", "0.0"], serial)
        self.adb.run_command(["shell", "settings", "put", "global", "animator_duration_scale", "0.0"], serial)

        # Iniciar URL
        self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url], serial)

        # Manejar diálogo "Abrir con" si aparece
        time.sleep(4)
        for _ in range(2):
            out_t = self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_awa.xml"], serial)
            out = self.adb.run_command(["shell", "cat", "/sdcard/dump_awa.xml"], serial)
            xml_text = out[0] if isinstance(out, tuple) else out
            
            if xml_text and ("Abrir con" in xml_text or "android:id/resolver_list" in xml_text):
                self.log(f"[{serial[-4:]}] 🛡️ Diálogo 'Abrir con' detectado. Seleccionando AWA...", "info")
                # Coordenadas por defecto para L1 PRO: AWA=240,714 Siempre=408,860
                self.adb.run_command(["shell", "input", "tap", "240", "714"], serial)
                time.sleep(1)
                self.adb.run_command(["shell", "input", "tap", "408", "860"], serial)
                time.sleep(3)
            else:
                break
                
        # Buscar botón Play
        for attempt in range(8):
            if self._is_cancelled(serial, token): break
            try:
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_awa.xml"], serial)
                out_t = self.adb.run_command(["shell", "cat", "/sdcard/dump_awa.xml"], serial)
                out = out_t[0] if isinstance(out_t, tuple) else out_t
                if out:
                    import re
                    import xml.etree.ElementTree as ET
                    out = re.sub(r"<\?xml.*?\?>", "", out)
                    root = ET.fromstring(out.encode("utf-8", "ignore"))
                    
                    btn_play = None
                    for node in root.iter("node"):
                        res_id = (node.get("resource-id") or "")
                        desc = (node.get("content-desc") or "").lower()
                        text_n = (node.get("text") or "").lower()
                        bounds = node.get("bounds", "")
                        
                        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                        if not m: continue
                        x1, y1, x2, y2 = map(int, m.groups())
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        
                        if cy > 750: continue # Ignorar mini reproductor
                        
                        if res_id == "fm.awa.liverpool:id/play":
                            btn_play = (cx, cy)
                            break
                            
                    if btn_play:
                        self.log(f"[{serial[-4:]}] ▶️ Botón Play encontrado en AWA — Presionando...", "info")
                        self.adb.run_command(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])], serial)
                        break
            except Exception:
                pass
            time.sleep(2)
            
        # Restaurar animaciones
        self.adb.run_command(["shell", "settings", "put", "global", "window_animation_scale", "1.0"], serial)
        self.adb.run_command(["shell", "settings", "put", "global", "transition_animation_scale", "1.0"], serial)
        self.adb.run_command(["shell", "settings", "put", "global", "animator_duration_scale", "1.0"], serial)

    def inject_awa_batch(self, devices, urls, drip_mode="rápido"):
        if not urls:
            self.log("⚠️ No hay URLs de AWA", "warn")
            return
        self.log(f"🌸 Inyectando AWA en {len(devices)} dispositivos... (Modo: {drip_mode})", "info")
        for i, dev in enumerate(devices):
            import random
            serial = dev["serial"]
            url = random.choice(urls)
            delay = 0
            if drip_mode == "rápido" and i > 0:
                delay = i * random.randint(3, 8)
            elif drip_mode == "lento" and i > 0:
                delay = i * random.randint(15, 30)
            elif i > 0:
                delay = i * 1.5
            import threading
            threading.Thread(target=self.inject_awa, args=(serial, url, delay), daemon=True).start()
''')
