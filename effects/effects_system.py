import math
import random
import time
from direct.task import Task
from panda3d.core import CardMaker, TransparencyAttrib, PNMImage, Texture

class EffectsSystem:
    def __init__(self, game):
        self.game = game
        self.explosions = []
        self.explosion_data = {}
        self.explosion_duration = 0.3
        
        # Dash effect properties
        self.dash_trail_particles = []
        self.dash_arc = None
        self.dash_glow = None
        self.trail_lifetime = 0.4
        self.max_trail_particles = 15

    def create_explosion(self, pos_x, pos_y, is_aoe=False):
        """Create an explosion effect at the given position"""
        explosion_size = 0.3 if is_aoe else 0.2
        
        cm = CardMaker("explosion")
        cm.setFrame(-explosion_size, explosion_size, -explosion_size, explosion_size)
        explosion = self.game.render2d.attachNewNode(cm.generate())
        
        texture_size = 128
        image = PNMImage(texture_size, texture_size, 4)
        center_x = texture_size // 2
        center_y = texture_size // 2
        radius = texture_size // 2
        
        image.fill(0, 0, 0)
        image.alphaFill(0)
        
        # Use different colors for AoE explosions
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    noise = random.uniform(0.8, 1.0)
                    intensity = intensity * noise
                    
                    if is_aoe:
                        # Blue-white explosion for AoE
                        if distance < radius * 0.3:
                            image.setXel(x, y, 0.9, 0.95, 1.0)  # White-blue core
                        elif distance < radius * 0.6:
                            image.setXel(x, y, 0.4, 0.6, 1.0)  # Bright blue
                        else:
                            image.setXel(x, y, 0.2, 0.4, 0.8)  # Darker blue
                    else:
                        # Original orange explosion
                        if distance < radius * 0.3:
                            image.setXel(x, y, 1.0, 1.0, 0.7)
                        elif distance < radius * 0.6:
                            image.setXel(x, y, 1.0, 0.5, 0.0)
                        else:
                            image.setXel(x, y, 1.0, 0.2, 0.0)
                    
                    if distance > radius * 0.7:
                        edge_factor = 1.0 - ((distance - radius * 0.7) / (radius * 0.3))
                        intensity *= edge_factor
                    
                    image.setAlpha(x, y, intensity)
        
        texture = Texture()
        texture.load(image)
        explosion.setTexture(texture)
        
        explosion.setBin('fixed', 100)
        explosion.setDepthTest(False)
        explosion.setDepthWrite(False)
        explosion.setTransparency(TransparencyAttrib.MAlpha)
        explosion.setPos(pos_x, 0, pos_y)
        
        initial_rotation = random.uniform(0, 360)
        explosion.setR(initial_rotation)
        
        self.explosion_data[explosion] = {
            'start_time': time.time(),
            'pos_x': pos_x,
            'pos_y': pos_y,
            'rotation_speed': random.uniform(-180, 180),
            'initial_rotation': initial_rotation,
            'is_aoe': is_aoe
        }
        
        self.explosions.append(explosion)

    def create_dash_visuals(self):
        """Create visual effects for dash ability"""
        # Create dash arc
        arc_size = 0.15
        cm = CardMaker("dash_arc")
        cm.setFrame(-arc_size, arc_size, -arc_size, arc_size)
        self.dash_arc = self.game.render2d.attachNewNode(cm.generate())
        
        # Create arc texture
        texture_size = 128
        arc_image = PNMImage(texture_size, texture_size, 4)
        center_x = texture_size // 2
        center_y = texture_size // 2
        radius = texture_size // 2
        
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                angle = math.atan2(dy, dx)
                
                if distance <= radius and 0 <= angle <= math.pi/2:
                    intensity = 1.0 - (distance / radius)
                    intensity = intensity ** 0.3
                    arc_image.setXel(x, y, 0.9, 0.95, 1.0)
                    arc_image.setAlpha(x, y, intensity)
                else:
                    arc_image.setAlpha(x, y, 0)

        arc_texture = Texture()
        arc_texture.load(arc_image)
        self.dash_arc.setTexture(arc_texture)
        self.dash_arc.setTransparency(TransparencyAttrib.MAlpha)
        self.dash_arc.setBin('fixed', 100)
        self.dash_arc.hide()

        # Create dash glow
        glow_size = 0.2
        cm = CardMaker("dash_glow")
        cm.setFrame(-glow_size, glow_size, -glow_size, glow_size)
        self.dash_glow = self.game.render2d.attachNewNode(cm.generate())
        
        # Create glow texture
        glow_image = PNMImage(texture_size, texture_size, 4)
        
        for x in range(texture_size):
            for y in range(texture_size):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= radius:
                    intensity = 1.0 - (distance / radius)
                    intensity = intensity ** 1.5
                    glow_image.setXel(x, y, 0.8, 0.9, 1.0)
                    glow_image.setAlpha(x, y, intensity * 0.9)
                else:
                    glow_image.setAlpha(x, y, 0)
        
        glow_texture = Texture()
        glow_texture.load(glow_image)
        self.dash_glow.setTexture(glow_texture)
        self.dash_glow.setTransparency(TransparencyAttrib.MAlpha)
        self.dash_glow.setBin('fixed', 99)
        self.dash_glow.hide()

    def create_trail_particle(self):
        """Create a trail particle for dash effect"""
        particle_size = 0.04
        cm = CardMaker("trail_particle")
        cm.setFrame(-particle_size, particle_size, -particle_size, particle_size)
        particle = self.game.render2d.attachNewNode(cm.generate())
        
        texture_size = 64
        particle_image = PNMImage(texture_size, texture_size, 4)
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
                    particle_image.setXel(x, y, 0.7, 0.85, 1.0)
                    particle_image.setAlpha(x, y, intensity * 0.8)
                else:
                    particle_image.setAlpha(x, y, 0)
        
        particle_texture = Texture()
        particle_texture.load(particle_image)
        particle.setTexture(particle_texture)
        particle.setTransparency(TransparencyAttrib.MAlpha)
        particle.setBin('fixed', 98)
        
        return particle

    def update_explosions(self, task):
        """Update explosion animations"""
        if self.game.paused and not self.game.boss_system.boss_death_sequence:
            return Task.cont
        
        current_time = time.time()
        
        for explosion in self.explosions[:]:
            if explosion not in self.explosion_data:
                continue
                
            data = self.explosion_data[explosion]
            age = current_time - data['start_time']
            duration = data.get('duration', self.explosion_duration)
            
            if age > duration:
                explosion.removeNode()
                self.explosions.remove(explosion)
                self.explosion_data.pop(explosion)
                continue
            
            progress = age / duration
            
            # Handle custom scaling if specified
            if 'start_scale' in data and 'end_scale' in data:
                if progress < 0.5:
                    current_scale = data['start_scale'] + (data['end_scale'] - data['start_scale']) * (2 * progress * progress)
                else:
                    progress = progress * 2 - 1
                    current_scale = data['start_scale'] + (data['end_scale'] - data['start_scale']) * (1 - 0.5 * (1 - progress) * (1 - progress))
                explosion.setScale(current_scale)
            else:
                scale_factor = math.sin(progress * math.pi) * 0.5 + 0.5
                base_size = 0.4 if data.get('is_aoe', False) else 0.3
                max_size = 0.8 if data.get('is_aoe', False) else 0.6
                current_size = base_size + (max_size * scale_factor)
                explosion.setScale(current_size)
            
            rotation = data['initial_rotation'] + (data['rotation_speed'] * age)
            explosion.setR(rotation)
            
            if progress < 0.3:
                intensity = 1.0
            else:
                intensity = 1.0 - ((progress - 0.3) / 0.7)
                pulse = math.sin(progress * 20) * 0.1
                intensity = max(0, min(1, intensity + pulse))
            
            explosion.setColorScale(1, 1, 1, intensity)
        
        return Task.cont

    def cleanup(self):
        """Clean up system resources"""
        for explosion in self.explosions:
            explosion.removeNode()
        self.explosions.clear()
        self.explosion_data.clear()
        
        for particle in self.dash_trail_particles:
            particle['node'].removeNode()
        self.dash_trail_particles.clear()
        
        if self.dash_arc:
            self.dash_arc.removeNode()
            self.dash_arc = None
            
        if self.dash_glow:
            self.dash_glow.removeNode()
            self.dash_glow = None