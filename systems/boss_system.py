import random
import time
import math
from direct.task import Task
from panda3d.core import CardMaker, TransparencyAttrib, Texture, PNMImage
from entities.boss.boss import Boss
from utils.resource_loader import get_resource_path

class BossSystem:
    def __init__(self, game):
        self.game = game
        self.boss = None
        self.boss_projectiles = []
        
        # Boss spawn configuration
        self.boss_spawn_time_base = 15  # Base time before boss spawns
        self.boss_spawn_time = self.boss_spawn_time_base
        self.boss_hits_required = 10
        
        # Projectile configuration
        self.projectile_speed = 0.005  # 1/6 of player projectile speed
        self.fire_rate = 0.8  # Fire 4x per second
        self.last_fire_time = 0
        
        # Death sequence configuration
        self.boss_death_sequence = False
        self.boss_death_duration = 180      # Time for explosions
        self.white_fade_duration = 120      # Time to fade to white
        self.white_screen_duration = 210    # Time to hold white
        self.fade_duration = 60             # Time to fade to town
        self.screen_shake_intensity = 0.05
        self.boss_death_shake_intensity = 0.02
        self.boss_death_scale_start = 1.0
        self.boss_death_scale_end = 1.3
        
        self.white_overlay = None
        self.boss_final_pos = None
        self.update_sequence_count = 0
        self.last_boss_break = 0
        self.final_explosion = None

    def spawn_boss(self):
        """Spawn a boss at a random edge position"""
        if self.boss:
            return

        # Choose random side to spawn from
        side = random.choice(['top', 'bottom', 'left', 'right'])
        boss_size = 0.3
        buffer = 0.1

        # Calculate spawn position
        if side == 'top':
            x = random.uniform(-self.game.aspect_ratio + boss_size, self.game.aspect_ratio - boss_size)
            y = 1 + buffer
        elif side == 'bottom':
            x = random.uniform(-self.game.aspect_ratio + boss_size, self.game.aspect_ratio - boss_size)
            y = -1 - buffer
        elif side == 'left':
            x = -self.game.aspect_ratio - buffer
            y = random.uniform(-1 + boss_size, 1 - boss_size)
        else:  # right
            x = self.game.aspect_ratio + buffer
            y = random.uniform(-1 + boss_size, 1 - boss_size)

        self.boss = Boss(self.game, (x, y))
        self.boss.health = self.boss_hits_required

    def update(self, task):
        """Update boss behavior"""
        if not self.boss and not self.boss_death_sequence:
            return Task.cont

        if self.boss_death_sequence:
            return self.update_boss_death_sequence(task)

        if self.game.paused or self.game.game_over:
            return Task.cont

        # Update boss movement
        current_time = time.time()
        player_pos = self.game.player_system.player.get_position()
        
        # Calculate current speed based on game time
        seconds_elapsed = current_time - self.game.enemy_system.game_start_time
        current_max = (self.game.enemy_system.base_speed_max + 
                      (self.game.enemy_system.speed_max_increase_rate * seconds_elapsed))
        
        self.boss.move_towards(player_pos, current_max)
        
        # Fire projectiles
        if current_time - self.last_fire_time >= self.fire_rate:
            self.fire_projectile()
            self.last_fire_time = current_time

        # Update projectiles
        self.update_projectiles()
        
        # Check collision with player
        if self.check_collision_with_player():
            if not self.game.player_system.player.is_invincible:
                self.game.game_over = True
                self.game.ui_system.show_game_over()
                self.game.paused = True
                if hasattr(self.game, 'music') and self.game.music:
                    self.game.music.stop()

        return Task.cont

    def fire_projectile(self):
        """Create and fire a boss projectile"""
        if not self.boss:
            return

        boss_pos = self.boss.get_position()
        player_pos = self.game.player_system.player.get_position()
        
        # Calculate direction to player
        dx = player_pos[0] - boss_pos[0]
        dy = player_pos[1] - boss_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            dx /= distance
            dy /= distance

        # Create projectile
        cm = CardMaker("boss_projectile")
        projectile_size = 0.06  # 3x normal projectile size
        cm.setFrame(-projectile_size, projectile_size, -projectile_size, projectile_size)
        projectile = self.game.render2d.attachNewNode(cm.generate())
        
        projectile_tex = self.game.loader.loadTexture(get_resource_path("orb.png"))
        projectile.setTexture(projectile_tex)
        projectile.setTransparency(TransparencyAttrib.MAlpha)
        
        projectile.setPos(boss_pos[0], 0, boss_pos[1])
        projectile.setPythonTag("direction", (dx, dy))
        self.boss_projectiles.append(projectile)

    def update_projectiles(self):
        """Update boss projectile positions and check collisions"""
        for projectile in self.boss_projectiles[:]:
            current_pos = projectile.getPos()
            direction = projectile.getPythonTag("direction")
            new_x = current_pos[0] + direction[0] * self.projectile_speed
            new_z = current_pos[2] + direction[1] * self.projectile_speed
            projectile.setPos(new_x, 0, new_z)
            
            # Remove if off screen
            if (new_x > self.game.aspect_ratio + 0.1 or 
                new_x < -self.game.aspect_ratio - 0.1 or 
                new_z > 1.1 or new_z < -1.1):
                projectile.removeNode()
                self.boss_projectiles.remove(projectile)
                continue
            
            # Check collision with player
            if (not self.game.player_system.player.is_invincible and
                abs(self.game.player_system.player.pos[0] - new_x) < 0.1 and 
                abs(self.game.player_system.player.pos[1] - new_z) < 0.1):
                self.game.game_over = True
                self.game.ui_system.show_game_over()
                self.game.paused = True
                if hasattr(self.game, 'music') and self.game.music:
                    self.game.music.stop()

    def check_collision_with_player(self):
        """Check if boss collides with player"""
        if not self.boss:
            return False
            
        boss_pos = self.boss.get_position()
        player_pos = self.game.player_system.player.get_position()
        return (abs(player_pos[0] - boss_pos[0]) < 0.3 and 
                abs(player_pos[1] - boss_pos[1]) < 0.3)

    def start_death_sequence(self):
        """Start boss death sequence"""
        if not self.boss:
            return
            
        self.boss_death_sequence = True
        self.update_sequence_count = 0
        self.last_boss_break = 0
        self.boss_final_pos = self.boss.get_position()
        
        # Create white overlay
        cm = CardMaker("white_overlay")
        cm.setFrame(-2, 2, -2, 2)
        self.white_overlay = self.game.render2d.attachNewNode(cm.generate())
        self.white_overlay.setColor(1, 1, 1, 0)
        self.white_overlay.setBin('fixed', 1000)
        self.white_overlay.setDepthTest(False)
        self.white_overlay.setDepthWrite(False)
        self.white_overlay.setTransparency(TransparencyAttrib.MAlpha)
        
        # Create final explosion
        self.create_final_explosion()

    def create_final_explosion(self):
        """Create the final large explosion effect"""
        if not self.boss:
            return
            
        final_pos = self.boss.get_position()
        final_scale = self.boss.sprite.getScale()[0]
        explosion_size = 0.3 * final_scale * 3
        
        cm = CardMaker("final_explosion")
        cm.setFrame(-explosion_size, explosion_size, -explosion_size, explosion_size)
        self.final_explosion = self.game.render2d.attachNewNode(cm.generate())
        
        texture_size = 256
        image = self.create_explosion_texture(texture_size)
        self.final_explosion.setTexture(image)
        self.final_explosion.setTransparency(TransparencyAttrib.MAlpha)
        self.final_explosion.setBin('fixed', 100)
        self.final_explosion.setPos(final_pos[0], 0, final_pos[1])
        
        # Start with small scale
        self.final_explosion.setScale(0.1)

    def create_explosion_texture(self, size):
        """Create the explosion texture"""
        image = PNMImage(size, size, 4)
        center_x = size // 2
        center_y = size // 2
        radius = size // 2
        
        for x in range(size):
            for y in range(size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    intensity = intensity ** 0.5
                    
                    if distance < radius * 0.3:
                        # Bright white-red core
                        image.setXel(x, y, 1.0, 0.9, 0.9)
                    elif distance < radius * 0.6:
                        # Bright red-white middle with blue tint
                        image.setXel(x, y, 1.0, 0.7, 0.9)
                    else:
                        # Red-blue outer
                        image.setXel(x, y, 0.8, 0.4, 1.0)
                    
                    image.setAlpha(x, y, intensity)
                else:
                    image.setAlpha(x, y, 0)
        
        texture = Texture()
        texture.load(image)
        return texture

    def update_boss_death_sequence(self, task):
        """Update boss death sequence animation"""
        if not self.boss_death_sequence:
            return Task.cont

        if not self.white_overlay:
            self.start_death_sequence()
            return Task.cont

        self.update_sequence_count += 1
        total_frames = (self.boss_death_duration + self.white_fade_duration + 
                       self.white_screen_duration + self.fade_duration)

        # Handle boss death animation during explosion phase
        if self.update_sequence_count <= self.boss_death_duration:
            progress = self.update_sequence_count / self.boss_death_duration
            
            if self.boss:
                # Shake effect
                shake_intensity = self.boss_death_shake_intensity * (1 - progress)
                shake_x = random.uniform(-shake_intensity, shake_intensity)
                self.boss.sprite.setPos(
                    self.boss_final_pos[0] + shake_x,
                    0,
                    self.boss_final_pos[1]
                )
                
                # Scale effect
                scale_factor = self.boss_death_scale_start + (
                    (self.boss_death_scale_end - self.boss_death_scale_start) * progress
                )
                self.boss.set_scale(scale_factor)
            
            # Update final explosion scale
            if self.final_explosion:
                explosion_scale = 0.1 + (3.0 * progress)  # Scale from 0.1 to 3.1
                self.final_explosion.setScale(explosion_scale)
                self.final_explosion.setColorScale(1, 1, 1, max(0, 1 - progress))

            # Remove boss and explosion at the end of the explosion phase
            if self.update_sequence_count >= self.boss_death_duration - 20:
                if self.boss:
                    self.boss.cleanup()
                    self.boss = None
                if self.final_explosion:
                    self.final_explosion.removeNode()
                    self.final_explosion = None

        # Handle white overlay phases
        if self.update_sequence_count <= self.boss_death_duration:
            if self.white_overlay:
                self.white_overlay.setColor(1, 1, 1, 0)
        elif self.update_sequence_count <= self.boss_death_duration + self.white_fade_duration:
            fade_frames = self.update_sequence_count - self.boss_death_duration
            opacity = fade_frames / self.white_fade_duration
            if self.white_overlay:
                self.white_overlay.setColor(1, 1, 1, min(1.0, opacity))
                
            # Ensure explosion is cleaned up during fade to white
            if self.final_explosion:
                self.final_explosion.removeNode()
                self.final_explosion = None
                
        elif self.update_sequence_count <= self.boss_death_duration + self.white_fade_duration + self.white_screen_duration:
            if self.white_overlay:
                self.white_overlay.setColor(1, 1, 1, 1)
            
            # Start loading town when we first enter the white screen phase
            if self.update_sequence_count == self.boss_death_duration + self.white_fade_duration + 1:
                # Ensure all effects are cleaned up before transition
                if self.final_explosion:
                    self.final_explosion.removeNode()
                    self.final_explosion = None
                self.game.transition_to_town()
        else:
            fade_out_frames = self.update_sequence_count - (
                self.boss_death_duration + self.white_fade_duration + self.white_screen_duration
            )
            opacity = 1.0 - (fade_out_frames / self.fade_duration)
            if self.white_overlay:
                self.white_overlay.setColor(1, 1, 1, max(0.0, opacity))

        # End sequence when complete
        if self.update_sequence_count > total_frames:
            self.boss_death_sequence = False
            if self.white_overlay:
                self.white_overlay.removeNode()
                self.white_overlay = None
            if self.final_explosion:
                self.final_explosion.removeNode()
                self.final_explosion = None
            return Task.done

        return Task.cont

    def cleanup(self):
        """Clean up system resources"""
        if self.boss:
            self.boss.cleanup()
            self.boss = None
            
        for projectile in self.boss_projectiles:
            projectile.removeNode()
        self.boss_projectiles.clear()
        
        if self.white_overlay:
            self.white_overlay.removeNode()
            self.white_overlay = None
            
        if self.final_explosion:
            self.final_explosion.removeNode()
            self.final_explosion = None