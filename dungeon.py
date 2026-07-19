import random
from constants import *
from room import Room

class Dungeon:
    def __init__(self, size=5):
        self.size = size  # Размер сетки подземелья (5x5)
        self.rooms = {}   # Словарь комнат {(x, y): Room}
        self.current_pos = (size // 2, size // 2)  # Стартовая позиция в центре
        self.visited_rooms = set()
        
        # Генерация подземелья
        self._generate_dungeon()
        
        # Установка текущей комнаты
        self.current_room = self.rooms[self.current_pos]
        self.current_room.visited = True
        self.visited_rooms.add(self.current_pos)
    
    def _generate_dungeon(self):
        """Генерация подземелья с комнатами и связями"""
        # Создаем стартовую комнату в центре
        start_pos = (self.size // 2, self.size // 2)
        self.rooms[start_pos] = Room(ROOM_TYPES['NORMAL'])
        
        # Генерируем основной путь
        self._generate_main_path(start_pos)
        
        # Добавляем дополнительные комнаты
        self._add_side_rooms()
        
        # Добавляем специальные комнаты
        self._add_special_rooms()
        
        # Устанавливаем двери между комнатами
        self._setup_doors()
    
    def _generate_main_path(self, start_pos):
        """Генерация основного пути через подземелье"""
        current_pos = start_pos
        path_length = random.randint(6, 10)
        
        for _ in range(path_length):
            # Выбираем случайное направление
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                new_pos = (current_pos[0] + dx, current_pos[1] + dy)
                
                # Проверяем границы
                if (0 <= new_pos[0] < self.size and 
                    0 <= new_pos[1] < self.size and 
                    new_pos not in self.rooms):
                    
                    # Создаем новую комнату
                    self.rooms[new_pos] = Room(ROOM_TYPES['NORMAL'])
                    current_pos = new_pos
                    break
    
    def _add_side_rooms(self):
        """Добавление боковых комнат"""
        existing_positions = list(self.rooms.keys())
        
        for pos in existing_positions:
            # Шанс добавить боковую комнату
            if random.random() < 0.4:
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                direction = random.choice(directions)
                
                new_pos = (pos[0] + direction[0], pos[1] + direction[1])
                
                if (0 <= new_pos[0] < self.size and 
                    0 <= new_pos[1] < self.size and 
                    new_pos not in self.rooms):
                    
                    self.rooms[new_pos] = Room(ROOM_TYPES['NORMAL'])
    
    def _add_special_rooms(self):
        """Добавление специальных комнат (сокровищница, босс)"""
        positions = list(self.rooms.keys())
        
        # Добавляем 1-2 комнаты сокровищ
        treasure_count = random.randint(1, 2)
        for _ in range(treasure_count):
            if positions:
                # Выбираем тупиковые комнаты для сокровищ
                dead_ends = self._find_dead_ends()
                if dead_ends:
                    pos = random.choice(dead_ends)
                    self.rooms[pos].room_type = ROOM_TYPES['TREASURE']
        
        # Добавляем комнату босса в самом дальнем углу
        boss_pos = self._find_farthest_room()
        if boss_pos:
            self.rooms[boss_pos].room_type = ROOM_TYPES['BOSS']
    
    def _find_dead_ends(self):
        """Поиск тупиковых комнат (с одним соседом)"""
        dead_ends = []
        
        for pos in self.rooms.keys():
            neighbor_count = self._count_neighbors(pos)
            if neighbor_count == 1:
                dead_ends.append(pos)
        
        return dead_ends
    
    def _find_farthest_room(self):
        """Поиск самой дальней комнаты от стартовой"""
        start_pos = (self.size // 2, self.size // 2)
        max_distance = 0
        farthest_pos = None
        
        for pos in self.rooms.keys():
            distance = abs(pos[0] - start_pos[0]) + abs(pos[1] - start_pos[1])
            if distance > max_distance:
                max_distance = distance
                farthest_pos = pos
        
        return farthest_pos
    
    def _count_neighbors(self, pos):
        """Подсчет соседних комнат"""
        count = 0
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            neighbor_pos = (pos[0] + dx, pos[1] + dy)
            if neighbor_pos in self.rooms:
                count += 1
        
        return count
    
    def _setup_doors(self):
        """Установка дверей между смежными комнатами"""
        for pos, room in self.rooms.items():
            x, y = pos
            
            # Проверяем каждое направление
            if (x, y - 1) in self.rooms:  # Вверх
                room.add_door('up')
            if (x, y + 1) in self.rooms:  # Вниз
                room.add_door('down')
            if (x - 1, y) in self.rooms:  # Влево
                room.add_door('left')
            if (x + 1, y) in self.rooms:  # Вправо
                room.add_door('right')
    
    def can_move_to(self, direction):
        """Проверка возможности перехода в указанном направлении"""
        if not self.current_room.cleared and len(self.current_room.enemies) > 0:
            return False  # Нельзя покинуть комнату с живыми врагами
        
        return self.current_room.doors.get(direction, False)
    
    def move_to_room(self, direction):
        """Переход в комнату в указанном направлении"""
        if not self.can_move_to(direction):
            return False
        
        # Определяем новую позицию
        x, y = self.current_pos
        
        if direction == 'up':
            new_pos = (x, y - 1)
        elif direction == 'down':
            new_pos = (x, y + 1)
        elif direction == 'left':
            new_pos = (x - 1, y)
        elif direction == 'right':
            new_pos = (x + 1, y)
        else:
            return False
        
        # Проверяем существование комнаты
        if new_pos not in self.rooms:
            return False
        
        # Переходим в новую комнату
        self.current_pos = new_pos
        self.current_room = self.rooms[new_pos]
        
        # Отмечаем комнату как посещенную
        if not self.current_room.visited:
            self.current_room.visited = True
            self.visited_rooms.add(new_pos)
            
            # Генерируем врагов для новой комнаты, подальше от двери, через
            # которую войдёт игрок, чтобы не спавнить их у него под ногами
            if self.current_room.room_type == ROOM_TYPES['NORMAL']:
                enemy_count = random.randint(2, 5)
                entry_pos = self._get_entry_position(direction)
                self.current_room.generate_enemies(enemy_count, avoid_pos=entry_pos, min_distance=150)
            elif self.current_room.room_type == ROOM_TYPES['TREASURE']:
                # В комнате сокровищ нет врагов, но есть предмет
                self.current_room.generate_treasure()
            elif self.current_room.room_type == ROOM_TYPES['BOSS']:
                # В комнате босса один сильный враг
                self.current_room.generate_boss()

        return True

    def _get_entry_position(self, direction):
        """Точка, где игрок появится в новой комнате после перехода в direction"""
        cx = ROOM_OFFSET_X + ROOM_WIDTH // 2
        cy = ROOM_OFFSET_Y + ROOM_HEIGHT // 2

        if direction == 'up':
            return (cx, ROOM_OFFSET_Y + ROOM_HEIGHT - WALL_THICKNESS - ROOM_ENTRY_MARGIN)
        elif direction == 'down':
            return (cx, ROOM_OFFSET_Y + WALL_THICKNESS + ROOM_ENTRY_MARGIN)
        elif direction == 'left':
            return (ROOM_OFFSET_X + ROOM_WIDTH - WALL_THICKNESS - ROOM_ENTRY_MARGIN, cy)
        elif direction == 'right':
            return (ROOM_OFFSET_X + WALL_THICKNESS + ROOM_ENTRY_MARGIN, cy)

        return (cx, cy)
    
    def get_minimap_data(self):
        """Получение данных для мини-карты"""
        return {
            'rooms': {pos: room.room_type for pos, room in self.rooms.items()},
            'visited': self.visited_rooms,
            'current': self.current_pos,
            'size': self.size
        }