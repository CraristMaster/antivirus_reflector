import tkinter as tk
from tkinter import filedialog, messagebox
from antivirus_scanner import scan_directory

def browse_and_scan():
    folder_path = filedialog.askdirectory()
    if folder_path:
        infected = scan_directory(folder_path)
        if infected:
            messagebox.showwarning("Threat Detected!", f"Infected files:\n\n" + "\n".join(infected))
        else:
            messagebox.showinfo("Scan Complete", "No threats found.")

app = tk.Tk()
app.title("Simple Antivirus Scanner")
app.geometry("300x150")

tk.Label(app, text="Antivirus App", font=("Arial", 14)).pack(pady=10)
tk.Button(app, text="Scan Folder", command=browse_and_scan).pack(pady=20)

app.mainloop()
