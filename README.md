# Pong RL

A small reinforcement-learning project that trains a PPO agent to play Pong,
using a fast, headless Python simulation (no Godot needed for training).

## What it does

- `pong_rl/physics.py` — deterministic Pong physics (ball, paddles, walls, scoring).
- `pong_rl/env.py` — a [Gymnasium](https://gymnasium.farama.org/) environment (`PongEnv`) wrapping that physics.
- `pong_rl/opponent.py` — opponent strategies: random, tracking bot, or a previously trained model.
- `pong_rl/renderer.py` — optional pygame visualization, used only by `watch.py`.
- `scripts/train.py`, `scripts/evaluate.py`, `scripts/watch.py` — CLIs for training, evaluating, and watching.

The agent always controls the **left** paddle. Training runs fully headless and much faster than real time.

## Observation (6 features)

```
[ball_x, ball_y, ball_velocity_x, ball_velocity_y, my_paddle_y, opponent_paddle_y]
```

All positions are normalized to `0.0-1.0`, velocities to `-1.0-1.0`. This is a deliberately
minimal, unshaped observation — no distance-to-ball or predicted-intercept features. The
agent has to learn those relationships itself.

## Actions (3 discrete)

```
0 = STAY
1 = UP
2 = DOWN
```

## Rewards

| Event                              | Reward |
|-------------------------------------|--------|
| Paddle hits the ball                | +1     |
| Score a point                       | +5     |
| Opponent scores a point             | -5     |
| Normal step                         |  0     |

Configurable via `pong_rl.env.RewardConfig`.

## What PPO is (briefly)

PPO (Proximal Policy Optimization) is a reinforcement-learning algorithm that trains a
neural network policy — here, a small MLP mapping the 6 observations to 3 action
probabilities — by repeatedly playing episodes, then nudging the policy toward actions
that led to higher reward, while limiting how much it changes per update (for stability).
This project uses Stable-Baselines3's PPO implementation rather than writing PPO from scratch.

## Install

```bash
uv sync
```

## Train

```bash
uv run python scripts/train.py --timesteps 100000 --opponent tracking
```

Options: `--timesteps`, `--opponent {random,tracking,self_play}`, `--seed`,
`--model-dir` (default `models/`), `--checkpoint-frequency`.

Training is headless by default and saves periodic checkpoints plus a final
`models/best_model.zip`.

## Watch

```bash
uv run python scripts/watch.py --model models/best_model.zip --opponent tracking
```

Opens a pygame window and plays a few episodes at human-viewable speed.
`--opponent` also accepts `random` or `model` (with `--opponent-model <path>`
to watch two trained policies play each other).

## Evaluate

```bash
uv run python scripts/evaluate.py --model models/best_model.zip --episodes 100
```

Runs headless and reports games played, wins, losses, win rate, average reward,
and average episode length.

## Self-play

Pass `--opponent self_play` to `train.py`. Each checkpoint saved to `models/`
becomes a candidate opponent; every episode reset randomly samples one of the
saved checkpoints (falling back to a tracking bot until checkpoints exist).
This avoids the opponent changing on every single gradient update, which
would make training unstable.

## Tests

```bash
uv run pytest
```

Covers environment reset/step behavior, physics bounces, scoring rewards,
episode termination, and Gymnasium's `check_env` validation.

## Godot integration (future)

Not implemented in this version. The observation/action contract above is
designed so a Godot game could construct the same 6-value observation vector
and consume one of the same 3 discrete actions from an exported model.
