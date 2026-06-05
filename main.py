import sys
from PySide6.QtWidgets import QApplication
from ui import GameWindow

def main():
    """
    Das Große Alchemie-Labor - 10.000x10.000 Simulation.

    Installation:
    pip install PySide6 numpy scipy
    """
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = GameWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
