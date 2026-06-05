import sys
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QSlider, QLabel, QCheckBox, QFrame,
                             QSizePolicy, QGridLayout, QScrollArea, QComboBox)
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QSize, QRect
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPalette, QBrush

import config
from engine import GameEngine

class GridWidget(QWidget):
    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine
        self.setMouseTracking(True)
        self.drawing = False
        self.panning = False
        self.draw_value = True
        self.draw_layer = 'alive'

        # Viewport settings
        self.zoom = 1.0
        self.offset_x = 4500
        self.offset_y = 4500

        self.colors = {
            'bg': self._hex_to_rgb(config.COLOR_BACKGROUND),
            'alive': self._hex_to_rgb(config.COLOR_ALIVE),
            'sulfur': self._hex_to_rgb(config.COLOR_SULFUR),
            'salt': self._hex_to_rgb(config.COLOR_SALT),
            'fire': self._hex_to_rgb(config.COLOR_FIRE),
            'ghost': self._hex_to_rgb(config.COLOR_GHOST),
            'zombie': self._hex_to_rgb(config.COLOR_ZOMBIE),
            'predator': self._hex_to_rgb(config.COLOR_PREDATOR),
            'mutation': self._hex_to_rgb(config.COLOR_MUTATION if hasattr(config, 'COLOR_MUTATION') else '#FFD700'),
            'bh': self._hex_to_rgb(config.COLOR_BLACK_HOLE),
            'bh_border': self._hex_to_rgb(config.COLOR_BLACK_HOLE_BORDER)
        }

    def _hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.uint8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(config.COLOR_BACKGROUND))

        view_w = self.width()
        view_h = self.height()
        grid_scale = 1.0 / self.zoom

        grid_w = int(view_w * grid_scale)
        grid_h = int(view_h * grid_scale)

        # Clamp viewport but allow for small world
        max_ox = max(0, self.engine.width - grid_w)
        max_oy = max(0, self.engine.height - grid_h)
        self.offset_x = max(0, min(self.offset_x, max_ox))
        self.offset_y = max(0, min(self.offset_y, max_oy))

        # Visible slice
        x_end = min(self.offset_x + grid_w, self.engine.width)
        y_end = min(self.offset_y + grid_h, self.engine.height)

        slice_w = x_end - self.offset_x
        slice_h = y_end - self.offset_y

        if slice_w <= 0 or slice_h <= 0: return

        state = self.engine.state
        data = np.full((slice_h, slice_w, 3), self.colors['bg'], dtype=np.uint8)
        s = np.s_[self.offset_y:y_end, self.offset_x:x_end]

        # Apply layers (Lower priority to Higher)
        if np.any(state.ghost[s]): data[state.ghost[s]] = self.colors['ghost']
        if np.any(state.salt[s]): data[state.salt[s]] = self.colors['salt']
        if np.any(state.sulfur[s]): data[state.sulfur[s]] = self.colors['sulfur']

        if np.any(state.alive[s]):
            data[state.alive[s]] = self.colors['alive']

            # Sub-layers of alive
            mut_mask = (state.mutation[s] > 0) & state.alive[s]
            if np.any(mut_mask): data[mut_mask] = self.colors['mutation']

        if np.any(state.zombie[s]): data[state.zombie[s]] = self.colors['zombie']
        if np.any(state.predator[s]): data[state.predator[s]] = self.colors['predator']
        if np.any(state.fire[s] > 0): data[state.fire[s] > 0] = self.colors['fire']

        bh_mask = state.black_hole[s] > 0
        if np.any(bh_mask):
            from scipy.ndimage import binary_dilation
            border_mask = binary_dilation(bh_mask, structure=np.ones((3,3)))
            data[border_mask] = self.colors['bh_border']
            data[bh_mask] = self.colors['bh']

        qimg = QImage(data.data, slice_w, slice_h, slice_w * 3, QImage.Format_RGB888)

        # Target rect might be smaller if zoomed out very far
        target_w = int(slice_w * self.zoom)
        target_h = int(slice_h * self.zoom)
        painter.drawImage(QRect(0, 0, target_w, target_h), qimg)

        # HUD
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(10, 20, f"Position: {self.offset_x}, {self.offset_y} | Zoom: {self.zoom:.2f}x")
        painter.drawText(10, 40, "Rechtsklick + Ziehen zum Bewegen | Mausrad zum Zoomen")

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle > 0: self.zoom *= 1.2
        else: self.zoom /= 1.2
        self.zoom = max(0.01, min(self.zoom, 100.0))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self._handle_mouse(event.pos())
        elif event.button() == Qt.RightButton:
            self.last_mouse_pos = event.pos()
            self.panning = True

    def mouseMoveEvent(self, event):
        if self.drawing:
            self._handle_mouse(event.pos())
        elif self.panning:
            delta = event.pos() - self.last_mouse_pos
            self.offset_x -= int(delta.x() / self.zoom)
            self.offset_y -= int(delta.y() / self.zoom)
            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.drawing = False
        self.panning = False

    def _handle_mouse(self, pos):
        grid_x = self.offset_x + int(pos.x() / self.zoom)
        grid_y = self.offset_y + int(pos.y() / self.zoom)
        self.engine.set_cell(grid_x, grid_y, True, self.draw_layer)
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

        self.engine.randomize()
        self.toggle_play()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #050505; color: #d0d0d0;")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        sidebar = QScrollArea()
        sidebar.setFixedWidth(300)
        sidebar.setWidgetResizable(True)
        sidebar.setStyleSheet("border: none; background-color: #101010;")
        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)

        # Simulation Controls
        ctrl_group = self._create_group(config.STR_SETTINGS)
        self.btn_play = QPushButton(config.STR_PLAY)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("background-color: #1b5e20; color: white; font-weight: bold; height: 40px;")

        btn_reset = QPushButton(config.STR_RESET)
        btn_reset.clicked.connect(self.reset_engine)

        btn_random = QPushButton(config.STR_RANDOMIZE)
        btn_random.clicked.connect(self.randomize_engine)

        ctrl_group.layout().addWidget(self.btn_play)
        ctrl_group.layout().addWidget(btn_reset)
        ctrl_group.layout().addWidget(btn_random)
        sidebar_layout.addWidget(ctrl_group)

        # Alchemy Lab
        alchemy_group = self._create_group("Alchemie-Labor")
        self.combo_layer = QComboBox()
        self.combo_layer.addItems(["Quecksilber", "Schwefel", "Salz"])
        layer_map = {"Quecksilber": "alive", "Schwefel": "sulfur", "Salz": "salt"}
        self.combo_layer.currentTextChanged.connect(lambda t: setattr(self.grid_widget, 'draw_layer', layer_map[t]))
        alchemy_group.layout().addWidget(QLabel("Aktive Substanz:"))
        alchemy_group.layout().addWidget(self.combo_layer)

        btn_spawn = QPushButton("Substanz-Injektion")
        btn_spawn.clicked.connect(self.engine._spawn_seeds)
        alchemy_group.layout().addWidget(btn_spawn)
        sidebar_layout.addWidget(alchemy_group)

        # Rules Cockpit
        rules_group = self._create_group(config.STR_RULES)
        for i in range(1, 11):
            cb = QCheckBox(config.RULES[i])
            cb.setToolTip(config.RULE_TOOLTIPS[i])
            cb.toggled.connect(lambda checked, idx=i: self.engine.toggle_rule(idx, checked))
            rules_group.layout().addWidget(cb)
        sidebar_layout.addWidget(rules_group)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #ffeb3b;")
        sidebar_layout.addWidget(self.info_label)

        sidebar_layout.addStretch()
        sidebar.setWidget(sidebar_content)

        self.grid_widget = GridWidget(self.engine)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.grid_widget, stretch=1)

    def _create_group(self, title):
        group = QFrame()
        group.setStyleSheet("QFrame { background-color: #1a1a1a; border-radius: 5px; padding: 5px; margin-bottom: 5px; }")
        layout = QVBoxLayout(group)
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; color: #00e5ff;")
        layout.addWidget(label)
        return group

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_play.setText(config.STR_PLAY)
            self.btn_play.setStyleSheet("background-color: #1b5e20; color: white; font-weight: bold; height: 40px;")
        else:
            self.timer.start()
            self.btn_play.setText(config.STR_PAUSE)
            self.btn_play.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold; height: 40px;")

    def set_tps(self, tps):
        self.timer.setInterval(1000 // tps)

    def tick(self):
        self.engine.step()
        self.grid_widget.update()
        if self.engine._is_winter() and self.engine.rules_enabled[6]:
            self.info_label.setText(config.STR_WINTER_ACTIVE)
        else:
            self.info_label.setText("")

    def reset_engine(self):
        self.engine.reset()
        self.grid_widget.update()

    def randomize_engine(self):
        self.engine.randomize()
        self.grid_widget.update()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec())
