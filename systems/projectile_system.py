from panda3d.core import CardMaker, TransparencyAttrib
from direct.task import Task
from utils.resource_loader import get_resource_path

class ProjectileSystem:
    def __init__(self, game):
        self.game = game
        self.projectiles = []  # Player projectiles
        self.projectile_speed = 0.03
        self.fire_rate = 0.1  # Time in seconds between shots
        self.last_fire_time = 0

    def create_projectile(self, position, direction):
        """Create a new projectile at given position moving in given direction"""
        cm = CardMaker("projectile")
        projectile_size = 0.02
        cm.setFrame(-projectile_size, projectile_size, -projectile_size, projectile_size)
        projectile = self.game.render2d.attachNewNode(cm.generate())
        
        projectile_tex = self.game.loader.loadTexture(get_resource_path("orb.png"))
        projectile.setTexture(projectile_tex)
        projectile.setTransparency(TransparencyAttrib.MAlpha)
        
        projectile.setPos(position[0], 0, position[1])
        projectile.setPythonTag("direction", direction)
        self.projectiles.append(projectile)

        # Play gun sound if available
        if hasattr(self.game, 'gun_sound') and self.game.gun_sound:
            self.game.gun_sound.play()

    def update(self, task):
        """Update projectile positions and check collisions"""
        if self.game.paused or self.game.game_over:
            return Task.cont

        # Update projectiles
        for projectile in self.projectiles[:]:
            current_pos = projectile.getPos()
            direction = projectile.getPythonTag("direction")
            new_x = current_pos[0] + direction[0] * self.projectile_speed
            new_z = current_pos[2] + direction[1] * self.projectile_speed
            projectile.setPos(new_x, 0, new_z)
            
            # Remove if off screen
            if (new_x > self.game.aspect_ratio + 0.1 or 
                new_x < -self.game.aspect_ratio - 0.1 or 
                new_z > 1.1 or 
                new_z < -1.1):
                projectile.removeNode()
                self.projectiles.remove(projectile)
                continue

            # Check collisions with enemies
            self.check_enemy_collisions(projectile, (new_x, new_z))
            
            # Check collisions with boss
            if self.game.boss_system.boss:
                self.check_boss_collision(projectile, (new_x, new_z))

        return Task.cont

    def check_enemy_collisions(self, projectile, proj_pos):
        """Check projectile collision with enemies"""
        for enemy in self.game.enemy_system.enemies[:]:
            enemy_pos = enemy.get_position()
            if (abs(proj_pos[0] - enemy_pos[0]) < 0.07 and 
                abs(proj_pos[1] - enemy_pos[1]) < 0.07):
                # Create explosion effect
                self.game.effects_system.create_explosion(enemy_pos[0], enemy_pos[1])
                
                # Update score
                self.game.score += 1
                self.game.ui_system.update_score(self.game.score)
                
                # Handle enemy destruction
                self.game.enemy_system.destroy_enemy(enemy)
                projectile.removeNode()
                self.projectiles.remove(projectile)
                
                # Check for difficulty increase
                self.game.enemy_system.check_difficulty_increase()
                break

    def check_boss_collision(self, projectile, proj_pos):
        """Check projectile collision with boss"""
        if not self.game.boss_system.boss:
            return
            
        boss_pos = self.game.boss_system.boss.get_position()
        if (abs(proj_pos[0] - boss_pos[0]) < 0.3 and 
            abs(proj_pos[1] - boss_pos[1]) < 0.3):
            # Create explosion effect
            self.game.effects_system.create_explosion(boss_pos[0], boss_pos[1])
            
            # Handle boss damage
            if self.game.boss_system.boss.take_damage():
                # Boss defeated
                self.game.score += 10
                self.game.ui_system.update_score(self.game.score)
                self.game.boss_system.start_death_sequence()
                
                # Play death sound
                if hasattr(self.game, 'enemy_death_sound') and self.game.enemy_death_sound:
                    self.game.enemy_death_sound.play()
            else:
                # Boss still alive
                if hasattr(self.game, 'enemy_death_sound') and self.game.enemy_death_sound:
                    self.game.enemy_death_sound.play()
            
            # Remove projectile
            projectile.removeNode()
            self.projectiles.remove(projectile)

    def cleanup(self):
        """Clean up system resources"""
        for projectile in self.projectiles:
            projectile.removeNode()
        self.projectiles.clear()