from panda3d.core import loadPrcFileData



#pyinstaller --add-data "*.png;." --add-data "*.mp3;." --hidden-import direct.showbase.ShowBase --hidden-import panda3d.core --hidden-import direct.task --hidden-import direct.task.Task --hidden-import direct.gui --hidden-import direct.showbase --add-binary ".\.env\Lib\site-packages\panda3d\*;panda3d" --add-binary ".\.env\Lib\site-packages\panda3d\libpandagl.dll;." main.py

# Configure panda3d
loadPrcFileData('', '''
load-display pandagl
audio-library-name p3openal_audio
win-size 1920 1080
window-title Castle Bullet
''')


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    # Define common file extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    sound_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
    
