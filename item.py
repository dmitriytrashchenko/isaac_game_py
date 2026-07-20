import pygame
import random
import math
from constants import *

ITEM_BASE_COLORS = {
    "health": GREEN,
    "damage_up": RED,
    "speed_up": BLUE,
    "tears_up": YELLOW,
    "max_health": (255, 100, 100),
    "luck_up": (80, 220, 120),
    "range_up": (120, 190, 230),
}


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type=None):
        super().__init__()

        # Случайный тип предмета, если не указан
        if item_type is None:
            self.item_type = random.choice(list(ITEM_BASE_COLORS.keys()))
        else:
            self.item_type = item_type

        self.rect = pygame.Rect(0, 0, ITEM_SIZE, ITEM_SIZE)
        self.rect.center = (x, y)

        # Эффекты анимации
        self.float_offset = 0
        self.float_speed = 3
        self.original_y = y

        # Имя/описание в зависимости от типа
        self._setup_item_properties()
        self._render(ITEM_BASE_COLORS.get(self.item_type, WHITE))

    def _setup_item_properties(self):
        """Название и описание предмета в зависимости от типа"""
        names = {
            "health": ("Health Up", "Restores 1 health"),
            "damage_up": ("Damage Up", "Increases tear damage"),
            "speed_up": ("Speed Up", "Increases movement speed"),
            "tears_up": ("Tears Up", "Increases tear rate"),
            "max_health": ("Max Health Up", "Increases maximum health"),
            "luck_up": ("Luck Up", "Increases luck (drop chances)"),
            "range_up": ("Range Up", "Increases tear range"),
        }
        self.name, self.description = names.get(self.item_type, ("Unknown Item", "???"))

    def update(self, dt):
        """Обновление анимации предмета"""
        # Эффект парения
        self.float_offset += self.float_speed * dt
        float_y = self.original_y + math.sin(self.float_offset) * 3
        self.rect.centery = int(float_y)

        # Эффект мерцания
        brightness = int(200 + 55 * math.sin(self.float_offset * 2))
        base = ITEM_BASE_COLORS.get(self.item_type, (brightness, brightness, brightness))
        color = tuple(min(255, int(c * (brightness / 255))) for c in base)

        self._render(color)

    def _render(self, color):
        """Простой узнаваемый силуэт вместо плоского квадрата — форма
        отличает тип предмета не только по цвету"""
        s = ITEM_SIZE
        surface = pygame.Surface((s, s), pygame.SRCALPHA)

        if self.item_type == "health":
            # Флакон зелья: горлышко + округлое тело с бликом
            pygame.draw.rect(surface, color, (s // 2 - 1, 1, 2, 3))
            pygame.draw.ellipse(surface, color, (2, 4, s - 4, s - 5))
            highlight = tuple(min(255, c + 60) for c in color)
            pygame.draw.ellipse(surface, highlight, (4, 6, 3, 3))
        elif self.item_type == "damage_up":
            # Клинок: ромб-лезвие + рукоять
            pygame.draw.polygon(surface, color, [
                (s // 2, 1), (s // 2 + 3, s // 2), (s // 2, s - 4), (s // 2 - 3, s // 2)
            ])
            pygame.draw.rect(surface, (90, 60, 30), (s // 2 - 1, s - 4, 2, 4))
        elif self.item_type == "speed_up":
            # Сапог
            pygame.draw.polygon(surface, color, [
                (4, 2), (9, 2), (9, 8), (13, 8), (13, 13), (4, 13)
            ])
        elif self.item_type == "tears_up":
            # Молния
            pygame.draw.polygon(surface, color, [
                (9, 1), (4, 9), (7, 9), (6, 15), (12, 6), (9, 6)
            ])
        elif self.item_type == "max_health":
            # Сердце: два кружка-доли + треугольник-низ
            pygame.draw.circle(surface, color, (s // 2 - 3, 5), 3)
            pygame.draw.circle(surface, color, (s // 2 + 3, 5), 3)
            pygame.draw.polygon(surface, color, [(2, 6), (s - 2, 6), (s // 2, s - 1)])
        elif self.item_type == "luck_up":
            # Клевер: 4 кружка-лепестка + стебель
            for dx, dy in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
                pygame.draw.circle(surface, color, (s // 2 + dx, s // 2 - 2 + dy), 3)
            pygame.draw.line(surface, (60, 140, 70), (s // 2, s // 2 + 3), (s // 2, s - 1), 2)
        elif self.item_type == "range_up":
            # Мишень: концентрические кольца
            pygame.draw.circle(surface, color, (s // 2, s // 2), 7, 2)
            pygame.draw.circle(surface, color, (s // 2, s // 2), 4, 1)
            pygame.draw.circle(surface, color, (s // 2, s // 2), 1)
        else:
            surface.fill(color)

        self.image = surface

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
        elif self.item_type == "luck_up":
            player.increase_luck(1)
        elif self.item_type == "range_up":
            player.increase_range(0.4)
