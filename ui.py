import pygame
import math
from constants import *

class UI:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Размеры сердечек
        self.heart_size = 16
        self.heart_spacing = 4
    
    def draw(self, screen, player, floor=1, hero_name=None):
        """Отрисовка UI"""
        self._draw_health(screen, player)
        self._draw_stats(screen, player)
        self._draw_controls(screen)
        self._draw_floor(screen, floor)
        if hero_name:
            self._draw_hero_name(screen, hero_name)

    def _draw_hero_name(self, screen, hero_name):
        """Имя выбранного на старте героя (верхний левый угол, под сердечками)"""
        text = self.small_font.render(hero_name, True, GOLD)
        rect = text.get_rect(topleft=(20, 130))
        screen.blit(text, rect)

    def _draw_floor(self, screen, floor):
        """Номер текущего этажа"""
        text = self.font.render(f"Floor {floor}", True, WHITE)
        rect = text.get_rect(midtop=(SCREEN_WIDTH // 2, 10))
        screen.blit(text, rect)
    
    def _draw_health(self, screen, player):
        """Отрисовка полоски здоровья"""
        start_x = 20
        start_y = 20
        
        # Отрисовка сердечек
        for i in range(player.max_health):
            x = start_x + i * (self.heart_size + self.heart_spacing)
            y = start_y
            
            # Определение состояния сердечка
            if i < player.health:
                # Полное сердце
                self._draw_heart(screen, x, y, "full")
            else:
                # Пустое сердце
                self._draw_heart(screen, x, y, "empty")
    
    def _draw_heart(self, screen, x, y, state):
        """Отрисовка одного сердечка"""
        heart_rect = pygame.Rect(x, y, self.heart_size, self.heart_size)
        
        if state == "full":
            # Полное сердце - красное
            pygame.draw.rect(screen, RED, heart_rect)
            pygame.draw.rect(screen, (150, 0, 0), heart_rect, 2)
        elif state == "empty":
            # Пустое сердце - контур
            pygame.draw.rect(screen, DARK_GRAY, heart_rect)
            pygame.draw.rect(screen, GRAY, heart_rect, 2)
    
    def _draw_stats(self, screen, player):
        """Отрисовка статистик игрока"""
        stats_x = 20
        stats_y = 50
        line_height = 25
        
        # Урон
        damage_text = self.small_font.render(f"Damage: {player.tear_damage:.1f}", True, WHITE)
        screen.blit(damage_text, (stats_x, stats_y))
        
        # Скорость
        speed_text = self.small_font.render(f"Speed: {player.speed:.0f}", True, WHITE)
        screen.blit(speed_text, (stats_x, stats_y + line_height))
        
        # Скорострельность
        tears_per_sec = 1.0 / player.tear_rate if player.tear_rate > 0 else 0
        tears_text = self.small_font.render(f"Tears: {tears_per_sec:.1f}/s", True, WHITE)
        screen.blit(tears_text, (stats_x, stats_y + line_height * 2))
    
    def _draw_controls(self, screen):
        """Отрисовка подсказок по управлению"""
        controls_x = SCREEN_WIDTH - 200
        controls_y = 20
        line_height = 20
        
        controls = [
            "WASD - Move",
            "Arrows - Shoot",
            "LMB (hold) - Shoot at mouse",
            "ESC - Pause"
        ]
        
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, WHITE)
            screen.blit(text, (controls_x, controls_y + i * line_height))
    
    def draw_game_over(self, screen):
        """Отрисовка экрана поражения"""
        # Полупрозрачный фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Текст Game Over
        game_over_text = self.font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        screen.blit(game_over_text, game_over_rect)
        
        # Подсказка перезапуска
        restart_text = self.small_font.render("Press R to restart or ESC to quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        screen.blit(restart_text, restart_rect)
    
    def draw_pause(self, screen):
        """Отрисовка экрана паузы"""
        # Полупрозрачный фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Текст паузы
        pause_text = self.font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(pause_text, pause_rect)
        
        # Подсказка продолжения
        continue_text = self.small_font.render("Press ESC to continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
        screen.blit(continue_text, continue_rect)
    
    def draw_pickup_message(self, screen, text, color=WHITE):
        """Крупная надпись о полученном призе (сундук-рулетка и т.п.),
        держится на экране несколько секунд после получения."""
        banner = self.font.render(text, True, color)
        rect = banner.get_rect(midtop=(SCREEN_WIDTH // 2, 45))

        bg = pygame.Surface((rect.width + 20, rect.height + 10))
        bg.set_alpha(180)
        bg.fill(BLACK)
        bg_rect = bg.get_rect(center=rect.center)
        screen.blit(bg, bg_rect)
        screen.blit(banner, rect)

    def draw_room_transition(self, screen, progress):
        """Отрисовка перехода между комнатами"""
        # Эффект затемнения
        alpha = int(255 * progress)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(alpha)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
    
    def draw_minimap(self, screen, minimap_data):
        """Отрисовка мини-карты подземелья (только посещённые комнаты)"""
        room_size = 10
        room_gap = 3
        minimap_x = SCREEN_WIDTH - 110
        minimap_y = SCREEN_HEIGHT - 110

        rooms = minimap_data['rooms']
        visited = minimap_data['visited']
        current = minimap_data['current']

        room_colors = {
            ROOM_TYPES['NORMAL']: GRAY,
            ROOM_TYPES['TREASURE']: YELLOW,
            ROOM_TYPES['BOSS']: RED,
            ROOM_TYPES['SECRET']: (150, 0, 150)
        }

        for pos in visited:
            if pos not in rooms:
                continue

            rel_x = pos[0] - current[0]
            rel_y = pos[1] - current[1]
            x = minimap_x + rel_x * (room_size + room_gap)
            y = minimap_y + rel_y * (room_size + room_gap)

            color = room_colors.get(rooms[pos], GRAY)
            rect = pygame.Rect(x, y, room_size, room_size)
            pygame.draw.rect(screen, color, rect)

            if pos == current:
                pygame.draw.rect(screen, WHITE, rect, 2)
            else:
                pygame.draw.rect(screen, DARK_GRAY, rect, 1)