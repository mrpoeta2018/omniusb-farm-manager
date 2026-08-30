import os
import time
import json
import asyncio
import subprocess
import psutil
import socket
from datetime import datetime, timedelta
from collections import deque
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PC_NAME = socket.gethostname()

# Rutas
FARM_DIR = r"C:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager"
APP_SCRIPT = "app.py"
LOGS_DIR = os.path.join(FARM_DIR, "logs")
STATE_FILE = os.path.join(os.path.dirname(__file__), "supervisor_state.json")

# Variables de estado y umbrales (Monitor de Logs)
quarantine_events = deque()
tunnel_events = deque()
playback_events = deque()
MAX_QUARANTINE_5MIN = 5
MAX_TUNNEL_1MIN = 20
MAX_PLAYBACK_5MIN = 10
is_recovering = False

# ================= FUNCIONES DE UTILIDAD =================
async def enviar_alerta(context, mensaje):
    if CHAT_ID:
        try:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"[{PC_NAME}] {mensaje}")
        except Exception as e:
            print(f"Error al enviar por Telegram: {e}")
    else:
        print(f"ALERTA: [{PC_NAME}] {mensaje}")

def is_app_running():
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            if p.info['name'] == 'python.exe' and p.info['cmdline'] and APP_SCRIPT in p.info['cmdline']:
                return True
        except: pass
    return False

def kill_app():
    killed = False
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            if p.info['name'] == 'python.exe' and p.info['cmdline'] and APP_SCRIPT in p.info['cmdline']:
                p.kill()
                killed = True
        except: pass
    return killed

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"last_maintenance": time.time()} # Inicia el conteo de 48h desde la primera ejecución

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ================= COMANDOS DE TELEGRAM =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    if not CHAT_ID:
        CHAT_ID = str(update.message.chat_id)
        # Podriamos persistir el CHAT_ID en el archivo de estado
        state = load_state()
        state["chat_id"] = CHAT_ID
        save_state(state)
        
    await update.message.reply_text(f"[{PC_NAME}] 👋 Agente Supervisor en línea. Rutinas y Monitoreo activos.")

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_app_running():
        await update.message.reply_text(f"[{PC_NAME}] 🟢 La granja está CORRIENDO.")
    else:
        await update.message.reply_text(f"[{PC_NAME}] 🔴 La granja está DETENIDA.")

async def detener_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"[{PC_NAME}] 🛑 Deteniendo granja...")
    if kill_app():
        await update.message.reply_text(f"[{PC_NAME}] ✅ Detenida.")
    else:
        await update.message.reply_text(f"[{PC_NAME}] ⚠️ No corría.")

# ================= RECUPERACIÓN Y RUTINAS =================
def get_expected_task():
    # Retorna la tarea que debería estar ejecutándose según la hora actual
    hora = datetime.now().hour
    if 0 <= hora < 12:
        return "SOLO SPOTIFY"     # 12h
    elif 12 <= hora < 18:
        return "SOLO YT MUSIC"    # 6h
    else:
        return "SOLO YT VIDEO"    # 6h

