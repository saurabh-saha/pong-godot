"""Gymnasium environment wrapping the Python Pong simulation.

The learning agent always controls the LEFT paddle. The RIGHT paddle is
driven by an injected opponent strategy (see opponent.py).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from pong_rl import physics
from pong_rl.opponent import Opponent, RandomOpponent

DT: float = 1.0 / 60.0
DEFAULT_MAX_STEPS: int = 3000
DEFAULT_WIN_SCORE: int = 5


@dataclass
class RewardConfig:
    hit_paddle: float = 1.0
    score_point: float = 5.0
    lose_point: float = -5.0
    step: float = 0.0


def _normalize_observation(
    ball_x: float,
    ball_y: float,
    ball_vx: float,
    ball_vy: float,
    my_paddle_y: float,
    opponent_paddle_y: float,
) -> np.ndarray:
    return np.array(
        [
            np.clip(ball_x / physics.GAME_WIDTH, 0.0, 1.0),
            np.clip(ball_y / physics.GAME_HEIGHT, 0.0, 1.0),
            np.clip(ball_vx / physics.BALL_MAX_SPEED, -1.0, 1.0),
            np.clip(ball_vy / physics.BALL_MAX_SPEED, -1.0, 1.0),
            np.clip(my_paddle_y / physics.GAME_HEIGHT, 0.0, 1.0),
            np.clip(opponent_paddle_y / physics.GAME_HEIGHT, 0.0, 1.0),
        ],
        dtype=np.float32,
    )


def build_observation(state: physics.PongState, for_left: bool) -> np.ndarray:
    """Build the 6-feature observation from one paddle's point of view.

    Mirroring the x-axis for the right paddle keeps both sides' observations
    conceptually identical ("my paddle" / "opponent paddle"), which is what
    lets a saved model be reused as an opponent (self-play).
    """
    ball = state.ball
    if for_left:
        return _normalize_observation(
            ball.x, ball.y, ball.vx, ball.vy,
            state.left_paddle_y, state.right_paddle_y,
        )

    mirrored_x = physics.GAME_WIDTH - ball.x
    return _normalize_observation(
        mirrored_x, ball.y, -ball.vx, ball.vy,
        state.right_paddle_y, state.left_paddle_y,
    )


class PongEnv(gym.Env):
    """Single-agent Pong environment. The agent always plays the left paddle."""

    metadata = {"render_modes": ["human"], "render_fps": 60}

    def __init__(
        self,
        opponent: Opponent | None = None,
        render_mode: str | None = None,
        max_steps: int = DEFAULT_MAX_STEPS,
        win_score: int = DEFAULT_WIN_SCORE,
        reward_config: RewardConfig | None = None,
    ) -> None:
        super().__init__()

        self.opponent: Opponent = opponent or RandomOpponent()
        self.render_mode = render_mode
        self.max_steps = max_steps
        self.win_score = win_score
        self.rewards = reward_config or RewardConfig()

        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, -1.0, -1.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

        self._rng = random.Random()
        self._state = physics.PongState()
        self._steps = 0
        self._renderer = None

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self._rng.seed(seed)

        self._state = physics.PongState()
        direction = self._rng.choice([-1, 1])
        self._state.ball = physics.launch_ball(direction, self._rng)
        self._steps = 0
        self.opponent.reset(seed)

        observation = build_observation(self._state, for_left=True)
        return observation, {}

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        state = self._state

        state.left_paddle_y = physics.move_paddle(state.left_paddle_y, action, DT)

        opponent_observation = build_observation(state, for_left=False)
        opponent_action = self.opponent.choose_action(opponent_observation)
        state.right_paddle_y = physics.move_paddle(state.right_paddle_y, opponent_action, DT)

        result = physics.step_ball(state, DT)
        self._steps += 1

        reward = self.rewards.step
        if result.hit == "left":
            reward += self.rewards.hit_paddle
        if result.scored == "left":
            reward += self.rewards.score_point
        elif result.scored == "right":
            reward += self.rewards.lose_point

        if result.scored is not None:
            direction = 1 if result.scored == "right" else -1
            state.ball = physics.launch_ball(direction, self._rng)

        terminated = (
            state.left_score >= self.win_score or state.right_score >= self.win_score
        )
        truncated = self._steps >= self.max_steps

        observation = build_observation(state, for_left=True)
        info = {"left_score": state.left_score, "right_score": state.right_score}

        if self.render_mode == "human":
            self.render()

        return observation, reward, terminated, truncated, info

    def render(self) -> None:
        if self.render_mode != "human":
            return

        if self._renderer is None:
            from pong_rl.renderer import PygameRenderer

            self._renderer = PygameRenderer()

        self._renderer.draw(self._state)

    def close(self) -> None:
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
