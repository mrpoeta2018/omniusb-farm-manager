"""
core/monitor.py
===============
Monitor de Salud de Dispositivos — Limpio y Aislado

Corre en hilo de fondo.
Cada 60s verifica si cada celular activo tiene tun0.
Si cae 2 veces seguidas → notificación.
Si cae 3 veces → intenta reconectar automáticamente.
"""

import threading
import time


class DeviceMonitor:
    """
    Monitor de salud para dispositivos activos.
    Notifica vía callbacks sin bloquear la UI.
    """

    def __init__(self, adb_manager, log_fn, on_device_alert=None):
        """
        adb_manager: instancia de ADBManager
        log_fn: función log(msg, tipo)
        on_device_alert: callback(serial, status) donde status = "ok"|"warning"|"dead"
        """
        self.adb = adb_manager
        self.log = log_fn
        self.on_device_alert = on_device_alert

        self._running = False
        self._thread = None
        self._lock = threading.Lock()

        # Estado por dispositivo
        self._fail_counts = {}     # serial -> int (fallos consecutivos)
        self._device_status = {}   # serial -> "ok"|"warning"|"dead"|"inactive"

    def start(self, get_active_devices_fn):
        """
        Inicia el monitor.
        get_active_devices_fn: función callable que retorna lista de dicts activos [{serial, ...}]
        """
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop,
            args=(get_active_devices_fn,),
            daemon=True
        )
        self._thread.start()
        self.log("🛡️ Monitor de salud iniciado (chequeo cada 60s)", "info")

    def stop(self):
        self._running = False
        self.log("🛡️ Monitor de salud detenido.", "info")

    def get_status(self, serial):
        """Retorna el estado actual de un dispositivo."""
        return self._device_status.get(serial, "inactive")

    def get_all_status(self):
        """Retorna dict {serial: status}."""
        return dict(self._device_status)

    def reset_device(self, serial):
        """Resetea el contador de fallos de un dispositivo (tras reconexión exitosa)."""
        with self._lock:
            self._fail_counts[serial] = 0
            self._device_status[serial] = "ok"

    def _check_tunnel(self, serial):
        """
        Verifica salida a internet.
        A petición del usuario, si el dispositivo tiene un túnel VPN activo (Gnirehtet), 
        se asume que tiene internet para evitar falsos positivos que interrumpan la reproducción.
        """
        try:
            # 1. Verificamos si tiene Gnirehtet (VPN) encendido
            out, _, _ = self.adb.run_command(["shell", "ip", "addr", "show"], serial)
            has_tun = "tun" in out.lower() or "vpn" in out.lower() or "10.0.2." in out
            if has_tun:
                return True # Túnel encendido = Asumimos Internet OK (Sin falsos positivos)
                
            # 2. Si no tiene túnel (WiFi Nativo), probamos un ping básico
            _, _, ping_code = self.adb.run_command(["shell", "ping", "-c", "1", "-W", "3", "8.8.8.8"], serial)
            if ping_code == 0:
                return True
                
            return False
        except Exception:
            return False

    def _loop(self, get_active_devices_fn):
        """Bucle principal del monitor."""
        # Esperar a que los túneles se establezcan antes del primer chequeo
        time.sleep(60)

        while self._running:
            try:
                devices = get_active_devices_fn()
            except Exception:
                devices = []

            for dev in devices:
                if not self._running:
                    break

                serial = dev.get("serial", "")
                if not serial:
                    continue

                # Pausa entre chequeos para no saturar el cable USB
                time.sleep(2)

                tunnel_ok = self._check_tunnel(serial)

                with self._lock:
                    if tunnel_ok:
                        # ✅ Túnel sano — resetear contador
                        old_fails = self._fail_counts.get(serial, 0)
                        if old_fails > 0:
                            self.log(
                                f"[{serial[-4:]}] ✅ Túnel restaurado — contador reseteado",
                                "info"
                            )
                        self._fail_counts[serial] = 0
                        old_status = self._device_status.get(serial)
                        self._device_status[serial] = "ok"
                        if old_status and old_status != "ok":
                            self._notify(serial, "ok")

                    else:
                        # ❌ Túnel caído — incrementar contador
                        fails = self._fail_counts.get(serial, 0) + 1
                        self._fail_counts[serial] = fails

                        if fails == 1:
                            # Primer fallo: warning, aún no alarma
                            self._device_status[serial] = "warning"
                            self.log(
                                f"[{serial[-4:]}] 🟡 Aviso: Internet inestable. Reintentando confirmación en 15s...",
                                "warn"
                            )
                            self._notify(serial, "warning")
                            
                            # Hacemos una pausa corta de 15s y volvemos a intentar inmediatamente
                            time.sleep(15)
                            segundo_intento = self._check_tunnel(serial)
                            if segundo_intento:
                                self._fail_counts[serial] = 0
                                self._device_status[serial] = "ok"
                                self._notify(serial, "ok")
                                self.log(f"[{serial[-4:]}] ✅ Internet recuperado en el segundo intento.", "info")
                            else:
                                self._fail_counts[serial] = 2
                                self._device_status[serial] = "dead"
                                self.log(
                                    f"[{serial[-4:]}] 🔴 DISPOSITIVO CAÍDO — Sin internet confirmado (2 fallos)",
                                    "error"
                                )
                                self._notify(serial, "dead")

                        elif fails >= 2:
                            # Ya fue notificado como caído, no spamear
                            self._device_status[serial] = "dead"

            # Esperar hasta el próximo ciclo (15 minutos = 900 segundos) para no saturar
            for _ in range(900):
                if not self._running:
                    return
                time.sleep(1)

    def _notify(self, serial, status):
        """Llama al callback de alerta si está configurado."""
        if self.on_device_alert:
            try:
                self.on_device_alert(serial, status)
            except Exception:
                pass
