with open('core/injector.py', 'a', encoding='utf-8') as f:
    f.write('''
    # ─────────────────────────────────────────
    # INYECCIÓN APPLE MUSIC
    # ─────────────────────────────────────────

    def inject_apple_music(self, serial, url, drip_delay=0):
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        safe_url = f"'{url.strip()}'"

        self.log(f"[{serial[-4:]}] 🍎 Iniciando Apple Music → {url[:50]}...", "info")

        self.adb.run_command(["shell", "am", "force-stop", "com.apple.android.music"], serial)
        self._cleanup_apps(serial, keep_pkg="com.apple.android.music")
        time.sleep(2)

        if self._is_cancelled(serial, token): return

        # Abrir Apple Music con la URL
        self.adb.run_command(
            ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "com.apple.android.music"],
            serial
        )

        for _ in range(5):
            time.sleep(1)
            if self._is_cancelled(serial, token): return

        self.log(f"[{serial[-4:]}] 🔍 Buscando botón de Reproducir en Apple Music...", "info")
        for attempt in range(8):
            if self._is_cancelled(serial, token): return
            try:
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_am.xml"], serial)
                out_t = self.adb.run_command(["shell", "cat", "/sdcard/dump_am.xml"], serial)
                out = out_t[0] if isinstance(out_t, tuple) else out_t
                if out:
                    import re
                    import xml.etree.ElementTree as ET
                    out = re.sub(r"<\?xml.*?\?>", "", out)
                    root = ET.fromstring(out.encode("utf-8", "ignore"))
                    
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
                        
                        if cy > 750: continue # Ignorar mini reproductor
                        
                        if "collection_list_item" in res_id or "list_item_track" in res_id:
                            if fallback_song is None:
                                fallback_song = (cx, cy)
                                
                        if "play_button" in res_id or "shuffle_button" in res_id or any(k in desc or k in text_n for k in ["reproducir", "play", "aleatorio", "shuffle"]):
                            btn_play = (cx, cy)
                            break
                            
                    if btn_play:
                        self.log(f"[{serial[-4:]}] ▶️ Botón Play encontrado — Presionando...", "info")
                        self.adb.run_command(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])], serial)
                        return
                    elif fallback_song:
                        self.log(f"[{serial[-4:]}] 🎯 Canción encontrada — Presionando...", "info")
                        self.adb.run_command(["shell", "input", "tap", str(fallback_song[0]), str(fallback_song[1])], serial)
                        return
            except Exception:
                pass
            time.sleep(2)
            
        self.log(f"[{serial[-4:]}] ⚠️ No se encontró botón Play en Apple Music", "warn")

    def inject_apple_music_batch(self, devices, urls, drip_mode="rápido"):
        if not urls:
            self.log("⚠️ No hay URLs de Apple Music", "warn")
            return
        self.log(f"🍎 Inyectando Apple Music en {len(devices)} dispositivos... (Modo: {drip_mode})", "info")
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
            threading.Thread(target=self.inject_apple_music, args=(serial, url, delay), daemon=True).start()
''')
