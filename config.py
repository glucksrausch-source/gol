"""
Configuration and constants for the Game of Life simulation.
"""

# Window settings
WINDOW_TITLE = "Advanced Conway's Game of Life - 10-Regeln-Cockpit"
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800

# Simulation Defaults
DEFAULT_GRID_WIDTH = 200
DEFAULT_GRID_HEIGHT = 200
DEFAULT_TPS = 10
MAX_TPS = 60

# Colors (Hex)
COLOR_BACKGROUND = "#121212"
COLOR_ALIVE = "#00F0FF"
COLOR_ZOMBIE = "#39FF14"
COLOR_MUTATION = "#FFD700"
COLOR_PREDATOR = "#FF003C"
COLOR_GHOST = "#404040"
COLOR_BLACK_HOLE = "#000000"
COLOR_BLACK_HOLE_BORDER = "#FFFFFF"

# UI Strings (German)
STR_PLAY = "Start"
STR_PAUSE = "Pause"
STR_RESET = "Reset"
STR_CLEAR = "Löschen"
STR_RANDOMIZE = "Zufällig"
STR_SETTINGS = "Einstellungen"
STR_RULES = "10-Regeln-Cockpit"
STR_GRID_SIZE = "Grid-Größe"
STR_SPEED = "Geschwindigkeit (TPS)"
STR_WINTER_ACTIVE = "--- WINTER ---"

# Rule names
RULES = {
    1: "Zombie-Zellen",
    2: "Zell-Alterung",
    3: "Spontane Mutation",
    4: "Torus-Welt (Pac-Man)",
    5: "Epidemien",
    6: "Klima-Zyklen (Winter)",
    7: "Räuber und Beute",
    8: "Geister-Spuren",
    9: "Fruchtbarkeits-Boost",
    10: "Schwarze Löcher"
}

# Rule Tooltips
RULE_TOOLTIPS = {
    1: "Sterbende Zellen werden für 1 Tick zu Zombies und töten einen Nachbarn.",
    2: "Zellen sterben nach 15 Ticks an Altersschwäche.",
    3: "2% Chance auf Mutation bei Geburt (3 Ticks immun).",
    4: "Spielfeld ohne Ränder (Wrap-around).",
    5: "Volle 3x3 Matrizen sterben sofort.",
    6: "Alle 50 Ticks kommt für 10 Ticks der Winter (3 Nachbarn zum Überleben nötig).",
    7: "Rote Räuber fressen Zellen und verhungern nach 3 Ticks ohne Nahrung.",
    8: "Sterbende Zellen blockieren das Feld für 1 Tick.",
    9: "Zellen > 10 Ticks sind hochfruchtbar (Geburt bei 2 Nachbarn).",
    10: "Statische 2x2 Blöcke werden nach 20 Ticks zu Schwarzen Löchern."
}
