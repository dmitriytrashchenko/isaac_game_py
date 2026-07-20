import pygame
from constants import *
from player import render_character_silhouette

# Три героя на выбор (см. Setting.md). "weapon" определяет стиль атаки
# в Player: "bow" — дальний бой стрелами (Лучник, базовая механика),
# "sword" — ближний бой (Воин, щит гасит слабые удары), "staff" —
# медленные, но мощные файрболы (Маг).
HEROES = [
    {
        "id": "archer",
        "name": "Лучник",
        "desc": "Дальний бой, стрелы. Сбалансированный урон и скорость.",
        "color": YELLOW,
        "weapon": "bow",
    },
    {
        "id": "warrior",
        "name": "Воин",
        "desc": "Меч и щит, ближний бой. Высокий урон, щит гасит слабые удары.",
        "color": GRAY,
        "weapon": "sword",
    },
    {
        "id": "mage",
        "name": "Маг",
        "desc": "Файрболы: медленнее и реже, зато мощнее и крупнее.",
        "color": FIRE_ORANGE,
        "weapon": "staff",
    },
]


def _wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class MainMenu:
    OPTIONS = ["Начать игру", "Настройки", "Выход"]

    def __init__(self):
        self.selected = 0
        self.title_font = pygame.font.Font(None, 56)
        self.option_font = pygame.font.Font(None, 40)
        self.result = None  # "start" / "settings" / "quit"
        self._option_rects = []

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate(self.selected)
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._option_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._option_rects):
                if rect.collidepoint(event.pos):
                    self._activate(i)

    def _activate(self, index):
        choice = self.OPTIONS[index]
        if choice == "Начать игру":
            self.result = "start"
        elif choice == "Настройки":
            self.result = "settings"
        elif choice == "Выход":
            self.result = "quit"

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BLACK)

        title = self.title_font.render("Подземелья Забытого Короля", True, GOLD)
        screen.blit(title, title.get_rect(midtop=(SCREEN_WIDTH // 2, 100)))

        start_y = 260
        gap = 55
        self._option_rects = []
        for i, option in enumerate(self.OPTIONS):
            color = GOLD if i == self.selected else WHITE
            text = self.option_font.render(option, True, color)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * gap))
            screen.blit(text, rect)
            self._option_rects.append(rect.inflate(60, 20))
            if i == self.selected:
                pointer = self.option_font.render(">", True, GOLD)
                screen.blit(pointer, pointer.get_rect(midright=(rect.left - 20, rect.centery)))


class SettingsMenu:
    """Настройки экрана: полноэкранный режим + размер окна (пресеты).
    Размер окна применяется только пока не включён полный экран."""

    WINDOW_PRESETS = [(800, 600), (1152, 864), (1536, 1152)]

    def __init__(self, fullscreen, window_index=0):
        self.fullscreen = fullscreen
        self.window_index = window_index
        self.display_changed = False

        self.font = pygame.font.Font(None, 34)
        self.title_font = pygame.font.Font(None, 56)
        self.result = None  # "back"

        self._fullscreen_rect = pygame.Rect(0, 0, 0, 0)
        self._resolution_rect = pygame.Rect(0, 0, 0, 0)
        self._back_rect = pygame.Rect(0, 0, 0, 0)

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.display_changed = True

    def _cycle_resolution(self, step):
        if self.fullscreen:
            return
        self.window_index = (self.window_index + step) % len(self.WINDOW_PRESETS)
        self.display_changed = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_f):
                self._toggle_fullscreen()
            elif event.key == pygame.K_LEFT:
                self._cycle_resolution(-1)
            elif event.key == pygame.K_RIGHT:
                self._cycle_resolution(1)
            elif event.key == pygame.K_ESCAPE:
                self.result = "back"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._fullscreen_rect.collidepoint(event.pos):
                self._toggle_fullscreen()
            elif self._resolution_rect.collidepoint(event.pos):
                self._cycle_resolution(1)
            elif self._back_rect.collidepoint(event.pos):
                self.result = "back"

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BLACK)
        title = self.title_font.render("Настройки", True, GOLD)
        screen.blit(title, title.get_rect(midtop=(SCREEN_WIDTH // 2, 80)))

        state_text = "Вкл" if self.fullscreen else "Выкл"
        line = self.font.render(f"Полноэкранный режим (Enter/F): {state_text}", True, WHITE)
        self._fullscreen_rect = line.get_rect(center=(SCREEN_WIDTH // 2, 220)).inflate(40, 16)
        screen.blit(line, line.get_rect(center=self._fullscreen_rect.center))

        res_w, res_h = self.WINDOW_PRESETS[self.window_index]
        res_color = GRAY if self.fullscreen else WHITE
        res_line = self.font.render(f"Размер окна (← →): {res_w}x{res_h}", True, res_color)
        self._resolution_rect = res_line.get_rect(center=(SCREEN_WIDTH // 2, 270)).inflate(40, 16)
        screen.blit(res_line, res_line.get_rect(center=self._resolution_rect.center))
        if self.fullscreen:
            hint = pygame.font.Font(None, 22).render("(недоступно в полноэкранном режиме)", True, GRAY)
            screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 296)))

        back = self.font.render("Назад", True, WHITE)
        self._back_rect = back.get_rect(center=(SCREEN_WIDTH // 2, 380)).inflate(40, 16)
        screen.blit(back, back.get_rect(center=self._back_rect.center))

        hint = self.font.render("ESC — назад в меню", True, GRAY)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 430)))


class HeroSelectMenu:
    def __init__(self):
        self.selected = 0
        self.title_font = pygame.font.Font(None, 48)
        self.name_font = pygame.font.Font(None, 36)
        self.desc_font = pygame.font.Font(None, 22)
        self.result = None  # "confirm" / "back"
        self._card_rects = []

    @property
    def chosen_hero(self):
        return HEROES[self.selected]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(HEROES)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(HEROES)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.result = "confirm"
            elif event.key == pygame.K_ESCAPE:
                self.result = "back"
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._card_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._card_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    self.result = "confirm"

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BLACK)
        title = self.title_font.render("Выбери героя", True, GOLD)
        screen.blit(title, title.get_rect(midtop=(SCREEN_WIDTH // 2, 50)))

        card_width = 200
        card_height = 260
        gap = 40
        total_width = card_width * len(HEROES) + gap * (len(HEROES) - 1)
        start_x = (SCREEN_WIDTH - total_width) // 2
        card_y = 160

        self._card_rects = []
        for i, hero in enumerate(HEROES):
            x = start_x + i * (card_width + gap)
            rect = pygame.Rect(x, card_y, card_width, card_height)
            self._card_rects.append(rect)

            selected = i == self.selected
            pygame.draw.rect(screen, DARK_GRAY, rect)
            pygame.draw.rect(screen, GOLD if selected else GRAY, rect, 4 if selected else 2)

            icon = render_character_silhouette(hero["weapon"], hero["color"], PLAYER_SIZE)
            icon = pygame.transform.scale(icon, (PLAYER_SIZE * 2, PLAYER_SIZE * 2))
            icon_rect = icon.get_rect(center=(rect.centerx, rect.top + 60))
            screen.blit(icon, icon_rect)

            name = self.name_font.render(hero["name"], True, WHITE)
            screen.blit(name, name.get_rect(center=(rect.centerx, rect.top + 120)))

            for j, line in enumerate(_wrap_text(hero["desc"], self.desc_font, card_width - 20)):
                text = self.desc_font.render(line, True, GRAY)
                screen.blit(text, text.get_rect(center=(rect.centerx, rect.top + 160 + j * 22)))

        hint = self.desc_font.render("<- -> выбор, Enter - начать, ESC - назад", True, GRAY)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, card_y + card_height + 40)))
