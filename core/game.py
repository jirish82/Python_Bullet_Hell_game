from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import WindowProperties, InputDevice, CardMaker, TransparencyAttrib
import time

from utils.resource_loader import get_resource_path
from utils.debug import out
from core.town import TownArea

from systems.player_system import PlayerSystem
from systems.enemy_system import EnemySystem
from systems.boss_system import BossSystem
from systems.projectile_system import ProjectileSystem
from systems.orb_system import OrbSystem
from effects.effects_system import EffectsSystem
from ui.ui_system import UISystem

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Game state
        self.paused = True
        self.game_over = False
        self.level = 1
        self.score = 0
        self.actual_game_time = 0
        self.last_time_update = time.time()
        self.game_start_time = time.time()
        
        # Initialize window properties
        self.setup_window()
        
        # Load and set up background
        self.setup_background()
        
        # Initialize systems
        self.ui_system = UISystem(self)
        self.effects_system = EffectsSystem(self)
        self.projectile_system = ProjectileSystem(self)
        self.player_system = PlayerSystem(self)
        self.enemy_system = EnemySystem(self)
        self.boss_system = BossSystem(self)
        self.orb_system = OrbSystem(self)
        
        # Initialize town area
        self.town_area = None
        
        # Load sounds
        self.load_sounds()
        
        # Set up input handling
        self.setup_input()
        
        # Show initial pause text since game starts paused
        self.ui_system.show_pause()
        
        # Add the game loop update task
        self.taskMgr.add(self.update, "gameUpdate")

    def setup_window(self):
        """Set up window properties and camera"""
        wp = WindowProperties()
        wp.setSize(1920, 1080)
        self.win.requestProperties(wp)
        
        # Calculate and store aspect ratio
        props = self.win.getProperties()
        self.aspect_ratio = props.getXSize() / props.getYSize()
        
        # Disable mouse control of the camera
        self.disableMouse()
        
        # Set up orthographic camera
        lens = self.cam.node().getLens()
        lens.setFov(0.5)

    def setup_background(self):
        """Load and set up the game background"""
        self.background = self.loader.loadTexture(get_resource_path("map.png"))
        cm = CardMaker("background")
        cm.setFrame(-self.aspect_ratio * 0.58, self.aspect_ratio * 0.8, -1, 1)
        self.background_node = self.render2d.attachNewNode(cm.generate())
        self.background_node.setTexture(self.background)

    def load_sounds(self):
        """Load and set up game sounds"""
        try:
            # Background music
            self.music = self.loader.loadSfx(get_resource_path("music.mp3"))
            if self.music:
                self.music.setLoop(True)
                self.music.setVolume(0)
                self.music.play()
                self.music_playing = True
                self.music_paused = False
                self.music.stop()
            
            # Effect sounds
            self.enemy_death_sound = self.loader.loadSfx(get_resource_path("enemy_death.mp3"))
            self.enemy_death_sound.setVolume(0.2)
            self.gun_sound = self.loader.loadSfx(get_resource_path("gun.mp3"))
            self.gun_sound.setVolume(0.03)
            self.dash_ready_sound = self.loader.loadSfx(get_resource_path("powerup1.mp3"))
            self.dash_ready_sound.setVolume(0.8)
            self.dash_sound = self.loader.loadSfx(get_resource_path("zoom.mp3"))
            self.dash_sound.setVolume(0.8)
        except Exception as e:
            out(f"Error loading sounds: {e}")
            self.music_playing = False
            self.music_paused = False

    def setup_input(self):
        """Set up input handling"""
        # Clear any existing bindings
        self.ignore_all()
        
        # Set up pause controls
        self.accept("start", self.toggle_pause)
        self.accept("gamepad-start", self.toggle_pause)
        self.accept("p", self.toggle_pause)
        
        # Add fullscreen toggle and music controls
        self.accept("f", self.toggle_fullscreen)
        self.accept("m", self.toggle_music)
        
        # Initialize gamepad
        self.gamepad = None
        self.init_gamepad()

    def init_gamepad(self):
        """Initialize gamepad if available"""
        devices = self.devices.getDevices(InputDevice.DeviceClass.gamepad)
        if devices:
            self.gamepad = devices[0]
            self.attachInputDevice(self.gamepad, prefix="gamepad")
            out(f"Gamepad connected: {self.gamepad.name}", 2)
            
            # Set up gamepad button handlers
            self.accept("gamepad-face_a", self.toggle_music)
            self.accept("gamepad-face_b", self.toggle_pause)
            self.accept("gamepad-face_y", self.toggle_fullscreen)
            
            # Handle dash with right shoulder button
            self.accept("gamepad-right_shoulder", self.handle_dash)

    def handle_dash(self):
        """Handle gamepad dash input"""
        if self.gamepad:
            left_x = self.gamepad.findAxis(InputDevice.Axis.left_x).value
            left_y = self.gamepad.findAxis(InputDevice.Axis.left_y).value
            self.player_system.perform_dash(left_x, left_y)

    def update(self, task):
        """Main game update loop"""
        # Update game time
        current_time = time.time()
        if not self.paused and not self.game_over:
            self.actual_game_time += current_time - self.last_time_update
        self.last_time_update = current_time
        
        # Check for boss spawn
        if (self.actual_game_time >= self.boss_system.boss_spawn_time and 
            not self.boss_system.boss and not self.game_over):
            self.boss_system.spawn_boss()
        
        # Update all systems
        self.player_system.update(task)
        self.enemy_system.update(task)
        self.boss_system.update(task)
        self.projectile_system.update(task)
        self.orb_system.update(task)
        self.effects_system.update_explosions(task)
        self.ui_system.update_debug_text()
        
        return Task.cont

    def toggle_pause(self):
        """Toggle game pause state"""
        if self.game_over:
            self.restart_game()
        else:
            self.paused = not self.paused
            if self.paused:
                self.ui_system.show_pause()
                if self.music:
                    self.music.stop()
            else:
                self.ui_system.hide_pause()
                if self.music:
                    self.music.play()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        wp = self.win.getProperties()
        wp2 = WindowProperties()
        wp2.setFullscreen(not wp.getFullscreen())
        self.win.requestProperties(wp2)

    def toggle_music(self):
        """Toggle music on/off"""
        if self.music:
            if self.music_playing:
                self.music.setVolume(0)
                self.music_playing = False
            else:
                self.music.setVolume(0.3)
                self.music_playing = True

    def restart_game(self):
        """Restart the game"""
        self.actual_game_time = 0
        self.last_time_update = time.time()
        self.game_start_time = time.time()
        self.level = 1
        self.score = 0
        
        # Reset game state
        self.game_over = False
        self.ui_system.hide_game_over()
        self.ui_system.hide_pause()
        self.paused = False
        
        # Reset all systems
        self.player_system.cleanup()
        self.enemy_system.reset()
        self.boss_system.cleanup()
        self.projectile_system.cleanup()
        self.orb_system.cleanup()
        self.effects_system.cleanup()
        
        # Reinitialize systems as needed
        self.player_system = PlayerSystem(self)
        
        # Restart music
        if self.music:
            self.music.play()

    def transition_to_town(self):
        """Handle transition to town area"""
        # Clear combat entities
        self.enemy_system.cleanup()
        self.boss_system.cleanup()
        self.projectile_system.cleanup()
        self.orb_system.cleanup()
        
        # Hide combat background
        self.background_node.hide()
        
        # Initialize and show town area
        if not self.town_area:
            self.town_area = TownArea(self)
        self.town_area.enter()
        
        # Reset camera
        self.camera.setPos(0, 0, 0)

    def cleanup(self):
        """Clean up game resources"""
        self.player_system.cleanup()
        self.enemy_system.cleanup()
        self.boss_system.cleanup()
        self.projectile_system.cleanup()
        self.orb_system.cleanup()
        self.effects_system.cleanup()
        self.ui_system.cleanup()
        
        if self.town_area:
            self.town_area.exit()
