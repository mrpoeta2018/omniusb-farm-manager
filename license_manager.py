import os
import uuid
import json
import urllib.request
import hashlib

# ====== CONFIGURACIÓN DE TU NEGOCIO ======
# Este es el link RAW a tu archivo licencias.json en GitHub.
# Ejemplo del contenido que debes tener en GitHub:
# {
#    "llaves_activas": {
#        "LIC-PABLO-1X9A": "A1B2C3D4E5F6",
#        "LIC-VIP-ILIMITADA": "C8D9E0A1B2C3"
#    }
# }
LICENSE_URL = "https://raw.githubusercontent.com/escucha0012-lab/OmniUSB-Licencias/main/licencias.json"
# =========================================

def get_hardware_id():
    """Returns a unique fingerprint of the current PC."""
    mac = uuid.getnode()
    # Hash the MAC to create a clean, professional-looking HWID
    hashed = hashlib.md5(str(mac).encode()).hexdigest().upper()
    # Format as XXXX-XXXX-XXXX
    hwid = f"{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}"
    return hwid

def validate_license(key, hwid):
    """
    Downloads the remote license database and checks:
    1. If the key exists.
    2. If the key is bound to the provided HWID (or "ANY" for universal keys).
    """
    if not LICENSE_URL or "TU_USUARIO" in LICENSE_URL:
        # Modo de prueba si no has configurado GitHub
        return False, "⚠️ No has configurado el LICENSE_URL con tu GitHub."

    try:
        req = urllib.request.Request(LICENSE_URL, headers={"User-Agent": "OmniUSB/4.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            llaves = data.get("llaves_activas", {})
            
            if key not in llaves:
                return False, "❌ La Licencia no existe o expiró."
            
            llave_hwid = llaves[key].upper().replace("-", "")
            local_hwid = hwid.upper().replace("-", "")
            
            if llave_hwid != "ANY" and llave_hwid != local_hwid:
                return False, "❌ Licencia válida pero atada a OTRA computadora."
                
            return True, "✅ Licencia Aprobada."
    except Exception as e:
        return False, f"⚠️ Error comprobando en servidor. Revisa tu internet."
