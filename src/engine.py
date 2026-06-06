import numpy as np
from scipy.signal import convolve2d
from src.constants import *
import random

class GameEngine:
    def __init__(self, width=GRID_WIDTH, height=GRID_HEIGHT):
        self.width = width
        self.height = height

        # Parallel arrays for performance
        self.state = np.zeros((height, width), dtype=np.uint8)
        self.element = np.zeros((height, width), dtype=np.uint8)

        self.age = np.zeros((height, width), dtype=np.uint16)
        self.static_timer = np.zeros((height, width), dtype=np.uint16)
        self.mutation_timer = np.zeros((height, width), dtype=np.uint8)
        self.last_fed = np.zeros((height, width), dtype=np.uint16)
        self.ghost_timer = np.zeros((height, width), dtype=np.uint8)
        self.black_hole_timer = np.zeros((height, width), dtype=np.uint8)

        self.ticks = 0

        # Rules toggles
        self.rules = {
            "zombie": False,
            "aging": False,
            "mutation": False,
            "torus": False,
            "epidemic": False,
            "climate": False,
            "predator": False,
            "ghosts": False,
            "fertility": False,
            "black_hole": False
        }

        self.autopilot = False

        # Pre-allocate convolution kernel
        self.kernel = np.array([[1, 1, 1],
                                [1, 0, 1],
                                [1, 1, 1]], dtype=np.uint8)

    def toggle_rule(self, rule_name, state):
        if rule_name in self.rules:
            self.rules[rule_name] = state

    def clear(self):
        self.state.fill(EntityType.EMPTY)
        self.element.fill(ElementType.NONE)
        self.age.fill(0)
        self.static_timer.fill(0)
        self.mutation_timer.fill(0)
        self.last_fed.fill(0)
        self.ghost_timer.fill(0)
        self.black_hole_timer.fill(0)
        self.ticks = 0

    def randomize(self, density=0.1):
        self.clear()
        mask = np.random.rand(self.height, self.width) < density
        self.state[mask] = EntityType.NORMAL

    def step(self):
        self.ticks += 1

        # 1. Neighbor counting
        # For Game of Life, we only count normal cells, zombies, mutants, etc.
        # Ghosts and Black holes might affect this differently based on rules, but let's stick to basic counts first.
        alive_mask = (self.state == EntityType.NORMAL) | (self.state == EntityType.ZOMBIE) | (self.state == EntityType.MUTATED) | (self.state == EntityType.PREDATOR)

        # Determine mode for convolution
        mode = 'wrap' if self.rules["torus"] else 'same'

        if mode == 'wrap':
            # scipy convolve2d 'wrap' isn't natively supported with boundary='wrap', we use boundary='wrap' in convolve2d
            neighbors = convolve2d(alive_mask.astype(np.uint8), self.kernel, mode='same', boundary='wrap')
        else:
            neighbors = convolve2d(alive_mask.astype(np.uint8), self.kernel, mode='same', boundary='fill', fillvalue=0)

        # 2. Rule 6: Climate Cycles (Winter)
        winter = False
        if self.rules["climate"]:
            cycle = self.ticks % 50
            if cycle >= 40:
                winter = True

        # 3. Base Conway Rules
        # B3/S23
        # If winter, S3 (survival requires exactly 3 neighbors)
        survive_min = 3 if winter else 2
        survive_max = 3
        birth_req = 3

        # Apply standard Conway rules to normal cells
        is_empty = self.state == EntityType.EMPTY
        is_alive = (self.state == EntityType.NORMAL) | (self.state == EntityType.MUTATED)

        # Birth
        birth_mask = is_empty & (neighbors == birth_req)

        # Rule 8: Ghosts
        if self.rules["ghosts"]:
            birth_mask &= (self.ghost_timer == 0)

        # Rule 9: Fertility Boost
        if self.rules["fertility"]:
            highly_fertile = (self.state == EntityType.NORMAL) & (self.age > 10)
            if mode == 'wrap':
                fertile_neighbors = convolve2d(highly_fertile.astype(np.uint8), self.kernel, mode='same', boundary='wrap')
            else:
                fertile_neighbors = convolve2d(highly_fertile.astype(np.uint8), self.kernel, mode='same', boundary='fill', fillvalue=0)

            fertility_birth = is_empty & (fertile_neighbors == 2)
            if self.rules["ghosts"]:
                fertility_birth &= (self.ghost_timer == 0)
            birth_mask |= fertility_birth

        # Survival
        survive_mask = is_alive & (neighbors >= survive_min) & (neighbors <= survive_max)

        # Death
        death_mask = is_alive & ~survive_mask

        # Rule 1: Zombies
        zombie_mask = np.zeros_like(self.state, dtype=bool)
        if self.rules["zombie"]:
            # Death by loneliness -> Zombie
            lonely_death = is_alive & (neighbors < survive_min)
            zombie_mask = lonely_death
            # Remove from standard death
            death_mask &= ~lonely_death

        # Update age and static timer
        self.age[survive_mask] += 1

        # Rule 2: Aging
        if self.rules["aging"]:
            old_age_mask = (self.age >= 15) & is_alive
            death_mask |= old_age_mask

        # Rule 3: Mutation
        new_mutants_mask = np.zeros_like(self.state, dtype=bool)
        if self.rules["mutation"]:
            mutation_chance = np.random.rand(self.height, self.width) < 0.02
            new_mutants_mask = birth_mask & mutation_chance
            birth_mask &= ~new_mutants_mask

            # Mutated immunity
            immune = self.mutation_timer > 0
            death_mask &= ~immune
            self.mutation_timer[immune] -= 1

            # Revert mutant to normal when timer expires
            expired_mutant = (self.state == EntityType.MUTATED) & (self.mutation_timer == 0)
            self.state[expired_mutant] = EntityType.NORMAL

        # Apply deaths
        self.state[death_mask] = EntityType.EMPTY
        self.age[death_mask] = 0

        # Update state for previous step's Black Holes and Predators
        # Handled in their respective blocks later.

        # Determine static blocks for Black Holes BEFORE changing state
        if self.rules["black_hole"]:
            # Check if state is identical to previous
            # Actually, Black holes require a static 2x2 block. This is highly complex for pure numpy without tracking previous state exactly.
            # Simplified approach: If a cell hasn't changed age (meaning it survived) and hasn't moved, we increment static timer.
            # We just track static individual cells for now to represent the "idea" of static matter collapsing.
            # If a 2x2 block of static timer >= 20 is found, collapse it.
            self.static_timer[survive_mask] += 1
            self.static_timer[~survive_mask] = 0

        # Handle ghost creation
        if self.rules["ghosts"]:
            self.ghost_timer[self.ghost_timer > 0] -= 1
            self.ghost_timer[death_mask] = 1 # Ghosts last 1 tick
            self.state[(self.ghost_timer == 1) & (self.state == EntityType.EMPTY)] = EntityType.GHOST

        # Apply Zombies
        if self.rules["zombie"]:
            # Zombies from previous tick disappear
            old_zombies = self.state == EntityType.ZOMBIE
            self.state[old_zombies] = EntityType.EMPTY

            # New zombies
            self.state[zombie_mask] = EntityType.ZOMBIE
            self.age[zombie_mask] = 0

            # Zombies kill random neighbor
            # Convolve zombies to find normal cells near them
            if np.any(zombie_mask):
                if mode == 'wrap':
                    zombie_neighbors = convolve2d(zombie_mask.astype(np.uint8), self.kernel, mode='same', boundary='wrap')
                else:
                    zombie_neighbors = convolve2d(zombie_mask.astype(np.uint8), self.kernel, mode='same', boundary='fill', fillvalue=0)

                # Cells next to zombies are killed
                killed_by_zombies = is_alive & (zombie_neighbors > 0)
                self.state[killed_by_zombies] = EntityType.EMPTY
                self.age[killed_by_zombies] = 0

        # Apply births
        self.state[birth_mask] = EntityType.NORMAL
        self.age[birth_mask] = 0

        # Apply mutants
        self.state[new_mutants_mask] = EntityType.MUTATED
        self.mutation_timer[new_mutants_mask] = 3
        self.age[new_mutants_mask] = 0

        # Rule 5: Epidemics
        if self.rules["epidemic"]:
            # Find 3x3 blocks of 9 living cells
            # Convolve with a 3x3 kernel of 1s
            if mode == 'wrap':
                density = convolve2d(is_alive.astype(np.uint8), np.ones((3,3)), mode='same', boundary='wrap')
            else:
                density = convolve2d(is_alive.astype(np.uint8), np.ones((3,3)), mode='same', boundary='fill', fillvalue=0)

            epidemic_centers = density == 9
            if np.any(epidemic_centers):
                # We need to kill all 9 cells around these centers.
                # Convolve again to spread the death mask
                if mode == 'wrap':
                    epidemic_kill = convolve2d(epidemic_centers.astype(np.uint8), np.ones((3,3)), mode='same', boundary='wrap') > 0
                else:
                    epidemic_kill = convolve2d(epidemic_centers.astype(np.uint8), np.ones((3,3)), mode='same', boundary='fill', fillvalue=0) > 0

                self.state[epidemic_kill] = EntityType.EMPTY
                self.age[epidemic_kill] = 0

        # Rule 7: Predators
        if self.rules["predator"]:
            predators = np.argwhere(self.state == EntityType.PREDATOR)
            for y, x in predators:
                self.last_fed[y, x] += 1
                if self.last_fed[y, x] >= 3:
                    self.state[y, x] = EntityType.EMPTY
                    self.last_fed[y, x] = 0
                else:
                    # Move randomly
                    dy, dx = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)])
                    ny, nx = y + dy, x + dx
                    if mode == 'wrap':
                        ny %= self.height
                        nx %= self.width

                    if 0 <= ny < self.height and 0 <= nx < self.width:
                        # Eat if normal
                        if self.state[ny, nx] == EntityType.NORMAL:
                            self.state[ny, nx] = EntityType.PREDATOR
                            self.last_fed[ny, nx] = 0
                            self.state[y, x] = EntityType.EMPTY
                            self.last_fed[y, x] = 0
                        elif self.state[ny, nx] == EntityType.EMPTY:
                            self.state[ny, nx] = EntityType.PREDATOR
                            self.last_fed[ny, nx] = self.last_fed[y, x]
                            self.state[y, x] = EntityType.EMPTY
                            self.last_fed[y, x] = 0

        # Rule 10: Black Holes
        if self.rules["black_hole"]:
            # Find 2x2 blocks of highly static cells (timer >= 20)
            is_static = self.static_timer >= 20
            if np.any(is_static):
                if mode == 'wrap':
                    static_density = convolve2d(is_static.astype(np.uint8), np.ones((2,2)), mode='same', boundary='wrap')
                else:
                    static_density = convolve2d(is_static.astype(np.uint8), np.ones((2,2)), mode='same', boundary='fill', fillvalue=0)

                bh_centers = np.argwhere(static_density == 4)
                for by, bx in bh_centers:
                    self.state[by, bx] = EntityType.BLACK_HOLE
                    self.black_hole_timer[by, bx] = 5
                    self.static_timer[by, bx] = 0

            # Process existing black holes
            bhs = np.argwhere(self.state == EntityType.BLACK_HOLE)
            for by, bx in bhs:
                if self.black_hole_timer[by, bx] > 0:
                    # Suck in cells within radius 3
                    # Simplified: 7x7 block
                    y1, y2 = max(0, by - 3), min(self.height, by + 4)
                    x1, x2 = max(0, bx - 3), min(self.width, bx + 4)

                    # Kill everything in radius except the black hole itself
                    mask = np.ones((y2-y1, x2-x1), dtype=bool)
                    center_y, center_x = min(by, 3), min(bx, 3) # relative to slice
                    # If near edge, center might shift
                    mask[by-y1, bx-x1] = False

                    self.state[y1:y2, x1:x2][mask] = EntityType.EMPTY
                    self.age[y1:y2, x1:x2][mask] = 0

                    self.black_hole_timer[by, bx] -= 1
                else:
                    self.state[by, bx] = EntityType.EMPTY

        # ALCHEMY SYSTEM
        if self.autopilot:
            # Ur-Suppen-Spawner: randomly spawn elements and cells
            if np.random.rand() < 0.1: # 10% chance per tick to spawn something
                rx, ry = np.random.randint(0, self.width), np.random.randint(0, self.height)
                self.state[ry, rx] = EntityType.NORMAL
                self.element[ry, rx] = np.random.choice([ElementType.QUICKSILVER, ElementType.SULFUR, ElementType.SALT])

            if np.random.rand() < 0.01: # Rare Predator spawn
                rx, ry = np.random.randint(0, self.width), np.random.randint(0, self.height)
                self.state[ry, rx] = EntityType.PREDATOR

            # Process Alchemy Reactions
            # Quicksilver + Sulfur + adjacent = Zombie
            qs_mask = self.element == ElementType.QUICKSILVER
            su_mask = self.element == ElementType.SULFUR

            # Simple vector check: If a normal cell is near quicksilver and sulfur
            if np.any(qs_mask) and np.any(su_mask):
                if mode == 'wrap':
                    qs_near = convolve2d(qs_mask.astype(np.uint8), self.kernel, mode='same', boundary='wrap') > 0
                    su_near = convolve2d(su_mask.astype(np.uint8), self.kernel, mode='same', boundary='wrap') > 0
                else:
                    qs_near = convolve2d(qs_mask.astype(np.uint8), self.kernel, mode='same', boundary='fill', fillvalue=0) > 0
                    su_near = convolve2d(su_mask.astype(np.uint8), self.kernel, mode='same', boundary='fill', fillvalue=0) > 0

                alchemy_zombies = (self.state == EntityType.NORMAL) & qs_near & su_near
                self.state[alchemy_zombies] = EntityType.ZOMBIE

                # Consume elements
                self.element[alchemy_zombies] = ElementType.NONE

    def get_render_data(self, x, y, w, h):
        # Extract a slice of the grid for rendering
        # Ensure bounds are within the grid
        x1 = max(0, min(x, self.width))
        y1 = max(0, min(y, self.height))
        x2 = max(0, min(x + w, self.width))
        y2 = max(0, min(y + h, self.height))

        return self.state[y1:y2, x1:x2], self.element[y1:y2, x1:x2]
