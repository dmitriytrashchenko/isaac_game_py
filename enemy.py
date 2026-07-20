import pygame
import random
from constants import *
from tear import EnemyTear

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="basic"):
        super().__init__()
        
        self.enemy_type = enemy_type

        # Создание поверхности врага
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Характеристики в зависимости от типа
        if enemy_type == "basic":
            self.health = ENEMY_HEALTH
            self.max_health = ENEMY_HEALTH
            self.speed = ENEMY_SPEED
            self.damage = ENEMY_DAMAGE
            self.ai_type = "chase"
        elif enemy_type == "shooter":
            self.health = ENEMY_HEALTH - 1
            self.max_health = ENEMY_HEALTH - 1
            self.speed = ENEMY_SPEED * 0.7
            self.damage = ENEMY_DAMAGE
            self.ai_type = "shoot"
            self.shoot_timer = 0
            self.shoot_cooldown = 2.0
        elif enemy_type == "tank":
            self.health = ENEMY_HEALTH * 2
            self.max_health = ENEMY_HEALTH * 2
            self.speed = ENEMY_SPEED * 0.5
            self.damage = ENEMY_DAMAGE + 1
            self.ai_type = "chase"
        elif enemy_type == "fast":
            # Крыса-разведчик: очень быстрая, но хрупкая и слабая
            self.health = 1
            self.max_health = 1
            self.speed = ENEMY_SPEED * 1.8
            self.damage = ENEMY_DAMAGE
            self.ai_type = "chase"
        elif enemy_type == "brute":
            # Тяжёлый громила: медленный, но бьёт очень больно вплотную
            self.health = ENEMY_HEALTH + 1
            self.max_health = ENEMY_HEALTH + 1
            self.speed = ENEMY_SPEED * 0.4
            self.damage = ENEMY_DAMAGE * 2
            self.ai_type = "chase"
        else:
            self.health = ENEMY_HEALTH
            self.max_health = ENEMY_HEALTH
            self.speed = ENEMY_SPEED
            self.damage = ENEMY_DAMAGE
            self.ai_type = "chase"

        # Движение
        self.velocity = pygame.math.Vector2(0, 0)

        # Снаряды, выпущенные в этот кадр (собираются игрой через get_new_tears)
        self.new_tears = []

        self._render()

    def update(self, dt, player_pos):
        if self.ai_type == "chase":
            self._ai_chase(dt, player_pos)
        elif self.ai_type == "shoot":
            self._ai_shoot(dt, player_pos)
        
        # Ограничение движения границами комнаты
        self._clamp_to_room()
        
        # Перерисовка силуэта (цвет зависит от текущего здоровья)
        self._render()
    
    def _ai_chase(self, dt, player_pos):
        # Простое преследование игрока
        direction = pygame.math.Vector2(
            player_pos[0] - self.rect.centerx,
            player_pos[1] - self.rect.centery
        )
        
        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * self.speed
        else:
            self.velocity = pygame.math.Vector2(0, 0)
        
        # Применение движения
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
    
    def _ai_shoot(self, dt, player_pos):
        # ИИ стрелка: останавливается и стреляет
        distance_to_player = pygame.math.Vector2(
            player_pos[0] - self.rect.centerx,
            player_pos[1] - self.rect.centery
        ).length()
        
        if distance_to_player > 150:  # Приближается к игроку
            direction = pygame.math.Vector2(
                player_pos[0] - self.rect.centerx,
                player_pos[1] - self.rect.centery
            ).normalize()
            self.velocity = direction * self.speed
        elif distance_to_player < 100:  # Отдаляется от игрока
            direction = pygame.math.Vector2(
                self.rect.centerx - player_pos[0],
                self.rect.centery - player_pos[1]
            ).normalize()
            self.velocity = direction * self.speed * 0.5
        else:  # Останавливается и стреляет
            self.velocity = pygame.math.Vector2(0, 0)
        
        # Обновление таймера стрельбы
        if hasattr(self, 'shoot_timer'):
            self.shoot_timer += dt
            if self.shoot_timer >= self.shoot_cooldown:
                self._shoot_at(player_pos)
                self.shoot_timer = 0

        # Применение движения
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt

    def _shoot_at(self, player_pos):
        direction = pygame.math.Vector2(
            player_pos[0] - self.rect.centerx,
            player_pos[1] - self.rect.centery
        )
        if direction.length() == 0:
            return
        direction = direction.normalize()

        tear = EnemyTear(self.rect.centerx, self.rect.centery, direction, ENEMY_TEAR_SPEED, self.damage)
        self.new_tears.append(tear)

    def get_new_tears(self):
        # Возвращает и очищает список новых снарядов
        tears = self.new_tears.copy()
        self.new_tears.clear()
        return tears

    def _clamp_to_room(self):
        # Ограничение движения врага границами комнаты
        room_left = ROOM_OFFSET_X + WALL_THICKNESS
        room_right = ROOM_OFFSET_X + ROOM_WIDTH - WALL_THICKNESS - ENEMY_SIZE
        room_top = ROOM_OFFSET_Y + WALL_THICKNESS
        room_bottom = ROOM_OFFSET_Y + ROOM_HEIGHT - WALL_THICKNESS - ENEMY_SIZE
        
        if self.rect.left < room_left:
            self.rect.left = room_left
        elif self.rect.right > room_right:
            self.rect.right = room_right
        
        if self.rect.top < room_top:
            self.rect.top = room_top
        elif self.rect.bottom > room_bottom:
            self.rect.bottom = room_bottom
    
    def _current_color(self):
        # Цвет в зависимости от здоровья: на полном ХП — чистый базовый
        # цвет типа врага, по мере урона высветляется к белому
        health_ratio = self.health / self.max_health if self.max_health else 0
        damage_ratio = 1 - health_ratio

        if self.enemy_type == "basic":
            component = int(255 * damage_ratio)
            return (255, component, component)
        elif self.enemy_type == "shooter":
            component = int(255 * damage_ratio)
            return (component, component, 255)
        elif self.enemy_type == "tank":
            component = int(128 + 127 * damage_ratio)
            return (component, component, component)
        elif self.enemy_type == "fast":
            component = int(255 * damage_ratio)
            return (component, 255, component)
        elif self.enemy_type == "brute":
            component = int(255 * damage_ratio)
            return (140 + component // 3, 60, 20)
        return WHITE

    def _render(self):
        """Простой силуэт вместо плоской заливки — каждый тип врага
        отрисован набором примитивов, узнаваемый по форме, не только по цвету"""
        color = self._current_color()
        surface = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE), pygame.SRCALPHA)
        w = ENEMY_SIZE

        if self.enemy_type == "basic":
            # Скелет-воин: череп + рёбра + руки/ноги-линии
            pygame.draw.circle(surface, color, (w // 2, 4), 4)
            pygame.draw.rect(surface, color, (w // 2 - 3, 8, 6, 7))
            for i in range(3):
                y = 9 + i * 2
                pygame.draw.line(surface, color, (w // 2 - 4, y), (w // 2 + 4, y), 1)
            pygame.draw.line(surface, color, (w // 2 - 3, 10), (w // 2 - 6, 13), 1)
            pygame.draw.line(surface, color, (w // 2 + 3, 10), (w // 2 + 6, 13), 1)
            pygame.draw.line(surface, color, (w // 2 - 2, 15), (w // 2 - 3, 19), 1)
            pygame.draw.line(surface, color, (w // 2 + 2, 15), (w // 2 + 3, 19), 1)
        elif self.enemy_type == "shooter":
            # Гоблин-лучник: голова с ушами + туловище-плащ треугольником
            pygame.draw.circle(surface, color, (w // 2, 5), 4)
            pygame.draw.line(surface, color, (w // 2 - 4, 3), (w // 2 - 7, 1), 1)
            pygame.draw.line(surface, color, (w // 2 + 4, 3), (w // 2 + 7, 1), 1)
            pygame.draw.polygon(surface, color, [
                (w // 2, 8), (w // 2 - 5, 19), (w // 2 + 5, 19)
            ])
        elif self.enemy_type == "tank":
            # Каменный голем: массивный блок с трещинами и светящимися глазами
            pygame.draw.rect(surface, color, (1, 2, w - 2, w - 3), border_radius=3)
            dark = tuple(max(0, c - 60) for c in color)
            pygame.draw.line(surface, dark, (5, 5), (9, 11), 1)
            pygame.draw.line(surface, dark, (w - 6, 4), (w - 9, 10), 1)
            pygame.draw.circle(surface, (255, 60, 60), (w // 2 - 4, 8), 1)
            pygame.draw.circle(surface, (255, 60, 60), (w // 2 + 4, 8), 1)
        elif self.enemy_type == "fast":
            # Крыса-разведчик: приземистое тело + острые уши + хвост
            pygame.draw.ellipse(surface, color, (2, 8, w - 4, 10))
            pygame.draw.polygon(surface, color, [(w // 2 - 5, 8), (w // 2 - 2, 3), (w // 2 - 1, 9)])
            pygame.draw.polygon(surface, color, [(w // 2 + 5, 8), (w // 2 + 2, 3), (w // 2 + 1, 9)])
            pygame.draw.line(surface, color, (w - 3, 14), (w, 18), 1)
            pygame.draw.circle(surface, (255, 0, 0), (w // 2 - 2, 11), 1)
            pygame.draw.circle(surface, (255, 0, 0), (w // 2 + 2, 11), 1)
        elif self.enemy_type == "brute":
            # Громила: широкие плечи, маленькая голова, шипы на кулаках
            pygame.draw.circle(surface, color, (w // 2, 4), 3)
            pygame.draw.polygon(surface, color, [
                (2, w - 3), (w - 2, w - 3), (w - 5, 8), (5, 8)
            ])
            for dx in (-1, 0, 1):
                pygame.draw.line(surface, (60, 30, 10),
                                  (w // 2 + dx * 5, w - 4), (w // 2 + dx * 5, w - 1), 1)
        else:
            surface.fill(color)

        self.image = surface

    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0
    
    def is_dead(self):
        return self.health <= 0

    def apply_item_effect(self, item_type):
        """Враг наступил на предмет и "воровски" забрал бафф себе (шанс
        на это — в Game.update(), тут только применение эффекта)"""
        if item_type == "health":
            self.health = min(self.health + 1, self.max_health)
        elif item_type == "damage_up":
            self.damage += 0.5
        elif item_type == "speed_up":
            self.speed += 20
        elif item_type == "tears_up" and hasattr(self, "shoot_cooldown"):
            self.shoot_cooldown = max(0.3, self.shoot_cooldown - 0.2)
        elif item_type == "max_health":
            self.max_health += 2
            self.health += 2