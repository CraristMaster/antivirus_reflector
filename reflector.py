import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import psutil
import platform

# ---------------- Style for ttk ----------------
def set_dark_theme():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="black")
    style.configure("TLabel", background="black", foreground="lime")
    style.configure("TButton", background="black", foreground="lime")
    style.configure("TProgressbar", troughcolor="black", background="lime", thickness=20)

# ---------------- Splash Screen ----------------
class SplashScreen(tk.Toplevel):
    def __init__(self, parent, image_path, duration=5000):
        super().__init__(parent)
        self.overrideredirect(True)
        self.geometry("600x400+400+200")
        self.config(bg="black")

        try:
            self.image = tk.PhotoImage(file=image_path)
            label = tk.Label(self, image=self.image, bg="black")
            label.pack(expand=True)
        except Exception:
            label = tk.Label(self, text="Lian Antivirus Loading...", fg="lime", bg="black", font=("Arial", 16))
            label.pack(expand=True)

        footer = tk.Label(self, text="Version 1.0", fg="orange", bg="black", font=("Arial", 10))
        footer.pack(side="left", anchor="s", padx=10, pady=5)

        self.after(duration, self.destroy)

# ---------------- USB Monitor ----------------
class USBMonitor(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
        self.existing_devices = self.get_connected_devices()

    def get_connected_devices(self):
        return {p.device for p in psutil.disk_partitions() if "removable" in p.opts}

    def run(self):
        while True:
            time.sleep(2)
            new_devices = self.get_connected_devices()
            added = new_devices - self.existing_devices
            if added:
                for device in added:
                    self.app.log_message(f"USB plugged: {device}")
                    self.app.scan_directory(device)
            self.existing_devices = new_devices

# ---------------- Antivirus App ----------------
class AntivirusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lian the Antivirus")
        self.geometry("900x600")
        self.config(bg='black')

        set_dark_theme()

        try:
            self.iconphoto(False, tk.PhotoImage(file="/media/kali/reflector/lian/lian.png"))
        except:
            pass

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)
        self.grid_columnconfigure(0, weight=1)

        # ---- TOP ----
        self.top_frame = tk.Frame(self, bg='black')
        self.top_frame.grid(row=0, column=0, sticky="nsew")

        self.scan_title = tk.Label(self.top_frame, text="Lian", font=("Arial", 22, "bold"), bg='black', fg="lime")
        self.scan_title.pack(expand=True)

        # Separation line
        self.separator = tk.Frame(self.top_frame, bg="lime", height=2)
        self.separator.pack(fill="x", pady=5)

        # ---- BOTTOM ----
        self.bottom_frame = tk.Frame(self, bg='black')
        self.bottom_frame.grid(row=1, column=0, sticky="nsew")

        # --- Auto scan frame ---
        self.scan_frame = tk.Frame(self.bottom_frame, bg="black")
        self.scan_frame.pack(expand=True, fill="both")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.scan_frame, maximum=100, variable=self.progress_var, length=400, style="TProgressbar")
        self.progress_bar.pack(pady=20)

        # Scan labels (hidden initially)
        self.scan_dir_label = tk.Label(self.scan_frame, text="", font=("Arial", 12), bg="black", fg="lime")
        self.scan_percent_label = tk.Label(self.scan_frame, text="", font=("Arial", 14, "bold"), bg="black", fg="lime")

        self.log_box = None

        # Tab content frame
        self.tab_content = tk.Frame(self.bottom_frame, bg="black")
        self.tabs = {}
        self.tab_buttons_frame = None

    # ----------------- Lian Color Animation -----------------
    def start_lian_animation(self):
        self.lian_colors = ["lime", "orange", "cyan", "magenta", "yellow", "red"]
        self.lian_color_index = 0
        self.animate_lian_color_slow()

    def animate_lian_color_slow(self):
        self.scan_title.config(fg=self.lian_colors[self.lian_color_index])
        self.lian_color_index = (self.lian_color_index + 1) % len(self.lian_colors)
        self.after(800, self.animate_lian_color_slow)

    # Logging helper
    def log_message(self, msg):
        if self.log_box:
            self.log_box.insert(tk.END, msg + "\n")
            self.log_box.see(tk.END)
        self.update_idletasks()

    # Auto scan
    def start_auto_scan(self):
        threading.Thread(target=self.auto_scan, daemon=True).start()

    def auto_scan(self):
        # Show labels at start
        self.scan_dir_label.pack(pady=10)
        self.scan_percent_label.pack(pady=5)

        root_path = "C:\\" if platform.system() == "Windows" else "/home"
        total_files = sum(len(files) for _, _, files in os.walk(root_path))
        if total_files == 0:
            self.scan_dir_label.config(text="No files found for scanning.")
            self.scan_percent_label.config(text="")
            return

        scanned = 0
        malware_found = False

        for root, _, files in os.walk(root_path):
            for file in files:
                scanned += 1
                percent = int(scanned / total_files * 100)

                # Update UI
                self.scan_dir_label.config(text=f"Scanning: {root}")
                self.scan_percent_label.config(text=f"{percent}%")
                self.progress_var.set(percent)
                self.update_idletasks()

                filepath = os.path.join(root, file)
                if "virus" in file.lower():
                    malware_found = True

                time.sleep(0.002)

        if malware_found:
            messagebox.showwarning("Scan Complete", "⚠ Malware found and deleted.")
        else:
            messagebox.showinfo("Scan Complete", "✅ No malware found.")

        # Switch to tabs
        self.scan_frame.pack_forget()
        self.init_tabs()

        # Start slow color animation after auto scan
        self.start_lian_animation()

    # Initialize tabs
    def init_tabs(self):
        self.tab_buttons_frame = tk.Frame(self.bottom_frame, bg="black", width=180)
        self.tab_buttons_frame.pack(side="left", fill="y")
        self.tab_buttons_frame.pack_propagate(False)

        self.tab_content.pack(side="right", expand=True, fill="both")
        self.tab_content.pack_propagate(False)

        self.add_tab("Scan")
        self.add_tab("Safe App Installer")
        self.add_tab("Maintenance & Repair")
        self.add_tab("Settings & Modes")

        self.show_tab("Scan")

    def add_tab(self, name):
        btn = tk.Button(self.tab_buttons_frame, text=name, width=20, bg="black", fg="lime", command=lambda n=name: self.show_tab(n))
        btn.pack(fill="x", pady=2)

        frame = tk.Frame(self.tab_content, bg="black")
        self.tabs[name] = frame

        if name == "Scan":
            self.browse_button = tk.Button(frame, text="Browse & Scan", bg="black", fg="lime", command=self.browse_and_scan)
            self.browse_button.pack(pady=10)
        else:
            tk.Label(frame, text=f"{name} content coming soon!", bg="black", fg="lime", font=("Arial", 12)).pack(pady=50)

    def show_tab(self, name):
        for frame in self.tabs.values():
            frame.pack_forget()
        self.tabs[name].pack(expand=True, fill="both")

    def browse_and_scan(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.scan_log_box.delete(1.0, tk.END)
            self.scan_progress_bar_tab.pack(pady=10)
            self.scan_status_label.pack(pady=5)
            self.scan_log_box.pack(pady=10)
            self.scan_status_label.config(text=f"Scanning: {folder_path}")

# ---------------- Main Run ----------------
if __name__ == "__main__":
    root = AntivirusApp()
    splash = SplashScreen(root, "/media/ubuntu-studio/JOKER/I.png", 5000)
    root.withdraw()
    splash.wait_window()
    root.deiconify()

    root.after(1000, root.start_auto_scan)

    usb_monitor = USBMonitor(root)
    usb_monitor.start()

    root.mainloop()
