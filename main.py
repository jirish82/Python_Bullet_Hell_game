from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import TextureStage, TransparencyAttrib, CardMaker
from panda3d.core import WindowProperties
from panda3d.core import loadPrcFileData

# Configure the window for 2D
loadPrcFileData('', 'win-size 1920 1080')  # Default size, will scale properly on 4K
loadPrcFileData('', 'window-title My 2D Game')

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Disable mouse control of the camera
        self.disableMouse()
        
        # Set up proper aspect ratio handling
        wp = WindowProperties()
        wp.setSize(1920, 1080)  # Base resolution
        self.win.requestProperties(wp)
        
        # Calculate aspect ratio
        self.aspect_ratio = self.win.getXSize() / self.win.getYSize()
        
        # Set up orthographic camera
        lens = self.cam.node().getLens()
        lens.setFov(0.5)
        
        # Load and set up the background
        self.background = self.loader.loadTexture("map.png")
        cm = CardMaker("background")
        # Adjust background card to maintain aspect ratio
        cm.setFrame(-self.aspect_ratio, self.aspect_ratio, -1, 1)
        self.background_node = self.render2d.attachNewNode(cm.generate())
        self.background_node.setTexture(self.background)
        
        # Load and set up the player sprite
        cm = CardMaker("player")
        # Adjust player size relative to screen height
        player_size = 0.05
        aspect_adjusted_size = player_size * self.aspect_ratio
        cm.setFrame(-player_size, player_size, -player_size, player_size)
        self.player = self.render2d.attachNewNode(cm.generate())
        player_tex = self.loader.loadTexture("player.png")
        self.player.setTexture(player_tex)
        self.player.setTransparency(TransparencyAttrib.MAlpha)
        
        # Initialize player position
        self.player_pos = [0, 0]  # x, y coordinates
        
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
        
        # Add fullscreen toggle
        self.accept("f", self.toggleFullscreen)
        
        # Add the game loop update task
        self.taskMgr.add(self.update, "update")
        
    def toggleFullscreen(self):
        wp = self.win.getProperties()
        wp2 = WindowProperties()
        wp2.setFullscreen(not wp.getFullscreen())
        self.win.requestProperties(wp2)
        
    def updateKeyMap(self, key, value):
        self.keys[key] = value
        
    def update(self, task):
        # Movement speed (adjust as needed)
        speed = 0.02
        
        # Update position based on key states
        if self.keys["arrow_left"]:
            self.player_pos[0] -= speed
        if self.keys["arrow_right"]:
            self.player_pos[0] += speed
        if self.keys["arrow_up"]:
            self.player_pos[1] += speed
        if self.keys["arrow_down"]:
            self.player_pos[1] -= speed
            
        # Clamp position to screen bounds, accounting for aspect ratio
        self.player_pos[0] = max(-self.aspect_ratio + 0.05, min(self.aspect_ratio - 0.05, self.player_pos[0]))
        self.player_pos[1] = max(-0.95, min(0.95, self.player_pos[1]))
        
        # Update player sprite position
        self.player.setPos(self.player_pos[0], 0, self.player_pos[1])
        
        return Task.cont

game = Game()
game.run()