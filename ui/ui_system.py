from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

class UISystem:
    def __init__(self, game):
        self.game = game
        
        # Score display
        self.score_text = OnscreenText(
            text="Score: 0",
            pos=(-0.9, 0.9),  # Top left corner
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            shadow=(0, 0, 0, 1)
        )

        # Game over text
        self.game_over_text = OnscreenText(
            text="GAME OVER\nPress START or P to restart",
            pos=(0, 0),
            scale=0.1,
            fg=(1, 0, 0, 1),
            shadow=(0, 0, 0, 1)
        )
        self.game_over_text.hide()

        # Pause text
        self.pause_text = OnscreenText(
            text="PAUSED",
            pos=(0, 0),
            scale=0.1,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 1)
        )
        self.pause_text.hide()

        # Debug text
        self.debug_text = OnscreenText(
            text="",
            pos=(game.aspect_ratio - 0.1, 0.9),  # Top right position
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            mayChange=True,
            bg=(0, 0, 0, 0.5)  # Semi-transparent black background
        )

    def update_score(self, score):
        """Update score display"""
        self.score_text.setText(f"Score: {score}")

    def show_game_over(self):
        """Show game over screen"""
        self.game_over_text.show()

    def hide_game_over(self):
        """Hide game over screen"""
        self.game_over_text.hide()

    def show_pause(self):
        """Show pause screen"""
        self.pause_text.show()

    def hide_pause(self):
        """Hide pause screen"""
        self.pause_text.hide()

    def update_debug_text(self):
        """Update debug information display"""
        current_time = self.game.actual_game_time
        effective_time = self.game.enemy_system.game_start_time - self.game.game_start_time
        
        debug_str = (
            f"Enemy Limit: {self.game.enemy_system.enemy_limit}\n"
            f"Game Time: {effective_time:.1f}s\n"
            f"Boss Time: {current_time:.1f}s\n"
            f"Level: {self.game.level}"
        )
        
        self.debug_text.setText(debug_str)

    def cleanup(self):
        """Clean up UI elements"""
        self.score_text.destroy()
        self.game_over_text.destroy()
        self.pause_text.destroy()
        self.debug_text.destroy()