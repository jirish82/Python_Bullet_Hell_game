from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import TextureStage, TransparencyAttrib, CardMaker
from panda3d.core import WindowProperties
from panda3d.core import loadPrcFileData
from panda3d.core import InputDevice
import math
import random

# Add audio configuration
loadPrcFileData('', 'audio-library-name p3openal_audio')
loadPrcFileData('', 'win-size 1920 1080')
loadPrcFileData('', 'window-title My 2D Game')

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)


        # Calculate and store aspect ratio
        props = self.win.getProperties()
        self.aspect_ratio = props.getXSize() / props.getYSize()


        # Add these new variables with your other initializations
        self.explosions = []  # List to track active explosions
        self.explosion_duration = 0.3  # Duration in seconds
        self.explosion_data = {}  # Store start time and initial position for each explosion

        self.enemies = []
        self.max_enemy_speed = 0.01  # This is now the maximum speed
        self.num_enemies = 10
        
        # Dictionary to store enemy data
        self.enemy_data = {}  # Will store speeds keyed by enemy node
        
        # Create initial enemies
        self.spawn_enemies()    

        # Initialize projectiles list
        self.projectiles = []
        self.projectile_speed = 0.03
        
        # Initialize trigger state
        self.last_trigger_state = 0

        # Add fire rate control
        self.last_fire_time = 0
        self.fire_rate = 0.1  # Time in seconds between shots (adjust this to control fire rate)

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
            
            # Get trigger value
            trigger_value = self.gamepad.findAxis(InputDevice.Axis.right_trigger).value
            
            # Calculate stick distance from center (magnitude)
            stick_magnitude = math.sqrt(right_x * right_x + right_y * right_y)
            
            # Get current time
            current_time = task.time
            
            # Fire if stick is pushed AND trigger is pressed AND enough time has passed since last shot
            deadzone = 0.2
            if (stick_magnitude > deadzone and 
                trigger_value > 0.5 and 
                current_time - self.last_fire_time >= self.fire_rate):
                # Normalize the direction vector
                direction_x = right_x / stick_magnitude
                direction_y = right_y / stick_magnitude
                self.createProjectile(direction_x, direction_y)
                self.last_fire_time = current_time

        # Update projectiles
        for projectile in self.projectiles[:]:
            current_pos = projectile.getPos()
            direction = projectile.getPythonTag("direction")
            new_x = current_pos[0] + direction[0] * self.projectile_speed
            new_z = current_pos[2] + direction[1] * self.projectile_speed
            projectile.setPos(new_x, 0, new_z)
            
            # Remove if off screen
            if (new_x > self.aspect_ratio + 0.1 or 
                new_x < -self.aspect_ratio - 0.1 or 
                new_z > 1.1 or 
                new_z < -1.1):
                projectile.removeNode()
                self.projectiles.remove(projectile)

        # Update enemies (moved outside projectile loop)
        for enemy in self.enemies[:]:
            enemy_pos = enemy.getPos()
            player_pos = (self.player_pos[0], self.player_pos[1])
            
            dx = player_pos[0] - enemy_pos[0]
            dy = player_pos[1] - enemy_pos[2]
            
            distance = math.sqrt(dx * dx + dy * dy)
            if distance > 0:
                dx /= distance
                dy /= distance
            
            enemy_speed = self.enemy_data[enemy]
            new_x = enemy_pos[0] + dx * enemy_speed
            new_y = enemy_pos[2] + dy * enemy_speed
            
            # Keep enemy within screen bounds
            new_x = max(min(new_x, self.aspect_ratio - 0.05), -self.aspect_ratio + 0.05)
            new_y = max(min(new_y, 0.95), -0.95)
            
            enemy.setPos(new_x, 0, new_y)
            
            # Check for collision with player
            if (abs(self.player_pos[0] - new_x) < 0.07 and 
                abs(self.player_pos[1] - new_y) < 0.07):
                print("Game Over!")
        
        # Check for projectile-enemy collisions (separate loop)
        for projectile in self.projectiles[:]:
            proj_pos = projectile.getPos()
            for enemy in self.enemies[:]:
                enemy_pos = enemy.getPos()
                if (abs(proj_pos[0] - enemy_pos[0]) < 0.07 and 
                    abs(proj_pos[2] - enemy_pos[2]) < 0.07):
                    self.enemy_data.pop(enemy)
                    enemy.removeNode()
                    projectile.removeNode()
                    self.enemies.remove(enemy)
                    self.projectiles.remove(projectile)
                    self.spawn_single_enemy()
                    break
        
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

    def spawn_enemies(self):
        # Create enemies
        for _ in range(self.num_enemies):
            # Create enemy sprite
            cm = CardMaker("enemy")
            enemy_size = 0.05  # Adjust size as needed
            cm.setFrame(-enemy_size, enemy_size, -enemy_size, enemy_size)
            enemy = self.render2d.attachNewNode(cm.generate())
            
            # Load and apply enemy texture
            enemy_tex = self.loader.loadTexture("enemy.png")
            enemy.setTexture(enemy_tex)
            enemy.setTransparency(TransparencyAttrib.MAlpha)
            
            # Random position (keeping within screen bounds)
            x = random.uniform(-self.aspect_ratio + enemy_size, self.aspect_ratio - enemy_size)
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)
            enemy.setPos(x, 0, y)
            
            # Assign random speed between 30% and 100% of max speed
            self.enemy_data[enemy] = random.uniform(0.3 * self.max_enemy_speed, self.max_enemy_speed)
            
            # Add to enemies list
            self.enemies.append(enemy)

    def spawn_single_enemy(self):
        # Choose a random edge of the screen to spawn from
        side = random.choice(['top', 'bottom', 'left', 'right'])
        enemy_size = 0.05
        
        if side == 'top':
            x = random.uniform(-self.aspect_ratio + enemy_size, self.aspect_ratio - enemy_size)
            y = 1 - enemy_size
        elif side == 'bottom':
            x = random.uniform(-self.aspect_ratio + enemy_size, self.aspect_ratio - enemy_size)
            y = -1 + enemy_size
        elif side == 'left':
            x = -self.aspect_ratio + enemy_size
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)
        else:  # right
            x = self.aspect_ratio - enemy_size
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)
        
        # Create enemy sprite
        cm = CardMaker("enemy")
        cm.setFrame(-enemy_size, enemy_size, -enemy_size, enemy_size)
        enemy = self.render2d.attachNewNode(cm.generate())
        
        # Load and apply enemy texture
        enemy_tex = self.loader.loadTexture("enemy.png")
        enemy.setTexture(enemy_tex)
        enemy.setTransparency(TransparencyAttrib.MAlpha)
        
        # Set position
        enemy.setPos(x, 0, y)
        
        # Assign random speed between 30% and 100% of max speed
        self.enemy_data[enemy] = random.uniform(0.3 * self.max_enemy_speed, self.max_enemy_speed)
        
        # Add to enemies list
        self.enemies.append(enemy)

game = Game()
game.run()