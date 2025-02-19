import random
import time
from direct.task import Task
from entities.enemy.enemy import Enemy

class EnemySystem:
    def __init__(self, game):
        self.game = game
        self.enemies = []
        
        # Enemy spawn configuration
        self.base_speed_min = 0.001
        self.base_speed_max = 0.003
        self.base_num_enemies = 5
        self.speed_min_increase_rate = 0.0001  # per second
        self.speed_max_increase_rate = 0.0002  # per second
        
        # Current state
        self.enemy_limit = self.base_num_enemies
        self.enemies_per_score = 8  # Increase enemies every 8 points
        self.previous_enemy_increase = 0
        self.game_start_time = time.time()
        
        # Initialize with base enemies
        self.spawn_initial_enemies()

    def spawn_initial_enemies(self):
        """Spawn initial set of enemies"""
        while len(self.enemies) < self.enemy_limit:
            self.spawn_single_enemy()

    def spawn_single_enemy(self):
        """Spawn a single enemy at a random edge position"""
        side = random.choice(['top', 'bottom', 'left', 'right'])
        enemy_size = 0.1
        buffer = 0.1  # Small buffer distance outside the screen

        # Calculate spawn position based on side
        if side == 'top':
            x = random.uniform(-self.game.aspect_ratio + enemy_size, self.game.aspect_ratio - enemy_size)
            y = 1 + buffer
        elif side == 'bottom':
            x = random.uniform(-self.game.aspect_ratio + enemy_size, self.game.aspect_ratio - enemy_size)
            y = -1 - buffer
        elif side == 'left':
            x = -self.game.aspect_ratio - buffer
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)
        else:  # right
            x = self.game.aspect_ratio + buffer
            y = random.uniform(-1 + enemy_size, 1 - enemy_size)

        # Calculate time-based speed limits
        seconds_elapsed = time.time() - self.game_start_time
        current_min = self.base_speed_min + (self.speed_min_increase_rate * seconds_elapsed)
        current_max = self.base_speed_max + (self.speed_max_increase_rate * seconds_elapsed)
        
        # Create enemy with random speed
        speed = random.uniform(current_min, current_max)
        enemy = Enemy(self.game, (x, y), speed)
        self.enemies.append(enemy)

    def update(self, task):
        """Update all enemies"""
        if self.game.paused or self.game.game_over:
            return Task.cont

        # Ensure we maintain the enemy limit
        while len(self.enemies) < self.enemy_limit:
            self.spawn_single_enemy()

        player_pos = self.game.player_system.player.get_position()
        
        # Update each enemy
        for enemy in self.enemies[:]:
            enemy.move_towards(player_pos)
            
            # Check collision with player
            enemy_pos = enemy.get_position()
            if self.check_collision_with_player(enemy_pos):
                if self.game.player_system.player.is_invincible:
                    # Destroy enemy if player is invincible
                    self.destroy_enemy(enemy)
                    self.game.score += 1
                    self.game.ui_system.update_score(self.game.score)
                    self.check_difficulty_increase()
                else:
                    # Game over if player is not invincible
                    self.game.game_over = True
                    self.game.ui_system.show_game_over()
                    self.game.paused = True
                    if hasattr(self.game, 'music') and self.game.music:
                        self.game.music.stop()

        return Task.cont

    def check_collision_with_player(self, enemy_pos):
        """Check if enemy collides with player"""
        player_pos = self.game.player_system.player.get_position()
        return (abs(player_pos[0] - enemy_pos[0]) < 0.07 and 
                abs(player_pos[1] - enemy_pos[1]) < 0.07)

    def destroy_enemy(self, enemy):
        """Remove an enemy from the game"""
        if enemy in self.enemies:
            self.enemies.remove(enemy)
            enemy.cleanup()
            if hasattr(self.game, 'enemy_death_sound') and self.game.enemy_death_sound:
                self.game.enemy_death_sound.play()

    def check_difficulty_increase(self):
        """Check and apply difficulty increase based on score"""
        difficulty_level = self.game.score // self.enemies_per_score
        if difficulty_level > self.previous_enemy_increase:
            self.enemy_limit += 1
            self.previous_enemy_increase = difficulty_level

    def reset(self):
        """Reset enemy system to initial state"""
        # Clean up existing enemies
        for enemy in self.enemies:
            enemy.cleanup()
        self.enemies.clear()
        
        # Reset configuration
        self.enemy_limit = self.base_num_enemies
        self.previous_enemy_increase = 0
        self.game_start_time = time.time()
        
        # Spawn new enemies
        self.spawn_initial_enemies()

    def cleanup(self):
        """Clean up system resources"""
        for enemy in self.enemies:
            enemy.cleanup()
        self.enemies.clear()