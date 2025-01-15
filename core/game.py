from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import TextureStage, TransparencyAttrib, CardMaker, PNMImage, Texture, TextNode
from panda3d.core import WindowProperties, InputDevice
import math
import random
from utils.resource_loader import get_resource_path


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Add these new speed-related variables
        self.initial_max_speed = 0.006  # Same as before
        self.max_enemy_speed = self.initial_max_speed
        self.min_speed_ratio = 0.1  # Starting minimum speed ratio
        self.speed_window_threshold = 0.5  # Trigger max speed increase at 50% instead of 80%
        self.max_speed_increase = 0.0005  # Same as before
        self.speed_difficulty_points = 3

        self.num_enemies = 3  # Start with 3 enemies
        self.base_num_enemies = 3  # Store the initial number
        self.enemies_per_score = 3  # Increase enemies every 3 points
        self.previous_enemy_increase = 0  # Track when we last increased enemies

        self.score = 0
        self.score_text = OnscreenText(
            text="Score: 0",
            pos=(-0.9, 0.9),  # Top left corner
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            shadow=(0, 0, 0, 1)
        )

        self.game_over = False
        self.game_over_text = OnscreenText(
            text="GAME OVER\nPress START or P to restart",
            pos=(0, 0),
            scale=0.1,
            fg=(1, 0, 0, 1),
            shadow=(0, 0, 0, 1)
        )
        self.game_over_text.hide()

        self.paused = True
    
        # Clear any existing bindings
        self.ignore_all()
        
        # Set up our pause controls
        self.accept("start", self.custom_toggle_pause)
        self.accept("gamepad-start", self.custom_toggle_pause)  # Try alternative name
        self.accept("p", self.custom_toggle_pause)
        
        # Debug print for all inputs
        def print_button(button):
            print(f"Button pressed: {button}")
        self.accept("*", print_button)

        self.pause_text = OnscreenText(
            text="PAUSED",
            pos=(0, 0),
            scale=0.1,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 1)
        )
        if self.paused:
            self.pause_text.show()
        else:
            self.pause_text.hide()

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
            self.music = self.loader.loadSfx(get_resource_path("music.mp3"))
            if self.music:
                self.music.setLoop(True)
                self.music.setVolume(0.8)
                self.music.play()
                self.music_playing = True
                self.music_paused = False
                self.music.stop()

                # Add these after your music setup
                self.enemy_death_sound = self.loader.loadSfx(get_resource_path("enemy_death.mp3"))
                self.gun_sound = self.loader.loadSfx(get_resource_path("gun.mp3"))
            else:
                print("Could not load music file")
                self.music_playing = False
                self.music_paused = False
        except Exception as e:
            print(f"Error loading music: {e}")
            self.music_playing = False
            self.music_paused = False

        # Load and set up the background
        self.background = self.loader.loadTexture(get_resource_path("map.png"))
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
        player_tex = self.loader.loadTexture(get_resource_path("player.png"))
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

    def custom_toggle_pause(self):
        if self.game_over:
            self.restart_game()
        else:
            self.paused = not self.paused
            if self.paused:
                self.pause_text.show()
                if hasattr(self, 'music') and self.music:
                    self.music.stop()
            else:
                self.pause_text.hide()
                if hasattr(self, 'music') and self.music:
                    self.music.play()

    def initGamepad(self):
        devices = self.devices.getDevices(InputDevice.DeviceClass.gamepad)
        if devices:
            self.gamepad = devices[0]
            self.attachInputDevice(self.gamepad, prefix="gamepad")
            print("Gamepad connected:", self.gamepad.name)
            
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
        if self.paused or self.game_over:
            return task.cont

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
            
            # Add gamepad movement
            dx += left_x * self.movement_speed
            dy += left_y * self.movement_speed
            
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
            right_x = self.gamepad.findAxis(InputDevice.Axis.right_x).value
            right_y = self.gamepad.findAxis(InputDevice.Axis.right_y).value
            trigger_value = self.gamepad.findAxis(InputDevice.Axis.right_trigger).value
            stick_magnitude = math.sqrt(right_x * right_x + right_y * right_y)
            current_time = task.time
            
            deadzone = 0.2
            if (stick_magnitude > deadzone and 
                trigger_value > 0.5 and 
                current_time - self.last_fire_time >= self.fire_rate):
                direction_x = right_x / stick_magnitude
                direction_y = right_y / stick_magnitude
                self.createProjectile(direction_x, direction_y)
                self.gun_sound.play()
                self.last_fire_time = current_time

        # Update projectiles
        for projectile in self.projectiles[:]:
            current_pos = projectile.getPos()
            direction = projectile.getPythonTag("direction")
            new_x = current_pos[0] + direction[0] * self.projectile_speed
            new_z = current_pos[2] + direction[1] * self.projectile_speed
            projectile.setPos(new_x, 0, new_z)
            
            if (new_x > self.aspect_ratio + 0.1 or 
                new_x < -self.aspect_ratio - 0.1 or 
                new_z > 1.1 or 
                new_z < -1.1):
                projectile.removeNode()
                self.projectiles.remove(projectile)

        # Update enemies
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
            
            new_x = max(min(new_x, self.aspect_ratio - 0.05), -self.aspect_ratio + 0.05)
            new_y = max(min(new_y, 0.95), -0.95)
            
            enemy.setPos(new_x, 0, new_y)
            
            if (abs(self.player_pos[0] - new_x) < 0.07 and 
                abs(self.player_pos[1] - new_y) < 0.07):
                self.game_over = True
                self.game_over_text.show()
                self.paused = True
                if hasattr(self, 'music') and self.music:
                    self.music.stop()
        
        # Check for projectile-enemy collisions
        for projectile in self.projectiles[:]:
            proj_pos = projectile.getPos()
            for enemy in self.enemies[:]:
                enemy_pos = enemy.getPos()
                if (abs(proj_pos[0] - enemy_pos[0]) < 0.07 and 
                    abs(proj_pos[2] - enemy_pos[2]) < 0.07):
                    self.create_explosion(enemy_pos[0], enemy_pos[2])
                    self.score += 1
                    self.score_text.setText(f"Score: {self.score}")
                    self.check_difficulty_increase()  # Add this line
                    self.enemy_data.pop(enemy)
                    enemy.removeNode()
                    projectile.removeNode()
                    self.enemies.remove(enemy)
                    self.enemy_death_sound.play()
                    self.projectiles.remove(projectile)
                    self.spawn_single_enemy()
                    break
        
        # Update explosions
        self.update_explosions(task)
        
        return Task.cont

    def createProjectile(self, direction_x, direction_y):
        cm = CardMaker("projectile")
        projectile_size = 0.02
        cm.setFrame(-projectile_size, projectile_size, -projectile_size, projectile_size)
        projectile = self.render2d.attachNewNode(cm.generate())
        
        projectile_tex = self.loader.loadTexture(get_resource_path("orb.png"))
        projectile.setTexture(projectile_tex)
        projectile.setTransparency(TransparencyAttrib.MAlpha)
        
        projectile.setPos(self.player_pos[0], 0, self.player_pos[1])
        projectile.setPythonTag("direction", (direction_x, direction_y))
        self.projectiles.append(projectile)

    def spawn_enemies(self):
        for _ in range(self.num_enemies):
            cm = CardMaker("enemy")
            enemy_size = 0.05
            cm.setFrame(-enemy_size, enemy_size, -enemy_size, enemy_size)
            enemy = self.render2d.attachNewNode(cm.generate())
            
            enemy_tex = self.loader.loadTexture(get_resource_path("enemy.png"))
            enemy.setTexture(enemy_tex)
            enemy.setTransparency(TransparencyAttrib.MAlpha)
            
            x = random.uniform(-self.aspect_ratio + enemy_size, self.aspect_ratio - enemy_size)
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)
            enemy.setPos(x, 0, y)
            
            self.enemy_data[enemy] = random.uniform(0.3 * self.max_enemy_speed, self.max_enemy_speed)
            self.enemies.append(enemy)

    def spawn_single_enemy(self):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        enemy_size = 0.05
        buffer = 0.1  # Small buffer distance outside the screen

        # Calculate spawn position based on side
        if side == 'top':
            x = random.uniform(-self.aspect_ratio + enemy_size, self.aspect_ratio - enemy_size)
            y = 1 + buffer
        elif side == 'bottom':
            x = random.uniform(-self.aspect_ratio + enemy_size, self.aspect_ratio - enemy_size)
            y = -1 - buffer
        elif side == 'left':
            x = -self.aspect_ratio - buffer
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)
        else:  # right
            x = self.aspect_ratio + buffer
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)

        # Create the enemy
        cm = CardMaker("enemy")
        cm.setFrame(-enemy_size, enemy_size, -enemy_size, enemy_size)
        enemy = self.render2d.attachNewNode(cm.generate())
        enemy_tex = self.loader.loadTexture(get_resource_path("enemy.png"))
        enemy.setTexture(enemy_tex)
        enemy.setTransparency(TransparencyAttrib.MAlpha)
        enemy.setPos(x, 0, y)
        
        # Calculate speed with progressive difficulty
        min_speed = self.max_enemy_speed * self.min_speed_ratio
        
        # Higher chance of max speed based on score
        max_speed_chance = min(0.8, 0.1 + (self.score / self.enemies_per_score * 0.1))
        
        if random.random() < max_speed_chance:
            speed = self.max_enemy_speed
        else:
            speed = random.uniform(min_speed, self.max_enemy_speed)
        
        self.enemy_data[enemy] = speed
        self.enemies.append(enemy)

    def create_explosion(self, pos_x, pos_y):
        explosion_size = 0.2
        cm = CardMaker("explosion")
        cm.setFrame(-explosion_size, explosion_size, -explosion_size, explosion_size)
        explosion = self.render2d.attachNewNode(cm.generate())
        
        texture_size = 128
        image = PNMImage(texture_size, texture_size, 4)
        center_x = texture_size // 2
        center_y = texture_size // 2
        radius = texture_size // 2
        
        image.fill(0, 0, 0)
        image.alphaFill(0)
        
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    noise = random.uniform(0.8, 1.0)
                    intensity = intensity * noise
                    
                    if distance < radius * 0.3:
                        image.setXel(x, y, 1.0, 1.0, 0.7)
                    elif distance < radius * 0.6:
                        image.setXel(x, y, 1.0, 0.5, 0.0)
                    else:
                        image.setXel(x, y, 1.0, 0.2, 0.0)
                    
                    if distance > radius * 0.7:
                        edge_factor = 1.0 - ((distance - radius * 0.7) / (radius * 0.3))
                        intensity *= edge_factor
                    
                    image.setAlpha(x, y, intensity)
        
        texture = Texture()
        texture.load(image)
        explosion.setTexture(texture)
        
        explosion.setBin('fixed', 100)
        explosion.setDepthTest(False)
        explosion.setDepthWrite(False)
        explosion.setTransparency(TransparencyAttrib.MAlpha)
        explosion.setPos(pos_x, 0, pos_y)
        
        initial_rotation = random.uniform(0, 360)
        explosion.setR(initial_rotation)
        
        self.explosion_data[explosion] = {
            'start_time': globalClock.getFrameTime(),
            'pos_x': pos_x,
            'pos_y': pos_y,
            'rotation_speed': random.uniform(-180, 180),
            'initial_rotation': initial_rotation
        }
        
        self.explosions.append(explosion)

    def update_explosions(self, task):
        if self.paused:
            return task.cont
        
        current_time = globalClock.getFrameTime()
        
        for explosion in self.explosions[:]:
            if explosion not in self.explosion_data:
                continue
                
            data = self.explosion_data[explosion]
            start_time = data['start_time']
            age = current_time - start_time
            
            if age > self.explosion_duration:
                explosion.removeNode()
                self.explosions.remove(explosion)
                self.explosion_data.pop(explosion)
                continue
            
            progress = age / self.explosion_duration
            scale_factor = math.sin(progress * math.pi) * 0.5 + 0.5
            current_size = 0.3 + (0.6 * scale_factor)
            explosion.setScale(current_size)
            
            rotation = data['initial_rotation'] + (data['rotation_speed'] * age)
            explosion.setR(rotation)
            
            if progress < 0.3:
                intensity = 1.0
            else:
                intensity = 1.0 - ((progress - 0.3) / 0.7)
                pulse = math.sin(progress * 20) * 0.1
                intensity = max(0, min(1, intensity + pulse))
            
            explosion.setColorScale(1, 1, 1, intensity)
        
        return task.cont

    def restart_game(self):
        # Reset game state
        self.game_over = False
        self.game_over_text.hide()
        self.pause_text.hide()
        self.paused = False

        # Reset speed-related variables
        self.max_enemy_speed = self.initial_max_speed
        self.min_speed_ratio = 0.3
        
        # Reset score and difficulty
        self.score = 0
        self.num_enemies = self.base_num_enemies  # Reset to initial number of enemies
        self.previous_enemy_increase = 0  # Reset difficulty tracking
        self.score_text.setText(f"Score: {self.score}")
        
        # Reset player position
        self.player_pos = [0, 0]
        self.player.setPos(0, 0, 0)
        
        # Clear existing enemies and projectiles
        for enemy in self.enemies:
            enemy.removeNode()
        self.enemies.clear()
        self.enemy_data.clear()
        
        for projectile in self.projectiles:
            projectile.removeNode()
        self.projectiles.clear()
        
        # Respawn initial enemies
        self.spawn_enemies()
        
        # Restart music if it exists
        if hasattr(self, 'music') and self.music:
            self.music.play()

    def check_difficulty_increase(self):
        difficulty_level = self.score // self.enemies_per_score
        if difficulty_level > self.previous_enemy_increase:
            # Increase number of enemies
            self.num_enemies += 1
            self.previous_enemy_increase = difficulty_level
            
            # Calculate new minimum speed ratio
            new_min_ratio = self.min_speed_ratio + (0.1 * difficulty_level)  # Increase by 10% each time
            
            # If minimum speed would be too close to max speed
            if new_min_ratio >= self.speed_window_threshold:
                # Increase max speed
                self.max_enemy_speed += self.max_speed_increase
                # Reset minimum speed ratio to create new window
                new_min_ratio = self.min_speed_ratio
            
            self.min_speed_ratio = min(new_min_ratio, self.speed_window_threshold)
            
            # Spawn the additional enemy
            self.spawn_single_enemy()