import pygame
import random

class Particle(pygame.sprite.Sprite):
    """Лёгкая затухающая частица для эффектов (искры факелов, вспышка
    при попадании/смерти врага)."""

    def __init__(self, pos, velocity, color, lifetime, size=3, gravity=0.0):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(velocity)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.gravity = gravity

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self._render()

    def update(self, dt):
        self.velocity.y += self.gravity * dt
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.lifetime -= dt
        self._render()
        if self.lifetime <= 0:
            self.kill()

    def _render(self):
        alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(surface, (*self.color, alpha), (self.size // 2, self.size // 2), max(1, self.size // 2))
        self.image = surface


def spawn_hit_sparks(pos, color, count=6):
    """Взрыв искр при попадании/смерти врага"""
    particles = []
    for _ in range(count):
        angle = random.uniform(0, 6.283)
        speed = random.uniform(40, 110)
        velocity = pygame.math.Vector2(speed, 0).rotate_rad(angle)
        lifetime = random.uniform(0.2, 0.4)
        particles.append(Particle(pos, velocity, color, lifetime, size=random.randint(2, 4)))
    return particles


def spawn_ember(pos):
    """Одна искра/уголёк, поднимающийся от факела"""
    velocity = (random.uniform(-8, 8), random.uniform(-35, -15))
    lifetime = random.uniform(0.6, 1.1)
    color = (255, random.randint(120, 190), 30)
    return Particle(pos, velocity, color, lifetime, size=2, gravity=-6)
