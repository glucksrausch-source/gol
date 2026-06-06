from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QSlider, QLabel, QCheckBox,
                               QScrollArea, QFrame, QGroupBox, QComboBox)
from PySide6.QtCore import Qt, QTimer
from src.gui_widget import GridWidget
from src.constants import EntityType, ElementType

class GameWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle("Alchemic Conway's Game of Life")

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)

        # Left Sidebar: Cockpit
        self.left_sidebar = QVBoxLayout()
        self.setup_cockpit()
        self.layout.addLayout(self.left_sidebar, 1)

        # Center: Grid
        self.grid_widget = GridWidget(self.engine)
        self.layout.addWidget(self.grid_widget, 4)

        # Right Sidebar: Alchemy Lab
        self.right_sidebar = QVBoxLayout()
        self.setup_alchemy_lab()
        self.layout.addLayout(self.right_sidebar, 1)

        # Timer for simulation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.is_playing = False

    def setup_cockpit(self):
        group_box = QGroupBox("10-Regeln-Cockpit")
        layout = QVBoxLayout()

        # Controls
        controls_layout = QHBoxLayout()
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_step = QPushButton("Step")
        self.btn_step.clicked.connect(self.update_simulation)
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self.reset_grid)
        self.btn_random = QPushButton("Randomize")
        self.btn_random.clicked.connect(self.randomize_grid)

        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_step)
        controls_layout.addWidget(self.btn_reset)
        controls_layout.addWidget(self.btn_random)
        layout.addLayout(controls_layout)

        # Speed Slider
        self.lbl_speed = QLabel("Speed (Ticks/sec): 10")
        layout.addWidget(self.lbl_speed)
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setMinimum(1)
        self.slider_speed.setMaximum(60)
        self.slider_speed.setValue(10)
        self.slider_speed.valueChanged.connect(self.update_speed)
        layout.addWidget(self.slider_speed)

        # 10 Rules Toggles
        rules = [
            ("zombie", "Regel 1: Zombies"),
            ("aging", "Regel 2: Zell-Alterung"),
            ("mutation", "Regel 3: Spontane Mutation"),
            ("torus", "Regel 4: Torus-Welt"),
            ("epidemic", "Regel 5: Epidemien"),
            ("climate", "Regel 6: Klima-Zyklen"),
            ("predator", "Regel 7: Räuber und Beute"),
            ("ghosts", "Regel 8: Geister-Spuren"),
            ("fertility", "Regel 9: Fruchtbarkeits-Boost"),
            ("black_hole", "Regel 10: Schwarze Löcher")
        ]

        for rule_id, rule_label in rules:
            cb = QCheckBox(rule_label)
            cb.toggled.connect(lambda checked, r=rule_id: self.engine.toggle_rule(r, checked))
            layout.addWidget(cb)

        group_box.setLayout(layout)
        self.left_sidebar.addWidget(group_box)
        self.left_sidebar.addStretch()

    def setup_alchemy_lab(self):
        group_box = QGroupBox("Alchemie-Labor")
        layout = QVBoxLayout()

        # Autopilot
        self.cb_autopilot = QCheckBox("Auto-Pilot (Ur-Suppe & Evolution)")
        self.cb_autopilot.toggled.connect(self.toggle_autopilot)
        layout.addWidget(self.cb_autopilot)

        # Brush Tool (Drop elements)
        layout.addWidget(QLabel("Brush Tool:"))
        self.combo_brush = QComboBox()
        self.combo_brush.addItems(["Cells", "Quicksilver", "Sulfur", "Salt"])
        layout.addWidget(self.combo_brush)

        # Element Shower
        self.btn_shower = QPushButton("Trigger Element Shower")
        layout.addWidget(self.btn_shower)

        # Status / active reactions
        layout.addWidget(QLabel("Active Reactions:"))
        self.lbl_reactions = QLabel("None")
        self.lbl_reactions.setStyleSheet("color: lightblue;")
        layout.addWidget(self.lbl_reactions)

        group_box.setLayout(layout)
        self.right_sidebar.addWidget(group_box)
        self.right_sidebar.addStretch()

    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("Pause")
            self.update_speed()
        else:
            self.btn_play.setText("Play")
            self.timer.stop()

    def update_speed(self):
        tps = self.slider_speed.value()
        self.lbl_speed.setText(f"Speed (Ticks/sec): {tps}")
        if self.is_playing:
            self.timer.start(1000 // tps)

    def update_simulation(self):
        self.engine.step()
        self.grid_widget.update()

    def reset_grid(self):
        self.engine.clear()
        self.grid_widget.update()

    def randomize_grid(self):
        self.engine.randomize()
        self.grid_widget.update()

    def toggle_autopilot(self, checked):
        self.engine.autopilot = checked
