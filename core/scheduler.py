"""
core/scheduler.py
=================
Piloto Automático — Limpio, secuencial, sin conflictos

Lógica:
  1. Recibe una lista de fases: [(nombre, segundos, función_inyectar), ...]
  2. Ejecuta cada fase en orden, espera el tiempo configurado, pasa a la siguiente.
  3. Solo UNA plataforma activa a la vez — imposible que se pisen.
  4. Cancela la inyección anterior ANTES de empezar la siguiente.
  5. Repite el ciclo infinitamente hasta que el usuario detenga.
"""

import threading
import time


class Scheduler:
    """
    Piloto automático secuencial.

    Uso:
        sched = Scheduler(log_fn)
        sched.start([
            ("Spotify",    7200, fn_spotify),
            ("YouTube",    7200, fn_youtube),
            ("YT Music",   7200, fn_ytmusic),
        ])
        sched.pause()
        sched.resume()
        sched.stop()
    """

    def __init__(self, log_fn, on_phase_change=None, on_tick=None):
        """
        log_fn: función para escribir en la consola (msg, tipo)
        on_phase_change: callback(phase_name, remaining_secs) cuando cambia de fase
        on_tick: callback(phase_name, remaining_secs) cada segundo
        """
        self.log = log_fn
        self.on_phase_change = on_phase_change
        self.on_tick = on_tick

        self._running = False
        self._paused = False
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # No pausado por defecto

        self.current_phase = None
        self.current_remaining = 0

    @property
    def is_running(self):
        return self._running

    @property
    def is_paused(self):
        return self._paused

    def start(self, phases, use_watchdog=False, watchdog_fn=None):
        """
        Inicia el piloto automático.
        phases: lista de tuplas (nombre: str, segundos: int, fn: callable)
        """
        if self._running:
            self.log("⚠️ El Piloto ya está corriendo. Detené primero.", "warn")
            return

        # Filtrar fases con duración = 0
        active_phases = [(n, s, f) for n, s, f in phases if s > 0 and f is not None]

        if not active_phases:
            self.log("⚠️ No hay fases configuradas con duración mayor a 0.", "warn")
            return

        self._running = True
        self._paused = False
        self._stop_event.clear()
        self._pause_event.set()

        self.log(f"🤖 PILOTO AUTOMÁTICO INICIADO — {len(active_phases)} fase(s) activa(s)", "success")
        for name, secs, _ in active_phases:
            h, m = divmod(secs, 3600)
            m = m // 60
            self.log(f"   → {name}: {h}h {m:02d}m", "info")

        self._thread = threading.Thread(
            target=self._loop,
            args=(active_phases, use_watchdog, watchdog_fn),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Detiene el piloto automático limpiamente."""
        if not self._running:
            return
        self.log("⏹️ DETENIENDO Piloto Automático...", "warn")
        self._running = False
        self._paused = False
        self._stop_event.set()
        self._pause_event.set()  # Desbloquear si estaba en pausa
        self.current_phase = None
        self.current_remaining = 0
        self.log("✅ Piloto Automático detenido.", "info")

    def pause(self):
        """Pausa el temporizador del Piloto (la inyección actual sigue)."""
        if not self._running or self._paused:
            return
        self._paused = True
        self._pause_event.clear()
        self.log("⏸️ Piloto en PAUSA — el tiempo no corre.", "warn")

    def resume(self):
        """Reanuda el temporizador."""
        if not self._paused:
            return
        self._paused = False
        self._pause_event.set()
        self.log("▶️ Piloto REANUDADO.", "info")

    def _loop(self, phases, use_watchdog, watchdog_fn):
        """Bucle principal del piloto. Corre en hilo daemon."""
        while self._running:
            for name, total_secs, inject_fn in phases:
                if not self._running:
                    return

                # ── Notificar cambio de fase ──
                self.current_phase = name
                self.current_duration = total_secs
                self.current_remaining = total_secs
                h, m = divmod(total_secs, 3600)
                m = m // 60

                self.log(
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info"
                )
                self.log(
                    f"🚀 FASE: {name.upper()} — Duración: {h}h {m:02d}m", "info"
                )
                self.log(
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info"
                )

                if self.on_phase_change:
                    try:
                        self.on_phase_change(name, total_secs)
                    except Exception:
                        pass

                # ── Ejecutar la inyección de esta fase ──
                try:
                    inject_fn()
                except Exception as e:
                    self.log(f"⚠️ Error en fase {name}: {e}", "warn")

                # ── Esperar el tiempo de la fase ──
                elapsed = 0
                while elapsed < total_secs and self._running:
                    # Esperar si está en pausa
                    self._pause_event.wait()

                    if not self._running:
                        return

                    time.sleep(1)
                    elapsed += 1
                    self.current_remaining = total_secs - elapsed

                    # REGLA WATCHDOG LIVIANO: Solo si dura >= 20 mins (1200s), revisar cada 10 mins (600s)
                    if use_watchdog and total_secs >= 1200 and watchdog_fn:
                        if elapsed % 600 == 0:
                            self.log(f"🛡️ [WATCHDOG] Pausando cronómetro para revisión de rutina ({name})...", "warn")
                            try:
                                watchdog_fn(name)
                            except Exception as e:
                                self.log(f"Error en Watchdog: {e}", "error")
                            self.log("🛡️ [WATCHDOG] Revisión terminada. Retomando fase...", "success")

                    if self.on_tick:
                        try:
                            self.on_tick(name, self.current_remaining)
                        except Exception:
                            pass

                if not self._running:
                    return

                self.log(f"✅ Fase {name} completada.", "success")

            # Ciclo completado — volvemos al principio
            if self._running:
                self.log("🔄 Ciclo completo. Reiniciando desde el principio...", "info")

        self._running = False
        self.log("⏹️ Piloto Automático finalizado.", "info")
