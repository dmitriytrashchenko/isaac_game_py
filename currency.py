import pygame
import math
from constants import *

CURRENCY_SIZE = ITEM_SIZE - 2


class Eye(pygame.sprite.Sprite):
    """Глаз — валюта. Копится на счётчике игрока (Player.eyes).
    Магазина/траты пока нет — см. Known_Issues.md."""

    def __init__(self, x, y, amount=1):
        super().__init__()
        self.amount = amount

        self.float_offset = 0.0
        self.original_y = y

        self.image = pygame.Surface((CURRENCY_SIZE, CURRENCY_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self._render()

    def update(self, dt):
        self.float_offset += 3 * dt
        self.rect.centery = int(self.original_y + math.sin(self.float_offset) * 3)

    def _render(self):
        s = CURRENCY_SIZE
        pygame.draw.ellipse(self.image, WHITE, (0, s // 2 - 4, s, 8))
        pygame.draw.ellipse(self.image, WHITE, (0, s // 2 - 4, s, 8), 1)
        pygame.draw.circle(self.image, (90, 190, 90), (s // 2, s // 2), 3)  # радужка
        pygame.draw.circle(self.image, BLACK, (s // 2, s // 2), 1)  # зрачок
