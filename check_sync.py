import subprocess
import concurrent.futures
import re

adb_path = r'C:\Users\poeta marzo\Desktop\omniusb-farm-manager-main\omniusb-farm-manager\platform-tools\adb.exe'

def get_devices():
    res = subprocess.run([adb_path, 'devices'], capture_output=True, text=True)
    devices = []
    for line in res.stdout.splitlines():
        if 'device' in line and not 'List' in line:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == 'device':
                devices.append(parts[0])
    return devices

def check_device(serial):
    # Check focus
    focus_res = subprocess.run([adb_path, '-s', serial, 'shell', 'dumpsys', 'window', 'windows', '|', 'grep', '-E', "'mCurrentFocus|mFocusedApp'"], capture_output=True, text=True)
    focus = focus_res.stdout.strip()
    app = "Desconocido"
    if "com.spotify.music" in focus: app = "Spotify"
    elif "com.google.android.youtube" in focus: app = "YouTube"
    elif "com.google.android.apps.youtube.music" in focus: app = "YT Music"
    elif "Launcher" in focus or "NexusLauncherActivity" in focus: app = "Menu Inicio"
    
    # Check media
    media_res = subprocess.run([adb_path, '-s', serial, 'shell', 'dumpsys', 'media_session'], capture_output=True, text=True)
    media_out = media_res.stdout
    state = "Detenido ??"
    if "state=PlaybackState {state=3" in media_out or "state=3" in media_out:
        state = "Reproduciendo ??"
    elif "state=PlaybackState {state=2" in media_out or "state=2" in media_out:
        state = "Pausado ??"
        
    return f"?? {serial[-6:]:>6} | ?? App: {app:<11} | ?? Audio: {state}"

devices = get_devices()
print(f"Buscando estado de {len(devices)} dispositivos...\n")

with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
    results = list(executor.map(check_device, devices))
    
for r in sorted(results):
    print(r)
