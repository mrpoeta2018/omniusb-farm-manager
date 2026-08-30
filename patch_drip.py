import os, re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

# 1. Update the UI Checkbox to have a variable and tooltip
old_chk = 'ctk.CTkCheckBox(ctrl_frame, text=" Goteo Humano", variable=self.youtube_drip_var).pack(side="left", padx=(15, 5))'
new_chk = '''self.chk_drip = ctk.CTkCheckBox(ctrl_frame, text=" Goteo Humano", variable=self.youtube_drip_var)
        self.chk_drip.pack(side="left", padx=(15, 5))
        if hasattr(self, 'bind_tooltip'):
            self.bind_tooltip(self.chk_drip, "TIP ANTI-BOT:\\nAgrega un retraso aleatorio (10 a 30 seg) al inyectar celular por celular.\\nHace que las cuentas parezcan humanas reales.\\nNo es obligatorio, pero mejora la seguridad.")'''
if old_chk in content:
    content = content.replace(old_chk, new_chk)

# 2. Patch the sleep logic inside mass injections
# Looking for lines like:
# self._inject_playlist_to_single(...)
# s_sleep(1.5) or time.sleep(...)

drip_logic = '''
                    if hasattr(self, "youtube_drip_var") and self.youtube_drip_var.get():
                        st = random.randint(10, 30)
                        self.log_msg(f" ⏳ [Goteo Humano] Esperando {st}s para el sig. celular...", "info")
                        s_sleep(st)
                    else:
                        s_sleep(1.5)'''

# We will just replace s_sleep(1.5) globally where it follows an injection, or just all s_sleep(1.5) inside _mass_inject.
# Actually, the most reliable way is regex targeting s_sleep(1.5)
content = re.sub(r'\s+s_sleep\(1\.5\)', drip_logic, content)

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Goteo Humano activado y Tooltip añadido.")
