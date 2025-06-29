import pygame
from constants import *

class Tear(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed, damage):
        super().__init__()
        
        # Создание поверхности слезы
        self.image = pygame.Surface((TEAR_SIZE, TEAR_SIZE))
        self.image.fill(BLUE)
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
        new_surface = pygame.Surface((TEAR_SIZE, TEAR_SIZE), pygame.SRCALPHA)
        new_surface.fill((*BLUE, alpha))
        self.image = new_surface
        
        # Удаление слезы, если время жизни истекло
        if self.lifetime <= 0:
            self.kill()

class EnemyTear(Tear):
    def __init__(self, x, y, direction, speed, damage):
        super().__init__(x, y, direction, speed, damage)
        
        # Слёзы врагов красного цвета
        self.image.fill(RED)
        self.base_color = RED
    
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
        new_surface = pygame.Surface((TEAR_SIZE, TEAR_SIZE), pygame.SRCALPHA)
        new_surface.fill((*self.base_color, alpha))
        self.image = new_surface
        
        # Удаление слезы, если время жизни истекло
        if self.lifetime <= 0:
            self.kill()