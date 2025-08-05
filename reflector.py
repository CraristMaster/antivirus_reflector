import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw

def create_antivirus_icon():
    if not os.path.exists("antivirus_icon.png"):
        img_size = (64, 64)
        img = Image.new("RGBA", img_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        shield_points = [(32,4),(12,16),(12,44),(32,60),(52,44),(52,16)]
        draw.polygon(shield_points, fill=(30,144,255,255), outline=(0,0,128))
        checkmark_points = [(20,32),(28,40),(44,20),(40,16),(28,32),(24,28)]
        draw.line(checkmark_points, fill="white", width=5, joint="curve")
        img.save("antivirus_icon.png")

malware_hashes = {
    "44d88612fea8a8f36de82e1278abb02f",
    "098f6bcd4621d373cade4e832627b4f6",
}

def compute_md5(file_path):
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                file_hash.update(chunk)
            return file_hash.hexdigest()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def scan_directory_with_progress(directory, progress_var, progress_bar, status_label, app):
    files_list = []
    for root_dir, _, files in os.walk(directory):
        for name in files:
            files_list.append(os.path.join(root_dir, name))
    total_files = len(files_list)
    infected_files = []
    for idx, file_path in enumerate(files_list):
        file_hash = compute_md5(file_path)
        if file_hash in malware_hashes:
            infected_files.append(file_path)
        # Update progress bar
        progress = int(((idx + 1) / total_files) * 100)
        progress_var.set(progress)
        status_label.config(text=f"Scanning: {os.path.basename(file_path)}")
        app.update_idletasks()
    return infected_files

def browse_and_scan_with_progress(app, progress_var, progress_bar, status_label):
    folder_path = filedialog.askdirectory()
    if folder_path:
        progress_var.set(0)
        progress_bar.pack()
        status_label.config(text="Starting scan...")
        app.update_idletasks()
        infected = scan_directory_with_progress(folder_path, progress_var, progress_bar, status_label, app)
        progress_var.set(100)
        status_label.config(text="Scan complete.")
        progress_bar.pack_forget()
        if infected:
            messagebox.showwarning("Threat Detected!", f"Infected files:\n\n" + "\n".join(infected))
        else:
            messagebox.showinfo("Scan Complete", "No threats found.")

def show_typing_splash(root, text, delay=150):
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x150+500+300")
    splash.config(bg="lightblue")

    label = tk.Label(splash, text="", font=("Arial", 24), bg="lightblue")
    label.pack(expand=True)

    def type_letter(i=0):
        if i <= len(text):
            label.config(text=text[:i])
            root.after(delay, type_letter, i+1)
        else:
            root.after(1000, splash.destroy)  # hold 1 sec then close splash

    type_letter()

def main_app(auto_scan_dir=None):
    app = tk.Tk()
    app.title("Reflector Antivirus")
    app.geometry("800x500")
    app.config(bg='lightblue')

    # --- Custom Window Controls ---
    controls_frame = tk.Frame(app, bg='lightblue')
    controls_frame.pack(anchor='ne', padx=10, pady=5)

 

    tk.Label(app, text="jonathan Antivirus app", font=("Arial", 24), bg='lightblue').pack(pady=20)

    # --- Progress Bar and Status ---
    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(app, variable=progress_var, maximum=100, length=350)
    progress_bar.pack(pady=10)
    progress_bar.pack_forget()  # Hide initially

    status_label = tk.Label(app, text="", font=("Arial", 12), bg='lightblue')
    status_label.pack()

    scan_btn = tk.Button(
        app, text="Browse and Scan",
        command=lambda: browse_and_scan_with_progress(app, progress_var, progress_bar, status_label)
    )
    scan_btn.pack(pady=10)

    exit_btn = tk.Button(app, text="Exit", command=app.destroy)
    exit_btn.pack(pady=10)

    if auto_scan_dir:
        def auto_scan():
            progress_var.set(0)
            progress_bar.pack()
            status_label.config(text="Starting scan...")
            app.update_idletasks()
            infected = scan_directory_with_progress(auto_scan_dir, progress_var, progress_bar, status_label, app)
            progress_var.set(100)
            status_label.config(text="Scan complete.")
            progress_bar.pack_forget()
            if infected:
                messagebox.showwarning("Threat Detected!", f"Infected files:\n\n" + "\n".join(infected))
            else:
                messagebox.showinfo("Scan Complete", "No threats found.")
        app.after(500, auto_scan)

    app.mainloop()

# --- Main Run ---
create_antivirus_icon()

root = tk.Tk()
root.withdraw()

# Show splash typing animation
show_typing_splash(root, "reflector Antivirus ")

# After splash typing finishes, start main app and scan
total_time = 150 * len("reflector Antivirus ") + 1000 + 100

# Put here the folder you want to scan automatically on start (change this path as you want)
default_scan_folder = os.path.expanduser("~")  # example: user's home folder

root.after(total_time, lambda: (root.destroy(), main_app(default_scan_folder)))

root.mainloop()
