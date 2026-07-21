import pygame
import random
from constants import *

VASE_SIZE = 26

# Палитры глины: (тело, тёмная обводка, блик)
VASE_PALETTES = [
    ((160, 100, 60), (95, 55, 30), (200, 145, 95)),   # терракота
    ((110, 120, 130), (60, 65, 75), (170, 180, 190)),  # каменная
    ((90, 110, 90), (50, 65, 50), (140, 165, 130)),    # позеленевшая бронза
    ((120, 80, 130), (70, 45, 80), (175, 130, 190)),   # ритуальная (фиолетовая)
]

VASE_SHAPES = ["pot", "urn", "bowl"]


class Vase(pygame.sprite.Sprite):
    """Разрушаемая ваза-препятствие (аналог жанровых горшков/ваз). Блокирует
    проход игроку, пока цела; разбивается с одного попадания снаряда/меча,
    с шансом оставить предмет (валюта с ваз не выпадает — см. Game._destroy_vase).
    Цвет/форма/узор выбираются случайно при создании для визуального
    разнообразия между вазами."""

    def __init__(self, x, y, palette=None, shape=None):
        super().__init__()
        self.health = 1
        self.destroyed = False

        self.clay, self.dark, self.highlight = palette or random.choice(VASE_PALETTES)
        self.shape = shape or random.choice(VASE_SHAPES)
        self.shard_color = self.clay
        self.pattern = random.choice(["crack", "dots", "stripe"])

        self.image = pygame.Surface((VASE_SIZE, VASE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self._render()

    def take_damage(self, damage):
        self.health -= damage

    def _render(self):
        s = VASE_SIZE
        surface = pygame.Surface((s, s), pygame.SRCALPHA)

        if self.shape == "pot":
            body = [(s // 2 - 5, 5), (s // 2 + 5, 5), (s - 3, s - 5), (3, s - 5)]
            neck = (s // 2 - 6, 0, 12, 5)
            base = (2, s - 6, s - 4, 5)
        elif self.shape == "urn":
            body = [(s // 2 - 3, 3), (s // 2 + 3, 3), (s - 2, s // 2), (s - 4, s - 5), (4, s - 5), (2, s // 2)]
            neck = (s // 2 - 4, 0, 8, 4)
            base = (5, s - 6, s - 10, 5)
        else:  # bowl — широкая и низкая
            body = [(s // 2 - 7, 9), (s // 2 + 7, 9), (s - 2, s - 4), (2, s - 4)]
            neck = (s // 2 - 7, 6, 14, 4)
            base = (3, s - 5, s - 6, 4)

        pygame.draw.polygon(surface, self.dark, body)
        pygame.draw.polygon(surface, self.clay, [(x, y - 2) for x, y in body])
        pygame.draw.polygon(surface, self.dark, body, 2)
        pygame.draw.line(surface, self.highlight, (s // 2 - 3, body[0][1] + 2), (5, s - 8), 2)

        pygame.draw.ellipse(surface, self.dark, neck)
        pygame.draw.ellipse(surface, self.clay, (neck[0] + 1, neck[1], neck[2] - 2, max(2, neck[3] - 2)))
        pygame.draw.ellipse(surface, self.dark, base)

        # Узор
        if self.pattern == "crack":
            pygame.draw.line(surface, self.dark, (s // 2 - 2, 9), (s // 2 + 3, 15), 1)
        elif self.pattern == "dots":
            for dx in (-4, 0, 4):
                pygame.draw.circle(surface, self.dark, (s // 2 + dx, s // 2 + 2), 1)
        elif self.pattern == "stripe":
            pygame.draw.line(surface, self.dark, (4, s // 2 + 3), (s - 4, s // 2 + 3), 1)

        self.image = surface
