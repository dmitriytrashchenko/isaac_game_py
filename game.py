import pygame
import random
from constants import *
from player import Player
from enemy import Enemy
from room import Room
from item import Item
from ui import UI

class Game:
    def __init__(self, screen):
        self.screen = screen
        self._reset()

    def _reset(self):
        self.state = "playing"  # playing, paused, game_over

        # Создание игрока
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Создание UI
        self.ui = UI()

        # Создание первой комнаты
        self.current_room = Room(ROOM_TYPES['NORMAL'])
        self.current_room.generate_enemies(3)

        # Группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.tears = pygame.sprite.Group()
        self.items = pygame.sprite.Group()

        # Добавляем игрока в группу спрайтов
        self.all_sprites.add(self.player)

        # Добавляем врагов в группы
        for enemy in self.current_room.enemies:
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)

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
        
        # Обновление игрока
        self.player.update(dt)
        
        # Добавление новых слёз игрока
        new_tears = self.player.get_new_tears()
        for tear in new_tears:
            self.all_sprites.add(tear)
            self.tears.add(tear)
        
        # Обновление врагов
        for enemy in self.enemies:
            enemy.update(dt, self.player.rect.center)
        
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
        
        # Столкновения слёз с врагами
        for tear in self.tears:
            hit_enemies = pygame.sprite.spritecollide(tear, self.enemies, False)
            for enemy in hit_enemies:
                enemy.take_damage(tear.damage)
                tear.kill()
                
                # Проверка смерти врага
                if enemy.health <= 0:
                    # Шанс выпадения предмета
                    if random.random() < 0.3:
                        item = Item(enemy.rect.centerx, enemy.rect.centery)
                        self.all_sprites.add(item)
                        self.items.add(item)
                    enemy.kill()
        
        # Столкновения игрока с врагами
        hit_enemies = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for enemy in hit_enemies:
            if self.player.can_take_damage():
                self.player.take_damage(enemy.damage)
        
        # Столкновения игрока с предметами
        collected_items = pygame.sprite.spritecollide(self.player, self.items, True)
        for item in collected_items:
            item.apply_effect(self.player)
        
        # Проверка границ комнаты для игрока
        self._check_room_boundaries()
        
        # Проверка условий поражения
        if self.player.health <= 0:
            self.state = "game_over"
        
        # Проверка очистки комнаты
        if len(self.enemies) == 0 and len(self.current_room.enemies) > 0:
            self.current_room.cleared = True
    
    def _check_room_boundaries(self):
        # Ограничение движения игрока границами комнаты
        room_left = ROOM_OFFSET_X + WALL_THICKNESS
        room_right = ROOM_OFFSET_X + ROOM_WIDTH - WALL_THICKNESS
        room_top = ROOM_OFFSET_Y + WALL_THICKNESS
        room_bottom = ROOM_OFFSET_Y + ROOM_HEIGHT - WALL_THICKNESS
        
        if self.player.rect.left < room_left:
            self.player.rect.left = room_left
        elif self.player.rect.right > room_right:
            self.player.rect.right = room_right
        
        if self.player.rect.top < room_top:
            self.player.rect.top = room_top
        elif self.player.rect.bottom > room_bottom:
            self.player.rect.bottom = room_bottom
    
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == "playing":
            # Отрисовка комнаты
            self.current_room.draw(self.screen)
            
            # Отрисовка всех спрайтов
            self.all_sprites.draw(self.screen)
            
            # Отрисовка UI
            self.ui.draw(self.screen, self.player)
            
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