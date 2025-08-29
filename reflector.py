import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import psutil
import platform

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
            label = tk.Label(self, text="Lian Antivirus Loading...", fg="green", bg="black", font=("Arial", 16))
            label.pack(expand=True)

        # Footer version bottom-left
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
                    self.app.scan_directory(device)   # Auto scan USB
            self.existing_devices = new_devices

# ---------------- Antivirus App ----------------
class AntivirusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lian the Antivirus")
        self.geometry("900x600")
        self.config(bg='black')

        try:
            self.iconphoto(False, tk.PhotoImage(file="/media/kali/reflector/lian/lian.png"))
        except:
            pass

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)
        self.grid_columnconfigure(0, weight=1)

        # ---- TOP ----
        self.top_frame = tk.Frame(self, bg='lightblue')
        self.top_frame.grid(row=0, column=0, sticky="nsew")
        self.scan_title = tk.Label(self.top_frame, text="AutoScan ", font=("Arial", 22), bg='lightblue')
        self.scan_title.pack(expand=True)

        # ---- BOTTOM ----
        self.bottom_frame = tk.Frame(self, bg='white')
        self.bottom_frame.grid(row=1, column=0, sticky="nsew")

        # --- Auto scan frame ---
        self.scan_frame = tk.Frame(self.bottom_frame, bg="white")
        self.scan_frame.pack(expand=True, fill="both")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.scan_frame, maximum=100, variable=self.progress_var, length=400)
        self.progress_bar.pack(pady=10)

        self.status_label = tk.Label(self.scan_frame, text="Preparing scan...", font=("Arial", 10), bg="white")
        self.status_label.pack(pady=5)

        # Note: No log box during auto-scan
        self.log_box = None

        # --- Tab content frame (hidden initially) ---
        self.tab_content = tk.Frame(self.bottom_frame, bg="white")
        self.tabs = {}
        self.tab_buttons_frame = None

    # ----------- Logging helper -----------
    def log_message(self, msg):
        # During auto-scan, show only status_label updates
        if self.log_box:
            self.log_box.insert(tk.END, msg + "\n")
            self.log_box.see(tk.END)
        self.status_label.config(text=msg)
        self.update_idletasks()

    # ----------- Auto Scan ----------- 
    def start_auto_scan(self):
        self.log_message("--- Auto Scan Started ---")
        threading.Thread(target=self.auto_scan, daemon=True).start()

    def auto_scan(self):
        # Detect root path based on OS
        if platform.system() == "Windows":
            root_path = "C:\\"
        else:
            root_path = "/home"

        total_files = 0
        for _, _, files in os.walk(root_path):
            total_files += len(files)

        if total_files == 0:
            self.log_message("No files found for scanning.")
            return

        scanned = 0
        malware_found = False  # Dummy flag

        for root, _, files in os.walk(root_path):
            for file in files:
                scanned += 1
                # Only show the directory being scanned in status
                self.status_label.config(text=f"Scanning directory: {root} ({int(scanned / total_files * 100)}%)")
                self.update_idletasks()

                filepath = os.path.join(root, file)
                # Fake malware detection rule
                if "virus" in file.lower():
                    malware_found = True

                time.sleep(0.002)  # simulate scanning speed
                self.progress_var.set((scanned / total_files) * 100)

        self.log_message("--- Auto Scan Finished ---")
        self.status_label.config(text="Scan Complete")
        self.scan_title.config(text="Auto Scan Complete")

        # Show alarm after scan
        if malware_found:
            messagebox.showwarning("Scan Complete", "⚠ Malware found and deleted.")
        else:
            messagebox.showinfo("Scan Complete", "✅ No malware found.")

        # Switch to normal tab view
        self.scan_frame.pack_forget()
        self.init_tabs()

    # ----------- Initialize Tabs -----------
    def init_tabs(self):
        # Left tab buttons
        self.tab_buttons_frame = tk.Frame(self.bottom_frame, bg="lightgrey", width=180)
        self.tab_buttons_frame.pack(side="left", fill="y")
        self.tab_buttons_frame.pack_propagate(False)

        # Right tab content
        self.tab_content.pack(side="right", expand=True, fill="both")
        self.tab_content.pack_propagate(False)

        # Create tabs
        self.add_tab("Scan")
        self.add_tab("Safe App Installer")
        self.add_tab("Maintenance & Repair")
        self.add_tab("Settings & Modes")

        # Show default tab
        self.show_tab("Scan")

    def add_tab(self, name):
        btn = tk.Button(self.tab_buttons_frame, text=name, width=20, command=lambda n=name: self.show_tab(n))
        btn.pack(fill="x", pady=2)

        frame = tk.Frame(self.tab_content, bg="white")
        self.tabs[name] = frame

        if name == "Scan":
            self.scan_progress_var = tk.DoubleVar()
            self.scan_progress_bar = ttk.Progressbar(frame, maximum=100, variable=self.scan_progress_var, length=400)
            self.scan_progress_bar.pack(pady=10)
            self.scan_status_label = tk.Label(frame, text="Ready to scan...", font=("Arial", 10), bg="white")
            self.scan_status_label.pack(pady=5)
            self.scan_log_box = tk.Text(frame, height=15, width=80, bg="black", fg="lime", font=("Courier", 9))
            self.scan_log_box.pack(pady=10)
            self.browse_button = tk.Button(frame, text="Browse & Scan", command=self.browse_and_scan)
            self.browse_button.pack(pady=10)
        else:
            tk.Label(frame, text=f"{name} content coming soon!", bg="white", font=("Arial", 12)).pack(pady=50)

    def show_tab(self, name):
        for frame in self.tabs.values():
            frame.pack_forget()
        self.tabs[name].pack(expand=True, fill="both")

    def browse_and_scan(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.scan_log_box.delete(1.0, tk.END)
            self.scan_progress_bar.pack(pady=10)
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

    # Auto scan on startup
    root.after(1000, root.start_auto_scan)

    # Start USB monitor
    usb_monitor = USBMonitor(root)
    usb_monitor.start()

    root.mainloop()
