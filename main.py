import pygame
import sys
from game import Game
from menu import MainMenu, SettingsMenu, HeroSelectMenu
from constants import *
import viewport

LOGICAL_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)


def compute_viewport(window_size):
    """Вписывает логическое разрешение (800x600) в окно window_size с
    сохранением пропорций (letterbox). Возвращает (масштаб, смещение)."""
    win_w, win_h = window_size
    scale = min(win_w / LOGICAL_SIZE[0], win_h / LOGICAL_SIZE[1])
    scaled_w = int(LOGICAL_SIZE[0] * scale)
    scaled_h = int(LOGICAL_SIZE[1] * scale)
    offset = ((win_w - scaled_w) // 2, (win_h - scaled_h) // 2)
    return scale, offset


def apply_display_mode(fullscreen, window_size, desktop_size):
    if fullscreen:
        display_surface = pygame.display.set_mode(desktop_size, pygame.FULLSCREEN)
    else:
        display_surface = pygame.display.set_mode(window_size)

    scale, offset = compute_viewport(display_surface.get_size())
    viewport.set_viewport(scale, offset)
    return display_surface, scale, offset


def transform_event_pos(event, scale, offset):
    logical_pos = ((event.pos[0] - offset[0]) / scale, (event.pos[1] - offset[1]) / scale)
    return pygame.event.Event(event.type, {**event.dict, "pos": logical_pos})


def main():
    pygame.init()

    # Настоящее разрешение монитора нужно спросить ДО первого set_mode —
    # после того, как окно уже создано, pygame.display.Info() на некоторых
    # драйверах возвращает размер текущего окна вместо размера экрана,
    # из-за чего полноэкранный режим создавался в маленьком разрешении
    # и потом мылился при растяжении средствами ОС/драйвера
    desktop_info = pygame.display.Info()
    desktop_size = (desktop_info.current_w, desktop_info.current_h)

    fullscreen = False
    window_index = 0
    display_surface, scale, offset = apply_display_mode(
        fullscreen, SettingsMenu.WINDOW_PRESETS[window_index], desktop_size
    )
    pygame.display.set_caption("Подземелья Забытого Короля")

    game_surface = pygame.Surface(LOGICAL_SIZE)
    clock = pygame.time.Clock()

    app_state = "main_menu"  # main_menu -> settings / hero_select -> playing
    main_menu = MainMenu()
    settings_menu = None
    hero_select = None
    game = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                event = transform_event_pos(event, scale, offset)
            events.append(event)

        if app_state == "main_menu":
            for event in events:
                main_menu.handle_event(event)
            main_menu.update(dt)
            main_menu.draw(game_surface)

            if main_menu.result == "start":
                main_menu.result = None
                hero_select = HeroSelectMenu()
                app_state = "hero_select"
            elif main_menu.result == "settings":
                main_menu.result = None
                settings_menu = SettingsMenu(fullscreen, window_index)
                app_state = "settings"
            elif main_menu.result == "quit":
                running = False

        elif app_state == "settings":
            for event in events:
                settings_menu.handle_event(event)
            settings_menu.update(dt)
            settings_menu.draw(game_surface)

            if settings_menu.display_changed:
                fullscreen = settings_menu.fullscreen
                window_index = settings_menu.window_index
                window_size = SettingsMenu.WINDOW_PRESETS[window_index]
                display_surface, scale, offset = apply_display_mode(fullscreen, window_size, desktop_size)
                settings_menu.display_changed = False

            if settings_menu.result == "back":
                app_state = "main_menu"

        elif app_state == "hero_select":
            for event in events:
                hero_select.handle_event(event)
            hero_select.update(dt)
            hero_select.draw(game_surface)

            if hero_select.result == "confirm":
                hero = hero_select.chosen_hero
                game = Game(game_surface, hero=hero)
                pygame.display.set_caption(f"Подземелья Забытого Короля — {hero['name']}")
                app_state = "playing"
            elif hero_select.result == "back":
                app_state = "main_menu"

        elif app_state == "playing":
            for event in events:
                game.handle_event(event)
            game.update(dt)
            game.draw()

        # Масштабирование логического кадра на реальное окно/экран.
        # pygame.transform.scale (не smoothscale) — чтобы не размывать
        # пиксельную графику при растяжении на весь экран.
        display_surface.fill(BLACK)
        scaled_w = int(LOGICAL_SIZE[0] * scale)
        scaled_h = int(LOGICAL_SIZE[1] * scale)
        scaled_frame = pygame.transform.scale(game_surface, (scaled_w, scaled_h))
        display_surface.blit(scaled_frame, offset)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
