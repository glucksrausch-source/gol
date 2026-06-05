import sys
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QSlider, QLabel, QCheckBox, QFrame,
                             QSizePolicy, QGridLayout, QScrollArea)
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPalette

import config
from engine import GameEngine

class GridWidget(QWidget):
    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine
        self.setMouseTracking(True)
        self.drawing = False
        self.draw_value = True

        # Color mapping as numpy arrays (RGB)
        self.colors = {
            'bg': self._hex_to_rgb(config.COLOR_BACKGROUND),
            'alive': self._hex_to_rgb(config.COLOR_ALIVE),
            'zombie': self._hex_to_rgb(config.COLOR_ZOMBIE),
            'mutation': self._hex_to_rgb(config.COLOR_MUTATION),
            'predator': self._hex_to_rgb(config.COLOR_PREDATOR),
            'ghost': self._hex_to_rgb(config.COLOR_GHOST),
            'bh': self._hex_to_rgb(config.COLOR_BLACK_HOLE),
            'bh_border': self._hex_to_rgb(config.COLOR_BLACK_HOLE_BORDER)
        }

    def _hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.uint8)

    def paintEvent(self, event):
        painter = QPainter(self)

        w, h = self.engine.width, self.engine.height
        state = self.engine.state

        # Create RGB image from engine state
        # Initialize with background
        data = np.full((h, w, 3), self.colors['bg'], dtype=np.uint8)

        # Apply layers by priority (lowest to highest)
        if np.any(state.ghost):
            data[state.ghost] = self.colors['ghost']

        if np.any(state.alive):
            data[state.alive] = self.colors['alive']

        # Mutations
        mutation_mask = state.mutation > 0
        if np.any(mutation_mask):
            data[mutation_mask] = self.colors['mutation']

        if np.any(state.zombie):
            data[state.zombie] = self.colors['zombie']

        if np.any(state.predator):
            data[state.predator] = self.colors['predator']

        # Black holes
        bh_mask = state.black_hole > 0
        if np.any(bh_mask):
            # Border: dilate black hole mask to get 3x3 or slightly larger area
            from scipy.ndimage import binary_dilation
            border_mask = binary_dilation(bh_mask, structure=np.ones((3,3)))
            data[border_mask] = self.colors['bh_border']
            data[bh_mask] = self.colors['bh']

        # Convert to QImage
        # QImage needs the data to be contiguous and stay alive
        qimg = QImage(data.data, w, h, w * 3, QImage.Format_RGB888)

        # Scale image to fit widget
        target_rect = self.rect()
        painter.drawImage(target_rect, qimg)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.draw_value = True
            self._handle_mouse(event.pos())
        elif event.button() == Qt.RightButton:
            self.drawing = True
            self.draw_value = False
            self._handle_mouse(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing:
            self._handle_mouse(event.pos())

    def mouseReleaseEvent(self, event):
        self.drawing = False

    def _handle_mouse(self, pos):
        # Map widget coordinates to grid coordinates
        x = int(pos.x() * self.engine.width / self.width())
        y = int(pos.y() * self.engine.height / self.height())
        self.engine.set_cell(x, y, self.draw_value)
        self.update()

class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.WINDOW_TITLE)
        self.resize(config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT)

        self.engine = GameEngine(config.DEFAULT_GRID_WIDTH, config.DEFAULT_GRID_HEIGHT)

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.set_tps(config.DEFAULT_TPS)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar
        sidebar = QScrollArea()
        sidebar.setFixedWidth(300)
        sidebar.setWidgetResizable(True)
        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)

        # Simulation Controls
        ctrl_group = self._create_group(config.STR_SETTINGS)
        self.btn_play = QPushButton(config.STR_PLAY)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; height: 40px;")

        btn_reset = QPushButton(config.STR_RESET)
        btn_reset.clicked.connect(self.reset_engine)

        btn_clear = QPushButton(config.STR_CLEAR)
        btn_clear.clicked.connect(self.clear_engine)

        btn_random = QPushButton(config.STR_RANDOMIZE)
        btn_random.clicked.connect(self.randomize_engine)

        ctrl_group.layout().addWidget(self.btn_play)
        ctrl_group.layout().addWidget(btn_reset)
        ctrl_group.layout().addWidget(btn_clear)
        ctrl_group.layout().addWidget(btn_random)

        # Speed Slider
        speed_label = QLabel(f"{config.STR_SPEED}: {config.DEFAULT_TPS}")
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(1, config.MAX_TPS)
        speed_slider.setValue(config.DEFAULT_TPS)
        speed_slider.valueChanged.connect(lambda v: (self.set_tps(v), speed_label.setText(f"{config.STR_SPEED}: {v}")))
        ctrl_group.layout().addWidget(speed_label)
        ctrl_group.layout().addWidget(speed_slider)

        # Grid Size
        size_label = QLabel(f"{config.STR_GRID_SIZE}: {self.engine.width}x{self.engine.height}")
        size_slider = QSlider(Qt.Horizontal)
        size_slider.setRange(50, 1000)
        size_slider.setValue(self.engine.width)
        size_slider.valueChanged.connect(self.change_grid_size)
        self.size_label = size_label
        ctrl_group.layout().addWidget(size_label)
        ctrl_group.layout().addWidget(size_slider)

        sidebar_layout.addWidget(ctrl_group)

        # Rules Cockpit
        rules_group = self._create_group(config.STR_RULES)
        for i in range(1, 11):
            cb = QCheckBox(config.RULES[i])
            cb.setToolTip(config.RULE_TOOLTIPS[i])
            cb.toggled.connect(lambda checked, idx=i: self.engine.toggle_rule(idx, checked))
            rules_group.layout().addWidget(cb)

        sidebar_layout.addWidget(rules_group)

        # Info Area
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #FFD700;")
        sidebar_layout.addWidget(self.info_label)

        sidebar_layout.addStretch()
        sidebar.setWidget(sidebar_content)

        # Grid Area
        self.grid_widget = GridWidget(self.engine)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.grid_widget, stretch=1)

    def _create_group(self, title):
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(group)
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(label)
        return group

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_play.setText(config.STR_PLAY)
            self.btn_play.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; height: 40px;")
        else:
            self.timer.start()
            self.btn_play.setText(config.STR_PAUSE)
            self.btn_play.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; height: 40px;")

    def set_tps(self, tps):
        self.timer.setInterval(1000 // tps)

    def tick(self):
        self.engine.step()
        self.grid_widget.update()

        # Update Info (Winter)
        if self.engine._is_winter() and self.engine.rules_enabled[6]:
            self.info_label.setText(config.STR_WINTER_ACTIVE)
        else:
            self.info_label.setText("")

    def reset_engine(self):
        self.engine.reset()
        self.grid_widget.update()

    def clear_engine(self):
        self.engine.state.alive.fill(False)
        self.engine.state.age.fill(0)
        self.grid_widget.update()

    def randomize_engine(self):
        self.engine.randomize()
        self.grid_widget.update()

    def change_grid_size(self, size):
        self.engine.reset(size, size)
        self.size_label.setText(f"{config.STR_GRID_SIZE}: {size}x{size}")
        self.grid_widget.update()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec())
