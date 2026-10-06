"""
app_clean.py
============
Punto de Entrada para OmniUSB Rediseñado (Lego)
Diseño de "Asistente Paso a Paso" con caja de proxies ampliada.
"""

import os
import time
import json
import updater
import threading
import re
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(0.9)
ctk.set_window_scaling(0.9)

# Importar bloques viejos reutilizados
from adb_manager import ADBManager
from gnirehtet_runner import GnirehtetRunner
from node_proxy import NodeProxyManager
from proxy_tester import ProxyTester  # Rescatado de la app original

# Importar nuevos bloques
from core.tunnel import FarmTunnel
from core.injector import MediaInjector
from core.scheduler import Scheduler
from core.monitor import DeviceMonitor

# Configuración UI
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class OmniUSBCleanApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OmniUSB Piloto Automático - EDICIÓN ORO 🏆")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # ── Dependencias Core ──
        self.adb = ADBManager()
        self.gnirehtet = GnirehtetRunner()
        self.proxy_mgr = NodeProxyManager()
        
        # ── Bloques Nuevos ──
        self.tunnel = FarmTunnel(self.adb, self.gnirehtet, self.proxy_mgr, self.log_msg)
        self.injector = MediaInjector(self.adb, self.log_msg)
        self.scheduler = Scheduler(self.log_msg, on_phase_change=self._on_phase_change, on_tick=self._on_tick)
        self.monitor = DeviceMonitor(self.adb, self.log_msg, on_device_alert=self._on_device_alert)
        
        # Estado
        self.scanned_devices = []
        self.device_ui_vars = {} 
        self.device_ui_cards = {}
        
        self.config_file = "config_clean.json"
        
        # Estado de Bloqueos
        self.manual_btns = []
        self.is_cleaning = False
        self.is_injecting_manual = False
        self._build_ui()
        self._load_config()
        self.after(0, lambda: self._on_mode_change(self.mode_var.get()))
        
        threading.Thread(target=self._ghost_touch_loop, daemon=True).start()
        threading.Thread(target=self._impatient_skip_loop, daemon=True).start()
        threading.Thread(target=self._ad_skipper_loop, daemon=True).start()
        
        # --- VERIFICACIÓN DE ACTUALIZACIÓN EN SEGUNDO PLANO ---
        def _bg_check(has_upd, info):
            if has_upd:
                self.btn_update.configure(
                    text="⭐ ¡HAY UNA ACTUALIZACIÓN! ⭐",
                    fg_color="#DC2626", # Rojo brillante
                    text_color="#FFFFFF",
                    hover_color="#991B1B"
                )
        try:
            import updater
            updater.check_for_updates_async(_bg_check)
        except: pass
        
    # =========================================================================
    # UI BUILDER - MODO GUÍA PASO A PASO
    # =========================================================================
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=6, uniform="main")
        self.grid_columnconfigure(1, weight=4, uniform="main")
        self.grid_rowconfigure(1, weight=1) # 1 will be the main panels, 0 will be the banner
        
        # --- BANNER DE AUTO-ARRANQUE ---
        self.f_autoboot = ctk.CTkFrame(self, fg_color="#4338CA", corner_radius=0)
        self.f_autoboot.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.lbl_autoboot = ctk.CTkLabel(self.f_autoboot, text="🚀 AUTO-ARRANQUE EN 300 SEGUNDOS... Haremos el Escaneo, Proxies y Túnel automáticamente.", font=("Arial", 14, "bold"), text_color="white")
        self.lbl_autoboot.pack(side="left", padx=20, pady=5)
        
        self.btn_cancel_autoboot = ctk.CTkButton(self.f_autoboot, text="❌ Cancelar Auto-Arranque", fg_color="#EF4444", hover_color="#DC2626", command=self.cancel_autoboot)
        self.btn_cancel_autoboot.pack(side="right", padx=10, pady=5)
        
        self.btn_now_autoboot = ctk.CTkButton(self.f_autoboot, text="⚡ Arrancar AHORA", fg_color="#10B981", hover_color="#059669", command=self.force_autoboot_now)
        self.btn_now_autoboot.pack(side="right", padx=10, pady=5)
        
        self.autoboot_secs = 300
        self.autoboot_id = self.after(1000, self._autoboot_tick)
        
        # PANEL IZQUIERDO (Pasos 1, 2, 3 y Piloto)
        left_panel = ctk.CTkScrollableFrame(self, border_color="#F59E0B", border_width=2)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
                # --- BANNER ORO ---
        f_oro = ctk.CTkFrame(left_panel, fg_color="#F59E0B", corner_radius=8)
        f_oro.pack(fill="x", pady=(0, 10))
        
        self.btn_update = ctk.CTkButton(f_oro, text="🔄 Buscar Actualización", fg_color="#000000", hover_color="#333333", text_color="#F59E0B", font=("Arial", 12, "bold"), height=26, command=self.action_check_update)
        self.btn_update.pack(side="right", padx=10, pady=5)
        
        # El titulo va al medio pero le damos padx compensando
        ctk.CTkLabel(f_oro, text="🏆 EDICIÓN ORO FINAL 🏆", font=("Arial", 16, "bold"), text_color="black").pack(pady=5, expand=True)

        
        # --- PASO 1: ESCANEO ---
        f_step1 = ctk.CTkFrame(left_panel, fg_color="#1E293B", corner_radius=8, border_color="#3B82F6", border_width=1)
        f_step1.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(f_step1, text="PASO 1: ESCANEAR DISPOSITIVOS", font=("Arial", 14, "bold"), text_color="#60A5FA").pack(pady=(10, 0))
        ctk.CTkLabel(f_step1, text="💡 Consejo: Conectá los celulares por USB, asegurate de que tengan depuración USB activa.", font=("Arial", 10), text_color="#94A3B8").pack()
        
        btn_f1 = ctk.CTkFrame(f_step1, fg_color="transparent")
        btn_f1.pack(fill="x", padx=15, pady=10)
        
        self.btn_scan = ctk.CTkButton(btn_f1, text="🔍 Buscar Celulares", command=self.action_scan)
        self.btn_scan.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.combo_apps = ctk.CTkComboBox(btn_f1, values=["Gnirehtet", "Apple Music", "AWA", "JOOX", "Tidal", "📂 Otra APK..."], width=120)
        self.combo_apps.pack(side="left", padx=5)
        
        self.btn_install_apk = ctk.CTkButton(btn_f1, text="📦 Instalar", fg_color="#D97706", hover_color="#B45309", command=self.action_install_apk)
        self.btn_install_apk.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # --- PASO 2: GESTIÓN DE PROXIES ---
        f_step2 = ctk.CTkFrame(left_panel, fg_color="#1E293B", corner_radius=8, border_color="#F59E0B", border_width=1)
        f_step2.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(f_step2, text="PASO 2: PROXIES Y RED", font=("Arial", 14, "bold"), text_color="#FCD34D").pack(pady=(10, 0))
        ctk.CTkLabel(f_step2, text="💡 Consejo: Pegá tus Proxies. Luego probá cuáles están vivos para evitar que los celulares se queden sin internet.", font=("Arial", 10), text_color="#94A3B8").pack()
        
        # Caja de Proxies más pequeña
        self.txt_proxies = ctk.CTkTextbox(f_step2, height=70)
        self.txt_proxies.pack(fill="x", padx=15, pady=5)
        
        # Botones de Proxy
        prx_btn_f = ctk.CTkFrame(f_step2, fg_color="transparent")
        prx_btn_f.pack(fill="x", padx=15, pady=(0, 10))
        
        self.btn_test_prx = ctk.CTkButton(prx_btn_f, text="🧪 Probar Proxies", fg_color="#D97706", hover_color="#B45309", width=110, command=self.action_test_proxies)
        self.btn_test_prx.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(prx_btn_f, text="💾 Guardar", fg_color="#059669", width=80, command=self._save_config).pack(side="left", padx=5)
        ctk.CTkButton(prx_btn_f, text="🗑️ Borrar", fg_color="#475569", width=80, command=lambda: self.txt_proxies.delete("1.0", "end")).pack(side="left", padx=5)
        
        self.lbl_prx_status = ctk.CTkLabel(prx_btn_f, text="", font=("Arial", 11, "bold"), text_color="#10B981")
        self.lbl_prx_status.pack(side="right", padx=5)
        
        # --- PASO 3: CREAR TÚNEL ---
        f_step3 = ctk.CTkFrame(left_panel, fg_color="#1E293B", corner_radius=8, border_color="#10B981", border_width=1)
        f_step3.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(f_step3, text="PASO 3: ABRIR TÚNEL DE INTERNET", font=("Arial", 14, "bold"), text_color="#34D399").pack(pady=(10, 0))
        ctk.CTkLabel(f_step3, text="💡 Consejo: Esto le dará internet a los celulares usando los Proxies vivos. Esperá el OK verde.", font=("Arial", 10), text_color="#94A3B8").pack()
        
        lote_frame = ctk.CTkFrame(f_step3, fg_color="transparent")
        lote_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(lote_frame, text="Cantidad a usar (Lote):").pack(side="left")
        self.batch_var = ctk.StringVar(value="Todos")
        ctk.CTkComboBox(lote_frame, values=["1", "2", "3", "5", "Todos"], variable=self.batch_var, width=80).pack(side="left", padx=5)
        
        start_frame = ctk.CTkFrame(f_step3, fg_color="transparent")
        start_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.btn_start = ctk.CTkButton(start_frame, text="🚀 ABRIR TÚNEL", fg_color="#10B981", hover_color="#059669", height=35, command=self.action_start_tunnel)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_stop = ctk.CTkButton(start_frame, text="🛑 Cerrar Túnel", fg_color="#EF4444", hover_color="#DC2626", height=35, command=self.action_stop_tunnel, state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self.chk_wifi_var = ctk.BooleanVar(value=False)
        self.chk_wifi = ctk.CTkCheckBox(f_step3, text="📶 Ignorar Proxies y usar solo el WiFi nativo del celular", variable=self.chk_wifi_var)
        self.chk_wifi.pack(pady=(0, 10))
        
        # --- SELECTOR DE MODO (MANUAL vs PILOTO) ---
        mode_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(0, 10))
        
        self.mode_var = ctk.StringVar(value="Modo Manual")
        self.seg_mode = ctk.CTkSegmentedButton(mode_frame, values=["🛠️ Modo Manual", "🤖 Piloto Automático"], variable=self.mode_var, command=self._on_mode_change)
        self.seg_mode.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_creador = ctk.CTkButton(mode_frame, text="👤 Gestor de Cuentas", fg_color="#D946EF", hover_color="#C026D3", width=150, command=self.open_creador)
        self.btn_creador.pack(side="right")
        
        # --- CAJAS DE TEXTO (SIEMPRE VISIBLES) ---
        f_boxes = ctk.CTkFrame(left_panel, fg_color="#1E1E1E", corner_radius=8, border_color="#334155", border_width=1)
        f_boxes.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(f_boxes, text="LISTAS DE REPRODUCCIÓN", font=("Arial", 14, "bold"), text_color="#A5B4FC").pack(pady=(10, 0))
        ctk.CTkLabel(f_boxes, text="💡 Pegá tus enlaces acá. El sistema borrará la basura y extraerá los links automáticamente.", font=("Arial", 10), text_color="#94A3B8").pack()
        
        cajas_frame = ctk.CTkScrollableFrame(f_boxes, fg_color="transparent", height=220)
        cajas_frame.pack(fill="x", padx=10, pady=10)
        
        sp_f = ctk.CTkFrame(cajas_frame, fg_color="#064E3B", corner_radius=5)
        sp_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(sp_f, text="🟢 Spotify", font=("Arial", 11, "bold")).pack()
        self.txt_sp = ctk.CTkTextbox(sp_f, height=50)
        self.txt_sp.pack(fill="x", padx=4, pady=4)
        
        yt_f = ctk.CTkFrame(cajas_frame, fg_color="#7F1D1D", corner_radius=5)
        yt_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(yt_f, text="🔴 YouTube", font=("Arial", 11, "bold")).pack()
        self.txt_yt = ctk.CTkTextbox(yt_f, height=50)
        self.txt_yt.pack(fill="x", padx=4, pady=4)
        
        ym_f = ctk.CTkFrame(cajas_frame, fg_color="#4A044E", corner_radius=5)
        ym_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(ym_f, text="🟣 YT Music", font=("Arial", 11, "bold")).pack()
        self.txt_ym = ctk.CTkTextbox(ym_f, height=50)
        self.txt_ym.pack(fill="x", padx=4, pady=4)
        
        am_f = ctk.CTkFrame(cajas_frame, fg_color="#9D174D", corner_radius=5)
        am_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(am_f, text="🍎 Apple Music", font=("Arial", 11, "bold")).pack()
        self.txt_am = ctk.CTkTextbox(am_f, height=50)
        self.txt_am.pack(fill="x", padx=4, pady=4)
        
        ti_f = ctk.CTkFrame(cajas_frame, fg_color="#1E293B", corner_radius=5)
        ti_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(ti_f, text="🌊 Tidal", font=("Arial", 11, "bold")).pack()
        self.txt_ti = ctk.CTkTextbox(ti_f, height=50)
        self.txt_ti.pack(fill="x", padx=4, pady=4)

        awa_f = ctk.CTkFrame(cajas_frame, fg_color="#F43F5E", corner_radius=5)
        awa_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(awa_f, text="🌸 AWA", font=("Arial", 11, "bold")).pack()
        self.txt_awa = ctk.CTkTextbox(awa_f, height=50)
        self.txt_awa.pack(fill="x", padx=4, pady=4)
        
        ki_f = ctk.CTkFrame(cajas_frame, fg_color="#00FF00", corner_radius=5)
        ki_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(ki_f, text="🟩 Kick", font=("Arial", 11, "bold"), text_color="black").pack()
        self.txt_kick = ctk.CTkTextbox(ki_f, height=50)
        self.txt_kick.pack(fill="x", padx=4, pady=4)
        
        tw_f = ctk.CTkFrame(cajas_frame, fg_color="#9146FF", corner_radius=5)
        tw_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(tw_f, text="🟣 Twitch", font=("Arial", 11, "bold"), text_color="white").pack()
        self.txt_twitch = ctk.CTkTextbox(tw_f, height=50)
        self.txt_twitch.pack(fill="x", padx=4, pady=4)
        
        yts_f = ctk.CTkFrame(cajas_frame, fg_color="#EA580C", corner_radius=5)
        yts_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(yts_f, text="📱 YT Shorts", font=("Arial", 11, "bold")).pack()
        self.txt_yts = ctk.CTkTextbox(yts_f, height=50)
        self.txt_yts.pack(fill="x", padx=4, pady=4)
        
        # --- NUEVA CAJA: CANCIONES SUELTAS ---
        sin_f = ctk.CTkFrame(cajas_frame, fg_color="#1E3A8A", corner_radius=5)
        sin_f.pack(side="top", fill="x", expand=True, pady=3)
        ctk.CTkLabel(sin_f, text="🎵 Canciones Sueltas", font=("Arial", 11, "bold")).pack()
        self.txt_singles = ctk.CTkTextbox(sin_f, height=50)
        self.txt_singles.pack(fill="x", padx=4, pady=4)

        
        btn_action_f = ctk.CTkFrame(f_boxes, fg_color="transparent")
        btn_action_f.pack(pady=(0, 10), fill="x", padx=10)
        
        ctk.CTkButton(btn_action_f, text="🗑️ Borrar", fg_color="#475569", width=80, command=self.action_clear_lists).pack(side="left", padx=5)
        ctk.CTkButton(btn_action_f, text="💾 Guardar", fg_color="#059669", hover_color="#047857", width=80, command=self._save_config).pack(side="left", padx=5)
        
        self.ghost_enabled = ctk.BooleanVar(value=False)
        self.chk_ghost = ctk.CTkCheckBox(btn_action_f, text="👻 Fantasma", variable=self.ghost_enabled)
        self.chk_ghost.pack(side="right", padx=5)
        
        self.skip_enabled = ctk.BooleanVar(value=False)
        self.chk_skip = ctk.CTkCheckBox(btn_action_f, text="⏭️ Saltos (2h+)", variable=self.skip_enabled)
        self.chk_skip.pack(side="right", padx=5)
        
        # --- PASO 4: CONTROLES MANUALES ---
        self.f_man = ctk.CTkFrame(left_panel, fg_color="#1E1E1E", corner_radius=8, border_color="#8B5CF6", border_width=1)
        self.f_man.pack(fill="x", pady=(0, 10))
        
        lbl_man = ctk.CTkLabel(self.f_man, text="Controles Manuales", font=("Arial", 14, "bold"), text_color="#A78BFA")
        lbl_man.pack(pady=5)
        
        list_btn_f = ctk.CTkScrollableFrame(self.f_man, fg_color="transparent", height=150)
        list_btn_f.pack(fill="x", padx=10, pady=5)
        
        self.manual_btns = []
        btn1 = ctk.CTkButton(list_btn_f, text="▶ Spotify", fg_color="#10B981", command=lambda: self.action_manual_inject("spotify"))
        btn1.pack(side="top", fill="x", pady=3)
        btn2 = ctk.CTkButton(list_btn_f, text="▶ YouTube", fg_color="#EF4444", command=lambda: self.action_manual_inject("youtube"))
        btn2.pack(side="top", fill="x", pady=3)
        btn3 = ctk.CTkButton(list_btn_f, text="▶ YT Music", fg_color="#8B5CF6", command=lambda: self.action_manual_inject("ytmusic"))
        btn3.pack(side="top", fill="x", pady=3)
        btn4 = ctk.CTkButton(list_btn_f, text="▶ Apple Music", fg_color="#BE185D", command=lambda: self.action_manual_inject("applemusic"))
        btn4.pack(side="top", fill="x", pady=3)
        btn5 = ctk.CTkButton(list_btn_f, text="▶ TIDAL", fg_color="#334155", command=lambda: self.action_manual_inject("tidal"))
        btn5.pack(side="top", fill="x", pady=3)
        btn6 = ctk.CTkButton(list_btn_f, text="▶ AWA", fg_color="#F43F5E", command=lambda: self.action_manual_inject("awa"))
        btn6.pack(side="top", fill="x", pady=3)
        btn7 = ctk.CTkButton(list_btn_f, text="▶ YT Shorts", fg_color="#EA580C", command=lambda: self.action_manual_inject("ytshorts"))
        btn7.pack(side="top", fill="x", pady=3)
        
        btn8 = ctk.CTkButton(list_btn_f, text="🟩 Kick", fg_color="#10B981", command=lambda: self.action_manual_inject("kick"))
        btn8.pack(side="top", fill="x", pady=3)
        
        btn9 = ctk.CTkButton(list_btn_f, text="🟣 Twitch", fg_color="#9146FF", command=lambda: self.action_manual_inject("twitch"))
        btn9.pack(side="top", fill="x", pady=3)
        
        btn_clone = ctk.CTkButton(list_btn_f, text="🧬 Clonar SP", fg_color="#047857", command=self.action_manual_clone)
        btn_clone.pack(side="top", fill="x", pady=3)
        
        self.manual_btns.extend([btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn_clone])
        
        ctrl_f = ctk.CTkFrame(self.f_man, fg_color="transparent")
        ctrl_f.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ctrl_f, text="Vel. Inyección:").pack(side="left", padx=(15, 5))
        self.drip_var = ctk.StringVar(value="rápido")
        self.seg_drip = ctk.CTkSegmentedButton(ctrl_f, values=["apagado", "rápido", "lento"], variable=self.drip_var)
        self.seg_drip.pack(side="left", padx=5)
        
        ctk.CTkButton(ctrl_f, text="🛑 CANCELAR INYECCIÓN", fg_color="#991B1B", command=self.action_cancel_inject).pack(side="right", padx=15)
        
        # --- PASO 5: MODO PILOTO AUTOMÁTICO ---
        self.f_auto = ctk.CTkFrame(left_panel, fg_color="#312E81", corner_radius=8, border_color="#8B5CF6", border_width=1)
        # f_auto no se hace pack() inicialmente, arranca oculto
        
        # Cabecera de Paso 5 fija (Watchdog siempre visible)
        head_auto = ctk.CTkFrame(self.f_auto, fg_color="transparent")
        head_auto.pack(fill="x", padx=10, pady=5)
        lbl_auto = ctk.CTkLabel(head_auto, text="Paso 5: Piloto Automático", font=("Arial", 14, "bold"), text_color="#A78BFA")
        lbl_auto.pack(side="left")
        
        self.chk_watchdog_var = ctk.BooleanVar(value=False)
        self.chk_watchdog = ctk.CTkCheckBox(head_auto, text="🛡️ Watchdog", variable=self.chk_watchdog_var, command=self._on_watchdog_toggle)
        self.chk_watchdog.pack(side="right")
        
        # Opciones en scroll ("de a 1 bajando")
        timers_f = ctk.CTkScrollableFrame(self.f_auto, fg_color="transparent", height=150)
        timers_f.pack(fill="x", padx=10, pady=5)
        
        def _make_timer_row(parent, label_text):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label_text, width=90, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=60)
            entry.pack(side="left", padx=5)
            entry.insert(0, "0")
            ctk.CTkLabel(row, text="minutos").pack(side="left")
            return entry
            
        self.sp_m = _make_timer_row(timers_f, "🟢 Spotify")
        self.yt_m = _make_timer_row(timers_f, "🔴 YouTube")
        self.ytm_m = _make_timer_row(timers_f, "🟣 YT Music")
        self.am_m = _make_timer_row(timers_f, "🍎 Apple M.")
        self.ti_m = _make_timer_row(timers_f, "🌊 Tidal")
        self.awa_m = _make_timer_row(timers_f, "🌸 AWA")
        self.kick_m = _make_timer_row(timers_f, "🟩 Kick")
        self.twitch_m = _make_timer_row(timers_f, "🟣 Twitch")
        self.yts_m = _make_timer_row(timers_f, "📱 YT Shorts")
        self.mix_m = _make_timer_row(timers_f, "🌪️ MODO MIX")
        self.singles_m = _make_timer_row(timers_f, "⏱️ Canción Suelta")
        
        # Opciones de Shorts
        shorts_opt_f = ctk.CTkFrame(self.f_auto, fg_color="transparent")
        shorts_opt_f.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(shorts_opt_f, text="Opción Especial de Shorts:", font=("Arial", 11, "bold"), text_color="#EA580C").pack(anchor="w")
        
        row_s = ctk.CTkFrame(shorts_opt_f, fg_color="transparent")
        row_s.pack(fill="x")
        ctk.CTkLabel(row_s, text="Swipe min:").pack(side="left")
        self.yts_min = ctk.CTkEntry(row_s, width=40)
        self.yts_min.pack(side="left", padx=2)
        self.yts_min.insert(0, "45")
        ctk.CTkLabel(row_s, text="max:").pack(side="left")
        self.yts_max = ctk.CTkEntry(row_s, width=40)
        self.yts_max.pack(side="left", padx=2)
        self.yts_max.insert(0, "120")
        ctk.CTkLabel(row_s, text="seg").pack(side="left")
        
        self.chk_yts_like_var = ctk.BooleanVar(value=True)
        self.chk_yts_save_var = ctk.BooleanVar(value=True)
        self.chk_yts_comment_var = ctk.BooleanVar(value=True)
        self.chk_yts_share_var = ctk.BooleanVar(value=True)
        row_s2 = ctk.CTkFrame(shorts_opt_f, fg_color="transparent")
        row_s2.pack(fill="x", pady=(5,0))
        
        self.chk_yts_like = ctk.CTkCheckBox(row_s2, text="Like", variable=self.chk_yts_like_var, width=10)
        self.chk_yts_like.pack(side="left", padx=5)
        self.chk_yts_save = ctk.CTkCheckBox(row_s2, text="Guardar", variable=self.chk_yts_save_var, width=10)
        self.chk_yts_save.pack(side="left", padx=5)
        self.chk_yts_comment = ctk.CTkCheckBox(row_s2, text="Comentar", variable=self.chk_yts_comment_var, width=10)
        self.chk_yts_comment.pack(side="left", padx=5)
        self.chk_yts_share = ctk.CTkCheckBox(row_s2, text="Compartir", variable=self.chk_yts_share_var, width=10)
        self.chk_yts_share.pack(side="left", padx=5)
        
        # Opciones de Kick
        kick_opt_f = ctk.CTkFrame(self.f_auto, fg_color="transparent")
        kick_opt_f.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(kick_opt_f, text="Opciones de Kick:", font=("Arial", 11, "bold"), text_color="#00FF00").pack(anchor="w")
        
        self.chk_kick_text_var = ctk.BooleanVar(value=True)
        self.chk_kick_emoji_var = ctk.BooleanVar(value=True)
        
        row_k = ctk.CTkFrame(kick_opt_f, fg_color="transparent")
        row_k.pack(fill="x")
        self.chk_kick_text = ctk.CTkCheckBox(row_k, text="Comentar (Texto)", variable=self.chk_kick_text_var, width=10)
        self.chk_kick_text.pack(side="left", padx=5)
        self.chk_kick_emoji = ctk.CTkCheckBox(row_k, text="Emojis", variable=self.chk_kick_emoji_var, width=10)
        self.chk_kick_emoji.pack(side="left", padx=5)
        
        row_k_int = ctk.CTkFrame(kick_opt_f, fg_color="transparent")
        row_k_int.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(row_k_int, text="Frecuencia de chat (min):").pack(side="left")
        self.kick_interval = ctk.CTkEntry(row_k_int, width=40)
        self.kick_interval.pack(side="left", padx=5)
        self.kick_interval.insert(0, "5") # Default 5 mins
        
        ctk.CTkLabel(kick_opt_f, text="📝 Comentarios Personalizados (uno por línea):", text_color="#A3E635").pack(anchor="w", pady=(5,0))
        self.txt_kick_comments = ctk.CTkTextbox(kick_opt_f, height=80)
        self.txt_kick_comments.pack(fill="x", padx=5, pady=2)
        
        # Opciones de Twitch
        twitch_opt_f = ctk.CTkFrame(self.f_auto, fg_color="transparent")
        twitch_opt_f.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(twitch_opt_f, text="Opciones de Twitch:", font=("Arial", 11, "bold"), text_color="#D8B4FE").pack(anchor="w")
        
        self.chk_twitch_text_var = ctk.BooleanVar(value=False)
        self.chk_twitch_emoji_var = ctk.BooleanVar(value=False)
        
        row_tw = ctk.CTkFrame(twitch_opt_f, fg_color="transparent")
        row_tw.pack(fill="x")
        self.chk_twitch_text = ctk.CTkCheckBox(row_tw, text="Comentar (Desactivado)", variable=self.chk_twitch_text_var, width=10, state="disabled", text_color="gray")
        self.chk_twitch_text.pack(side="left", padx=5)
        self.chk_twitch_emoji = ctk.CTkCheckBox(row_tw, text="Emojis (Desactivado)", variable=self.chk_twitch_emoji_var, width=10, state="disabled", text_color="gray")
        self.chk_twitch_emoji.pack(side="left", padx=5)
        
        row_tw_int = ctk.CTkFrame(twitch_opt_f, fg_color="transparent")
        row_tw_int.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(row_tw_int, text="Frecuencia de chat (min):").pack(side="left")
        self.twitch_interval = ctk.CTkEntry(row_tw_int, width=40)
        self.twitch_interval.pack(side="left", padx=5)
        self.twitch_interval.insert(0, "5") # Default 5 mins
        
        ctk.CTkLabel(twitch_opt_f, text="💬 Comentarios Personalizados (uno por línea):", text_color="#E9D5FF").pack(anchor="w", pady=(5,0))
        self.txt_twitch_comments = ctk.CTkTextbox(twitch_opt_f, height=80, state="disabled", text_color="gray")
        self.txt_twitch_comments.pack(fill="x", padx=5, pady=2)
        
        row_s3 = ctk.CTkFrame(shorts_opt_f, fg_color="transparent")
        auto_ctrl = ctk.CTkFrame(self.f_auto, fg_color="transparent")
        auto_ctrl.pack(fill="x", padx=10, pady=10)
        
        self.btn_auto_start = ctk.CTkButton(auto_ctrl, text="▶ INICIAR PILOTO", fg_color="#10B981", command=self.action_start_pilot)
        self.btn_auto_start.pack(side="left", expand=True, padx=5)
        self.btn_auto_pause = ctk.CTkButton(auto_ctrl, text="⏸ Pausar", fg_color="#F59E0B", state="disabled", command=self.action_pause_pilot)
        self.btn_auto_pause.pack(side="left", expand=True, padx=5)
        self.btn_auto_stop = ctk.CTkButton(auto_ctrl, text="⏹ Detener", fg_color="#EF4444", state="disabled", command=self.action_stop_pilot)
        self.btn_auto_stop.pack(side="left", expand=True, padx=5)
        
        self.lbl_pilot_status = ctk.CTkLabel(self.f_auto, text="Piloto Detenido", text_color="#94A3B8")
        self.lbl_pilot_status.pack(pady=(0, 5))
        
        # PANEL DERECHO (Monitor y Consola)
        right_panel = ctk.CTkFrame(self, fg_color="transparent", border_color="#F59E0B", border_width=3)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        right_panel.grid_columnconfigure(0, weight=1) # <--- AÑADIDO PARA QUE SE EXPANDA HORIZONTALMENTE
        right_panel.grid_rowconfigure(0, weight=3) # Monitor
        right_panel.grid_rowconfigure(1, weight=1) # Consola
        
        # --- MONITOR ---
        f_mon = ctk.CTkFrame(right_panel, fg_color="#0F172A", corner_radius=8)
        f_mon.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        top_mon = ctk.CTkFrame(f_mon, fg_color="transparent")
        top_mon.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(top_mon, text="🖥️ ESTADO EN VIVO", font=("Arial", 14, "bold"), text_color="#34D399").pack(side="left")
        
        tools_mon = ctk.CTkFrame(f_mon, fg_color="transparent")
        tools_mon.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_repair = ctk.CTkButton(tools_mon, text="🔧 Reconectar Caídos", fg_color="#F59E0B", width=130, command=self.action_repair_failed)
        self.btn_repair.pack(side="right", padx=(5, 0))

        self.btn_ping = ctk.CTkButton(tools_mon, text="📡 Ping Test", fg_color="#2563EB", hover_color="#1D4ED8", width=90, command=self.action_ping_test)
        self.btn_ping.pack(side="right", padx=(5, 0))
        
        self.chk_autorepair_var = ctk.BooleanVar(value=False)
        self.chk_autorepair = ctk.CTkCheckBox(tools_mon, text="Auto-Reconectar", variable=self.chk_autorepair_var)
        self.chk_autorepair.pack(side="right", padx=10)
        
        self.btn_reset_net = ctk.CTkButton(tools_mon, text="🧹 Limpiar Red", fg_color="#475569", hover_color="#334155", width=100, command=self.action_reset_network)
        self.btn_reset_net.pack(side="right")
        
        self.scroll_devs = ctk.CTkScrollableFrame(f_mon, fg_color="transparent")
        self.scroll_devs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # --- CONSOLA ---
        self.txt_log = ctk.CTkTextbox(right_panel, font=("Consolas", 12), text_color="#10B981", fg_color="#000000")
        self.txt_log.grid(row=1, column=0, sticky="nsew")
        self.txt_log.configure(state="disabled")
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # =========================================================================
    # LÓGICA CORE
    # =========================================================================
    def log_msg(self, msg, type="info"):
        def _write():
            self.txt_log.configure(state="normal")
            sym = "🟢" if type == "info" else "✅"
            if type == "warn": sym = "⚠️"
            if type == "error": sym = "🔴"
            ts = time.strftime("%H:%M:%S")
            self.txt_log.insert("end", f"[{ts}] {sym} {msg}\n")
            lines = int(self.txt_log.index("end-1c").split(".")[0])
            if lines > 500: self.txt_log.delete("1.0", f"{lines - 500}.0")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        self.after(0, _write)

    def _on_mode_change(self, selected_mode):
        if self.scheduler.is_running:
            self.log_msg("⚠️ No podés cambiar de modo mientras el Piloto está corriendo. Detenelo primero.", "error")
            self.mode_var.set("🤖 Piloto Automático") # Forzar vuelta atrás
            return
            
        if self.is_cleaning:
            self.log_msg("⏳ Esperá a que termine la limpieza antes de cambiar de modo.", "warn")
            self.mode_var.set(self.mode_var.get())
            return
            
        if selected_mode == "🛠️ Modo Manual":
            self.f_auto.pack_forget()
            self.f_man.pack(fill="x", pady=(0, 10))
            self.log_msg("🛠️ Cambiaste a Modo Manual (Inyección de 1 tiro).", "info")
        else:
            self.f_man.pack_forget()
            self.f_auto.pack(fill="x", pady=(0, 10))
            self.log_msg("🤖 Cambiaste a Piloto Automático (Bucle 24/7).", "info")

    def _on_watchdog_toggle(self):
        if self.scheduler.is_running:
            messagebox.showwarning("Bloqueado", "El Piloto ya está corriendo. Debes detenerlo primero para activar o desactivar el Watchdog.")
            self.chk_watchdog_var.set(not self.chk_watchdog_var.get())

    def _load_config(self):
        if not os.path.exists(self.config_file): return
        try:
            with open(self.config_file, "r") as f: d = json.load(f)
            if "proxies" in d: self.txt_proxies.insert("1.0", d["proxies"])
            if "sp_urls" in d: self.txt_sp.insert("1.0", d["sp_urls"])
            if "yt_urls" in d: self.txt_yt.insert("1.0", d["yt_urls"])
            if "ytm_urls" in d: self.txt_ym.insert("1.0", d["ytm_urls"])
            if "am_urls" in d: self.txt_am.insert("1.0", d["am_urls"])
            if "ti_urls" in d: self.txt_ti.insert("1.0", d["ti_urls"])
            if "awa_urls" in d: self.txt_awa.insert("1.0", d["awa_urls"])
            if "yts_urls" in d: self.txt_yts.insert("1.0", d["yts_urls"])
            if "batch" in d: self.batch_var.set(d["batch"])
            if "drip" in d: self.drip_var.set(d["drip"])
            if "sp_m" in d: self.sp_m.delete(0, "end"); self.sp_m.insert(0, str(d["sp_m"]))
            if "yt_m" in d: self.yt_m.delete(0, "end"); self.yt_m.insert(0, str(d["yt_m"]))
            if "ytm_m" in d: self.ytm_m.delete(0, "end"); self.ytm_m.insert(0, str(d["ytm_m"]))
            if "am_m" in d: self.am_m.delete(0, "end"); self.am_m.insert(0, str(d["am_m"]))
            if "ti_m" in d: self.ti_m.delete(0, "end"); self.ti_m.insert(0, str(d["ti_m"]))
            if "awa_m" in d: self.awa_m.delete(0, "end"); self.awa_m.insert(0, str(d["awa_m"]))
            if "kick_m" in d: self.kick_m.delete(0, "end"); self.kick_m.insert(0, str(d["kick_m"]))
            if "kick_urls" in d: self.txt_kick.delete("1.0", "end"); self.txt_kick.insert("1.0", d["kick_urls"])
            if "yts_m" in d: self.yts_m.delete(0, "end"); self.yts_m.insert(0, str(d["yts_m"]))
            if "mix_m" in d: self.mix_m.delete(0, "end"); self.mix_m.insert(0, str(d["mix_m"]))
            if "singles_m" in d: self.singles_m.delete(0, "end"); self.singles_m.insert(0, str(d["singles_m"]))
            if "singles_urls" in d: self.txt_singles.delete("1.0", "end"); self.txt_singles.insert("1.0", d["singles_urls"])
            if "yts_min" in d: self.yts_min.delete(0, "end"); self.yts_min.insert(0, str(d["yts_min"]))
            if "yts_max" in d: self.yts_max.delete(0, "end"); self.yts_max.insert(0, str(d["yts_max"]))
            if "yts_like" in d: self.chk_yts_like_var.set(d["yts_like"])
            if "yts_save" in d: self.chk_yts_save_var.set(d["yts_save"])
            if "yts_comment" in d: self.chk_yts_comment_var.set(d["yts_comment"])
            if "yts_share" in d: self.chk_yts_share_var.set(d["yts_share"])
            if "wifi_nativo" in d: self.chk_wifi_var.set(d["wifi_nativo"])
            if "watchdog" in d: self.chk_watchdog_var.set(d["watchdog"])
            if "ghost" in d: self.ghost_enabled.set(d["ghost"])
            if "skip" in d: self.skip_enabled.set(d["skip"])
            if "autorepair" in d: self.chk_autorepair_var.set(d["autorepair"])
        except: pass

    def _save_config(self):
        try:
            d = {
                "proxies": self.txt_proxies.get("1.0", "end").strip(),
                "sp_urls": self.txt_sp.get("1.0", "end").strip(),
                "yt_urls": self.txt_yt.get("1.0", "end").strip(),
                "ytm_urls": self.txt_ym.get("1.0", "end").strip(),
                "am_urls": self.txt_am.get("1.0", "end").strip(),
                "ti_urls": self.txt_ti.get("1.0", "end").strip(),
                "awa_urls": self.txt_awa.get("1.0", "end").strip(),
                "yts_urls": self.txt_yts.get("1.0", "end").strip(),
                "batch": self.batch_var.get(),
                "drip": self.drip_var.get(),
                "sp_m": self.sp_m.get(),
                "yt_m": self.yt_m.get(),
                "ytm_m": self.ytm_m.get(),
                "am_m": self.am_m.get(),
                "ti_m": self.ti_m.get(),
                "awa_m": self.awa_m.get(),
                "kick_m": self.kick_m.get(),
                "kick_urls": self.txt_kick.get("1.0", "end").strip(),
                "twitch_m": self.twitch_m.get(),
                "twitch_urls": self.txt_twitch.get("1.0", "end").strip(),
                "twitch_text": self.chk_twitch_text_var.get(),
                "twitch_emoji": self.chk_twitch_emoji_var.get(),
                "twitch_interval": self.twitch_interval.get(),
                "twitch_comments": self.txt_twitch_comments.get("1.0", "end").strip(),
                "kick_text": self.chk_kick_text_var.get(),
                "kick_emoji": self.chk_kick_emoji_var.get(),
                "kick_interval": self.kick_interval.get(),
                "kick_comments": self.txt_kick_comments.get("1.0", "end").strip(),
                "yts_m": self.yts_m.get(),
                "mix_m": self.mix_m.get(),
                "singles_m": self.singles_m.get(),
                "singles_urls": self.txt_singles.get("1.0", "end").strip(),
                "yts_min": self.yts_min.get(),
                "yts_max": self.yts_max.get(),
                "yts_like": self.chk_yts_like_var.get(),
            "yts_save": self.chk_yts_save_var.get(),
            "yts_comment": self.chk_yts_comment_var.get(),
            "yts_share": self.chk_yts_share_var.get(),
            "wifi_nativo": self.chk_wifi_var.get(),
                "watchdog": self.chk_watchdog_var.get(),
                "ghost": self.ghost_enabled.get(),
                "skip": self.skip_enabled.get(),
                "autorepair": self.chk_autorepair_var.get()
            }
            with open(self.config_file, "w") as f: json.dump(d, f)
            self.log_msg("Configuración guardada.", "success")
        except: pass

    def _on_closing(self):
        if self.tunnel.running or self.scheduler.is_running:
            if not messagebox.askyesno("Confirmar Cierre", "⚠️ Tenés el Túnel o el Piloto Automático encendidos.\n\n¿Estás seguro de que querés cerrar la aplicación? (Esto detendrá todos los procesos y desconectará a los celulares)."):
                return
                
        self.log_msg("Cerrando sistema, por favor espera...", "info")
        self.update() # Forzar dibujado del mensaje
        
        self._save_config()
        self.tunnel.stop_farm()
        self.scheduler.stop()
        self.monitor.stop()
        self.destroy()

    # --- PASO 1 ---
    def action_scan(self):
        self.cancel_autoboot()
        self.btn_scan.configure(state="disabled", text="⏳ Buscando...")
        def _do_scan():
            devices = self.adb.list_devices()
            self.scanned_devices = devices
            self.after(0, self._render_devices, devices)
            self.log_msg(f"Paso 1 Completado: {len(devices)} conectados. Avanzá al Paso 2.", "success")
        threading.Thread(target=_do_scan, daemon=True).start()

    def _render_devices(self, devices):
        self.btn_scan.configure(state="normal", text="🔍 Buscar Celulares")
        for widget in self.scroll_devs.winfo_children(): widget.destroy()
        self.device_ui_vars.clear()
        self.device_ui_cards.clear()
        
        for dev in devices:
            serial = dev["serial"]
            has_apk = dev.get("pkg_ok", False)
            
            card = ctk.CTkFrame(self.scroll_devs, fg_color="#1E1E1E", corner_radius=8, border_width=1, border_color="#333")
            card.pack(fill="x", pady=2, padx=2)
            var = tk.BooleanVar(value=True)
            self.device_ui_vars[serial] = var
            ctk.CTkCheckBox(card, text="", variable=var, width=20).pack(side="left", padx=10, pady=10)
            
            # Nombre y estado de APK
            apk_text = "📦 OK" if has_apk else "❌ SIN APK"
            apk_color = "#34D399" if has_apk else "#EF4444"
            
            info_f = ctk.CTkFrame(card, fg_color="transparent")
            info_f.pack(side="left", padx=5)
            ctk.CTkLabel(info_f, text=f"📱 {dev.get('model', 'Phone')} ({serial})", font=("Arial", 12, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_f, text=f"Gnirehtet: {apk_text}", font=("Arial", 10), text_color=apk_color).pack(anchor="w")
            
            lbl_health = ctk.CTkLabel(card, text="⭕ Esperando...", font=("Arial", 11, "bold"), text_color="#64748B")
            lbl_health.pack(side="right", padx=15)
            self.device_ui_cards[serial] = {"card": card, "health": lbl_health}

    def action_install_apk(self):
        app_name = self.combo_apps.get()
        target_path = ""
        is_split = False
        
        # Determinar qué dispositivos instalar
        if app_name == "Gnirehtet":
            objetivos = [d for d in self.scanned_devices if not d.get("pkg_ok", False)]
            if not objetivos:
                self.log_msg("✅ Todos los celulares ya tienen Gnirehtet instalado.", "success")
                return
        else:
            objetivos = [d for d in self.scanned_devices if self.device_ui_vars.get(d["serial"], tk.BooleanVar(value=False)).get()]
            if not objetivos:
                self.log_msg(f"⚠️ Seleccioná al menos un celular para instalar {app_name}.", "warn")
                return
                
        # Si eligió "Otra APK...", abrimos explorador de archivos
        if app_name == "📂 Otra APK...":
            from tkinter import filedialog, messagebox
            if messagebox.askyesno("Tipo de Instalación", "¿Vas a instalar un archivo .apk normal único?\n\n(Elegí 'No' si la aplicación viene dividida en varios archivos 'Split APK' dentro de una carpeta, como las que te pasé antes).", parent=self):
                target_path = filedialog.askopenfilename(parent=self, title="Seleccionar archivo APK", filetypes=[("Archivos APK", "*.apk")])
            else:
                target_path = filedialog.askdirectory(parent=self, title="Seleccionar Carpeta con Split APKs")
                is_split = True
                
            if not target_path:
                self.log_msg("⚠️ Instalación cancelada (no se seleccionó archivo/carpeta).", "warn")
                return
            app_name = os.path.basename(target_path) or "App Personalizada"
            
        self.btn_install_apk.configure(state="disabled", text="Instalando...")
        
        def _install():
            self.log_msg(f"📦 Instalando {app_name} en {len(objetivos)} celular(es)... (Puede tardar bastante)", "warn")
            for dev in objetivos:
                serial = dev["serial"]
                self.log_msg(f"[{serial[-4:]}] Transfiriendo {app_name}...", "info")
                
                success = False
                if target_path:
                    # Instalación Personalizada
                    if is_split:
                        success = self.adb.install_split_apk(serial, target_path)
                    else:
                        success = self.adb.install_apk(serial, target_path)
                elif app_name == "Gnirehtet":
                    success = self.adb.install_apk(serial, "gnirehtet.apk")
                elif app_name == "Apple Music":
                    base_path = "applemusic"
                    if not os.path.exists(base_path): base_path = r"C:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\applemusic"
                    success = self.adb.install_split_apk(serial, base_path)
                elif app_name == "AWA":
                    base_path = "awa"
                    if not os.path.exists(base_path): base_path = r"C:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\awa"
                    success = self.adb.install_split_apk(serial, base_path)
                elif app_name == "JOOX":
                    base_path = "joox"
                    if not os.path.exists(base_path): base_path = r"C:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\joox"
                    success = self.adb.install_split_apk(serial, base_path)
                elif app_name == "Tidal":
                    base_path = "tidal"
                    if not os.path.exists(base_path): base_path = r"C:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\tidal"
                    success = self.adb.install_split_apk(serial, base_path)
                    
                if success:
                    self.log_msg(f"[{serial[-4:]}] ✅ {app_name} instalado correctamente", "success")
                else:
                    self.log_msg(f"[{serial[-4:]}] ❌ Error al instalar {app_name} (Asegurate que la carpeta exista o revisá permisos)", "error")
                    
            self.after(0, lambda: self.btn_install_apk.configure(state="normal", text="📦 Instalar"))
            if self.combo_apps.get() == "Gnirehtet":
                self.action_scan() # Refrescar la vista solo si fue Gnirehtet
            
        threading.Thread(target=_install, daemon=True).start()

    # --- PASO 2 ---
    def action_test_proxies(self):
        self.cancel_autoboot()
        raw = self.txt_proxies.get("1.0", "end").strip().split('\n')
        proxies = [p.strip() for p in raw if p.strip() and not p.startswith("#")]
        
        if not proxies:
            self.log_msg("⚠️ La lista de proxies está vacía. Pegalos primero.", "warn")
            return
            
        self.btn_test_prx.configure(state="disabled", text="🧪 Probando...")
        self.lbl_prx_status.configure(text=f"Probando {len(proxies)}...")
        
        def _update(c, t, p, alive):
            pass # Para no saturar
            
        def _finish(results):
            def _gui():
                self.btn_test_prx.configure(state="normal", text="🧪 Probar Proxies")
                self.lbl_prx_status.configure(text=f"Vivos: {len(results['alive'])} | Muertos: {len(results['dead'])}")
                
                # Reemplazar texto con solo los vivos
                self.txt_proxies.delete("1.0", "end")
                self.txt_proxies.insert("end", f"# VIVOS ({len(results['alive'])}):\n")
                for p in results['alive']: self.txt_proxies.insert("end", p + "\n")
                
                if results['dead']:
                    self.txt_proxies.insert("end", f"\n# MUERTOS ({len(results['dead'])}):\n")
                    for p in results['dead']: self.txt_proxies.insert("end", "# " + p + "\n")
                    
                self.log_msg(f"Paso 2 Completado: Test de proxies listo ({len(results['alive'])} sirvieron). Avanzá al Paso 3.", "success")
                self._save_config()
            self.after(0, _gui)
            
        ProxyTester.test_proxies_async(proxies, _update, _finish)

    # --- PASO 3 ---
    def action_start_tunnel(self, force_empty_proxies=False):
        self.cancel_autoboot()
        selected = [d for d in self.scanned_devices if self.device_ui_vars.get(d["serial"], tk.BooleanVar(value=False)).get()]
        if not selected:
            if not force_empty_proxies:
                messagebox.showwarning("Sin Dispositivos", "Seleccioná al menos un celular en el monitor.")
            return
            
        usar_wifi = bool(self.chk_wifi.get())
        
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_scan.configure(state="disabled")
        
        if usar_wifi:
            # MODO WIFI NATIVO (SIN PROXY)
            self.log_msg("📶 Iniciando en Modo WiFi Nativo (Sin Túnel)", "warn")
            self.tunnel._running = True
            self.tunnel.active_devices = selected
            for ui in self.device_ui_cards.values():
                ui["health"].configure(text="🟢 WiFi OK", text_color="#10B981")
                ui["card"].configure(border_color="#064E3B")
            # En modo WiFi no arrancamos el Monitor de Gnirehtet porque no hay túnel tun0
        else:
            # MODO NORMAL CON PROXY Y GNIREHTET
            proxies_raw = self.txt_proxies.get("1.0", "end").strip().split('\n')
            proxies = [p.strip() for p in proxies_raw if p.strip() and not p.startswith("#")]
            if not proxies:
                if not force_empty_proxies:
                    if not messagebox.askyesno("Sin Proxies", "No hay proxies en la lista.\n\n¿Querés usar los túneles de Gnirehtet usando el Internet directo de esta PC?\n(Todos los celulares tendrán la IP de tu casa)"):
                        self.btn_start.configure(state="normal")
                        self.btn_stop.configure(state="disabled")
                        self.btn_scan.configure(state="normal")
                        return
                
            self.tunnel.start_farm(selected, proxies, batch_size=self.batch_var.get())
            self.monitor.start(lambda: self.tunnel.active_devices)
            
            # Forzar actualización inicial a OK (el monitor lo mantendrá)
            def _force_ok():
                time.sleep(10) # Esperar a que el túnel se levante
                if self.tunnel.running:
                    for dev in self.tunnel.active_devices:
                        self._on_device_alert(dev["serial"], "ok")
            threading.Thread(target=_force_ok, daemon=True).start()
            
        self.log_msg("Paso 3 en proceso... Esperá a que el semáforo se ponga en OK 🟢 para el Paso 4.", "info")

    def action_stop_tunnel(self):
        self.log_msg("🛑 Acción Manual: Cerrando Túneles...", "warn")
        self.tunnel.stop_farm()
        self.monitor.stop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.btn_scan.configure(state="normal")
        for ui in self.device_ui_cards.values():
            ui["health"].configure(text="⭕ Inactivo", text_color="#64748B")
            ui["card"].configure(border_color="#333")
        self.log_msg("✅ Túneles detenidos por completo de forma manual.", "success")
            
    def action_reset_network(self):
        self.cancel_autoboot()
        if not self.scanned_devices: return
        
        desinstalar = messagebox.askyesno("Limpieza Profunda", "¿Deseás también DESINSTALAR la aplicación de Gnirehtet de los celulares para dejarlos 100% limpios para usar WiFi libre?\n\n(Si elegís No, solo se borrará el proxy atascado).")
        
        self.log_msg("🧹 Limpiando configuraciones de red fantasma en los celulares...", "warn")
        
        def _clean():
            for dev in self.scanned_devices:
                serial = dev["serial"]
                self.log_msg(f"[{serial[-4:]}] Eliminando proxy global...", "info")
                self.adb.clear_global_proxy(serial)
                
                self.log_msg(f"[{serial[-4:]}] Apagando proceso Gnirehtet en memoria...", "info")
                self.adb.run_command(["shell", "am", "force-stop", "com.genymobile.gnirehtet"], serial)
                
                if desinstalar:
                    self.log_msg(f"[{serial[-4:]}] Desinstalando la APK de Gnirehtet...", "warn")
                    self.adb.run_command(["uninstall", "com.genymobile.gnirehtet"], serial)
                    dev["pkg_ok"] = False
                    
                self.log_msg(f"[{serial[-4:]}] ✅ Red de fábrica restaurada confirmada.", "success")
                
                def _update_ui(s=serial):
                    ui = self.device_ui_cards.get(s)
                    if ui:
                        ui["health"].configure(text="⭕ WiFi Libre", text_color="#94A3B8")
                        ui["card"].configure(border_color="#475569")
                self.after(0, _update_ui)
                
            self.log_msg("✅ Limpieza de Red completada. Dispositivos listos para WiFi nativo.", "success")
            if desinstalar:
                self.after(0, self.action_scan)
                
        threading.Thread(target=_clean, daemon=True).start()

    def action_repair_failed(self):
        failed = [s for s, st in self.monitor.get_all_status().items() if st in ("warning", "dead")]
        if not failed:
            self.log_msg("No hay dispositivos caídos para reparar.", "info")
            return
        def _repair():
            self.log_msg(f"🔧 Iniciando reparación por error de red en {len(failed)} celulares...", "warn")
            for serial in failed:
                success, msg = self.tunnel.reconnect_device(serial)
                if success:
                    self.monitor.reset_device(serial)
                    self.log_msg(f"[{serial[-4:]}] ✅ Reconexión forzada exitosa", "success")
                else:
                    self.log_msg(f"[{serial[-4:]}] ❌ Error en reparación: {msg}", "error")
        threading.Thread(target=_repair, daemon=True).start()

    def action_ping_test(self):
        activos = [d for d in self.scanned_devices if self.device_ui_vars.get(d["serial"], tk.BooleanVar(value=False)).get()]
        if not activos:
            self.log_msg("⚠️ Selecciona celulares primero.", "warn")
            return
            
        self.btn_ping.configure(state="disabled", text="Probando...")
        def _ping():
            self.log_msg(f"📡 Verificando conexión en {len(activos)} celulares...", "warn")
            for dev in activos:
                serial = dev["serial"]
                # 1. Verificar si tiene Gnirehtet encendido
                out, _, _ = self.adb.run_command(["shell", "ip", "addr", "show"], serial)
                has_tun = "tun" in out.lower() or "vpn" in out.lower() or "10.0.2." in out
                if has_tun:
                    self.log_msg(f"[{serial[-4:]}] ✅ Internet OK (Túnel Detectado)", "success")
                    self._on_device_alert(serial, "ok")
                    continue
                    
                # 2. Si no tiene túnel, hacer ping directo (WiFi)
                _, _, ping_code = self.adb.run_command(["shell", "ping", "-c", "1", "-W", "3", "8.8.8.8"], serial)
                if ping_code == 0:
                    self.log_msg(f"[{serial[-4:]}] ✅ Internet OK (WiFi Nativo)", "success")
                    self._on_device_alert(serial, "ok")
                else:
                    self.log_msg(f"[{serial[-4:]}] ❌ SIN INTERNET (Ping WiFi Falló)", "error")
                    self._on_device_alert(serial, "dead")
            self.after(0, lambda: self.btn_ping.configure(state="normal", text="📡 Ping Test"))
        threading.Thread(target=_ping, daemon=True).start()

    def _on_device_alert(self, serial, status):
        def _update():
            ui = self.device_ui_cards.get(serial)
            if not ui: return
            if status == "ok":
                ui["health"].configure(text="🟢 OK", text_color="#10B981")
                ui["card"].configure(border_color="#064E3B")
            elif status == "warning":
                ui["health"].configure(text="🟡 ALERTA", text_color="#F59E0B")
                ui["card"].configure(border_color="#78350F")
                self.log_msg(f"[{serial[-4:]}] ⚠️ Advertencia de red: la conexión parece lenta o inestable.", "warn")
            elif status == "dead":
                ui["health"].configure(text="🔴 CAÍDO", text_color="#EF4444")
                ui["card"].configure(border_color="#7F1D1D")
                self.log_msg(f"[{serial[-4:]}] ❌ ERROR CRÍTICO: Se perdió la conexión VPN de este celular.", "error")
                
                # AUTO-RECONECTAR SI ESTÁ ACTIVADO
                if getattr(self, "chk_autorepair_var", None) and self.chk_autorepair_var.get():
                    if not getattr(self, "is_repairing", False):
                        self.is_repairing = True
                        self.log_msg("🔄 Auto-Sanación Activada: Esperando 10 segundos antes de reconectar caídos...", "warn")
                        def _auto_trigger():
                            self.action_repair_failed()
                            self.is_repairing = False
                        self.after(10000, _auto_trigger)
                        
        self.after(0, _update)

    # --- PASO 4 ---
    def action_manual_clone(self):
        if self.is_cleaning:
            messagebox.showwarning("Limpiando", "Espera un momento, el sistema está limpiando procesos...")
            return
            
        if not self.tunnel.running or not self.tunnel.active_devices:
            self.log_msg("⚠️ Iniciá el túnel (Paso 3) con los celulares seleccionados.", "warn")
            return
            
        urls_crudas = self.txt_sp.get("1.0", "end").strip().split('\n')
        urls_validas = []
        for u in urls_crudas:
            u = u.strip()
            if not u: continue
            m = re.search(r'(https?://[^\s]+)', u)
            if m: urls_validas.append(m.group(1))
            
        if not urls_validas:
            self.log_msg("⚠️ No se encontraron links válidos en la caja de Spotify.", "warn")
            return
            
        # Podríamos usar el mismo popup de chulitos, pero como es riesgoso clonar 20 a la vez, 
        # directamente inyectamos aleatorio a todos los dispositivos.
        self.log_msg(f"🧬 Iniciando proceso de clonación en {len(self.tunnel.active_devices)} dispositivo(s)...", "warn")
        self.injector.cancel_all()
        self.injector.clone_spotify_batch(self.tunnel.active_devices, urls_validas)
        
    def action_manual_inject(self, mode):
        # ... validation ...
        if self.is_cleaning:
            messagebox.showwarning("Limpiando", "Espera un momento, el sistema está limpiando procesos colgados...")
            return
            
        if self.scheduler.is_running:
            messagebox.showwarning("Bloqueo de Seguridad", "El Piloto Automático está corriendo.\n\nPara usar el control manual y evitar choques, debés detener el Piloto primero (botón ⏹ Detener en el Paso 5).")
            return
            
        if not self.tunnel.running or not self.tunnel.active_devices:
            self.log_msg("⚠️ Completá el Paso 3 (Abrir Túnel) antes de inyectar.", "warn")
            return
            
        # --- DISPARO ---
        self.is_injecting_manual = True
        if mode == "spotify": t = self.txt_sp
        elif mode == "youtube": t = self.txt_yt
        elif mode == "ytmusic": t = self.txt_ym
        elif mode == "applemusic": t = self.txt_am
        elif mode == "tidal": t = self.txt_ti
        elif mode == "awa": t = self.txt_awa
        elif mode == "ytshorts": t = self.txt_yts
        elif mode == "kick": t = self.txt_kick
        elif mode == "twitch": t = self.txt_twitch
        
        raw_urls = t.get("1.0", "end").strip().split('\n')
        urls_validas = []
        for u in raw_urls:
            u = u.strip()
            if not u: continue
            match = re.search(r'(https?://[^\s]+)', u)
            if match:
                urls_validas.append(match.group(1))
            else:
                self.log_msg(f"⚠️ Saltando línea sin link: {u[:20]}...", "warn")
        
        if not urls_validas:
            self.log_msg(f"❌ No se encontró ningún enlace válido para {mode.upper()}.", "error")
            return
            
        # --- VENTANA EMERGENTE PARA SELECCIONAR CON CHULITOS ---
        popup = ctk.CTkToplevel(self)
        popup.title(f"Seleccionar Listas de {mode.capitalize()}")
        popup.geometry("600x400")
        popup.attributes("-topmost", True)
        popup.grab_set() # Foco obligatorio
        
        ctk.CTkLabel(popup, text=f"¿Qué listas querés inyectar en {mode.capitalize()}?", font=("Arial", 14, "bold")).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(popup, fg_color="#1E1E1E")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)
        
        vars_chulitos = []
        for url in urls_validas:
            # Mostrar solo el principio y fin para que no sea gigante
            display_url = url if len(url) < 60 else url[:30] + "..." + url[-20:]
            var = tk.BooleanVar(value=True) # Marcado por defecto
            vars_chulitos.append((var, url))
            
            chk = ctk.CTkCheckBox(scroll, text=display_url, variable=var, font=("Consolas", 11))
            chk.pack(anchor="w", padx=10, pady=5)
            
        def _confirmar_inyeccion():
            urls_finales = [u for v, u in vars_chulitos if v.get()]
            popup.destroy()
            
            if not urls_finales:
                self.log_msg("⚠️ Inyección cancelada: no seleccionaste ninguna lista.", "warn")
                return
                
            self.injector.cancel_all()
            drip = self.drip_var.get()
            devices = self.tunnel.active_devices
            
            self.log_msg(f"Paso 4: ¡Iniciando inyección manual en {len(devices)} dispositivo(s)! ({len(urls_finales)} listas seleccionadas)", "success")
            
            if mode == "spotify":
                self.injector.inject_spotify_batch(devices, urls_finales, drip_mode=drip)
            elif mode == "youtube":
                self.injector.inject_youtube_batch(devices, urls_finales, is_music=False, drip_mode=drip)
            elif mode == "ytmusic":
                self.injector.inject_youtube_batch(devices, urls_finales, is_music=True, drip_mode=drip)
            elif mode == "applemusic":
                self.injector.inject_apple_music_batch(devices, urls_finales, drip_mode=drip)
            elif mode == "tidal":
                self.injector.inject_tidal_batch(devices, urls_finales, drip_mode=drip)
            elif mode == "awa":
                self.injector.inject_awa_batch(devices, urls_finales, drip_mode=drip)
            elif mode == "ytshorts":
                try:
                    t_min = int(self.yts_min.get())
                    t_max = int(self.yts_max.get())
                except:
                    t_min, t_max = 45, 120
                do_like, do_save, do_comment, do_share, = self.chk_yts_like_var.get(), self.chk_yts_save_var.get(), self.chk_yts_comment_var.get(), self.chk_yts_share_var.get()
                self.injector.inject_ytshorts_batch(devices, urls_finales, t_min, t_max, do_like, do_save, do_comment, do_share, drip_mode=drip)
            elif mode == "kick":
                do_txt = self.chk_kick_text_var.get()
                do_emo = self.chk_kick_emoji_var.get()
                try:
                    k_interval = float(self.kick_interval.get())
                except:
                    k_interval = 5.0
                raw_comments = self.txt_kick_comments.get("1.0", "end").strip().split('\n')
                k_comments = [c.strip() for c in raw_comments if c.strip()]
                self.injector.inject_kick_batch(devices, urls_finales, do_text=do_txt, do_emojis=do_emo, chat_interval=k_interval, custom_comments=k_comments, drip_mode=drip)
            elif mode == "twitch":
                do_txt = self.chk_twitch_text_var.get()
                do_emo = self.chk_twitch_emoji_var.get()
                try:
                    tw_interval = float(self.twitch_interval.get())
                except:
                    tw_interval = 5.0
                raw_comments = self.txt_twitch_comments.get("1.0", "end").strip().split('\n')
                tw_comments = [c.strip() for c in raw_comments if c.strip()]
                self.injector.inject_twitch_batch(devices, urls_finales, do_text=do_txt, do_emojis=do_emo, chat_interval=tw_interval, custom_comments=tw_comments, drip_mode=drip)
                
        btn_f = ctk.CTkFrame(popup, fg_color="transparent")
        btn_f.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_f, text="✔️ Inyectar Seleccionadas", fg_color="#10B981", command=_confirmar_inyeccion).pack(side="left", expand=True, padx=10)
        ctk.CTkButton(btn_f, text="❌ Cancelar", fg_color="#991B1B", command=popup.destroy).pack(side="right", expand=True, padx=10)

    def action_clear_lists(self):
        self.txt_sp.delete("1.0", "end")
        self.txt_yt.delete("1.0", "end")
        self.txt_ym.delete("1.0", "end")
        self.log_msg("🗑️ Todas las listas de reproducción han sido borradas de la pantalla.", "info")

    def action_cancel_inject(self):
        self.log_msg("🛑 Cancelando y cerrando aplicaciones en los celulares...", "warn")
        self.injector.cancel_all()
        self.is_injecting_manual = False
        
        # Hilo para enviar el comando de muerte a todos los celulares
        def _kill_apps():
            if self.tunnel.active_devices:
                for dev in self.tunnel.active_devices:
                    self.injector._cleanup_apps(dev["serial"])
                    self.adb.run_command(["shell", "input", "keyevent", "3"], dev["serial"]) # Volver a inicio
                    self.adb.run_command(["shell", "svc", "wifi", "disable"], dev["serial"]) # 🔌 APAGAR WIFI DE EMERGENCIA
                self.log_msg("✅ Todas las apps (Spotify/YT) fueron cerradas de raíz.", "success")
        threading.Thread(target=_kill_apps, daemon=True).start()

    # --- PASO 5: PILOTO ---
    def action_start_pilot(self):
        # ... validation ...
        if self.is_cleaning:
            messagebox.showwarning("Limpiando", "Espera un momento, el sistema está limpiando procesos colgados...")
            return
            
        if not self.tunnel.running or not self.tunnel.active_devices:
            self.log_msg("⚠️ Iniciá el túnel (Paso 3) antes de arrancar el piloto.", "warn")
            return
            
        try:
            sp_s = int(float(self.sp_m.get()) * 60)
            yt_s = int(float(self.yt_m.get()) * 60)
            ytm_s = int(float(self.ytm_m.get()) * 60)
            am_s = int(float(self.am_m.get()) * 60)
            ti_s = int(float(self.ti_m.get()) * 60)
            awa_s = int(float(self.awa_m.get()) * 60)
            kick_s = int(float(self.kick_m.get()) * 60)
            twitch_s = int(float(self.twitch_m.get()) * 60)
            yts_s = int(float(self.yts_m.get()) * 60)
            mix_s = int(float(self.mix_m.get()) * 60)
            singles_s = int(float(self.singles_m.get()) * 60)
        except ValueError:
            messagebox.showerror("Error", "Los minutos deben ser números (ej: 30 o 45.5)")
            return
            
        drip = self.drip_var.get()
        
        def parse_urls(txt_widget):
            raw_urls = txt_widget.get("1.0", "end").strip().split('\n')
            urls = []
            for u in raw_urls:
                u = u.strip()
                if not u: continue
                match = re.search(r'(https?://[^\s]+)', u)
                if match: urls.append(match.group(1))
            return urls
        
        def fn_sp():
            urls = parse_urls(self.txt_sp)
            if urls: self.injector.inject_spotify_batch(self.tunnel.active_devices, urls, drip)
            
        def fn_yt():
            urls = parse_urls(self.txt_yt)
            if urls: self.injector.inject_youtube_batch(self.tunnel.active_devices, urls, is_music=False, drip_mode=drip)
            
        def fn_ytm():
            urls = parse_urls(self.txt_ym)
            if urls: self.injector.inject_youtube_batch(self.tunnel.active_devices, urls, is_music=True, drip_mode=drip)

        def fn_am():
            urls = parse_urls(self.txt_am)
            if urls: self.injector.inject_apple_music_batch(self.tunnel.active_devices, urls, drip_mode=drip)

        def fn_ti():
            urls = parse_urls(self.txt_ti)
            if urls: self.injector.inject_tidal_batch(self.tunnel.active_devices, urls, drip_mode=drip)

        def fn_kick():
            urls = parse_urls(self.txt_kick)
            do_txt = self.chk_kick_text_var.get()
            do_emo = self.chk_kick_emoji_var.get()
            try:
                k_interval = float(self.kick_interval.get())
            except:
                k_interval = 5.0
            raw_comments = self.txt_kick_comments.get("1.0", "end").strip().split('\n')
            k_comments = [c.strip() for c in raw_comments if c.strip()]
            if urls: self.injector.inject_kick_batch(self.tunnel.active_devices, urls, do_text=do_txt, do_emojis=do_emo, chat_interval=k_interval, custom_comments=k_comments, drip_mode=drip)
            
        def fn_awa():
            urls = parse_urls(self.txt_awa)
            if urls: self.injector.inject_awa_batch(self.tunnel.active_devices, urls, drip_mode=drip)
            
        def fn_twitch():
            urls = parse_urls(self.txt_twitch)
            do_txt = self.chk_twitch_text_var.get()
            do_emo = self.chk_twitch_emoji_var.get()
            try:
                tw_interval = float(self.twitch_interval.get())
            except:
                tw_interval = 5.0
            raw_comments = self.txt_twitch_comments.get("1.0", "end").strip().split('\n')
            tw_comments = [c.strip() for c in raw_comments if c.strip()]
            if urls: self.injector.inject_twitch_batch(self.tunnel.active_devices, urls, do_text=do_txt, do_emojis=do_emo, chat_interval=tw_interval, custom_comments=tw_comments, drip_mode=drip)
            
        def fn_yts():
            urls = parse_urls(self.txt_yts)
            if urls: 
                try:
                    t_min = int(self.yts_min.get())
                    t_max = int(self.yts_max.get())
                except:
                    t_min, t_max = 45, 120
                do_like, do_save, do_comment, do_share, = self.chk_yts_like_var.get(), self.chk_yts_save_var.get(), self.chk_yts_comment_var.get(), self.chk_yts_share_var.get()
                self.injector.inject_ytshorts_batch(self.tunnel.active_devices, urls, t_min, t_max, do_like, do_save, do_comment, do_share, drip_mode=drip)

        def fn_mix():
            import random
            urls_yt = parse_urls(self.txt_yt)
            urls_ytm = parse_urls(self.txt_ym)
            urls_yts = parse_urls(self.txt_yts)
            
            platforms = []
            if urls_yt: platforms.append("yt")
            if urls_ytm: platforms.append("ytm")
            if urls_yts: platforms.append("yts")
            
            if not platforms: return
            
            random.shuffle(platforms)
            devs = list(self.tunnel.active_devices)
            random.shuffle(devs)
            
            n = len(platforms)
            chunks = {p: [] for p in platforms}
            for i, d in enumerate(devs):
                chunks[platforms[i % n]].append(d)
                
            if "yts" in chunks and chunks["yts"]:
                try: t_min, t_max = int(self.yts_min.get()), int(self.yts_max.get())
                except: t_min, t_max = 45, 120
                do_like, do_save, do_comment, do_share = self.chk_yts_like_var.get(), self.chk_yts_save_var.get(), self.chk_yts_comment_var.get(), self.chk_yts_share_var.get()
                import time
                self.injector.inject_ytshorts_batch(chunks["yts"], urls_yts, t_min, t_max, do_like, do_save, do_comment, do_share, drip_mode=drip)
                time.sleep(2.5)
                
            if "ytm" in chunks and chunks["ytm"]:
                import time
                self.injector.inject_youtube_batch(chunks["ytm"], urls_ytm, is_music=True, drip_mode=drip)
                time.sleep(2.5)
                
            if "yt" in chunks and chunks["yt"]:
                self.injector.inject_youtube_batch(chunks["yt"], urls_yt, is_music=False, drip_mode=drip)

        # Solo agregar al ciclo las fases que tengan minutos > 0 Y que tengan links válidos
        phases = []
        if sp_s > 0 and parse_urls(self.txt_sp): phases.append(("Spotify", sp_s, fn_sp))
        if yt_s > 0 and parse_urls(self.txt_yt): phases.append(("YouTube", yt_s, fn_yt))
        if ytm_s > 0 and parse_urls(self.txt_ym): phases.append(("YT Music", ytm_s, fn_ytm))
        if am_s > 0 and parse_urls(self.txt_am): phases.append(("Apple Music", am_s, fn_am))
        if ti_s > 0 and parse_urls(self.txt_ti): phases.append(("Tidal", ti_s, fn_ti))
        if awa_s > 0 and parse_urls(self.txt_awa): phases.append(("AWA", awa_s, fn_awa))
        if kick_s > 0 and parse_urls(self.txt_kick): phases.append(("Kick", kick_s, fn_kick))
        if twitch_s > 0 and parse_urls(self.txt_twitch): phases.append(("Twitch", twitch_s, fn_twitch))
        if yts_s > 0 and parse_urls(self.txt_yts): phases.append(("YT Shorts", yts_s, fn_yts))
        if mix_s > 0 and (parse_urls(self.txt_yt) or parse_urls(self.txt_ym) or parse_urls(self.txt_yts)): phases.append(("Modo MIX", mix_s, fn_mix))

        # --- LOGICA DE ENTRE-TIEMPO (CANCIONES SUELTAS) ---
        singles_urls = parse_urls(self.txt_singles)
        if singles_s > 0 and singles_urls and phases:
            def make_single_fn(u):
                def fn():
                    if "spotify.com" in u:
                        self.injector.inject_spotify_batch(self.tunnel.active_devices, [u], drip_mode=drip)
                    elif "music.youtube.com" in u:
                        self.injector.inject_youtube_batch(self.tunnel.active_devices, [u], is_music=True, drip_mode=drip)
                    elif "youtube.com" in u or "youtu.be" in u:
                        self.injector.inject_youtube_batch(self.tunnel.active_devices, [u], is_music=False, drip_mode=drip)
                    elif "apple.com" in u:
                        self.injector.inject_apple_music_batch(self.tunnel.active_devices, [u], drip_mode=drip)
                    elif "tidal.com" in u:
                        self.injector.inject_tidal_batch(self.tunnel.active_devices, [u], drip_mode=drip)
                    elif "kick.com" in u:
                        self.injector.inject_kick_batch(self.tunnel.active_devices, [u], drip_mode=drip)
                    elif "twitch.tv" in u:
                        self.injector.inject_twitch_batch(self.tunnel.active_devices, [u], drip_mode=drip)
                    elif "awa.fm" in u or "awa" in u:
                        self.injector.inject_awa_batch(self.tunnel.active_devices, [u], drip_mode=drip)
                return fn
            
            interleaved_phases = []
            for p in phases:
                interleaved_phases.append(p)
                for i, su in enumerate(singles_urls):
                    interleaved_phases.append((f"Entre-Tiempo (Single {i+1})", singles_s, make_single_fn(su)))
            phases = interleaved_phases
        # --------------------------------------------------
        
        if not phases:
            messagebox.showwarning("Piloto Vacío", "No hay nada que reproducir.\n\nAsegurate de poner al menos 1 minuto en alguna plataforma y pegar links válidos en sus cajas.")
            return
            
        def watchdog_check(phase_name):
            pkg = ""
            if phase_name == "Spotify": pkg = "com.spotify.music"
            elif phase_name == "YouTube": pkg = "com.google.android.youtube"
            elif phase_name == "YT Music": pkg = "com.google.android.apps.youtube.music"
            elif phase_name == "Apple Music": pkg = "com.apple.android.music"
            elif phase_name == "Tidal": pkg = "com.aspiro.tidal"
            elif phase_name == "AWA": pkg = "fm.awa.liverpool"
            elif phase_name == "Kick": pkg = "com.kick.mobile"
            elif phase_name == "Twitch": pkg = "tv.twitch.android.app"
            elif phase_name == "YT Shorts": pkg = "com.google.android.youtube"
            elif phase_name == "Modo MIX": pkg = "com.google.android"
            
            if not pkg: return
            
            for dev in self.tunnel.active_devices:
                serial = dev["serial"]
                out, _, _ = self.adb.run_command(["shell", "dumpsys", "window", "windows"], serial)
                if pkg not in out:
                    self.log_msg(f"🛡️ [{serial[-4:]}] ¡Crasheo detectado en {phase_name}! Rescatando dispositivo...", "error")
                    if phase_name == "Spotify":
                        urls = parse_urls(self.txt_sp)
                        if urls: self.injector.inject_spotify_batch([dev], urls, "apagado")
                    elif phase_name == "YouTube":
                        urls = parse_urls(self.txt_yt)
                        if urls: self.injector.inject_youtube_batch([dev], urls, is_music=False, drip_mode="apagado")
                    elif phase_name == "YT Music":
                        urls = parse_urls(self.txt_ym)
                        if urls: self.injector.inject_youtube_batch([dev], urls, is_music=True, drip_mode="apagado")
                    elif phase_name == "Apple Music":
                        urls = parse_urls(self.txt_am)
                        if urls: self.injector.inject_apple_music_batch([dev], urls, drip_mode="apagado")
                    elif phase_name == "Tidal":
                        urls = parse_urls(self.txt_ti)
                        if urls: self.injector.inject_tidal_batch([dev], urls, drip_mode="apagado")
                    elif phase_name == "AWA":
                        urls = parse_urls(self.txt_awa)
                        if urls: self.injector.inject_awa_batch([dev], urls, drip_mode="apagado")
                    elif phase_name == "YT Shorts":
                        urls = parse_urls(self.txt_yts)
                        if urls: 
                            try:
                                t_min = int(self.yts_min.get())
                                t_max = int(self.yts_max.get())
                            except:
                                t_min, t_max = 45, 120
                            do_like, do_save, do_comment, do_share, = self.chk_yts_like_var.get(), self.chk_yts_save_var.get(), self.chk_yts_comment_var.get(), self.chk_yts_share_var.get()
                            self.injector.inject_ytshorts_batch([dev], urls, t_min, t_max, do_like, do_save, do_comment, do_share, drip_mode="apagado")
                    time.sleep(3)
        
        self.log_msg(f"▶️ Iniciando Piloto Automático con {len(phases)} plataforma(s) en rotación.", "success")
        self.injector.cancel_all()
        self.scheduler.start(phases, use_watchdog=self.chk_watchdog_var.get(), watchdog_fn=watchdog_check)
        
        for btn in self.manual_btns:
            btn.configure(state="disabled")
            
        self.btn_auto_start.configure(state="disabled")
        self.btn_auto_pause.configure(state="normal", text="⏸ Pausar")
        self.btn_auto_stop.configure(state="normal")
        self._save_config()

    def action_pause_pilot(self):
        if self.scheduler.is_paused:
            self.scheduler.resume()
            self.log_msg("▶️ Piloto Reanudado manualmente.", "info")
            self.btn_auto_pause.configure(text="⏸ Pausar")
        else:
            self.scheduler.pause()
            self.log_msg("⏸️ Piloto Pausado manualmente.", "warn")
            self.btn_auto_pause.configure(text="▶ Reanudar")

    def action_stop_pilot(self):
        if self.is_cleaning: return
        self.is_cleaning = True
        
        self.log_msg("🛑 Acción Manual: Deteniendo Piloto y limpiando inyecciones...", "warn")
        self.scheduler.stop()
        self.injector.cancel_all()
        
        self.btn_auto_start.configure(state="disabled", text="Limpiando...")
        self.btn_auto_pause.configure(state="disabled")
        self.btn_auto_stop.configure(state="disabled")
        self.lbl_pilot_status.configure(text="Limpiando procesos colgados...")
        
        def _clean_and_unlock():
            if self.tunnel.active_devices:
                for dev in self.tunnel.active_devices:
                    self.injector._cleanup_apps(dev["serial"])
                    self.adb.run_command(["shell", "input", "keyevent", "3"], dev["serial"]) # Volver a inicio
                    self.adb.run_command(["shell", "svc", "wifi", "disable"], dev["serial"]) # 🔌 APAGAR WIFI DE EMERGENCIA
            time.sleep(3)
            self.log_msg("✅ Piloto detenido por completo. Apps cerradas de raíz.", "success")
            
            def _gui():
                self.btn_auto_start.configure(state="normal", text="▶ INICIAR PILOTO")
                self.lbl_pilot_status.configure(text="Piloto Detenido")
                for btn in self.manual_btns:
                    btn.configure(state="normal")
                self.is_cleaning = False
            self.after(0, _gui)
            
        threading.Thread(target=_clean_and_unlock, daemon=True).start()

    # Callbacks del Scheduler
    def _on_phase_change(self, name, total_secs):
        def _update(): self.lbl_pilot_status.configure(text=f"Fase: {name} | Iniciando...")
        self.after(0, _update)
        
    def _on_tick(self, name, remaining_secs):
        def _update():
            if self.scheduler.is_paused:
                self.lbl_pilot_status.configure(text=f"Fase: {name} | [PAUSADO]")
            else:
                m, s = divmod(remaining_secs, 60)
                self.lbl_pilot_status.configure(text=f"Fase: {name} | Quedan: {m:02d}m {s:02d}s")
        self.after(0, _update)

    def _ghost_touch_loop(self):
        """Bucle global para toques fantasma."""
        while True:
            time.sleep(900) # Cada 15 minutos (900 segs)
            
            # Solo corre si está activado
            if not getattr(self, 'ghost_enabled', None) or not self.ghost_enabled.get():
                continue
                
            # Solo corre si hay celulares activos
            if not self.tunnel.running or not self.tunnel.active_devices:
                continue
                
            # Solo corre si hay una inyección en curso (Manual o Piloto)
            if not (self.is_injecting_manual or self.scheduler.is_running):
                continue
                
            self.log_msg("👻 [FANTASMA] Enviando toques ciegos para prevenir inactividad...", "warn")
            for dev in self.tunnel.active_devices:
                s = dev["serial"]
                # 1. Enviar WAKEUP para asegurar que la pantalla está encendida sin usar el volumen
                self.adb.run_command(["shell", "input", "keyevent", "224"], s)
                
                # 2. Enviar PLAY para reanudar si estaba pausado
                self.adb.run_command(["shell", "input", "keyevent", "126"], s)
                time.sleep(0.5)

    def _ad_skipper_loop(self):
        """Bucle global para saltar anuncios de YouTube/YT Music en medio de la reproducción."""
        while True:
            time.sleep(300) # Cada 5 minutos
            
            # Solo corre si está activado el Watchdog o es inyección manual
            if not self.tunnel.running or not self.tunnel.active_devices:
                continue
                
            is_pilot = self.scheduler.is_running
            is_manual = self.is_injecting_manual
            
            if not is_pilot and not is_manual:
                continue
                
            # Evitar saltar anuncios si la app actual es Spotify (para no gastar CPU)
            # Asumimos que si el piloto está corriendo, revisamos si es YouTube/YT Music
            current_phase = getattr(self.scheduler, 'current_phase_name', "")
            if is_pilot and current_phase == "Spotify":
                continue
                
            self.log_msg("📢 [AD-SKIPPER] Buscando anuncios de YouTube para saltar...", "info")
            for dev in self.tunnel.active_devices:
                s = dev["serial"]
                try:
                    if self.injector._find_and_click_text(s, ["Omitir", "Skip", "omitir", "skip", "Saltar", "saltar"]):
                        self.log_msg(f"[{s[-4:]}] 📢 Anuncio intermedio omitido con éxito.", "success")
                except Exception:
                    pass
                time.sleep(1) # Pausa pequeña para no saturar USB

    def _impatient_skip_loop(self):
        """Motor invisible de Saltos Impacientes (Humanizador)."""
        import random
        device_states = {}
        
        while True:
            time.sleep(5)
            
            if not getattr(self, 'skip_enabled', None) or not self.skip_enabled.get():
                device_states.clear()
                continue
                
            if not self.tunnel.running or not self.tunnel.active_devices:
                device_states.clear()
                continue
                
            is_manual = self.is_injecting_manual
            is_pilot = self.scheduler.is_running
            
            if not is_manual and not is_pilot:
                device_states.clear()
                continue
                
            # Regla: Solo si la plataforma tiene al menos 2 horas (7200s)
            if is_pilot and not is_manual:
                duration = getattr(self.scheduler, 'current_duration', 0)
                if duration < 7200:
                    device_states.clear()
                    continue
                    
            current_time = time.time()
            for dev in self.tunnel.active_devices:
                s = dev["serial"]
                if s not in device_states:
                    device_states[s] = {
                        "next_action_time": current_time + random.uniform(200, 240),
                        "songs_played": random.randint(0, 4)
                    }
                    
                state = device_states[s]
                if current_time >= state["next_action_time"]:
                    # Mandar comando de siguiente
                    self.adb.run_command(["shell", "input", "keyevent", "87"], s)
                    state["songs_played"] += 1
                    
                    if state["songs_played"] >= random.randint(6, 8):
                        # Se aburrió: la próxima canción dura poco (40-60 segs)
                        state["next_action_time"] = current_time + random.uniform(40, 60)
                        state["songs_played"] = 0
                        self.log_msg(f"⏭️ [{s[-4:]}] Salto Impaciente simulado (aburrimiento).", "info")
                    else:
                        # Canción completa (200-240 segs)
                        state["next_action_time"] = current_time + random.uniform(200, 240)

    def open_creador(self):
        # Evitar abrir múltiples ventanas
        if hasattr(self, 'creador_window') and self.creador_window is not None and self.creador_window.winfo_exists():
            self.creador_window.focus()
            return
            
        try:
            from core.creador import GestorCuentas
            self.creador_window = GestorCuentas(self, self.adb)
            self.creador_window.grab_set() # Hacerla modal (opcional)
        except Exception as e:
            self.log_msg(f"Error al abrir el Gestor de Cuentas: {e}", "error")

    def cancel_autoboot(self):
        if hasattr(self, 'autoboot_id') and self.autoboot_id:
            self.after_cancel(self.autoboot_id)
            self.autoboot_id = None
        if hasattr(self, 'f_autoboot'):
            self.f_autoboot.destroy()
        self.log_msg("🛑 Auto-Arranque cancelado por el usuario.", "warn")

    def force_autoboot_now(self):
        if hasattr(self, 'autoboot_id') and self.autoboot_id:
            self.after_cancel(self.autoboot_id)
            self.autoboot_id = None
        if hasattr(self, 'f_autoboot'):
            self.f_autoboot.destroy()
        threading.Thread(target=self._fully_automated_boot_sequence, daemon=True).start()

    def _autoboot_tick(self):
        if not hasattr(self, 'autoboot_secs'): return
        self.autoboot_secs -= 1
        if self.autoboot_secs <= 0:
            if hasattr(self, 'f_autoboot'):
                self.f_autoboot.destroy()
            threading.Thread(target=self._fully_automated_boot_sequence, daemon=True).start()
        else:
            if hasattr(self, 'lbl_autoboot') and self.lbl_autoboot.winfo_exists():
                self.lbl_autoboot.configure(text=f"🚀 AUTO-ARRANQUE EN {self.autoboot_secs} SEGUNDOS... Haremos el Escaneo, Proxies y Túnel automáticamente.")
                self.autoboot_id = self.after(1000, self._autoboot_tick)

    def _fully_automated_boot_sequence(self):
        self.log_msg("=== INICIANDO ARRANQUE TOTAL AUTOMATIZADO ===", "warn")
        
        # PASO 1
        self.action_scan()
        # Esperar inteligentemente a que termine el escaneo (incluso si son 40 dispositivos)
        while self.btn_scan.cget("state") == "disabled":
            time.sleep(1)
            
        if not self.scanned_devices:
            self.log_msg("Fallo auto-arranque: No se detectaron celulares conectados.", "error")
            return
            
        # PASO 2
        self.log_msg("Auto-Arranque: Probando proxies...", "info")
        self.action_test_proxies()
        # Esperar a que la prueba de proxies termine
        while self.btn_test_prx.cget("state") == "disabled":
            time.sleep(1)
        
        # PASO 3
        self.log_msg("Auto-Arranque: Abriendo túneles (Lote: Todos)...", "info")
        self.batch_var.set("Todos") # Forzar inyección a todos los dispositivos a la vez ANTES de iniciar túneles
        self.action_start_tunnel(force_empty_proxies=True)
        
        # Esperar inteligentemente a que todos los túneles se pongan en Verde
        self.log_msg("Auto-Arranque: Esperando luz verde en los túneles...", "info")
        timeout = 180 # Máximo 3 minutos de espera para 40 dispositivos
        elapsed = 0
        while elapsed < timeout:
            all_ok = True
            for ui in self.device_ui_cards.values():
                if "🟢" not in ui["health"].cget("text"):
                    all_ok = False
                    break
            if all_ok and len(self.device_ui_cards) > 0:
                break
            time.sleep(2)
            elapsed += 2
            
        if elapsed >= timeout:
            self.log_msg("⚠️ Auto-Arranque: Tiempo de espera agotado para los túneles. Continuando igual...", "warn")
        else:
            self.log_msg("✅ Auto-Arranque: Todos los túneles confirmados en verde.", "success")
        
        # Unos segunditos extra de colchón para que el OS de Android estabilice el proxy
        time.sleep(10)
        
        # PASO 5: Configuraciones
        self.log_msg("Auto-Arranque: Configurando fases a 60 mins...", "info")
        self.sp_m.delete(0, 'end'); self.sp_m.insert(0, "60")
        self.yt_m.delete(0, 'end'); self.yt_m.insert(0, "60")
        self.ytm_m.delete(0, 'end'); self.ytm_m.insert(0, "60")
        self.am_m.delete(0, 'end'); self.am_m.insert(0, "0")
        self.ti_m.delete(0, 'end'); self.ti_m.insert(0, "0")
        self.awa_m.delete(0, 'end'); self.awa_m.insert(0, "0")
        self.kick_m.delete(0, 'end'); self.kick_m.insert(0, "0")
        self.twitch_m.delete(0, 'end'); self.twitch_m.insert(0, "0")
        self.yts_m.delete(0, 'end'); self.yts_m.insert(0, "0")
        self.mix_m.delete(0, 'end'); self.mix_m.insert(0, "0")
        self.singles_m.delete(0, 'end'); self.singles_m.insert(0, "0")
        
        self.chk_watchdog_var.set(True)
        self._on_watchdog_toggle()
        
        self.mode_var.set("🤖 Piloto Automático")
        self._on_mode_change("🤖 Piloto Automático")
        
        self.action_start_pilot()
        self.log_msg("🚀 AUTO-ARRANQUE COMPLETADO. ¡FARMING ON!", "success")

    def action_check_update(self):
        self.log_msg("Buscando actualizaciones en la nube (Edición Oro)...", "info")
        self.btn_update.configure(state="disabled", text="Buscando...")
        
        def _on_result(has_update, remote_info):
            self.btn_update.configure(state="normal", text="🔄 Actualizar")
            if has_update and remote_info:
                ver = remote_info.get("version", "Nueva")
                msg = f"¡Hay una nueva versión disponible ({ver})!\n\nNovedades:\n{remote_info.get('notes', '')}\n\n¿Deseas descargarla y reiniciar la aplicación ahora?"
                if messagebox.askyesno("Actualización Disponible", msg):
                    self.log_msg("Descargando actualización...", "warn")
                    
                    def _prog(msg_text):
                        self.log_msg(msg_text, "info")
                    def _done(success, err):
                        if success:
                            self.log_msg("¡Actualización aplicada con éxito! Reiniciando...", "success")
                            self.after(2000, self.quit)
                        else:
                            self.log_msg(f"Fallo al actualizar: {err}", "error")
                            messagebox.showerror("Error", f"No se pudo actualizar:\n{err}")
                    
                    threading.Thread(target=updater.download_update, args=(remote_info.get("download_url"), _prog, _done), daemon=True).start()
            else:
                self.log_msg("Ya tienes la última versión instalada.", "success")
                messagebox.showinfo("Al día", "Ya tienes la última versión de la Edición Oro instalada.")

        updater.check_for_updates_async(_on_result)

if __name__ == "__main__":
    app = OmniUSBCleanApp()
    app.mainloop()
