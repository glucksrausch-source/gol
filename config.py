"""
Configuration and constants for the Alchemical Game of Life - 10,000x10,000 World.
"""

# Window settings
WINDOW_TITLE = "Das Große Alchemie-Labor - 10.000x10.000"
DEFAULT_WIDTH = 1400
DEFAULT_HEIGHT = 900

# Simulation Defaults
DEFAULT_GRID_WIDTH = 10000
DEFAULT_GRID_HEIGHT = 10000
DEFAULT_TPS = 15
MAX_TPS = 60

# Colors (Hex)
COLOR_BACKGROUND = "#000000"
COLOR_ALIVE = "#00F0FF" # Quecksilber (Mercury)
COLOR_SULFUR = "#FF3E00" # Schwefel
COLOR_SALT = "#FFFFFF" # Salz
COLOR_FIRE = "#FFD700" # Philosophisches Feuer
COLOR_ZOMBIE = "#39FF14"
COLOR_PREDATOR = "#FF003C"
COLOR_GHOST = "#404040"
COLOR_BLACK_HOLE = "#101010"
COLOR_BLACK_HOLE_BORDER = "#444444"

# UI Strings (German)
STR_PLAY = "Transmutation Starten"
STR_PAUSE = "Stasis"
STR_RESET = "Labor Reinigen"
STR_CLEAR = "Alles Löschen"
STR_RANDOMIZE = "Ur-Suppe Erzeugen"
STR_SETTINGS = "Alchemistische Parameter"
STR_RULES = "Die 10 Großen Regeln"
STR_GRID_SIZE = "Welt-Größe"
STR_SPEED = "Reaktions-Geschwindigkeit"
STR_WINTER_ACTIVE = "--- KÄLTE-SCHOCK ---"
STR_ALCHEMY_BREW = "Substanz Hinzufügen"

# Rule names (Alchemical themed)
RULES = {
    1: "Zombifizierung (Fäulnis)",
    2: "Natürlicher Zerfall",
    3: "Spontane Transmutation",
    4: "Torus-Welt (Unendlichkeit)",
    5: "Große Reinigung (Epidemie)",
    6: "Ewiger Winter",
    7: "Räuber & Beute (Verzehr)",
    8: "Schatten-Echos",
    9: "Lebens-Elixier (Boost)",
    10: "Der Abgrund (Schwarze Löcher)"
}

# Rule Tooltips
RULE_TOOLTIPS = {
    1: "Zellen im Zerfall reißen andere mit sich.",
    2: "Alles Leben kehrt irgendwann zu Staub zurück.",
    3: "Zufällige Verwandlung bei der Geburt.",
    4: "Die Welt hat kein Ende.",
    5: "Überpopulation führt zur sofortigen Reinigung.",
    6: "Kälte verlangsamt das Wachstum.",
    7: "Rote Räuber jagen die blauen Zellen.",
    8: "Vergangenes Leben hinterlässt Spuren.",
    9: "Alte Zellen begünstigen neues Leben.",
    10: "Konzentrierte Materie kollabiert."
}
