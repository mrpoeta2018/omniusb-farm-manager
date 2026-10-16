import subprocess
import os
import socket
import threading
import time


class ADBManager:
    # --- Convivencia con otras apps que traen su propio ADB (ej. Xiaowei) ---
    PRIMARY_PORT = 5037
    EXTRA_PORTS = (5038,)
    _OWNER_TTL = 20     # seg. de validez del mapa serial -> servidor
    _DUP_TTL = 120      # seg. que se recuerda a quien pertenece un celular listado en ambos

    def __init__(self, adb_path="platform-tools\\adb.exe"):
        if not os.path.isabs(adb_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            adb_path = os.path.join(base_dir, adb_path)
            
        self.adb_path = adb_path
        if not os.path.exists(self.adb_path):
            self.adb_path = "adb"

        try:
            self.primary_port = int(os.environ.get("ANDROID_ADB_SERVER_PORT") or self.PRIMARY_PORT)
        except ValueError:
            self.primary_port = self.PRIMARY_PORT
        self.extra_ports = [p for p in self.EXTRA_PORTS if p != self.primary_port]
        self._owner = {}
        self._entries = {}
        self._owner_ts = 0.0
        self._owner_lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._dup_cache = {}

    @staticmethod
    def _startupinfo():
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return si
        return None

    @staticmethod
    def _port_alive(port):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.4):
                return True
        except OSError:
            return False

    def _port_args(self, port):
        return [] if port == self.primary_port else ["-P", str(port)]

    def _list_port(self, port, timeout=12, tries=2):
        cmd = [self.adb_path] + self._port_args(port) + ["devices", "-l"]
        for _ in range(tries):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                   errors="ignore", startupinfo=self._startupinfo(), timeout=timeout)
                if r.returncode != 0:
                    continue
                entries = []
                for line in r.stdout.split('\n'):
                    line = line.strip()
                    if not line or line.startswith("List of devices") or line.startswith("*"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        entries.append({'serial': parts[0], 'state': parts[1], 'line': line})
                return entries
            except Exception:
                continue
        return []

    def _probe(self, port, serial):
        cmd = [self.adb_path] + self._port_args(port) + ["-s", serial, "shell", "echo", "ok"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                               errors="ignore", startupinfo=self._startupinfo(), timeout=4)
            return "ok" in r.stdout
        except Exception:
            return False

    def refresh_owners(self, max_age=None, wait=False):
        if max_age is None:
            max_age = self._OWNER_TTL
        if not self._refresh_lock.acquire(blocking=wait):
            return
        try:
            if max_age and (time.time() - self._owner_ts) < max_age:
                return
            ports = [self.primary_port] + [p for p in self.extra_ports if self._port_alive(p)]
            entries = {}
            found = {}
            for port in ports:
                entries[port] = self._list_port(port)
                for e in entries[port]:
                    if e['state'] == 'device':
                        found.setdefault(e['serial'], []).append(port)
            owner = {}
            now = time.time()
            for serial, plist in found.items():
                if len(plist) == 1:
                    owner[serial] = plist[0]
                    continue
                cached = self._dup_cache.get(serial)
                if cached and (now - cached[1]) < self._DUP_TTL and cached[0] in plist:
                    owner[serial] = cached[0]
                    continue
                chosen = next((p for p in plist if self._probe(p, serial)), plist[0])
                self._dup_cache[serial] = (chosen, now)
                owner[serial] = chosen
            with self._owner_lock:
                self._owner = owner
                self._entries = entries
                self._owner_ts = time.time()
        finally:
            self._refresh_lock.release()

    def server_port_for(self, serial):
        if not serial or not self.extra_ports:
            return self.primary_port
        with self._owner_lock:
            port = self._owner.get(serial)
        if port is None:
            self.refresh_owners()
            with self._owner_lock:
                port = self._owner.get(serial, self.primary_port)
        return port

    def kill_own_adb(self):
        """Cierra SOLO el ADB de OmniUSB. No toca el de Xiaowei."""
        try:
            self.run_command(["kill-server"], retries=1, timeout=6)
        except Exception:
            pass
        try:
            import psutil
            mine = os.path.normcase(os.path.abspath(self.adb_path))
            for proc in psutil.process_iter(['name']):
                try:
                    if (proc.info['name'] or '').lower() != 'adb.exe':
                        continue
                    if os.path.normcase(os.path.abspath(proc.exe())) == mine:
                        proc.kill()
                except Exception:
                    pass
        except Exception:
            pass

    def run_command(self, cmd_args, device_serial=None, retries=2, timeout=12, _rerouted=False):
        port = self.server_port_for(device_serial) if device_serial else self.primary_port
        base_cmd = [self.adb_path]
        if device_serial:
            base_cmd.extend(self._port_args(port))
            base_cmd.extend(["-s", device_serial])
        base_cmd.extend(cmd_args)
        
        last_err = ""
        for attempt in range(retries):
            try:
                startupinfo = self._startupinfo()
                result = subprocess.run(base_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", startupinfo=startupinfo, timeout=timeout)
                if result.returncode == 0:
                    return result.stdout.strip(), result.stderr.strip(), result.returncode
                
                last_err = result.stderr.strip()
                if "not found" in last_err or "offline" in last_err or "unauthorized" in last_err:
                    if device_serial and self.extra_ports and not _rerouted:
                        self.refresh_owners(max_age=5, wait=True)
                        if self.server_port_for(device_serial) != port:
                            return self.run_command(cmd_args, device_serial, retries, timeout, _rerouted=True)
                    return "", "DEVICE_OFFLINE", -2
            except subprocess.TimeoutExpired:
                last_err = "Timeout CMD"
            except Exception as e:
                last_err = str(e)
            
        return "", last_err, -1

    def list_devices(self):
        self.refresh_owners(max_age=0, wait=True)
        with self._owner_lock:
            entries = {p: list(v) for p, v in self._entries.items()}
            owner = dict(self._owner)
        devices = []
        
        pre_list = []
        seen = set()
        for port, port_entries in entries.items():
            for entry in port_entries:
                serial = entry['serial']
                if entry['state'] != "device": continue
                if serial in seen or owner.get(serial, port) != port: continue
                seen.add(serial)
                
                line = entry['line']
                parts = line.split()
                is_wifi = ":" in serial or "tcp" in line.lower()
                model = "Android Device"
                for p in parts:
                    if p.startswith("model:"):
                        model = p.replace("model:", "").replace("_", " ")
                        break
                pre_list.append({'serial': serial, 'state': entry['state'], 'is_wifi': is_wifi, 'model': model, 'adb_port': port})

        # Parallel Package Check
        threads = []
        sem = threading.Semaphore(10)
        
        def _check_pkg(dev_info):
            with sem:
                out, _, _ = self.run_command(["shell", "pm", "list", "packages", "com.genymobile.gnirehtet"], dev_info['serial'])
                dev_info['pkg_ok'] = ("package:com.genymobile.gnirehtet" in out)
                devices.append(dev_info)

        for dev in pre_list:
            t = threading.Thread(target=_check_pkg, args=(dev,))
            t.start()
            threads.append(t)
        
        for t in threads: t.join()
        return devices

    def install_apk(self, device_serial, apk_path):
        stdout, stderr, code = self.run_command(["install", "-r", apk_path], device_serial, timeout=180)
        return "Success" in stdout

    def install_split_apk(self, device_serial, folder_path):
        import glob
        apks = glob.glob(os.path.join(folder_path, "*.apk"))
        if not apks:
            return False
        cmd = ["install-multiple", "-r"] + apks
        stdout, stderr, code = self.run_command(cmd, device_serial, timeout=180)
        return "Success" in stdout

    def is_package_installed(self, device_serial, package_name):
        stdout, _, _ = self.run_command(["shell", "pm", "list", "packages"], device_serial)
        return package_name in stdout

    def set_global_proxy(self, device_serial, proxy_ip, proxy_port):
        cmd = ["shell", "settings", "put", "global", "http_proxy", f"{proxy_ip}:{proxy_port}"]
        _, _, code = self.run_command(cmd, device_serial)
        return code == 0

    def remove_global_proxy(self, device_serial):
        cmd = ["shell", "settings", "put", "global", "http_proxy", ":0"]
        _, _, code = self.run_command(cmd, device_serial)
        return code == 0

    def clear_global_proxy(self, device_serial):
        self.run_command(["shell", "settings", "delete", "global", "http_proxy"], device_serial)
        self.run_command(["shell", "settings", "delete", "global", "global_http_proxy_host"], device_serial)
        self.run_command(["shell", "settings", "delete", "global", "global_http_proxy_port"], device_serial)
        self.run_command(["shell", "am", "broadcast", "-a", "android.intent.action.PROXY_CHANGE"], device_serial)
        return True

    def boost_network_speed(self, device_serial):
        self.run_command(["shell", "settings", "put", "global", "captive_portal_mode", "0"], device_serial)
        self.run_command(["shell", "settings", "put", "global", "captive_portal_detection_enabled", "0"], device_serial)
        return True

    def get_real_ip(self, device_serial):
        stdout, _, _ = self.run_command(["shell", "settings", "get", "global", "http_proxy"], device_serial)
        proxy_val = stdout.strip()
        
        import requests
        proxies = None
        local_assignment = "Directo (:0)"
        if proxy_val and proxy_val != "null" and proxy_val != ":0" and ":" in proxy_val:
            proxies = {
                "http": f"http://{proxy_val}",
                "https": f"http://{proxy_val}"
            }
            local_assignment = f"Asignado Local: {proxy_val}"
            
        try:
            res = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=5)
            ip = res.json().get("ip", "")
            return local_assignment, f"🌍 {ip}"
        except Exception:
            if proxies:
                return local_assignment, "❌ PROXY MUERTO"
            return local_assignment, "❌ SIN CONEXIÓN"