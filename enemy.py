import pygame
import random
from constants import *
from tear import EnemyTear

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="basic"):
        super().__init__()
        
        self.enemy_type = enemy_type
        
        # Создание поверхности врага
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Характеристики в зависимости от типа
        if enemy_type == "basic":
            self.image.fill(RED)
            self.health = ENEMY_HEALTH
            self.max_health = ENEMY_HEALTH
            self.speed = ENEMY_SPEED
            self.damage = ENEMY_DAMAGE
            self.ai_type = "chase"
        elif enemy_type == "shooter":
            self.image.fill(BLUE)
            self.health = ENEMY_HEALTH - 1
            self.max_health = ENEMY_HEALTH - 1
            self.speed = ENEMY_SPEED * 0.7
            self.damage = ENEMY_DAMAGE
            self.ai_type = "shoot"
            self.shoot_timer = 0
            self.shoot_cooldown = 2.0
        elif enemy_type == "tank":
            self.image.fill(GRAY)
            self.health = ENEMY_HEALTH * 2
            self.max_health = ENEMY_HEALTH * 2
            self.speed = ENEMY_SPEED * 0.5
            self.damage = ENEMY_DAMAGE + 1
            self.ai_type = "chase"
        else:
            self.image.fill(RED)
            self.health = ENEMY_HEALTH
            self.max_health = ENEMY_HEALTH
            self.speed = ENEMY_SPEED
            self.damage = ENEMY_DAMAGE
            self.ai_type = "chase"
        
        # Движение
        self.velocity = pygame.math.Vector2(0, 0)

        # Снаряды, выпущенные в этот кадр (собираются игрой через get_new_tears)
        self.new_tears = []

    def update(self, dt, player_pos):
        if self.ai_type == "chase":
            self._ai_chase(dt, player_pos)
        elif self.ai_type == "shoot":
            self._ai_shoot(dt, player_pos)
        
        # Ограничение движения границами комнаты
        self._clamp_to_room()
        
        # Обновление цвета в зависимости от здоровья
        self._update_color()
    
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
    
    def _update_color(self):
        # Изменение цвета в зависимости от здоровья: на полном ХП — чистый
        # базовый цвет типа врага, по мере урона высветляется к белому
        health_ratio = self.health / self.max_health
        damage_ratio = 1 - health_ratio

        if self.enemy_type == "basic":
            component = int(255 * damage_ratio)
            self.image.fill((255, component, component))
        elif self.enemy_type == "shooter":
            component = int(255 * damage_ratio)
            self.image.fill((component, component, 255))
        elif self.enemy_type == "tank":
            component = int(128 + 127 * damage_ratio)
            self.image.fill((component, component, component))
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0
    
    def is_dead(self):
        return self.health <= 0