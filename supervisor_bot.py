import os
import time
import json
import asyncio
import subprocess
import psutil
import socket
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIGURACIÓN =================
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PC_NAME = socket.gethostname()

FARM_DIR = os.path.dirname(os.path.abspath(__file__))
APP_SCRIPT = "app.py"
LOGS_DIR = os.path.join(FARM_DIR, "logs")

# ================= ESTADO DE SALUD (SISTEMA SANADOR) =================
device_fails = {}          # { 'serial_o_sufijo': fallos_consecutivos }
quarantined_devices = set() # { 'serial_o_sufijo' }
active_serials = set()     # Para calcular el total de dispositivos

code_red_active = False
code_red_deadline = 0

# Palabras clave de éxito para curar un celular
SUCCESS_KEYWORDS = ["Reproduciendo correctamente", "Modo Aleatorio", "Anuncio omitido", "Inyectando", "Logueado", "Guardando playlist", "Activado"]
# Palabras clave de fallo
FAIL_KEYWORDS = ["Offline", "Sigue sin reproducir", "Error de red", "Caída"]

# ================= FUNCIONES DE SISTEMA =================
async def enviar_alerta(context, mensaje):
    global CHAT_ID
    if CHAT_ID:
        try:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"[{PC_NAME}] {mensaje}")
        except Exception as e:
            print(f"Error al enviar Telegram: {e}")
    else:
        print(f"ALERTA (Sin CHAT_ID): [{PC_NAME}] {mensaje}")

def is_app_running():
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            if p.info['name'] == 'python.exe' and p.info['cmdline']:
                if APP_SCRIPT in ' '.join(p.info['cmdline']) and "supervisor_bot.py" not in ' '.join(p.info['cmdline']):
                    return True
        except: pass
    return False

def kill_app():
    killed = False
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] == 'python.exe' and p.info['cmdline']:
                if APP_SCRIPT in ' '.join(p.info['cmdline']) and "supervisor_bot.py" not in ' '.join(p.info['cmdline']):
                    p.kill()
                    killed = True
        except: pass
    return killed

def extraer_id_celular(linea):
    match = re.search(r'\[([A-Z0-9]{6,20})\]', linea)
    if match: return match.group(1)
    match_offline = re.search(r'Offline\s([A-Za-z0-9]+)', linea)
    if match_offline: return match_offline.group(1)
    return None

