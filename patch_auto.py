import os
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

def patch_auto_trigger(func_name, action_name):
    global content
    old_start = f'def {func_name}(self):\n'
    if old_start in content:
        # Find where it actually starts doing work
        search_str = 'target_list = '
        idx = content.find(search_str, content.find(old_start))
        if idx != -1:
            protection = f'''
        if hasattr(self, '_check_conflicts'):
            if self._check_conflicts('{action_name}'):
                self.log_msg(f"⏳ [Auto-Rotación] Cancelada porque el sistema está ocupado.", "warn")
                return
        if hasattr(self, '_action_start'):
            self._action_start('{action_name}')
        '''
            content = content[:idx] + protection.lstrip() + content[idx:]

patch_auto_trigger('_trigger_auto_spotify', 'spotify')
patch_auto_trigger('_trigger_auto_yt_music', 'yt_music')
patch_auto_trigger('_trigger_auto_yt_video', 'youtube')

with open(path, 'w', encoding='utf-8') as f: f.write(content)
print("Protección ActionManager aplicada a los disparadores automáticos.")
