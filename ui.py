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
    
    def draw(self, screen, player):
        """Отрисовка UI"""
        self._draw_health(screen, player)
        self._draw_stats(screen, player)
        self._draw_controls(screen)
    
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
    
    def draw_room_transition(self, screen, progress):
        """Отрисовка перехода между комнатами"""
        # Эффект затемнения
        alpha = int(255 * progress)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(alpha)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
    
    def draw_minimap(self, screen, current_room, visited_rooms):
        """Отрисовка мини-карты (для будущего расширения)"""
        # Позиция мини-карты
        minimap_x = SCREEN_WIDTH - 100
        minimap_y = SCREEN_HEIGHT - 100
        room_size = 10
        
        # Текущая комната
        current_rect = pygame.Rect(minimap_x, minimap_y, room_size, room_size)
        pygame.draw.rect(screen, YELLOW, current_rect)
        pygame.draw.rect(screen, WHITE, current_rect, 1)