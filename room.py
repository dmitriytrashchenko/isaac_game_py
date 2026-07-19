import pygame
import random
from constants import *
from enemy import Enemy
from item import Item

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
        
        # Генерация базовых стен комнаты
        self._generate_walls()
    
    def _generate_walls(self):
        # Генерация стен по периметру комнаты
        # Верхняя стена
        for x in range(ROOM_OFFSET_X, ROOM_OFFSET_X + ROOM_WIDTH, TILE_SIZE):
            wall_rect = pygame.Rect(x, ROOM_OFFSET_Y, TILE_SIZE, WALL_THICKNESS)
            self.walls.append(wall_rect)
        
        # Нижняя стена
        for x in range(ROOM_OFFSET_X, ROOM_OFFSET_X + ROOM_WIDTH, TILE_SIZE):
            wall_rect = pygame.Rect(x, ROOM_OFFSET_Y + ROOM_HEIGHT - WALL_THICKNESS, TILE_SIZE, WALL_THICKNESS)
            self.walls.append(wall_rect)
        
        # Левая стена
        for y in range(ROOM_OFFSET_Y, ROOM_OFFSET_Y + ROOM_HEIGHT, TILE_SIZE):
            wall_rect = pygame.Rect(ROOM_OFFSET_X, y, WALL_THICKNESS, TILE_SIZE)
            self.walls.append(wall_rect)
        
        # Правая стена
        for y in range(ROOM_OFFSET_Y, ROOM_OFFSET_Y + ROOM_HEIGHT, TILE_SIZE):
            wall_rect = pygame.Rect(ROOM_OFFSET_X + ROOM_WIDTH - WALL_THICKNESS, y, WALL_THICKNESS, TILE_SIZE)
            self.walls.append(wall_rect)
    
    def generate_enemies(self, count):
        """Генерация врагов в комнате"""
        self.enemies.clear()
        
        enemy_types = ["basic", "shooter", "tank"]
        
        for _ in range(count):
            # Случайная позиция в комнате (избегаем стен)
            margin = 50
            x = random.randint(ROOM_OFFSET_X + margin, ROOM_OFFSET_X + ROOM_WIDTH - margin)
            y = random.randint(ROOM_OFFSET_Y + margin, ROOM_OFFSET_Y + ROOM_HEIGHT - margin)
            
            # Случайный тип врага
            enemy_type = random.choice(enemy_types)
            
            # Уменьшаем шанс появления танка
            if enemy_type == "tank" and random.random() > 0.3:
                enemy_type = "basic"
            
            enemy = Enemy(x, y, enemy_type)
            self.enemies.append(enemy)
    
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

    def add_door(self, direction):
        """Добавление двери в указанном направлении"""
        if direction in self.doors:
            self.doors[direction] = True
    
    def remove_door(self, direction):
        """Удаление двери в указанном направлении"""
        if direction in self.doors:
            self.doors[direction] = False
    
    def draw(self, screen):
        """Отрисовка комнаты"""
        # Заливка фона комнаты
        room_rect = pygame.Rect(ROOM_OFFSET_X, ROOM_OFFSET_Y, ROOM_WIDTH, ROOM_HEIGHT)
        pygame.draw.rect(screen, DARK_GRAY, room_rect)
        
        # Отрисовка стен
        for wall in self.walls:
            pygame.draw.rect(screen, BROWN, wall)
        
        # Отрисовка дверей (пропуски в стенах)
        door_width = 60
        door_height = 20
        
        if self.doors['up']:
            door_rect = pygame.Rect(
                ROOM_OFFSET_X + ROOM_WIDTH // 2 - door_width // 2,
                ROOM_OFFSET_Y,
                door_width,
                door_height
            )
            pygame.draw.rect(screen, DARK_GRAY, door_rect)
            
        if self.doors['down']:
            door_rect = pygame.Rect(
                ROOM_OFFSET_X + ROOM_WIDTH // 2 - door_width // 2,
                ROOM_OFFSET_Y + ROOM_HEIGHT - door_height,
                door_width,
                door_height
            )
            pygame.draw.rect(screen, DARK_GRAY, door_rect)
            
        if self.doors['left']:
            door_rect = pygame.Rect(
                ROOM_OFFSET_X,
                ROOM_OFFSET_Y + ROOM_HEIGHT // 2 - door_width // 2,
                door_height,
                door_width
            )
            pygame.draw.rect(screen, DARK_GRAY, door_rect)
            
        if self.doors['right']:
            door_rect = pygame.Rect(
                ROOM_OFFSET_X + ROOM_WIDTH - door_height,
                ROOM_OFFSET_Y + ROOM_HEIGHT // 2 - door_width // 2,
                door_height,
                door_width
            )
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