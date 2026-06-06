import sys
from PySide6.QtWidgets import QApplication
from src.engine import GameEngine
from src.gui import GameWindow
from src.constants import GRID_WIDTH, GRID_HEIGHT

def main():
    app = QApplication(sys.argv)

    # Enable dark mode styling
    app.setStyle("Fusion")

    # Initialize Engine with massive grid
    # We use 2000x2000 for realistic high-end performance, but engine allows 10k x 10k if RAM allows
    engine = GameEngine(GRID_WIDTH, GRID_HEIGHT)
    engine.randomize() # Start with some life to not be boring

    window = GameWindow(engine)
    window.resize(1200, 800)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
