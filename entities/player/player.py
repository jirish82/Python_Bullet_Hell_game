from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker, TransparencyAttrib, TextureStage
from utils.resource_loader import get_resource_path

class Player:
    def __init__(self, game):
        self.game = game
        self.pos = [0, 0]
        self.movement_speed = 0.02
        self.is_invincible = False
        self.invincibility_duration = 1.5
        self.invincibility_start_time = 0
        self.invincibility_flash_speed = 8.0

        # Dash properties
        self.dash_cooldown = 3
        self.last_dash_time = 0
        self.dash_distance = 0.6
        self.is_dashing = False
        self.dash_duration = 0.15
        self.dash_start_time = 0
        self.dash_start_pos = None
        self.dash_target_pos = None
        
        # Create player sprite
        cm = CardMaker("player")
        player_size = 0.035
        cm.setFrame(-player_size, player_size, -player_size, player_size)
        self.sprite = game.render2d.attachNewNode(cm.generate())
        player_tex = game.loader.loadTexture(get_resource_path("player.png"))
        self.sprite.setTexture(player_tex)
        self.sprite.setTransparency(TransparencyAttrib.MAlpha)
        self.sprite.setScale(game.aspect_ratio, 1, 2.5)

    def update_position(self, dx, dy):
        """Update player position with bounds checking"""
        self.pos[0] += dx
        self.pos[1] += dy
        
        # Clamp position to screen bounds
        self.pos[0] = max(-self.game.aspect_ratio + 0.05, min(self.game.aspect_ratio - 0.05, self.pos[0]))
        self.pos[1] = max(-0.95, min(0.95, self.pos[1]))
        
        # Update sprite position
        self.sprite.setPos(self.pos[0], 0, self.pos[1])

    def get_position(self):
        """Get current player position"""
        return self.pos[0], self.pos[1]

    def cleanup(self):
        """Clean up player resources"""
        if self.sprite:
            self.sprite.removeNode()