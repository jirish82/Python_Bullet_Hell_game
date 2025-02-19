from panda3d.core import CardMaker, TransparencyAttrib
from utils.resource_loader import get_resource_path

class Enemy:
    def __init__(self, game, position, speed):
        self.game = game
        self.pos = list(position)  # [x, y]
        self.speed = speed
        
        # Create enemy sprite
        cm = CardMaker("enemy")
        enemy_size = 0.1
        cm.setFrame(-enemy_size, enemy_size, -enemy_size, enemy_size)
        self.sprite = game.render2d.attachNewNode(cm.generate())
        enemy_tex = game.loader.loadTexture(get_resource_path("enemy.png"))
        self.sprite.setTexture(enemy_tex)
        self.sprite.setTransparency(TransparencyAttrib.MAlpha)
        self.update_position()

    def update_position(self):
        """Update sprite position based on current position"""
        self.sprite.setPos(self.pos[0], 0, self.pos[1])

    def move_towards(self, target_pos):
        """Move enemy towards target position"""
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        
        # Normalize direction
        distance = (dx * dx + dy * dy) ** 0.5
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Update position with speed
        new_x = self.pos[0] + dx * self.speed
        new_y = self.pos[1] + dy * self.speed
        
        # Clamp to screen bounds
        new_x = max(min(new_x, self.game.aspect_ratio - 0.05), -self.game.aspect_ratio + 0.05)
        new_y = max(min(new_y, 0.95), -0.95)
        
        self.pos[0] = new_x
        self.pos[1] = new_y
        self.update_position()

    def get_position(self):
        """Get current enemy position"""
        return self.pos[0], self.pos[1]

    def cleanup(self):
        """Clean up enemy resources"""
        if self.sprite:
            self.sprite.removeNode()