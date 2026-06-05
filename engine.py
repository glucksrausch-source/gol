from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
import numpy as np
from scipy.ndimage import convolve, binary_dilation
import random

@dataclass
class EngineState:
    """Dataclass to hold the state of the simulation for better structure."""
    alive: np.ndarray
    age: np.ndarray
    mutation: np.ndarray
    zombie: np.ndarray
    ghost: np.ndarray
    predator: np.ndarray
    predator_starve: np.ndarray
    black_hole: np.ndarray
    block_static_count: np.ndarray
    tick_count: int = 0

class GameEngine:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.rules_enabled: Dict[int, bool] = {i: False for i in range(1, 11)}
        self.state: Optional[EngineState] = None
        self.reset(width, height)

    def reset(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        if width: self.width = width
        if height: self.height = height

        shape = (self.height, self.width)
        self.state = EngineState(
            alive=np.zeros(shape, dtype=bool),
            age=np.zeros(shape, dtype=np.int16),
            mutation=np.zeros(shape, dtype=np.int8),
            zombie=np.zeros(shape, dtype=bool),
            ghost=np.zeros(shape, dtype=bool),
            predator=np.zeros(shape, dtype=bool),
            predator_starve=np.zeros(shape, dtype=np.int8),
            black_hole=np.zeros(shape, dtype=np.int8),
            block_static_count=np.zeros(shape, dtype=np.int8),
            tick_count=0
        )

    def toggle_rule(self, rule_id: int, enabled: bool) -> None:
        self.rules_enabled[rule_id] = enabled
        if not enabled:
            if rule_id == 1: self.state.zombie.fill(False)
            if rule_id == 3: self.state.mutation.fill(0)
            if rule_id == 7:
                self.state.predator.fill(False)
                self.state.predator_starve.fill(0)
            if rule_id == 8: self.state.ghost.fill(False)
            if rule_id == 10:
                self.state.black_hole.fill(0)
                self.state.block_static_count.fill(0)

    def set_cell(self, x: int, y: int, value: bool) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.state.alive[y, x] = value
            if value:
                self.state.age[y, x] = 0
                self.state.zombie[y, x] = False
                self.state.ghost[y, x] = False
            else:
                self.state.age[y, x] = 0
                self.state.mutation[y, x] = 0

    def randomize(self) -> None:
        self.state.alive = np.random.choice([True, False], size=(self.height, self.width), p=[0.2, 0.8])
        self.state.age.fill(0)
        self.state.mutation.fill(0)
        self.state.zombie.fill(False)
        self.state.ghost.fill(False)
        self.state.predator.fill(False)
        self.state.black_hole.fill(0)
        if self.rules_enabled[7]:
            self.state.predator = np.random.choice([True, False], size=(self.height, self.width), p=[0.001, 0.999])

    def step(self) -> None:
        self.state.tick_count += 1

        # 1. Pre-Step
        self._handle_black_holes()
        self._handle_predators_vectorized()

        # 2. Umwelt-Checks
        dying_of_old_age = self._handle_aging()
        is_winter = self._is_winter()

        # 3. Conway-Core
        neighbor_count = self._count_neighbors(self.state.alive)

        if self.rules_enabled[9]:
            hf_mask = self.state.alive & (self.state.age > 10)
            hf_neighbors = self._count_neighbors(hf_mask)
        else:
            hf_neighbors = np.zeros_like(neighbor_count)

        if is_winter and self.rules_enabled[6]:
            survive = self.state.alive & (neighbor_count == 3)
        else:
            survive = self.state.alive & ((neighbor_count == 2) | (neighbor_count == 3))

        birth = (~self.state.alive) & (neighbor_count == 3)
        if self.rules_enabled[9]:
            birth |= (~self.state.alive) & (hf_neighbors == 2)

        if self.rules_enabled[8]:
            birth &= (~self.state.ghost)

        immune = (self.state.mutation > 0)
        new_alive = (survive | birth | immune) & (~dying_of_old_age)

        # 4. Post-Step
        just_died = self.state.alive & (~new_alive)

        if self.rules_enabled[5]:
            epidemic_mask = self._find_epidemic_mask(new_alive)
            new_alive[epidemic_mask] = False

        new_zombie = np.zeros_like(self.state.zombie)
        if self.rules_enabled[1]:
            lonely_death = just_died & (neighbor_count <= 1)
            self._apply_zombie_kills_vectorized(lonely_death, new_alive)
            new_zombie = lonely_death

        new_ghost = np.zeros_like(self.state.ghost)
        if self.rules_enabled[8]:
            new_ghost = just_died

        if self.rules_enabled[3]:
            newly_mutated = (birth & new_alive) & (np.random.random(new_alive.shape) < 0.02)
            self.state.mutation[newly_mutated] = 4

        if self.rules_enabled[10]:
            self._update_black_hole_generation()

        # Update State
        self.state.age[new_alive] += 1
        self.state.age[~new_alive] = 0
        self.state.mutation[self.state.mutation > 0] -= 1
        self.state.alive = new_alive
        self.state.zombie = new_zombie
        self.state.ghost = new_ghost

    def _count_neighbors(self, grid: np.ndarray) -> np.ndarray:
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int8)
        mode = 'wrap' if self.rules_enabled[4] else 'constant'
        return convolve(grid.astype(np.int8), kernel, mode=mode)

    def _is_winter(self) -> bool:
        cycle = (self.state.tick_count - 1) % 50
        return 0 <= cycle < 10

    def _handle_aging(self) -> np.ndarray:
        if self.rules_enabled[2]:
            return self.state.alive & (self.state.age >= 15)
        return np.zeros_like(self.state.alive)

    def _handle_black_holes(self) -> None:
        if not self.rules_enabled[10]: return
        active_bh = self.state.black_hole > 0
        if np.any(active_bh):
            radius = 3
            y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
            struct = x**2 + y**2 <= radius**2
            sucked_mask = binary_dilation(active_bh, structure=struct)
            self.state.alive[sucked_mask] = False
            self.state.predator[sucked_mask] = False
            self.state.mutation[sucked_mask] = 0
        self.state.black_hole[active_bh] -= 1

    def _update_black_hole_generation(self) -> None:
        kernel = np.array([[1, 1], [1, 1]])
        counts = convolve(self.state.alive.astype(np.int8), kernel, mode='constant', origin=(-1,-1))
        is_block = (counts == 4)
        self.state.block_static_count[is_block] += 1
        self.state.block_static_count[~is_block] = 0
        collapsing = (self.state.block_static_count >= 20)
        if np.any(collapsing):
            self.state.black_hole[collapsing] = 5
            to_kill = binary_dilation(collapsing, structure=kernel, origin=(-1,-1))
            self.state.alive[to_kill] = False
            self.state.block_static_count[collapsing] = 0

    def _handle_predators_vectorized(self) -> None:
        if not self.rules_enabled[7] or not np.any(self.state.predator): return

        # Pick one of 8 directions randomly for ALL predators
        dy, dx = random.choice([(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)])

        # Shift the entire predator grid
        # Using np.roll for torus, otherwise manual slicing for constant
        if self.rules_enabled[4]:
            new_predator = np.roll(np.roll(self.state.predator, dy, axis=0), dx, axis=1)
            new_starve = np.roll(np.roll(self.state.predator_starve, dy, axis=0), dx, axis=1)
        else:
            new_predator = np.zeros_like(self.state.predator)
            new_starve = np.zeros_like(self.state.predator_starve)

            # Source slice
            y_start, y_end = max(0, -dy), min(self.height, self.height - dy)
            x_start, x_end = max(0, -dx), min(self.width, self.width - dx)
            # Target slice
            ty_start, ty_end = max(0, dy), min(self.height, self.height + dy)
            tx_start, tx_end = max(0, dx), min(self.width, self.width + dx)

            new_predator[ty_start:ty_end, tx_start:tx_end] = self.state.predator[y_start:y_end, x_start:x_end]
            new_starve[ty_start:ty_end, tx_start:tx_end] = self.state.predator_starve[y_start:y_end, x_start:x_end]

        # Eating and Starving
        ate_mask = new_predator & self.state.alive
        self.state.alive[ate_mask] = False

        new_starve[ate_mask] = 0
        new_starve[new_predator & ~ate_mask] += 1

        # Kill starving predators
        still_alive_predators = new_predator & (new_starve < 3)

        self.state.predator = still_alive_predators
        self.state.predator_starve[still_alive_predators] = new_starve[still_alive_predators]
        self.state.predator_starve[~still_alive_predators] = 0

    def _apply_zombie_kills_vectorized(self, zombie_mask: np.ndarray, target_grid: np.ndarray) -> None:
        if not np.any(zombie_mask): return
        # A zombie kills one RANDOM neighbor.
        # Vectorized approach: check each of 8 directions.
        # To make it "random", we'll shuffle the directions we check.
        offsets = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        random.shuffle(offsets)

        zombies_still_need_to_kill = zombie_mask.copy()

        for dy, dx in offsets:
            if not np.any(zombies_still_need_to_kill): break

            # Find neighbors in this direction
            if self.rules_enabled[4]:
                neighbor_alive = np.roll(np.roll(target_grid, dy, axis=0), dx, axis=1)
            else:
                # Same slicing as predator move but for checking
                neighbor_alive = np.zeros_like(target_grid)
                y_s, y_e = max(0, -dy), min(self.height, self.height - dy)
                x_s, x_e = max(0, -dx), min(self.width, self.width - dx)
                ty_s, ty_e = max(0, dy), min(self.height, self.height + dy)
                tx_s, tx_e = max(0, dx), min(self.width, self.width + dx)
                neighbor_alive[ty_s:ty_e, tx_s:tx_e] = target_grid[y_s:y_e, x_s:x_e]

            # Potential kills for the zombies that haven't killed yet
            killable = zombies_still_need_to_kill & neighbor_alive
            if np.any(killable):
                # Kill them in the target grid (need to reverse shift)
                if self.rules_enabled[4]:
                    target_grid[np.roll(np.roll(killable, -dy, axis=0), -dx, axis=1)] = False
                else:
                    target_grid[y_s:y_e, x_s:x_e] &= ~killable[ty_s:ty_e, tx_s:tx_e]

                # These zombies are done
                zombies_still_need_to_kill &= ~killable

    def _find_epidemic_mask(self, grid: np.ndarray) -> np.ndarray:
        kernel = np.ones((3, 3), dtype=np.int8)
        counts = convolve(grid.astype(np.int8), kernel, mode='constant')
        centers = (counts == 9)
        return binary_dilation(centers, structure=kernel) if np.any(centers) else np.zeros_like(grid)
