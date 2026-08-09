import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from pong_rl import physics
from pong_rl.env import PongEnv
from pong_rl.opponent import RandomOpponent


def make_env(**kwargs) -> PongEnv:
    return PongEnv(opponent=RandomOpponent(), **kwargs)


def test_reset_returns_valid_observation():
    env = make_env()
    observation, info = env.reset(seed=0)
    assert observation.shape == (6,)
    assert observation.dtype == np.float32
    assert isinstance(info, dict)


def test_observation_within_declared_space():
    env = make_env()
    observation, _ = env.reset(seed=1)
    assert env.observation_space.contains(observation)

    for _ in range(200):
        observation, _, terminated, truncated, _ = env.step(env.action_space.sample())
        assert env.observation_space.contains(observation)
        if terminated or truncated:
            env.reset()


def test_actions_move_paddle():
    env = make_env()
    env.reset(seed=2)

    start_y = env._state.left_paddle_y
    env.step(physics.UP)
    assert env._state.left_paddle_y < start_y

    env.reset(seed=2)
    start_y = env._state.left_paddle_y
    env.step(physics.DOWN)
    assert env._state.left_paddle_y > start_y


def test_paddle_cannot_leave_screen():
    env = make_env()
    env.reset(seed=3)

    for _ in range(500):
        env.step(physics.UP)
    assert env._state.left_paddle_y >= physics.PADDLE_HEIGHT / 2.0

    env.reset(seed=3)
    for _ in range(500):
        env.step(physics.DOWN)
    assert env._state.left_paddle_y <= physics.GAME_HEIGHT - physics.PADDLE_HEIGHT / 2.0


def test_ball_bounces_from_top_wall():
    state = physics.PongState()
    state.ball = physics.BallState(x=physics.GAME_WIDTH / 2, y=5.0, vx=100.0, vy=-200.0)
    physics.step_ball(state, dt=1.0 / 60.0)
    assert state.ball.vy > 0


def test_ball_bounces_from_bottom_wall():
    state = physics.PongState()
    state.ball = physics.BallState(
        x=physics.GAME_WIDTH / 2, y=physics.GAME_HEIGHT - 5.0, vx=100.0, vy=200.0
    )
    physics.step_ball(state, dt=1.0 / 60.0)
    assert state.ball.vy < 0


def test_ball_collision_with_paddle_changes_direction():
    state = physics.PongState()
    state.left_paddle_y = physics.GAME_HEIGHT / 2.0
    state.ball = physics.BallState(
        x=physics.LEFT_PADDLE_X + 10.0, y=physics.GAME_HEIGHT / 2.0, vx=-400.0, vy=10.0
    )
    result = physics.step_ball(state, dt=1.0 / 60.0)
    assert result.hit == "left"
    assert state.ball.vx > 0


def test_scoring_produces_correct_reward():
    env = make_env()
    env.reset(seed=4)

    env._state.ball = physics.BallState(x=-50.0, y=300.0, vx=-400.0, vy=0.0)
    _, reward, _, _, info = env.step(physics.STAY)
    assert reward == pytest.approx(env.rewards.lose_point)
    assert info["right_score"] == 1

    env._state.ball = physics.BallState(
        x=physics.GAME_WIDTH + 50.0, y=300.0, vx=400.0, vy=0.0
    )
    _, reward, _, _, info = env.step(physics.STAY)
    assert reward == pytest.approx(env.rewards.score_point)
    assert info["left_score"] == 1


def test_episode_terminates_on_win_score():
    env = make_env(win_score=1)
    env.reset(seed=5)
    env._state.ball = physics.BallState(
        x=physics.GAME_WIDTH + 50.0, y=300.0, vx=400.0, vy=0.0
    )
    _, _, terminated, _, _ = env.step(physics.STAY)
    assert terminated


def test_episode_truncates_at_max_steps():
    env = make_env(max_steps=5)
    env.reset(seed=6)
    truncated = False
    for _ in range(10):
        _, _, terminated, truncated, _ = env.step(physics.STAY)
        if terminated or truncated:
            break
    assert truncated


def test_gymnasium_env_checker():
    env = make_env()
    check_env(env.unwrapped, skip_render_check=True)
