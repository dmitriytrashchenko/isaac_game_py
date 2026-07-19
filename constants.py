# Размеры экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BROWN = (139, 69, 19)
GOLD = (212, 175, 55)
DARK_GOLD = (120, 90, 0)
FIRE_ORANGE = (255, 140, 0)

# Размеры комнаты
ROOM_WIDTH = 640
ROOM_HEIGHT = 480
ROOM_OFFSET_X = (SCREEN_WIDTH - ROOM_WIDTH) // 2
ROOM_OFFSET_Y = (SCREEN_HEIGHT - ROOM_HEIGHT) // 2

# Размеры тайлов
TILE_SIZE = 32
WALL_THICKNESS = 16

# Отступ от стены, на который ставится игрок при входе в новую комнату
# через дверь (используется и для защитной зоны от спавна врагов рядом с ним)
ROOM_ENTRY_MARGIN = 80

# Игрок
PLAYER_SIZE = 24
PLAYER_SPEED = 200
PLAYER_MAX_HEALTH = 6
PLAYER_TEAR_SPEED = 300
PLAYER_TEAR_DAMAGE = 1
PLAYER_TEAR_RATE = 0.3  # секунд между выстрелами

# Враги
ENEMY_SIZE = 20
ENEMY_SPEED = 80
ENEMY_HEALTH = 2
ENEMY_DAMAGE = 1
ENEMY_TEAR_SPEED = 250

# Слёзы (пули)
TEAR_SIZE = 8
TEAR_LIFETIME = 2.0  # секунд

# Предметы
ITEM_SIZE = 16

# Направления
DIRECTIONS = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0)
}

# Типы комнат
ROOM_TYPES = {
    'NORMAL': 0,
    'TREASURE': 1,
    'BOSS': 2,
    'SECRET': 3
}