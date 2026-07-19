"""Общее состояние масштабирования логического кадра (SCREEN_WIDTH x
SCREEN_HEIGHT) под реальное окно/полноэкранный режим. main.py вызывает
set_viewport() при создании/смене режима окна; player.py использует
to_logical() чтобы перевести реальную позицию мыши в логические
координаты игры для прицеливания."""

scale = 1.0
offset = (0, 0)


def set_viewport(new_scale, new_offset):
    global scale, offset
    scale = new_scale
    offset = new_offset


def to_logical(pos):
    return ((pos[0] - offset[0]) / scale, (pos[1] - offset[1]) / scale)
