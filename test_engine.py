import unittest
import numpy as np
from engine import GameEngine

class TestGameEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(10, 10)

    def test_initialization(self):
        self.assertEqual(self.engine.width, 10)
        self.assertEqual(self.engine.height, 10)
        self.assertFalse(np.any(self.engine.state.alive))

    def test_set_cell(self):
        self.engine.set_cell(5, 5, True)
        self.assertTrue(self.engine.state.alive[5, 5])
        self.engine.set_cell(5, 5, False)
        self.assertFalse(self.engine.state.alive[5, 5])

    def test_conway_rules(self):
        # Blinker pattern (Horizontal)
        # x=1,2,3; y=2 => alive[2,1], alive[2,2], alive[2,3]
        self.engine.set_cell(1, 2, True)
        self.engine.set_cell(2, 2, True)
        self.engine.set_cell(3, 2, True)

        self.engine.step()

        # Should become vertical: x=2; y=1,2,3 => alive[1,2], alive[2,2], alive[3,2]
        self.assertTrue(self.engine.state.alive[1, 2])
        self.assertTrue(self.engine.state.alive[2, 2])
        self.assertTrue(self.engine.state.alive[3, 2])
        self.assertFalse(self.engine.state.alive[2, 1])
        self.assertFalse(self.engine.state.alive[2, 3])

    def test_torus_world(self):
        self.engine.toggle_rule(4, True) # Torus
        # Set cells at edges
        self.engine.set_cell(0, 0, True)
        self.engine.set_cell(0, 1, True)
        self.engine.set_cell(1, 0, True)

        # In a torus, (0,0) has neighbors at (9,0), (0,9), (9,9) etc.
        # Let's just check neighbor count at (0,0)
        nc = self.engine._count_neighbors(self.engine.state.alive)
        self.assertEqual(nc[0, 0], 2)

        # Birth at (9,9) if we set (0,0), (0,9), (9,0)
        self.engine.reset()
        self.engine.toggle_rule(4, True)
        self.engine.set_cell(0, 0, True)
        self.engine.set_cell(0, 9, True)
        self.engine.set_cell(9, 0, True)
        self.engine.step()
        self.assertTrue(self.engine.state.alive[9, 9])

    def test_aging(self):
        self.engine.toggle_rule(2, True)
        self.engine.set_cell(5, 5, True)
        # Create survival conditions (2 neighbors)
        self.engine.set_cell(5, 4, True)
        self.engine.set_cell(5, 6, True)

        for _ in range(16):
            self.engine.step()

        # At tick 16, it should be dead (it survived 15 ticks)
        self.assertFalse(self.engine.state.alive[5, 5])

if __name__ == '__main__':
    unittest.main()
