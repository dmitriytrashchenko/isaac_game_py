import pygame

TORCH_MAX_HEALTH = 4


class Torch:
    """Разрушаемый факел: 4 попадания снаряда/меча тушат его, тускнея
    по пути (см. Room._draw_torch для визуала — сам факел не спрайт,
    рендерится процедурно в Room.draw()). Хитбокс — для ручных проверок
    коллизий в Game (тот же паттерн, что у Vase, но без pygame.Surface)."""

    def __init__(self, x, y):
        self.pos = (x, y)
        self.health = TORCH_MAX_HEALTH
        self.extinguished = False

        self.rect = pygame.Rect(0, 0, 16, 22)
        self.rect.midbottom = (x, y + 12)

    def take_damage(self, damage):
        if self.extinguished:
            return False
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.extinguished = True
            return True  # факел только что потушен этим попаданием
        return False
