"""
core/tunnel.py
==============
Gestor de Conexión y Túneles (Bloque 1) — Limpio

Solo se encarga de:
1. Recibir dispositivos y proxies.
2. Iniciar proxies locales (Node.js).
3. Conectar Gnirehtet a cada dispositivo.
4. Detener todo limpiamente.
"""

import time
import threading

class FarmTunnel:
    """
    Controlador centralizado para la granja de túneles.
    """

    def __init__(self, adb_manager, gnirehtet_runner, proxy_manager, log_fn):
        self.adb = adb_manager
        self.runner = gnirehtet_runner
        self.proxy_mgr = proxy_manager
        self.log = log_fn
        
        self.active_devices = []
        self.active_ports = {} # serial -> local_port
        
        self._running = False
        self._lock = threading.Lock()

    @property
    def running(self):
        return self._running

    def start_farm(self, devices, proxies, batch_size="Todos"):
        """
        Inicia la granja. Si batch_size no es 'Todos', inicia en lotes.
        Por simplicidad del rediseño, si es 'Todos', inicia todos a la vez.
        Si es un número, usaremos solo ese número máximo de dispositivos simultáneos.
        """
        if self._running:
            self.log("⚠️ El túnel ya está corriendo. Detenelo primero.", "warn")
            return

        if not devices:
            self.log("⚠️ No hay dispositivos para iniciar.", "warn")
            return

        with self._lock:
            self._running = True
            
        def _setup():
            # Determinar cuántos iniciar
            target_devices = devices
            if batch_size != "Todos":
                try:
                    limit = int(batch_size)
                    target_devices = devices[:limit]
                    self.log(f"📦 Iniciando lote de {limit} dispositivos...", "info")
                except ValueError:
                    pass

            self.active_devices = target_devices
            self.active_ports = {}

            # 1. Asignar Proxies
            used_ports = set()
            for i, dev in enumerate(self.active_devices):
                serial = dev['serial']
                
                if proxies:
                    proxy = proxies[i % len(proxies)]
                    # Buscar un puerto libre
                    port = 15000 + i
                    while port in used_ports:
                        port += 1
                    used_ports.add(port)
                    
                    # Formatear proxy por si viene como ip:port:user:pass
                    parts = proxy.replace("@", ":").split(":")
                    formatted_p = proxy
                    if len(parts) == 4:
                        if "." in parts[0] and parts[1].isdigit():
                            formatted_p = f"{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                        else:
                            formatted_p = f"{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}"
                            
                    self.log(f"[{serial[-4:]}] Iniciando Proxy en puerto {port}...", "info")
                    self.proxy_mgr.start_proxy_node(port, formatted_p)
                    self.active_ports[serial] = port
                    
                    self.adb.set_global_proxy(serial, "10.0.2.2", port)
                else:
                    self.log(f"[{serial[-4:]}] Iniciando SIN PROXY (Internet de PC)...", "warn")
                    self.adb.clear_global_proxy(serial)
                    
                time.sleep(1) # Pequeña pausa para no saturar

            # 2. Iniciar Gnirehtet
            self.log("🚀 Levantando túneles Gnirehtet en los dispositivos...", "info")
            for dev in self.active_devices:
                serial = dev['serial']
                self.runner.start(serial)
                time.sleep(2)
                
            self.log("✅ ¡Túneles listos! Todos los dispositivos tienen internet.", "success")
            
        threading.Thread(target=_setup, daemon=True).start()

    def stop_farm(self):
        """Detiene todo: Gnirehtet, Proxies, y limpia los celulares."""
        if not self._running:
            return
            
        self.log("🛑 Deteniendo túneles y limpiando...", "warn")
        
        with self._lock:
            self._running = False
            
        def _cleanup():
            # 1. Detener Gnirehtet
            for dev in self.active_devices:
                serial = dev['serial']
                self.runner.stop(serial)
                self.adb.clear_global_proxy(serial)
                
            # Detener relay global por si acaso
            self.runner.kill_all_gnirehtet()
            
            # 2. Detener Proxies Locales
            for port in self.active_ports.values():
                self.proxy_mgr.stop_proxy_node(port)
                
            self.active_devices = []
            self.active_ports = {}
            
            self.log("✅ Granja detenida y celulares limpios.", "success")
            
        threading.Thread(target=_cleanup, daemon=True).start()

    def reconnect_device(self, serial):
        """Intenta reconectar un dispositivo caído."""
        if not self._running:
            return False, "La granja no está corriendo"
            
        if serial not in [d['serial'] for d in self.active_devices]:
            return False, "El dispositivo no es parte del lote activo"
            
        self.log(f"[{serial[-4:]}] 🔧 Intentando reparación...", "warn")
        
        # 1. Detener
        self.runner.stop(serial)
        time.sleep(2)
        
        # 2. Reimponer proxy si tenía
        port = self.active_ports.get(serial)
        if port:
            self.adb.set_global_proxy(serial, "10.0.2.2", port)
        else:
            self.adb.clear_global_proxy(serial)
            
        time.sleep(1)
        
        # 3. Reiniciar túnel
        self.runner.start(serial)
        
        return True, "Reconexión enviada"
