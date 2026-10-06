with open('core/injector.py', 'a', encoding='utf-8') as f:
    f.write('''
    # ─────────────────────────────────────────
    # INYECCIÓN TIDAL
    # ─────────────────────────────────────────

    def inject_tidal(self, serial, url, drip_delay=0):
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        safe_url = f"'{url.strip()}'"

        self.log(f"[{serial[-4:]}] 🌊 Iniciando Tidal → {url[:50]}...", "info")

        self.adb.run_command(["shell", "am", "force-stop", "com.aspiro.tidal"], serial)
        self._cleanup_apps(serial, keep_pkg="com.aspiro.tidal")
        time.sleep(2)

        if self._is_cancelled(serial, token): return

        # Abrir Tidal con la URL
        self.adb.run_command(
            ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "com.aspiro.tidal"],
            serial
        )

        for _ in range(6):
            time.sleep(1)
            if self._is_cancelled(serial, token): return

        self.log(f"[{serial[-4:]}] 🔍 Buscando botón de Reproducir en Tidal...", "info")
        for attempt in range(8):
            if self._is_cancelled(serial, token): return
            try:
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_tidal.xml"], serial)
                out_t = self.adb.run_command(["shell", "cat", "/sdcard/dump_tidal.xml"], serial)
                out = out_t[0] if isinstance(out_t, tuple) else out_t
                if out:
                    import re
                    import xml.etree.ElementTree as ET
                    out = re.sub(r"<\?xml.*?\?>", "", out)
                    root = ET.fromstring(out.encode("utf-8", "ignore"))
                    
                    btn_play = None
                    for node in root.iter("node"):
                        res_id = (node.get("resource-id") or "")
                        text_n = (node.get("text") or "").lower()
                        bounds = node.get("bounds", "")
                        
                        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                        if not m: continue
                        x1, y1, x2, y2 = map(int, m.groups())
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        
                        if cy > 750: continue # Ignorar mini reproductor
                        
                        if res_id == "com.aspiro.tidal:id/playButton" or res_id == "com.aspiro.tidal:id/shufflePlayButton" or "reproducir" == text_n or "aleatorio" == text_n:
                            btn_play = (cx, cy)
                            break
                            
                    if btn_play:
                        self.log(f"[{serial[-4:]}] ▶️ Botón Play encontrado — Presionando...", "info")
                        self.adb.run_command(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])], serial)
                        return
            except Exception:
                pass
            time.sleep(2)
            
        self.log(f"[{serial[-4:]}] ⚠️ No se encontró botón Play en Tidal", "warn")

    def inject_tidal_batch(self, devices, urls, drip_mode="rápido"):
        if not urls:
            self.log("⚠️ No hay URLs de Tidal", "warn")
            return
        self.log(f"🌊 Inyectando Tidal en {len(devices)} dispositivos... (Modo: {drip_mode})", "info")
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
            threading.Thread(target=self.inject_tidal, args=(serial, url, delay), daemon=True).start()
''')
