# 🔥 Nexus Grabber Builder

**Nexus Grabber** is a modular, customizable Windows payload builder written in Python. It generates a standalone executable that collects Discord tokens, Roblox cookies, browser passwords/cookies, screenshots, clipboard data, Steam sessions, and local files – all exfiltrated via a Discord webhook.

> ⚠ **WARNING**  
> This tool is provided **exclusively for educational and authorized security testing**.  
> Misuse (e.g., stealing accounts, privacy violations) is illegal. The author is **not responsible** for any damage caused by this software.

---

## ✨ Features

- **Discord token stealer** – from desktop clients and browser cookies (Chrome, Edge, Brave, Opera, Vivaldi, Yandex, Amigo, Torch, Kometa, Orbitum, CentBrowser, 7Star, Sputnik, Chrome SxS, Epic, Uran, Iridium)
- **Roblox .ROBLOSECURITY cookie** – from all supported browsers + Firefox
- **Browser passwords** – AES‑GCM decryption for Chromium‑based browsers
- **Browser cookies** – exfiltrate any cookies (up to 200 per browser)
- **Screenshot** – captured as PNG, sent as file attachment
- **Clipboard** – text capture (Unicode + ANSI)
- **Steam session** – loginusers.vdf
- **File grabber** – collects files by extension (e.g., .txt, .docx, .pdf) from Desktop, Documents, Downloads; packs into a ZIP (optional password with 7‑Zip)
- **Persistence** – registry run key on startup
- **Anti‑VM & Anti‑analysis** – checks for VM drivers and analysis tools
- **IP logging** – public IP via api.ipify.org
- **Self‑delete** – removes the executable after execution (Windows batch delay)
- **Executable padding** – artificially inflate file size (e.g., 20 MB) to evade simple size‑based detection
- **Icon spoofing** – embed any custom .ico file

---

## 📦 Requirements (build environment)

- Python 3.8+ (Windows)
- Pip packages (automatically installed by `run.bat`):
  - `customtkinter`
  - `pillow`
  - `pywin32`
  - `psutil`
  - `cryptography`
  - `requests`
  - `pyinstaller`

---

## 🚀 Quick start

1. **Clone or download** this repository.
2. **Double‑click `run.bat`** – it installs dependencies and launches the builder GUI.
3. **Configure the builder**:
   - Paste your Discord webhook URL (where stolen data will be sent).
   - Set a ZIP password for the file grabber (optional).
   - Enable/disable features as you wish.
   - Choose a custom icon (.ico) and target file size (MB).
4. **Click "BUILD GRABBER"** – the final `.exe` will appear in the `dist` folder.
5. **Distribute the `.exe`** – the victim does **not** need Python.

---

## 🧩 How it works

When the generated executable is run on a Windows machine, it:

1. Performs anti‑VM and anti‑analysis checks (if enabled).
2. Adds itself to startup (if enabled).
3. Collects data using the enabled modules.
4. Sends the data to your Discord webhook (text messages + file attachments).
5. Optionally deletes itself.

All sensitive operations are performed in memory or with temporary files that are cleaned up.

---

## ⚙️ Builder GUI preview

![Builder GUI](https://cdn.discordapp.com/attachments/1503386227485966389/1503413141189427240/image.png?ex=6a034218&is=6a01f098&hm=87f200c7ac6b2d84f0d918190522aee97aca1148c65c773920cb29da9908729c&)

*(Concept – your actual GUI will look similar with dark theme & neon accents)*

---

## 📜 License & Disclaimer

This project is released under the **MIT License**.  
**By using this software, you agree that:**

- You will not use it for any illegal or unauthorized purpose.
- You are solely responsible for complying with all applicable laws and terms of service (Discord, Roblox, etc.).
- The author assumes no liability for any damage, data loss, or legal consequences arising from the use of this tool.

See the `LICENSE` file for full text.

---

## 🛠️ Troubleshooting

- **Missing modules after building** – make sure the template file (`Nexus_template.py`) is in the same folder as the builder.
- **File grabber does nothing** – check that you have selected file extensions and folders that actually exist on the target machine.
- **Browser passwords/cookies not found** – the target must have saved passwords in Chromium‑based browsers. The decryption works for Chrome/Edge v80+ (AES‑GCM).
- **Self‑delete fails** – Windows may block the batch deletion; it works in most cases. You can disable `MELT` to keep the exe.

---

## 📁 Files

| File | Description |
|------|-------------|
| `run.bat` | Installs dependencies and launches the builder GUI |
| `Nexus_grabber.py` | Builder script (GUI) |
| `Nexus_template.py` | Payload template (embedded in the final exe) |
| `.gitignore` | Standard Python ignores |
| `LICENSE` | MIT License with disclaimer |
| `README.md` | This file |

---

## 🙏 Credits

- Inspired by open‑source token grabbers and educational research.
- Uses AES‑GCM decryption method from Chromium’s `os_crypt`.

---

**Last updated:** 2026  
**Maintainer:** Nexus Project (educational purposes)