async def protocolo_reinicio_app(context):
    global is_recovering
    if is_recovering: return
    is_recovering = True
    
    await enviar_alerta(context, "🔧 Nivel 1: Reiniciando App por fallas...")
    kill_app()
    await asyncio.sleep(3)
    try:
        subprocess.Popen(["python", APP_SCRIPT, "--auto"], cwd=FARM_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
    except Exception as e:
        await enviar_alerta(context, f"❌ Error fatal al reiniciar: {e}")
        
    quarantine_events.clear()
    tunnel_events.clear()
    playback_events.clear()
    await asyncio.sleep(10)
    is_recovering = False

async def protocolo_reinicio_pc(context):
    global is_recovering
    if is_recovering: return
    is_recovering = True
    await enviar_alerta(context, "🚨 Nivel 2: REINICIANDO PC EN 15s...")
    await asyncio.sleep(2)
    os.system("shutdown /r /t 15 /c \"Fallo critico en granja\"")

async def cambiar_tarea_y_reiniciar(context, nueva_tarea):
    global is_recovering
    is_recovering = True
    await enviar_alerta(context, f"🔄 Cambiando tarea a: {nueva_tarea}")
    kill_app()
    await asyncio.sleep(3)
    
    config_path = os.path.join(FARM_DIR, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f: data = json.load(f)
            data["master_mode"] = nueva_tarea
            with open(config_path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
        except Exception as e:
            await enviar_alerta(context, f"⚠️ Error al editar config.json: {e}")
            
    try:
        subprocess.Popen(["python", APP_SCRIPT, "--auto"], cwd=FARM_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
    except Exception as e:
        await enviar_alerta(context, f"❌ Error al iniciar app: {e}")
        
    await asyncio.sleep(5)
    is_recovering = False

async def rutina_mantenimiento_48h(context):
    global is_recovering
    is_recovering = True
    await enviar_alerta(context, "🧹 MANTENIMIENTO 48H: Apagando celulares y PC...")
    kill_app()
    await asyncio.sleep(3)
    
    adb_path = os.path.join(FARM_DIR, "platform-tools", "adb.exe")
    if os.path.exists(adb_path):
        os.system(f'"{adb_path}" reboot')
        await enviar_alerta(context, "📱 Celulares reiniciando... Esperando 40s")
        await asyncio.sleep(40)
        
    state = load_state()
    state["last_maintenance"] = time.time()
    save_state(state)
    os.system("shutdown /r /t 0")

# ================= BACKGROUND TASKS =================
def limpiar_eventos_viejos(now):
    while quarantine_events and quarantine_events[0] < now - timedelta(minutes=5): quarantine_events.popleft()
    while tunnel_events and tunnel_events[0] < now - timedelta(minutes=1): tunnel_events.popleft()
    while playback_events and playback_events[0] < now - timedelta(minutes=5): playback_events.popleft()

async def monitor_logs_task(context: ContextTypes.DEFAULT_TYPE):
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOGS_DIR, f"registro_{hoy_str}.txt")
    if not os.path.exists(log_file): return

    if not hasattr(monitor_logs_task, "file_pointer"):
        monitor_logs_task.file = open(log_file, "r", encoding="utf-8")
        monitor_logs_task.file.seek(0, 2)
        monitor_logs_task.current_date = hoy_str

    if monitor_logs_task.current_date != hoy_str:
        monitor_logs_task.file.close()
        monitor_logs_task.file = open(log_file, "r", encoding="utf-8")
        monitor_logs_task.current_date = hoy_str
    
    lineas = monitor_logs_task.file.readlines()
    if not lineas: return
        
    now = datetime.now()
    limpiar_eventos_viejos(now)
    
    for linea in lineas:
        if "CUARENTENA" in linea: quarantine_events.append(now)
        elif "Túnel caído" in linea: tunnel_events.append(now)
        elif "Sigue sin reproducir" in linea: playback_events.append(now)
        elif "ERROR CRÍTICO EN ARRANQUE" in linea:
            asyncio.create_task(protocolo_reinicio_app(context))
            return

    if len(quarantine_events) >= MAX_QUARANTINE_5MIN: asyncio.create_task(protocolo_reinicio_pc(context))
    elif len(tunnel_events) >= MAX_TUNNEL_1MIN: asyncio.create_task(protocolo_reinicio_app(context))
    elif len(playback_events) >= MAX_PLAYBACK_5MIN: asyncio.create_task(protocolo_reinicio_app(context))

async def monitor_rutinas_task(context: ContextTypes.DEFAULT_TYPE):
    if is_recovering: return

    # 1. Chequeo Mantenimiento 48h
    state = load_state()
    if time.time() - state.get("last_maintenance", time.time()) > (48 * 3600):
        asyncio.create_task(rutina_mantenimiento_48h(context))
        return

    # 2. Chequeo de Tarea / Arranque automático
    expected_task = get_expected_task()
    config_path = os.path.join(FARM_DIR, "config.json")
    current_task = None
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                current_task = json.load(f).get("master_mode")
        except: pass

    # Si la app no corre, O si hay que rotar tarea
    if not is_app_running() or current_task != expected_task:
        asyncio.create_task(cambiar_tarea_y_reiniciar(context, expected_task))

# ================= MAIN =================
if __name__ == '__main__':
    # Cargar CHAT_ID persistido si existe
    state = load_state()
    if "chat_id" in state:
        CHAT_ID = state["chat_id"]

    if not TOKEN or TOKEN == "PEGA_TU_TOKEN_AQUI_SIN_COMILLAS":
        print("ERROR: Token faltante.")
        exit(1)
        
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("reiniciar_app", lambda u, c: asyncio.create_task(protocolo_reinicio_app(c))))
    app.add_handler(CommandHandler("detener_app", detener_app))

    # Tareas programadas
    app.job_queue.run_repeating(monitor_logs_task, interval=3.0, first=5.0)
    app.job_queue.run_repeating(monitor_rutinas_task, interval=30.0, first=2.0)

    print(f"Bot en línea en [{PC_NAME}]. Monitoreo y Rutinas activos.")
    app.run_polling()
