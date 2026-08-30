import re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

# Fix the over-indented block at line 1795
bad_block = '''                    if hasattr(self, "youtube_drip_var") and self.youtube_drip_var.get():
                        st = random.randint(10, 30)
                        self.log_msg(f" ⏳ [Goteo Humano] Esperando {st}s para el sig. celular...", "info")
                        s_sleep(st)
                    else:
                        s_sleep(1.5)'''

good_block = '''                if hasattr(self, "youtube_drip_var") and self.youtube_drip_var.get():
                    st = random.randint(10, 30)
                    self.log_msg(f" ⏳ [Goteo Humano] Esperando {st}s para el sig. celular...", "info")
                    s_sleep(st)
                else:
                    s_sleep(1.5)'''

# For the generic injector specifically, where it follows _inject_generic_audio_to_single
content = content.replace(bad_block, good_block)

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Indentation fixed at generic injector.")
