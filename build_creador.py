import os

with open('X:/Desktop/OmniUSB-Piloto-Automatico-Edicion-Oro-Final/core/creador_raw.py', 'r', encoding='utf-8') as f:
    raw_code = f.read()

lines = raw_code.split('\n')
new_lines = []

header = '''import customtkinter as ctk
import tkinter.messagebox as messagebox
import threading
import time
import os
import re
import xml.etree.ElementTree as ET
import json
import random

class GestorCuentas(ctk.CTkToplevel):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.title("👤 Gestor de Cuentas (Modo Aislado)")
        self.geometry("1000x700")
        self.adb = adb_manager
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Panel Izquierdo: Controles
        left_frame = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=8)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text="👤 Creador de Cuentas Automático", font=("Arial", 16, "bold"), text_color="#F59E0B").pack(pady=10)
        
        # Selector Múltiple de Celulares
        ctk.CTkLabel(left_frame, text="📱 Seleccionar Celular(es):", font=("Arial", 12)).pack(pady=(10, 2))
        
        self.acc_devices_frame = ctk.CTkScrollableFrame(left_frame, width=250, height=120)
        self.acc_devices_frame.pack(pady=5, fill="x", padx=30)
        self.acc_device_vars = {}
        
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=2)
        
        def _sel_all():
            for var in self.acc_device_vars.values(): var.set(True)
        def _sel_none():
            for var in self.acc_device_vars.values(): var.set(False)
            
        ctk.CTkButton(btn_frame, text="Todos", width=120, command=_sel_all).pack(side="left")
        ctk.CTkButton(btn_frame, text="Ninguno", width=120, command=_sel_none).pack(side="right")
'''

inside_init = True
for idx in range(40, len(lines)):
    line = lines[idx]
    if line.startswith('    def update_account_creator_devices(self):'):
        inside_init = False
        new_lines.append('')
        
    if inside_init:
        line = line.replace('self.tab_accounts', 'self')
        new_lines.append(line)
    else:
        new_lines.append(line)

final_code = header + '\n'.join(new_lines)

final_code = final_code.replace('self.launch_scrcpy(serial)', 'self.adb.run_command(["shell", "echo", "Scrcpy not included in popup"], serial)')
final_code = final_code.replace("getattr(self, 'scanned_devices', [])", "self.adb.list_devices()")

with open('X:/Desktop/OmniUSB-Piloto-Automatico-Edicion-Oro-Final/core/creador.py', 'w', encoding='utf-8') as f:
    f.write(final_code)
