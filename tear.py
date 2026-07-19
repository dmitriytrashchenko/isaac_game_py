import pygame
from constants import *

class Tear(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed, damage, color=BLUE, size=TEAR_SIZE):
        super().__init__()

        self.base_color = color
        self.size = size

        # Создание поверхности слезы
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Характеристики
        self.direction = pygame.math.Vector2(direction)
        self.speed = speed
        self.damage = damage
        self.lifetime = TEAR_LIFETIME

        # Скорость
        self.velocity = self.direction * self.speed

    def update(self, dt):
        # Обновление позиции
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt

        # Уменьшение времени жизни
        self.lifetime -= dt

        # Изменение прозрачности в зависимости от времени жизни
        alpha = int(255 * (self.lifetime / TEAR_LIFETIME))
        alpha = max(0, min(255, alpha))

        # Создание новой поверхности с альфа-каналом
        new_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        new_surface.fill((*self.base_color, alpha))
        self.image = new_surface

        # Удаление слезы, если время жизни истекло
        if self.lifetime <= 0:
            self.kill()

class EnemyTear(Tear):
    def __init__(self, x, y, direction, speed, damage):
        super().__init__(x, y, direction, speed, damage, color=RED)


class MeleeSwing(pygame.sprite.Sprite):
    """Кратковременная визуальная вспышка удара мечом Воина. Сам урон
    применяется мгновенно в Game.update() в момент создания удара
    (нужен доступ к группе врагов, которого у Player нет) — этот
    спрайт не наносит урон, только показывает взмах."""

    LIFETIME = 0.15

    def __init__(self, pos, color=WHITE, size=40):
        super().__init__()
        self.base_color = color
        self.size = size
        self.lifetime = self.LIFETIME

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self._render()

    def update(self, dt):
        self.lifetime -= dt
        self._render()
        if self.lifetime <= 0:
            self.kill()

    def _render(self):
        alpha = max(0, min(255, int(255 * (self.lifetime / self.LIFETIME))))
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(surface, (*self.base_color, alpha), surface.get_rect(), 4)
        self.image = surface
