import pygame
import random
import math
from constants import *
from enemy import Enemy
from item import Item
from chest import Chest
from vase import Vase
from torch import Torch, TORCH_MAX_HEALTH

TORCH_MARGIN = 30


class Room:
    def __init__(self, room_type=ROOM_TYPES['NORMAL']):
        self.room_type = room_type
        self.cleared = False
        self.visited = False

        # Двери (вверх, вниз, влево, вправо)
        self.doors = {
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }

        # Враги в комнате
        self.enemies = []

        # Предметы в комнате
        self.items = []

        # Стены и препятствия
        self.walls = []

        # Разрушаемые вазы-препятствия (аналог горшков из Isaac)
        self.vases = []

        # Колонны — неразрушимые препятствия, дают части комнат разную
        # планировку без изменения формы самой комнаты (см. maybe_add_pillars)
        self.pillars = []

        # Сундук после победы над боссом (см. maybe_spawn_chest)
        self.chest = None
        self.chest_rolled = False

        # Факелы (объекты Torch — разрушаемые) генерируются лениво в
        # get_torches() после того, как двери уже расставлены (иначе
        # факел может оказаться прямо в дверном проёме)
        self.torches = None
        # Сработало ли уже событие "все факелы потушены" (см. Game._check_torch_challenge)
        self.torch_challenge_triggered = False

        # random с отдельным сидом на комнату — используется для стен,
        # пола, тона палитры: одна комната выглядит целостно, но отличается
        # от соседних. Текстуры кэшируются (не пересчитываются в draw()),
        # чтобы не мерцали между кадрами
        self._rng = random.Random(id(self))
        self._tint = tuple(self._rng.randint(-25, 25) for _ in range(3))

        # Генерация базовых стен комнаты
        self._generate_walls()
        self.floor_texture = self._generate_floor_texture()

    def _tinted(self, base_color):
        return tuple(max(0, min(255, c + t)) for c, t in zip(base_color, self._tint))

    def maybe_add_pillars(self):
        """С шансом 40% расставляет 2 или 4 колонны симметрично вокруг
        центра — даёт части обычных комнат другую планировку прохода"""
        self.pillars = []
        if self._rng.random() >= 0.4:
            return

        cx = ROOM_OFFSET_X + ROOM_WIDTH // 2
        cy = ROOM_OFFSET_Y + ROOM_HEIGHT // 2
        offset_x, offset_y = 110, 80
        size = 28

        corners = [(-offset_x, -offset_y), (offset_x, -offset_y), (-offset_x, offset_y), (offset_x, offset_y)]
        if self._rng.random() < 0.5:
            corners = corners[:2]  # только верхние две — асимметричный вариант

        for dx, dy in corners:
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (cx + dx, cy + dy)
            self.pillars.append(rect)

    def _generate_walls(self):
        rng = self._rng
        wall_base = self._tinted(BROWN)

        self.wall_colors = []

        def add_wall(rect):
            self.walls.append(rect)
            shade = rng.randint(-15, 15)
            self.wall_colors.append(tuple(max(0, min(255, c + shade)) for c in wall_base))

        # Верхняя стена
        for x in range(ROOM_OFFSET_X, ROOM_OFFSET_X + ROOM_WIDTH, TILE_SIZE):
            add_wall(pygame.Rect(x, ROOM_OFFSET_Y, TILE_SIZE, WALL_THICKNESS))

        # Нижняя стена
        for x in range(ROOM_OFFSET_X, ROOM_OFFSET_X + ROOM_WIDTH, TILE_SIZE):
            add_wall(pygame.Rect(x, ROOM_OFFSET_Y + ROOM_HEIGHT - WALL_THICKNESS, TILE_SIZE, WALL_THICKNESS))

        # Левая стена
        for y in range(ROOM_OFFSET_Y, ROOM_OFFSET_Y + ROOM_HEIGHT, TILE_SIZE):
            add_wall(pygame.Rect(ROOM_OFFSET_X, y, WALL_THICKNESS, TILE_SIZE))

        # Правая стена
        for y in range(ROOM_OFFSET_Y, ROOM_OFFSET_Y + ROOM_HEIGHT, TILE_SIZE):
            add_wall(pygame.Rect(ROOM_OFFSET_X + ROOM_WIDTH - WALL_THICKNESS, y, WALL_THICKNESS, TILE_SIZE))

    def _generate_floor_texture(self):
        """Каменный пол плиткой со случайным (но кэшированным — не мерцает)
        оттенком каждой плитки и тёмной затиркой между ними. Общий тон
        (self._tint) делает пол одной комнаты цельным по палитре, но
        отличным от соседних комнат."""
        surface = pygame.Surface((ROOM_WIDTH, ROOM_HEIGHT))
        rng = self._rng
        floor_base = self._tinted(DARK_GRAY)
        grout = tuple(max(0, c - 20) for c in floor_base)

        for ty in range(0, ROOM_HEIGHT, TILE_SIZE):
            for tx in range(0, ROOM_WIDTH, TILE_SIZE):
                shade = rng.randint(-10, 10)
                color = tuple(max(0, min(255, c + shade)) for c in floor_base)
                pygame.draw.rect(surface, color, (tx, ty, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(surface, grout, (tx, ty, TILE_SIZE, TILE_SIZE), 1)

                # Редкие декоративные детали (трещины/мох) — разнообразят
                # пустой пол без влияния на геймплей
                if rng.random() < 0.04:
                    speck = tuple(max(0, c - 30) for c in color)
                    pygame.draw.line(surface, speck, (tx + 4, ty + 4), (tx + TILE_SIZE - 6, ty + TILE_SIZE - 8), 1)

        return surface
    
    def generate_enemies(self, count, avoid_pos=None, min_distance=150):
        """Генерация врагов в комнате, подальше от точки входа игрока (avoid_pos)"""
        self.enemies.clear()

        enemy_types = ["basic", "shooter", "tank", "fast", "brute"]
        enemy_weights = [35, 25, 10, 20, 10]

        for _ in range(count):
            # Случайная позиция в комнате (избегаем стен и точки входа игрока)
            margin = 50
            x, y = None, None
            for _attempt in range(30):
                candidate_x = random.randint(ROOM_OFFSET_X + margin, ROOM_OFFSET_X + ROOM_WIDTH - margin)
                candidate_y = random.randint(ROOM_OFFSET_Y + margin, ROOM_OFFSET_Y + ROOM_HEIGHT - margin)
                if avoid_pos is None:
                    x, y = candidate_x, candidate_y
                    break
                dx = candidate_x - avoid_pos[0]
                dy = candidate_y - avoid_pos[1]
                if (dx * dx + dy * dy) ** 0.5 >= min_distance:
                    x, y = candidate_x, candidate_y
                    break
            if x is None:
                # Не нашли позицию подальше за 30 попыток — берём последнюю как есть
                x, y = candidate_x, candidate_y

            # Случайный тип врага (танк/громила реже, крыса-разведчик почаще)
            enemy_type = random.choices(enemy_types, weights=enemy_weights, k=1)[0]

            enemy = Enemy(x, y, enemy_type)
            self.enemies.append(enemy)

    def generate_vases(self, count, avoid_pos=None, min_distance=100):
        """Расставляет разрушаемые вазы по комнате (аналог горшков Isaac),
        подальше друг от друга и от точки входа игрока"""
        self.vases.clear()
        margin = 60
        placed = []

        for _ in range(count):
            x, y = None, None
            for _attempt in range(30):
                candidate_x = random.randint(ROOM_OFFSET_X + margin, ROOM_OFFSET_X + ROOM_WIDTH - margin)
                candidate_y = random.randint(ROOM_OFFSET_Y + margin, ROOM_OFFSET_Y + ROOM_HEIGHT - margin)

                if avoid_pos is not None:
                    dx, dy = candidate_x - avoid_pos[0], candidate_y - avoid_pos[1]
                    if (dx * dx + dy * dy) ** 0.5 < min_distance:
                        continue

                too_close = any(
                    ((candidate_x - px) ** 2 + (candidate_y - py) ** 2) ** 0.5 < min_distance
                    for px, py in placed
                )
                if not too_close:
                    x, y = candidate_x, candidate_y
                    break

            if x is None:
                continue  # не нашли свободное место за 30 попыток — пропускаем эту вазу

            placed.append((x, y))
            self.vases.append(Vase(x, y))

    def generate_treasure(self):
        """Генерация сокровища в комнате"""
        center_x = ROOM_OFFSET_X + ROOM_WIDTH // 2
        center_y = ROOM_OFFSET_Y + ROOM_HEIGHT // 2
        self.items = [Item(center_x, center_y)]

    def generate_boss(self):
        """Генерация босса в комнате"""
        self.enemies.clear()
        center_x = ROOM_OFFSET_X + ROOM_WIDTH // 2
        center_y = ROOM_OFFSET_Y + ROOM_HEIGHT // 2
        boss = Enemy(center_x, center_y, "tank")
        boss.health *= 3
        boss.max_health = boss.health
        boss.damage += 1
        self.enemies.append(boss)

    def maybe_spawn_chest(self):
        """Вызывается при зачистке комнаты босса. Спавнит сундук рядом
        с люком (один раз за комнату) с одним из 10 уровней редкости
        приза внутри — см. chest.roll_tier()."""
        if self.chest_rolled:
            return
        self.chest_rolled = True

        cx = ROOM_OFFSET_X + ROOM_WIDTH // 2
        cy = ROOM_OFFSET_Y + ROOM_HEIGHT // 2
        self.chest = Chest(cx + 70, cy)

    def is_locked(self):
        """Комната заперта, если в ней изначально были враги и она ещё не зачищена"""
        return len(self.enemies) > 0 and not self.cleared

    def add_door(self, direction):
        """Добавление двери в указанном направлении"""
        if direction in self.doors:
            self.doors[direction] = True
    
    def remove_door(self, direction):
        """Удаление двери в указанном направлении"""
        if direction in self.doors:
            self.doors[direction] = False
    
    def get_torches(self):
        """Факелы (объекты Torch) — генерируются один раз лениво (после
        того, как двери уже расставлены дандженом) и кэшируются"""
        if self.torches is None:
            self.torches = self._generate_torches()
        return self.torches

    def all_torches_extinguished(self):
        torches = self.get_torches()
        return bool(torches) and all(t.extinguished for t in torches)

    def _generate_torches(self):
        """2-4 факела на случайных местах вдоль стен (не только по углам),
        с отступом от дверных проёмов и друг от друга"""
        rng = self._rng
        count = rng.randint(2, 4)
        positions = []
        door_gap = 45

        for _attempt in range(50):
            if len(positions) >= count:
                break

            side = rng.choice(['up', 'down', 'left', 'right'])
            if side in ('up', 'down'):
                x = rng.randint(ROOM_OFFSET_X + TORCH_MARGIN, ROOM_OFFSET_X + ROOM_WIDTH - TORCH_MARGIN)
                y = ROOM_OFFSET_Y + TORCH_MARGIN if side == 'up' else ROOM_OFFSET_Y + ROOM_HEIGHT - TORCH_MARGIN
                door_center = ROOM_OFFSET_X + ROOM_WIDTH // 2
                coord_on_wall = x
            else:
                y = rng.randint(ROOM_OFFSET_Y + TORCH_MARGIN, ROOM_OFFSET_Y + ROOM_HEIGHT - TORCH_MARGIN)
                x = ROOM_OFFSET_X + TORCH_MARGIN if side == 'left' else ROOM_OFFSET_X + ROOM_WIDTH - TORCH_MARGIN
                door_center = ROOM_OFFSET_Y + ROOM_HEIGHT // 2
                coord_on_wall = y

            if self.doors[side] and abs(coord_on_wall - door_center) < door_gap:
                continue
            if any(((x - px) ** 2 + (y - py) ** 2) ** 0.5 < 80 for px, py in positions):
                continue

            positions.append((x, y))

        return [Torch(x, y) for x, y in positions]

    def _draw_torch(self, screen, torch, time, phase=0.0):
        """Тёплое аддитивное свечение факела — компактное и мягкое +
        скоба на стене с мерцающим двухслойным пламенем. Тускнеет по
        мере урона (torch.health), потушенный факел — просто холодная
        скоба без пламени/свечения."""
        pos = torch.pos

        if torch.extinguished:
            pygame.draw.rect(screen, (50, 45, 40), (pos[0] - 2, pos[1] - 2, 4, 12))
            return

        dim = torch.health / TORCH_MAX_HEALTH  # 1.0 цел, ближе к 0 перед тем как потухнет
        flicker = math.sin(time * 9 + phase) * 2 + math.sin(time * 23 + phase) * 1

        radius = int((22 + flicker) + 8 * dim)
        glow_alpha = max(4, int(16 * dim))
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -6):
            pygame.draw.circle(glow, (255, 140, 40, glow_alpha), (radius, radius), r)
        screen.blit(glow, (pos[0] - radius, pos[1] - radius), special_flags=pygame.BLEND_RGBA_ADD)

        # Скоба-держатель на стене
        pygame.draw.rect(screen, (60, 40, 20), (pos[0] - 2, pos[1] - 2, 4, 12))

        # Пламя: внешний слой (оранжевый) + внутренний более яркий (почти белый),
        # высота и яркость падают вместе со здоровьем факела
        flame_h = (6 + flicker) * dim + 2
        outer = tuple(int(c * (0.4 + 0.6 * dim)) for c in (255, 190, 70))
        inner = tuple(int(c * (0.4 + 0.6 * dim)) for c in (255, 245, 190))
        pygame.draw.polygon(screen, outer, [
            (pos[0], pos[1] - 6 - flame_h),
            (pos[0] - 4, pos[1] - 3),
            (pos[0] + 4, pos[1] - 3),
        ])
        pygame.draw.polygon(screen, inner, [
            (pos[0], pos[1] - 4 - flame_h * 0.55),
            (pos[0] - 2, pos[1] - 3),
            (pos[0] + 2, pos[1] - 3),
        ])

    def draw(self, screen, time=0.0):
        """Отрисовка комнаты"""
        room_rect = pygame.Rect(ROOM_OFFSET_X, ROOM_OFFSET_Y, ROOM_WIDTH, ROOM_HEIGHT)

        # Каменный пол плиткой (кэшированная текстура, не пересчитывается каждый кадр)
        screen.blit(self.floor_texture, (ROOM_OFFSET_X, ROOM_OFFSET_Y))

        # Кирпичная кладка стен: у каждого сегмента свой оттенок + тёмная
        # окантовка снизу-справа для лёгкого объёма
        for wall, color in zip(self.walls, self.wall_colors):
            pygame.draw.rect(screen, color, wall)
            edge_color = tuple(max(0, c - 35) for c in color)
            pygame.draw.rect(screen, edge_color, wall, 1)

        # Колонны — неразрушимые препятствия (если есть в этой комнате)
        for pillar in self.pillars:
            pygame.draw.rect(screen, self._tinted(GRAY), pillar)
            pygame.draw.rect(screen, tuple(max(0, c - 40) for c in self._tinted(GRAY)), pillar, 2)

        # Свечение факелов на случайных местах вдоль стен (тёплый
        # аддитивный градиент + мерцание)
        for i, torch in enumerate(self.get_torches()):
            self._draw_torch(screen, torch, time, phase=i * 1.7)

        # Отрисовка дверей (пропуски в стенах). Если в комнате есть живые
        # враги — двери рисуются запертыми (сплошная стена + красная рамка),
        # проход через них физически блокируется в Game._check_room_boundaries
        door_width = 60
        door_height = 20
        locked = self.is_locked()

        door_rects = {
            'up': pygame.Rect(
                ROOM_OFFSET_X + ROOM_WIDTH // 2 - door_width // 2,
                ROOM_OFFSET_Y,
                door_width, door_height
            ),
            'down': pygame.Rect(
                ROOM_OFFSET_X + ROOM_WIDTH // 2 - door_width // 2,
                ROOM_OFFSET_Y + ROOM_HEIGHT - door_height,
                door_width, door_height
            ),
            'left': pygame.Rect(
                ROOM_OFFSET_X,
                ROOM_OFFSET_Y + ROOM_HEIGHT // 2 - door_width // 2,
                door_height, door_width
            ),
            'right': pygame.Rect(
                ROOM_OFFSET_X + ROOM_WIDTH - door_height,
                ROOM_OFFSET_Y + ROOM_HEIGHT // 2 - door_width // 2,
                door_height, door_width
            )
        }

        for direction, door_rect in door_rects.items():
            if not self.doors[direction]:
                continue

            if locked:
                pygame.draw.rect(screen, BROWN, door_rect)
                pygame.draw.rect(screen, RED, door_rect, 2)
            else:
                pygame.draw.rect(screen, DARK_GRAY, door_rect)
        
        # Отрисовка индикатора очистки комнаты
        if self.cleared:
            # Зеленая рамка, если комната очищена
            pygame.draw.rect(screen, GREEN, room_rect, 3)
    
    def get_spawn_position(self):
        """Получение безопасной позиции для спавна игрока"""
        # Центр комнаты
        return (ROOM_OFFSET_X + ROOM_WIDTH // 2, ROOM_OFFSET_Y + ROOM_HEIGHT // 2)
    
    def is_position_valid(self, x, y, size):
        """Проверка, свободна ли позиция от стен"""
        test_rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        
        for wall in self.walls:
            if test_rect.colliderect(wall):
                return False
        
        return True