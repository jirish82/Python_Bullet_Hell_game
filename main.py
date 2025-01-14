from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import TextureStage, TransparencyAttrib, CardMaker
from panda3d.core import WindowProperties
from panda3d.core import loadPrcFileData

# Add audio configuration
loadPrcFileData('', 'audio-library-name p3openal_audio')
loadPrcFileData('', 'win-size 1920 1080')
loadPrcFileData('', 'window-title My 2D Game')

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Disable mouse control of the camera
        self.disableMouse()
        
        # Set up proper aspect ratio handling
        wp = WindowProperties()
        wp.setSize(1920, 1080)
        self.win.requestProperties(wp)
        
        # Calculate aspect ratio
        self.aspect_ratio = self.win.getXSize() / self.win.getYSize()
        
        # Set up orthographic camera
        lens = self.cam.node().getLens()
        lens.setFov(0.5)
        
        # Load and play background music
        try:
            self.music = self.loader.loadSfx("music.mp3")  # Changed to loadSfx
            if self.music:
                self.music.setLoop(True)
                self.music.setVolume(0.8)
                self.music.play()
                self.music_playing = True
                self.music_paused = False
            else:
                print("Could not load music file")
                self.music_playing = False
                self.music_paused = False
        except Exception as e:
            print(f"Error loading music: {e}")
            self.music_playing = False
            self.music_paused = False
        
        # Rest of your initialization code...
        # [Previous code for background and player sprite remains the same]
        
        # Load and set up the background
        self.background = self.loader.loadTexture("map.png")
        cm = CardMaker("background")
        cm.setFrame(-self.aspect_ratio, self.aspect_ratio, -1, 1)
        self.background_node = self.render2d.attachNewNode(cm.generate())
        self.background_node.setTexture(self.background)
        
        # Load and set up the player sprite
        cm = CardMaker("player")
        player_size = 0.05
        aspect_adjusted_size = player_size * self.aspect_ratio
        cm.setFrame(-player_size, player_size, -player_size, player_size)
        self.player = self.render2d.attachNewNode(cm.generate())
        player_tex = self.loader.loadTexture("player.png")
        self.player.setTexture(player_tex)
        self.player.setTransparency(TransparencyAttrib.MAlpha)
        
        # Initialize player position
        self.player_pos = [0, 0]
        
        # Set up key monitoring
        self.keys = {}
        for key in ['arrow_left', 'arrow_right', 'arrow_up', 'arrow_down']:
            self.keys[key] = False
        
        # Set up key handlers
        self.accept("arrow_left", self.updateKeyMap, ["arrow_left", True])
        self.accept("arrow_left-up", self.updateKeyMap, ["arrow_left", False])
        self.accept("arrow_right", self.updateKeyMap, ["arrow_right", True])
        self.accept("arrow_right-up", self.updateKeyMap, ["arrow_right", False])
        self.accept("arrow_up", self.updateKeyMap, ["arrow_up", True])
        self.accept("arrow_up-up", self.updateKeyMap, ["arrow_up", False])
        self.accept("arrow_down", self.updateKeyMap, ["arrow_down", True])
        self.accept("arrow_down-up", self.updateKeyMap, ["arrow_down", False])
        
        # Add fullscreen toggle and music controls
        self.accept("f", self.toggleFullscreen)
        self.accept("m", self.toggleMusic)
        self.accept("p", self.togglePause)
        
        # Add the game loop update task
        self.taskMgr.add(self.update, "update")
        
    def toggleMusic(self):
        if hasattr(self, 'music') and self.music:
            if self.music_playing:
                self.music.setVolume(0)
                self.music_playing = False
            else:
                self.music.setVolume(0.8)
                self.music_playing = True
            
    def togglePause(self):
        if hasattr(self, 'music') and self.music:
            if self.music_paused:
                self.music.play()
                self.music_paused = False
            else:
                self.music.stop()
                self.music_paused = True
        
    def toggleFullscreen(self):
        wp = self.win.getProperties()
        wp2 = WindowProperties()
        wp2.setFullscreen(not wp.getFullscreen())
        self.win.requestProperties(wp2)
        
    def updateKeyMap(self, key, value):
        self.keys[key] = value
        
    def update(self, task):
        speed = 0.02
        
        if self.keys["arrow_left"]:
            self.player_pos[0] -= speed
        if self.keys["arrow_right"]:
            self.player_pos[0] += speed
        if self.keys["arrow_up"]:
            self.player_pos[1] += speed
        if self.keys["arrow_down"]:
            self.player_pos[1] -= speed
            
        self.player_pos[0] = max(-self.aspect_ratio + 0.05, min(self.aspect_ratio - 0.05, self.player_pos[0]))
        self.player_pos[1] = max(-0.95, min(0.95, self.player_pos[1]))
        
        self.player.setPos(self.player_pos[0], 0, self.player_pos[1])
        
        return Task.cont

game = Game()
game.run()