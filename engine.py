from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
import numpy as np
from scipy.ndimage import convolve, binary_dilation
import random

@dataclass
class EngineState:
    """Dataclass to hold the state of the simulation for better structure."""
    alive: np.ndarray  # Mercury (Blue/Cyan)
    sulfur: np.ndarray # Sulfur (Red)
    salt: np.ndarray   # Salt (White)
    fire: np.ndarray   # Fire (Gold)
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
            sulfur=np.zeros(shape, dtype=bool),
            salt=np.zeros(shape, dtype=bool),
            fire=np.zeros(shape, dtype=np.int8),
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

    def set_cell(self, x: int, y: int, value: bool, layer: str = 'alive', brush_size: int = 1) -> None:
        half_brush = brush_size // 2
        y_min = max(0, y - half_brush)
        y_max = min(self.height, y + half_brush + (brush_size % 2))
        x_min = max(0, x - half_brush)
        x_max = min(self.width, x + half_brush + (brush_size % 2))

        if y_min < y_max and x_min < x_max:
            target = getattr(self.state, layer)
            if target.dtype == bool:
                target[y_min:y_max, x_min:x_max] = value
            else:
                target[y_min:y_max, x_min:x_max] = 5 if value else 0
            if value and layer == 'alive':
                self.state.age[y_min:y_max, x_min:x_max] = 0

    def get_alive_count(self) -> int:
        return np.count_nonzero(self.state.alive)

    def randomize(self) -> None:
        shape = (self.height, self.width)
        self.state.alive.fill(False)
        # Sparse cluster-based randomization for performance on 10k
        c_size = min(100, self.width, self.height)
        for _ in range(50):
            rx = random.randint(0, max(0, self.width - c_size))
            ry = random.randint(0, max(0, self.height - c_size))
            self.state.alive[ry:ry+c_size, rx:rx+c_size] |= (np.random.random((c_size, c_size)) < 0.2)

        self.state.sulfur.fill(False)
        self.state.salt.fill(False)
        self.state.age.fill(0)
        self.state.mutation.fill(0)
        self.state.zombie.fill(False)
        self.state.ghost.fill(False)
        self.state.predator.fill(False)
        self.state.black_hole.fill(0)

        if self.rules_enabled[7]:
            for _ in range(10):
                rx = random.randint(0, max(0, self.width - 20))
                ry = random.randint(0, max(0, self.height - 20))
                self.state.predator[ry:ry+20, rx:rx+20] = (np.random.random((20, 20)) < 0.1)

    def step(self) -> None:
        self.state.tick_count += 1

        # Calculate bounding box to dramatically reduce calculation size
        bounds = self._get_active_bounds()
        if bounds is None:
            # Nothing active, just process tick-based spawns and fading effects
            if self.state.tick_count % 10 == 0:
                self._spawn_seeds()
            self.state.fire[self.state.fire > 0] -= 1
            if self.rules_enabled[8]:
                self.state.ghost.fill(False)
            return

        rmin, rmax, cmin, cmax = bounds
        slice_obj = np.s_[rmin:rmax, cmin:cmax]

        # 0. Autonomous Spawning
        if self.state.tick_count % 10 == 0:
            self._spawn_seeds()

        # 1. Pre-Step Rules
        self._handle_black_holes()
        self._handle_predators_vectorized()
        self._handle_alchemy()

        # 2. Umwelt-Checks
        is_winter = self._is_winter()
        dying_of_old_age = self._handle_aging()

        # 3. Conway Core (Mercury/Alive)
        if np.any(self.state.alive[slice_obj]):
            # Use bounded area for neighbors
            neighbor_count_sub = self._count_neighbors(self.state.alive, slice_obj)
            neighbor_count = np.zeros_like(self.state.alive, dtype=np.int8)
            neighbor_count[slice_obj] = neighbor_count_sub

            # Rule 9: Fertility Boost
            if self.rules_enabled[9]:
                hf_mask = self.state.alive & (self.state.age > 10)
                hf_neighbors_sub = self._count_neighbors(hf_mask, slice_obj)
                hf_neighbors = np.zeros_like(neighbor_count)
                hf_neighbors[slice_obj] = hf_neighbors_sub
            else:
                hf_neighbors = np.zeros_like(neighbor_count)

            # Core Logic
            if is_winter and self.rules_enabled[6]:
                survive = self.state.alive & (neighbor_count == 3)
            else:
                survive = self.state.alive & ((neighbor_count == 2) | (neighbor_count == 3))

            birth = (~self.state.alive) & (neighbor_count == 3)
            if self.rules_enabled[9]:
                birth |= (~self.state.alive) & (hf_neighbors == 2)

            # Rule 8: Ghost tracks block birth
            if self.rules_enabled[8]:
                birth &= (~self.state.ghost)

            # Rule 3: Mutation (Immunity)
            immune = (self.state.mutation > 0)

            new_alive = (survive | birth | immune) & (~dying_of_old_age)

            # 4. Post-Step Logic
            just_died = self.state.alive & (~new_alive)

            # Rule 5: Epidemics
            if self.rules_enabled[5]:
                epidemic_mask = self._find_epidemic_mask(new_alive)
                new_alive[epidemic_mask] = False

            # Rule 1: Zombies
            new_zombie = np.zeros_like(self.state.zombie)
            if self.rules_enabled[1]:
                lonely_death = just_died & (neighbor_count <= 1)
                self._apply_zombie_kills_vectorized(lonely_death, new_alive)
                new_zombie = lonely_death

            # Rule 8: Ghost
            new_ghost = np.zeros_like(self.state.ghost)
            if self.rules_enabled[8]:
                new_ghost = just_died

            # Rule 3: Mutation generation
            if self.rules_enabled[3]:
                newly_mutated = (birth & new_alive) & (np.random.random(new_alive.shape) < 0.02)
                self.state.mutation[newly_mutated] = 4

            if self.rules_enabled[10]:
                self._update_black_hole_generation()

            # Apply updates
            self.state.age[new_alive] += 1
            self.state.age[~new_alive] = 0
            self.state.mutation[self.state.mutation > 0] -= 1
            self.state.alive = new_alive
            self.state.zombie = new_zombie
            self.state.ghost = new_ghost

        # 5. Secondary Elements (Sulfur & Salt)
        if np.any(self.state.sulfur[slice_obj]):
            sn_sub = self._count_neighbors(self.state.sulfur, slice_obj)
            sn = np.zeros_like(self.state.sulfur, dtype=np.int8)
            sn[slice_obj] = sn_sub
            self.state.sulfur = (self.state.sulfur & (sn > 0) & (sn < 5)) | ((~self.state.sulfur) & (sn == 3))

        if np.any(self.state.salt[slice_obj]):
            san_sub = self._count_neighbors(self.state.salt, slice_obj)
            san = np.zeros_like(self.state.salt, dtype=np.int8)
            san[slice_obj] = san_sub
            self.state.salt = (self.state.salt & (san >= 2) & (san <= 3)) | ((~self.state.salt) & (san == 3))

        self.state.fire[self.state.fire > 0] -= 1

    def _spawn_seeds(self) -> None:
        size = min(20, self.width, self.height)
        if size < 1: return
        for _ in range(5):
            x = random.randint(0, max(0, self.width - size))
            y = random.randint(0, max(0, self.height - size))
            seed_type = random.choice(['alive', 'sulfur', 'salt'])
            pattern = np.random.random((size, size)) < 0.4
            if seed_type == 'alive':
                self.state.alive[y:y+size, x:x+size] |= pattern
            elif seed_type == 'sulfur':
                self.state.sulfur[y:y+size, x:x+size] |= pattern
            else:
                self.state.salt[y:y+size, x:x+size] |= pattern

    def _handle_alchemy(self) -> None:
        # Sulfur + Alive = Fire
        reaction_mask = self.state.sulfur & self.state.alive
        if np.any(reaction_mask):
            self.state.fire[reaction_mask] = 10
            self.state.sulfur[reaction_mask] = False
            self.state.alive[reaction_mask] = False

        # Salt + Fire = Explosion (Creates life)
        explosion_mask = self.state.salt & (self.state.fire > 0)
        if np.any(explosion_mask):
            self.state.alive[explosion_mask] = True
            self.state.salt[explosion_mask] = False

    def _get_active_bounds(self) -> Optional[Tuple[int, int, int, int]]:
        """Returns the bounding box (rmin, rmax, cmin, cmax) of active cells to optimize calculations."""
        # Simple mask of what we consider "active" for bounding box purposes
        active = self.state.alive | self.state.sulfur | self.state.salt | self.state.zombie | self.state.predator
        if self.rules_enabled[10]:
            active |= (self.state.black_hole > 0)

        rows = np.any(active, axis=1)
        if not np.any(rows):
            return None
        cols = np.any(active, axis=0)

        rmin, rmax = int(np.argmax(rows)), int(len(rows) - np.argmax(rows[::-1]))
        cmin, cmax = int(np.argmax(cols)), int(len(cols) - np.argmax(cols[::-1]))

        # Add padding to allow expansion
        pad = 5
        rmin = max(0, rmin - pad)
        rmax = min(self.height, rmax + pad)
        cmin = max(0, cmin - pad)
        cmax = min(self.width, cmax + pad)

        # In torus world (Rule 4), we just process the whole grid if wrapping is enabled
        # and things get too close to the edges to avoid complex boundary math.
        if self.rules_enabled[4] and (rmin == 0 or rmax == self.height or cmin == 0 or cmax == self.width):
            return 0, self.height, 0, self.width

        return rmin, rmax, cmin, cmax

    def _count_neighbors(self, grid: np.ndarray, slice_obj: Optional[Tuple[slice, slice]] = None) -> np.ndarray:
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int8)
        mode = 'wrap' if self.rules_enabled[4] else 'constant'

        if slice_obj is not None:
            subgrid = grid[slice_obj].astype(np.int8)
            return convolve(subgrid, kernel, mode=mode)

        return convolve(grid.astype(np.int8), kernel, mode=mode)

    def _is_winter(self) -> bool:
        return 0 <= ((self.state.tick_count - 1) % 50) < 10

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
            self.state.sulfur[sucked_mask] = False
            self.state.salt[sucked_mask] = False
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
        dy, dx = random.choice([(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)])
        if self.rules_enabled[4]:
            new_predator = np.roll(np.roll(self.state.predator, dy, axis=0), dx, axis=1)
            new_starve = np.roll(np.roll(self.state.predator_starve, dy, axis=0), dx, axis=1)
        else:
            new_predator = np.zeros_like(self.state.predator)
            new_starve = np.zeros_like(self.state.predator_starve)
            y_s, y_e = max(0, -dy), min(self.height, self.height - dy)
            x_s, x_e = max(0, -dx), min(self.width, self.width - dx)
            ty_s, ty_e = max(0, dy), min(self.height, self.height + dy)
            tx_s, tx_e = max(0, dx), min(self.width, self.width + dx)
            new_predator[ty_s:ty_e, tx_s:tx_e] = self.state.predator[y_s:y_e, x_s:x_e]
            new_starve[ty_s:ty_e, tx_s:tx_e] = self.state.predator_starve[y_s:y_e, x_s:x_e]
        ate_mask = new_predator & self.state.alive
        self.state.alive[ate_mask] = False
        new_starve[ate_mask] = 0
        new_starve[new_predator & ~ate_mask] += 1
        alive_p = new_predator & (new_starve < 3)
        self.state.predator = alive_p
        self.state.predator_starve[alive_p] = new_starve[alive_p]
        self.state.predator_starve[~alive_p] = 0

    def _apply_zombie_kills_vectorized(self, mask: np.ndarray, target: np.ndarray) -> None:
        if not np.any(mask): return
        offsets = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        random.shuffle(offsets)
        remaining = mask.copy()
        for dy, dx in offsets:
            if not np.any(remaining): break
            if self.rules_enabled[4]:
                nb = np.roll(np.roll(target, dy, axis=0), dx, axis=1)
            else:
                nb = np.zeros_like(target)
                y_s, y_e = max(0, -dy), min(self.height, self.height - dy)
                x_s, x_e = max(0, -dx), min(self.width, self.width - dx)
                ty_s, ty_e = max(0, dy), min(self.height, self.height + dy)
                tx_s, tx_e = max(0, dx), min(self.width, self.width + dx)
                nb[ty_s:ty_e, tx_s:tx_e] = target[y_s:y_e, x_s:x_e]
            killable = remaining & nb
            if np.any(killable):
                if self.rules_enabled[4]:
                    target[np.roll(np.roll(killable, -dy, axis=0), -dx, axis=1)] = False
                else:
                    target[y_s:y_e, x_s:x_e] &= ~killable[ty_s:ty_e, tx_s:tx_e]
                remaining &= ~killable

    def _find_epidemic_mask(self, grid: np.ndarray) -> np.ndarray:
        kernel = np.ones((3, 3), dtype=np.int8)
        counts = convolve(grid.astype(np.int8), kernel, mode='constant')
        centers = (counts == 9)
        return binary_dilation(centers, structure=kernel) if np.any(centers) else np.zeros_like(grid)
