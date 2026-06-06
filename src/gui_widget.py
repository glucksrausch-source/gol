import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import Qt, QRect, QPoint
from src.constants import *

class GridWidget(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.viewport_x = 0
        self.viewport_y = 0
        self.cell_size = 5
        self.setMinimumSize(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)

        # Color lookup table for fast rendering
        self.color_lut = np.zeros((256, 3), dtype=np.uint8)
        self.color_lut[EntityType.EMPTY] = COLOR_EMPTY
        self.color_lut[EntityType.NORMAL] = COLOR_NORMAL
        self.color_lut[EntityType.ZOMBIE] = COLOR_ZOMBIE
        self.color_lut[EntityType.PREDATOR] = COLOR_PREDATOR
        self.color_lut[EntityType.GHOST] = COLOR_GHOST
        self.color_lut[EntityType.BLACK_HOLE] = COLOR_BLACK_HOLE
        self.color_lut[EntityType.MUTATED] = COLOR_MUTATED

        self.last_pos = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), Qt.black)

        # Calculate how many cells fit in the viewport
        w_cells = self.width() // self.cell_size + 1
        h_cells = self.height() // self.cell_size + 1

        state_slice, element_slice = self.engine.get_render_data(
            self.viewport_x, self.viewport_y, w_cells, h_cells
        )

        if state_slice.size == 0:
            return

        # Map state to RGB colors using LUT
        rgb_data = self.color_lut[state_slice]

        # Add element overlays or glow effects here if needed in the future

        # Create QImage from numpy array
        # Ensure contiguous memory
        rgb_data = np.ascontiguousarray(rgb_data)
        h, w, _ = rgb_data.shape
        bytes_per_line = 3 * w
        image = QImage(rgb_data.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Scale up image to match cell size
        scaled_image = image.scaled(w * self.cell_size, h * self.cell_size, Qt.KeepAspectRatio)

        painter.drawImage(0, 0, scaled_image)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = event.pos()
            self._handle_click(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if self.last_pos:
                # Calculate delta for panning if we were in pan mode, but let's implement drawing first
                self._handle_click(event.pos())
        elif event.buttons() & Qt.RightButton:
            # Panning
            if self.last_pos:
                delta = event.pos() - self.last_pos
                self.viewport_x -= delta.x() // self.cell_size
                self.viewport_y -= delta.y() // self.cell_size
                # Clamp viewport
                self.viewport_x = max(0, min(self.viewport_x, self.engine.width - self.width() // self.cell_size))
                self.viewport_y = max(0, min(self.viewport_y, self.engine.height - self.height() // self.cell_size))
                self.update()
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        self.last_pos = None

    def wheelEvent(self, event):
        # Zooming
        delta = event.angleDelta().y()
        if delta > 0:
            self.cell_size = min(20, self.cell_size + 1)
        else:
            self.cell_size = max(1, self.cell_size - 1)
        self.update()

    def _handle_click(self, pos):
        # Translate click to grid coordinates
        grid_x = self.viewport_x + pos.x() // self.cell_size
        grid_y = self.viewport_y + pos.y() // self.cell_size

        if 0 <= grid_x < self.engine.width and 0 <= grid_y < self.engine.height:
            # Toggle cell state for simplicity right now
            if self.engine.state[grid_y, grid_x] == EntityType.EMPTY:
                self.engine.state[grid_y, grid_x] = EntityType.NORMAL
            else:
                self.engine.state[grid_y, grid_x] = EntityType.EMPTY
            self.update()
