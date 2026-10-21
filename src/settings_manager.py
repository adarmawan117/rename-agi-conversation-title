import json
import os

def get_settings_file_path() -> str:
    """Returns absolute path to settings.json at project root."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(base_dir, "settings.json")
    if os.path.exists(target):
        return target
    if os.path.exists("settings.json"):
        return os.path.abspath("settings.json")
    return target


def load_settings():
    path = get_settings_file_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_settings(settings):
    path = get_settings_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
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
