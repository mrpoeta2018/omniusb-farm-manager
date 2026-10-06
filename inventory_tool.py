import subprocess
import json
import tkinter as tk
import customtkinter as ctk

def get_usb_topology():
    # PowerShell logic to get physical location
    ps_script = """
    $devices = Get-PnpDevice -PresentOnly -Class USB | Where-Object { $_.InstanceId -match 'USB\\\\VID_18D1' }
    $results = @()
    foreach ($dev in $devices) {
        if ($dev.InstanceId -match 'USB\\\\VID_18D1&PID_4EE8\\\\([0-9A-Z]+)') {
            $serial = $matches[1]
            $loc = ($dev | Get-PnpDeviceProperty -KeyName 'DEVPKEY_Device_LocationInfo').Data
            $results += [PSCustomObject]@{
                Serial = $serial
                Location = $loc
            }
        }
    }
    $results | Sort-Object Location | ConvertTo-Json
    """
    
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], 
                                capture_output=True, text=True, startupinfo=startupinfo)
        
        output = result.stdout.strip()
        if not output:
            return []
            
        data = json.loads(output)
        if isinstance(data, dict):
            data = [data] # if only one device connected, powershell outputs dict instead of list
        return data
    except Exception as e:
        print("Error getting USB details:", e)
        return []

def group_devices(devices_list):
    boxes = {}
    for i, dev in enumerate(devices_list):
        loc = dev.get("Location", "")
        # The location looks like "Port_#0001.Hub_#0003"
        # The first Port_# usually identifies the Root Port, determining the Box.
        parts = loc.split('.')
        box_id = parts[0] if parts else "Unknown Box"
        
        if box_id not in boxes:
            boxes[box_id] = []
        boxes[box_id].append(dev)
    return boxes

class InventoryWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("📦 Mapa Físico (Inventario OmniUSB)")
        self.geometry("1100x850")
        self.attributes("-topmost", True)
        
        # Main Gradient-like Header
        self.header_frame = ctk.CTkFrame(self, fg_color="#1E293B", height=100, corner_radius=0)
        self.header_frame.pack(fill="x")
        
        self.header = ctk.CTkLabel(self.header_frame, text="📦 MAPA FÍSICO Y UBICACIÓN DE DISPOSITIVOS", 
                                   font=("Arial", 26, "bold"), text_color="#60A5FA")
        self.header.pack(pady=20)
        
        # Stats Bar
        self.stats_bar = ctk.CTkFrame(self, fg_color="#0F172A", height=40, corner_radius=0)
        self.stats_bar.pack(fill="x")
        self.stats_lbl = ctk.CTkLabel(self.stats_bar, text="Detectando hardware...", font=("Arial", 12, "italic"), text_color="#94A3B8")
        self.stats_lbl.pack(padx=20, side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.footer = ctk.CTkFrame(self, fg_color="#1E293B", height=80, corner_radius=0)
        self.footer.pack(fill="x")
        
        self.btn_refresh = ctk.CTkButton(self.footer, text="🔄 Refrescar Hardware", height=45, width=200,
                                         font=("Arial", 14, "bold"), command=self.load_devices)
        self.btn_refresh.pack(side="left", padx=20, pady=15)
        
        self.btn_export = ctk.CTkButton(self.footer, text="📋 Exportar a Excel (Tab)", height=45, width=200,
                                         font=("Arial", 14, "bold"), fg_color="#059669", hover_color="#047857", command=self.export_excel)
        self.btn_export.pack(side="right", padx=20, pady=15)
        
        self.current_data = {}
        # Initial load
        self.after(500, self.load_devices)

    def load_devices(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        loading = ctk.CTkLabel(self.scroll_frame, text="🔍 Escaneando topología USB... por favor espera.", font=("Arial", 16))
        loading.pack(pady=50)
        self.update() 
        
        devices = get_usb_topology()
        self.current_data = group_devices(devices)
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.current_data:
            ctk.CTkLabel(self.scroll_frame, text="❌ No se detectaron dispositivos Android (VID_18D1).\nVerifica que estén conectados y con depuración USB activa.", 
                         font=("Arial", 16, "bold"), text_color="#EF4444").pack(pady=50)
            self.stats_lbl.configure(text="Total: 0 dispositivos encontrados.")
            return
            
        total_found = sum(len(v) for v in self.current_data.values())
        self.stats_lbl.configure(text=f"Total: {total_found} dispositivos encontrados en {len(self.current_data)} HUBs.")

        box_counter = 1
        for root_port, dev_list in self.current_data.items():
            # Box Container
            box_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#0F172A", border_width=1, border_color="#334155")
            box_frame.pack(fill="x", pady=15, padx=10)
            
            title_fr = ctk.CTkFrame(box_frame, fg_color="#1E293B", height=40)
            title_fr.pack(fill="x")
            
            ctk.CTkLabel(title_fr, text=f"📦 HUB / CAJA {box_counter}", font=("Arial", 18, "bold"), text_color="#3B82F6").pack(side="left", padx=15)
            ctk.CTkLabel(title_fr, text=f"📍 Ubicación Root: {root_port}", font=("Arial", 11), text_color="#64748B").pack(side="right", padx=15)
            
            grid_frame = ctk.CTkFrame(box_frame, fg_color="transparent")
            grid_frame.pack(padx=15, pady=20)
            
            # Draw max 10 per row (Industrial style)
            for j, dev in enumerate(dev_list):
                row = j // 10
                col = j % 10
                
                # Port Card
                card = ctk.CTkFrame(grid_frame, width=95, height=65, corner_radius=8, fg_color="#1E293B", border_width=1, border_color="#3B82F6")
                card.grid(row=row, column=col, padx=6, pady=6)
                card.grid_propagate(False)
                
                ctk.CTkLabel(card, text=f"PORT {j+1}", font=("Arial", 10, "bold"), text_color="#60A5FA").pack(pady=(8, 0))
                ctk.CTkLabel(card, text=dev.get("Serial", ""), font=("Consolas", 11), text_color="white").pack(pady=(2, 0))
                
            box_counter += 1

    def export_excel(self):
        out_str = "Caja\tPuerto\tSerial\tUbicacion\n"
        box_counter = 1
        for root_port, dev_list in self.current_data.items():
            for j, dev in enumerate(dev_list):
                out_str += f"HUB {box_counter}\t{j+1}\t{dev.get('Serial','')}\t{dev.get('Location','')}\n"
            box_counter += 1
            
        self.clipboard_clear()
        self.clipboard_append(out_str)
        self.update()
        
        original_text = self.btn_export.cget("text")
        self.btn_export.configure(text="✅ ¡Copiado para Excel!")
        self.after(2000, lambda: self.btn_export.configure(text=original_text))

if __name__ == "__main__":
    # Test block
    app = ctk.CTk()
    app.geometry("10x10")
    app.withdraw() # hide main window
    dialog = InventoryWindow(app)
    app.mainloop()
