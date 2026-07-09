import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Failed to save settings: {e}")

def get_agi_path():
    settings = load_settings()
    path = settings.get("agi_path", "")
    
    # Check default path if empty or invalid
    if not path or not os.path.exists(path):
        default_path = os.path.expanduser(r"~\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe")
        if os.path.exists(default_path):
            return default_path
        return ""
    return path

def save_agi_path(path):
    settings = load_settings()
    settings["agi_path"] = path
    save_settings(settings)
