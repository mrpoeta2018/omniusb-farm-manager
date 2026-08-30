import os
path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()

old_vol_logic = '''                            # Ocasionalmente un ajuste humano (volumen invisible)
                            elif random.randint(1, 5) == 1:
                                # Fix E: reducido de 15 a 5 para no saturar ADB
                                for _ in range(5):
                                    self.adb.run_command(["shell", "input", "keyevent", "25"], serial)
                                time.sleep(0.5)
                                self.adb.run_command(["shell", "input", "keyevent", "24"], serial)'''

new_vol_logic = '''                            # Ocasionalmente un ajuste humano (volumen invisible)
                            elif random.randint(1, 50) == 1: # Reducido 90% a pedido del usuario (casi nulo)
                                # Solo hace -1 y +1 para simular toque sin cambiar el nivel que el usuario dejó
                                self.adb.run_command(["shell", "input", "keyevent", "25"], serial)
                                time.sleep(0.5)
                                self.adb.run_command(["shell", "input", "keyevent", "24"], serial)'''

if old_vol_logic in content:
    content = content.replace(old_vol_logic, new_vol_logic)
    with open(path, 'w', encoding='utf-8') as f: f.write(content)
    print("Lógica de volumen actualizada.")
else:
    print("No se encontró la lógica anterior, buscando con regex...")
    import re
    content = re.sub(
        r'elif random\.randint\(1, 5\) == 1:.*?self\.adb\.run_command\(\["shell", "input", "keyevent", "24"\], serial\)',
        new_vol_logic, content, flags=re.DOTALL
    )
    with open(path, 'w', encoding='utf-8') as f: f.write(content)
    print("Lógica de volumen actualizada via regex.")
