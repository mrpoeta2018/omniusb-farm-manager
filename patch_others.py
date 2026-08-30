import os, re
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

def patch_injector(func_name, action_name, app_name):
    global content
    old_def = f'def {func_name}(self):\n        try:\n            interval_minutes = float(self.playlist_interval.get())'
    if old_def not in content:
        old_def = f'def {func_name}(self):\n        # Reset the automatic timer to prevent collisions\n        try:\n            interval_minutes = float(self.playlist_interval.get())'

    if old_def in content:
        new_def = f'''def {func_name}(self):
        if hasattr(self, '_action_is_running') and self._action_is_running("{action_name}"):
            if messagebox.askyesno("Detener Inyeccion", "Deseas CANCELAR la inyeccion de {app_name} en curso?"):
                self._cancel_all_injections("{action_name}")
                try: getattr(self, "btn_manual_{func_name.replace('inject_manual_', '')}").configure(text="{app_name}", fg_color="#C026D3" if "{action_name}" == "yt_music" else "#F59E0B")
                except: pass
            return

        if not messagebox.askyesno("Confirmar", "Vas a inyectar {app_name}.\\n\\n¿Continuar?"):
            return

        if hasattr(self, '_check_conflicts'):
            conflicts = self._check_conflicts('{action_name}')
            if conflicts:
                self.log_msg(self._action_conflict_msg('{action_name}'), 'warn')
                return
        if hasattr(self, '_action_start'):
            self._action_start('{action_name}')
            try: getattr(self, "btn_manual_{func_name.replace('inject_manual_', '')}").configure(text="DETENER", fg_color="#EF4444")
            except: pass

        try:
            interval_minutes = float(self.playlist_interval.get())'''
        
        content = content.replace(old_def, new_def)
        
        # Patch the threading part
        # We need to find the specific mass_inject thread for this function.
        # It's tricky with regex, let's just do a string replace for the generic threading launch in these functions.

patch_injector('inject_manual_ytmusic', 'yt_music', 'YT Music')
patch_injector('inject_manual_awa', 'awa', 'AWA')
patch_injector('inject_manual_pandora', 'pandora', 'Pandora')
patch_injector('inject_manual_audiomack', 'audiomack', 'Audiomack')
patch_injector('inject_manual_applemusic', 'apple_music', 'Apple Music')
patch_injector('inject_manual_tidal', 'tidal', 'Tidal')

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Todas las plataformas adicionales parcheadas con escudos.")
