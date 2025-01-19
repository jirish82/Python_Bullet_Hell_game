from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextureStage, TransparencyAttrib, CardMaker
from utils.resource_loader import get_resource_path

class TownArea:
    def __init__(self, game):
        self.game = game  # Reference to main game instance
        
        # Load and set up the town background
        self.background = game.loader.loadTexture(get_resource_path("town.png"))
        cm = CardMaker("town_background")
        cm.setFrame(-game.aspect_ratio * 0.58, game.aspect_ratio * 0.8, -1, 1)
        self.background_node = game.render2d.attachNewNode(cm.generate())
        self.background_node.setTexture(self.background)
        
        # Initially hide the town background
        self.background_node.hide()
    
    def enter(self):
        """Called when entering the town area"""
        self.background_node.show()
        
    def exit(self):
        """Called when leaving the town area"""
        self.background_node.hide()

    def update(self, task):
        """Update logic for town area"""
        # Town-specific update logic will go here
        return task.cont