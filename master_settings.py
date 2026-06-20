import json
import os
import plistlib
from pathlib import Path

def get_device_name(backup_dir: str) -> str:
    """Extract Device Name from Info.plist."""
    if not backup_dir:
        return "Dispositivo Sconosciuto"
    info_path = Path(backup_dir) / "Info.plist"
    if info_path.exists():
        try:
            with open(info_path, "rb") as f:
                info = plistlib.load(f)
                return info.get("Device Name", "Dispositivo Sconosciuto")
        except Exception:
            pass
    return "Dispositivo Sconosciuto"

def get_master_settings_path() -> Path:
    """Return the path to the master settings JSON file."""
    base_dir = Path(__file__).parent / "0-Exportes"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "master_settings.json"

def load_master_settings() -> dict:
    """Load the full master settings dictionary."""
    path = get_master_settings_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_master_settings(settings: dict):
    """Save the full master settings dictionary."""
    path = get_master_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def get_device_exclusions(device_name: str) -> dict:
    """Get exclusions for a specific device. Returns a dict with 'names' and 'numbers' lists."""
    settings = load_master_settings()
    devices = settings.setdefault("devices", {})
    return devices.get(device_name, {"names": [], "numbers": []})

def save_device_exclusions(device_name: str, exclusions: dict):
    """Save exclusions for a specific device."""
    settings = load_master_settings()
    devices = settings.setdefault("devices", {})
    devices[device_name] = exclusions
    save_master_settings(settings)

def is_excluded(contact_name: str, phone_number: str, exclusions: dict) -> bool:
    """Check if a contact should be excluded based on the device's exclusion rules."""
    if not exclusions:
        return False
        
    contact_name = (contact_name or "").strip().lower()
    phone_number = (phone_number or "").strip()
    
    # Strip Excel formatting if present for accurate comparison
    if contact_name.startswith('="') and contact_name.endswith('"'):
        contact_name = contact_name[2:-1]
    if phone_number.startswith('="') and phone_number.endswith('"'):
        phone_number = phone_number[2:-1]
    
    # Check numbers
    for exc_num in exclusions.get("numbers", []):
        exc_num_clean = exc_num.strip()
        if exc_num_clean and exc_num_clean in phone_number:
            return True
            
    # Check names
    for exc_name in exclusions.get("names", []):
        exc_name_clean = exc_name.strip().lower()
        if exc_name_clean and exc_name_clean in contact_name:
            return True
            
    return False
