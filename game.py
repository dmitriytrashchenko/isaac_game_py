import pygame
import random
from constants import *
from player import Player
from enemy import Enemy
from room import Room
from item import Item
from tear import MeleeSwing
from chest import TIER_COLORS
from ui import UI
from dungeon import Dungeon
from transition import RoomTransition, DoorDetector
from currency import Eye
import particles

class Game:
    def __init__(self, screen, hero=None):
        self.screen = screen
        # Выбранный на экране выбора героя персонаж (см. menu.py) — задаёт
        # оружие/механику боя игрока (Player.weapon). См. Setting.md.
        self.hero = hero
        self._reset()

    def _reset(self):
        self.state = "playing"  # playing, paused, game_over
        self.floor = 1

        # Создание игрока — оружие берётся из выбранного героя (Лучник
        # "bow" / Воин "sword" / Маг "staff"), см. menu.py и Setting.md
        weapon = self.hero["weapon"] if self.hero else "bow"
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, weapon=weapon)

        # Создание UI
        self.ui = UI()

        # Генерация подземелья
        self.dungeon = Dungeon()
        self.transition = RoomTransition()
        self.door_detector = DoorDetector()

        # Группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.tears = pygame.sprite.Group()
        self.enemy_tears = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.chests = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()  # чисто визуальные, без коллизий (вспышка удара мечом)
        self.particles = pygame.sprite.Group()  # искры факелов, вспышки попаданий
        self.vases = pygame.sprite.Group()
        self.currency = pygame.sprite.Group()

        # Добавляем игрока в группу спрайтов
        self.all_sprites.add(self.player)

        self._load_current_room()

        # Флаг: комната уже подменена в текущем переходе (срабатывает
        # один раз в момент полной черноты экрана, см. update())
        self._room_swapped_this_transition = False

        # Всплывающая надпись о полученном призе (сундук-рулетка)
        self.pickup_message = None
        self.pickup_message_color = WHITE
        self.pickup_message_timer = 0.0

        # Время с начала забега — используется для мерцания факелов
        self.elapsed_time = 0.0

        # Периодический спавн искр-угольков от факелов
        self.ember_timer = 0.0
        self.ember_interval = 0.12

        # Тряска камеры при уроне/победе над боссом
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        self.shake_magnitude = 0.0

        # Буфер для отрисовки игрового мира отдельно от UI — тряска
        # камеры сдвигает только его, UI остаётся неподвижным
        self.world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    @property
    def current_room(self):
        return self.dungeon.current_room

    def _load_current_room(self):
        """Заполняет группы спрайтов содержимым текущей комнаты подземелья"""
        for enemy in list(self.enemies):
            enemy.kill()
        for tear in list(self.tears):
            tear.kill()
        for tear in list(self.enemy_tears):
            tear.kill()
        for item in list(self.items):
            item.kill()
        for chest in list(self.chests):
            chest.kill()
        for effect in list(self.effects):
            effect.kill()
        for particle in list(self.particles):
            particle.kill()
        for vase in list(self.vases):
            vase.kill()
        for currency in list(self.currency):
            currency.kill()

        # Живые враги комнаты (мёртвые из прошлого визита не воскрешаем)
        for enemy in self.current_room.enemies:
            if enemy.health > 0:
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)

        # Несобранные предметы комнаты (сокровищница)
        for item in self.current_room.items:
            self.all_sprites.add(item)
            self.items.add(item)

        # Целые вазы комнаты (разбитые из прошлого визита не восстанавливаем)
        for vase in self.current_room.vases:
            if not vase.destroyed:
                self.all_sprites.add(vase)
                self.vases.add(vase)

        # Редкий сундук-рулетка (если уже был заспавнен при прошлом визите)
        if self.current_room.chest:
            self.all_sprites.add(self.current_room.chest)
            self.chests.add(self.current_room.chest)

    def _kill_enemy_with_drop(self, enemy):
        """Убивает врага: шанс 30% оставить предмет, отдельно шанс 20%
        оставить валюту (глаз) — независимые роллы, вазы глаза не дают"""
        self._spawn_hit_sparks(enemy.rect.center, enemy._current_color(), count=10)
        if random.random() < 0.3:
            item = Item(enemy.rect.centerx, enemy.rect.centery)
            self.all_sprites.add(item)
            self.items.add(item)
        if random.random() < 0.2:
            eye = Eye(enemy.rect.centerx, enemy.rect.centery, amount=1)
            self.all_sprites.add(eye)
            self.currency.add(eye)
        enemy.kill()

    def _destroy_vase(self, vase):
        """Разбивает вазу: искры + шанс 40% оставить предмет (глаза с
        ваз не выпадают — только с врагов, см. _kill_enemy_with_drop)"""
        vase.destroyed = True
        self._spawn_hit_sparks(vase.rect.center, vase.shard_color, count=8)

        if random.random() < 0.4:
            item = Item(vase.rect.centerx, vase.rect.centery)
            self.all_sprites.add(item)
            self.items.add(item)

        vase.kill()

    def _resolve_static_obstacle_collisions(self):
        """Простое выталкивание игрока из целых ваз и колонн по оси
        наименьшего перекрытия — оба типа физически блокируют проход"""
        obstacle_rects = [vase.rect for vase in self.vases] + list(self.current_room.pillars)

        for obstacle_rect in obstacle_rects:
            if not self.player.rect.colliderect(obstacle_rect):
                continue

            dx1 = obstacle_rect.right - self.player.rect.left
            dx2 = self.player.rect.right - obstacle_rect.left
            dy1 = obstacle_rect.bottom - self.player.rect.top
            dy2 = self.player.rect.bottom - obstacle_rect.top
            overlap_x = min(dx1, dx2)
            overlap_y = min(dy1, dy2)

            if overlap_x < overlap_y:
                if dx1 < dx2:
                    self.player.rect.left = obstacle_rect.right
                else:
                    self.player.rect.right = obstacle_rect.left
            else:
                if dy1 < dy2:
                    self.player.rect.top = obstacle_rect.bottom
                else:
                    self.player.rect.bottom = obstacle_rect.top

    def _spawn_hit_sparks(self, pos, color, count=6):
        for spark in particles.spawn_hit_sparks(pos, color, count):
            self.all_sprites.add(spark)
            self.particles.add(spark)

    def _trigger_shake(self, magnitude, duration):
        """Тряска камеры (мира, не UI) — суммируется, если уже трясётся"""
        self.shake_magnitude = max(self.shake_magnitude, magnitude)
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_duration = max(self.shake_duration, duration)

    def _get_shake_offset(self):
        if self.shake_timer <= 0:
            return (0, 0)
        progress = self.shake_timer / self.shake_duration if self.shake_duration else 0
        magnitude = self.shake_magnitude * progress
        return (random.randint(-int(magnitude), int(magnitude)),
                random.randint(-int(magnitude), int(magnitude)))

    def _get_stairs_rect(self):
        """Прямоугольник люка на следующий этаж (появляется в центре
        зачищенной комнаты босса)"""
        size = 40
        cx = ROOM_OFFSET_X + ROOM_WIDTH // 2
        cy = ROOM_OFFSET_Y + ROOM_HEIGHT // 2
        return pygame.Rect(cx - size // 2, cy - size // 2, size, size)

    def _advance_floor(self):
        """Переход на следующий этаж после победы над боссом.
        Статы игрока сохраняются, подземелье генерируется заново"""
        self.floor += 1

        self.dungeon = Dungeon()
        self.door_detector = DoorDetector()
        self.transition = RoomTransition()
        self._room_swapped_this_transition = False

        self._load_current_room()
        self.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.state != "game_over":
                self.state = "paused" if self.state == "playing" else "playing"
            elif event.key == pygame.K_r and self.state == "game_over":
                self._reset()
                return

        self.player.handle_event(event)

    def update(self, dt):
        if self.state != "playing":
            return

        if self.transition.is_transitioning:
            self.transition.update(dt)
            # Меняем комнату ровно в момент полной черноты экрана (середина
            # перехода), а не в конце — иначе смена происходит уже на свету
            # и выглядит как рывок/телепорт на глазах у игрока
            if self.transition.is_halfway() and not self._room_swapped_this_transition:
                self._complete_room_transition(self.transition.direction)
                self._room_swapped_this_transition = True
            return

        # Обновление таймера всплывающей надписи о призе
        if self.pickup_message_timer > 0:
            self.pickup_message_timer -= dt

        # Время забега (мерцание факелов) и тряска камеры
        self.elapsed_time += dt
        if self.shake_timer > 0:
            self.shake_timer -= dt

        # Периодический спавн искр-угольков от факелов текущей комнаты
        self.ember_timer += dt
        torches = self.current_room.get_torch_positions()
        if self.ember_timer >= self.ember_interval and torches:
            self.ember_timer = 0.0
            torch = random.choice(torches)
            ember = particles.spawn_ember((torch[0], torch[1] - 12))
            self.all_sprites.add(ember)
            self.particles.add(ember)

        # Обновление игрока
        self.player.update(dt)

        # Добавление новых слёз игрока
        new_tears = self.player.get_new_tears()
        for tear in new_tears:
            self.all_sprites.add(tear)
            self.tears.add(tear)

        # Удары мечом (Воин) — урон применяется мгновенно здесь (у Player
        # нет доступа к группе врагов), плюс визуальная вспышка
        for swing in self.player.get_new_melee_swings():
            swing_rect = pygame.Rect(0, 0, 40, 40)
            swing_rect.center = swing["pos"]
            for enemy in list(self.enemies):
                if swing_rect.colliderect(enemy.rect):
                    enemy.take_damage(swing["damage"])
                    if enemy.health <= 0:
                        self._kill_enemy_with_drop(enemy)
                    else:
                        self._spawn_hit_sparks(enemy.rect.center, enemy._current_color(), count=4)
            for vase in list(self.vases):
                if swing_rect.colliderect(vase.rect):
                    vase.take_damage(swing["damage"])
                    if vase.health <= 0:
                        self._destroy_vase(vase)

            slash = MeleeSwing(swing["pos"])
            self.all_sprites.add(slash)
            self.effects.add(slash)

        # Обновление врагов
        for enemy in self.enemies:
            enemy.update(dt, self.player.rect.center)

            # Снаряды врагов-стрелков
            for tear in enemy.get_new_tears():
                self.all_sprites.add(tear)
                self.enemy_tears.add(tear)

        # Обновление визуальных эффектов (вспышка удара мечом) и частиц
        # (искры факелов, вспышки попаданий) — сами себя удаляют по
        # истечении lifetime в update()
        for effect in list(self.effects):
            effect.update(dt)
        for particle in list(self.particles):
            particle.update(dt)

        # Анимация парения предметов/валюты
        for item in self.items:
            item.update(dt)
        for eye in self.currency:
            eye.update(dt)

        # Обновление слёз
        for tear in self.tears:
            tear.update(dt)

            # Удаление слёз, вышедших за границы экрана или истёкших
            if (tear.rect.right < ROOM_OFFSET_X or
                tear.rect.left > ROOM_OFFSET_X + ROOM_WIDTH or
                tear.rect.bottom < ROOM_OFFSET_Y or
                tear.rect.top > ROOM_OFFSET_Y + ROOM_HEIGHT or
                tear.lifetime <= 0):
                tear.kill()

        # Обновление вражеских слёз
        for tear in self.enemy_tears:
            tear.update(dt)

            if (tear.rect.right < ROOM_OFFSET_X or
                tear.rect.left > ROOM_OFFSET_X + ROOM_WIDTH or
                tear.rect.bottom < ROOM_OFFSET_Y or
                tear.rect.top > ROOM_OFFSET_Y + ROOM_HEIGHT or
                tear.lifetime <= 0):
                tear.kill()

        # Столкновения вражеских слёз с игроком
        hit_by_enemy_tears = pygame.sprite.spritecollide(self.player, self.enemy_tears, True)
        for tear in hit_by_enemy_tears:
            if self.player.can_take_damage():
                self.player.take_damage(tear.damage)
                self._trigger_shake(6, 0.2)

        # Столкновения слёз с врагами
        for tear in self.tears:
            hit_enemies = pygame.sprite.spritecollide(tear, self.enemies, False)
            for enemy in hit_enemies:
                enemy.take_damage(tear.damage)
                tear.kill()

                if enemy.health <= 0:
                    self._kill_enemy_with_drop(enemy)
                else:
                    self._spawn_hit_sparks(enemy.rect.center, enemy._current_color(), count=4)

        # Столкновения слёз с вазами
        for tear in self.tears:
            hit_vases = pygame.sprite.spritecollide(tear, self.vases, False)
            for vase in hit_vases:
                vase.take_damage(tear.damage)
                tear.kill()
                if vase.health <= 0:
                    self._destroy_vase(vase)

        # Игрок физически не проходит сквозь целые вазы и колонны
        self._resolve_static_obstacle_collisions()

        # Столкновения игрока с врагами
        hit_enemies = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for enemy in hit_enemies:
            if self.player.can_take_damage():
                self.player.take_damage(enemy.damage)
                self._trigger_shake(6, 0.2)

        # Враги иногда воруют предметы: наступив на предмет, с шансом 25%
        # забирают бафф себе вместо игрока (и предмет пропадает)
        for enemy in list(self.enemies):
            looted = pygame.sprite.spritecollide(enemy, self.items, False)
            for item in looted:
                if random.random() < 0.25:
                    enemy.apply_item_effect(item.item_type)
                    self._spawn_hit_sparks(item.rect.center, enemy._current_color(), count=5)
                    if item in self.current_room.items:
                        self.current_room.items.remove(item)
                    item.kill()

        # Столкновения игрока с предметами
        collected_items = pygame.sprite.spritecollide(self.player, self.items, True)
        for item in collected_items:
            item.apply_effect(self.player)
            # Сокровище комнаты собрано — чтобы не воскресало при повторном визите
            if item in self.current_room.items:
                self.current_room.items.remove(item)

        # Столкновения игрока с валютой (глаза)
        collected_currency = pygame.sprite.spritecollide(self.player, self.currency, True)
        for eye in collected_currency:
            self.player.add_eyes(eye.amount)

        # Проверка границ комнаты для игрока (с учётом открытых дверей)
        self._check_room_boundaries()

        # Проверка условий поражения
        if self.player.health <= 0:
            self.state = "game_over"
            return

        # Проверка очистки комнаты — "not self.current_room.cleared" тут
        # обязателен: без него это условие оставалось бы истинным КАЖДЫЙ
        # кадр после зачистки (враги не воскресают), и тряска ниже
        # запускалась бы бесконечно вместо одного раза
        if len(self.enemies) == 0 and len(self.current_room.enemies) > 0 and not self.current_room.cleared:
            self.current_room.cleared = True

            # Комната босса только что зачищена — спавним сундук со случайным уровнем редкости приза (1-10)
            if self.current_room.room_type == ROOM_TYPES['BOSS']:
                self._trigger_shake(14, 0.4)
                self.current_room.maybe_spawn_chest()
                if self.current_room.chest and self.current_room.chest not in self.chests:
                    self.all_sprites.add(self.current_room.chest)
                    self.chests.add(self.current_room.chest)

        # Обновление и взаимодействие с сундуком-рулеткой
        for chest in self.chests:
            chest.update(dt)

            if chest.state == "closed" and self.player.rect.colliderect(chest.rect):
                chest.start_spin()

            if chest.state == "opened" and not chest.reward_applied:
                chest.apply_reward(self.player)
                chest.reward_applied = True
                self.pickup_message = f"{chest.reward_name}  (Tier {chest.tier}/10)"
                self.pickup_message_color = TIER_COLORS[chest.tier - 1]
                self.pickup_message_timer = 3.0

        # Комната босса зачищена — проверяем, не наступил ли игрок на люк
        if self.current_room.room_type == ROOM_TYPES['BOSS'] and self.current_room.cleared:
            if self.player.rect.colliderect(self._get_stairs_rect()):
                self._advance_floor()
                return

        # Проверка перехода в соседнюю комнату через дверь
        direction = self.door_detector.check_door_collision(self.player.rect, self.current_room)
        if direction and self.dungeon.can_move_to(direction):
            self._room_swapped_this_transition = False
            self.transition.start_transition(direction)

    def _complete_room_transition(self, direction):
        if not self.dungeon.move_to_room(direction):
            return

        self._load_current_room()

        room_left = ROOM_OFFSET_X + WALL_THICKNESS
        room_right = ROOM_OFFSET_X + ROOM_WIDTH - WALL_THICKNESS
        room_top = ROOM_OFFSET_Y + WALL_THICKNESS
        room_bottom = ROOM_OFFSET_Y + ROOM_HEIGHT - WALL_THICKNESS
        cx = ROOM_OFFSET_X + ROOM_WIDTH // 2
        cy = ROOM_OFFSET_Y + ROOM_HEIGHT // 2

        # Ставим игрока у противоположной двери новой комнаты, но с запасом,
        # чтобы не попасть прямо в зону обнаружения этой же двери и не
        # запустить переход обратно на следующем кадре (зона двери уходит
        # ~30px вглубь комнаты за счёт zone_padding в DoorDetector)
        if direction == 'up':
            self.player.rect.midbottom = (cx, room_bottom - ROOM_ENTRY_MARGIN)
        elif direction == 'down':
            self.player.rect.midtop = (cx, room_top + ROOM_ENTRY_MARGIN)
        elif direction == 'left':
            self.player.rect.midright = (room_right - ROOM_ENTRY_MARGIN, cy)
        elif direction == 'right':
            self.player.rect.midleft = (room_left + ROOM_ENTRY_MARGIN, cy)

    def _check_room_boundaries(self):
        # Ограничение движения игрока границами комнаты, с проёмами в открытых дверях
        room_left = ROOM_OFFSET_X + WALL_THICKNESS
        room_right = ROOM_OFFSET_X + ROOM_WIDTH - WALL_THICKNESS
        room_top = ROOM_OFFSET_Y + WALL_THICKNESS
        room_bottom = ROOM_OFFSET_Y + ROOM_HEIGHT - WALL_THICKNESS

        door_width = 60
        cx = ROOM_OFFSET_X + ROOM_WIDTH // 2
        cy = ROOM_OFFSET_Y + ROOM_HEIGHT // 2
        in_horizontal_gap = abs(self.player.rect.centerx - cx) < door_width // 2
        in_vertical_gap = abs(self.player.rect.centery - cy) < door_width // 2

        # Пока в комнате есть живые враги, двери физически заперты
        room_open = not self.current_room.is_locked()

        can_pass_left = self.current_room.doors['left'] and in_vertical_gap and room_open
        can_pass_right = self.current_room.doors['right'] and in_vertical_gap and room_open
        can_pass_top = self.current_room.doors['up'] and in_horizontal_gap and room_open
        can_pass_bottom = self.current_room.doors['down'] and in_horizontal_gap and room_open

        if not can_pass_left and self.player.rect.left < room_left:
            self.player.rect.left = room_left
        if not can_pass_right and self.player.rect.right > room_right:
            self.player.rect.right = room_right
        if not can_pass_top and self.player.rect.top < room_top:
            self.player.rect.top = room_top
        if not can_pass_bottom and self.player.rect.bottom > room_bottom:
            self.player.rect.bottom = room_bottom

        # Не выпускаем игрока за пределы экрана даже в проёме двери
        self.player.rect.left = max(self.player.rect.left, 0)
        self.player.rect.right = min(self.player.rect.right, SCREEN_WIDTH)
        self.player.rect.top = max(self.player.rect.top, 0)
        self.player.rect.bottom = min(self.player.rect.bottom, SCREEN_HEIGHT)

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "playing":
            # Мир (комната + спрайты) рисуется в отдельный буфер, который
            # затем блитится со сдвигом тряски камеры — UI остаётся
            # неподвижным и не трясётся вместе с миром
            self.world_surface.fill(BLACK)

            self.current_room.draw(self.world_surface, self.elapsed_time)

            # Люк на следующий этаж, если босс побеждён
            if self.current_room.room_type == ROOM_TYPES['BOSS'] and self.current_room.cleared:
                pygame.draw.rect(self.world_surface, (80, 0, 120), self._get_stairs_rect())
                pygame.draw.rect(self.world_surface, WHITE, self._get_stairs_rect(), 2)

            # Отрисовка всех спрайтов
            self.all_sprites.draw(self.world_surface)

            # Игрок всегда поверх остальных спрайтов (сундуков, предметов,
            # врагов), иначе его перекрывает то, на чём он стоит
            self.world_surface.blit(self.player.image, self.player.rect)

            self.screen.blit(self.world_surface, self._get_shake_offset())

            # Отрисовка UI
            hero_name = self.hero["name"] if self.hero else None
            self.ui.draw(self.screen, self.player, self.floor, hero_name)

            # Всплывающая надпись о призе из сундука
            if self.pickup_message_timer > 0:
                self.ui.draw_pickup_message(self.screen, self.pickup_message, self.pickup_message_color)

            # Мини-карта подземелья
            self.ui.draw_minimap(self.screen, self.dungeon.get_minimap_data())

            # Затемнение при переходе между комнатами
            self.transition.draw_transition(self.screen)

        elif self.state == "paused":
            # Отрисовка паузы
            font = pygame.font.Font(None, 74)
            text = font.render("PAUSED", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(text, text_rect)

        elif self.state == "game_over":
            # Отрисовка экрана поражения
            font = pygame.font.Font(None, 74)
            text = font.render("GAME OVER", True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(text, text_rect)

            restart_text = pygame.font.Font(None, 36).render("Press R to restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(restart_text, restart_rect)
