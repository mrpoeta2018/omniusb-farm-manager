import threading
import requests

class ProxyTester:
    @staticmethod
    def test_proxies_async(proxy_list, update_callback, final_callback):
        results = {"alive": [], "dead": []}
        total = len(proxy_list)
        completed_count = [0]
        lock = threading.Lock()
        
        if total == 0:
            final_callback(results)
            return

        def worker(p):
            # Formatear proxy inteligentemente
            # Soporta: ip:port:user:pass o user:pass:ip:port o ip:port
            parts = p.replace("@", ":").split(":")
            formatted_p = p
            if len(parts) == 4:
                # Si las partes 0 y 1 son números (puertos/ips cortas), asumimos ip:port:user:pass
                # Una forma rápida es que el user no suele tener puntos
                if "." in parts[0] and parts[1].isdigit():
                    formatted_p = f"{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                else:
                    formatted_p = f"{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}"
                    
            req_p = {"http": f"http://{formatted_p}", "https": f"http://{formatted_p}"}
            is_alive = False
            try:
                r = requests.get("https://api.ipify.org?format=json", proxies=req_p, timeout=5)
                if r.status_code == 200:
                    is_alive = True
            except:
                pass
                
            with lock:
                if is_alive:
                    results["alive"].append(p)
                else:
                    results["dead"].append(p)
                completed_count[0] += 1
                c = completed_count[0]
                
            update_callback(c, total, p, is_alive)
            
            if c == total:
                final_callback(results)
                
        for p in proxy_list:
            threading.Thread(target=worker, args=(p,), daemon=True).start()
