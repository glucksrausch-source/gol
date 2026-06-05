import sys
from PySide6.QtWidgets import QApplication
from ui import GameWindow

def main():
    """
    Main entry point for the Advanced Game of Life application.

    Installation:
    pip install PySide6 numpy scipy
    """
    app = QApplication(sys.argv)

    # Set app-wide dark theme (optional but recommended for Cyberpunk feel)
    app.setStyle("Fusion")

    window = GameWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
