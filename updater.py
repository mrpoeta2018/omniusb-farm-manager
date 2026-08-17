"""
OmniUSB Auto-Updater
Checks a remote version.json and downloads updates if available.
"""
import os
import json
import urllib.request
import zipfile
import shutil
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")


def get_local_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "0.0.0", "check_url": ""}


def get_remote_version(check_url):
    """Fetch remote version.json from any URL (GitHub, Google Drive, etc)."""
    if not check_url:
        return None
    try:
        import time
        sep = "&" if "?" in check_url else "?"
        url_with_t = f"{check_url}{sep}t={int(time.time())}"
        
        req = urllib.request.Request(url_with_t, headers={"User-Agent": "OmniUSB/4.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def compare_versions(local_str, remote_str):
    """Returns True if remote is newer than local."""
    try:
        local_parts = [int(x) for x in local_str.split(".")]
        remote_parts = [int(x) for x in remote_str.split(".")]
        return remote_parts > local_parts
    except Exception:
        return False


def download_update(download_url, callback_progress=None, callback_done=None):
    """Download a zip update and extract it over the current installation."""
    def _worker():
        # SI EXISTE REPOSITORIO GIT, ACTUALIZAR VIA GIT PULL
        git_dir = os.path.join(BASE_DIR, ".git")
        if os.path.exists(git_dir):
            try:
                if callback_progress:
                    callback_progress("Actualizando desde GitHub (Hard Reset)...")
                import subprocess
                subprocess.run(["git", "fetch", "origin", "main"], capture_output=True, text=True, check=True)
                subprocess.run(["git", "reset", "--hard", "origin/main"], capture_output=True, text=True, check=True)
                res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, check=True)
                print("Git pull output:", res.stdout)
                
                # Instalar dependencias si cambiaron
                req_file = os.path.join(BASE_DIR, "requirements.txt")
                if os.path.exists(req_file):
                    if callback_progress:
                        callback_progress("Actualizando dependencias...")
                    # Buscar pip del venv local o pip global
                    pip_path = os.path.join(BASE_DIR, "venv", "Scripts", "pip.exe")
                    if os.path.exists(pip_path):
                        subprocess.run([pip_path, "install", "-r", req_file], capture_output=True, check=True)
                    else:
                        subprocess.run(["pip", "install", "-r", req_file], capture_output=True, check=True)

                if callback_done:
                    callback_done(True, "¡Actualizado con éxito! Reiniciando...")
                
                import time
                time.sleep(2)
                os._exit(0) # Forzar salida para que START_APP.bat reinicie la app
            except Exception as e:
                print(f"Git pull failed, falling back to ZIP: {e}")
                pass # Continue to ZIP download below

        zip_path = os.path.join(BASE_DIR, "_update.zip")
        extract_path = os.path.join(BASE_DIR, "_update_temp")
        try:
            if callback_progress:
                callback_progress("Descargando actualización...")

            urllib.request.urlretrieve(download_url, zip_path)

            if callback_progress:
                callback_progress("Extrayendo archivos...")

            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_path)

            # Copy extracted files over current installation
            # Walk through extracted files and copy to BASE_DIR
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    src = os.path.join(root, file)
                    # Calculate relative path from extract root
                    rel = os.path.relpath(src, extract_path)
                    # Skip first directory level if zip contains a wrapper folder
                    parts = rel.split(os.sep)
                    if len(parts) > 1:
                        rel_no_wrapper = os.path.join(*parts[1:])
                    else:
                        rel_no_wrapper = rel
                    
                    dst = os.path.join(BASE_DIR, rel_no_wrapper)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    # Don't overwrite config.json (user's proxies/settings)
                    if os.path.basename(dst) == "config.json":
                        continue
                    shutil.copy2(src, dst)

            if callback_progress:
                callback_progress("Limpiando...")

            # Cleanup
            shutil.rmtree(extract_path, ignore_errors=True)
            if os.path.exists(zip_path):
                os.remove(zip_path)

            if callback_done:
                callback_done(True, "Actualización completada. Reinicia la app.")

        except Exception as e:
            # Cleanup on error
            if os.path.exists(zip_path):
                os.remove(zip_path)
            shutil.rmtree(extract_path, ignore_errors=True)

            if callback_done:
                callback_done(False, f"Error al actualizar: {str(e)}")

    threading.Thread(target=_worker, daemon=True).start()


def check_for_updates_async(callback):
    """
    Check for updates in background. Calls callback(has_update, remote_info) on main thread.
    remote_info = {version, notes, download_url} or None
    """
    def _worker():
        local = get_local_version()
        check_url = local.get("check_url", "")
        if not check_url:
            callback(False, None)
            return

        remote = get_remote_version(check_url)
        if remote and compare_versions(local.get("version", "0.0.0"), remote.get("version", "0.0.0")):
            callback(True, remote)
        else:
            callback(False, None)

    threading.Thread(target=_worker, daemon=True).start()
