import os
import time
import threading
import tempfile
import math
import platform
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ---------------- Theme & Utilities ----------------
def modern_theme():
    return {
        "bg": "#0a0f1f",
        "panel": "#0f1724",
        "fg": "#eaeef6",
        "accent": "#00fff7",
        "muted": "#9aa6b2"
    }

def classic_theme():
    return {
        "bg": "#1c1c1c",
        "panel": "#262626",
        "fg": "#e0e0e0",
        "accent": "#3cb371",
        "muted": "#a9b3b8"
    }

# ---------------- Neon Progress / Radar Widget ----------------
class NeonProgressRing(tk.Canvas):
    """
    Dual-mode widget:
    - idle mode: rotating radar sweep animation
    - active mode: progress arc (percent)
    Use: update_progress(percent, label) OR start_radar()/stop_radar()
    """
    def __init__(self, parent, size=260, thickness=18, theme=None, **kwargs):
        bg = theme["bg"]
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.theme = theme
        self.percent = 0.0
        self.label_text = ""
        self.radar_angle = 0
        self.radar_running = False
        self.radar_id = None
        self.text_id = None
        self.subtext_id = None
        self.mode = "idle"  # "idle" or "active"
        self.draw_idle_frame()

    def draw_idle_frame(self):
        self.delete("all")
        pad = self.thickness + 4
        self.create_oval(pad, pad, self.size - pad, self.size - pad,
                         outline="#11141a", width=self.thickness, tags="bgcircle")
        # center static percent placeholder
        self.text_id = self.create_text(self.size // 2, self.size // 2,
                                        text="Idle", fill=self.theme["muted"],
                                        font=("Segoe UI", 14, "bold"))
        if self.subtext_id:
            self.delete(self.subtext_id)
        self.subtext_id = self.create_text(self.size // 2, self.size // 2 + 36,
                                           text="Radar standby",
                                           fill=self.theme["muted"],
                                           font=("Segoe UI", 9))

    def start_radar(self):
        if self.mode != "idle":
            self.mode = "idle"
        if not self.radar_running:
            self.radar_running = True
            self._radar_step()

    def stop_radar(self):
        self.radar_running = False
        # leave last frame; will be cleared by active draw

    def _radar_step(self):
        if not self.radar_running:
            return
        self.delete("radar")
        pad = self.thickness + 4
        x0, y0, x1, y1 = pad, pad, self.size - pad, self.size - pad
        # faded circle
        self.create_oval(x0, y0, x1, y1, outline="#11141a", width=self.thickness, tags="radar")
        # rotating thin sweep (gradient simulated by multiple arcs)
        sweep_len = 40  # degrees
        for i in range(6):
            ang = (self.radar_angle - i * 6) % 360
            color_frac = max(0.1, 1 - i * 0.15)
            color = self._blend(self.theme["accent"], "#000000", 1 - color_frac)
            self.create_arc(x0, y0, x1, y1, start=90 - ang, extent=-6,
                            style="arc", width=self.thickness//3, outline=color, tags="radar")
        # update labels
        if self.text_id:
            self.itemconfig(self.text_id, text="Idle", fill=self.theme["muted"])
        if self.subtext_id:
            self.itemconfig(self.subtext_id, text="Radar standby", fill=self.theme["muted"])
        self.radar_angle = (self.radar_angle + 6) % 360
        self.after(60, self._radar_step)

    def update_progress(self, percent, label_text=""):
        """Switch to active mode and show progress arc."""
        self.mode = "active"
        self.radar_running = False
        self.delete("all")
        pad = self.thickness + 4
        x0, y0, x1, y1 = pad, pad, self.size - pad, self.size - pad

        # background ring
        self.create_oval(x0, y0, x1, y1, outline="#0b0e11", width=self.thickness)

        # progress arc
        extent = 360 * (percent / 100.0)
        # draw several concentric arcs with slight color shifts to simulate neon gradient
        steps = 6
        for i in range(steps):
            frac = i / float(steps)
            width = max(1, int(self.thickness * (0.6 + (1 - frac) * 0.6)))
            color = self._blend(self.theme["accent"], "#ff00ff", frac * 0.6)
            self.create_arc(x0, y0, x1, y1, start=90, extent=-extent,
                            style="arc", outline=color, width=width)

        # center percentage
        if self.text_id:
            self.delete(self.text_id)
        self.text_id = self.create_text(self.size // 2, self.size // 2,
                                        text=f"{percent:.0f}%", fill=self.theme["fg"],
                                        font=("Segoe UI", 22, "bold"))
        # subtext
        if self.subtext_id:
            self.delete(self.subtext_id)
        self.subtext_id = self.create_text(self.size // 2, self.size // 2 + 36,
                                           text=label_text or "", fill=self.theme["muted"],
                                           font=("Segoe UI", 10))

    def reset_to_idle(self):
        self.mode = "idle"
        self.delete("all")
        self.draw_idle_frame()
        self.start_radar()

    @staticmethod
    def _blend(hex1, hex2, t):
        """Blend two hex colors (simple linear). t in [0,1]."""
        def to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        def to_hex(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)
        r1, g1, b1 = to_rgb(hex1)
        r2, g2, b2 = to_rgb(hex2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return to_hex((r, g, b))

# ---------------- USB Monitor (kept, safe) ----------------
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
        if not self.psutil:
            return
        existing = {p.device for p in self.psutil.disk_partitions() if "removable" in p.opts}
        while self._running:
            try:
                new = {p.device for p in self.psutil.disk_partitions() if "removable" in p.opts}
                added = new - existing
                if added:
                    for d in added:
                        self.app.log_message(f"USB plugged: {d}")
                        # Do not auto-scan - just notify
                existing = new
            except Exception:
                pass
            time.sleep(2)

    def stop(self):
        self._running = False

# ---------------- Main App ----------------
class AntivirusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ Lian Antivirus — Futuristic")
        self.geometry("1100x700")
        self.minsize(980, 640)

        # state
        self.current_theme = modern_theme()
        self.scan_mode = tk.StringVar(value="Full")
        self.ai_protect = tk.BooleanVar(value=True)

        # build UI
        self._build_styles()
        self._build_header()
        self._build_body()

        # usb monitor
        self.usb_monitor = USBMonitor(self)
        self.usb_monitor.start()

        # start radar (idle)
        self.progress_ring.start_radar()

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        # minimal ttk style usage; most UI is custom tk widgets for look control
        self.configure(bg=self.current_theme["bg"])

    def _build_header(self):
        header = tk.Frame(self, bg=self.current_theme["bg"], height=90)
        header.pack(fill="x", side="top")

        title = tk.Label(header, text="Lian Antivirus", font=("Segoe UI", 28, "bold"),
                         fg=self.current_theme["accent"], bg=self.current_theme["bg"])
        title.pack(side="left", padx=20, pady=18)

        # subtitle / small status
        self.status_label = tk.Label(header, text="Status: Ready", font=("Segoe UI", 10),
                                     fg=self.current_theme["muted"], bg=self.current_theme["bg"])
        self.status_label.pack(side="right", padx=20)

    def _build_body(self):
        container = tk.Frame(self, bg=self.current_theme["bg"])
        container.pack(fill="both", expand=True)

        # sidebar
        sidebar = tk.Frame(container, bg=self.current_theme["panel"], width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # content area
        self.content = tk.Frame(container, bg=self.current_theme["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        # Tabs Buttons (glass-like)
        btn_specs = [
            ("🔍 Scan", self.show_scan_tab),
            ("📦 Safe App Installer", self.show_installer_tab),
            ("🛠 Maintenance", self.show_maintenance_tab),
            ("⚙ Settings", self.show_settings_tab),
        ]
        for text, cmd in btn_specs:
            b = tk.Button(sidebar, text=text, anchor="w", font=("Segoe UI", 12, "bold"),
                          fg=self.current_theme["accent"], bg=self.current_theme["panel"],
                          relief="flat", bd=0, padx=14, command=cmd)
            b.pack(fill="x", pady=6, padx=10)

        # create tab frames
        self.tabs = {}
        self._create_scan_tab()
        self._create_installer_tab()
        self._create_maintenance_tab()
        self._create_settings_tab()

        self.show_scan_tab()

    # ---------------- Tab: Scan ----------------
    def _create_scan_tab(self):
        f = tk.Frame(self.content, bg=self.current_theme["bg"])
        self.tabs["scan"] = f

        # description
        tk.Label(f, text="Manual Scan — choose folder and scan", bg=self.current_theme["bg"],
                 fg=self.current_theme["fg"], font=("Segoe UI", 14, "italic")).pack(pady=(18, 6))

        # ring + controls layout
        mid = tk.Frame(f, bg=self.current_theme["bg"])
        mid.pack(expand=True, fill="both")

        # progress ring
        self.progress_ring = NeonProgressRing(mid, size=320, thickness=20, theme=self.current_theme)
        self.progress_ring.pack(side="left", padx=40, pady=20)

        # controls
        ctrl = tk.Frame(mid, bg=self.current_theme["bg"])
        ctrl.pack(side="left", padx=8, pady=20, fill="y")

        tk.Button(ctrl, text="📁 Browse & Scan", bg=self.current_theme["panel"], fg=self.current_theme["accent"],
                  font=("Segoe UI", 12, "bold"), relief="raised", bd=0, padx=12,
                  command=self.browse_and_scan).pack(pady=12)

        self.scan_log = tk.Text(ctrl, width=40, height=12, bg=self.current_theme["panel"],
                                fg=self.current_theme["fg"], bd=0, padx=8, pady=8)
        self.scan_log.pack(pady=6)

        # quick info
        tk.Label(ctrl, text="Scan Mode:", bg=self.current_theme["bg"], fg=self.current_theme["muted"]).pack(pady=(12, 2))
        tk.OptionMenu(ctrl, self.scan_mode, "Quick", "Full", "Custom").pack()

    # ---------------- Tab: Safe App Installer ----------------
    def _create_installer_tab(self):
        f = tk.Frame(self.content, bg=self.current_theme["bg"])
        self.tabs["installer"] = f

        tk.Label(f, text="Safe App Installer", bg=self.current_theme["bg"],
                 fg=self.current_theme["fg"], font=("Segoe UI", 16, "bold")).pack(pady=14)

        box = tk.Frame(f, bg=self.current_theme["bg"])
        box.pack(pady=6, padx=16, fill="both", expand=True)

        # sample safe apps
        self.available_apps = [
            ("Google Chrome", "chrome"),
            ("Visual Studio Code", "vscode"),
            ("VLC Media Player", "vlc"),
            ("WhatsApp Desktop", "whatsapp"),
            ("Slack", "slack"),
            ("7-Zip", "7zip"),
        ]
        self.app_vars = {}
        left = tk.Frame(box, bg=self.current_theme["bg"])
        left.pack(side="left", padx=8, pady=6, fill="both", expand=True)

        for name, key in self.available_apps:
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(left, text=name, var=var,
                                bg=self.current_theme["bg"], fg=self.current_theme["fg"],
                                selectcolor=self.current_theme["panel"],
                                font=("Segoe UI", 12))
            cb.pack(anchor="w", pady=4)
            self.app_vars[key] = (var, name)

        right = tk.Frame(box, bg=self.current_theme["bg"])
        right.pack(side="right", padx=6, pady=6, fill="y")

        tk.Button(right, text="Install Selected", bg=self.current_theme["panel"],
                  fg=self.current_theme["accent"], font=("Segoe UI", 12, "bold"),
                  command=self.install_selected_apps).pack(pady=10)

        self.installer_log = tk.Text(right, width=36, height=14, bg=self.current_theme["panel"],
                                     fg=self.current_theme["fg"], bd=0, padx=8, pady=8)
        self.installer_log.pack(pady=6)

    # ---------------- Tab: Maintenance ----------------
    def _create_maintenance_tab(self):
        f = tk.Frame(self.content, bg=self.current_theme["bg"])
        self.tabs["maintenance"] = f

        tk.Label(f, text="Maintenance & Repair", bg=self.current_theme["bg"],
                 fg=self.current_theme["fg"], font=("Segoe UI", 16, "bold")).pack(pady=14)

        grid = tk.Frame(f, bg=self.current_theme["bg"])
        grid.pack(pady=8)

        tk.Button(grid, text="🧹 Clear Temp Files", bg=self.current_theme["panel"],
                  fg=self.current_theme["accent"], font=("Segoe UI", 12),
                  command=self.clear_temp_files).grid(row=0, column=0, padx=12, pady=8)

        tk.Button(grid, text="⚡ Optimize Startup", bg=self.current_theme["panel"],
                  fg=self.current_theme["accent"], font=("Segoe UI", 12),
                  command=self.optimize_startup).grid(row=0, column=1, padx=12, pady=8)

        tk.Button(grid, text="🔧 Repair System", bg=self.current_theme["panel"],
                  fg=self.current_theme["accent"], font=("Segoe UI", 12),
                  command=self.repair_system).grid(row=1, column=0, padx=12, pady=8)

        self.maintenance_log = tk.Text(f, bg=self.current_theme["panel"], fg=self.current_theme["fg"],
                                       width=80, height=10, bd=0)
        self.maintenance_log.pack(pady=12)

    # ---------------- Tab: Settings ----------------
    def _create_settings_tab(self):
        f = tk.Frame(self.content, bg=self.current_theme["bg"])
        self.tabs["settings"] = f

        tk.Label(f, text="Settings", bg=self.current_theme["bg"],
                 fg=self.current_theme["fg"], font=("Segoe UI", 16, "bold")).pack(pady=10)

        # Theme toggle
        theme_frame = tk.Frame(f, bg=self.current_theme["bg"])
        theme_frame.pack(pady=8)
        tk.Label(theme_frame, text="Theme:", bg=self.current_theme["bg"], fg=self.current_theme["muted"]).pack(side="left", padx=6)
        tk.Button(theme_frame, text="Modern", bg=self.current_theme["panel"], fg=self.current_theme["fg"],
                  command=lambda: self.apply_theme("modern")).pack(side="left", padx=6)
        tk.Button(theme_frame, text="Classic", bg=self.current_theme["panel"], fg=self.current_theme["fg"],
                  command=lambda: self.apply_theme("classic")).pack(side="left", padx=6)

        # AI Protection toggle
        ai_frame = tk.Frame(f, bg=self.current_theme["bg"])
        ai_frame.pack(pady=10)
        tk.Checkbutton(ai_frame, text="AI Protection Mode (Beta)", var=self.ai_protect,
                       bg=self.current_theme["bg"], fg=self.current_theme["fg"], selectcolor=self.current_theme["panel"]).pack()

        # Scan modes
        mode_frame = tk.Frame(f, bg=self.current_theme["bg"])
        mode_frame.pack(pady=8)
        tk.Label(mode_frame, text="Default Scan Mode:", bg=self.current_theme["bg"], fg=self.current_theme["muted"]).pack(side="left", padx=6)
        tk.OptionMenu(mode_frame, self.scan_mode, "Quick", "Full", "Custom").pack(side="left")

    # ---------------- Show Tabs ----------------
    def _show_tab(self, key):
        # clear all
        for t in self.tabs.values():
            t.pack_forget()
        self.tabs[key].pack(fill="both", expand=True)
        # update status
        self.status_label.config(text="Status: Ready" if key != "scan" else "Status: Scan mode active")

    def show_scan_tab(self):
        self._show_tab("scan")

    def show_installer_tab(self):
        self._show_tab("installer")

    def show_maintenance_tab(self):
        self._show_tab("maintenance")

    def show_settings_tab(self):
        self._show_tab("settings")

    # ---------------- Operations ----------------
    def browse_and_scan(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        # collect files in a background thread (safe blocking)
        self.scan_log.delete("1.0", tk.END)
        self.scan_log.insert(tk.END, f"Scanning folder: {folder}\nCollecting files...\n")
        self.progress_ring.update_progress(0, "Collecting...")
        self.progress_ring.stop_radar()

        collect_q = queue.Queue()

        def collect():
            files = []
            for root, _, filenames in os.walk(folder):
                for f in filenames:
                    files.append(os.path.join(root, f))
            collect_q.put(files)

        t = threading.Thread(target=collect, daemon=True)
        t.start()

        def wait_collect():
            try:
                files = collect_q.get_nowait()
            except queue.Empty:
                self.after(100, wait_collect)
                return
            # proceed with iterative scanning using after to remain responsive
            total = len(files)
            if total == 0:
                messagebox.showinfo("Scan", "No files to scan.")
                self.progress_ring.reset_to_idle()
                return
            self.scan_log.insert(tk.END, f"Found {total} files. Starting scan...\n")
            self._scan_iter(files, 0, total)
        wait_collect()

    def _scan_iter(self, files, idx, total):
        # simulate scanning a single file
        if idx >= total:
            self.scan_log.insert(tk.END, "Scan complete. No threats detected (simulation).\n")
            messagebox.showinfo("Scan Complete", "✨ Scan finished successfully!")
            self.progress_ring.reset_to_idle()
            return
        filepath = files[idx]
        # log step
        self.scan_log.insert(tk.END, f"Scanning: {os.path.basename(filepath)}\n")
        percent = (idx + 1) / total * 100
        self.progress_ring.update_progress(percent, os.path.basename(filepath))
        # schedule next
        self.after(8, lambda: self._scan_iter(files, idx + 1, total))

    def install_selected_apps(self):
        selected = [name for key, (var, name) in self.app_vars.items() if var.get()]
        if not selected:
            messagebox.showinfo("Installer", "No apps selected.")
            return
        self.installer_log.delete("1.0", tk.END)
        self.installer_log.insert(tk.END, f"Preparing to install {len(selected)} apps...\n")
        self.progress_ring.stop_radar()
        # simulate sequential install using after
        self._install_iter(selected, 0)

    def _install_iter(self, apps, idx):
        if idx >= len(apps):
            self.installer_log.insert(tk.END, "All selected apps installed (simulated).\n")
            messagebox.showinfo("Installer", "Installation simulation complete.")
            self.progress_ring.reset_to_idle()
            return
        app = apps[idx]
        self.installer_log.insert(tk.END, f"Installing {app}...\n")
        # show progress arc for each app (fake percent)
        steps = 50
        def step(i=0):
            pct = (i / steps) * 100
            self.progress_ring.update_progress(pct, f"Installing {app}")
            if i < steps:
                self.after(18, lambda: step(i + 1))
            else:
                self.installer_log.insert(tk.END, f"{app} installed.\n")
                self.after(300, lambda: self._install_iter(apps, idx + 1))
        step()

    def clear_temp_files(self):
        # SAFE simulation: count files in temp dir and offer to "clear" (but we won't delete by default)
        tmp = tempfile.gettempdir()
        count = 0
        for root, _, files in os.walk(tmp):
            count += len(files)
        if count == 0:
            self.maintenance_log.insert(tk.END, "No temporary files found (or none accessible).\n")
            messagebox.showinfo("Clear Temp", "No temporary files found.")
            return
        if messagebox.askyesno("Clear Temp", f"Found ~{count} files in temp. Simulate deletion?"):
            # Simulate deletion progress
            self.maintenance_log.insert(tk.END, f"Simulating removal of {count} temp files...\n")
            steps = min(80, count)
            def step(i=0):
                pct = (i / steps) * 100
                self.progress_ring.update_progress(pct, "Clearing temp")
                if i < steps:
                    self.after(25, lambda: step(i + 1))
                else:
                    self.maintenance_log.insert(tk.END, "Temp files 'cleared' (simulation).\n")
                    messagebox.showinfo("Clear Temp", "Temporary files cleared (simulation).")
                    self.progress_ring.reset_to_idle()
            step()
        else:
            self.maintenance_log.insert(tk.END, "Clear temp cancelled by user.\n")

    def optimize_startup(self):
        self.maintenance_log.insert(tk.END, "Analyzing startup items...\n")
        # fake analysis
        self.progress_ring.stop_radar()
        def run_opt(i=0):
            self.progress_ring.update_progress(i*10, "Optimizing startup")
            if i < 10:
                self.after(150, lambda: run_opt(i+1))
            else:
                self.maintenance_log.insert(tk.END, "Startup optimized (simulation).\n")
                messagebox.showinfo("Optimize Startup", "Startup optimization complete (simulation).")
                self.progress_ring.reset_to_idle()
        run_opt()

    def repair_system(self):
        self.maintenance_log.insert(tk.END, "Running quick repair routines...\n")
        self.progress_ring.stop_radar()
        def run_rep(i=0):
            self.progress_ring.update_progress(i*12.5, "Repairing")
            if i < 8:
                self.after(180, lambda: run_rep(i+1))
            else:
                self.maintenance_log.insert(tk.END, "Repair finished (simulation).\n")
                messagebox.showinfo("Repair", "System repair complete (simulation).")
                self.progress_ring.reset_to_idle()
        run_rep()

    def apply_theme(self, name):
        if name == "modern":
            self.current_theme = modern_theme()
        else:
            self.current_theme = classic_theme()
        # update colors across the app
        self.configure(bg=self.current_theme["bg"])
        # header/status
        for widget in self.winfo_children():
            widget.configure(bg=self.current_theme["bg"])
        # progress ring needs recreation to pick up theme cleanly
        # we will destroy and re-create where it exists (scan tab)
        try:
            # remove old ring and create new one in same parent
            parent = self.progress_ring.master
            self.progress_ring.destroy()
            self.progress_ring = NeonProgressRing(parent, size=320, thickness=20, theme=self.current_theme)
            self.progress_ring.pack(side="left", padx=40, pady=20)
            self.progress_ring.start_radar()
        except Exception:
            pass
        # update small labels and panels: brute-force update of text widgets & buttons
        for txt in (self.scan_log, self.installer_log, self.maintenance_log):
            try:
                txt.configure(bg=self.current_theme["panel"], fg=self.current_theme["fg"])
            except Exception:
                pass
        self.status_label.configure(fg=self.current_theme["muted"])

    # ---------------- Helpers ----------------
    def log_message(self, msg):
        # simple log; could be extended to file or on-screen logger
        print(f"[LIAN] {msg}")

    def on_close(self):
        # stop USB monitor
        try:
            self.usb_monitor.stop()
        except Exception:
            pass
        self.destroy()

# ---------------- Run ----------------
if __name__ == "__main__":
    app = AntivirusApp()
    # Splash (simple)
    splash = tk.Toplevel(app)
    splash.overrideredirect(True)
    splash.geometry("640x320+300+200")
    splash.configure(bg=app.current_theme["bg"])
    tk.Label(splash, text="⚡ Lian Antivirus — Futuristic", font=("Segoe UI", 22, "bold"),
             fg=app.current_theme["accent"], bg=app.current_theme["bg"]).pack(expand=True)
    tk.Label(splash, text="Initializing UI...", font=("Segoe UI", 10), fg=app.current_theme["muted"],
             bg=app.current_theme["bg"]).pack(side="bottom", pady=14)
    app.withdraw()
    app.after(900, lambda: (splash.destroy(), app.deiconify()))
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
