import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox
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

def scan_directory(directory):
    infected_files = []
    for root_dir, _, files in os.walk(directory):
        for name in files:
            file_path = os.path.join(root_dir, name)
            file_hash = compute_md5(file_path)
            if file_hash in malware_hashes:
                infected_files.append(file_path)
    return infected_files

def browse_and_scan(auto_dir=None):
    # If auto_dir provided, scan it automatically, else ask user
    folder_path = auto_dir if auto_dir else filedialog.askdirectory()
    if folder_path:
        infected = scan_directory(folder_path)
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
    # Remove fullscreen for custom window controls
    # app.attributes("-fullscreen",True)
    app.geometry("800x500")  # or any preferred size
    app.config(bg='lightblue')

    # Custom Window Control Buttons
    controls_frame = tk.Frame(app, bg='lightblue')
    controls_frame.pack(anchor='ne', padx=10, pady=5)

    min_btn = tk.Button(controls_frame, text='–', width=3, command=app.iconify)
    min_btn.pack(side='left', padx=2)

    def maximize_restore():
        if app.state() == 'zoomed':
            app.state('normal')
        else:
            app.state('zoomed')

    max_btn = tk.Button(controls_frame, text='⬜', width=3, command=maximize_restore)
    max_btn.pack(side='left', padx=2)

    close_btn = tk.Button(controls_frame, text='✕', width=3, command=app.destroy, fg='red')
    close_btn.pack(side='left', padx=2)

    tk.Label(app, text="jonathan Antivirus app", font=("Arial", 24), bg='lightblue').pack(pady=20)

    scan_btn = tk.Button(app, text="Browse and Scan", command=lambda: browse_and_scan())
    scan_btn.pack(pady=10)

    exit_btn = tk.Button(app, text="Exit", command=app.destroy)
    exit_btn.pack(pady=10)
    
    if auto_scan_dir:
        app.after(500, lambda: browse_and_scan(auto_scan_dir))

    app.mainloop()

create_antivirus_icon()

root = tk.Tk()
root.withdraw()

# Show splash typing animation
show_typing_splash(root, "reflector Antivirus ")

# After splash typing finishes (~delay * length + hold), start main app and scan
total_time = 150 * len("reflector Antivirus ") + 1000 + 100

# Put here the folder you want to scan automatically on start (change this path as you want)
default_scan_folder = os.path.expanduser("~")  # example: user's home folder

root.after(total_time, lambda: (root.destroy(), main_app(default_scan_folder)))

root.mainloop()

