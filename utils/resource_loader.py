import os
import sys
from pathlib import Path
from panda3d.core import loadPrcFileData
from utils.debug import out

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    # Define common file extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    sound_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
    
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    # Convert the relative path to Path object
    path_obj = Path(relative_path)
    extension = path_obj.suffix.lower()
    
    # Determine if file should go in a subdirectory
    if extension in image_extensions:
        relative_path = Path("images") / path_obj
    elif extension in sound_extensions:
        relative_path = Path("sounds") / path_obj
    
    # Convert to Path object and resolve
    full_path = Path(base_path) / relative_path
    full_path = full_path.resolve()
    
    # Convert to forward slashes and make relative
    unix_path = str(full_path).replace('\\', '/')
    
    # Remove drive letter if present (e.g., C:)
    if ':' in unix_path:
        unix_path = unix_path[unix_path.index(':') + 1:]
    
    out(f"Looking for resource: {relative_path}")
    out(f"Converted path: {unix_path}")
    out(f"File exists: {full_path.exists()}")
    
    return unix_path

# Add audio configuration
loadPrcFileData('', 'audio-library-name p3openal_audio')
loadPrcFileData('', 'win-size 1920 1080')
loadPrcFileData('', 'window-title Castle Bullet')