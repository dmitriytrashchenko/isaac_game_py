import pygame
import math
from constants import *
from tear import Tear

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # Создание поверхности игрока
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Характеристики игрока
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.speed = PLAYER_SPEED
        self.tear_damage = PLAYER_TEAR_DAMAGE
        self.tear_speed = PLAYER_TEAR_SPEED
        self.tear_rate = PLAYER_TEAR_RATE
        
        # Движение
        self.velocity = pygame.math.Vector2(0, 0)
        
        # Стрельба
        self.last_shot = 0
        self.new_tears = []
        
        # Урон
        self.invulnerable_time = 0
        self.invulnerable_duration = 1.0  # секунды неуязвимости после получения урона
        
        # Клавиши движения
        self.keys_pressed = {
            pygame.K_w: False,
            pygame.K_a: False,
            pygame.K_s: False,
            pygame.K_d: False,
            pygame.K_UP: False,
            pygame.K_LEFT: False,
            pygame.K_DOWN: False,
            pygame.K_RIGHT: False
        }
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.keys_pressed:
                self.keys_pressed[event.key] = True
        elif event.type == pygame.KEYUP:
            if event.key in self.keys_pressed:
                self.keys_pressed[event.key] = False
    
    def update(self, dt):
        # Обновление времени неуязвимости
        if self.invulnerable_time > 0:
            self.invulnerable_time -= dt
        
        # Обновление времени последнего выстрела
        self.last_shot += dt
        
        # Обработка движения
        self._handle_movement(dt)
        
        # Обработка стрельбы
        self._handle_shooting(dt)
        
        # Обновление визуала при получении урона
        if self.invulnerable_time > 0:
            # Мигание при неуязвимости
            if int(self.invulnerable_time * 10) % 2:
                self.image.fill(RED)
            else:
                self.image.fill(YELLOW)
        else:
            self.image.fill(YELLOW)
    
    def _handle_movement(self, dt):
        # Сбрасываем скорость
        self.velocity.x = 0
        self.velocity.y = 0
        
        # Проверяем нажатые клавиши движения
        if self.keys_pressed[pygame.K_w] or self.keys_pressed[pygame.K_UP]:
            self.velocity.y = -self.speed
        if self.keys_pressed[pygame.K_s] or self.keys_pressed[pygame.K_DOWN]:
            self.velocity.y = self.speed
        if self.keys_pressed[pygame.K_a] or self.keys_pressed[pygame.K_LEFT]:
            self.velocity.x = -self.speed
        if self.keys_pressed[pygame.K_d] or self.keys_pressed[pygame.K_RIGHT]:
            self.velocity.x = self.speed
        
        # Нормализация диагонального движения
        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize() * self.speed
        
        # Применение движения
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
    
    def _handle_shooting(self, dt):
        # Проверяем стрельбу стрелками
        shoot_direction = None
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            shoot_direction = DIRECTIONS['UP']
        elif keys[pygame.K_DOWN]:
            shoot_direction = DIRECTIONS['DOWN']
        elif keys[pygame.K_LEFT]:
            shoot_direction = DIRECTIONS['LEFT']
        elif keys[pygame.K_RIGHT]:
            shoot_direction = DIRECTIONS['RIGHT']
        
        # Стрельба
        if shoot_direction and self.last_shot >= self.tear_rate:
            self._shoot(shoot_direction)
            self.last_shot = 0
    
    def _shoot(self, direction):
        # Создание слезы
        tear_x = self.rect.centerx + direction[0] * (PLAYER_SIZE // 2 + TEAR_SIZE // 2)
        tear_y = self.rect.centery + direction[1] * (PLAYER_SIZE // 2 + TEAR_SIZE // 2)
        
        tear = Tear(tear_x, tear_y, direction, self.tear_speed, self.tear_damage)
        self.new_tears.append(tear)
    
    def get_new_tears(self):
        # Возвращает и очищает список новых слёз
        tears = self.new_tears.copy()
        self.new_tears.clear()
        return tears
    
    def take_damage(self, damage):
        if self.invulnerable_time <= 0:
            self.health -= damage
            self.invulnerable_time = self.invulnerable_duration
            
            if self.health < 0:
                self.health = 0
    
    def can_take_damage(self):
        return self.invulnerable_time <= 0
    
    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)
    
    def increase_max_health(self, amount):
        self.max_health += amount
        self.health += amount
    
    def increase_damage(self, amount):
        self.tear_damage += amount
    
    def increase_speed(self, amount):
        self.speed += amount
    
    def increase_tear_rate(self, amount):
        self.tear_rate = max(0.1, self.tear_rate - amount)  # Уменьшение времени = увеличение скорострельности