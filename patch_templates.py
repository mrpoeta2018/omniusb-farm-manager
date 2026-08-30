import os
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

# 1. Define the callback logic for the templates
templates_logic = '''
    def set_template_organic(self):
        try: self.watchdog_enabled.set(True)
        except: pass
        try: self.ghost_enabled.set(True)
        except: pass
        try: self.bot_enabled.set(True)
        except: pass
        try: self.youtube_drip_var.set(True)
        except: pass
        try: self.stealth_var.set(True)
        except: pass
        self.log_msg("🪄 [Plantilla] Modo Orgánico (Premium) Activado. Escudos listos.", "success")
        
    def set_template_fast(self):
        try: self.watchdog_enabled.set(False)
        except: pass
        try: self.ghost_enabled.set(False)
        except: pass
        try: self.bot_enabled.set(False)
        except: pass
        try: self.youtube_drip_var.set(False)
        except: pass
        try: self.stealth_var.set(False)
        except: pass
        self.log_msg("🪄 [Plantilla] Modo Testeo (Rápido) Activado. Escudos desactivados.", "warn")
        
    def show_template_info(self):
        from tkinter import messagebox
        messagebox.showinfo("Glosario de Funciones", 
        "📘 GLOSARIO DE FARMING\\n\\n"
        "• Auto-Reinicio (Watchdog): Revive Spotify/YT si se cierran o crashean.\\n"
        "• Toques Fantasmas (Ghost): Sube el volumen 1 vez y destraba pausas.\\n"
        "• Saltos Impacientes (MediaBot): Salta algunas canciones al azar para simular humano.\\n"
        "• Goteo Humano: Inyecta los celulares uno por uno con 10-30 segs de pausa aleatoria.\\n"
        "• Modo Sigilo (Goteo de Red): Reinicia el VPN (cambio de IP) celular por celular al azar.\\n\\n"
        "Recomendación: Usar Modo Orgánico siempre, excepto para hacer pruebas rápidas de velocidad.")
'''

if "def set_template_organic" not in content:
    idx = content.find("def build_traffic_tab(self):")
    content = content[:idx] + templates_logic + "\n" + content[idx:]

# 2. Add the UI frame
ui_code = '''
        # --- PLANTILLAS DE FARMING ---
        tpl_frame = ctk.CTkFrame(self.tab_traf, fg_color="#334155", corner_radius=8, border_width=1, border_color="#10B981")
        tpl_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(tpl_frame, text="🪄 Plantillas (Perfiles):", font=("Arial", 12, "bold"), text_color="#FCD34D").pack(side="left", padx=10, pady=5)
        
        ctk.CTkButton(tpl_frame, text="1. Modo Orgánico (Recomendado)", fg_color="#10B981", hover_color="#059669", height=28, command=self.set_template_organic).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(tpl_frame, text="2. Modo Rápido (Testeo)", fg_color="#F59E0B", hover_color="#D97706", height=28, command=self.set_template_fast).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(tpl_frame, text="¿Qué es cada cosa?", fg_color="#475569", hover_color="#334155", height=28, command=self.show_template_info).pack(side="right", padx=10, pady=5)
        # -----------------------------
'''

# Insert it before the Shield frame
if "# --- PLANTILLAS DE FARMING ---" not in content:
    idx = content.find("# Shield\n        shield_frame = ctk.CTkFrame(self.tab_traf")
    content = content[:idx] + ui_code + "\n        " + content[idx:]

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Plantillas de Farming añadidas a la UI.")
