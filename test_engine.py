import numpy as np
import pytest
from src.engine import GameEngine
from src.constants import EntityType

def test_engine_init():
    engine = GameEngine(10, 10)
    assert engine.state.shape == (10, 10)
    assert engine.width == 10
    assert engine.height == 10

def test_engine_conway_rules():
    engine = GameEngine(5, 5)
    # Blinker pattern
    engine.state[1, 2] = EntityType.NORMAL
    engine.state[2, 2] = EntityType.NORMAL
    engine.state[3, 2] = EntityType.NORMAL

    engine.step()

    assert engine.state[2, 1] == EntityType.NORMAL
    assert engine.state[2, 2] == EntityType.NORMAL
    assert engine.state[2, 3] == EntityType.NORMAL
    assert engine.state[1, 2] == EntityType.EMPTY
    assert engine.state[3, 2] == EntityType.EMPTY

def test_engine_zombie_rule():
    engine = GameEngine(5, 5)
    engine.toggle_rule("zombie", True)
    # Single cell dies of loneliness
    engine.state[2, 2] = EntityType.NORMAL

    engine.step()

    # Should become zombie
    assert engine.state[2, 2] == EntityType.ZOMBIE

if __name__ == "__main__":
    pytest.main(["-v", "test_engine.py"])
