with open('app_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

# UI: Textbox AWA
ui_ti = '''
        ti_f = ctk.CTkFrame(cajas_frame, fg_color="#1E293B", corner_radius=5)
        ti_f.pack(side="top", fill="x", expand=True, pady=2)
        ctk.CTkLabel(ti_f, text="🌊 Tidal", font=("Arial", 11, "bold")).pack()
        self.txt_ti = ctk.CTkTextbox(ti_f, height=50)
        self.txt_ti.pack(fill="x", padx=4, pady=4)
'''
ui_awa = '''
        awa_f = ctk.CTkFrame(cajas_frame, fg_color="#F43F5E", corner_radius=5)
        awa_f.pack(side="top", fill="x", expand=True, pady=2)
        ctk.CTkLabel(awa_f, text="🌸 AWA", font=("Arial", 11, "bold")).pack()
        self.txt_awa = ctk.CTkTextbox(awa_f, height=50)
        self.txt_awa.pack(fill="x", padx=4, pady=4)
'''
content = content.replace(ui_ti, ui_ti + ui_awa)

# UI: Timer AWA
timer_ti = '\n        self.ti_m = ctk.CTkEntry(timers_f, width=40); self.ti_m.pack(side="left", padx=2); self.ti_m.insert(0, "45")\n        ctk.CTkLabel(timers_f, text="TID").pack(side="left")'
timer_awa = '\n        ctk.CTkLabel(timers_f, text=" |").pack(side="left")\n        self.awa_m = ctk.CTkEntry(timers_f, width=40); self.awa_m.pack(side="left", padx=2); self.awa_m.insert(0, "45")\n        ctk.CTkLabel(timers_f, text="AWA").pack(side="left")'
content = content.replace(timer_ti, timer_ti + timer_awa)

# UI: Manual Button AWA
btn_ti = 'btn5 = ctk.CTkButton(list_btn_f, text="▶ TIDAL", fg_color="#334155", command=lambda: self.action_manual_inject("tidal"))\n        btn5.pack(side="left", expand=True, padx=2)'
btn_awa = '\n        btn6 = ctk.CTkButton(list_btn_f, text="▶ AWA", fg_color="#F43F5E", command=lambda: self.action_manual_inject("awa"))\n        btn6.pack(side="left", expand=True, padx=2)'
content = content.replace(btn_ti, btn_ti + btn_awa)
content = content.replace('self.manual_btns.extend([btn1, btn2, btn3, btn4, btn5, btn_clone])', 'self.manual_btns.extend([btn1, btn2, btn3, btn4, btn5, btn6, btn_clone])')

# Config load/save
content = content.replace('if "ti_urls" in d: self.txt_ti.insert("1.0", d["ti_urls"])', 'if "ti_urls" in d: self.txt_ti.insert("1.0", d["ti_urls"])\n            if "awa_urls" in d: self.txt_awa.insert("1.0", d["awa_urls"])')
content = content.replace('if "ti_m" in d: self.ti_m.delete(0, "end"); self.ti_m.insert(0, str(d["ti_m"]))', 'if "ti_m" in d: self.ti_m.delete(0, "end"); self.ti_m.insert(0, str(d["ti_m"]))\n            if "awa_m" in d: self.awa_m.delete(0, "end"); self.awa_m.insert(0, str(d["awa_m"]))')

content = content.replace('"ti_urls": self.txt_ti.get("1.0", "end").strip(),', '"ti_urls": self.txt_ti.get("1.0", "end").strip(),\n                "awa_urls": self.txt_awa.get("1.0", "end").strip(),')
content = content.replace('"ti_m": self.ti_m.get(),', '"ti_m": self.ti_m.get(),\n                "awa_m": self.awa_m.get(),')

# Manual logic
content = content.replace('elif mode == "tidal": t = self.txt_ti', 'elif mode == "tidal": t = self.txt_ti\n        elif mode == "awa": t = self.txt_awa')
content = content.replace('elif mode == "tidal":\n                self.injector.inject_tidal_batch(devices, urls_finales, drip_mode=drip)', 'elif mode == "tidal":\n                self.injector.inject_tidal_batch(devices, urls_finales, drip_mode=drip)\n            elif mode == "awa":\n                self.injector.inject_awa_batch(devices, urls_finales, drip_mode=drip)')

# Pilot logic
content = content.replace('ti_s = int(self.ti_m.get()) * 60', 'ti_s = int(self.ti_m.get()) * 60\n            awa_s = int(self.awa_m.get()) * 60')
fn_ti = '''        def fn_ti():
            urls = parse_urls(self.txt_ti)
            if urls: self.injector.inject_tidal_batch(self.tunnel.active_devices, urls, drip_mode=drip)'''
fn_awa = '''\n\n        def fn_awa():
            urls = parse_urls(self.txt_awa)
            if urls: self.injector.inject_awa_batch(self.tunnel.active_devices, urls, drip_mode=drip)'''
content = content.replace(fn_ti, fn_ti + fn_awa)
content = content.replace('if ti_s > 0 and parse_urls(self.txt_ti): phases.append(("Tidal", ti_s, fn_ti))', 'if ti_s > 0 and parse_urls(self.txt_ti): phases.append(("Tidal", ti_s, fn_ti))\n        if awa_s > 0 and parse_urls(self.txt_awa): phases.append(("AWA", awa_s, fn_awa))')

# Watchdog
content = content.replace('elif phase_name == "Tidal": pkg = "com.aspiro.tidal"', 'elif phase_name == "Tidal": pkg = "com.aspiro.tidal"\n            elif phase_name == "AWA": pkg = "fm.awa.liverpool"')
content = content.replace('elif phase_name == "Tidal":\n                            urls = parse_urls(self.txt_ti)\n                            if urls: self.injector.inject_tidal_batch([dev], urls, drip_mode="apagado")', 'elif phase_name == "Tidal":\n                            urls = parse_urls(self.txt_ti)\n                            if urls: self.injector.inject_tidal_batch([dev], urls, drip_mode="apagado")\n                        elif phase_name == "AWA":\n                            urls = parse_urls(self.txt_awa)\n                            if urls: self.injector.inject_awa_batch([dev], urls, drip_mode="apagado")')

# Combo installer
content = content.replace('"Tidal"', '"Tidal", "AWA"')

with open('app_clean.py', 'w', encoding='utf-8') as f:
    f.write(content)
