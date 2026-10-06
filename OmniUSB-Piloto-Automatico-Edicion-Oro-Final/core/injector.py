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
        pkgs = ["com.android.chrome", "com.spotify.music", "com.google.android.youtube", "com.google.android.apps.youtube.music"]
        for p in pkgs:
            if p != keep_pkg:
                self.adb.run_command(["shell", "am", "force-stop", p], serial)

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
        """Busca el botón Play/Shuffle en Spotify via UIAutomator XML."""
        for _ in range(3):
            try:
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_omni.xml"], serial)
                out_t = self.adb.run_command(["shell", "cat", "/sdcard/dump_omni.xml"], serial)
                out = out_t[0] if isinstance(out_t, tuple) else out_t
                if not out:
                    time.sleep(2)
                    continue

                out = re.sub(r"<\⏳xml.*⏳\⏳>", "", out)
                root = ET.fromstring(out.encode("utf-8", "ignore"))

                btn_agregar = None
                btn_play = None

                for node in root.iter("node"):
                    desc = (node.get("content-desc") or "").lower()
                    text_n = (node.get("text") or "").lower()
                    bounds = node.get("bounds", "")
                    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if not m:
                        continue
                    x1, y1, x2, y2 = map(int, m.groups())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    # Saltar anuncios si los hay
                    if any(k in desc or k in text_n for k in ["saltar", "skip", "omitir"]):
                        self.log(f"[{serial[-4:]}] 📢 Anuncio detectado — Saltando...", "warn")
                        self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                        time.sleep(2)

                    if "agregar" in desc and "playlist" in desc:
                        btn_agregar = (cx, cy)

                    is_play = lambda s: any(k in s for k in [
                        "reproducir playlist", "play playlist", "aleatorio", "shuffle", "mezclar"
                    ]) or s in ["reproducir", "play", "shuffle"]

                    if (is_play(desc) or is_play(text_n)) and "agregar" not in desc:
                        btn_play = (cx, cy)

                if btn_agregar:
                    self.log(f"[{serial[-4:]}] 💚 Guardando playlist en biblioteca...", "info")
                    self.adb.run_command(["shell", "input", "tap", str(btn_agregar[0]), str(btn_agregar[1])], serial)
                    time.sleep(2)

                if btn_play:
                    self.log(f"[{serial[-4:]}] ▶️ Botón Play encontrado — Presionando...", "info")
                    self.adb.run_command(["shell", "input", "tap", str(btn_play[0]), str(btn_play[1])], serial)
                    return True
                elif btn_agregar:
                    # Fallback geométrico: Play está a ~85% del ancho, misma altura que Agregar
                    sz_t = self.adb.run_command(["shell", "wm", "size"], serial)
                    sz = sz_t[0] if isinstance(sz_t, tuple) else sz_t
                    sz_m = re.search(r"(\d+)x(\d+)", str(sz))
                    if sz_m:
                        geo_x = int(int(sz_m.group(1)) * 0.85)
                        geo_y = btn_agregar[1]
                        self.log(f"[{serial[-4:]}] 🎯 Botón Play invisible — Toque geométrico ({geo_x},{geo_y})", "info")
                        self.adb.run_command(["shell", "input", "tap", str(geo_x), str(geo_y)], serial)
                        return True

            except Exception as e:
                self.log(f"[{serial[-4:]}] ⚠️ Error escaneando XML: {e}", "warn")
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
                self.log(f"[{serial[-4:]}] ⏳ Verificando si cambió a Pausa...", "info")
                time.sleep(10)  # Esperar que reaccione
                
                self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/dump_omni.xml"], serial)
                out_t = self.adb.run_command(["shell", "cat", "/sdcard/dump_omni.xml"], serial)
                out_xml = out_t[0] if isinstance(out_t, tuple) else out_t
                out_lower = out_xml.lower() if out_xml else ""
                
                if "pausa" in out_lower or "pause" in out_lower:
                    self.log(f"[{serial[-4:]}] ✅ ¡Confirmado! El nuevo link se activó correctamente.", "success")
                    pressed = True
                    break
                else:
                    self.log(f"[{serial[-4:]}] ⚠️ Falsa alarma o toque fallido. Reintentando...", "warn")
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
