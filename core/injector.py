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

    @staticmethod
    def _clean_text_for_adb(text):
        """
        Sanitiza texto para evitar crasheos de Java NullPointerException en 'adb shell input text'.
        Convierte acentos a caracteres ASCII estándar, limpia comillas y comillas tipográficas,
        y formatea los espacios como '%s'.
        """
        if not text:
            return ""
        import unicodedata
        replacements = {
            '’': "'", '‘': "'", '`': "'",
            '“': '"', '”': '"',
            '¿': '', '¡': '',
            '—': '-', '–': '-'
        }
        for orig, rep in replacements.items():
            text = text.replace(orig, rep)
        
        # Descomponer caracteres con acentos (á -> a, é -> e, ñ -> n)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        
        # Quitar comillas simples y dobles para no romper argumentos de shell
        text = text.replace('"', '').replace("'", "")
        
        # Mantener solo caracteres seguros imprimibles
        text = re.sub(r'[^a-zA-Z0-9\s.,!?:_+\-*/()]', '', text)
        
        return text.strip().replace(" ", "%s")

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
        """Busca el botón Play/Shuffle y gestiona Me Gusta en Spotify via UIAutomator XML."""
        import re
        import time
        self.log(f"[{serial[-4:]}] 🔍 Escaneando la estructura visual de Spotify...", "info")
        out_sz, _, _ = self.adb.run_command(["shell", "wm", "size"], serial)
        w, h = 480, 854
        sizes = re.findall(r'(\d+)x(\d+)', str(out_sz))
        if sizes:
            w, h = int(sizes[-1][0]), int(sizes[-1][1])

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
                btn_play_coords = None

                for node in root.iter("node"):
                    desc = (node.get("content-desc") or "").lower()
                    text_n = (node.get("text") or "").lower()
                    cls = (node.get("class") or "").lower()
                    selected = (node.get("selected") or "").lower() == "true"
                    checked = (node.get("checked") or "").lower() == "true"
                    bounds = node.get("bounds", "")
                    
                    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if not m: continue
                    x1, y1, x2, y2 = map(int, m.groups())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    # 1. Saltar anuncios si aparecen
                    if any(k in desc or k in text_n for k in ["saltar", "skip", "omitir"]):
                        self.log(f"[{serial[-4:]}] 🚧 Anuncio detectado 🚧 Saltando...", "warn")
                        self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                        time.sleep(2)
                        continue

                    # Solo elementos en el tercio medio de la pantalla (área de cabecera de playlist)
                    if not (int(h * 0.25) <= cy <= int(h * 0.75)):
                        continue

                    # 2. Detectar Botón Play / Aleatorio directo si está identificado en XML
                    if cx > int(w * 0.60):
                        if any(p in desc for p in ["reproducir", "play", "aleatorio", "shuffle"]) or any(p in text_n for p in ["reproducir", "play", "aleatorio", "shuffle"]):
                            btn_play_coords = (cx, cy)
                            anchor_y = cy

                    # 3. Detectar Botón Me Gusta / Biblioteca (siempre a la izquierda de la fila)
                    if cx < int(w * 0.60):
                        if any(w in desc for w in ['veces', 'minuto', 'cancion', 'seguidor', 'oyente', 'plays']):
                            continue

                        is_like_btn = any(w in desc for w in ['biblioteca', 'library', 'me gusta', 'like', 'favorit', 'agrega', 'añad', 'anad', 'guard', 'add', 'save'])
                        
                        if is_like_btn and 'textview' not in cls:
                            anchor_y = cy
                            # Detección exhaustiva de si YA está guardado / Me Gusta
                            ya_guardado = (
                                selected or
                                checked or
                                any(w in desc for w in [
                                    'añadido', 'anadido', 'agregado', 'guardado', 'added', 'saved',
                                    'en tu biblioteca', 'en la biblioteca', 'in your library', 'in library',
                                    'quitar', 'quit', 'elimin', 'remove', 'te gusta', 'liked'
                                ])
                            )
                            if ya_guardado:
                                self.log(f"[{serial[-4:]}] 🤍 Playlist YA tiene Me Gusta/Guardada ({desc[:28]}). NO se toca para evitar abrir ventanas.", "info")
                                btn_agregar_x = None
                            else:
                                self.log(f"[{serial[-4:]}] 💚 No estaba guardada ({desc[:28]}). Dando Me Gusta...", "success")
                                btn_agregar_x = cx

                if anchor_y:
                    self.log(f"[{serial[-4:]}] ⚓ Ancla localizada en Y={anchor_y}.", "success")
                    if btn_agregar_x:
                        self.adb.run_command(["shell", "input", "tap", str(btn_agregar_x), str(anchor_y)], serial)
                        time.sleep(1.5)
                else:
                    self.log(f"[{serial[-4:]}] ⚠️ Ancla no encontrada. Asumiendo altura estándar.", "warn")
                    anchor_y = int(h * 0.6)

                if btn_play_coords:
                    calc_x, calc_y = btn_play_coords
                    self.log(f"[{serial[-4:]}] 🎯 Tocando Botón Play detectado en X:{calc_x}, Y:{calc_y}...", "info")
                    self.adb.run_command(["shell", "input", "tap", str(calc_x), str(calc_y)], serial)
                else:
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
                                    
                                    adb_text = self._clean_text_for_adb(comment_to_type)
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

    # ─────────────────────────────────────────
    # INYECCIÓN STARVIOS (LIVE STREAMS WEB)
    # ─────────────────────────────────────────

    def inject_starvios(self, serial, url, do_chat=True, chat_interval=5.0, custom_comments=None, comment_mode="gaming", drip_delay=0, keepalive_mins=60):
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        self.log(f"[{serial[-4:]}] 📺 Iniciando Starvios -> {url[:50]}...", "info")

        # Asegurar pantalla encendida
        self.adb.run_command(["shell", "input", "keyevent", "224"], serial)
        self.adb.run_command(["shell", "input", "keyevent", "82"], serial)
        time.sleep(1)

        if self._is_cancelled(serial, token): return

        # Abrir Chrome con la transmisión de Starvios
        safe_url = f"'{url.strip()}'"
        self.adb.run_command(
            ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "-n", "com.android.chrome/com.google.android.apps.chrome.Main"],
            serial
        )

        self.log(f"[{serial[-4:]}] ⏳ Esperando 8s a que cargue Starvios...", "info")
        time.sleep(8)

        if self._is_cancelled(serial, token): return

        # Calcular coordenadas dinámicas de pantalla para chat
        w, h = 480, 854
        try:
            wm_out = self.adb.run_command(["shell", "wm", "size"], serial)
            m = re.search(r"(\d+)x(\d+)", wm_out or "")
            if m:
                w, h = int(m.group(1)), int(m.group(2))
        except:
            pass

        chat_x = int(w * 0.42)
        chat_y = int(h * 0.938)

        from core.comments_bank import get_comment_pool
        import random

        def send_starvios_comment():
            if self._is_cancelled(serial, token): return

            # 1. Tap dinámico en la caja de chat
            t_x = chat_x + random.randint(-6, 6)
            t_y = chat_y + random.randint(-3, 3)
            self.adb.run_command(["shell", "input", "tap", str(t_x), str(t_y)], serial)
            time.sleep(1.2)

            if self._is_cancelled(serial, token): return

            # 2. Elegir comentario
            msg = ""
            if custom_comments:
                msg = random.choice(custom_comments)
            else:
                pool = get_comment_pool(comment_mode)
                msg = random.choice(pool)

            if msg.strip():
                safe_msg = self._clean_text_for_adb(msg)
                if safe_msg:
                    self.log(f"[{serial[-4:]}] 💬 Starvios comentando: {msg[:35]}...", "info")
                    self.adb.run_command(["shell", "input", "text", safe_msg], serial)
                    time.sleep(1.0)
                    # Enviar con Enter virtual
                    self.adb.run_command(["shell", "input", "keyevent", "66"], serial)
                    time.sleep(0.8)
                    # Cerrar teclado suavemente con Back para ver el video completo
                    self.adb.run_command(["shell", "input", "keyevent", "4"], serial)

        # Primer comentario tras 10 segundos
        if do_chat:
            time.sleep(10)
            send_starvios_comment()

        # Ciclo de retención / Keep-Alive y Comentarios periódicos
        wait_seconds = int(keepalive_mins * 60)
        chat_info = f" | Chat cada {chat_interval} min" if do_chat else ""
        self.log(f"[{serial[-4:]}] ⏳ Starvios en vivo: retención activa ({keepalive_mins} mins){chat_info}", "info")

        try:
            interval_sec = max(30, int(float(chat_interval) * 60))
        except:
            interval_sec = 300

        elapsed = 0
        last_comment_time = 0

        while elapsed < wait_seconds and not self._is_cancelled(serial, token):
            time.sleep(1)
            elapsed += 1

            # Toque de Keep-Alive cada 60s en la barra superior neutra
            if elapsed % 60 == 0:
                self.adb.run_command(["shell", "input", "tap", str(int(w * 0.5)), str(int(h * 0.12))], serial)

            # Enviar comentario periódico según intervalo
            if do_chat and (elapsed - last_comment_time) >= interval_sec:
                send_starvios_comment()
                last_comment_time = elapsed
                interval_sec = max(30, int(float(chat_interval) * 60) + random.randint(-15, 20))

    def inject_starvios_batch(self, devices, urls, do_chat=True, chat_interval=5.0, custom_comments=None, comment_mode="gaming", drip_mode="rápido", keepalive_mins=60):
        if not devices or not urls: return
        chat_status = f"con chat cada {chat_interval}m" if do_chat else "solo viewers"
        self.log(f"🌟 Inyectando Starvios en {len(devices)} dispositivo(s) ({chat_status})...", "info")
        for i, dev in enumerate(devices):
            import random
            url = random.choice(urls)
            delay = 0
            if drip_mode == "rápido" and i > 0: delay = i * random.randint(3, 8)
            elif drip_mode == "lento" and i > 0: delay = i * random.randint(15, 30)
            elif i > 0: delay = i * 1.5
            import threading
            threading.Thread(target=self.inject_starvios, args=(dev["serial"], url, do_chat, chat_interval, custom_comments, comment_mode, delay, keepalive_mins), daemon=True).start()

    def login_and_inject_starvios(self, serial, url=None, keepalive_mins=60):
        token = self._new_token(serial)
        self.log(f"[{serial[-4:]}] 🔑 Iniciando Verificación / Login Starvios...", "info")

        # 1. Despertar pantalla
        self.adb.run_command(["shell", "input", "keyevent", "224"], serial)
        self.adb.run_command(["shell", "input", "keyevent", "82"], serial)
        import time, os, re
        time.sleep(1)

        if self._is_cancelled(serial, token): return

        # Helper UI dump
        def _dump_root():
            self.adb.run_command(["shell", "uiautomator", "dump", "/sdcard/u_star.xml"], serial)
            import tempfile, xml.etree.ElementTree as ET
            tpath = os.path.join(tempfile.gettempdir(), f"u_star_{serial}.xml")
            self.adb.run_command(["pull", "/sdcard/u_star.xml", tpath], serial)
            if os.path.exists(tpath):
                try:
                    tree = ET.parse(tpath)
                    try:
                        os.remove(tpath)
                    except:
                        pass
                    return tree.getroot()
                except:
                    pass
            return None

        def _find_nodes(root, pattern, attr="text"):
            if root is None: return []
            res = []
            cp = re.compile(pattern, re.IGNORECASE)
            for n in root.iter():
                val = n.attrib.get(attr, "")
                if val and cp.search(val):
                    res.append(n)
            return res

        def _node_center(node):
            b = node.attrib.get("bounds", "")
            m = re.findall(r"\[(\d+),(\d+)\]", b)
            if len(m) == 2:
                x1, y1 = int(m[0][0]), int(m[0][1])
                x2, y2 = int(m[1][0]), int(m[1][1])
                if not (x1 == 0 and x2 == 0 and y1 == 0 and y2 == 0):
                    return ((x1 + x2) // 2, (y1 + y2) // 2)
            return None

        def _tap_c(center):
            if center:
                self.adb.run_command(["shell", "input", "tap", str(center[0]), str(center[1])], serial)
                return True
            return False

        def _is_logged():
            r = _dump_root()
            if r is None: return False
            logins = _find_nodes(r, r"^(Login|Log in|Acceder)$")
            if logins: return False
            profiles = _find_nodes(r, r"Profile|Perfil") or _find_nodes(r, r"Profile|Perfil", attr="content-desc")
            return bool(profiles)

        # 2. Verificar si ya está logueado
        self.log(f"[{serial[-4:]}] Comprobando sesión previa en Starvios...", "info")
        self.adb.run_command(
            ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "https://starvios.com/#", "-n", "com.android.chrome/com.google.android.apps.chrome.Main"],
            serial
        )
        time.sleep(6)

        if self._is_cancelled(serial, token): return

        if _is_logged():
            self.log(f"[{serial[-4:]}] ✅ Ya tiene sesión iniciada en Starvios.", "info")
        else:
            self.log(f"[{serial[-4:]}] Sin sesión activa. Procediendo con Login Google...", "info")
            self.adb.run_command(
                ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "https://starvios.com/auth", "-n", "com.android.chrome/com.google.android.apps.chrome.Main"],
                serial
            )
            time.sleep(5)

            if self._is_cancelled(serial, token): return

            # Tap Continue with Google
            r = _dump_root()
            g_btns = _find_nodes(r, r"Continue with Google") or _find_nodes(r, r"Continue with Google", attr="content-desc")
            if g_btns:
                _tap_c(_node_center(g_btns[0]))
            else:
                self.adb.run_command(["shell", "input", "tap", "240", "380"], serial)

            time.sleep(5)
            if self._is_cancelled(serial, token): return

            # Buscar cuentas Gmail
            r = _dump_root()
            gmail_accounts = []
            if r is not None:
                for node in r.iter():
                    txt = node.attrib.get("text", "")
                    if "@gmail.com" in txt.lower():
                        c = _node_center(node)
                        if c:
                            gmail_accounts.append((txt, c))

            if not gmail_accounts:
                gmail_accounts = [("cuenta_default", (240, 510))]

            self.log(f"[{serial[-4:]}] {len(gmail_accounts)} cuenta(s) Gmail detectadas.", "info")

            for acc_name, acc_pos in gmail_accounts:
                if self._is_cancelled(serial, token): return
                self.log(f"[{serial[-4:]}] Intentando login con {acc_name}...", "info")
                _tap_c(acc_pos)
                time.sleep(5)

                # Consentimiento Supabase si aparece
                r_c = _dump_root()
                if r_c is not None:
                    down_arrows = _find_nodes(r_c, r"Desplazar hacia abajo") or _find_nodes(r_c, r"Desplazar hacia abajo", attr="content-desc")
                    if down_arrows:
                        _tap_c(_node_center(down_arrows[0]))
                        time.sleep(2)
                        r_c = _dump_root()

                    cont_btns = _find_nodes(r_c, r"^Continuar$")
                    if cont_btns:
                        _tap_c(_node_center(cont_btns[0]))
                        time.sleep(5)

                # Fecha de nacimiento si aparece
                r_d = _dump_root()
                if r_d is not None:
                    missing = _find_nodes(r_d, r"missing some information|fecha de nacimiento")
                    if missing:
                        self.log(f"[{serial[-4:]}] Completando fecha de nacimiento...", "info")
                        dp = [n for n in r_d.iter() if "DatePicker" in n.attrib.get("class", "") or "dd/mm/aaaa" in n.attrib.get("text", "")]
                        if dp:
                            _tap_c(_node_center(dp[0]))
                        else:
                            self.adb.run_command(["shell", "input", "tap", "240", "595"], serial)
                        time.sleep(2)

                        r_pencil = _dump_root()
                        pencils = _find_nodes(r_pencil, r"mtrl_picker_header_toggle", attr="resource-id") or _find_nodes(r_pencil, r"modo de entrada de texto", attr="content-desc")
                        if pencils:
                            _tap_c(_node_center(pencils[0]))
                        else:
                            self.adb.run_command(["shell", "input", "tap", "400", "250"], serial)
                        time.sleep(2)

                        # Limpiar y escribir 01012000
                        self.adb.run_command(["shell", "for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do input keyevent 67; done"], serial)
                        time.sleep(1)
                        self.adb.run_command(["shell", "input", "text", "01012000"], serial)
                        time.sleep(1)
                        self.adb.run_command(["shell", "input", "keyevent", "4"], serial)
                        time.sleep(1)

                        r_ok = _dump_root()
                        oks = _find_nodes(r_ok, r"confirm_button", attr="resource-id") or _find_nodes(r_ok, r"Aceptar")
                        if oks:
                            _tap_c(_node_center(oks[0]))
                        else:
                            self.adb.run_command(["shell", "input", "tap", "385", "600"], serial)
                        time.sleep(2)

                        r_cont2 = _dump_root()
                        cont_final = _find_nodes(r_cont2, r"^Continuar$")
                        if cont_final:
                            _tap_c(_node_center(cont_final[0]))
                        else:
                            self.adb.run_command(["shell", "input", "tap", "240", "660"], serial)
                        time.sleep(5)

                if _is_logged():
                    self.log(f"[{serial[-4:]}] 🎉 Login/Registro exitoso con {acc_name}!", "success")
                    break
                else:
                    self.log(f"[{serial[-4:]}] No completó con {acc_name}, probando siguiente...", "warning")

        # 3. Inyectar transmisión si se proporcionó URL
        if url and url.strip():
            self.log(f"[{serial[-4:]}] 📺 Inyectando stream en vivo: {url[:50]}...", "info")
            safe_url = f"'{url.strip()}'"
            self.adb.run_command(
                ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", safe_url, "-n", "com.android.chrome/com.google.android.apps.chrome.Main"],
                serial
            )
            time.sleep(6)

            # Keep-Alive
            wait_seconds = int(keepalive_mins * 60)
            self.log(f"[{serial[-4:]}] ⏳ Starvios en vivo: retención activa ({keepalive_mins} mins)", "info")
            for i in range(wait_seconds):
                if self._is_cancelled(serial, token): return
                time.sleep(1)
                if i > 0 and i % 60 == 0:
                    self.adb.run_command(["shell", "input", "tap", "240", "100"], serial)

    def login_starvios_batch(self, devices, url=None, keepalive_mins=60):
        if not devices: return
        self.log(f"🔑 Iniciando Login/Registro Starvios en {len(devices)} dispositivo(s)...", "info")
        for dev in devices:
            import threading
            threading.Thread(target=self.login_and_inject_starvios, args=(dev["serial"], url, keepalive_mins), daemon=True).start()

    def inject_twitch(self, serial, url, do_text=False, do_emojis=False, chat_interval=5.0, custom_comments=None, drip_delay=0, comment_mode="gaming"):
        import time
        import re
        import random
        from core.comments_bank import get_comment_pool
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
        
        # Escanear UI para Seguir (1 sola vez al inicio)
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
        if not do_text:
            return
            
        self.log(f"[{serial[-4:]}] 💬 Motor de Chat de Twitch Activado (Modo: {comment_mode} | Intervalo: {chat_interval} min)", "info")
        
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
            
            # 1. Seleccionar texto limpio
            msg = ""
            if custom_comments:
                msg = random.choice(custom_comments)
            else:
                pool = get_comment_pool(comment_mode)
                msg = random.choice(pool)

            if msg.strip():
                self.log(f"[{serial[-4:]}] 💬 Twitch Escribiendo: {msg[:35]}...", "info")
                safe_msg = self._clean_text_for_adb(msg)
                if safe_msg:
                    self.adb.run_command(["shell", "input", "text", safe_msg], serial)
                    time.sleep(1.2)
                    self.adb.run_command(["shell", "input", "keyevent", "66"], serial) # ENTER
                
        time.sleep(5)
        send_comment()
        
        while not self._is_cancelled(serial, token):
            wait_time = int(float(chat_interval) * 60)
            for _ in range(wait_time):
                if self._is_cancelled(serial, token): return
                time.sleep(1)
            send_comment()

    def inject_twitch_batch(self, devices, urls, do_text=False, do_emojis=False, chat_interval=5.0, custom_comments=None, drip_mode="rápido", comment_mode="gaming"):
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
            threading.Thread(target=self.inject_twitch, args=(dev["serial"], url, do_text, do_emojis, chat_interval, custom_comments, delay, comment_mode), daemon=True).start()


    def inject_kick(self, serial, url, do_text=False, do_emojis=False, chat_interval=5, custom_comments=None, drip_delay=0, comment_mode="gaming"):
        self._mute_device(serial)
        import time, random, re
        from core.comments_bank import get_comment_pool
        if drip_delay > 0:
            time.sleep(drip_delay)

        token = self._new_token(serial)
        self.log(f"[{serial[-4:]}] 🟩 Iniciando Kick -> {url[:50]}...", "info")

        # Asegurar pantalla encendida
        self.adb.run_command(["shell", "input", "keyevent", "224"], serial)

        self.adb.run_command(["shell", "am", "force-stop", "com.kick.mobile"], serial)
        self._cleanup_apps(serial, keep_pkg="com.kick.mobile")
        time.sleep(2)

        if self._is_cancelled(serial, token): return

        self.adb.run_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"'{url.strip()}'", "com.kick.mobile"], serial)
        self.log(f"[{serial[-4:]}] 🟩 Esperando 8s a que cargue el canal de Kick...", "info")
        time.sleep(8)

        if self._is_cancelled(serial, token): return

        # Obtener resolución de pantalla dinámica universal
        w, h = 480, 854
        try:
            out_sz = self.adb.run_command(["shell", "wm", "size"], serial)[0]
            sizes = re.findall(r'(\d+)x(\d+)', str(out_sz))
            if sizes:
                w, h = int(sizes[-1][0]), int(sizes[-1][1])
        except Exception:
            pass

        # --- AUTO-FOLLOW Y ENTRADA AL STREAM EN VIVO ---
        dump_name = f"/sdcard/dump_kick_{serial[-4:]}.xml"
        self.adb.run_command(["shell", "uiautomator", "dump", dump_name], serial)
        xml_data = self.adb.run_command(["shell", "cat", dump_name], serial)[0]
        stream_entered = False
        if xml_data:
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(xml_data)
                # 1. Buscar Seguir
                for node in root.iter("node"):
                    t = (node.get("text") or "").lower()
                    d = (node.get("content-desc") or "").lower()
                    b = node.get("bounds", "")
                    if "seguir" in t or "follow" in t or "seguir" in d:
                        m = re.search(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', b)
                        if m:
                            x1, y1, x2, y2 = map(int, m.groups())
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            self.log(f"[{serial[-4:]}] 💚 ¡Botón Seguir detectado! Dándole a Seguir...", "success")
                            self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                            time.sleep(2)
                            break
                            
                # 2. Buscar tarjeta de Stream Actual
                for node in root.iter("node"):
                    t = (node.get("text") or "").lower()
                    d = (node.get("content-desc") or "").lower()
                    b = node.get("bounds", "")
                    if "stream actual" in t or "stream actual" in d or "streamear" in t:
                        m = re.search(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', b)
                        if m:
                            x1, y1, x2, y2 = map(int, m.groups())
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            self.log(f"[{serial[-4:]}] 🎬 Entrando al stream en vivo...", "info")
                            self.adb.run_command(["shell", "input", "tap", str(cx), str(cy)], serial)
                            stream_entered = True
                            break
            except Exception:
                pass

        if not stream_entered:
            # Fallback proporcional para entrar al stream
            self.adb.run_command(["shell", "input", "tap", str(int(w * 0.40)), str(int(h * 0.75))], serial)

        self.log(f"[{serial[-4:]}] 🟩 Esperando 5s a que el reproductor y chat sincronicen...", "info")
        time.sleep(5)
        
        # Cerrar posibles popups de recompensas tocando el botón Back o centro de video
        self.adb.run_command(["shell", "input", "tap", str(w // 2), str(int(h * 0.25))], serial)

        self.log(f"[{serial[-4:]}] ✅ KICK REPRODUCIENDO CORRECTAMENTE", "success")
        
        if not do_text and not do_emojis:
            return
            
        self.log(f"[{serial[-4:]}] 💬 Motor de Chat de Kick Activado (Modo: {comment_mode} | Intervalo: {chat_interval} min)", "info")
        
        chat_x = int(w * 0.40)
        chat_y = int(h * 0.85)
        emote_y = int(h * 0.761)
        emote_xs = [int(w * 0.08), int(w * 0.22), int(w * 0.35), int(w * 0.49), int(w * 0.63), int(w * 0.77), int(w * 0.91)]
        round_counter = [0]

        def send_comment():
            if self._is_cancelled(serial, token): return
            
            # Decidir si esta ronda envía texto o emote verde oficial
            send_type = "text"
            if do_text and do_emojis:
                send_type = "text" if (round_counter[0] % 2 == 0) else "emoji"
            elif do_emojis:
                send_type = "emoji"
                
            round_counter[0] += 1

            if send_type == "emoji":
                # 🟢 Enviar Emote Verde Oficial de Kick mediante toque directo instantáneo
                emo_base_x = random.choice(emote_xs)
                emo_x = emo_base_x + random.randint(-4, 4)
                emo_y = emote_y + random.randint(-3, 3)
                self.log(f"[{serial[-4:]}] 🟢 Kick Enviando Emote Verde Oficial (1-Tap)...", "info")
                self.adb.run_command(["shell", "input", "tap", str(emo_x), str(emo_y)], serial)
                return

            # 💬 Enviar Comentario de Texto
            # 1. Tap dinámico en la caja de chat (centro proporcional con micro-variación natural)
            t_x = chat_x + random.randint(-6, 6)
            t_y = chat_y + random.randint(-3, 3)
            self.adb.run_command(["shell", "input", "tap", str(t_x), str(t_y)], serial)
            time.sleep(1.5)
            
            if self._is_cancelled(serial, token): return
            
            # 2. Elegir comentario de texto limpio (sin emotes crudos)
            msg = ""
            if custom_comments:
                msg = random.choice(custom_comments)
            else:
                pool = get_comment_pool(comment_mode)
                msg = random.choice(pool)
                
            if msg.strip():
                self.log(f"[{serial[-4:]}] 💬 Kick Escribiendo: {msg[:35]}...", "info")
                safe_msg = self._clean_text_for_adb(msg)
                if safe_msg:
                    self.adb.run_command(["shell", "input", "text", safe_msg], serial)
                    time.sleep(1.2)
                    # Enviar vía Enter del teclado virtual (keyevent 66).
                    # Esto envía el mensaje y cierra el teclado limpiamente SIN tocar el engranaje de abajo.
                    self.adb.run_command(["shell", "input", "keyevent", "66"], serial)

        time.sleep(4)
        send_comment()
        
        while not self._is_cancelled(serial, token):
            try:
                wait_time = max(5, int(float(chat_interval) * 60))
            except Exception:
                wait_time = 300
            for _ in range(wait_time):
                if self._is_cancelled(serial, token): return
                time.sleep(1)
            send_comment()

    def inject_kick_batch(self, devices, urls, do_text=False, do_emojis=False, chat_interval=5, custom_comments=None, drip_mode="rápido", comment_mode="gaming"):
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
            threading.Thread(target=self.inject_kick, args=(dev["serial"], url, do_text, do_emojis, chat_interval, custom_comments, delay, comment_mode), daemon=True).start()


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
                                    
                                    adb_text = self._clean_text_for_adb(comment_to_type)
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
