from typing import List, Dict


try:
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.afc import AfcService
    from pymobiledevice3.exceptions import NoDeviceConnectedError
    PYMOBILEDEVICE_AVAILABLE = True
except ImportError:
    PYMOBILEDEVICE_AVAILABLE = False


def get_connected_device_info() -> str:
    """Returns the name/identifier of the connected device or raises an error."""
    if not PYMOBILEDEVICE_AVAILABLE:
        raise ImportError("La libreria pymobiledevice3 non è installata.")
        
    try:
        lockdown = create_using_usbmux()
        device_name = lockdown.short_info.get("DeviceName", "iPhone Sconosciuto")
        ios_version = lockdown.short_info.get("ProductVersion", "Sconosciuta")
        return f"{device_name} (iOS {ios_version})"
    except NoDeviceConnectedError:
        raise Exception("Nessun dispositivo iOS rilevato tramite USB/Wi-Fi. Assicurati che sia collegato e sbloccato ('Autorizza questo computer').")
    except Exception as e:
        raise Exception(f"Errore di connessione al dispositivo: {e}")


def list_live_files(path: str = "/") -> List[Dict]:
    """
    List files and directories in the given path using AFC.
    Returns a list of dicts: {"name": str, "path": str, "is_dir": bool}
    """
    if not PYMOBILEDEVICE_AVAILABLE:
        raise ImportError("La libreria pymobiledevice3 non è installata.")

    files = []
    try:
        lockdown = create_using_usbmux()
        with AfcService(lockdown) as afc:
            # afc.ls() returns a list of names
            items = afc.ls(path)
            for item in items:
                if item in (".", ".."):
                    continue
                
                full_path = f"{path}/{item}" if path != "/" else f"/{item}"
                # afc.stat() gives info. st_ifmt can tell if dir or file, but we can just use afc.resolve_path or check stat dict
                try:
                    stat_info = afc.stat(full_path)
                    is_dir = stat_info.get("st_ifmt", "") == "S_IFDIR"
                except Exception:
                    is_dir = False
                    
                files.append({
                    "name": item,
                    "path": full_path,
                    "is_dir": is_dir
                })
    except NoDeviceConnectedError:
        raise Exception("Dispositivo non connesso.")
    except Exception as e:
        raise Exception(f"Errore di lettura percorso {path}: {e}")
        
    # Sort directories first
    files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return files


def extract_live_file(remote_path: str, local_path: str) -> None:
    """Extract a file from the connected device to the local PC."""
    if not PYMOBILEDEVICE_AVAILABLE:
        raise ImportError("La libreria pymobiledevice3 non è installata.")

    try:
        lockdown = create_using_usbmux()
        with AfcService(lockdown) as afc:
            data = afc.get_file_contents(remote_path)
            with open(local_path, "wb") as f:
                f.write(data)
    except Exception as e:
        raise Exception(f"Errore durante l'estrazione di {remote_path}: {e}")
