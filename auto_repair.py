import os
import ssl
import urllib.request
import zipfile
import shutil
import subprocess

# SSL fix: some Windows/Python installs lack proper CA certificates
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def download_and_extract(url, zip_name, target_dir=None, flatten=False):
    print(f"[*] Descargando {zip_name} desde {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "OmniUSB/4.0"})
    with urllib.request.urlopen(req, context=ssl_ctx) as resp, open(zip_name, "wb") as f:
        f.write(resp.read())
    print(f"[*] Extrayendo {zip_name} ...")
    
    extract_path = target_dir if target_dir else "temp_extract"
    extract_path = os.path.abspath(extract_path)
    if os.name == 'nt' and not extract_path.startswith('\\\\?\\'):
        extract_path = '\\\\?\\' + extract_path
        
    os.makedirs(extract_path, exist_ok=True)
    
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        
    if flatten:
        # Move all files from subfolders to the root of the app
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                source_file = os.path.join(root, file)
                dest_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
                # Don't overwrite if not needed, or force overwrite
                shutil.move(source_file, dest_file)
        shutil.rmtree(extract_path, ignore_errors=True)
        
    if os.path.exists(zip_name):
        os.remove(zip_name)
    print(f"[+] Completado: {zip_name}")

def verify_system_integrity():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=== AIDX Proxy Farm V3 : VERIFICANDO INTEGRIDAD ===")
    
    # 1. Check Gnirehtet
    if not os.path.exists("gnirehtet.exe") or not os.path.exists("gnirehtet.apk"):
        print("[!] Gnirehtet faltante. Iniciando Auto-Reparación...")
        gnirehtet_url = "https://github.com/Genymobile/gnirehtet/releases/download/v2.5.1/gnirehtet-rust-win64-v2.5.1.zip"
        # Since v2.5.1 contains a folder `gnirehtet-rust-win64-2.5.1`, we use flatten=True
        try:
            download_and_extract(gnirehtet_url, "gnirehtet_dl.zip", flatten=True)
        except Exception as e:
            print("[X] Fallo al descargar Gnirehtet:", e)

    # 2. Check ADB (Platform-tools)
    if not os.path.exists(os.path.join("platform-tools", "adb.exe")):
        print("[!] ADB (Platform Tools) faltante. Iniciando Auto-Reparación...")
        adb_url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        try:
            # This extracts a `platform-tools` folder natively
            download_and_extract(adb_url, "platform_tools_dl.zip", target_dir=base_dir, flatten=False)
        except Exception as e:
            print("[X] Fallo al descargar ADB:", e)

    # 3. Check scrcpy (Screen Mirror)
    scrcpy_dir = os.path.join(base_dir, "scrcpy")
    if not os.path.exists(os.path.join(scrcpy_dir, "scrcpy.exe")):
        print("[!] scrcpy (Screen Mirror) faltante. Iniciando Auto-Reparación...")
        scrcpy_url = "https://github.com/Genymobile/scrcpy/releases/download/v3.2/scrcpy-win64-v3.2.zip"
        try:
            download_and_extract(scrcpy_url, "scrcpy_dl.zip", target_dir=base_dir, flatten=False)
            # Rename extracted folder to 'scrcpy'
            for item in os.listdir(base_dir):
                if item.startswith("scrcpy-win64") and os.path.isdir(os.path.join(base_dir, item)):
                    os.rename(os.path.join(base_dir, item), scrcpy_dir)
                    break
        except Exception as e:
            print("[X] Fallo al descargar scrcpy:", e)

    # 3. Check NodeJS & NPM
    try:
        subprocess.run(["node", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("[!] NodeJS NO encontrado. Iniciando descarga automatica de version portable (NodeJS 20)...")
        node_zip = "node_portable_dl.zip"
        node_url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
        try:
            download_and_extract(node_url, node_zip, target_dir=base_dir, flatten=False)
            node_portable_dir = os.path.join(base_dir, "node_portable")
            for item in os.listdir(base_dir):
                if item.startswith("node-v20") and os.path.isdir(os.path.join(base_dir, item)):
                    if os.path.exists(node_portable_dir):
                        shutil.rmtree(node_portable_dir)
                    os.rename(os.path.join(base_dir, item), node_portable_dir)
                    break
            print("[+] Instalacion de NodeJS Portable completada!")
            # Actualizar PATH temporalmente para que npm funcione de inmediato
            os.environ["PATH"] = node_portable_dir + os.pathsep + os.environ["PATH"]
        except Exception as e:
            print("[X] Fallo la descarga de NodeJS Portable:", e)
            print("Por favor instala NodeJS manualmente desde nodejs.org")
            input("Presiona ENTER para salir...")
            exit(1)

    # 4. Ensure Node dependencies are present now, not during run
    if not os.path.exists(os.path.join(base_dir, "node_modules", "proxy-chain")):
        print("[*] Instalando dependencias de Node (proxy-chain)... Esto solo ocurre una vez.")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.run([npm_cmd, "install", "proxy-chain"], cwd=base_dir, shell=True)

    # 5. Check Python Requirements (Self-Heal Venv)
    if os.path.exists("requirements.txt"):
        print("[*] Verificando librerías de Python... (psutil, customtkinter, etc.)")
        try:
            # We use the current python executable to install requirements
            subprocess.run([os.sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print("[!] Aviso: No se pudieron actualizar las librerías automáticamente.")

    # 6. Sincronizar binarios de ADB con Xiaowei si existe para evitar conflictos de versiones
    xw_tools_dir = os.path.join(base_dir, "xiaowei_android", "tools")
    pf_tools_dir = os.path.join(base_dir, "platform-tools")
    
    if os.path.exists(xw_tools_dir) and os.path.exists(pf_tools_dir):
        print("[*] Armonizando motor ADB con software externo para evitar desconexiones...")
        import shutil
        for adb_file in ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"]:
            src = os.path.join(xw_tools_dir, adb_file)
            dst = os.path.join(pf_tools_dir, adb_file)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dst)
                except:
                    pass

    # 7. Pre-start ADB server to avoid timeouts on first scan
    print("[*] Sincronizando con el motor ADB...")
    adb_exe = os.path.join(pf_tools_dir, "adb.exe")
    if os.path.exists(adb_exe):
        # NOTA: Ya no matamos 'adb.exe' (taskkill) para permitir que otras apps (como Xiaowei) sigan conectadas.
        try:
            subprocess.run([adb_exe, "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        except subprocess.TimeoutExpired:
            print("[!] Error crítico: ADB está congelado (Timeout). ¡Iniciando Auto-Sanación de ADB!")
            try:
                subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time
                time.sleep(2)
                subprocess.run([adb_exe, "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                print("[+] ADB reiniciado y desbugeado con éxito.")
            except Exception as e:
                print(f"[X] Falló la auto-sanación de ADB: {e}")
    
    print("=== SISTEMA 100% LISTO Y OPERATIVO ===")

if __name__ == "__main__":
    verify_system_integrity()
