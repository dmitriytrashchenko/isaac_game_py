import pygame
import math
from constants import *
from tear import Tear, MeleeSwing
import viewport

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, weapon="bow"):
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

        # Оружие героя ("bow" Лучник / "sword" Воин / "staff" Маг) — см.
        # menu.py HEROES и Setting.md. Влияет на стиль атаки и часть статов.
        self.weapon = weapon
        self.flat_damage_reduction = 0
        if weapon == "sword":
            # Воин: ближний бой, урон выше, скорость атаки чуть ниже,
            # щит полностью гасит слабые удары (флэт-редукция урона)
            self.tear_damage = PLAYER_TEAR_DAMAGE * 3
            self.tear_rate = PLAYER_TEAR_RATE * 1.3
            self.flat_damage_reduction = 1
        elif weapon == "staff":
            # Маг: файрболы — медленнее и реже, но сильнее и крупнее
            self.tear_speed = PLAYER_TEAR_SPEED * 0.6
            self.tear_damage = PLAYER_TEAR_DAMAGE * 2
            self.tear_rate = PLAYER_TEAR_RATE * 1.6

        # Движение
        self.velocity = pygame.math.Vector2(0, 0)

        # Стрельба / атака
        self.last_shot = 0
        self.new_tears = []
        self.new_melee_swings = []

        # Урон
        self.invulnerable_time = 0
        self.invulnerable_duration = 1.0  # секунды неуязвимости после получения урона

        # Клавиши движения (только WASD — как в оригинале, стрелки не
        # двигают персонажа, а только целятся/стреляют, иначе зажатая
        # стрелка для выстрела перебивала бы противоположное движение WASD)
        self.keys_pressed = {
            pygame.K_w: False,
            pygame.K_a: False,
            pygame.K_s: False,
            pygame.K_d: False
        }

        # Направления стрельбы по стрелкам: как в оригинальном Айзеке,
        # целится по ПОСЛЕДНЕЙ зажатой стрелке, а не по фиксированному
        # приоритету. Список хранит зажатые стрелки в порядке нажатия.
        self.shoot_key_to_direction = {
            pygame.K_UP: DIRECTIONS['UP'],
            pygame.K_DOWN: DIRECTIONS['DOWN'],
            pygame.K_LEFT: DIRECTIONS['LEFT'],
            pygame.K_RIGHT: DIRECTIONS['RIGHT']
        }
        self.shoot_key_order = []

        # Прицеливание мышью (альтернатива стрелкам): зажатая ЛКМ стреляет
        # на все 360° в сторону курсора, а не только по 4 направлениям
        self.mouse_aim_active = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.keys_pressed:
                self.keys_pressed[event.key] = True
            if event.key in self.shoot_key_to_direction and event.key not in self.shoot_key_order:
                self.shoot_key_order.append(event.key)
        elif event.type == pygame.KEYUP:
            if event.key in self.keys_pressed:
                self.keys_pressed[event.key] = False
            if event.key in self.shoot_key_order:
                self.shoot_key_order.remove(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_aim_active = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_aim_active = False
    
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
        if self.keys_pressed[pygame.K_w]:
            self.velocity.y = -self.speed
        if self.keys_pressed[pygame.K_s]:
            self.velocity.y = self.speed
        if self.keys_pressed[pygame.K_a]:
            self.velocity.x = -self.speed
        if self.keys_pressed[pygame.K_d]:
            self.velocity.x = self.speed
        
        # Нормализация диагонального движения
        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize() * self.speed
        
        # Применение движения
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
    
    def _handle_shooting(self, dt):
        shoot_direction = None

        # Мышь имеет приоритет над стрелками, если зажата ЛКМ — целится
        # на все 360° в сторону курсора, а не только по 4 направлениям
        if self.mouse_aim_active:
            mouse_pos = pygame.math.Vector2(viewport.to_logical(pygame.mouse.get_pos()))
            to_mouse = mouse_pos - pygame.math.Vector2(self.rect.center)
            if to_mouse.length() > 0:
                shoot_direction = to_mouse.normalize()
        elif self.shoot_key_order:
            # Целимся по последней зажатой стрелке (как в оригинале)
            last_key = self.shoot_key_order[-1]
            shoot_direction = self.shoot_key_to_direction[last_key]

        # Атака
        if shoot_direction is not None and self.last_shot >= self.tear_rate:
            if self.weapon == "sword":
                self._melee_attack(shoot_direction)
            else:
                self._shoot(shoot_direction)
            self.last_shot = 0

    def _blend_with_momentum(self, direction):
        # Как в оригинале: импульс движения подмешивается к направлению
        # атаки, давая диагональный "закрут" при стрельбе/ударе на бегу
        momentum_weight = 0.35
        aim_dir = pygame.math.Vector2(direction)
        if self.velocity.length() > 0:
            blended = aim_dir + self.velocity.normalize() * momentum_weight
            if blended.length() > 0:
                aim_dir = blended.normalize()
        return aim_dir

    def _shoot(self, direction):
        aim_dir = self._blend_with_momentum(direction)

        color = BLUE
        size = TEAR_SIZE
        if self.weapon == "staff":
            color = FIRE_ORANGE
            size = TEAR_SIZE + 6

        tear_x = self.rect.centerx + aim_dir.x * (PLAYER_SIZE // 2 + size // 2)
        tear_y = self.rect.centery + aim_dir.y * (PLAYER_SIZE // 2 + size // 2)

        tear = Tear(tear_x, tear_y, aim_dir, self.tear_speed, self.tear_damage, color=color, size=size)
        self.new_tears.append(tear)

    def _melee_attack(self, direction):
        # Воин: мгновенный удар мечом в направлении прицела вместо снаряда —
        # урон применяется в Game (нужен доступ к группе врагов), тут только
        # формируется запрос на удар с позицией/направлением/уроном
        aim_dir = self._blend_with_momentum(direction)
        swing_x = self.rect.centerx + aim_dir.x * 30
        swing_y = self.rect.centery + aim_dir.y * 30
        self.new_melee_swings.append({
            "pos": (swing_x, swing_y),
            "damage": self.tear_damage,
        })

    def get_new_tears(self):
        # Возвращает и очищает список новых слёз
        tears = self.new_tears.copy()
        self.new_tears.clear()
        return tears

    def get_new_melee_swings(self):
        # Возвращает и очищает список новых ударов мечом
        swings = self.new_melee_swings.copy()
        self.new_melee_swings.clear()
        return swings
    
    def take_damage(self, damage):
        if self.invulnerable_time <= 0:
            # Щит Воина полностью гасит слабые удары (флэт-редукция)
            damage = max(0, damage - self.flat_damage_reduction)
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