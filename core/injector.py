import re
import random
import os
"""
core/injector.py
================
Motor de Inyección de Media — LIMPIO 📱 AISLADO

Cada plataforma tiene su propio método independiente.
Imposible que Spotify termine en 📱ouTube.
Token de cancelación por dispositivo para matar hilos fantasma.
"""

import time
import threading
import random
import xml.etree.ElementTree as ET


class MediaInjector:
    """
    Inyecta contenido (Spotify, 📱ouTube, 📱T Music) en los dispositivos activos.
    Usa tokens de cancelación para que cada nueva inyección mate la anterior
    sin dejar hilos fantasma en memoria.
    """

    def __init__(self, adb_manager, log_fn):
        self.adb = adb_manager
        self.log = log_fn
        # Token por serial: si cambia, el hilo anterior se cancela solo
        self._tokens = {}
        self._lock = threading.Lock()

    # ─────────────────────────────────────────
    # TOKEN HELPERS
    # ─────────────────────────────────────────

    
    def _mute_device(self, serial):
        """Silencia el dispositivo cada 9 minutos para no estorbar la pantalla."""
        import time
        if not hasattr(self, '_last_mute'):
            self._last_mute = {}
        
        now = time.time()
        # 540 segundos = 9 minutos. Si pasaron menos de 9 mins, ignorar.
        if now - self._last_mute.get(serial, 0) < 540:
            return
            
        self._last_mute[serial] = now
        try:
            # Solo usamos el comando silencioso de Android. 
            # Eliminamos los keyevent 25 (botones físicos) para que la barra no tape la pantalla.
            self.adb.run_command(["shell", "media_session", "volume", "0"], serial)
        except:
            pass

    def _new_token(self, serial):
        with self._lock:
            t = str(time.time())
            self._tokens[serial] = t
            return t

    def _is_cancelled(self, serial, token):
        with self._lock:
            return self._tokens.get(serial) != token

    def cancel_all(self):
        """Cancela todas las inyecciones en curso (cambia todos los tokens)."""
        with self._lock:
            for s in list(self._tokens.keys()):
                self._tokens[s] = "CANCELLED"

    def cancel_device(self, serial):
        """Cancela inyección de un dispositivo específico."""
        with self._lock:
            self._tokens[serial] = "CANCELLED"

    # ─────────────────────────────────────────
    # UTILIDADES DE ADB
    # ─────────────────────────────────────────

    def _cleanup_apps(self, serial, keep_pkg=None):
        self.log(f"[{serial[-4:]}] 🧹 Cerrando de raíz procesos previos. Espere por favor...", "warn")
        pkgs = ["com.android.chrome", "com.spotify.music", "com.google.android.youtube", "com.google.android.apps.youtube.music", "com.kick.mobile", "tv.twitch.android.app", "fm.awa.liverpool", "com.apple.android.music", "com.aspiro.tidal"]
        for p in pkgs:
            if p != keep_pkg:
                self.adb.run_command(["shell", "am", "force-stop", p], serial)
        import time
        time.sleep(1) # Extra buffer time para que Android mate los procesos pesados
        self.log(f"[{serial[-4:]}] 🗑️ Limpieza profunda completada.", "success")

    # ==========================================
    # CLONADOR DE SPOTIF📱
    # ==========================================
    def clone_spotify_batch(self, devices, urls):
        """Dispara hilos para clonar una lista de Spotify en múltiples dispositivos."""
        self.log("🧬 Iniciando proceso masivo de Clonación de Listas en Spotify...", "warn")
        for i, dev in enumerate(devices):
            url = random.choice(urls)
            delay = i * random.randint(15, 30) # Siempre usar delay largo para clonar para no saturar
            t = threading.Thread(target=self._clone_and_play, args=(dev["serial"], url, delay), daemon=True)
            t.start()

    def _clone_and_play(self, serial, url, delay):
        token = self._new_token(serial)
        if delay > 0:
            time.sleep(delay)
        if self._is_cancelled(serial, token): return

        self.log(f"[{serial[-4:]}] 🧬 Iniciando CLONADOR en Spotify...", "info")
        
        self.adb.run_command(["shell", "am", "force-stop", "com.spotify.music"], serial)
        self._cleanup_apps(serial, keep_pkg="com.spotify.music")
        time.sleep(2)
        if self._is_cancelled(serial, token): return

        # 1. Abrir playlist original
        safe_url = f"'{url.strip()}'"
        self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "com.spotify.music"], serial)
        
        self.log(f"[{serial[-4:]}] ⏳ Esperando carga completa de la lista (15s)...", "warn")
        for _ in range(15):
            time.sleep(1)
            if self._is_cancelled(serial, token): return
            
        # 2. Tap 3 puntos menu
        self.log(f"[{serial[-4:]}] 📍 Tocando menú 3 puntos...", "info")
        self.adb.run_command(["shell", "input", "tap", "360", "898"], serial)
        time.sleep(4)
        if self._is_cancelled(serial, token): return
        
        # 3. Tap Agregar a otra playlist
        self.log(f"[{serial[-4:]}] 📍 Seleccionando 'Agregar a otra playlist'...", "info")
        self.adb.run_command(["shell", "input", "tap", "360", "1190"], serial)
        time.sleep(4)
        if self._is_cancelled(serial, token): return
        
        # 4. Tap Nueva playlist
        self.log(f"[{serial[-4:]}] 📍 Seleccionando 'Nueva playlist'...", "info")
        self.adb.run_command(["shell", "input", "tap", "600", "208"], serial)
        time.sleep(4)
        if self._is_cancelled(serial, token): return
        
        # 4.5 Escribir nombre aleatorio
        names = ["Mis Canciones", "Playlist Piola", "Top Music", "Favoritas 2026", "Mix Genial", "Temazos Hoy", "Musica Nueva"]
        name = random.choice(names).replace(" ", "%s")
        self.log(f"[{serial[-4:]}] ⌨️ Escribiendo nombre de lista...", "info")
        self.adb.run_command(["shell", "input", "text", name], serial)
        time.sleep(2)
        
        # Cerrar teclado garantizado (Back o Enter)
        self.adb.run_command(["shell", "input", "keyevent", "4"], serial)
        time.sleep(2)
        if self._is_cancelled(serial, token): return
        
        # 5. Tap Crear - Intento Principal
        self.log(f"[{serial[-4:]}] 📍 Tocando 'Crear'...", "info")
        self.adb.run_command(["shell", "input", "tap", "492", "921"], serial)
        time.sleep(5)
        
        # 5.5 VERIFICACION ROBUSTA (Leer Pantalla / UI Automator)
        if self._is_cancelled(serial, token): return
        try:
            dump_path = f"/sdcard/dump_clone_{serial}.xml"
            self.log(f"[{serial[-4:]}] 🔬 Radiografía de pantalla para verificar si se creó...", "warn")
            self.adb.run_command(["shell", "uiautomator", "dump", dump_path], serial)
            res = self.adb.run_command(["shell", "cat", dump_path], serial, capture_output=True)
            if res:
                xml_data = res.stdout.decode("utf-8", errors="ignore")
                if "Crear" in xml_data and "bounds=" in xml_data:
                    m = re.search(r'text="Crear".*⏳bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_data)
                    if m:
                        x1, y1, x2, y2 = map(int, m.groups())
                        cx, cy = (x1+x2)//2, (y1+y2)//2
                        self.log(f"[{serial[-4:]}] 🎯 Teclado estorbando. Disparando clic al botón invisible...", "warn")
                        self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                        time.sleep(5)
        except Exception as e:
            pass
            
        time.sleep(8) # Esperar que la cree y cargue la vista de la nueva playlist
        if self._is_cancelled(serial, token): return
        
        # 6. Tap Reproducir playlist (Botón verde grande)
        self.log(f"[{serial[-4:]}] ▶️ Dándole Play a la nueva playlist clonada...", "info")
        self.adb.run_command(["shell", "input", "tap", "632", "898"], serial)
        time.sleep(2)
        
        # 7. Tap en la primera cancion (para forzar que inicie ESA lista)
        self.adb.run_command(["shell", "input", "tap", "360", "1000"], serial)
        
        self.log(f"[{serial[-4:]}] ✅ CLONACIÓN 📱 REPRODUCCIÓN COMPLETADA.", "success")

    def _is_playing(self, serial):
        """Verifica si hay audio reproduciéndose (state=3)."""
        try:
            out, _, _ = self.adb.run_command(["shell", "dumpsys", "media_session"], serial)
            valid = [
                "com.spotify.music", "com.google.android.youtube",
                "com.google.android.apps.youtube.music",
            ]
            in_target = False
            for line in out.split("\n"):
                line = line.strip()
                if any(p in line for p in valid):
                    in_target = True
                elif "package=" in line:
                    in_target = False
                if in_target and "state=PlaybackState" in line:
                    return "state=3" in line
        except Exception:
            pass
        return False

    def _tap_green_play(self, serial):
        """Busca el botón Play/Shuffle en Spotify via UIAutomator XML usando ancla matemática (V6 Oro)."""
        import re
        import time
        self.log(f"[{serial[-4:]}] 🔍 Escaneando la estructura visual de Spotify...", "info")
        out_sz, _, _ = self.adb.run_command(["shell", "wm", "size"], serial)
        w, h = 720, 1280
        m_sz = re.search(r'(\d+)x(\d+)', str(out_sz))
        if m_sz:
            w, h = int(m_sz.group(1)), int(m_sz.group(2))

        for attempt in range(2):
            try:
                dump_name = f"/sdcard/dump_{serial[-4:]}.xml"
                self.adb.run_command(["shell", "uiautomator", "dump", dump_name], serial)
                out_t = self.adb.run_command(["shell", "cat", dump_name], serial)
                out = out_t[0] if isinstance(out_t, tuple) else out_t
                if not out:
                    time.sleep(2)
                    continue

                import xml.etree.ElementTree as ET
                out = re.sub(r"<\?xml.*?\?>", "", out)
                root = ET.fromstring(out.encode("utf-8", "ignore"))

                anchor_y = None
                btn_agregar_x = None

                for node in root.iter("node"):
                    desc = (node.get("content-desc") or "").lower()
                    text_n = (node.get("text") or "").lower()
                    cls = (node.get("class") or "").lower()
                    bounds = node.get("bounds", "")
                    
                    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if not m: continue
                    x1, y1, x2, y2 = map(int, m.groups())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    if any(k in desc or k in text_n for k in ["saltar", "skip", "omitir"]):
                        self.log(f"[{serial[-4:]}] 🚧 Anuncio detectado 🚧 Saltando...", "warn")
                        self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                        time.sleep(2)

                    if ('agrega' in desc or 'guard' in desc or 'add ' in desc) and 'veces' not in desc and 'min' not in desc:
                        if 'textview' not in cls:
                            anchor_y = cy
                            # Revisar si ya está guardado (si dice agregado, guardado, o quitar)
                            ya_guardado = any(w in desc for w in ['agregado', 'guardado', 'quit', 'elimin', 'remove', 'saved', 'added'])
                            if ya_guardado:
                                self.log(f"[{serial[-4:]}] 🤍 Ya estaba guardado en biblioteca (ignorar Like).", "info")
                                btn_agregar_x = None
                            else:
                                self.log(f"[{serial[-4:]}] 💚 No estaba guardado. Dando Like/Guardar.", "success")
                                btn_agregar_x = cx
                            break

                if anchor_y:
                    self.log(f"[{serial[-4:]}] ⚓ Ancla PERFECTA localizada en Y={anchor_y}.", "success")
                    if btn_agregar_x:
                        self.adb.run_command(["shell", "input", "tap", str(btn_agregar_x), str(anchor_y)], serial)
                        time.sleep(2)
                else:
                    self.log(f"[{serial[-4:]}] ⚠️ Ancla no encontrada. Asumiendo altura estándar.", "warn")
                    anchor_y = int(h * 0.6)

                calc_x = int(w * 0.88) if attempt == 0 else int(w * 0.75)
                
                self.log(f"[{serial[-4:]}] 🎯 Disparando dardo al Botón Verde en X:{calc_x}, Y:{anchor_y}...", "info")
                self.adb.run_command(["shell", "input", "tap", str(calc_x), str(anchor_y)], serial)
                return True

            except Exception as e:
                pass
            time.sleep(2)
        return False

    def _find_and_click_text(self, serial, texts):
        """Busca un texto en la UI y lo toca. Retorna True si lo encontró."""
        try:
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_omni.xml"], serial)
            out_t = self.adb.run_command(["shell", "cat", "/sdcard/dump_omni.xml"], serial)
            out = out_t[0] if isinstance(out_t, tuple) else out_t
            if not out:
                return False
            out = re.sub(r"<\⏳xml.*⏳\⏳>", "", out)
            root = ET.fromstring(out.encode("utf-8", "ignore"))
            for node in root.iter("node"):
                n_text = (node.get("text") or "").lower()
                n_desc = (node.get("content-desc") or "").lower()
                if any(t.lower() in n_text or t.lower() in n_desc for t in texts):
                    bounds = node.get("bounds", "")
                    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if m:
                        x1, y1, x2, y2 = map(int, m.groups())
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                        return True
        except Exception:
            pass
        return False

    # ─────────────────────────────────────────
    # IN📱ECCIÓN SPOTIF📱
    # ─────────────────────────────────────────

    def inject_spotify(self, serial, url, drip_delay=0):
        self._mute_device(serial)
        """
        Inyecta Spotify en UN dispositivo.
        drip_delay: segundos a esperar antes de empezar (para goteo humano).
        """
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        safe_url = f"'{url.strip()}'"

        self.log(f"[{serial[-4:]}] 🟢 Iniciando Spotify → {url[:50]}...", "info")

        # Limpiar apps rivales
        self.adb.run_command(["shell", "am", "force-stop", "com.spotify.music"], serial)
        self._cleanup_apps(serial, keep_pkg="com.spotify.music")
        time.sleep(2)

        if self._is_cancelled(serial, token):
            self.log(f"[{serial[-4:]}] ⛔ Inyección cancelada (nueva orden recibida)", "warn")
            return

        # Abrir Spotify con la URL
        self.adb.run_command(
            ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "com.spotify.music"],
            serial
        )

        # Segunda inyección a los 5s (para celulares lentos que olvidan la URL)
        for i in range(30):
            if self._is_cancelled(serial, token):
                self.log(f"[{serial[-4:]}] ⛔ Cancelado durante espera inicial", "warn")
                return
            if i == 5:
                self.adb.run_command(
                    ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "com.spotify.music"],
                    serial
                )
            time.sleep(1)

        if self._is_cancelled(serial, token):
            return

        # Intentar tocar el botón Play verde con VERIFICACIÓN
        self.log(f"[{serial[-4:]}] 🔍 Buscando botón Play para el nuevo link...", "info")
        pressed = False
        
        for attempt in range(2):
            clicked = self._tap_green_play(serial)
            if clicked:
                self.log(f"[{serial[-4:]}] 🧐 Verificando internamente si inició la música...", "info")
                time.sleep(4)
                
                if self._is_playing(serial):
                    self.log(f"[{serial[-4:]}] ✅ ¡Confirmado! El nuevo link se activó correctamente y está sonando.", "success")
                    pressed = True
                    break
                else:
                    self.log(f"[{serial[-4:]}] ⚠️ Falsa alarma o toque fallido. Reintentando con corrección...", "warn")
            else:
                time.sleep(3)

        if not pressed:
            self.log(f"[{serial[-4:]}] ⚠️ No se pudo confirmar Play en pantalla → Usando keyevent (126)", "warn")
            self.adb.run_command(["shell", "input", "keyevent", "126"], serial)

        # Esperar anuncios
        self.log(f"[{serial[-4:]}] ⏳ Esperando 60s (tiempo de anuncios)...", "info")
        for _ in range(60):
            if self._is_cancelled(serial, token):
                return
            time.sleep(1)

        # Verificación final
        if not self._is_cancelled(serial, token):
            if self._is_playing(serial):
                self.log(f"[{serial[-4:]}] ✅ SPOTIF📱 REPRODUCIENDO CORRECTAMENTE", "success")
            else:
                self.log(f"[{serial[-4:]}] ⚠️ No detecté audio — Adelantando canción (87)", "warn")
                self.adb.run_command(["shell", "input", "keyevent", "87"], serial)

    def inject_spotify_batch(self, devices, urls, drip_mode="rápido"):
        """
        Inyecta Spotify en todos los devices activos.
        drip_mode: "apagado", "rápido" (3-8s), "lento" (15-30s)
        """
        if not devices or not urls:
            self.log("⚠️ No hay dispositivos activos o lista de URLs vacía", "warn")
            return

        self.log(f"🟢 Inyectando Spotify en {len(devices)} dispositivo(s)... (Modo: {drip_mode})", "info")

        for i, dev in enumerate(devices):
            url = random.choice(urls)
            delay = 0
            if drip_mode == "rápido" and i > 0:
                delay = i * random.randint(3, 8)
            elif drip_mode == "lento" and i > 0:
                delay = i * random.randint(15, 30)
            elif i > 0:
                delay = i * 1.5  # Apagado (pequeño retraso USB)
                
            threading.Thread(
                target=self.inject_spotify,
                args=(dev["serial"], url, delay),
                daemon=True
            ).start()

    # ─────────────────────────────────────────
    # IN📱ECCIÓN 📱OUTUBE / 📱T MUSIC
    # ─────────────────────────────────────────

    def inject_youtube(self, serial, url, is_music=False, drip_delay=0):
        self._mute_device(serial)
        """
        Inyecta 📱ouTube o 📱T Music en UN dispositivo.
        is_music=True → abre 📱ouTube Music. False → 📱ouTube Video.
        """
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)

        # Limpiar parámetros de rastreo
        if "&si=" in url:
            url = url.split("&si=")[0]
        if "⏳si=" in url:
            url = url.split("⏳si=")[0]

        # Forzar shuffle en playlists de 📱ouTube (solo para 📱T normal, no Music)
        if "/playlist⏳list=" in url and not is_music:
            url = url.replace("/playlist⏳list=", "/watch⏳list=")
            if "&shuffle=" not in url:
                url += "&shuffle=1"
                
        # AUTO-CONVERSIÓN DE ENLACES: 
        # Si es modo Música, forzamos que el link sea music.youtube.com
        # Si es modo Normal, forzamos que sea youtube.com
        if is_music:
            url = url.replace("https://www.youtube.com", "https://music.youtube.com")
            url = url.replace("https://youtube.com", "https://music.youtube.com")
        else:
            url = url.replace("https://music.youtube.com", "https://youtube.com")

        target_pkg = "com.google.android.apps.youtube.music" if is_music else "com.google.android.youtube"
        platform_name = "📱T Music" if is_music else "📱ouTube"
        icon = "🟣" if is_music else "🔴"

        self.log(f"[{serial[-4:]}] {icon} Iniciando {platform_name} → {url[:50]}...", "info")

        # Limpiar apps
        self.adb.run_command(["shell", "am", "force-stop", target_pkg], serial)
        self._cleanup_apps(serial, keep_pkg=target_pkg)
        time.sleep(3)

        if self._is_cancelled(serial, token):
            self.log(f"[{serial[-4:]}] ⛔ Cancelado antes de abrir {platform_name}", "warn")
            return

        safe_url = f"'{url}'"
        self.adb.run_command(
            ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, target_pkg],
            serial
        )

        # Espera inicial
        for _ in range(25):
            if self._is_cancelled(serial, token):
                return
            time.sleep(1)

        if self._is_cancelled(serial, token):
            return

        # Buscar botón Shuffle/Aleatorio
        self.log(f"[{serial[-4:]}] 🔍 Buscando botón Aleatorio/Reproducir...", "info")
        if self._find_and_click_text(serial, ["Aleatorio", "Shuffle", "Reproducir aleatoriamente", "Reproducir", "Play", "Mezclar"]):
            self.log(f"[{serial[-4:]}] 🔀 ¡Botón de reproducción presionado!", "success")
        else:
            self.log(f"[{serial[-4:]}] ▶️ Asegurando reproducción (keyevent 126)...", "info")
            self.adb.run_command(["shell", "input", "keyevent", "126"], serial)

        # Esperar anuncios (Primer Ad)
        self.log(f"[{serial[-4:]}] ⏳ Esperando 12s (tiempo de 1er anuncio)...", "info")
        for _ in range(12):
            if self._is_cancelled(serial, token): return
            time.sleep(1)

        # Intentar saltar 1er anuncio
        if self._find_and_click_text(serial, ["Omitir", "Skip", "omitir", "skip", "Saltar", "saltar"]):
            self.log(f"[{serial[-4:]}] 📢 1er Anuncio omitido", "success")
            time.sleep(3)
            
        # Esperar y revisar un posible 2do anuncio (muy común en 📱T)
        self.log(f"[{serial[-4:]}] ⏳ Esperando 12s (tiempo de 2do anuncio)...", "info")
        for _ in range(12):
            if self._is_cancelled(serial, token): return
            time.sleep(1)
            
        if self._find_and_click_text(serial, ["Omitir", "Skip", "omitir", "skip", "Saltar", "saltar"]):
            self.log(f"[{serial[-4:]}] 📢 2do Anuncio omitido", "success")
            time.sleep(2)

        # Verificación final
        if not self._is_cancelled(serial, token):
            if self._is_playing(serial):
                self.log(f"[{serial[-4:]}] ✅ {platform_name.upper()} REPRODUCIENDO CORRECTAMENTE", "success")
            else:
                self.log(f"[{serial[-4:]}] ⚠️ No detecté audio — Forzando siguiente (87)", "warn")
                self.adb.run_command(["shell", "input", "keyevent", "87"], serial)

    def inject_youtube_batch(self, devices, urls, is_music=False, drip_mode="rápido"):
        """Inyecta 📱ouTube o 📱T Music en todos los dispositivos activos."""
        platform = "📱T Music" if is_music else "📱ouTube"
        icon = "🟣" if is_music else "🔴"

        if not devices or not urls:
            self.log(f"⚠️ No hay dispositivos activos o URLs de {platform}", "warn")
            return

        self.log(f"{icon} Inyectando {platform} en {len(devices)} dispositivo(s)... (Modo: {drip_mode})", "info")

        for i, dev in enumerate(devices):
            url = random.choice(urls)
            delay = 0
            if drip_mode == "rápido" and i > 0:
                delay = i * random.randint(3, 8)
            elif drip_mode == "lento" and i > 0:
                delay = i * random.randint(15, 30)
            elif i > 0:
                delay = i * 1.5  # Apagado (pequeño retraso USB)
                
            threading.Thread(
                target=self.inject_youtube,
                args=(dev["serial"], url),
                kwargs={"is_music": is_music, "drip_delay": delay},
                daemon=True
            ).start()

    # ─────────────────────────────────────────
    # IN📱ECCIÓN APPLE MUSIC
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
                    import xml.etree.ElementTree as ET
                    out = re.sub(r"<\⏳xml.*⏳\⏳>", "", out)
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
                        break
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

    # ─────────────────────────────────────────
    # IN📱ECCIÓN TIDAL
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
                    import xml.etree.ElementTree as ET
                    out = re.sub(r"<\⏳xml.*⏳\⏳>", "", out)
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
                        break
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

    # ─────────────────────────────────────────
    # IN📱ECCIÓN AWA
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
                
        # Buscar botón Play (Hasta 40 segundos)
        for attempt in range(20):
            if self._is_cancelled(serial, token): break
            try:
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_awa.xml"], serial)
                out_t = self.adb.run_command(["shell", "cat", "/sdcard/dump_awa.xml"], serial)
                out = out_t[0] if isinstance(out_t, tuple) else out_t
                if out:
                    import xml.etree.ElementTree as ET
                    out = re.sub(r"<\⏳xml.*⏳\⏳>", "", out)
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

    def inject_ytshorts(self, serial, url, t_min, t_max, do_like, do_save, do_comment, do_share, delay_start=0):
        try:
            t_min, t_max = int(t_min), int(t_max)
        except: pass
        token = self._new_token(serial)
        if delay_start > 0:
            time.sleep(delay_start)
        if self._is_cancelled(serial, token): return
        
        self.adb.run_command(["shell", "svc", "wifi", "enable"], serial) # 📡 PRENDER WIFI (Engaño Android)
        
        self.adb.run_command(["shell", "am", "force-stop", "com.google.android.youtube"], serial)
        self._cleanup_apps(serial, keep_pkg="com.google.android.youtube")
        time.sleep(4)
        clean_url = url.strip()
        import re
        if "/shorts/" in clean_url and "@" not in clean_url:
            match = re.search(r'/shorts/([a-zA-Z0-9_-]+)', clean_url)
            if match:
                vid = match.group(1)
                clean_url = f"https://www.youtube.com/watch?v={vid}"
        self.adb.run_command(["shell", "am", "start", "-S", "-a", "android.intent.action.VIEW", "-d", f"'{clean_url}'", "com.google.android.youtube"], serial)
        self.log(f"[{serial[-4:]}] \u25b6 Iniciando sesion de 📱T Shorts...", "info")
        time.sleep(10)
        if self._is_cancelled(serial, token): return
        
        # Click para asegurar foco en el primer short
        self.log(f"[{serial[-4:]}] 🔍 Escaneando pantalla inicial para abrir Short...", "info")
        self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_start.xml"], serial)
        out_start_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_start.xml"], serial)
        out_start = out_start_t[0] if isinstance(out_start_t, tuple) else out_start_t
        
        if out_start and "<node" in out_start:
            out_lower = out_start.lower()
            if "me gusta" in out_lower or "comentarios" in out_lower:
                self.log(f"[{serial[-4:]}] 🎬 Video detectado en pantalla completa. Autoplay activo.", "info")
            else:
                
                
                # Enfoque Geométrico: El usuario indica que la grilla tiene 3 columnas y empieza desde la mitad hacia abajo.
                # Queremos tocar la columna del MEDIO (X = 50%), de la fondo (Y = 82%).
                screen_match = re.search(r'bounds="\[0,0\]\[(\d+),(\d+)\]"', out_start)
                if screen_match:
                    w = int(screen_match.group(1))
                    h = int(screen_match.group(2))
                    cx = w // 2
                    cy = int(h * 0.82)
                    self.log(f"[{serial[-4:]}] 📏 Resolucion detectada: {w}x{h}. Tocando cuadro central en ({cx}, {cy}).", "info")
                else:
                    # Coordenadas por defecto si falla la lectura de resolucion
                    cx, cy = 360, 1000
                    self.log(f"[{serial[-4:]}] 📏 Resolucion no detectada. Usando toque central por defecto en ({cx}, {cy}).", "warn")
                
                self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                time.sleep(4)
        
        short_count = 1
        while not self._is_cancelled(serial, token):
            watch_time = random.randint(t_min, t_max)
            self.log(f"[{serial[-4:]}] \U0001f4fa Viendo Short #{short_count} por {watch_time}s...", "info")
            
            # Wait watch time (interruptible)
            for _ in range(watch_time):
                if self._is_cancelled(serial, token): return
                time.sleep(1)
                
            if self._is_cancelled(serial, token): return
            
            # ---------------------------
            # LOGICA LEGO: SMART SCANNER
            # ---------------------------
            if do_like or do_save or do_comment or do_share:
                
                try:
                    # Desincronizacion Natural
                    stagger = random.uniform(1.0, 8.0)
                    time.sleep(stagger)
                    if self._is_cancelled(serial, token): return
                    
                    self.log(f"[{serial[-4:]}] \U0001f50d Tomando radiografia de interfaz...", "info")
                    self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_shorts1.xml"], serial)
                    out1_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_shorts1.xml"], serial)
                    out1 = out1_t[0] if isinstance(out1_t, tuple) else out1_t

                    
                    if self._is_cancelled(serial, token): return
                    if out1 and "<node" in out1:
                        import xml.etree.ElementTree as ET
                        xml_data = out1.encode("utf-8", "ignore")
                        root = ET.fromstring(xml_data)
                        
                        btn_like, btn_save, btn_comment, btn_share = None, None, None, None
                        is_ad = False
                        
                        for node in root.iter("node"):
                            t = (node.get("text") or "").lower()
                            desc = (node.get("content-desc") or "").lower()
                            bounds = node.get("bounds", "")
                            
                            if "patrocinado" in t or "anuncio" in t or "visitar" in t or "instalar" in t:
                                is_ad = True
                                
                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                            if not m: continue
                            cx, cy = (int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2
                            
                            # Logica de deteccion
                            if ("me gusta" in desc or "like" in desc) and ("no me gusta" not in desc and "dislike" not in desc):
                                btn_like = "ALREAD📱_LIKED" if ("quitar" in desc or "remove" in desc) else (cx, cy)
                            if "guardar" in desc or "save" in desc:
                                btn_save = (cx, cy)
                            elif "guardado" in desc or "saved" in desc:
                                btn_save = "ALREAD📱_SAVED"
                            if "comentarios" in desc or "comentar" in desc:
                                btn_comment = "DISABLED" if ("inhabilit" in desc or "desactiv" in desc) else (cx, cy)
                            if "compartir" in desc or "share" in desc:
                                btn_share = (cx, cy)
                                
                        if is_ad:
                            self.log(f"[{serial[-4:]}] \U0001f6a8 Publicidad detectada. Saltando interacciones...", "warn")
                        else:
                            # 2.1 LIKE
                            if do_like and btn_like == "ALREADY_LIKED":
                                self.log(f"[{serial[-4:]}] \U0001f44d El video ya tiene Like.", "info")
                            elif do_like and btn_like:
                                self.log(f"[{serial[-4:]}] \u2764\ufe0f Dando Like en {btn_like}...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_like[0]} {btn_like[1]}"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                                
                            # 2.2 GUARDAR
                            if do_save and btn_save == "ALREADY_SAVED":
                                self.log(f"[{serial[-4:]}] \U0001f4be El video ya estaba guardado.", "info")
                            elif do_save and btn_save:
                                self.log(f"[{serial[-4:]}] \U0001f4be Guardando en listas {btn_save}...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_save[0]} {btn_save[1]}"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                                
                            # 2.3 COMENTAR
                            if do_comment and btn_comment == "DISABLED":
                                self.log(f"[{serial[-4:]}] \U0001f4ac Los comentarios estan inhabilitados.", "warn")
                            elif do_comment and btn_comment:
                                self.log(f"[{serial[-4:]}] \U0001f4ac Abriendo panel de comentarios...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_comment[0]} {btn_comment[1]}"], serial)
                                time.sleep(random.uniform(4.0, 6.0))
                                if self._is_cancelled(serial, token): return
                                
                                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_shorts2.xml"], serial)
                                out2_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_shorts2.xml"], serial)
                                out2 = out2_t[0] if isinstance(out2_t, tuple) else out2_t
                                
                                textbox, btn_close_panel = None, None
                                if out2 and "<node" in out2:
                                    root2 = ET.fromstring(out2.encode("utf-8", "ignore"))
                                    for node in root2.iter("node"):
                                        t = (node.get("text") or "").lower()
                                        d = (node.get("content-desc") or "").lower()
                                        if ("agrega" in t or "comenta" in t) and "inhabilit" not in t:
                                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                            if m: textbox = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                        if "cerrar" in d or "close" in d:
                                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                            if m: btn_close_panel = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                            
                                if textbox:
                                    self.log(f"[{serial[-4:]}] \u2328\ufe0f Abriendo teclado de comentarios...", "info")
                                    self.adb.run_command(["shell", f"input tap {textbox[0]} {textbox[1]}"], serial)
                                    time.sleep(2)
                                    if self._is_cancelled(serial, token): return
                                    
                                    # LIBRERIA DINAMICA
                                    comments_file = os.path.join(os.path.dirname(__file__), "..", "comentarios.txt")
                                    comentarios_default = ["Que buen contenido", "Sigue asi hermano", "Excelente video", "Aca apoyando", "Esto merece hacerse viral"]
                                    comment_to_type = random.choice(comentarios_default)
                                    try:
                                        if os.path.exists(comments_file):
                                            with open(comments_file, "r", encoding="utf-8") as f:
                                                lines = [l.strip() for l in f.readlines() if l.strip()]
                                                if lines: comment_to_type = random.choice(lines)
                                        else:
                                            with open(comments_file, "w", encoding="utf-8") as f:
                                                f.write("\n".join(comentarios_default))
                                    except: pass
                                    
                                    adb_text = comment_to_type.replace(" ", "%s").replace('"', '').replace("'", "")
                                    self.log(f"[{serial[-4:]}] \u270d\ufe0f Escribiendo comentario: '{comment_to_type}'", "info")
                                    self.adb.run_command(["shell", f"input text {adb_text}"], serial)
                                    time.sleep(random.uniform(3.0, 4.0))
                                    if self._is_cancelled(serial, token): return
                                    
                                    # Dump 3 para Enviar
                                    self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_shorts3.xml"], serial)
                                    out3_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_shorts3.xml"], serial)
                                    out3 = out3_t[0] if isinstance(out3_t, tuple) else out3_t
                                    
                                    btn_send = None
                                    if out3 and "<node" in out3:
                                        root3 = ET.fromstring(out3.encode("utf-8", "ignore"))
                                        for node in root3.iter("node"):
                                            d = (node.get("content-desc") or "").lower()
                                            t = (node.get("text") or "").lower()
                                            if "enviar" in d or "send" in d or "publicar" in d or "enviar" in t:
                                                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                                if m: btn_send = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                                
                                    if btn_send:
                                        self.log(f"[{serial[-4:]}] \U0001f680 Enviando comentario...", "info")
                                        self.adb.run_command(["shell", f"input tap {btn_send[0]} {btn_send[1]}"], serial)
                                    else:
                                        self.adb.run_command(["shell", f"input tap {textbox[0]+300} {textbox[1]}"], serial)
                                        
                                    time.sleep(random.uniform(2.5, 4.0))
                                    if self._is_cancelled(serial, token): return
                                    
                                    self.log(f"[{serial[-4:]}] \U0001f519 Cerrando teclado...", "info")
                                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                                    time.sleep(random.uniform(2.0, 3.5))
                                    if self._is_cancelled(serial, token): return
                                    
                                if btn_close_panel:
                                    self.log(f"[{serial[-4:]}] \U0001f519 Cerrando panel (X)...", "info")
                                    self.adb.run_command(["shell", f"input tap {btn_close_panel[0]} {btn_close_panel[1]}"], serial)
                                else:
                                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                                
                            # 2.4 Compartir y Copiar
                            if do_share and isinstance(btn_share, tuple):
                                self.log(f"[{serial[-4:]}] \U0001f517 Abriendo panel de Compartir...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_share[0]} {btn_share[1]}"], serial)
                                time.sleep(random.uniform(4.0, 5.5))
                                if self._is_cancelled(serial, token): return
                                
                                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_share.xml"], serial)
                                out_s_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_share.xml"], serial)
                                out_s = out_s_t[0] if isinstance(out_s_t, tuple) else out_s_t
                                
                                btn_copy = None
                                if out_s and "<node" in out_s:
                                    root_s = ET.fromstring(out_s.encode("utf-8", "ignore"))
                                    for node in root_s.iter("node"):
                                        t = (node.get("text") or "").lower()
                                        d = (node.get("content-desc") or "").lower()
                                        if "copiar" in t or "copy" in t or "copiar" in d or "copy" in d:
                                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                            if m: btn_copy = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                            
                                if btn_copy:
                                    self.log(f"[{serial[-4:]}] \U0001f4cb Copiando vinculo...", "info")
                                    self.adb.run_command(["shell", f"input tap {btn_copy[0]} {btn_copy[1]}"], serial)
                                else:
                                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                except Exception as e:
                    self.log(f"[{serial[-4:]}] \u26a0\ufe0f Error en ciclo avanzado: {e}", "error")
                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                    
            if self._is_cancelled(serial, token): return
                
            self.log(f"[{serial[-4:]}] \u2705 Interaccion completada. \U0001f446 Deslizando al siguiente...", "info")
            self.adb.run_command(["shell", "input", "swipe", "240", "800", "240", "150", "150"], serial)
            short_count += 1
            time.sleep(4)


    def inject_ytshorts_batch(self, devices, urls, t_min, t_max, do_like, do_save, do_comment, do_share, drip_mode="rápido"):
        if not urls:
            self.log("⚠️ No hay URLs de 📱T Shorts", "warn")
            return
        self.log(f"🚀 Inyectando 📱T Shorts en {len(devices)} dispositivos... (Swipe: {t_min}s-{t_max}s | Modo: {drip_mode})", "info")
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
            threading.Thread(target=self.inject_ytshorts, args=(serial, url, t_min, t_max, do_like, do_save, do_comment, do_share, delay), daemon=True).start()


    def inject_twitch(self, serial, url, do_text=False, do_emojis=False, chat_interval=5.0, custom_comments=None, drip_delay=0):
        import time
        import re
        import random
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        self.log(f"[{serial[-4:]}] 🟣 Iniciando Twitch -> {url[:50]}...", "info")
        self._mute_device(serial)

        self.adb.run_command(["shell", "am", "force-stop", "tv.twitch.android.app"], serial)
        self._cleanup_apps(serial, keep_pkg="tv.twitch.android.app")
        time.sleep(2)

        if self._is_cancelled(serial, token): return

        self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"'{url.strip()}'", "tv.twitch.android.app"], serial)
        
        # --- LÓGICA DE AUTO-FOLLOW PARA TWITCH ---
        self.log(f"[{serial[-4:]}] 🟣 Esperando 20s a que Twitch cargue para buscar el botón de Seguir...", "info")
        time.sleep(20)
        
        if self._is_cancelled(serial, token): return
        
        # Escanear UI para Seguir (si falla, no pasa nada)
        dump_name = f"/sdcard/dump_twitch_{serial[-4:]}.xml"
        self.adb.run_command(["shell", "uiautomator", "dump", dump_name], serial)
        xml_data = self.adb.run_command(["shell", "cat", dump_name], serial)[0]
        if xml_data:
            match = re.search(r'<node[^>]*text="(Seguir|Follow)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_data, re.IGNORECASE)
            if match:
                x1, y1, x2, y2 = map(int, match.groups()[1:])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                self.log(f"[{serial[-4:]}] 💜 ¡Botón de Follow detectado! Dándole a Seguir...", "success")
                self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
            else:
                self.log(f"[{serial[-4:]}] 🟣 Ya está siguiendo al canal o el botón no está visible.", "info")
            
        self.log(f"[{serial[-4:]}] 🟣 TWITCH REPRODUCIENDO CORRECTAMENTE", "success")

        # --- LÓGICA DE CHAT ---
        if not do_text and not do_emojis:
            return
            
        self.log(f"[{serial[-4:]}] 💬 Motor de Chat de Twitch Activado (Intervalo: {chat_interval} min)", "info")
        
        def send_comment():
            if self._is_cancelled(serial, token): return
            
            # Obtener resolución de pantalla para hacer tap ciego al 95% abajo
            out = self.adb.run_command(["shell", "wm", "size"], serial)[0]
            cx, cy = 500, 1500 # Fallback
            size_match = re.search(r'Physical size: (\d+)x(\d+)', out)
            if size_match:
                w, h = map(int, size_match.groups())
                cx = w // 2
                cy = int(h * 0.95)
                
            self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
            time.sleep(1.5)
            
            if self._is_cancelled(serial, token): return
            
            nonlocal custom_comments
            custom_comments = custom_comments or ['Siempre firme hoy y siempre', 'Aca apoyando gran mensaje', 'Dios te bendiga un fuerte abrazo', 'Muy interesante desde aca apoyando', 'Dios bendiga tu vida gracias por compartir', 'Sigue confiando en Dios gracias por compartir', 'Sigue asi a seguir asi', 'Oro puro este video exito', 'Increible trabajo me sirve mucho', 'Bendiciones inmensas a seguir asi', 'Sigue confiando en Dios hoy y siempre', 'Buenisimo totalmente de acuerdo', 'Que hermoso mensaje hermano', 'Todo lo puedo en Cristo saludos', 'Que buena vibra!!', 'Amen un fuerte abrazo', 'Genial hoy y siempre', 'De lo mejor que he visto hoy un fuerte abrazo', 'Dios esta en el control totalmente de acuerdo', 'Dios es amor a seguir asi', 'Muy interesante gran mensaje', 'Que el Altisimo te acompane totalmente de acuerdo', 'Que hermoso mensaje a seguir asi', 'Aca apoyando hoy y siempre', 'Dios te bendiga gran mensaje', 'Dios nunca falla hermano', 'Oro puro este video a seguir asi', 'El amor de Dios es infinito totalmente de acuerdo', 'Que Dios te siga usando amigo', 'Me gusto mucho sigue adelante', 'Tremendo aporte amigo', 'Que el Altisimo te acompane!!', 'Siempre firme gran mensaje', 'Sigue confiando en Dios totalmente de acuerdo', 'Me quedo a ver mas hermano', 'Buenisimo cuidese mucho', 'Dios bendiga tu vida cuidese mucho', 'Buenisimo', 'Fuerza y bendiciones no te detengas', 'Dios bendiga tu vida un fuerte abrazo', 'Con Dios todo es posible hoy y siempre', 'Sigue asi me sirve mucho', 'Cristo te ama siempre', 'Genial cuidese mucho', 'Me quedo a ver mas gracias por compartir', 'Que el Senor multiplique tus exitos un fuerte abrazo', 'Que el Senor multiplique tus exitos me sirve mucho', 'Saludos cordiales totalmente de acuerdo', 'Todo lo puedo en Cristo exito', 'A seguir creciendo hoy y siempre', 'Dios esta en el control desde aca apoyando', 'Sigue confiando en Dios desde aca apoyando', 'Bendiciones inmensas gracias por compartir', 'Amemos a Dios siempre siempre', 'Me suscribo y comparto gran mensaje', 'Sigue asi hoy y siempre', 'Aca apoyando hermano', 'Asi es, gloria a Dios a seguir asi', 'Que hermoso mensaje un fuerte abrazo', 'Que buen material hoy y siempre', 'Tremendo aporte exito', 'El amor de Dios es infinito exito', 'Sigue asi', 'Bendiciones inmensas siempre', 'Exito en todo hoy y siempre', 'La rompiste con esto exito', 'Con Dios todo es posible gran mensaje', 'Me encanto sigue adelante', 'Oro puro este video desde aca apoyando', 'Dios es amor', 'Dios esta en el control no te detengas', 'Se nota la dedicacion desde aca apoyando', 'El tiempo de Dios es perfecto sigue adelante', 'Que el Senor multiplique tus exitos!!', 'Que el Senor multiplique tus exitos siempre', 'Paz y bendiciones gracias por compartir', 'Que hermoso mensaje saludos', 'Con Dios todo es posible me sirve mucho', 'Siempre firme un fuerte abrazo', 'El amor de Dios es infinito gran mensaje', 'Gloria a Dios sigue adelante', 'Me quedo a ver mas gran mensaje', 'Dios es amor desde aca apoyando', 'Me encanto!!', 'Tremendo aporte cuidese mucho', 'Increible trabajo amigo', 'Sigue confiando en Dios saludos', 'Mis respetos un fuerte abrazo', 'Que buen material a seguir asi', 'Que Dios te siga usando!!', 'Todo lo puedo en Cristo sigue adelante', 'A seguir creciendo', 'Se nota la dedicacion totalmente de acuerdo', 'El tiempo de Dios es perfecto a seguir asi', 'Me alegraste el dia!!', 'El amor de Dios es infinito no te detengas', 'Que buen material gracias por compartir', 'Esto merece hacerse viral hermano', 'Amemos a Dios siempre un fuerte abrazo', 'Adelante con tu proyecto gracias por compartir', 'Me gusto mucho gracias por compartir', 'Que Dios te siga usando a seguir asi', 'Dios bendiga tu vida gran mensaje', 'Me gusto mucho saludos', 'Me quedo a ver mas hoy y siempre', 'Que el Senor te guarde exito', 'Asi es, gloria a Dios saludos', 'Fe y esperanza sigue adelante', 'Que buen material un fuerte abrazo', 'Adelante con tu proyecto hoy y siempre', 'Muy interesante me sirve mucho', 'Fuerza y bendiciones hermano', 'Sigue asi un fuerte abrazo', 'Sigue confiando en Dios exito', 'Gloria a Dios me sirve mucho', 'A seguir creciendo un fuerte abrazo', 'Dios te bendiga exito', 'Oro puro este video saludos', 'Amen siempre', 'Saludos cordiales no te detengas', 'Que Dios te siga usando hoy y siempre', 'Dios esta en el control me sirve mucho', 'Fuerza y bendiciones sigue adelante', 'De lo mejor que he visto hoy hoy y siempre', 'Amen me sirve mucho', 'Genial gracias por compartir', 'Que el Senor multiplique tus exitos totalmente de acuerdo', 'Que Dios te siga usando hermano', 'Excelente video gracias por compartir', 'Cristo te ama!!', 'Saludos cordiales sigue adelante', 'Que buen contenido no te detengas', 'Me alegraste el dia exito', 'Se nota la dedicacion gracias por compartir', 'Tremendo aporte gran mensaje', 'Me suscribo y comparto no te detengas', 'Me quedo a ver mas cuidese mucho', 'Increible trabajo hoy y siempre', 'Dios nunca falla gracias por compartir', 'Me quedo a ver mas!!', 'Asi es, gloria a Dios desde aca apoyando', 'Amemos a Dios siempre sigue adelante', 'Excelente video hermano', 'La rompiste con esto amigo', 'Mis respetos gracias por compartir', 'Mis respetos saludos', 'Gloria a Dios amigo', 'Que buen contenido', 'Se nota la dedicacion a seguir asi', 'Me encanto hoy y siempre', 'Adelante con tu proyecto!!', 'Muy interesante sigue adelante', 'Amen gran mensaje', 'Saludos cordiales hermano', 'Siempre firme amigo', 'De lo mejor que he visto hoy saludos', 'Que el Senor multiplique tus exitos hoy y siempre', 'Asi es, gloria a Dios amigo', 'Esto merece hacerse viral!!', 'Asi es, gloria a Dios me sirve mucho', 'Sigue confiando en Dios un fuerte abrazo', 'Dios nunca falla siempre', 'Que el Senor te guarde siempre', 'Muy interesante no te detengas', 'Siempre firme a seguir asi', 'Que buena vibra siempre', 'Excelente video totalmente de acuerdo', 'Dios es amor totalmente de acuerdo', 'A seguir creciendo a seguir asi', 'Saludos cordiales', 'Me alegraste el dia hermano', 'Dios nunca falla exito', 'Que hermoso mensaje', 'Adelante con tu proyecto totalmente de acuerdo', 'Que el Senor te guarde hermano', 'Con Dios todo es posible amigo', 'Fe y esperanza exito', 'Dios nunca falla un fuerte abrazo', 'Me gusto mucho no te detengas', 'Tremendo aporte sigue adelante', 'Dios es amor hermano', 'Me gusto mucho!!', 'Con Dios todo es posible desde aca apoyando', 'Que buena vibra hermano', 'Que el Altisimo te acompane hermano', 'Excelente video!!', 'Amemos a Dios siempre gracias por compartir', 'Mis respetos no te detengas', 'Cristo te ama totalmente de acuerdo', 'Me encanto un fuerte abrazo', 'Me gusto mucho me sirve mucho', 'Gloria a Dios cuidese mucho', 'Gloria a Dios totalmente de acuerdo', 'Me quedo a ver mas sigue adelante', 'De lo mejor que he visto hoy exito', 'Que Dios te siga usando gran mensaje', 'Mis respetos totalmente de acuerdo', 'Adelante con tu proyecto sigue adelante', 'Fuerza y bendiciones gracias por compartir', 'Que buen material hermano', 'Asi es, gloria a Dios un fuerte abrazo', 'Amen hoy y siempre', 'Me suscribo y comparto gracias por compartir', 'Excelente video', 'Que el Senor multiplique tus exitos gran mensaje', 'Que buen material exito', 'Que Dios te siga usando no te detengas', 'Dios bendiga tu vida hermano', 'Me gusto mucho siempre', 'Bendiciones inmensas gran mensaje', 'Dios te bendiga desde aca apoyando', 'Exito en todo desde aca apoyando', 'Que el Altisimo te acompane desde aca apoyando', 'Me gusto mucho gran mensaje', 'Oro puro este video no te detengas', 'Me suscribo y comparto totalmente de acuerdo', 'Buenisimo siempre', 'Dios es amor no te detengas', 'Bendiciones inmensas!!', 'Fuerza y bendiciones un fuerte abrazo', 'Dios nunca falla me sirve mucho', 'Que buen material totalmente de acuerdo', 'Fuerza y bendiciones desde aca apoyando', 'Tremendo aporte', 'Siempre firme totalmente de acuerdo', 'Fe y esperanza siempre', 'Se nota la dedicacion me sirve mucho', 'Un abrazo en Cristo!!', 'Paz y bendiciones!!', 'Que el Senor multiplique tus exitos cuidese mucho', 'Sigue asi sigue adelante', 'El tiempo de Dios es perfecto saludos', 'Que buen contenido exito', 'Fe y esperanza hoy y siempre', 'Oro puro este video cuidese mucho', 'Oro puro este video siempre', 'Mis respetos amigo', 'Dios nunca falla saludos', 'Todo lo puedo en Cristo siempre', 'Que hermoso mensaje exito', 'Tremendo aporte desde aca apoyando', 'Que buen material cuidese mucho', 'Fuerza y bendiciones!!', 'Bendiciones inmensas exito', 'Con Dios todo es posible siempre', 'Esto merece hacerse viral exito', 'Que el Senor te guarde no te detengas', 'Amen sigue adelante', 'De lo mejor que he visto hoy a seguir asi', 'Adelante con tu proyecto me sirve mucho', 'Exito en todo totalmente de acuerdo', 'Sigue confiando en Dios cuidese mucho', 'De lo mejor que he visto hoy!!', 'A seguir creciendo amigo', 'Saludos cordiales amigo', 'Todo lo puedo en Cristo gracias por compartir', 'Muy interesante un fuerte abrazo', 'Que el Senor te guarde me sirve mucho', 'Me alegraste el dia gran mensaje', 'Cristo te ama exito', 'Me quedo a ver mas siempre', 'Fe y esperanza hermano', 'Paz y bendiciones siempre', 'Me suscribo y comparto desde aca apoyando', 'Se nota la dedicacion hoy y siempre', 'Me alegraste el dia hoy y siempre', 'Saludos cordiales gran mensaje', 'Dios bendiga tu vida hoy y siempre', 'Que el Altisimo te acompane hoy y siempre', 'Se nota la dedicacion', 'Un abrazo en Cristo exito', 'Que buen material sigue adelante', 'El amor de Dios es infinito!!', 'Dios bendiga tu vida!!', 'Me encanto gran mensaje', 'Todo lo puedo en Cristo desde aca apoyando', 'Todo lo puedo en Cristo!!', 'De lo mejor que he visto hoy sigue adelante', 'Con Dios todo es posible cuidese mucho', 'Aca apoyando!!', 'A seguir creciendo sigue adelante', 'Tremendo aporte!!', 'Se nota la dedicacion no te detengas', 'Aca apoyando cuidese mucho', 'Cristo te ama me sirve mucho', 'Increible trabajo exito', 'Siempre firme desde aca apoyando', 'Se nota la dedicacion sigue adelante', 'Fe y esperanza a seguir asi', 'Excelente video no te detengas', 'Que el Altisimo te acompane siempre', 'Adelante con tu proyecto saludos', 'Que buen material amigo', 'Me alegraste el dia saludos', 'Que hermoso mensaje gracias por compartir', 'Sigue asi!!', 'Asi es, gloria a Dios no te detengas', 'Increible trabajo saludos', 'Dios te bendiga hoy y siempre', 'Excelente video un fuerte abrazo', 'El amor de Dios es infinito hermano', 'El amor de Dios es infinito', 'Adelante con tu proyecto desde aca apoyando', 'Se nota la dedicacion un fuerte abrazo', 'Paz y bendiciones cuidese mucho', 'Que el Altisimo te acompane gran mensaje', 'Siempre firme me sirve mucho', 'De lo mejor que he visto hoy me sirve mucho', 'De lo mejor que he visto hoy cuidese mucho', 'Que el Senor te guarde gracias por compartir', 'Dios te bendiga totalmente de acuerdo', 'Bendiciones inmensas amigo', 'El tiempo de Dios es perfecto me sirve mucho', 'Me gusto mucho amigo', 'Increible trabajo siempre', 'Mis respetos gran mensaje', 'Asi es, gloria a Dios!!', 'Amemos a Dios siempre', 'Paz y bendiciones sigue adelante', 'Esto merece hacerse viral desde aca apoyando', 'Que buena vibra gran mensaje', 'Genial exito', 'Asi es, gloria a Dios', 'Adelante con tu proyecto gran mensaje', 'Siempre firme no te detengas', 'Con Dios todo es posible hermano', 'Que el Altisimo te acompane un fuerte abrazo', 'Buenisimo no te detengas', 'Increible trabajo desde aca apoyando', 'Increible trabajo totalmente de acuerdo', 'Un abrazo en Cristo gran mensaje', 'Esto merece hacerse viral gran mensaje', 'Fe y esperanza desde aca apoyando', 'Saludos cordiales!!', 'Me alegraste el dia sigue adelante', 'Tremendo aporte hoy y siempre', 'Mis respetos exito', 'Dios es amor saludos', 'Siempre firme saludos', 'Cristo te ama hermano', 'Se nota la dedicacion amigo', 'Me suscribo y comparto hermano', 'Que Dios te siga usando un fuerte abrazo', 'Que buen material siempre', 'Exito en todo siempre', 'Gloria a Dios un fuerte abrazo', 'Genial me sirve mucho', 'Adelante con tu proyecto no te detengas', 'Muy interesante totalmente de acuerdo', 'Se nota la dedicacion hermano', 'Amemos a Dios siempre amigo', 'Que buena vibra', 'Gloria a Dios exito', 'Tremendo aporte un fuerte abrazo', 'De lo mejor que he visto hoy hermano', 'Adelante con tu proyecto amigo', 'Un abrazo en Cristo gracias por compartir', 'Oro puro este video totalmente de acuerdo', 'Me alegraste el dia desde aca apoyando', 'Gloria a Dios desde aca apoyando', 'Sigue asi cuidese mucho', 'Siempre firme', 'Excelente video hoy y siempre', 'Exito en todo gran mensaje', 'Amen', 'Cristo te ama desde aca apoyando', 'Exito en todo hermano', 'Con Dios todo es posible!!', 'Me gusto mucho un fuerte abrazo', 'Buenisimo me sirve mucho', 'Me suscribo y comparto me sirve mucho', 'Aca apoyando totalmente de acuerdo', 'Dios es amor hoy y siempre', 'Dios nunca falla', 'Un abrazo en Cristo', 'Gloria a Dios saludos', 'Dios esta en el control amigo', 'Dios bendiga tu vida sigue adelante', 'Amemos a Dios siempre exito', 'Sigue confiando en Dios me sirve mucho', 'Que buen material no te detengas', 'Increible trabajo un fuerte abrazo', 'Aca apoyando gracias por compartir', 'Dios esta en el control saludos', 'Me encanto hermano', 'Me encanto siempre', 'De lo mejor que he visto hoy gran mensaje', 'Se nota la dedicacion siempre', 'Con Dios todo es posible exito', 'Que buen material gran mensaje', 'Dios nunca falla hoy y siempre', 'De lo mejor que he visto hoy desde aca apoyando', 'El tiempo de Dios es perfecto cuidese mucho', 'Aca apoyando un fuerte abrazo', 'Aca apoyando', 'Tremendo aporte hermano', 'La rompiste con esto a seguir asi', 'La rompiste con esto gran mensaje', 'Oro puro este video gran mensaje', 'Que buen contenido cuidese mucho']
            
            msg = random.choice(custom_comments)
            
            if msg.strip():
                self.log(f"[{serial[-4:]}] 💬 Twitch Escribiendo: {msg[:30]}...", "info")
                safe_msg = msg.strip().replace(" ", "\ ")
                safe_msg = safe_msg.replace('"', '\"').replace("'", "\'")
                
                self.adb.run_command(["shell", "input", "text", f"'{safe_msg}'"], serial)
                time.sleep(1)
                self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # ENTER
                
        time.sleep(5)
        send_comment()
        
        while not self._is_cancelled(serial, token):
            wait_time = int(float(chat_interval) * 60)
            for _ in range(wait_time):
                if self._is_cancelled(serial, token): return
                time.sleep(1)
            send_comment()

    def inject_twitch_batch(self, devices, urls, do_text=False, do_emojis=False, chat_interval=5.0, custom_comments=None, drip_mode="rápido"):
        if not devices or not urls: return
        self.log(f"🟣 Inyectando Twitch en {len(devices)} dispositivo(s)... (Modo: {drip_mode})", "info")
        for i, dev in enumerate(devices):
            import random
            url = random.choice(urls)
            delay = 0
            if drip_mode == "rápido" and i > 0: delay = i * random.randint(3, 8)
            elif drip_mode == "lento" and i > 0: delay = i * random.randint(15, 30)
            elif i > 0: delay = i * 1.5
            import threading
            threading.Thread(target=self.inject_twitch, args=(dev["serial"], url, do_text, do_emojis, chat_interval, custom_comments, delay), daemon=True).start()


    def inject_kick(self, serial, url, do_text=False, do_emojis=False, chat_interval=5, custom_comments=None, drip_delay=0):
        self._mute_device(serial)
        import time, random, re
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        self.log(f"[{serial[-4:]}] 🟩 Iniciando Kick -> {url[:50]}...", "info")

        self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], serial)
        self._cleanup_apps(serial, keep_pkg="com.kick.mobile")
        time.sleep(2)

        if self._is_cancelled(serial, token): return

        self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"'{url.strip()}'", "com.kick.mobile"], serial)
        
        for i in range(15):
            if self._is_cancelled(serial, token): return
            time.sleep(1)

        self.log(f"[{serial[-4:]}] ✅ KICK REPRODUCIENDO CORRECTAMENTE", "success")
        
        if not do_text and not do_emojis:
            return
            
        self.log(f"[{serial[-4:]}] 💬 Motor de Chat de Kick Activado (Intervalo: {chat_interval} min)", "info")
        
        def click_chat():
            dump_name = f"/sdcard/dump_kick_{serial[-4:]}.xml"
            self.adb.run_command(["shell", "uiautomator", "dump", dump_name], serial)
            out_t = self.adb.run_command(["shell", "cat", dump_name], serial)
            out = out_t[0] if isinstance(out_t, tuple) else out_t
            if out:
                import xml.etree.ElementTree as ET
                out = re.sub(r"<\?xml.*?\?>", "", out)
                try:
                    root = ET.fromstring(out.encode("utf-8", "ignore"))
                    
                    # Para saber donde esta el medio de la pantalla
                    screen_h = 1000
                    
                    best_match = None
                    for node in root.iter("node"):
                        text_n = (node.get("text") or "").lower()
                        desc = (node.get("content-desc") or "").lower()
                        c_class = (node.get("class") or "").lower()
                        bounds = node.get("bounds", "")
                        
                        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                        if m:
                            x1, y1, x2, y2 = map(int, m.groups())
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            
                            # Criterio 1: Palabras exactas de la caja de texto (prioridad alta)
                            if any(w in text_n or w in desc for w in ["send a message", "enviar mensaje", "escribe un mensaje"]):
                                best_match = (cx, cy)
                                break # match perfecto, salimos
                                
                            # Criterio 2: Es un EditText (Caja de texto real)
                            if "edittext" in c_class:
                                best_match = (cx, cy)
                                
                            # Criterio 3: Palabras genericas pero solo si estan en la mitad inferior de la pantalla (Y > 500)
                            if any(w in text_n or w in desc for w in ["chat", "mensaje", "chatear"]):
                                if cy > 500:
                                    best_match = (cx, cy)
                                    
                    if best_match:
                        self.adb.run_command(["shell", "input", "tap", str(best_match[0]), str(best_match[1])], serial)
                        return True
                except: pass
            return False
            
        def send_comment():
            self.adb.run_command(["shell", "input", "tap", "360", "400"], serial)
            time.sleep(1.0)
            
            if click_chat():
                time.sleep(1.5)
                msg = ""
                if do_text and custom_comments: msg = random.choice(custom_comments)
                elif do_text: msg = random.choice(["Buen stream, crack.", "Excelente directo.", "Se disfruta mucho este stream.", "Buen contenido, seguí así.", "Muy buen trabajo.", "Tremendo directo.", "Acá bancando el stream.", "Buenísima transmisión.", "Se viene un gran stream.", "Todo muy bien armado.", "Gran directo hoy.", "Muy entretenido el contenido.", "Buen ambiente por acá.", "Está muy bueno el stream.", "Se nota el esfuerzo.", "Buen trabajo con la transmisión.", "Excelente energía.", "Me gusta mucho este contenido.", "Muy buen ritmo de stream.", "Todo excelente por acá.", "Stream de calidad.", "Se disfruta cada minuto.", "Muy buena transmisión.", "Acá acompañando como siempre.", "Buen directo para pasar el rato.", "Gran contenido, de verdad.", "Muy buena onda en el chat.", "Se viene una linda transmisión.", "Buen stream para arrancar.", "Todo muy claro y entretenido.", "Muy buen desempeño.", "La transmisión está impecable.", "Buenísimo el contenido.", "Acá apoyando el proyecto.", "Gran trabajo con el directo.", "Me quedo viendo un rato.", "Está muy interesante el stream.", "Excelente presentación.", "Buen contenido como siempre.", "Se nota la dedicación.", "Muy buen directo, gente.", "La estamos pasando bien.", "Este stream promete.", "Buena transmisión hoy.", "Muy entretenido todo.", "Buen ambiente en el canal.", "Gran nivel de contenido.", "Todo muy prolijo.", "Excelente directo, seguí así.", "Acá presentes en el stream.", "Muy buen trabajo con el canal.", "El stream está muy bueno.", "Se disfruta la energía.", "Buena calidad de transmisión.", "Gran contenido para la comunidad.", "Muy buena onda.", "Directo interesante y entretenido.", "Todo excelente hasta ahora.", "Buen stream para acompañar.", "Se nota el progreso.", "Muy buen manejo del directo.", "Gran trabajo hoy.", "La transmisión está genial.", "Buen contenido y buena energía.", "Acá mirando tranquilamente.", "Muy buen stream, felicitaciones.", "Excelente comunidad.", "Está saliendo muy bien.", "Buen directo para quedarse.", "Todo muy entretenido.", "Muy buena transmisión, crack.", "El canal viene creciendo.", "Buen trabajo con la producción.", "Este directo está genial.", "La estamos disfrutando.", "Gran stream para hoy.", "Muy buena calidad.", "Acá acompañando el directo.", "Se viene contenido interesante.", "Excelente ambiente en el canal.", "Muy buen stream hasta ahora.", "Está todo muy bien.", "Gran energía en la transmisión.", "Buen contenido para la comunidad.", "Se nota la buena preparación.", "Stream tranquilo y entretenido.", "Muy buena propuesta.", "Todo va excelente.", "Gran directo, como siempre.", "Acá firmes bancando.", "Muy buen canal.", "Se disfruta mucho este espacio.", "Buen trabajo, seguí metiéndole.", "Está muy bueno acompañar.", "Excelente stream para la noche.", "Gran contenido y buena onda.", "Muy buena transmisión en Kick.", "El directo está impecable.", "Acá viendo y apoyando.", "Buen stream, éxitos siempre.", "Muchas buenas vibras para el stream.", "Todo el apoyo para vos.", "Que salga excelente la transmisión.", "Te mando mucha fuerza.", "Acá apoyando con buena onda.", "Que siga creciendo el canal.", "Muchos éxitos en el directo.", "Ojalá tengas un stream increíble.", "Todo lo mejor para hoy.", "Mandando apoyo desde acá.", "Que llegue mucha gente nueva.", "Buenas energías para el stream.", "Te deseo una gran transmisión.", "Mucho éxito con el contenido.", "Que sigan los buenos directos.", "Acá dejando apoyo.", "Que tengas una noche excelente.", "Te mando las mejores vibras.", "Todo mi apoyo para el canal.", "Que el stream siga creciendo.", "Mucha suerte en la transmisión.", "Que tengas un directo genial.", "Apoyando siempre el contenido.", "Buenas vibras para toda la comunidad.", "Que venga una gran jornada.", "Te deseo muchos éxitos.", "Acá presentes mandando apoyo.", "Que se cumplan todos los objetivos.", "Mucha fuerza y buena energía.", "Apoyo total para este stream.", "Que sigan llegando buenas noticias.", "Te mando energía positiva.", "Ojalá sea un directo excelente.", "Todo el apoyo desde el chat.", "Que disfrutes mucho la transmisión.", "Mucha suerte con el canal.", "Que siga la buena racha.", "Buenas vibras para todos.", "Apoyando este proyecto.", "Te deseo lo mejor siempre.", "Que el stream salga perfecto.", "Mucho ánimo para seguir.", "Acá sumando buena energía.", "Que crezca mucho la comunidad.", "Todo va a salir muy bien.", "Buenas vibras y muchos éxitos.", "Te mando apoyo sincero.", "Que tengas un gran día.", "Mucha fuerza para el directo.", "Apoyo y respeto siempre.", "Que continúe el crecimiento.", "Te deseo un stream increíble.", "Acá acompañando con buena onda.", "Mucha energía para hoy.", "Que se cumplan tus metas.", "Todo lo mejor para el canal.", "Buenas vibras desde este chat.", "Mucho apoyo para la transmisión.", "Que sigan los buenos momentos.", "Ojalá venga una gran audiencia.", "Te mando mis mejores deseos.", "Acá apoyando el esfuerzo.", "Que salga todo genial.", "Mucha suerte con el contenido.", "Buenas energías para la comunidad.", "Todo mi respeto y apoyo.", "Que siga creciendo este espacio.", "Mucho ánimo, vas muy bien.", "Te deseo una transmisión increíble.", "Apoyando con toda la buena onda.", "Que hoy sea una gran noche.", "Muchas fuerzas para seguir creando.", "Acá dejando buenas vibras.", "Éxitos para todo el equipo.", "Ojalá alcances tus objetivos.", "Mucho apoyo para este proyecto.", "Que no pare el crecimiento.", "Todo lo mejor para el stream.", "Te mando buena energía.", "Que tengas una transmisión excelente.", "Apoyo total desde acá.", "Que se venga una gran noche.", "Mucha suerte y buenas vibras.", "Acá bancando el contenido.", "Que cada stream sea mejor.", "Te deseo mucho éxito.", "Todo el ánimo para hoy.", "Que siga la buena onda.", "Buenas vibras para el canal.", "Apoyando cada paso.", "Que lleguen más seguidores.", "Mucho éxito en esta etapa.", "Te mando fuerza y apoyo.", "Que se cumplan tus planes.", "Acá con energía positiva.", "Todo va a salir genial.", "Mucha suerte con el directo.", "Que siga creciendo la comunidad.", "Apoyo sincero para vos.", "Buenas vibras y excelente stream.", "¿Cómo viene el stream?", "¿Qué tal estuvo tu día?", "¿Qué vamos a ver hoy?", "¿Hace cuánto empezaste a transmitir?", "¿Cuál es el objetivo de hoy?", "¿Qué juego estás jugando?", "¿Vas a cambiar de juego después?", "¿Qué te motivó a hacer stream?", "¿Cuál es tu juego favorito?", "¿Qué música estás escuchando?", "¿Tenés alguna meta para este mes?", "¿Cuál fue tu mejor directo?", "¿Qué horario te gusta más para transmitir?", "¿Vas a hacer algún desafío?", "¿Qué recomendás para empezar en Kick?", "¿Cuál fue tu primer juego?", "¿Jugás también fuera de stream?", "¿Qué te parece este mapa?", "¿Cuál es tu personaje favorito?", "¿Qué estrategia estás usando?", "¿Vas a jugar con seguidores?", "¿Qué equipo estás usando?", "¿Tenés pensado hacer colaboraciones?", "¿Cuál fue tu momento favorito del stream?", "¿Qué contenido querés hacer después?", "¿Preferís jugar solo o acompañado?", "¿Qué juego recomendás para hoy?", "¿Cuánto hace que conocés Kick?", "¿Qué te parece la plataforma?", "¿Tenés otros canales?", "¿Dónde publicás tus clips?", "¿Cuál fue tu mejor partida?", "¿Qué objetivo estás buscando?", "¿Vas a seguir hasta más tarde?", "¿Qué fue lo más difícil de esta partida?", "¿Cómo elegís tus juegos?", "¿Cuál es tu modo favorito?", "¿Qué juego te gustaría probar?", "¿Vas a subir este directo?", "¿Qué consejo le darías a un streamer nuevo?", "¿Tenés alguna rutina antes del stream?", "¿Qué te gusta más, competir o divertirte?", "¿Cuál es tu mapa favorito?", "¿Qué personaje usás normalmente?", "¿Jugás en PC o consola?", "¿Qué micrófono estás usando?", "¿Qué cámara recomendás?", "¿Cómo preparás el directo?", "¿Qué meta querés alcanzar hoy?", "¿Cuál fue tu primer canal?", "¿Qué juego te trajo más visitas?", "¿Te gusta hacer streams largos?", "¿Tenés pensado hacer sorteos?", "¿Qué tipo de clips funcionan mejor?", "¿Qué horario te dio mejores resultados?", "¿Cómo conociste a tu comunidad?", "¿Qué te gustaría mejorar del canal?", "¿Vas a hacer contenido especial pronto?", "¿Qué opinás de esta actualización?", "¿Cuál es tu arma preferida?", "¿Qué consejo te ayudó más?", "¿Tenés algún ritual para ganar?", "¿Cuál es tu ranking actual?", "¿Querés llegar a alguna categoría?", "¿Qué fue lo primero que streameaste?", "¿Qué te gusta mirar cuando no transmitís?", "¿Seguís a otros streamers?", "¿Qué canal recomendás?", "¿Qué juego te gustaría dominar?", "¿Cómo elegís los títulos del stream?", "¿Leés todos los mensajes del chat?", "¿Qué te parece la comunidad?", "¿Vas a jugar competitivo?", "¿Qué modo te resulta más divertido?", "¿Tenés alguna meta de seguidores?", "¿Qué contenido te gustaría sumar?", "¿Qué fue lo más gracioso de hoy?", "¿Cuál es tu mayor logro en Kick?", "¿Qué te gustaría conseguir este año?", "¿Vas a hacer una pausa pronto?", "¿Qué te parece el nuevo parche?", "¿Qué consejo darías para mejorar?", "¿Cuál fue tu mejor victoria?", "¿Qué juego te frustró más?", "¿Cómo mantenés la energía en streams largos?", "¿Qué parte del stream disfrutás más?", "¿Qué te gustaría que votemos?", "¿Vas a abrir el chat de voz?", "¿Qué canción te pone de buen humor?", "¿Tenés una playlist para transmitir?", "¿Cuál es tu comida para los streams?", "¿Qué haces cuando perdés?", "¿Cuál es tu próximo objetivo?", "¿Qué contenido te gustaría repetir?", "¿Vas a invitar a alguien?", "¿Qué te parece este desafío?", "¿Qué juego te sorprendió más?", "¿Qué esperás de la comunidad?", "¿Qué fue lo mejor de esta semana?", "¿Qué plan tenés para el próximo stream?", "¡Vamos que arranca!", "¡Se viene lo bueno!", "¡Todo el chat presente!", "¡Vamos con toda!", "¡Que no pare el stream!", "¡Hoy se rompe todo!", "¡Tremendo momento!", "¡Vamos por esa victoria!", "¡El chat está activo!", "¡Se siente la energía!", "¡A dejar todo!", "¡Vamos equipo!", "¡Esto recién empieza!", "¡Qué buen momento!", "¡Estamos a full!", "¡Se viene una jugada épica!", "¡Vamos por más!", "¡El directo está encendido!", "¡Que siga la acción!", "¡Todo el chat bancando!", "¡Se viene una remontada!", "¡No aflojes ahora!", "¡Vamos que se puede!", "¡Esto está increíble!", "¡Chat, hagamos ruido!", "¡Tremenda energía!", "¡A romperla hoy!", "¡Vamos por el objetivo!", "¡El stream está prendido!", "¡Se siente el hype!", "¡Qué manera de jugar!", "¡Estamos todos mirando!", "¡Vamos con ese desafío!", "¡No se puede perder este momento!", "¡El chat acompaña!", "¡Se viene una gran partida!", "¡Dale que sale!", "¡Esto está emocionante!", "¡Vamos por otra!", "¡A seguir metiéndole!", "¡El canal está en llamas!", "¡Tremendo directo!", "¡Hoy hay victoria!", "¡Todos apoyando!", "¡La comunidad está presente!", "¡Vamos por esa meta!", "¡Qué nivel!", "¡No aflojes, crack!", "¡Se viene algo grande!", "¡El chat no abandona!", "¡Estamos firmes!", "¡A mantener la concentración!", "¡Vamos por todo!", "¡Esto se pone bueno!", "¡Tremenda jugada!", "¡La energía está arriba!", "¡No se detiene!", "¡Vamos a celebrar!", "¡El stream está increíble!", "¡A demostrar ese nivel!", "¡Chat activo!", "¡Vamos con la próxima!", "¡Se viene el momento clave!", "¡Qué partida!", "¡A seguir con esa energía!", "¡Todos juntos!", "¡Esto promete muchísimo!", "¡Vamos por la remontada!", "¡El público está presente!", "¡Dale con todo!", "¡No hay que rendirse!", "¡Estamos cerca!", "¡Se siente la emoción!", "¡Vamos por ese objetivo!", "¡Tremendo ambiente!", "¡El directo está volando!", "¡Hoy se gana!", "¡A mantener el ritmo!", "¡Qué espectáculo!", "¡Vamos que falta poco!", "¡Todos dejando apoyo!", "¡El chat está imparable!", "¡Se viene una locura!", "¡Gran jugada!", "¡La comunidad responde!", "¡Vamos a seguir!", "¡Momento histórico!", "¡Muchísima energía!", "¡No pare el hype!", "¡Estamos disfrutando mucho!", "¡A darlo todo!", "¡Vamos por otra victoria!", "¡El stream está prendidísimo!", "¡Chat, acompañemos!", "¡Se viene la mejor parte!", "¡Qué nivel de directo!", "¡Estamos todos atentos!", "¡A celebrar ese logro!", "¡La rompiste!", "¡Vamos por más, siempre!", "Acá seguimos firmes.", "Muy buen ambiente hoy.", "El directo está excelente.", "Se disfruta mucho este contenido.", "Todo el apoyo para el canal.", "Gran trabajo con la transmisión.", "Buenísima energía en el chat.", "El stream viene genial.", "Acá acompañando el momento.", "Muy buena comunidad.", "Está muy entretenido todo.", "Buen contenido para mirar tranquilo.", "Se nota el esfuerzo diario.", "Excelente trabajo hoy.", "Todo muy bien por acá.", "Buen stream para compartir.", "La transmisión está saliendo genial.", "Acá presentes apoyando.", "Muy buena propuesta de contenido.", "El canal tiene gran ambiente.", "Se viene un gran directo.", "Todo muy prolijo y entretenido.", "Buen trabajo, seguí adelante.", "La comunidad está muy buena.", "Este stream está para quedarse.", "Gran energía durante la transmisión.", "Buen contenido y buen ambiente.", "Acá mirando con atención.", "Muy buen ritmo.", "Excelente directo hasta ahora.", "Está muy buena la transmisión.", "Gran trabajo con el canal.", "Todo va muy bien.", "Buen momento para acompañar.", "El stream está muy entretenido.", "Acá bancando cada directo.", "Muy buena calidad de contenido.", "Se disfruta la transmisión.", "Gran ambiente en el chat.", "Buenísimo lo que estás haciendo.", "El canal viene muy bien.", "Me gusta mucho este formato.", "Buen directo para la comunidad.", "Acá apoyando con respeto.", "Muy buen nivel de stream.", "Se viene una noche genial.", "El contenido está muy bueno.", "Excelente manera de transmitir.", "Acá disfrutando el directo.", "Gran trabajo con la producción.", "La comunidad acompaña siempre.", "Todo muy entretenido hoy.", "El canal transmite muy buena onda.", "Está saliendo todo excelente.", "Se nota el crecimiento.", "Buen stream para pasar el rato.", "Acá seguimos acompañando.", "Excelente contenido, de verdad.", "Muy buena energía general.", "Todo está muy bien organizado.", "Gran directo para hoy.", "Buen trabajo y buena actitud.", "El stream está muy activo.", "Acá dejando apoyo nuevamente.", "Muy buen contenido para mirar.", "Gran ambiente en este canal.", "Se disfruta cada momento.", "Buenísima onda por acá.", "El directo está muy completo.", "Excelente forma de crear comunidad.", "Acá firmes con el stream.", "Todo muy interesante.", "Buen trabajo, se nota la mejora.", "Gran contenido para la audiencia.", "Muy buena experiencia de stream.", "Se viene más contenido bueno.", "El canal está creciendo mucho.", "Buen ambiente y buena energía.", "Muy entretenido el directo.", "Excelente trabajo como siempre.", "Acá disfrutando la transmisión.", "Todo está saliendo muy bien.", "Muy buen espacio para compartir.", "Gran stream para la comunidad.", "Buen contenido y buena compañía.", "Se nota el compromiso.", "Acá presentes hasta el final.", "Muy buena transmisión hoy.", "Todo mi apoyo para este canal.", "Gran trabajo, felicitaciones.", "Acá bancando con buena onda.", "Excelente stream, muchos éxitos.", "Hey chat!", "Yo, what’s up?", "How’s everyone doing?", "Glad to be here.", "Just chilling in chat.", "This stream is fun.", "Nice stream today.", "I’m enjoying this.", "The vibes are good.", "This is entertaining.", "Hello everyone!", "Chat is active today.", "Good vibes here.", "I just arrived.", "What did I miss?", "This is already funny.", "The stream looks great.", "I’m staying for a while.", "Nice atmosphere.", "This chat is friendly.", "Hope everyone is good.", "Great stream so far.", "The timing is perfect.", "I caught the best part.", "This is fun to watch.", "The chat is moving fast.", "What’s happening?", "I’m enjoying the show.", "Nice energy today.", "This is a good stream.", "Hello from chat!", "I’m here for the vibes.", "This is actually fun.", "The community seems cool.", "I just joined.", "Good evening everyone.", "Hope the stream goes well.", "This is a nice way to relax.", "The stream feels chill.", "I like this content.", "Good to see everyone.", "The chat is funny today.", "I’m watching quietly.", "This is a great moment.", "Nice setup.", "The stream looks clean.", "Good atmosphere in here.", "I’m enjoying the gameplay.", "This is pretty entertaining.", "The stream is going well.", "What’s the plan today?", "Is this your usual game?", "Who else is watching?", "This chat is great.", "I’m just passing by.", "Glad I found this stream.", "This is better than expected.", "Nice community here.", "The vibes are excellent.", "I’ll stay for a bit.", "This is a fun place.", "Good content as always.", "The stream is smooth.", "Nice job so far.", "I’m having a good time.", "Chat is in a good mood.", "This is really enjoyable.", "What a nice stream.", "I like the energy.", "Everything looks good.", "Great timing joining now.", "This is a cool channel.", "I’m enjoying the moment.", "Good luck with the stream.", "This is a nice hangout.", "The chat is welcoming.", "Pretty good stream.", "This is relaxing.", "I’m here to support.", "Nice work today.", "The stream feels positive.", "I like this community.", "Good vibes only.", "This is fun already.", "The content is solid.", "I’m enjoying the session.", "Nice place to hang out.", "The chat is alive.", "Great stream energy.", "This is really cool.", "I just discovered the channel.", "Looks like a fun stream.", "I’m watching from the side.", "Everything is going smoothly.", "Nice to be here.", "This is a good time.", "Great atmosphere, everyone.", "I’m enjoying the stream.", "The channel is doing great.", "Good stream, everyone.", "XD", "LOL", "LMAO", "I’m crying XD", "That was hilarious.", "LOL what was that?", "Bro, seriously?", "I can’t stop laughing.", "That timing was perfect.", "XD this chat.", "LOL nice one.", "That was so funny.", "I was not ready.", "Bro, what happened?", "I’m dead LOL.", "That caught me off guard.", "XD no way.", "This is comedy.", "LMAO that reaction.", "I can’t believe that.", "That was too good.", "LOL chat is wild.", "Why is this so funny?", "I’m laughing so hard.", "XD the timing.", "That was unexpected.", "Bro got surprised.", "This is hilarious.", "LOL I saw that.", "No way XD.", "That reaction was priceless.", "I’m actually crying.", "What just happened?", "LMAO incredible.", "This stream is funny.", "XD that move.", "I wasn’t expecting that.", "LOL what a moment.", "This is pure chaos.", "Bro, please.", "That was amazing.", "I can’t handle this chat.", "XD everyone saw that.", "LOL the perfect fail.", "That was so random.", "I’m laughing at the chat.", "This keeps getting better.", "LMAO no way.", "That was wild.", "XD I’m done.", "What a funny moment.", "LOL classic.", "That was smooth and funny.", "I’m losing it.", "Bro really did that.", "This is too entertaining.", "XD unbelievable.", "That was a perfect reaction.", "LOL I needed that.", "This is so chaotic.", "I can’t stop laughing XD.", "That was comedy gold.", "No words, just LOL.", "This chat is dangerous.", "LMAO what a play.", "That was beautiful chaos.", "XD the confidence.", "I did not see that coming.", "LOL that face.", "This is too funny.", "Bro is feeling lucky.", "That was a moment.", "I’m laughing so much.", "XD instant classic.", "LOL absolutely not.", "This is amazing.", "That was a funny fail.", "LMAO the timing.", "I’m gone, goodbye XD.", "This chat never disappoints.", "That was hilarious, bro.", "LOL what a save.", "I can’t believe my eyes.", "XD the reaction.", "That was so clean.", "LMAO I’m finished.", "This is getting ridiculous.", "LOL perfect.", "Bro, that was crazy.", "I’m laughing in silence.", "XD this is priceless.", "That was a great moment.", "LOL the confidence.", "I’m not okay.", "This stream is comedy.", "LMAO unbelievable play.", "That was unexpectedly funny.", "XD I love this chat.", "LOL what a stream.", "Best moment so far XD.", "GG", "GG well played.", "Huge W.", "Common W.", "Massive W.", "Big win.", "Clean play.", "Nice clutch.", "That was insane.", "What a play.", "Huge clutch.", "Nice move.", "Perfect timing.", "Great reaction.", "That was clean.", "Incredible play.", "Nice one!", "Well played.", "That was smooth.", "What a save.", "Amazing round.", "Great decision.", "Huge comeback.", "Nice strategy.", "That was smart.", "Excellent play.", "Big brain move.", "Incredible clutch.", "That was perfect.", "GG everyone.", "Clean victory.", "What a finish.", "Great round.", "Nice teamwork.", "Huge moment.", "That was impressive.", "Strong play.", "Excellent timing.", "Beautiful move.", "Great execution.", "That was legendary.", "Nice comeback.", "Huge W for the team.", "What a battle.", "Very well played.", "Great strategy.", "That was intense.", "Nice recovery.", "Perfect reaction.", "What a clutch.", "Amazing finish.", "Clean win.", "That was powerful.", "Big achievement.", "Great performance.", "Nice positioning.", "Smart play.", "Fantastic round.", "Huge play.", "That was close.", "Almost a perfect run.", "Nice effort.", "Great attempt.", "Good try.", "F in the chat.", "Press F.", "That hurts.", "Unlucky moment.", "So close.", "Almost had it.", "That was unfortunate.", "Better luck next round.", "It happens.", "Don’t worry, bro.", "Comeback incoming.", "Reset and go again.", "We still believe.", "Next round is yours.", "That was unlucky.", "Strong recovery.", "Nice comeback energy.", "Keep going.", "Don’t give up.", "You got this.", "One more try.", "The next one is a W.", "We can recover.", "Good effort.", "That was a tough round.", "Respect the attempt.", "Nice challenge.", "Close game.", "Great fight.", "Almost there.", "Keep pushing.", "The comeback starts now.", "We believe in the W.", "GG, next game.", "Let’s get the next win.", "Let’s go!", "We got this!", "Keep it going!", "Don’t stop now!", "Huge energy!", "The hype is real!", "Chat is ready!", "Let’s get this win!", "Big moment incoming!", "Everyone stay focused!", "We are locked in.", "This is the moment.", "Let’s go for it!", "Keep pushing!", "The chat believes!", "Time to shine!", "Bring the energy!", "We’re almost there!", "Let’s make it happen!", "Big goals today!", "The stream is popping.", "Chat is on fire.", "What a vibe!", "We’re all here.", "Let’s support the play.", "This is getting exciting.", "The energy is amazing.", "Keep the momentum.", "One step closer.", "Let’s go, streamer!", "Huge vibes in chat.", "This is our moment.", "We’re ready.", "Don’t lose focus.", "Keep that energy high.", "Let’s get another one.", "The hype is building.", "Everyone spam W.", "W in the chat!", "Let’s go team!", "We’re behind you.", "The community is strong.", "Big support from chat.", "This is looking good.", "We’re fully locked in.", "Keep the pressure.", "Let’s make history.", "Big play coming.", "Let’s finish strong.", "We’re not giving up.", "Stay confident.", "Keep believing.", "The win is close.", "Let’s bring it home.", "Massive energy right now.", "Everyone is watching.", "This is intense.", "Let’s go all the way.", "We’re ready for this.", "Keep fighting.", "The next play is huge.", "Let’s turn it around.", "Comeback time.", "The hype is unmatched.", "Chat, show some love.", "Let’s support the stream.", "Big respect always.", "Keep doing your thing.", "We love the energy.", "This is a great run.", "The goal is close.", "Let’s stay positive.", "We’re almost at the top.", "Huge moment for the channel.", "Keep the stream alive.", "Everyone drop a W.", "Let’s keep the vibes.", "The chat is strong today.", "Go for the big play.", "You’re doing great.", "Keep showing that skill.", "We’re all cheering.", "Let’s get another victory.", "The community is ready.", "This is so exciting.", "Stay calm and win.", "The finish is near.", "Let’s close it out.", "Keep that focus.", "We’re going higher.", "The stream is unstoppable.", "Big support from everyone.", "This is pure hype.", "Let’s make it count.", "We’re with you.", "Keep the momentum alive.", "Let’s get the W.", "Huge support today.", "Never stop grinding.", "Nice stream, bro.", "Keep up the great work.", "You’re doing amazing.", "This channel is awesome.", "I like the content.", "The vibes are perfect.", "Good luck today.", "Hope you reach your goal.", "Keep growing the channel.", "Much respect.", "Sending support.", "You have great energy.", "The stream looks amazing.", "This community is great.", "Keep creating.", "Good luck with the next round.", "I’ll stay for a while.", "This is a fun stream.", "The chat is awesome.", "Great atmosphere here.", "Keep the good vibes.", "I’m glad I joined.", "This is a good channel.", "The audio sounds good.", "The stream is running well.", "Great content today.", "Keep doing your best.", "You deserve more viewers.", "Hope the channel grows.", "This stream is underrated.", "You have a good community.", "I like your style.", "The energy is great.", "Thanks for the entertainment.", "This is a nice place.", "Good job with the stream.", "The content is relaxing.", "I’m enjoying this session.", "You’re improving a lot.", "Keep working hard.", "Great job, streamer.", "The stream is fun today.", "I support the grind.", "Nice work, as always.", "The channel has potential.", "Keep building your community.", "This is worth watching.", "Great vibes tonight.", "You’re doing a solid job.", "Keep the momentum going.", "I like this gameplay.", "The stream is very entertaining.", "Good luck with your goals.", "Keep chasing the dream.", "Your effort shows.", "Nice broadcast today.", "I’m enjoying the chat.", "Great job staying focused.", "This is a strong stream.", "Keep the energy alive.", "You have good timing.", "Nice reactions.", "The gameplay is impressive.", "This is very fun.", "Good luck with the channel.", "You’re creating a great space.", "Much love from chat.", "Keep moving forward.", "Great job entertaining everyone.", "This channel deserves support.", "The stream is getting better.", "You’re doing well today.", "I like the positive energy.", "Nice community spirit.", "Keep sharing good vibes.", "The stream is worth staying for.", "Great effort today.", "Keep enjoying the game.", "You have a good style.", "This is a great hangout.", "I’m happy to be here.", "Sending good vibes.", "Keep having fun.", "Great job with everything.", "You’re building something nice.", "Good content and good vibes.", "I’ll keep watching.", "Keep doing what you love.", "Respect and support.", "Great stream, everyone.", "GG, good vibes, and respect."])
                if do_emojis:
                    emojis = ["🔥", "😎", "🚀", "💯", "🎮", "💪", "🙌"]
                    msg += " " + random.choice(emojis)
                    
                if msg.strip():
                    self.log(f"[{serial[-4:]}] 💬 Kick Escribiendo: {msg}", "info")
                    safe_msg = msg.strip().replace(" ", "%s")
                    self.adb.run_command(["shell", "input", "text", f"'{safe_msg}'"], serial)
                    time.sleep(1)
                    self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # ENTER
            else:
                self.log(f"[{serial[-4:]}] ⚠️ No se vio la caja de chat de Kick.", "warn")

        time.sleep(5)
        send_comment()
        
        while not self._is_cancelled(serial, token):
            wait_time = int(float(chat_interval) * 60)
            for _ in range(wait_time):
                if self._is_cancelled(serial, token): return
                time.sleep(1)
            send_comment()

    def inject_kick_batch(self, devices, urls, do_text=False, do_emojis=False, chat_interval=5, custom_comments=None, drip_mode="rápido"):
        if not devices or not urls: return
        self.log(f"🟩 Inyectando Kick en {len(devices)} dispositivo(s)...", "info")
        for i, dev in enumerate(devices):
            import random
            url = random.choice(urls)
            delay = 0
            if drip_mode == "rápido" and i > 0: delay = i * random.randint(3, 8)
            elif drip_mode == "lento" and i > 0: delay = i * random.randint(15, 30)
            elif i > 0: delay = i * 1.5
            import threading
            threading.Thread(target=self.inject_kick, args=(dev["serial"], url, do_text, do_emojis, chat_interval, custom_comments, delay), daemon=True).start()

    def inject_ytshorts(self, serial, url, t_min, t_max, do_like, do_save, do_comment, do_share, delay_start=0):
        try:
            t_min, t_max = int(t_min), int(t_max)
        except: pass
        token = self._new_token(serial)
        if delay_start > 0:
            time.sleep(delay_start)
        if self._is_cancelled(serial, token): return
        
        self.adb.run_command(["shell", "svc", "wifi", "enable"], serial) # 📡 PRENDER WIFI (Engaño Android)
        
        self.adb.run_command(["shell", "am", "force-stop", "com.google.android.youtube"], serial)
        self._cleanup_apps(serial, keep_pkg="com.google.android.youtube")
        time.sleep(4)
        clean_url = url.strip()
        import re
        if "/shorts/" in clean_url and "@" not in clean_url:
            match = re.search(r'/shorts/([a-zA-Z0-9_-]+)', clean_url)
            if match:
                vid = match.group(1)
                clean_url = f"https://www.youtube.com/watch?v={vid}"
        self.adb.run_command(["shell", "am", "start", "-S", "-a", "android.intent.action.VIEW", "-d", f"'{clean_url}'", "com.google.android.youtube"], serial)
        self.log(f"[{serial[-4:]}] \u25b6 Iniciando sesion de 📱T Shorts...", "info")
        time.sleep(10)
        if self._is_cancelled(serial, token): return
        
        # Click para asegurar foco en el primer short
        self.log(f"[{serial[-4:]}] 🔍 Escaneando pantalla inicial para abrir Short...", "info")
        self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_start.xml"], serial)
        out_start_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_start.xml"], serial)
        out_start = out_start_t[0] if isinstance(out_start_t, tuple) else out_start_t
        
        if out_start and "<node" in out_start:
            out_lower = out_start.lower()
            if "me gusta" in out_lower or "comentarios" in out_lower:
                self.log(f"[{serial[-4:]}] 🎬 Video detectado en pantalla completa. Autoplay activo.", "info")
            else:
                
                
                # Enfoque Geométrico: El usuario indica que la grilla tiene 3 columnas y empieza desde la mitad hacia abajo.
                # Queremos tocar la columna del MEDIO (X = 50%), de la fondo (Y = 82%).
                screen_match = re.search(r'bounds="\[0,0\]\[(\d+),(\d+)\]"', out_start)
                if screen_match:
                    w = int(screen_match.group(1))
                    h = int(screen_match.group(2))
                    cx = w // 2
                    cy = int(h * 0.82)
                    self.log(f"[{serial[-4:]}] 📏 Resolucion detectada: {w}x{h}. Tocando cuadro central en ({cx}, {cy}).", "info")
                else:
                    # Coordenadas por defecto si falla la lectura de resolucion
                    cx, cy = 360, 1000
                    self.log(f"[{serial[-4:]}] 📏 Resolucion no detectada. Usando toque central por defecto en ({cx}, {cy}).", "warn")
                
                self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                time.sleep(4)
        
        short_count = 1
        while not self._is_cancelled(serial, token):
            watch_time = random.randint(t_min, t_max)
            self.log(f"[{serial[-4:]}] \U0001f4fa Viendo Short #{short_count} por {watch_time}s...", "info")
            
            # Wait watch time (interruptible)
            for _ in range(watch_time):
                if self._is_cancelled(serial, token): return
                time.sleep(1)
                
            if self._is_cancelled(serial, token): return
            
            # ---------------------------
            # LOGICA LEGO: SMART SCANNER
            # ---------------------------
            if do_like or do_save or do_comment or do_share:
                
                try:
                    # Desincronizacion Natural
                    stagger = random.uniform(1.0, 8.0)
                    time.sleep(stagger)
                    if self._is_cancelled(serial, token): return
                    
                    self.log(f"[{serial[-4:]}] \U0001f50d Tomando radiografia de interfaz...", "info")
                    self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_shorts1.xml"], serial)
                    out1_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_shorts1.xml"], serial)
                    out1 = out1_t[0] if isinstance(out1_t, tuple) else out1_t

                    
                    if self._is_cancelled(serial, token): return
                    if out1 and "<node" in out1:
                        import xml.etree.ElementTree as ET
                        xml_data = out1.encode("utf-8", "ignore")
                        root = ET.fromstring(xml_data)
                        
                        btn_like, btn_save, btn_comment, btn_share = None, None, None, None
                        is_ad = False
                        
                        for node in root.iter("node"):
                            t = (node.get("text") or "").lower()
                            desc = (node.get("content-desc") or "").lower()
                            bounds = node.get("bounds", "")
                            
                            if "patrocinado" in t or "anuncio" in t or "visitar" in t or "instalar" in t:
                                is_ad = True
                                
                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                            if not m: continue
                            cx, cy = (int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2
                            
                            # Logica de deteccion
                            if ("me gusta" in desc or "like" in desc) and ("no me gusta" not in desc and "dislike" not in desc):
                                btn_like = "ALREAD📱_LIKED" if ("quitar" in desc or "remove" in desc) else (cx, cy)
                            if "guardar" in desc or "save" in desc:
                                btn_save = (cx, cy)
                            elif "guardado" in desc or "saved" in desc:
                                btn_save = "ALREAD📱_SAVED"
                            if "comentarios" in desc or "comentar" in desc:
                                btn_comment = "DISABLED" if ("inhabilit" in desc or "desactiv" in desc) else (cx, cy)
                            if "compartir" in desc or "share" in desc:
                                btn_share = (cx, cy)
                                
                        if is_ad:
                            self.log(f"[{serial[-4:]}] \U0001f6a8 Publicidad detectada. Saltando interacciones...", "warn")
                        else:
                            # 2.1 LIKE
                            if do_like and btn_like == "ALREADY_LIKED":
                                self.log(f"[{serial[-4:]}] \U0001f44d El video ya tiene Like.", "info")
                            elif do_like and btn_like:
                                self.log(f"[{serial[-4:]}] \u2764\ufe0f Dando Like en {btn_like}...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_like[0]} {btn_like[1]}"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                                
                            # 2.2 GUARDAR
                            if do_save and btn_save == "ALREADY_SAVED":
                                self.log(f"[{serial[-4:]}] \U0001f4be El video ya estaba guardado.", "info")
                            elif do_save and btn_save:
                                self.log(f"[{serial[-4:]}] \U0001f4be Guardando en listas {btn_save}...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_save[0]} {btn_save[1]}"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                                
                            # 2.3 COMENTAR
                            if do_comment and btn_comment == "DISABLED":
                                self.log(f"[{serial[-4:]}] \U0001f4ac Los comentarios estan inhabilitados.", "warn")
                            elif do_comment and btn_comment:
                                self.log(f"[{serial[-4:]}] \U0001f4ac Abriendo panel de comentarios...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_comment[0]} {btn_comment[1]}"], serial)
                                time.sleep(random.uniform(4.0, 6.0))
                                if self._is_cancelled(serial, token): return
                                
                                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_shorts2.xml"], serial)
                                out2_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_shorts2.xml"], serial)
                                out2 = out2_t[0] if isinstance(out2_t, tuple) else out2_t
                                
                                textbox, btn_close_panel = None, None
                                if out2 and "<node" in out2:
                                    root2 = ET.fromstring(out2.encode("utf-8", "ignore"))
                                    for node in root2.iter("node"):
                                        t = (node.get("text") or "").lower()
                                        d = (node.get("content-desc") or "").lower()
                                        if ("agrega" in t or "comenta" in t) and "inhabilit" not in t:
                                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                            if m: textbox = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                        if "cerrar" in d or "close" in d:
                                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                            if m: btn_close_panel = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                            
                                if textbox:
                                    self.log(f"[{serial[-4:]}] \u2328\ufe0f Abriendo teclado de comentarios...", "info")
                                    self.adb.run_command(["shell", f"input tap {textbox[0]} {textbox[1]}"], serial)
                                    time.sleep(2)
                                    if self._is_cancelled(serial, token): return
                                    
                                    # LIBRERIA DINAMICA
                                    comments_file = os.path.join(os.path.dirname(__file__), "..", "comentarios.txt")
                                    comentarios_default = ["Que buen contenido", "Sigue asi hermano", "Excelente video", "Aca apoyando", "Esto merece hacerse viral"]
                                    comment_to_type = random.choice(comentarios_default)
                                    try:
                                        if os.path.exists(comments_file):
                                            with open(comments_file, "r", encoding="utf-8") as f:
                                                lines = [l.strip() for l in f.readlines() if l.strip()]
                                                if lines: comment_to_type = random.choice(lines)
                                        else:
                                            with open(comments_file, "w", encoding="utf-8") as f:
                                                f.write("\n".join(comentarios_default))
                                    except: pass
                                    
                                    adb_text = comment_to_type.replace(" ", "%s").replace('"', '').replace("'", "")
                                    self.log(f"[{serial[-4:]}] \u270d\ufe0f Escribiendo comentario: '{comment_to_type}'", "info")
                                    self.adb.run_command(["shell", f"input text {adb_text}"], serial)
                                    time.sleep(random.uniform(3.0, 4.0))
                                    if self._is_cancelled(serial, token): return
                                    
                                    # Dump 3 para Enviar
                                    self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_shorts3.xml"], serial)
                                    out3_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_shorts3.xml"], serial)
                                    out3 = out3_t[0] if isinstance(out3_t, tuple) else out3_t
                                    
                                    btn_send = None
                                    if out3 and "<node" in out3:
                                        root3 = ET.fromstring(out3.encode("utf-8", "ignore"))
                                        for node in root3.iter("node"):
                                            d = (node.get("content-desc") or "").lower()
                                            t = (node.get("text") or "").lower()
                                            if "enviar" in d or "send" in d or "publicar" in d or "enviar" in t:
                                                m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                                if m: btn_send = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                                
                                    if btn_send:
                                        self.log(f"[{serial[-4:]}] \U0001f680 Enviando comentario...", "info")
                                        self.adb.run_command(["shell", f"input tap {btn_send[0]} {btn_send[1]}"], serial)
                                    else:
                                        self.adb.run_command(["shell", f"input tap {textbox[0]+300} {textbox[1]}"], serial)
                                        
                                    time.sleep(random.uniform(2.5, 4.0))
                                    if self._is_cancelled(serial, token): return
                                    
                                    self.log(f"[{serial[-4:]}] \U0001f519 Cerrando teclado...", "info")
                                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                                    time.sleep(random.uniform(2.0, 3.5))
                                    if self._is_cancelled(serial, token): return
                                    
                                if btn_close_panel:
                                    self.log(f"[{serial[-4:]}] \U0001f519 Cerrando panel (X)...", "info")
                                    self.adb.run_command(["shell", f"input tap {btn_close_panel[0]} {btn_close_panel[1]}"], serial)
                                else:
                                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                                
                            # 2.4 Compartir y Copiar
                            if do_share and isinstance(btn_share, tuple):
                                self.log(f"[{serial[-4:]}] \U0001f517 Abriendo panel de Compartir...", "info")
                                self.adb.run_command(["shell", f"input tap {btn_share[0]} {btn_share[1]}"], serial)
                                time.sleep(random.uniform(4.0, 5.5))
                                if self._is_cancelled(serial, token): return
                                
                                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/omni_share.xml"], serial)
                                out_s_t = self.adb.run_command(["shell", "cat", "/sdcard/omni_share.xml"], serial)
                                out_s = out_s_t[0] if isinstance(out_s_t, tuple) else out_s_t
                                
                                btn_copy = None
                                if out_s and "<node" in out_s:
                                    root_s = ET.fromstring(out_s.encode("utf-8", "ignore"))
                                    for node in root_s.iter("node"):
                                        t = (node.get("text") or "").lower()
                                        d = (node.get("content-desc") or "").lower()
                                        if "copiar" in t or "copy" in t or "copiar" in d or "copy" in d:
                                            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
                                            if m: btn_copy = ((int(m.group(1))+int(m.group(3)))//2, (int(m.group(2))+int(m.group(4)))//2)
                                            
                                if btn_copy:
                                    self.log(f"[{serial[-4:]}] \U0001f4cb Copiando vinculo...", "info")
                                    self.adb.run_command(["shell", f"input tap {btn_copy[0]} {btn_copy[1]}"], serial)
                                else:
                                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                                time.sleep(random.uniform(3.0, 4.5))
                                if self._is_cancelled(serial, token): return
                except Exception as e:
                    self.log(f"[{serial[-4:]}] \u26a0\ufe0f Error en ciclo avanzado: {e}", "error")
                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                    self.adb.run_command(["shell", "input keyevent 4"], serial)
                    
            if self._is_cancelled(serial, token): return
                
            self.log(f"[{serial[-4:]}] \u2705 Interaccion completada. \U0001f446 Deslizando al siguiente...", "info")
            self.adb.run_command(["shell", "input", "swipe", "240", "800", "240", "150", "150"], serial)
            short_count += 1
            time.sleep(4)


    def inject_ytshorts_batch(self, devices, urls, t_min, t_max, do_like, do_save, do_comment, do_share, drip_mode="rápido"):
        if not urls:
            self.log("⚠️ No hay URLs de 📱T Shorts", "warn")
            return
        self.log(f"🚀 Inyectando 📱T Shorts en {len(devices)} dispositivos... (Swipe: {t_min}s-{t_max}s | Modo: {drip_mode})", "info")
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
            threading.Thread(target=self.inject_ytshorts, args=(serial, url, t_min, t_max, do_like, do_save, do_comment, do_share, delay), daemon=True).start()


