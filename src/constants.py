from enum import IntEnum

# Grid Settings
GRID_WIDTH = 2000
GRID_HEIGHT = 2000

# Viewport Defaults
VIEWPORT_WIDTH = 800
VIEWPORT_HEIGHT = 600

class EntityType(IntEnum):
    EMPTY = 0
    NORMAL = 1
    ZOMBIE = 2
    PREDATOR = 3
    GHOST = 4
    BLACK_HOLE = 5
    MUTATED = 6

class ElementType(IntEnum):
    NONE = 0
    QUICKSILVER = 1
    SULFUR = 2
    SALT = 3

# Colors (R, G, B)
COLOR_EMPTY = (0, 0, 0)
COLOR_NORMAL = (0, 255, 0)         # Neon Green
COLOR_ZOMBIE = (255, 0, 255)       # Magenta/Purple
COLOR_PREDATOR = (255, 0, 0)       # Red
COLOR_GHOST = (100, 100, 100)      # Gray
COLOR_BLACK_HOLE = (10, 10, 40)    # Deep Dark Blue/Black
COLOR_MUTATED = (0, 255, 255)      # Cyan
COLOR_QUICKSILVER = (192, 192, 192) # Silver
COLOR_SULFUR = (255, 255, 0)       # Yellow
COLOR_SALT = (255, 255, 255)       # White