# ================= COMANDOS DE TELEGRAM =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = str(update.message.chat_id)
    with open(os.path.join(FARM_DIR, ".env"), "a") as f:
        f.write(f"\nCHAT_ID={CHAT_ID}\n")
    
    keyboard = [
        ["/estado", "/ignorar"],
        ["/detener", "/reiniciar_pc", "/apagar_pc"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"[{PC_NAME}] Bot Supervisor conectado. Teclado activado.", reply_markup=reply_markup)

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        app_run = "CORRIENDO" if is_app_running() else "DETENIDA"
        
        msg = f"[{PC_NAME}] Estado de la Granja:\n"
        msg += f"App: {app_run}\n"
        msg += f"Dispositivos: {len(active_serials)}\n"
        msg += f"En Cuarentena: {len(quarantined_devices)}\n"
        
        if quarantined_devices:
            msg += f"Enfermeria: {', '.join(quarantined_devices)}\n"
            
        if code_red_active:
            faltan = int((code_red_deadline - time.time()) / 60)
            msg += f"\nCODIGO ROJO: Apagado en {faltan} min."
            
        keyboard = [
            ["/estado", "/ignorar"],
            ["/detener", "/reiniciar_pc", "/apagar_pc"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(msg, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error en estado: {e}")

async def detener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global code_red_active
    await update.message.reply_text(f"[{PC_NAME}] 🛑 Abortando inyecciones y deteniendo la granja...")
    if kill_app():
        await update.message.reply_text(f"[{PC_NAME}] ✅ Granja detenida de forma segura.")
    else:
        await update.message.reply_text(f"[{PC_NAME}] ℹ️ La granja ya estaba detenida.")
    code_red_active = False

async def reiniciar_pc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"[{PC_NAME}] 🔄 Reiniciando la computadora en 10 segundos...")
    os.system("shutdown /r /t 10")

async def apagar_pc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"[{PC_NAME}] ⚡ Apagando la computadora de forma segura en 10 segundos...")
    os.system("shutdown /s /t 10")

async def ignorar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global code_red_active
    if code_red_active:
        code_red_active = False
        await update.message.reply_text(f"[{PC_NAME}] 🛡️ Alerta ignorada. La PC NO se reiniciará sola. Bomba de tiempo desactivada.")
    else:
        await update.message.reply_text(f"[{PC_NAME}] No había ningún Código Rojo activo.")

# ================= BACKGROUND LOG READER =================
async def monitor_logs_task(context: ContextTypes.DEFAULT_TYPE):
    global code_red_active, code_red_deadline
    
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOGS_DIR, f"registro_{hoy_str}.txt")
    if not os.path.exists(log_file): return

    if not hasattr(monitor_logs_task, "file"):
        monitor_logs_task.file = open(log_file, "r", encoding="utf-8")
        monitor_logs_task.file.seek(0, 2)
        monitor_logs_task.current_date = hoy_str

    if monitor_logs_task.current_date != hoy_str:
        monitor_logs_task.file.close()
        monitor_logs_task.file = open(log_file, "r", encoding="utf-8")
        monitor_logs_task.current_date = hoy_str
    
    lineas = monitor_logs_task.file.readlines()
    
    for linea in lineas:
        serial = extraer_id_celular(linea)
        if not serial: continue
        
        active_serials.add(serial)
        
        if "Piloto Automático INICIADO por auto-arranque" in linea:
            asyncio.create_task(enviar_alerta(context, "🚀 ¡La cuenta regresiva terminó! El Piloto Automático ha tomado el control de la granja."))
            
        if any(kw in linea for kw in SUCCESS_KEYWORDS):
            device_fails[serial] = 0
            if serial in quarantined_devices:
                quarantined_devices.remove(serial)
                asyncio.create_task(enviar_alerta(context, f"💚 El celular {serial} logró recuperarse y salió de Cuarentena."))
                
        elif any(kw in linea for kw in FAIL_KEYWORDS):
            device_fails[serial] = device_fails.get(serial, 0) + 1
            if device_fails[serial] == 3 and serial not in quarantined_devices:
                quarantined_devices.add(serial)
                asyncio.create_task(enviar_alerta(context, f"⚠️ El celular {serial} falló 3 veces seguidas. Entra en CUARENTENA."))
                
    total = len(active_serials)
    if total > 0 and len(quarantined_devices) > (total / 2.0):
        if not code_red_active:
            code_red_active = True
            code_red_deadline = time.time() + (6 * 3600)
            msg = f"🚨 ALERTA CRÍTICA: La mitad de la granja ({len(quarantined_devices)}/{total}) está en cuarentena.\n\n"
            msg += "¿Qué debo hacer, Jefe?\n"
            msg += "▶ /reiniciar_pc\n"
            msg += "▶ /apagar_pc\n"
            msg += "▶ /detener (Cerrar app)\n"
            msg += "▶ /ignorar (Desactivar bomba)\n\n"
            msg += "⏳ Si no respondes, REINICIARÉ la PC automáticamente en 6 HORAS."
            asyncio.create_task(enviar_alerta(context, msg))
            
    if code_red_active and time.time() >= code_red_deadline:
        asyncio.create_task(enviar_alerta(context, "⚡ Jefe ausente. Límite de 6 horas alcanzado. REINICIANDO PC PARA REVIVIR LA GRANJA..."))
        os.system("shutdown /r /t 5")
        code_red_active = False

# ================= MAIN =================
if __name__ == '__main__':
    if not TOKEN or TOKEN == "PEGA_TU_TOKEN_AQUI_SIN_COMILLAS":
        print("ERROR: Configura TELEGRAM_BOT_TOKEN")
        exit(1)
        
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("detener", detener))
    app.add_handler(CommandHandler("reiniciar_pc", reiniciar_pc))
    app.add_handler(CommandHandler("apagar_pc", apagar_pc))
    app.add_handler(CommandHandler("ignorar", ignorar))

    app.job_queue.run_repeating(monitor_logs_task, interval=5.0, first=2.0)

    print(f"[{PC_NAME}] Bot Sanador y Supervisor activado.")
    import time
    while True:
        try:
            app.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"Error de Telegram: {e}")
            time.sleep(10)
