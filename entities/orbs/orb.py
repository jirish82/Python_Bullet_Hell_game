import random
import math
import time
from panda3d.core import CardMaker, TransparencyAttrib, PNMImage, Texture

class Orb:
    def __init__(self, game, size=0.05, color=(0, 1, 0)):  # Default to green
        self.game = game
        self.size = size
        self.color = color
        self.sprite = None
        self.spawn_time = None
        self.create_sprite()

    def create_sprite(self):
        """Create the orb sprite with glowing effect"""
        cm = CardMaker("orb")
        cm.setFrame(-self.size, self.size, -self.size, self.size)
        self.sprite = self.game.render2d.attachNewNode(cm.generate())
        
        # Create glowing texture
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
                        # White-tinted center
                        image.setXel(x, y, 
                            0.8 + 0.2 * self.color[0],
                            0.8 + 0.2 * self.color[1],
                            0.8 + 0.2 * self.color[2])
                        image.setAlpha(x, y, 1.0)
                    else:
                        # Colored glow
                        image.setXel(x, y, 
                            0.2 * self.color[0],
                            0.2 * self.color[1],
                            0.2 * self.color[2])
                        image.setAlpha(x, y, min(1.0, intensity * 1.5))
                else:
                    image.setAlpha(x, y, 0)
        
        texture = Texture()
        texture.load(image)
        self.sprite.setTexture(texture)
        self.sprite.setTransparency(TransparencyAttrib.MAlpha)
        
        self.sprite.setBin('fixed', 100)
        self.sprite.setDepthTest(False)
        self.sprite.setDepthWrite(False)

    def spawn(self):
        """Spawn orb at random position within screen bounds"""
        x = random.uniform(-self.game.aspect_ratio * 0.9 + 0.1, self.game.aspect_ratio * 0.9 - 0.1)
        y = random.uniform(-0.8, 0.8)
        self.sprite.setPos(x, 0, y)
        self.spawn_time = time.time()

    def get_position(self):
        """Get current orb position"""
        pos = self.sprite.getPos()
        return pos[0], pos[2]

    def cleanup(self):
        """Clean up orb resources"""
        if self.sprite:
            self.sprite.removeNode()
            self.sprite = None

class GreenOrb(Orb):
    def __init__(self, game):
        super().__init__(game, color=(0, 1, 0))
        self.duration = 2.0

class BlueOrb(Orb):
    def __init__(self, game):
        super().__init__(game, color=(0, 0, 1))
        self.duration = 3.0