import os
import platform
import re
import subprocess
import sys
import urllib.parse
import webbrowser
from database import get_connection

def _log(*args, **kwargs):
    print("BACKEND:", *args, file=sys.stderr, **kwargs)

def _handle_url(resource: str) -> bool:
    url = urllib.parse.urlparse(resource)
    if not (url.scheme and url.netloc):
        return False
    if not webbrowser.open(resource):
        _log(f"Interpreted {resource} as a URL, yet failed to open it")
        return False
    return True

def _handle_file(resource: str) -> bool:
    filepath = os.path.expanduser(resource)

    if not (
        os.path.exists(filepath) or 
        re.search(r"(^\.{1,2}/)|(^[A-Za-z]:\\)|(\.\w+$)", filepath)
    ):
        return False
    
    system = platform.system()

    try:
        if system == "Windows":
            os.startfile(filepath)
        elif system == "Darwin":
            subprocess.run(["open", filepath])
        else:
            subprocess.run(["xdg-open", filepath])
    except (OSError, subprocess.CalledProcessError):
        _log(f"Interpreted {resource} as a file, yet failed to open it")
        return False

    return True

def _handle_app(resource: str) -> bool:
    system = platform.system()

    try:
        if system == "Windows":
            subprocess.run(f'start "" "{resource}"', shell=True, check=True)
        elif system == "Darwin":
            subprocess.run(["open", "-a", resource], check=True)
        elif system == "Linux":
            subprocess.Popen([resource], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        _log(f"Interpreted {resource} as an app, yet failed to open it")
        return False
    
    return True

def get_profiles() -> list:
    conn = get_connection()

    profiles = {}

    try:
        with conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, r.resource
                FROM profiles p
                LEFT JOIN resources r ON p.id = r.profile_id
                ORDER BY p.id
            """)

            rows = cursor.fetchall()

            for profile_id, name, resource in rows:
                if profile_id not in profiles:
                    profiles[profile_id] = {
                        "id": profile_id,
                        "name": name,
                        "resources": []
                    }
                if resource is not None:
                    profiles[profile_id]["resources"].append(resource)

            return list(profiles.values())
    except:
        _log("Failed to fetch profiles")
        return []
    finally:
        conn.close()
    

def save_profile(name: str, resources: list[str]) -> bool:
    """Persist a new profile. Return True on success."""
    conn = get_connection()

    try:
        with conn:
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO profiles (name) VALUES (?)", (name,))
            profile_id = cursor.lastrowid
            cursor.executemany(
                "INSERT INTO resources (profile_id, resource) VALUES (?, ?)",
                [(profile_id, resource) for resource in resources],
            )
    except:
        _log("Failed to save profile")
        return False
    finally:
        conn.close()

    return True
    
def delete_profile(profile_id: int) -> bool:
    """Delete a profile by ID. Return True on success."""
    conn = get_connection()

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    except:
        _log("Failed to delete profile")
        return False
    finally:
        conn.close()

    return True

def launch_profile(profile_id: int) -> bool:
    """Open all resources in the profile. Return True on success."""
    conn = get_connection()

    resources = []

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT resource FROM resources WHERE profile_id = ? """, (profile_id,))
            rows = cursor.fetchall()
            resources = [row[0] for row in rows]
    except:
        return False
    finally:
        conn.close()

    handlers = [_handle_url, _handle_file, _handle_app]
    
    for resource in resources:
        if not any((f(resource) for f in handlers)):
            return False
            
    return True
    
def add_resource(profile_id: int, resource: str) -> bool:
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO resources (profile_id, resource) VALUES (?, ?)", (profile_id, resource))
    except:
        return False
    finally:
        conn.close()
    return True

def remove_resource(profile_id: int, resource: str) -> bool:
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resources WHERE profile_id = ? AND resource = ?", (profile_id, resource))
    except:
        return False
    finally:
        conn.close()
    return True

def rename_profile(profile_id: int, new_name: str) -> bool:
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE profiles SET name = ? WHERE id = ?", (new_name, profile_id))
    except:
        return False
    finally:
        conn.close()
    return True

def edit_resource(profile_id: int, old_resource: str, new_resource: str) -> bool:
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE resources SET resource = ? WHERE profile_id = ? AND resource = ?",
                (new_resource, profile_id, old_resource)
            )
    except:
        return False
    finally:
        conn.close()
    return True