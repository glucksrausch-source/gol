import sys
from PySide6.QtWidgets import QApplication
from src.engine import GameEngine
from src.gui_widget import GridWidget

app = QApplication(sys.argv)
engine = GameEngine(100, 100)
engine.randomize()
widget = GridWidget(engine)
print("Widget created")
