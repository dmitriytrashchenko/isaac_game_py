import pygame
import random
from constants import *

# 10 уровней редкости сундука: 1 — самый частый и слабый приз,
# 10 — самый редкий и мощный джекпот. Вес выбора уровня ∝ 1/уровень
# (плавно убывающая вероятность: 1 выпадает примерно в 10 раз чаще, чем 10).
TIER_WEIGHTS = [1.0 / tier for tier in range(1, 11)]

TIER_COLORS = [
    (150, 150, 150),  # 1 - серый (обычный)
    (139, 69, 19),    # 2 - коричневый
    (0, 200, 0),      # 3 - зелёный
    (0, 150, 220),    # 4 - голубой
    (60, 60, 220),    # 5 - синий
    (150, 0, 220),    # 6 - фиолетовый
    (220, 0, 150),    # 7 - пурпурный
    (220, 100, 0),    # 8 - оранжевый
    (220, 0, 0),      # 9 - красный
    (255, 215, 0),    # 10 - золотой (легендарный)
]


def _reward_health(player):
    player.heal(1)


def _reward_speed_small(player):
    player.increase_speed(20)


def _reward_tears_small(player):
    player.increase_tear_rate(0.03)


def _reward_damage_small(player):
    player.increase_damage(0.5)


def _reward_max_health_small(player):
    player.increase_max_health(1)


def _reward_speed_big(player):
    player.increase_speed(40)


def _reward_tears_big(player):
    player.increase_tear_rate(0.06)


def _reward_damage_big(player):
    player.increase_damage(1.0)


def _reward_max_health_big(player):
    player.increase_max_health(3)


def _reward_legendary(player):
    player.increase_damage(1.5)
    player.increase_speed(50)
    player.increase_tear_rate(0.08)
    player.increase_max_health(2)


# Индекс i соответствует уровню редкости i+1
TIER_REWARDS = [
    ("Health Up", _reward_health),
    ("Speed Up", _reward_speed_small),
    ("Tears Up", _reward_tears_small),
    ("Damage Up", _reward_damage_small),
    ("Max Health Up", _reward_max_health_small),
    ("Speed Surge", _reward_speed_big),
    ("Rapid Fire", _reward_tears_big),
    ("Power Shot", _reward_damage_big),
    ("Vitality Boost", _reward_max_health_big),
    ("Legendary Blessing", _reward_legendary),
]


def roll_tier():
    """Выбирает уровень редкости 1..10 с весом ∝ 1/уровень."""
    return random.choices(range(1, 11), weights=TIER_WEIGHTS, k=1)[0]


class Chest(pygame.sprite.Sprite):
    """Сундук после победы над боссом. Спавнится каждый раз, но с одним
    из 10 уровней редкости приза (1 — частый и слабый, 10 — редкий джекпот).
    При касании игроком запускает анимацию рулетки: вертикальная лента
    из 3 ячеек "тикает" по случайным уровням и в конце гарантированно
    останавливается на настоящем уровне этого сундука."""

    SPIN_DURATION = 1.8
    TICK_INTERVAL = 0.12

    def __init__(self, x, y, tier=None):
        super().__init__()
        self.state = "closed"  # closed -> spinning -> opened
        self.tier = tier if tier is not None else roll_tier()
        self.reward_name, self._reward_fn = TIER_REWARDS[self.tier - 1]
        self.reward_applied = False

        self._spin_elapsed = 0.0
        self._tick_elapsed = 0.0
        self._tick_index = 0
        self._reel_sequence = []

        self._closed_size = ITEM_SIZE + 8
        self.image = pygame.Surface((self._closed_size, self._closed_size))
        self.rect = self.image.get_rect(center=(x, y))

        self._render()

    def start_spin(self):
        if self.state != "closed":
            return
        self.state = "spinning"
        self._spin_elapsed = 0.0
        self._tick_elapsed = 0.0
        self._tick_index = 0

        # Случайная лента символов, гарантированно заканчивающаяся
        # настоящим уровнем редкости этого сундука
        tick_count = max(3, int(self.SPIN_DURATION / self.TICK_INTERVAL))
        self._reel_sequence = [random.randint(1, 10) for _ in range(tick_count - 1)] + [self.tier]

    def update(self, dt):
        if self.state == "spinning":
            self._spin_elapsed += dt
            self._tick_elapsed += dt

            if self._tick_elapsed >= self.TICK_INTERVAL and self._tick_index < len(self._reel_sequence) - 1:
                self._tick_elapsed = 0.0
                self._tick_index += 1

            if self._spin_elapsed >= self.SPIN_DURATION:
                self._tick_index = len(self._reel_sequence) - 1  # гарантированно приземляемся на self.tier
                self.state = "opened"

        self._render()

    def apply_reward(self, player):
        self._reward_fn(player)

    def _resize_image(self, size):
        """Меняет размер поверхности, сохраняя центр (позицию в комнате)"""
        if self.image.get_size() == size:
            return
        center = self.rect.center
        self.image = pygame.Surface(size)
        self.rect = self.image.get_rect(center=center)

    def _render(self):
        if self.state == "spinning":
            self._render_reel()
        else:
            self._render_static()

    def _render_static(self):
        size = self._closed_size
        self._resize_image((size, size))

        color = TIER_COLORS[self.tier - 1]
        if self.state == "closed":
            self.image.fill(color)
            pygame.draw.rect(self.image, DARK_GOLD, self.image.get_rect(), 3)
        else:  # opened
            self.image.fill(DARK_GRAY)
            pygame.draw.rect(self.image, color, self.image.get_rect(), 3)

    def _render_reel(self):
        slot = self._closed_size
        visible_cells = 3
        self._resize_image((slot, slot * visible_cells))

        self.image.fill(BLACK)

        seq = self._reel_sequence
        idx = self._tick_index

        # Три видимые ячейки ленты: предыдущая (тусклая) / текущая
        # (яркая, по центру, за рамкой окошка) / следующая (тусклая)
        for cell, seq_offset in enumerate((-1, 0, 1)):
            seq_idx = idx + seq_offset
            if 0 <= seq_idx < len(seq):
                tier = seq[seq_idx]
                color = TIER_COLORS[tier - 1]
                if seq_offset != 0:
                    color = tuple(c // 3 for c in color)
                cell_rect = pygame.Rect(2, cell * slot + 1, slot - 4, slot - 2)
                pygame.draw.rect(self.image, color, cell_rect)

        # Рамка окошка рулетки (выделяет центральную/текущую ячейку)
        pygame.draw.rect(self.image, WHITE, (0, slot, slot, slot), 2)
        pygame.draw.rect(self.image, GRAY, self.image.get_rect(), 2)
