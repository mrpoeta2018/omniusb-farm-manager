import customtkinter as ctk
import time
import threading
import tkinter.messagebox as messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AutoFarmUI(ctk.CTkToplevel):
    def __init__(self, master_app):
        super().__init__(master_app)
        self.master_app = master_app
        self.is_running = False
        self.is_paused = False
        self.current_phase = None
        self.timer_thread = None
        
        self.title("OmniUSB 2.0 - Piloto Automático 24/7")
        self.geometry("600x550")
        self.resizable(False, False)
        
        # Make it stay on top of the main window
        self.transient(master_app)
        
        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=15, padx=20, fill="x")
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text="🤖 PILOTO AUTOMÁTICO", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_lbl.pack(side="left")
        
        self.btn_help = ctk.CTkButton(self.header_frame, text="❔ Info", width=60, fg_color="#4B5563", hover_color="#374151", command=self.show_help)
        self.btn_help.pack(side="right")
        
        # --- ESCUDOS DE FONDO (Sincronizados con App Principal) ---
        self.shields_frame = ctk.CTkFrame(self)
        self.shields_frame.pack(pady=(0, 10), padx=20, fill="x")
        
        ctk.CTkLabel(self.shields_frame, text="🛡️ Escudos Activos en Piloto:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5), pady=10)
        
        if hasattr(master_app, 'watchdog_enabled'):
            self.sw_watchdog = ctk.CTkSwitch(self.shields_frame, text="Watchdog", variable=master_app.watchdog_enabled, onvalue=True, offvalue=False)
            self.sw_watchdog.pack(side="left", padx=10)
            
        if hasattr(master_app, 'ghost_enabled'):
            self.sw_ghost = ctk.CTkSwitch(self.shields_frame, text="Anti-Pausa 👻", variable=master_app.ghost_enabled, onvalue=True, offvalue=False)
            self.sw_ghost.pack(side="left", padx=10)

        # --- RECETA DE ROTACIÓN ---
        self.recipe_frame = ctk.CTkFrame(self)
        self.recipe_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.recipe_frame, text="Receta de Rotación (Duración por ciclo)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.durations = {}
        platforms = [
            ("Spotify", "#1DB954"),
            ("YouTube Music", "#C026D3"),
            ("YouTube Video", "#EF4444")
        ]
        
        for name, color in platforms:
            row = ctk.CTkFrame(self.recipe_frame, fg_color="transparent")
            row.pack(fill="x", pady=5, padx=20)
            
            lbl = ctk.CTkLabel(row, text=name, text_color=color, font=ctk.CTkFont(size=14, weight="bold"), width=150, anchor="w")
            lbl.pack(side="left")
            
            # Horas
            default_h = "12" if name == "Spotify" else "0"
            hrs_var = ctk.StringVar(value=default_h)
            hrs_entry = ctk.CTkEntry(row, textvariable=hrs_var, width=50, justify="center")
            hrs_entry.pack(side="left", padx=5)
            ctk.CTkLabel(row, text="h").pack(side="left")
            
            # Minutos
            mins_var = ctk.StringVar(value="0")
            mins_entry = ctk.CTkEntry(row, textvariable=mins_var, width=50, justify="center")
            mins_entry.pack(side="left", padx=(15, 5))
            ctk.CTkLabel(row, text="m").pack(side="left")
            
            self.durations[name] = {"h": hrs_var, "m": mins_var}
            
        # Valores por defecto
        self.durations["Spotify"]["h"].set("12")
        self.durations["YouTube Video"]["h"].set("6")
        
        # --- MONITOR DE ESTADO ---
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(pady=15, padx=20, fill="x")
        
        self.status_lbl = ctk.CTkLabel(self.status_frame, text="ESTADO: DETENIDO ⏹", text_color="#9CA3AF", font=ctk.CTkFont(size=18, weight="bold"))
        self.status_lbl.pack(pady=(15, 5))
        
        self.current_phase_lbl = ctk.CTkLabel(self.status_frame, text="Fase Actual: Esperando órdenes...", font=ctk.CTkFont(size=14))
        self.current_phase_lbl.pack(pady=0)
        
        self.next_jump_lbl = ctk.CTkLabel(self.status_frame, text="Próximo Salto en: --:--:--", font=ctk.CTkFont(size=14))
        self.next_jump_lbl.pack(pady=(0, 15))
        
        # --- CONTROLES ---
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(pady=10, padx=20, fill="x")
        
        self.btn_play = ctk.CTkButton(self.controls_frame, text="▶ INICIAR", fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.start_rotation)
        self.btn_play.pack(side="left", expand=True, padx=2)
        
        self.btn_pause = ctk.CTkButton(self.controls_frame, text="⏸ PAUSA", fg_color="#F59E0B", hover_color="#D97706", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.pause_rotation)
        self.btn_pause.pack(side="left", expand=True, padx=2)
        
        self.btn_restart = ctk.CTkButton(self.controls_frame, text="🔄 REINICIAR", fg_color="#3B82F6", hover_color="#2563EB", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.restart_rotation)
        self.btn_restart.pack(side="left", expand=True, padx=2)
        
        self.btn_stop = ctk.CTkButton(self.controls_frame, text="⏹ DETENER", fg_color="#EF4444", hover_color="#DC2626", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.stop_rotation)
        self.btn_stop.pack(side="left", expand=True, padx=2)

        # Capturar el cierre de la ventana (La 'X')
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def start_rotation(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.status_lbl.configure(text="ESTADO: EN EJECUCIÓN ▶", text_color="#10B981")
            self.timer_thread = threading.Thread(target=self.rotation_loop, daemon=True)
            self.timer_thread.start()
        elif self.is_paused:
            self.is_paused = False
            self.status_lbl.configure(text="ESTADO: EN EJECUCIÓN ▶", text_color="#10B981")

    def pause_rotation(self):
        if self.is_running:
            self.is_paused = True
            self.status_lbl.configure(text="ESTADO: EN PAUSA ⏸", text_color="#F59E0B")

    def stop_rotation(self):
        self.is_running = False
        self.is_paused = False
        self.status_lbl.configure(text="ESTADO: DETENIDO ⏹", text_color="#9CA3AF")
        self.current_phase_lbl.configure(text="Fase Actual: Esperando órdenes...")
        self.next_jump_lbl.configure(text="Próximo Salto en: --:--:--")
        
    def restart_rotation(self):
        self.stop_rotation()
        self.after(500, self.start_rotation)

    def rotation_loop(self):
        sequence = [
            ("Spotify", self.master_app._trigger_auto_spotify if hasattr(self.master_app, '_trigger_auto_spotify') else None),
            ("YouTube Music", self.master_app._trigger_auto_yt_music if hasattr(self.master_app, '_trigger_auto_yt_music') else None),
            ("YouTube Video", self.master_app._trigger_auto_yt_video if hasattr(self.master_app, '_trigger_auto_yt_video') else None)
        ]
        
        while self.is_running:
            for name, trigger_func in sequence:
                if not self.is_running: break
                
                # Get duration
                try:
                    h = int(self.durations[name]["h"].get() or 0)
                    m = int(self.durations[name]["m"].get() or 0)
                except ValueError:
                    h, m = 0, 0
                
                total_seconds = (h * 3600) + (m * 60)
                if total_seconds <= 0:
                    continue # Skip this phase
                    
                self.current_phase_lbl.configure(text=f"Fase Actual: {name}")
                
                # Trigger the app injection!
                if trigger_func:
                    # Execute in main thread
                    self.after(0, trigger_func)
                
                # Timer loop
                remaining = total_seconds
                while remaining > 0 and self.is_running:
                    if not self.is_paused:
                        mins, secs = divmod(remaining, 60)
                        hrs, mins = divmod(mins, 60)

                        self.next_jump_lbl.configure(text=f"Próximo Salto en: {hrs:02d}:{mins:02d}:{secs:02d}")
                        remaining -= 1
                        
                        # --- MANTENIMIENTO CONTINUO (Cazador de Anuncios) ---
                        if remaining % 45 == 0 and name == "YouTube Video":
                            # Cada 45 segundos, revisa todos los celulares por si salió un anuncio nuevo
                            try:
                                devices = self.master_app.engine.active_devices if hasattr(self.master_app, 'engine') else []
                                for d in devices:
                                    serial = d['serial']
                                    # Usa el buscador de textos del master_app
                                    if hasattr(self.master_app, 'find_and_click_by_text'):
                                        if self.master_app.find_and_click_by_text(serial, ["Omitir", "Skip", "omitir", "skip", "OMITIR"]):
                                            self.master_app.log_msg(f" [{serial}] [Cazador Continuo] Anuncio omitido en plena reproducción.", "success")
                            except:
                                pass

                    time.sleep(1)

    def on_closing(self):
        if messagebox.askyesno("Apagar Piloto Automático", "¿Estás seguro de apagar el Piloto Automático?\n\nLos túneles y la aplicación principal seguirán abiertos para control manual."):
            self.is_running = False
            self.destroy()

    def show_help(self):
        msg = (
            "Bienvenido al Piloto Automático 24/7.\n\n"
            "1. Define cuántas horas/minutos quieres que dure cada plataforma en un ciclo.\n"
            "2. Si dejas una en 0h 0m, esa plataforma será ignorada.\n"
            "3. Presiona ▶ INICIAR. El sistema levantará túneles e inyectará automáticamente rotando entre las elegidas.\n"
            "4. Presiona ⏹ DETENER si quieres volver al Taller Manual."
        )
        messagebox.showinfo("¿Cómo funciona?", msg)
