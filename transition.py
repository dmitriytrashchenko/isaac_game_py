import pygame
import math
from constants import *

class RoomTransition:
    def __init__(self):
        self.is_transitioning = False
        self.transition_timer = 0
        self.transition_duration = 0.5  # Секунды
        self.transition_type = "fade"  # fade, slide, etc.
        self.direction = None
        
        # Для эффекта слайда
        self.slide_offset = 0
        
        # Колбэк функции
        self.on_transition_complete = None
    
    def start_transition(self, direction, on_complete=None):
        """Запуск перехода в указанном направлении"""
        if self.is_transitioning:
            return False
        
        self.is_transitioning = True
        self.transition_timer = 0
        self.direction = direction
        self.on_transition_complete = on_complete
        self.slide_offset = 0
        
        return True
    
    def update(self, dt):
        """Обновление состояния перехода"""
        if not self.is_transitioning:
            return
        
        self.transition_timer += dt
        
        # Вычисляем прогресс перехода (0.0 - 1.0)
        progress = min(self.transition_timer / self.transition_duration, 1.0)
        
        # Применяем easing функцию для плавности
        eased_progress = self._ease_in_out(progress)
        
        if self.transition_type == "slide":
            # Для слайд-эффекта
            if self.direction in ['left', 'right']:
                max_offset = SCREEN_WIDTH
            else:
                max_offset = SCREEN_HEIGHT
            
            self.slide_offset = int(max_offset * eased_progress)
        
        # Проверяем завершение перехода
        if progress >= 1.0:
            self._complete_transition()
    
    def _ease_in_out(self, t):
        """Функция плавности для анимации"""
        return t * t * (3.0 - 2.0 * t)
    
    def _complete_transition(self):
        """Завершение перехода"""
        self.is_transitioning = False
        self.transition_timer = 0
        self.slide_offset = 0
        
        if self.on_transition_complete:
            self.on_transition_complete()
            self.on_transition_complete = None
    
    def draw_transition(self, screen):
        """Отрисовка эффекта перехода"""
        if not self.is_transitioning:
            return
        
        progress = min(self.transition_timer / self.transition_duration, 1.0)
        
        if self.transition_type == "fade":
            self._draw_fade_transition(screen, progress)
        elif self.transition_type == "slide":
            self._draw_slide_transition(screen, progress)
    
    def _draw_fade_transition(self, screen, progress):
        """Отрисовка fade-эффекта"""
        # Затемнение экрана
        alpha = int(255 * math.sin(progress * math.pi))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(alpha)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
    
    def _draw_slide_transition(self, screen, progress):
        """Отрисовка slide-эффекта"""
        # Создаем эффект скольжения
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        
        if self.direction == 'left':
            # Скольжение влево
            rect = pygame.Rect(SCREEN_WIDTH - self.slide_offset, 0, 
                             self.slide_offset, SCREEN_HEIGHT)
            pygame.draw.rect(screen, BLACK, rect)
        elif self.direction == 'right':
            # Скольжение вправо
            rect = pygame.Rect(0, 0, self.slide_offset, SCREEN_HEIGHT)
            pygame.draw.rect(screen, BLACK, rect)
        elif self.direction == 'up':
            # Скольжение вверх
            rect = pygame.Rect(0, SCREEN_HEIGHT - self.slide_offset, 
                             SCREEN_WIDTH, self.slide_offset)
            pygame.draw.rect(screen, BLACK, rect)
        elif self.direction == 'down':
            # Скольжение вниз
            rect = pygame.Rect(0, 0, SCREEN_WIDTH, self.slide_offset)
            pygame.draw.rect(screen, BLACK, rect)
    
    def get_transition_progress(self):
        """Получение прогресса перехода (0.0 - 1.0)"""
        if not self.is_transitioning:
            return 0.0
        
        return min(self.transition_timer / self.transition_duration, 1.0)
    
    def is_halfway(self):
        """Проверка, прошла ли половина перехода"""
        return self.get_transition_progress() >= 0.5
    
    def cancel_transition(self):
        """Отмена текущего перехода"""
        self.is_transitioning = False
        self.transition_timer = 0
        self.slide_offset = 0
        self.on_transition_complete = None

class DoorDetector:
    def __init__(self):
        self.door_zones = {}
        self._setup_door_zones()
    
    def _setup_door_zones(self):
        """Настройка зон дверей для обнаружения"""
        door_width = 60
        door_height = 20
        zone_padding = 10
        
        # Верхняя дверь
        self.door_zones['up'] = pygame.Rect(
            ROOM_OFFSET_X + ROOM_WIDTH // 2 - door_width // 2 - zone_padding,
            ROOM_OFFSET_Y - zone_padding,
            door_width + zone_padding * 2,
            door_height + zone_padding * 2
        )
        
        # Нижняя дверь
        self.door_zones['down'] = pygame.Rect(
            ROOM_OFFSET_X + ROOM_WIDTH // 2 - door_width // 2 - zone_padding,
            ROOM_OFFSET_Y + ROOM_HEIGHT - door_height - zone_padding,
            door_width + zone_padding * 2,
            door_height + zone_padding * 2
        )
        
        # Левая дверь
        self.door_zones['left'] = pygame.Rect(
            ROOM_OFFSET_X - zone_padding,
            ROOM_OFFSET_Y + ROOM_HEIGHT // 2 - door_width // 2 - zone_padding,
            door_height + zone_padding * 2,
            door_width + zone_padding * 2
        )
        
        # Правая дверь
        self.door_zones['right'] = pygame.Rect(
            ROOM_OFFSET_X + ROOM_WIDTH - door_height - zone_padding,
            ROOM_OFFSET_Y + ROOM_HEIGHT // 2 - door_width // 2 - zone_padding,
            door_height + zone_padding * 2,
            door_width + zone_padding * 2
        )
    
    def check_door_collision(self, player_rect, room):
        """Проверка столкновения игрока с дверью"""
        for direction, zone in self.door_zones.items():
            if (player_rect.colliderect(zone) and 
                room.doors.get(direction, False)):
                return direction
        
        return None
    
    def draw_debug_zones(self, screen):
        """Отрисовка зон дверей для отладки"""
        for direction, zone in self.door_zones.items():
            pygame.draw.rect(screen, (255, 0, 0, 50), zone, 2)