from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import TextureStage, TransparencyAttrib, CardMaker
from panda3d.core import WindowProperties
from panda3d.core import loadPrcFileData
from panda3d.core import InputDevice
import math

# Add audio configuration
loadPrcFileData('', 'audio-library-name p3openal_audio')
loadPrcFileData('', 'win-size 1920 1080')
loadPrcFileData('', 'window-title My 2D Game')

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Initialize projectiles list
        self.projectiles = []
        self.projectile_speed = 0.03
        
        # Initialize trigger state
        self.last_trigger_state = 0

        # Initialize gamepad
        self.gamepad = None
        self.initGamepad()
        
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
            self.music = self.loader.loadSfx("music.mp3")
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
        
        # Initialize player position and movement
        self.player_pos = [0, 0]
        self.movement_speed = 0.02
        
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
        
    def initGamepad(self):
        devices = self.devices.getDevices(InputDevice.DeviceClass.gamepad)
        if devices:
            self.gamepad = devices[0]
            self.attachInputDevice(self.gamepad, prefix="gamepad")
            print("Gamepad connected:", self.gamepad.name)  # Changed from deviceClass.name to name
            
            # Set up gamepad button handlers
            self.accept("gamepad-face_a", self.toggleMusic)
            self.accept("gamepad-face_b", self.togglePause)
            self.accept("gamepad-face_y", self.toggleFullscreen)
        else:
            print("No gamepad detected")
        
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
        # Handle keyboard input
        dx = 0
        dy = 0
        
        if self.keys["arrow_left"]:
            dx -= self.movement_speed
        if self.keys["arrow_right"]:
            dx += self.movement_speed
        if self.keys["arrow_up"]:
            dy += self.movement_speed
        if self.keys["arrow_down"]:
            dy -= self.movement_speed
            
        # Handle gamepad input
        if self.gamepad:
            # Left analog stick
            left_x = self.gamepad.findAxis(InputDevice.Axis.left_x).value
            left_y = self.gamepad.findAxis(InputDevice.Axis.left_y).value
            
            # Add deadzone
            deadzone = 0.2
            if abs(left_x) < deadzone: left_x = 0
            if abs(left_y) < deadzone: left_y = 0
            
            # Add gamepad movement (removed the negative sign from left_y)
            dx += left_x * self.movement_speed
            dy += left_y * self.movement_speed  # Changed from dy -= to dy +=
            
            # D-pad support
            if self.gamepad.findButton("dpad_left").pressed:
                dx -= self.movement_speed
            if self.gamepad.findButton("dpad_right").pressed:
                dx += self.movement_speed
            if self.gamepad.findButton("dpad_up").pressed:
                dy += self.movement_speed
            if self.gamepad.findButton("dpad_down").pressed:
                dy -= self.movement_speed
        
        # Update position
        self.player_pos[0] += dx
        self.player_pos[1] += dy
            
        # Clamp position to screen bounds
        self.player_pos[0] = max(-self.aspect_ratio + 0.05, min(self.aspect_ratio - 0.05, self.player_pos[0]))
        self.player_pos[1] = max(-0.95, min(0.95, self.player_pos[1]))
        
        # Update player sprite position
        self.player.setPos(self.player_pos[0], 0, self.player_pos[1])



        # Handle projectile firing with right analog stick + trigger
        if self.gamepad:
            # Get right stick values
            right_x = self.gamepad.findAxis(InputDevice.Axis.right_x).value
            right_y = self.gamepad.findAxis(InputDevice.Axis.right_y).value
            
            # Get trigger value (try both possible trigger axes)
            trigger_value = max(
                self.gamepad.findAxis(InputDevice.Axis.right_trigger).value,
                self.gamepad.findAxis(InputDevice.Axis.right_y).value
            )
            
            # Calculate stick distance from center (magnitude)
            stick_magnitude = math.sqrt(right_x * right_x + right_y * right_y)
            
            # Only fire if stick is pushed AND trigger is pressed AND wasn't pressed last frame
            deadzone = 0.2
            if stick_magnitude > deadzone and trigger_value > 0.5 and self.last_trigger_state <= 0.5:
                # Normalize the direction vector
                direction_x = right_x / stick_magnitude
                direction_y = right_y / stick_magnitude
                self.createProjectile(direction_x, direction_y)
            
            self.last_trigger_state = trigger_value

        # Update projectiles
        for projectile in self.projectiles[:]:
            current_pos = projectile.getPos()
            # Get the projectile's direction from its Python tag
            direction = projectile.getPythonTag("direction")
            # Move projectile in its stored direction
            new_x = current_pos[0] + direction[0] * self.projectile_speed
            new_z = current_pos[2] + direction[1] * self.projectile_speed
            projectile.setPos(new_x, 0, new_z)
            
            # Remove if off screen (check all edges)
            if (new_x > self.aspect_ratio + 0.1 or 
                new_x < -self.aspect_ratio - 0.1 or 
                new_z > 1.1 or 
                new_z < -1.1):
                projectile.removeNode()
                self.projectiles.remove(projectile)
            
        return Task.cont

    def createProjectile(self, direction_x, direction_y):
        # Create a projectile using the orb image
        cm = CardMaker("projectile")
        projectile_size = 0.02
        cm.setFrame(-projectile_size, projectile_size, -projectile_size, projectile_size)
        projectile = self.render2d.attachNewNode(cm.generate())
        
        # Load and apply the orb texture
        projectile_tex = self.loader.loadTexture("orb.png")
        projectile.setTexture(projectile_tex)
        projectile.setTransparency(TransparencyAttrib.MAlpha)
        
        # Position it at the player's location
        projectile.setPos(self.player_pos[0], 0, self.player_pos[1])
        
        # Store the direction in the projectile node
        projectile.setPythonTag("direction", (direction_x, direction_y))
        
        # Add to projectiles list
        self.projectiles.append(projectile)

game = Game()
game.run()