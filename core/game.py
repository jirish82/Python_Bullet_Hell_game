from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import TextureStage, TransparencyAttrib, CardMaker, PNMImage, Texture, TextNode
from panda3d.core import WindowProperties, InputDevice
import math
import random
from utils.resource_loader import get_resource_path
from utils.debug import out
import time


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.dash_trail_particles = []
        self.dash_arc = None
        self.dash_glow = None
        self.trail_lifetime = 0.4  # Increased from 0.3
        self.max_trail_particles = 15  # Increased from 10

        self.dash_cooldown = 0.5  # Time between dashes
        self.last_dash_time = 0
        self.dash_distance = 0.6  # 30% of screen width
        self.is_dashing = False
        self.dash_duration = 0.15  # How long the dash animation lasts
        self.dash_start_time = 0
        self.dash_start_pos = None
        self.dash_target_pos = None

        # Add these new speed-related variables
        self.speed_base_min = 0.001
        self.speed_base_max = 0.003
        self.speed_min_increase_rate = 0.0001  # per second
        self.speed_max_increase_rate = 0.0002  # per second
        self.game_start_time = time.time()

        # Initialize enemy-related variables first
        self.num_enemies = 10  # Start with 10 enemies
        self.enemy_limit = self.num_enemies  # Track max allowed enemies separately
        self.base_num_enemies = 10  # Store the initial number
        self.enemies_per_score = 8  # Increase enemies every 10 points
        self.previous_enemy_increase = 0  # Track when we last increased enemies

        # Add orb-related variables
        self.green_orb = None
        self.orb_spawn_time = None
        self.orb_duration = 2.0  # 3 seconds
        self.orb_points_interval = 10  # Spawn orb every 10 points
        self.last_orb_spawn_score = 0

        self.blue_orb = None
        self.blue_orb_spawn_time = None
        self.blue_orb_duration = 3.0  # 3 seconds
        self.blue_orb_interval = 11.0  # Spawn every 11 seconds
        self.last_blue_orb_spawn_time = time.time()

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
            out(f"Button pressed: {button}", 2)
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
                self.music.setVolume(0.1)
                self.music.play()
                self.music_playing = True
                self.music_paused = False
                self.music.stop()

                # Add these after your music setup
                self.enemy_death_sound = self.loader.loadSfx(get_resource_path("enemy_death.mp3"))
                self.enemy_death_sound.setVolume(0.3)  # Add this line
                self.gun_sound = self.loader.loadSfx(get_resource_path("gun.mp3"))
                self.gun_sound.setVolume(0.3)  # Add this line
            else:
                out("Could not load music file")
                self.music_playing = False
                self.music_paused = False
        except Exception as e:
            out(f"Error loading music: {e}")
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

        self.debug_text = OnscreenText(
        text="",
        pos=(self.aspect_ratio - 0.1, 0.9),  # Top right position
        scale=0.04,
        fg=(1, 1, 1, 1),  # White text
        align=TextNode.ARight,
        mayChange=True,
        bg=(0, 0, 0, 0.5)  # Semi-transparent black background
    )

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
            out(f"Gamepad connected: {self.gamepad.name}", 2)
            
            # Set up gamepad button handlers
            self.accept("gamepad-face_a", self.toggleMusic)
            self.accept("gamepad-face_b", self.togglePause)
            self.accept("gamepad-face_y", self.toggleFullscreen)

            # Try multiple possible shoulder button names
            possible_buttons = [
                "gamepad-right_shoulder",
                "gamepad-rshoulder",
                "gamepad-r1",
                "gamepad-shoulder_right",
                "gamepad-rtrigger"
            ]
            
            for button in possible_buttons:
                out(f"Attempting to bind to button: {button}", 2)
                self.accept(button, self.debug_button)
        else:
            out("No gamepad detected", 2)
        
    def toggleMusic(self):
        if hasattr(self, 'music') and self.music:
            if self.music_playing:
                self.music.setVolume(0)
                self.music_playing = False
            else:
                self.music.setVolume(0.5)
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

        # Update dash animation
        self.update_dash(task)
        
        

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
                #trigger_value > 0.5 and 
                current_time - self.last_fire_time >= self.fire_rate):
                direction_x = right_x / stick_magnitude
                direction_y = right_y / stick_magnitude
                self.createProjectile(direction_x, direction_y)
                self.gun_sound.play()
                self.last_fire_time = current_time

            # Handle dash with right shoulder button
            right_shoulder = self.gamepad.findButton("right_shoulder")
            if right_shoulder:
                out(f"Update method - Right shoulder button state: {right_shoulder.pressed}", 2)
                if right_shoulder.pressed:
                    right_x = self.gamepad.findAxis(InputDevice.Axis.right_x).value
                    right_y = self.gamepad.findAxis(InputDevice.Axis.right_y).value
                    out(f"Update method - Dash triggered with stick values: {right_x}, {right_y}", 2)
                    self.perform_dash(right_x, right_y)

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
                    self.check_difficulty_increase()
                    self.enemy_data.pop(enemy)
                    enemy.removeNode()
                    projectile.removeNode()
                    self.enemies.remove(enemy)
                    self.enemy_death_sound.play()
                    self.projectiles.remove(projectile)
                    # Only spawn new enemy if we're below the current enemy limit
                    if len(self.enemies) < self.enemy_limit:
                        self.spawn_single_enemy()
                    break
        
        # Update explosions
        self.update_explosions(task)

        self.update_orb()
        self.check_orb_collection()

        self.update_blue_orb()
        self.check_blue_orb_collection()

        self.update_debug_text()
        
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
            
            # Calculate time-based speed limits
            seconds_elapsed = time.time() - self.game_start_time
            current_min = self.speed_base_min + (self.speed_min_increase_rate * seconds_elapsed)
            current_max = self.speed_base_max + (self.speed_max_increase_rate * seconds_elapsed)
            
            # Random speed between current limits
            speed = random.uniform(current_min, current_max)
            self.enemy_data[enemy] = speed
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
        
        # Calculate time-based speed limits
        seconds_elapsed = time.time() - self.game_start_time
        current_min = self.speed_base_min + (self.speed_min_increase_rate * seconds_elapsed)
        current_max = self.speed_base_max + (self.speed_max_increase_rate * seconds_elapsed)
        
        # Random speed between current limits
        speed = random.uniform(current_min, current_max)
        self.enemy_data[enemy] = speed
        self.enemies.append(enemy)

    def create_explosion(self, pos_x, pos_y, is_aoe=False):
        # Make AoE explosions larger
        explosion_size = 0.3 if is_aoe else 0.2
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
        
        # Use different colors for AoE explosions
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    noise = random.uniform(0.8, 1.0)
                    intensity = intensity * noise
                    
                    if is_aoe:
                        # Blue-white explosion for AoE
                        if distance < radius * 0.3:
                            image.setXel(x, y, 0.9, 0.95, 1.0)  # White-blue core
                        elif distance < radius * 0.6:
                            image.setXel(x, y, 0.4, 0.6, 1.0)  # Bright blue
                        else:
                            image.setXel(x, y, 0.2, 0.4, 0.8)  # Darker blue
                    else:
                        # Original orange explosion for dash hits
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
            'initial_rotation': initial_rotation,
            'is_aoe': is_aoe
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
            is_aoe = data.get('is_aoe', False)
            
            if age > self.explosion_duration:
                explosion.removeNode()
                self.explosions.remove(explosion)
                self.explosion_data.pop(explosion)
                continue
            
            progress = age / self.explosion_duration
            scale_factor = math.sin(progress * math.pi) * 0.5 + 0.5
            # Larger scale for AoE explosions
            base_size = 0.4 if is_aoe else 0.3
            max_size = 0.8 if is_aoe else 0.6
            current_size = base_size + (max_size * scale_factor)
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

        self.enemy_limit = self.base_num_enemies
        if self.green_orb:
            self.green_orb.removeNode()
            self.green_orb = None
        self.last_orb_spawn_score = 0

        if self.blue_orb:
            self.blue_orb.removeNode()
            self.blue_orb = None
        self.last_blue_orb_spawn_time = time.time()

        # Reset speed-related variables
        self.game_start_time = time.time()
        
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
            # Increase both the limit and current number
            self.num_enemies += 1
            self.enemy_limit = self.num_enemies  # Update the limit too
            self.previous_enemy_increase = difficulty_level
            
            # Spawn the additional enemy immediately
            self.spawn_single_enemy()

    def create_green_orb(self):
        if self.green_orb:  # Remove existing orb if there is one
            self.green_orb.removeNode()
            
        cm = CardMaker("green_orb")
        orb_size = 0.05
        cm.setFrame(-orb_size, orb_size, -orb_size, orb_size)
        self.green_orb = self.render2d.attachNewNode(cm.generate())
        
        # Create a more vibrant green glowing texture
        texture_size = 128  # Increased texture size for better quality
        image = PNMImage(texture_size, texture_size, 4)
        center_x = texture_size // 2
        center_y = texture_size // 2
        radius = texture_size // 2
        
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    # Make the glow effect stronger
                    intensity = intensity ** 0.5  # This makes the falloff less steep
                    
                    # Bright core
                    if distance < radius * 0.3:
                        # White-green center
                        image.setXel(x, y, 0.8, 1.0, 0.8)
                        image.setAlpha(x, y, 1.0)
                    else:
                        # Vibrant green glow
                        image.setXel(x, y, 0.2, 1.0, 0.2)
                        image.setAlpha(x, y, min(1.0, intensity * 1.5))  # Increased alpha
                else:
                    image.setAlpha(x, y, 0)
        
        texture = Texture()
        texture.load(image)
        self.green_orb.setTexture(texture)
        self.green_orb.setTransparency(TransparencyAttrib.MAlpha)
        
        # Make it render on top of other elements
        self.green_orb.setBin('fixed', 100)
        self.green_orb.setDepthTest(False)
        self.green_orb.setDepthWrite(False)
        
        # Random position within visible bounds, now 10% more constrained
        x = random.uniform(-self.aspect_ratio * 0.9 + 0.1, self.aspect_ratio * 0.9 - 0.1)
        y = random.uniform(-0.8, 0.8)  # Changed from -0.9, 0.9 to -0.8, 0.8
        self.green_orb.setPos(x, 0, y)
        
        self.orb_spawn_time = time.time()
        
        # Add pulsing effect
        self.orb_scale = 1.0
        taskMgr.add(self.pulse_orb, "pulseOrb")

    def pulse_orb(self, task):
        if not self.green_orb:
            return Task.done
        
        pulse_speed = 3.0  # Adjust this to change pulse speed
        pulse_magnitude = 0.2  # Adjust this to change pulse size
        
        # Calculate scale based on sine wave
        base_scale = 1.0
        pulse = math.sin(task.time * pulse_speed) * pulse_magnitude
        new_scale = base_scale + pulse
        
        self.green_orb.setScale(new_scale)
        
        return Task.cont

    def check_orb_collection(self):
        if not self.green_orb:
            return
            
        orb_pos = self.green_orb.getPos()
        if (abs(self.player_pos[0] - orb_pos[0]) < 0.1 and 
            abs(self.player_pos[1] - orb_pos[2]) < 0.1):
            # Collected the orb
            if self.enemy_limit > 1:  # Don't go below 1 enemy
                self.enemy_limit -= 1
            self.green_orb.removeNode()
            self.green_orb = None

    def update_orb(self):
        current_time = time.time()
        
        # Check if we should spawn a new orb
        if self.score > 0 and self.score % self.orb_points_interval == 0 and self.score != self.last_orb_spawn_score:
            self.create_green_orb()
            self.last_orb_spawn_score = self.score
        
        # Remove orb if it's been there too long
        if self.green_orb and self.orb_spawn_time:
            if current_time - self.orb_spawn_time > self.orb_duration:
                self.green_orb.removeNode()
                self.green_orb = None

    def create_blue_orb(self):
        if self.blue_orb:  # Remove existing orb if there is one
            self.blue_orb.removeNode()
            
        cm = CardMaker("blue_orb")
        orb_size = 0.05
        cm.setFrame(-orb_size, orb_size, -orb_size, orb_size)
        self.blue_orb = self.render2d.attachNewNode(cm.generate())
        
        # Create a vibrant blue glowing texture
        texture_size = 128
        image = PNMImage(texture_size, texture_size, 4)
        center_x = texture_size // 2
        center_y = texture_size // 2
        radius = texture_size // 2
        
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    intensity = intensity ** 0.5
                    
                    if distance < radius * 0.3:
                        # White-blue center
                        image.setXel(x, y, 0.8, 0.8, 1.0)
                        image.setAlpha(x, y, 1.0)
                    else:
                        # Vibrant blue glow
                        image.setXel(x, y, 0.2, 0.2, 1.0)
                        image.setAlpha(x, y, min(1.0, intensity * 1.5))
                else:
                    image.setAlpha(x, y, 0)
        
        texture = Texture()
        texture.load(image)
        self.blue_orb.setTexture(texture)
        self.blue_orb.setTransparency(TransparencyAttrib.MAlpha)
        
        self.blue_orb.setBin('fixed', 100)
        self.blue_orb.setDepthTest(False)
        self.blue_orb.setDepthWrite(False)
        
        # Random position within visible bounds, 10% constrained
        x = random.uniform(-self.aspect_ratio * 0.9 + 0.1, self.aspect_ratio * 0.9 - 0.1)
        y = random.uniform(-0.8, 0.8)
        self.blue_orb.setPos(x, 0, y)
        
        self.blue_orb_spawn_time = time.time()
        
        taskMgr.add(self.pulse_blue_orb, "pulseBlueOrb")

    def pulse_blue_orb(self, task):
        if not self.blue_orb:
            return Task.done
        
        pulse_speed = 3.0
        pulse_magnitude = 0.2
        
        base_scale = 1.0
        pulse = math.sin(task.time * pulse_speed) * pulse_magnitude
        new_scale = base_scale + pulse
        
        self.blue_orb.setScale(new_scale)
        
        return Task.cont

    def check_blue_orb_collection(self):
        if not self.blue_orb:
            return
            
        orb_pos = self.blue_orb.getPos()
        if (abs(self.player_pos[0] - orb_pos[0]) < 0.1 and 
            abs(self.player_pos[1] - orb_pos[2]) < 0.1):
            # Collected the blue orb - add 10 seconds to game_start_time
            self.game_start_time += 10
            self.blue_orb.removeNode()
            self.blue_orb = None

    def update_blue_orb(self):
        current_time = time.time()
        
        # Check if we should spawn a new blue orb
        if current_time - self.last_blue_orb_spawn_time >= self.blue_orb_interval:
            self.create_blue_orb()
            self.last_blue_orb_spawn_time = current_time
        
        # Remove orb if it's been there too long
        if self.blue_orb and self.blue_orb_spawn_time:
            if current_time - self.blue_orb_spawn_time > self.blue_orb_duration:
                self.blue_orb.removeNode()
                self.blue_orb = None

    def update_debug_text(self):
        current_time = time.time()
        effective_time = current_time - self.game_start_time
        
        debug_str = (
            f"Enemy Limit: {self.enemy_limit}\n"
            f"Game Time: {effective_time:.1f}s"
        )
        
        self.debug_text.setText(debug_str)

    def perform_dash(self, direction_x, direction_y):
        current_time = time.time()
        out(f"Dash attempt - direction: ({direction_x}, {direction_y})", 2)
        
        if current_time - self.last_dash_time < self.dash_cooldown or self.is_dashing:
            out("Dash blocked by cooldown or already dashing", 2)
            return
                
        # Normalize direction
        magnitude = math.sqrt(direction_x * direction_x + direction_y * direction_y)
        if magnitude < 0.2:  # Don't dash if stick barely moved
            out("Dash blocked by small stick movement", 2)
            return
                
        direction_x /= magnitude
        direction_y /= magnitude
        
        # Store start position
        self.dash_start_pos = [self.player_pos[0], self.player_pos[1]]
        
        # Calculate dash end position
        target_x = self.player_pos[0] + direction_x * self.dash_distance
        target_y = self.player_pos[1] + direction_y * self.dash_distance
        
        # Clamp to screen bounds
        target_x = max(-self.aspect_ratio + 0.05, min(self.aspect_ratio - 0.05, target_x))
        target_y = max(-0.95, min(0.95, target_y))
        
        self.dash_target_pos = [target_x, target_y]
        
        out(f"Dash executing - from: ({self.dash_start_pos[0]}, {self.dash_start_pos[1]}) to: ({target_x}, {target_y})", 2)
        
        # Start dash
        self.is_dashing = True
        self.dash_start_time = current_time
        self.last_dash_time = current_time

        # Create initial visual effects
        if not self.dash_arc:
            self.create_dash_visuals()
        
        # Calculate angle for the arc
        angle = math.atan2(direction_y, direction_x)
        self.dash_arc.setR(-math.degrees(angle) - 45)  # -45 to align the quarter circle
        self.dash_arc.setPos(self.player_pos[0], 0, self.player_pos[1])
        self.dash_arc.show()
        
        self.dash_glow.setPos(self.player_pos[0], 0, self.player_pos[1])
        self.dash_glow.show()

    def update_dash(self, task):
        if not self.is_dashing:
            return
                
        current_time = time.time()
        progress = (current_time - self.dash_start_time) / self.dash_duration
        
        if progress >= 1.0:
            # Dash complete
            self.is_dashing = False
            self.player_pos[0] = self.dash_target_pos[0]
            self.player_pos[1] = self.dash_target_pos[1]
            self.player.setPos(self.dash_target_pos[0], 0, self.dash_target_pos[1])
            
            # Clean up visual effects
            self.dash_arc.hide()
            self.dash_glow.hide()
            
            # Clean up trail particles
            for particle in self.dash_trail_particles[:]:
                particle['node'].removeNode()
            self.dash_trail_particles.clear()
            
            return
        
        # Update dash visuals
        t = 1 - (1 - progress) * (1 - progress)  # Quadratic ease-out
        
        # Update player position
        new_x = self.dash_start_pos[0] + (self.dash_target_pos[0] - self.dash_start_pos[0]) * t
        new_y = self.dash_start_pos[1] + (self.dash_target_pos[1] - self.dash_start_pos[1]) * t
        
        # Create trail particles
        if len(self.dash_trail_particles) < self.max_trail_particles:
            particle = self.create_trail_particle()
            particle.setPos(self.player_pos[0], 0, self.player_pos[1])
            self.dash_trail_particles.append({
                'node': particle,
                'spawn_time': current_time,
                'position': (self.player_pos[0], self.player_pos[1])
            })
        
        # Update existing trail particles
        for particle in self.dash_trail_particles[:]:
            age = current_time - particle['spawn_time']
            if age > self.trail_lifetime:
                particle['node'].removeNode()
                self.dash_trail_particles.remove(particle)
            else:
                # Fade out particle
                fade = 1.0 - (age / self.trail_lifetime)
                particle['node'].setColorScale(1, 1, 1, fade)
        
        # Update arc and glow
        self.dash_arc.setPos(new_x, 0, new_y)
        self.dash_glow.setPos(new_x, 0, new_y)
        
        # Fade arc and glow based on progress
        fade = 1.0 - progress
        self.dash_arc.setColorScale(1, 1, 1, fade)
        self.dash_glow.setColorScale(1, 1, 1, fade * 0.7)
        
        # Update player position
        self.player_pos[0] = new_x
        self.player_pos[1] = new_y
        self.player.setPos(new_x, 0, new_y)

        # Check for enemy collisions - this is the important addition
        self.check_dash_collision()

    def check_dash_collision(self):
        if not self.is_dashing:
            return
                
        dash_vector_x = self.dash_target_pos[0] - self.dash_start_pos[0]
        dash_vector_y = self.dash_target_pos[1] - self.dash_start_pos[1]
        
        # Define AoE radius (5% of screen width)
        aoe_radius = self.aspect_ratio * 0.20
        
        # Check each enemy for intersection with dash path or destination AoE
        for enemy in self.enemies[:]:
            enemy_pos = enemy.getPos()
            
            # First check dash destination AoE
            dist_to_destination = math.sqrt(
                (enemy_pos[0] - self.dash_target_pos[0])**2 + 
                (enemy_pos[2] - self.dash_target_pos[1])**2
            )
            
            # If enemy is within AoE radius of destination or along dash path, destroy it
            if dist_to_destination <= aoe_radius:
                # Create a bigger explosion for AoE kills
                self.create_explosion(enemy_pos[0], enemy_pos[2], is_aoe=True)
                self.score += 1
                self.score_text.setText(f"Score: {self.score}")
                self.check_difficulty_increase()
                self.enemy_data.pop(enemy)
                enemy.removeNode()
                self.enemies.remove(enemy)
                self.enemy_death_sound.play()
                if len(self.enemies) < self.enemy_limit:
                    self.spawn_single_enemy()
                continue
            
            # Then check dash path collision as before
            px = enemy_pos[0] - self.dash_start_pos[0]
            py = enemy_pos[2] - self.dash_start_pos[1]
            
            dash_length_squared = dash_vector_x * dash_vector_x + dash_vector_y * dash_vector_y
            if dash_length_squared == 0:
                continue
                
            t = max(0, min(1, (px * dash_vector_x + py * dash_vector_y) / dash_length_squared))
            
            closest_x = self.dash_start_pos[0] + t * dash_vector_x
            closest_y = self.dash_start_pos[1] + t * dash_vector_y
            
            dist = math.sqrt((enemy_pos[0] - closest_x)**2 + (enemy_pos[2] - closest_y)**2)
            if dist < 0.1:  # Regular dash collision threshold
                self.create_explosion(enemy_pos[0], enemy_pos[2])
                self.score += 1
                self.score_text.setText(f"Score: {self.score}")
                self.check_difficulty_increase()
                self.enemy_data.pop(enemy)
                enemy.removeNode()
                self.enemies.remove(enemy)
                self.enemy_death_sound.play()
                if len(self.enemies) < self.enemy_limit:
                    self.spawn_single_enemy()

    def debug_button(self):
        out("Shoulder button pressed!", 2)
        if self.gamepad:
            right_x = self.gamepad.findAxis(InputDevice.Axis.left_x).value
            right_y = self.gamepad.findAxis(InputDevice.Axis.left_y).value
            out(f"Left stick position: {right_x}, {right_y}", 2)
            self.perform_dash(right_x, right_y)

    def create_dash_visuals(self):
        # Increase arc size
        arc_size = 0.15  # Increased from 0.1
        cm = CardMaker("dash_arc")
        cm.setFrame(-arc_size, arc_size, -arc_size, arc_size)
        self.dash_arc = self.render2d.attachNewNode(cm.generate())
        
        # Create arc texture with stronger glow
        texture_size = 128
        arc_image = PNMImage(texture_size, texture_size, 4)
        center_x = texture_size // 2
        center_y = texture_size // 2
        radius = texture_size // 2
        
        # Draw 1/4 circle arc with stronger glow
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                angle = math.atan2(dy, dx)
                
                if distance <= radius and 0 <= angle <= math.pi/2:
                    intensity = 1.0 - (distance / radius)
                    intensity = intensity ** 0.3  # Less falloff for stronger glow
                    
                    # Brighter core with blue tint
                    arc_image.setXel(x, y, 0.9, 0.95, 1.0)
                    arc_image.setAlpha(x, y, intensity)
                else:
                    arc_image.setAlpha(x, y, 0)

        arc_texture = Texture()
        arc_texture.load(arc_image)
        self.dash_arc.setTexture(arc_texture)
        self.dash_arc.setTransparency(TransparencyAttrib.MAlpha)
        self.dash_arc.setBin('fixed', 100)
        self.dash_arc.hide()

        # Create larger dash glow effect
        glow_size = 0.2  # Increased from 0.15
        cm = CardMaker("dash_glow")
        cm.setFrame(-glow_size, glow_size, -glow_size, glow_size)
        self.dash_glow = self.render2d.attachNewNode(cm.generate())
        
        # Create brighter glow texture
        glow_image = PNMImage(texture_size, texture_size, 4)
        
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    intensity = intensity ** 1.5  # Adjusted for better falloff
                    
                    # Brighter blue tint
                    glow_image.setXel(x, y, 0.8, 0.9, 1.0)
                    glow_image.setAlpha(x, y, intensity * 0.9)  # More opacity
                else:
                    glow_image.setAlpha(x, y, 0)
        
        glow_texture = Texture()
        glow_texture.load(glow_image)
        self.dash_glow.setTexture(glow_texture)
        self.dash_glow.setTransparency(TransparencyAttrib.MAlpha)
        self.dash_glow.setBin('fixed', 99)
        self.dash_glow.hide()

    def create_trail_particle(self):
        particle_size = 0.04  # Increased from 0.03
        cm = CardMaker("trail_particle")
        cm.setFrame(-particle_size, particle_size, -particle_size, particle_size)
        particle = self.render2d.attachNewNode(cm.generate())
        
        texture_size = 64
        particle_image = PNMImage(texture_size, texture_size, 4)
        center_x = texture_size // 2
        center_y = texture_size // 2
        radius = texture_size // 2
        
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    intensity = intensity ** 0.5  # Less falloff for stronger particles
                    
                    # Brighter blue color
                    particle_image.setXel(x, y, 0.7, 0.85, 1.0)
                    particle_image.setAlpha(x, y, intensity * 0.8)  # More opacity
                else:
                    particle_image.setAlpha(x, y, 0)
        
        particle_texture = Texture()
        particle_texture.load(particle_image)
        particle.setTexture(particle_texture)
        particle.setTransparency(TransparencyAttrib.MAlpha)
        particle.setBin('fixed', 98)
        
        return particle
