with open('app_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('ytm_s = int(self.ytm_m.get()) * 60', 'ytm_s = int(self.ytm_m.get()) * 60\n            am_s = int(self.am_m.get()) * 60')

content = content.replace('def fn_ytm():\n            urls = parse_urls(self.txt_ym)\n            if urls: self.injector.inject_youtube_batch(self.tunnel.active_devices, urls, is_music=True, drip_mode=drip)', 'def fn_ytm():\n            urls = parse_urls(self.txt_ym)\n            if urls: self.injector.inject_youtube_batch(self.tunnel.active_devices, urls, is_music=True, drip_mode=drip)\n\n        def fn_am():\n            urls = parse_urls(self.txt_am)\n            if urls: self.injector.inject_apple_music_batch(self.tunnel.active_devices, urls, drip_mode=drip)')

content = content.replace('if ytm_s > 0 and parse_urls(self.txt_ym): phases.append(("YT Music", ytm_s, fn_ytm))', 'if ytm_s > 0 and parse_urls(self.txt_ym): phases.append(("YT Music", ytm_s, fn_ytm))\n        if am_s > 0 and parse_urls(self.txt_am): phases.append(("Apple Music", am_s, fn_am))')

# Watchdog updates
content = content.replace('elif phase_name == "YT Music": pkg = "com.google.android.apps.youtube.music"', 'elif phase_name == "YT Music": pkg = "com.google.android.apps.youtube.music"\n            elif phase_name == "Apple Music": pkg = "com.apple.android.music"')
content = content.replace('elif phase_name == "YT Music":\n                            urls = parse_urls(self.txt_ym)\n                            if urls: self.injector.inject_youtube_batch([dev], urls, is_music=True, drip_mode="apagado")', 'elif phase_name == "YT Music":\n                            urls = parse_urls(self.txt_ym)\n                            if urls: self.injector.inject_youtube_batch([dev], urls, is_music=True, drip_mode="apagado")\n                        elif phase_name == "Apple Music":\n                            urls = parse_urls(self.txt_am)\n                            if urls: self.injector.inject_apple_music_batch([dev], urls, drip_mode="apagado")')

with open('app_clean.py', 'w', encoding='utf-8') as f:
    f.write(content)
