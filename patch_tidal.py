with open('app_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

# UI: Textbox Tidal
ui_am = '''        am_f = ctk.CTkFrame(cajas_frame, fg_color="#9D174D", corner_radius=5)
        am_f.pack(side="top", fill="x", expand=True, pady=2)
        ctk.CTkLabel(am_f, text="🍎 Apple Music", font=("Arial", 11, "bold")).pack()
        self.txt_am = ctk.CTkTextbox(am_f, height=50)
        self.txt_am.pack(fill="x", padx=4, pady=4)'''
ui_ti = '''
        ti_f = ctk.CTkFrame(cajas_frame, fg_color="#1E293B", corner_radius=5)
        ti_f.pack(side="top", fill="x", expand=True, pady=2)
        ctk.CTkLabel(ti_f, text="🌊 Tidal", font=("Arial", 11, "bold")).pack()
        self.txt_ti = ctk.CTkTextbox(ti_f, height=50)
        self.txt_ti.pack(fill="x", padx=4, pady=4)
'''
content = content.replace(ui_am, ui_am + ui_ti)

# UI: Timer Tidal
timer_am = 'self.am_m = ctk.CTkEntry(timers_f, width=40); self.am_m.pack(side="left", padx=2); self.am_m.insert(0, "45")\n        ctk.CTkLabel(timers_f, text="AM").pack(side="left")'
timer_ti = '\n        ctk.CTkLabel(timers_f, text=" |").pack(side="left")\n        self.ti_m = ctk.CTkEntry(timers_f, width=40); self.ti_m.pack(side="left", padx=2); self.ti_m.insert(0, "45")\n        ctk.CTkLabel(timers_f, text="TID").pack(side="left")'
content = content.replace(timer_am, timer_am + timer_ti)

# UI: Manual Button Tidal
btn_am = 'btn4 = ctk.CTkButton(list_btn_f, text="▶ AM", fg_color="#BE185D", command=lambda: self.action_manual_inject("applemusic"))\n        btn4.pack(side="left", expand=True, padx=2)'
btn_ti = '\n        btn5 = ctk.CTkButton(list_btn_f, text="▶ TIDAL", fg_color="#334155", command=lambda: self.action_manual_inject("tidal"))\n        btn5.pack(side="left", expand=True, padx=2)'
content = content.replace(btn_am, btn_am + btn_ti)
content = content.replace('self.manual_btns.extend([btn1, btn2, btn3, btn4, btn_clone])', 'self.manual_btns.extend([btn1, btn2, btn3, btn4, btn5, btn_clone])')

# Config load/save
content = content.replace('if "am_urls" in d: self.txt_am.insert("1.0", d["am_urls"])', 'if "am_urls" in d: self.txt_am.insert("1.0", d["am_urls"])\n            if "ti_urls" in d: self.txt_ti.insert("1.0", d["ti_urls"])')
content = content.replace('if "am_m" in d: self.am_m.delete(0, "end"); self.am_m.insert(0, str(d["am_m"]))', 'if "am_m" in d: self.am_m.delete(0, "end"); self.am_m.insert(0, str(d["am_m"]))\n            if "ti_m" in d: self.ti_m.delete(0, "end"); self.ti_m.insert(0, str(d["ti_m"]))')

content = content.replace('"am_urls": self.txt_am.get("1.0", "end").strip(),', '"am_urls": self.txt_am.get("1.0", "end").strip(),\n                "ti_urls": self.txt_ti.get("1.0", "end").strip(),')
content = content.replace('"am_m": self.am_m.get(),', '"am_m": self.am_m.get(),\n                "ti_m": self.ti_m.get(),')

# Manual logic
content = content.replace('elif mode == "applemusic": t = self.txt_am', 'elif mode == "applemusic": t = self.txt_am\n        elif mode == "tidal": t = self.txt_ti')
content = content.replace('elif mode == "applemusic":\n                self.injector.inject_apple_music_batch(devices, urls_finales, drip_mode=drip)', 'elif mode == "applemusic":\n                self.injector.inject_apple_music_batch(devices, urls_finales, drip_mode=drip)\n            elif mode == "tidal":\n                self.injector.inject_tidal_batch(devices, urls_finales, drip_mode=drip)')

# Pilot logic
content = content.replace('am_s = int(self.am_m.get()) * 60', 'am_s = int(self.am_m.get()) * 60\n            ti_s = int(self.ti_m.get()) * 60')
fn_am = '''def fn_am():
            urls = parse_urls(self.txt_am)
            if urls: self.injector.inject_apple_music_batch(self.tunnel.active_devices, urls, drip_mode=drip)'''
fn_ti = '''\n\n        def fn_ti():
            urls = parse_urls(self.txt_ti)
            if urls: self.injector.inject_tidal_batch(self.tunnel.active_devices, urls, drip_mode=drip)'''
content = content.replace(fn_am, fn_am + fn_ti)
content = content.replace('if am_s > 0 and parse_urls(self.txt_am): phases.append(("Apple Music", am_s, fn_am))', 'if am_s > 0 and parse_urls(self.txt_am): phases.append(("Apple Music", am_s, fn_am))\n        if ti_s > 0 and parse_urls(self.txt_ti): phases.append(("Tidal", ti_s, fn_ti))')

# Watchdog
content = content.replace('elif phase_name == "Apple Music": pkg = "com.apple.android.music"', 'elif phase_name == "Apple Music": pkg = "com.apple.android.music"\n            elif phase_name == "Tidal": pkg = "com.aspiro.tidal"')
content = content.replace('elif phase_name == "Apple Music":\n                            urls = parse_urls(self.txt_am)\n                            if urls: self.injector.inject_apple_music_batch([dev], urls, drip_mode="apagado")', 'elif phase_name == "Apple Music":\n                            urls = parse_urls(self.txt_am)\n                            if urls: self.injector.inject_apple_music_batch([dev], urls, drip_mode="apagado")\n                        elif phase_name == "Tidal":\n                            urls = parse_urls(self.txt_ti)\n                            if urls: self.injector.inject_tidal_batch([dev], urls, drip_mode="apagado")')

with open('app_clean.py', 'w', encoding='utf-8') as f:
    f.write(content)
