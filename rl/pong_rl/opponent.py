"""Opponent strategies for the learning paddle to play against.

Every opponent exposes `choose_action(observation) -> int`, matching the
same 3-action interface (STAY=0, UP=1, DOWN=2) used by the RL agent, so
opponents are interchangeable inside PongEnv.
"""

from __future__ import annotations

import random
from typing import Protocol

import numpy as np

from pong_rl.physics import DOWN, STAY, UP


class Opponent(Protocol):
    def choose_action(self, observation: np.ndarray) -> int: ...

    def reset(self, seed: int | None = None) -> None: ...


class RandomOpponent:
    """Chooses a uniformly random action every step. Useful for Stage 1 sanity checks."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def choose_action(self, observation: np.ndarray) -> int:
        return self._rng.choice([STAY, UP, DOWN])

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self._rng.seed(seed)


class TrackingOpponent:
    """Deterministic bot that moves toward the ball's y position.

    `imperfection` (0.0-1.0) adds a dead zone and occasional random
    mistakes so the bot is beatable rather than a perfect wall.
    """

    def __init__(self, imperfection: float = 0.1, rng: random.Random | None = None) -> None:
        self.imperfection = imperfection
        self._rng = rng or random.Random()

    def choose_action(self, observation: np.ndarray) -> int:
        # observation is [ball_x, ball_y, ball_vx, ball_vy, my_paddle_y, opponent_paddle_y]
        # For the opponent's own view, "my_paddle_y" is passed in as the opponent's paddle.
        ball_y = observation[1]
        my_paddle_y = observation[4]

        if self._rng.random() < self.imperfection:
            return self._rng.choice([STAY, UP, DOWN])

        dead_zone = 0.03
        diff = ball_y - my_paddle_y
        if abs(diff) < dead_zone:
            return STAY
        return DOWN if diff > 0 else UP

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self._rng.seed(seed)


class ModelOpponent:
    """Wraps a saved Stable-Baselines3 PPO policy so it can act as an opponent."""

    def __init__(self, model_path: str) -> None:
        from stable_baselines3 import PPO

        self._model = PPO.load(model_path)

    def choose_action(self, observation: np.ndarray) -> int:
        action, _ = self._model.predict(observation, deterministic=True)
        return int(action)

    def reset(self, seed: int | None = None) -> None:
        pass
