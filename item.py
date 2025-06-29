import pygame
import random
from constants import *

class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type=None):
        super().__init__()
        
        # Случайный тип предмета, если не указан
        if item_type is None:
            self.item_type = random.choice([
                "health", "damage_up", "speed_up", "tears_up", "max_health"
            ])
        else:
            self.item_type = item_type
        
        # Создание поверхности предмета
        self.image = pygame.Surface((ITEM_SIZE, ITEM_SIZE))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Эффекты анимации
        self.float_offset = 0
        self.float_speed = 3
        self.original_y = y
        
        # Цвет и описание в зависимости от типа
        self._setup_item_properties()
    
    def _setup_item_properties(self):
        """Настройка свойств предмета в зависимости от типа"""
        if self.item_type == "health":
            self.image.fill(GREEN)
            self.name = "Health Up"
            self.description = "Restores 1 health"
        elif self.item_type == "damage_up":
            self.image.fill(RED)
            self.name = "Damage Up"
            self.description = "Increases tear damage"
        elif self.item_type == "speed_up":
            self.image.fill(BLUE)
            self.name = "Speed Up"
            self.description = "Increases movement speed"
        elif self.item_type == "tears_up":
            self.image.fill(YELLOW)
            self.name = "Tears Up"
            self.description = "Increases tear rate"
        elif self.item_type == "max_health":
            self.image.fill((255, 100, 100))  # Светло-красный
            self.name = "Max Health Up"
            self.description = "Increases maximum health"
        else:
            self.image.fill(WHITE)
            self.name = "Unknown Item"
            self.description = "???"
    
    def update(self, dt):
        """Обновление анимации предмета"""
        # Эффект парения
        self.float_offset += self.float_speed * dt
        float_y = self.original_y + math.sin(self.float_offset) * 3
        self.rect.centery = int(float_y)
        
        # Эффект мерцания
        brightness = int(200 + 55 * math.sin(self.float_offset * 2))
        
        if self.item_type == "health":
            color = (0, brightness, 0)
        elif self.item_type == "damage_up":
            color = (brightness, 0, 0)
        elif self.item_type == "speed_up":
            color = (0, 0, brightness)
        elif self.item_type == "tears_up":
            color = (brightness, brightness, 0)
        elif self.item_type == "max_health":
            color = (brightness, brightness//2, brightness//2)
        else:
            color = (brightness, brightness, brightness)
        
        self.image.fill(color)
    
    def apply_effect(self, player):
        """Применение эффекта предмета к игроку"""
        if self.item_type == "health":
            player.heal(1)
        elif self.item_type == "damage_up":
            player.increase_damage(0.5)
        elif self.item_type == "speed_up":
            player.increase_speed(30)
        elif self.item_type == "tears_up":
            player.increase_tear_rate(0.05)
        elif self.item_type == "max_health":
            player.increase_max_health(2)

# Импорт math для анимации
import math