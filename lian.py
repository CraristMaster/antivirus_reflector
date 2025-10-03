import os
import time
import threading
import queue
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ---------------- Malware Database (SIMULATION) ----------------
MALWARE_HASHES = {}
MALWARE_EXTENSIONS = []
malware_signatures = ["malware_code", "virus123", "trojan_test"]

# ---------------- Theme ----------------
def modern_theme():
    return {"bg": "#0a0f1f", "panel": "#0f1724", "fg": "#eaeef6", "accent": "#00fff7", "muted": "#9aa6b2"}

def classic_theme():
    return {"bg": "#1c1c1c", "panel": "#262626", "fg": "#e0e0e0", "accent": "#3cb371", "muted": "#a9b3b8"}

# ---------------- Neon Progress Ring ----------------
class NeonProgressRing(tk.Canvas):
    def __init__(self, parent, size=260, thickness=18, theme=None, **kwargs):
        bg = theme["bg"]
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.theme = theme
        self.mode = "idle"
        self.percent = 0
        self.label_text = ""
        self.radar_angle = 0
        self.radar_running = False
        self.text_id = None
        self.subtext_id = None
        self.draw_idle_frame()

    def draw_idle_frame(self):
        self.delete("all")
        pad = self.thickness + 4
        self.create_oval(pad, pad, self.size - pad, self.size - pad, outline="#11141a", width=self.thickness)
        self.text_id = self.create_text(self.size//2, self.size//2, text="Idle", fill=self.theme["muted"], font=("Segoe UI", 14, "bold"))
        if self.subtext_id:
            self.delete(self.subtext_id)
        self.subtext_id = self.create_text(self.size//2, self.size//2 + 36, text="Radar standby", fill=self.theme["muted"], font=("Segoe UI", 9))

    def start_radar(self):
        self.mode = "idle"
        if not self.radar_running:
            self.radar_running = True
            self._radar_step()

    def stop_radar(self):
        self.radar_running = False

    def _radar_step(self):
        if not self.radar_running: return
        self.delete("radar")
        pad = self.thickness + 4
        x0, y0, x1, y1 = pad, pad, self.size - pad, self.size - pad
        self.create_oval(x0, y0, x1, y1, outline="#11141a", width=self.thickness, tags="radar")
        sweep_len = 40
        for i in range(6):
            ang = (self.radar_angle - i*6) % 360
            color_frac = max(0.1, 1 - i*0.15)
            color = self._blend(self.theme["accent"], "#000000", 1 - color_frac)
            self.create_arc(x0, y0, x1, y1, start=90 - ang, extent=-6, style="arc", width=self.thickness//3, outline=color, tags="radar")
        self.radar_angle = (self.radar_angle + 6) % 360
        if self.text_id:
            self.itemconfig(self.text_id, text="Idle", fill=self.theme["muted"])
        if self.subtext_id:
            self.itemconfig(self.subtext_id, text="Radar standby", fill=self.theme["muted"])
        self.after(60, self._radar_step)

    def update_progress(self, percent, label_text=""):
        self.mode = "active"
        self.radar_running = False
        self.delete("all")
        pad = self.thickness + 4
        x0, y0, x1, y1 = pad, pad, self.size - pad, self.size - pad
        self.create_oval(x0, y0, x1, y1, outline="#0b0e11", width=self.thickness)
        extent = 360 * (percent/100.0)
        steps = 6
        for i in range(steps):
            frac = i / float(steps)
            width = max(1, int(self.thickness*(0.6 + (1-frac)*0.6)))
            color = self._blend(self.theme["accent"], "#ff00ff", frac*0.6)
            self.create_arc(x0, y0, x1, y1, start=90, extent=-extent, style="arc", outline=color, width=width)
        if self.text_id: self.delete(self.text_id)
        self.text_id = self.create_text(self.size//2, self.size//2, text=f"{percent:.0f}%", fill=self.theme["fg"], font=("Segoe UI", 22, "bold"))
        if self.subtext_id: self.delete(self.subtext_id)
        self.subtext_id = self.create_text(self.size//2, self.size//2 + 36, text=label_text, fill=self.theme["muted"], font=("Segoe UI", 10))

    def reset_to_idle(self):
        self.mode = "idle"
        self.delete("all")
        self.draw_idle_frame()
        self.start_radar()

    @staticmethod
    def _blend(hex1, hex2, t):
        def to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2],16) for i in (0,2,4))
        def to_hex(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)
        r1,g1,b1 = to_rgb(hex1)
        r2,g2,b2 = to_rgb(hex2)
        r=int(r1+(r2-r1)*t)
        g=int(g1+(g2-g1)*t)
        b=int(b1+(b2-b1)*t)
        return to_hex((r,g,b))

# ---------------- USB Monitor ----------------
class USBMonitor(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
        self._running = True
        try:
            import psutil
            self.psutil = psutil
        except Exception:
            self.psutil = None

    def run(self):
        if not self.psutil: return
        try:
            existing = {p.device for p in self.psutil.disk_partitions() if "removable" in p.opts}
        except Exception: existing = set()
        while self._running:
            try:
                current = {p.device for p in self.psutil.disk_partitions() if "removable" in p.opts}
                added = current - existing
                for d in added:
                    self.app.log_message(f"USB plugged: {d}")
                existing = current
            except Exception as e:
                self.app.log_message(f"USB Monitor Error: {e}")
            time.sleep(2)

    def stop(self): self._running = False

# ---------------- Main App ----------------
class AntivirusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ Lian Antivirus — Futuristic")
        self.geometry("1100x700")
        self.minsize(980,640)

        self.current_theme = modern_theme()
        self.scan_mode = tk.StringVar(value="Full")
        self.ai_protect = tk.BooleanVar(value=True)

        self._build_styles()
        self._build_header()
        self._build_body()

        self.usb_monitor = USBMonitor(self)
        self.usb_monitor.start()
        self.progress_ring.start_radar()

    # ---------------- UI ----------------
    def _build_styles(self):
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: style.theme_use("default")
        self.configure(bg=self.current_theme["bg"])

    def _build_header(self):
        header = tk.Frame(self, bg=self.current_theme["bg"], height=90)
        header.pack(fill="x", side="top")
        title = tk.Label(header, text="Lian Antivirus", font=("Segoe UI",28,"bold"), fg=self.current_theme["accent"], bg=self.current_theme["bg"])
        title.pack(side="left", padx=20, pady=18)
        self.status_label = tk.Label(header, text="Status: Ready", font=("Segoe UI",10), fg=self.current_theme["muted"], bg=self.current_theme["bg"])
        self.status_label.pack(side="right", padx=20)

    def _build_body(self):
        container = tk.Frame(self, bg=self.current_theme["bg"])
        container.pack(fill="both", expand=True)
        sidebar = tk.Frame(container, bg=self.current_theme["panel"], width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.content = tk.Frame(container, bg=self.current_theme["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        self.tabs = {}
        self._create_scan_tab()
        self._create_installer_tab()
        self._create_maintenance_tab()
        self._create_settings_tab()

        # sidebar buttons
        btn_specs = [
            ("🔍 Scan", self.show_scan_tab),
            ("📦 Installer", self.show_installer_tab),
            ("🛠 Maintenance", self.show_maintenance_tab),
            ("⚙ Settings", self.show_settings_tab)
        ]
        for text, cmd in btn_specs:
            b = tk.Button(sidebar, text=text, anchor="w", font=("Segoe UI",12,"bold"),
                          fg=self.current_theme["accent"], bg=self.current_theme["panel"],
                          relief="flat", bd=0, padx=14, command=cmd)
            b.pack(fill="x", pady=6, padx=10)
        self.show_scan_tab()

    # ---------------- Tab Handling ----------------
    def _show_tab(self,key):
        for t in self.tabs.values(): t.pack_forget()
        self.tabs[key].pack(fill="both",expand=True)
        self.status_label.config(text="Status: Scan mode active" if key=="scan" else "Status: Ready")

    def show_scan_tab(self): self._show_tab("scan")
    def show_installer_tab(self): self._show_tab("installer")
    def show_maintenance_tab(self): self._show_tab("maintenance")
    def show_settings_tab(self): self._show_tab("settings")

    # ---------------- Logging ----------------
    def log_message(self,msg): print(f"[LIAN] {msg}")

    # ---------------- Cleanup ----------------
    def on_close(self):
        try: self.usb_monitor.stop()
        except: pass
        self.destroy()

# ---------------- Run ----------------
if __name__ == "__main__":
    app = AntivirusApp()
    splash = tk.Toplevel(app)
    splash.overrideredirect(True)
    splash.geometry("640x320+300+200")
    splash.configure(bg=app.current_theme["bg"])
    tk.Label(splash,text="⚡ Lian Antivirus — Futuristic", font=("Segoe UI",22,"bold"), fg=app.current_theme["accent"], bg=app.current_theme["bg"]).pack(expand=True)
    tk.Label(splash,text="Initializing UI...", font=("Segoe UI",10), fg=app.current_theme["muted"], bg=app.current_theme["bg"]).pack(side="bottom", pady=14)
    app.withdraw()
    app.after(900, lambda: (splash.destroy(), app.deiconify()))
    app.protocol("WM_DELETE
