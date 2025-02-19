import time
import math
from direct.task import Task
from entities.orbs.orb import GreenOrb, BlueOrb

class OrbSystem:
    def __init__(self, game):
        self.game = game
        
        # Green orb configuration
        self.green_orb = None
        self.orb_points_interval = 10  # Spawn green orb every 10 points
        self.last_orb_spawn_score = 0
        
        # Blue orb configuration
        self.blue_orb = None
        self.blue_orb_interval = 11.0  # Spawn blue orb every 11 seconds
        self.last_blue_orb_spawn_time = time.time()

    def update(self, task):
        """Update orb states and check for collection"""
        if self.game.paused or self.game.game_over:
            return Task.cont

        self.update_green_orb()
        self.check_green_orb_collection()
        
        self.update_blue_orb()
        self.check_blue_orb_collection()
        
        return Task.cont

    def update_green_orb(self):
        """Update green orb state and spawning"""
        current_time = time.time()
        
        # Check if we should spawn a new orb
        if (self.game.score > 0 and 
            self.game.score % self.orb_points_interval == 0 and 
            self.game.score != self.last_orb_spawn_score):
            self.spawn_green_orb()
            self.last_orb_spawn_score = self.game.score
        
        # Remove orb if it's been there too long
        if self.green_orb and self.green_orb.spawn_time:
            if current_time - self.green_orb.spawn_time > self.green_orb.duration:
                self.green_orb.cleanup()
                self.green_orb = None

    def update_blue_orb(self):
        """Update blue orb state and spawning"""
        current_time = time.time()
        
        # Check if we should spawn a new blue orb
        if current_time - self.last_blue_orb_spawn_time >= self.blue_orb_interval:
            self.spawn_blue_orb()
            self.last_blue_orb_spawn_time = current_time
        
        # Remove orb if it's been there too long
        if self.blue_orb and self.blue_orb.spawn_time:
            if current_time - self.blue_orb.spawn_time > self.blue_orb.duration:
                self.blue_orb.cleanup()
                self.blue_orb = None

    def spawn_green_orb(self):
        """Spawn a new green orb"""
        if self.green_orb:
            self.green_orb.cleanup()
        
        self.green_orb = GreenOrb(self.game)
        self.green_orb.spawn()
        
        # Start pulsing effect
        taskMgr = self.game.taskMgr
        taskMgr.remove("pulseGreenOrb")  # Remove any existing task
        taskMgr.add(self.pulse_green_orb, "pulseGreenOrb")

    def spawn_blue_orb(self):
        """Spawn a new blue orb"""
        if self.blue_orb:
            self.blue_orb.cleanup()
        
        self.blue_orb = BlueOrb(self.game)
        self.blue_orb.spawn()
        
        # Start pulsing effect
        taskMgr = self.game.taskMgr
        taskMgr.remove("pulseBlueOrb")  # Remove any existing task
        taskMgr.add(self.pulse_blue_orb, "pulseBlueOrb")

    def check_green_orb_collection(self):
        """Check if player has collected the green orb"""
        if not self.green_orb:
            return
            
        orb_pos = self.green_orb.get_position()
        player_pos = self.game.player_system.player.get_position()
        
        if (abs(player_pos[0] - orb_pos[0]) < 0.1 and 
            abs(player_pos[1] - orb_pos[1]) < 0.1):
            # Collected the orb - reduce enemy limit
            if self.game.enemy_system.enemy_limit > 1:  # Don't go below 1 enemy
                self.game.enemy_system.enemy_limit -= 1
            self.green_orb.cleanup()
            self.green_orb = None

    def check_blue_orb_collection(self):
        """Check if player has collected the blue orb"""
        if not self.blue_orb:
            return
            
        orb_pos = self.blue_orb.get_position()
        player_pos = self.game.player_system.player.get_position()
        
        if (abs(player_pos[0] - orb_pos[0]) < 0.1 and 
            abs(player_pos[1] - orb_pos[1]) < 0.1):
            # Collected the blue orb - add 10 seconds to game_start_time
            self.game.enemy_system.game_start_time += 10
            self.blue_orb.cleanup()
            self.blue_orb = None

    def pulse_green_orb(self, task):
        """Create pulsing effect for green orb"""
        if not self.green_orb or not self.green_orb.sprite:
            return Task.done
        
        pulse_speed = 3.0
        pulse_magnitude = 0.2
        
        base_scale = 1.0
        pulse = math.sin(task.time * pulse_speed) * pulse_magnitude
        new_scale = base_scale + pulse
        
        self.green_orb.sprite.setScale(new_scale)
        
        return Task.cont

    def pulse_blue_orb(self, task):
        """Create pulsing effect for blue orb"""
        if not self.blue_orb or not self.blue_orb.sprite:
            return Task.done
        
        pulse_speed = 3.0
        pulse_magnitude = 0.2
        
        base_scale = 1.0
        pulse = math.sin(task.time * pulse_speed) * pulse_magnitude
        new_scale = base_scale + pulse
        
        self.blue_orb.sprite.setScale(new_scale)
        
        return Task.cont

    def cleanup(self):
        """Clean up system resources"""
        if self.green_orb:
            self.green_orb.cleanup()
            self.green_orb = None
            
        if self.blue_orb:
            self.blue_orb.cleanup()
            self.blue_orb = None
            
        # Remove any running tasks
        taskMgr = self.game.taskMgr
        taskMgr.remove("pulseGreenOrb")
        taskMgr.remove("pulseBlueOrb")