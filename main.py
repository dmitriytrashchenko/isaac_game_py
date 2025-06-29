import pygame
import sys
from game import Game
from constants import *

def main():
    pygame.init()
    
    # Создание окна
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Isaac Clone")
    
    # Создание игры
    game = Game(screen)
    
    # Основной игровой цикл
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(FPS) / 1000.0  # Время в секундах
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)
        
        # Обновление игры
        game.update(dt)
        
        # Отрисовка
        game.draw()
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()