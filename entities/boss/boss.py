from panda3d.core import CardMaker, TransparencyAttrib
from utils.resource_loader import get_resource_path

class Boss:
    def __init__(self, game, position):
        self.game = game
        self.pos = list(position)
        self.health = 10  # Default health
        self.speed_multiplier = 0.5
        
        # Create boss sprite
        cm = CardMaker("boss")
        self.size = 0.3  # Boss is larger than regular enemies
        cm.setFrame(-self.size, self.size, -self.size, self.size)
        self.sprite = game.render2d.attachNewNode(cm.generate())
        boss_tex = game.loader.loadTexture(get_resource_path("boss1.png"))
        self.sprite.setTexture(boss_tex)
        self.sprite.setTransparency(TransparencyAttrib.MAlpha)
        self.update_position()

    def update_position(self):
        """Update sprite position based on current position"""
        self.sprite.setPos(self.pos[0], 0, self.pos[1])

    def move_towards(self, target_pos, speed):
        """Move boss towards target position"""
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        
        # Normalize direction
        distance = (dx * dx + dy * dy) ** 0.5
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Update position with speed
        new_x = self.pos[0] + dx * speed * self.speed_multiplier
        new_y = self.pos[1] + dy * speed * self.speed_multiplier
        
        # Clamp to screen bounds with boss size consideration
        new_x = max(min(new_x, self.game.aspect_ratio - self.size), -self.game.aspect_ratio + self.size)
        new_y = max(min(new_y, 0.95), -0.95)
        
        self.pos[0] = new_x
        self.pos[1] = new_y
        self.update_position()

    def get_position(self):
        """Get current boss position"""
        return self.pos[0], self.pos[1]

    def take_damage(self, amount=1):
        """Reduce boss health by given amount"""
        self.health -= amount
        return self.health <= 0

    def set_scale(self, scale):
        """Set boss sprite scale"""
        self.sprite.setScale(scale)

    def set_color_scale(self, r, g, b, a):
        """Set boss sprite color scale"""
        self.sprite.setColorScale(r, g, b, a)

    def cleanup(self):
        """Clean up boss resources"""
        if self.sprite:
            self.sprite.removeNode()