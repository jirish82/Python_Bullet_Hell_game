import math
import time
from direct.task import Task
from panda3d.core import InputDevice
from entities.player.player import Player

class PlayerSystem:
    def __init__(self, game):
        self.game = game
        self.player = Player(game)
        
        # Movement input state
        self.keys = {}
        for key in ['arrow_left', 'arrow_right', 'arrow_up', 'arrow_down']:
            self.keys[key] = False
            
        # Set up key handlers
        game.accept("arrow_left", self.update_key_map, ["arrow_left", True])
        game.accept("arrow_left-up", self.update_key_map, ["arrow_left", False])
        game.accept("arrow_right", self.update_key_map, ["arrow_right", True])
        game.accept("arrow_right-up", self.update_key_map, ["arrow_right", False])
        game.accept("arrow_up", self.update_key_map, ["arrow_up", True])
        game.accept("arrow_up-up", self.update_key_map, ["arrow_up", False])
        game.accept("arrow_down", self.update_key_map, ["arrow_down", True])
        game.accept("arrow_down-up", self.update_key_map, ["arrow_down", False])

        # Shooting properties
        self.last_fire_time = 0
        self.fire_rate = 0.1  # Time in seconds between shots

    def update_key_map(self, key, value):
        """Update keyboard input state"""
        self.keys[key] = value

    def update(self, task):
        """Update player state"""
        if self.game.paused or self.game.game_over:
            return Task.cont

        # Handle keyboard input
        dx = 0
        dy = 0
        
        if self.keys["arrow_left"]:
            dx -= self.player.movement_speed
        if self.keys["arrow_right"]:
            dx += self.player.movement_speed
        if self.keys["arrow_up"]:
            dy += self.player.movement_speed
        if self.keys["arrow_down"]:
            dy -= self.player.movement_speed
            
        # Handle gamepad input if available
        if self.game.gamepad:
            # Left analog stick (movement)
            left_x = self.game.gamepad.findAxis(InputDevice.Axis.left_x).value
            left_y = self.game.gamepad.findAxis(InputDevice.Axis.left_y).value
            
            # Add deadzone
            deadzone = 0.2
            if abs(left_x) < deadzone: left_x = 0
            if abs(left_y) < deadzone: left_y = 0
            
            # Add gamepad movement
            dx += left_x * self.player.movement_speed
            dy += left_y * self.player.movement_speed
            
            # D-pad support
            if self.game.gamepad.findButton("dpad_left").pressed:
                dx -= self.player.movement_speed
            if self.game.gamepad.findButton("dpad_right").pressed:
                dx += self.player.movement_speed
            if self.game.gamepad.findButton("dpad_up").pressed:
                dy += self.player.movement_speed
            if self.game.gamepad.findButton("dpad_down").pressed:
                dy -= self.player.movement_speed

            # Handle shooting with right analog stick
            right_x = self.game.gamepad.findAxis(InputDevice.Axis.right_x).value
            right_y = self.game.gamepad.findAxis(InputDevice.Axis.right_y).value
            stick_magnitude = math.sqrt(right_x * right_x + right_y * right_y)
            current_time = time.time()
            
            if (stick_magnitude > deadzone and 
                current_time - self.last_fire_time >= self.fire_rate):
                direction_x = right_x / stick_magnitude
                direction_y = right_y / stick_magnitude
                self.game.projectile_system.create_projectile(
                    self.player.get_position(),
                    (direction_x, direction_y)
                )
                if hasattr(self.game, 'gun_sound') and self.game.gun_sound:
                    self.game.gun_sound.play()
                self.last_fire_time = current_time

        # Update position
        self.player.update_position(dx, dy)

        # Update invincibility
        self.update_invincibility()
        
        return Task.cont

    def update_invincibility(self):
        """Update player invincibility state"""
        if self.player.is_invincible:
            current_time = time.time()
            time_in_invincibility = current_time - self.player.invincibility_start_time
            
            if time_in_invincibility >= self.player.invincibility_duration:
                self.player.is_invincible = False
                self.player.sprite.setColorScale(1, 1, 1, 1)  # Reset color
            else:
                # Create flashing effect
                flash = (math.sin(time_in_invincibility * self.player.invincibility_flash_speed) * 0.3) + 0.7
                self.player.sprite.setColorScale(1, 1, flash, 1)  # Blue-tinted flash

    def perform_dash(self, direction_x, direction_y):
        """Perform dash movement"""
        if not self.can_dash():
            return False

        # Play dash sound if available
        if hasattr(self.game, 'dash_sound') and self.game.dash_sound:
            self.game.dash_sound.play()

        # Normalize direction
        magnitude = math.sqrt(direction_x * direction_x + direction_y * direction_y)
        if magnitude < 0.2:  # Don't dash if stick barely moved
            return False
                
        direction_x /= magnitude
        direction_y /= magnitude
        
        # Store start position
        self.player.dash_start_pos = [self.player.pos[0], self.player.pos[1]]
        
        # Calculate dash end position
        target_x = self.player.pos[0] + direction_x * self.player.dash_distance
        target_y = self.player.pos[1] + direction_y * self.player.dash_distance
        
        # Clamp to screen bounds
        target_x = max(-self.game.aspect_ratio + 0.05, min(self.game.aspect_ratio - 0.05, target_x))
        target_y = max(-0.95, min(0.95, target_y))
        
        self.player.dash_target_pos = [target_x, target_y]
        
        # Start dash
        self.player.is_dashing = True
        self.player.dash_start_time = time.time()
        self.player.last_dash_time = time.time()

        return True

    def can_dash(self):
        """Check if player can perform a dash"""
        current_time = time.time()
        return (not self.player.is_dashing and 
                current_time - self.player.last_dash_time >= self.player.dash_cooldown)

    def start_invincibility(self):
        """Start player invincibility period"""
        self.player.is_invincible = True
        self.player.invincibility_start_time = time.time()

    def cleanup(self):
        """Clean up system resources"""
        self.player.cleanup()