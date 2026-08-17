"""Deterministic Pong physics simulation.

Coordinates roughly correspond to the Godot Pong implementation
(1152x648 playfield), scaled down for fast simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

GAME_WIDTH: float = 1152.0
GAME_HEIGHT: float = 648.0

PADDLE_WIDTH: float = 20.0
PADDLE_HEIGHT: float = 100.0
PADDLE_SPEED: float = 450.0

BALL_SIZE: float = 16.0
BALL_START_SPEED: float = 400.0
BALL_MAX_SPEED: float = 800.0
BALL_SPEED_INCREASE: float = 25.0

LEFT_PADDLE_X: float = 40.0
RIGHT_PADDLE_X: float = GAME_WIDTH - 40.0

MAX_BOUNCE_ANGLE: float = math.radians(50.0)

STAY = 0
UP = 1
DOWN = 2


@dataclass
class BallState:
    x: float = GAME_WIDTH / 2.0
    y: float = GAME_HEIGHT / 2.0
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class PongState:
    """Full simulation state for one rally-based Pong match."""

    left_paddle_y: float = GAME_HEIGHT / 2.0
    right_paddle_y: float = GAME_HEIGHT / 2.0
    ball: BallState = field(default_factory=BallState)
    left_score: int = 0
    right_score: int = 0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def move_paddle(paddle_y: float, action: int, dt: float) -> float:
    """Move a paddle vertically based on a discrete action, staying in bounds."""
    direction = 0.0
    if action == UP:
        direction = -1.0
    elif action == DOWN:
        direction = 1.0

    half = PADDLE_HEIGHT / 2.0
    new_y = paddle_y + direction * PADDLE_SPEED * dt
    return _clamp(new_y, half, GAME_HEIGHT - half)


def launch_ball(direction_sign: int, rng) -> BallState:
    """Create a fresh ball at center moving toward direction_sign (+1 right, -1 left)."""
    angle = rng.uniform(-0.3, 0.3)
    speed = BALL_START_SPEED
    vx = math.cos(angle) * speed * direction_sign
    vy = math.sin(angle) * speed
    return BallState(x=GAME_WIDTH / 2.0, y=GAME_HEIGHT / 2.0, vx=vx, vy=vy)


def _bounce_off_paddle(ball: BallState, paddle_y: float, paddle_x: float, direction_sign: int) -> None:
    """Reflect the ball off a paddle, adjusting angle by hit offset and increasing speed."""
    half_paddle = PADDLE_HEIGHT / 2.0
    offset = _clamp((ball.y - paddle_y) / half_paddle, -1.0, 1.0)
    angle = offset * MAX_BOUNCE_ANGLE

    speed = math.hypot(ball.vx, ball.vy) + BALL_SPEED_INCREASE
    speed = min(speed, BALL_MAX_SPEED)

    ball.vx = math.cos(angle) * speed * direction_sign
    ball.vy = math.sin(angle) * speed

    half_ball = BALL_SIZE / 2.0
    half_pad = PADDLE_WIDTH / 2.0
    if direction_sign > 0:
        ball.x = paddle_x + half_pad + half_ball
    else:
        ball.x = paddle_x - half_pad - half_ball


@dataclass
class StepResult:
    scored: str | None = None  # "left" or "right", whichever side scored
    hit: str | None = None  # "left" or "right", whichever paddle just hit the ball


def step_ball(state: PongState, dt: float) -> StepResult:
    """Advance the ball one timestep, resolving wall/paddle bounces and scoring."""
    ball = state.ball
    ball.x += ball.vx * dt
    ball.y += ball.vy * dt

    half_ball = BALL_SIZE / 2.0
    result = StepResult()

    if ball.y - half_ball <= 0.0:
        ball.y = half_ball
        ball.vy = abs(ball.vy)
    elif ball.y + half_ball >= GAME_HEIGHT:
        ball.y = GAME_HEIGHT - half_ball
        ball.vy = -abs(ball.vy)

    half_paddle = PADDLE_HEIGHT / 2.0
    half_pad_w = PADDLE_WIDTH / 2.0

    if ball.vx < 0.0:
        within_x = abs(ball.x - LEFT_PADDLE_X) <= (half_ball + half_pad_w)
        within_y = abs(ball.y - state.left_paddle_y) <= (half_ball + half_paddle)
        if within_x and within_y:
            _bounce_off_paddle(ball, state.left_paddle_y, LEFT_PADDLE_X, direction_sign=1)
            result.hit = "left"
    else:
        within_x = abs(ball.x - RIGHT_PADDLE_X) <= (half_ball + half_pad_w)
        within_y = abs(ball.y - state.right_paddle_y) <= (half_ball + half_paddle)
        if within_x and within_y:
            _bounce_off_paddle(ball, state.right_paddle_y, RIGHT_PADDLE_X, direction_sign=-1)
            result.hit = "right"

    if ball.x < -half_ball:
        state.right_score += 1
        result.scored = "right"
    elif ball.x > GAME_WIDTH + half_ball:
        state.left_score += 1
        result.scored = "left"

    return result
