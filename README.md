# Pong

A classic Pong game built in Godot 4.7, using GDScript only.

![Pong gameplay screenshot](screenshot.png)

## Gameplay

- Left paddle vs. right paddle, ball bounces between them.
- Ball bounces off the top/bottom walls and paddles, speeding up slightly on each paddle hit (capped so it stays playable).
- Missing the ball scores a point for the other side.
- First to 5 points wins; the game shows the winner and can be restarted.
- On launch, choose **1** for Player vs Player, or **2** for Player vs Computer.

## Controls

| Player | Up | Down |
|---|---|---|
| Left paddle | `W` | `S` |
| Right paddle (if not AI-controlled) | `↑` | `↓` |

Press `Space` to restart after a game ends. Press `1`/`2` at game start to pick the mode.

## Playing against the AI

Selecting **Player vs Computer** hands the right paddle to a neural network trained with
reinforcement learning in the companion [pong-rl](https://github.com/saurabh-saha/pong-rl)
project (PPO, ~66% win rate against a scripted tracking bot after training). Since Godot has
no PyTorch/ML runtime, the trained network's weights were exported to plain JSON
(`ai_model.json`) and its forward pass is reimplemented by hand in `ai_policy.gd` — just
matrix multiplications and `tanh`, no external dependency. `ai_policy.gd`'s `build_observation()`
mirrors the ball's x-position and velocity for the right paddle, since the model was only ever
trained playing the *left* paddle; mirroring reframes "right paddle" as "my paddle" from the
model's point of view, matching exactly how `pong_rl/env.py`'s `build_observation(for_left=False)`
builds an opponent's view during training.

## Project structure

```
pong/
├── project.godot    # engine config, window size, input map
├── game.tscn         # scene tree: paddles, ball, walls, UI
├── game.gd           # scoring, win condition, mode select, restart logic
├── paddle.gd         # paddle input/movement/bounds, or AI control if enabled
├── ball.gd           # ball movement, bouncing, scoring
├── ai_policy.gd       # hand-rolled forward pass for the trained RL model
├── ai_model.json      # exported weights (see pong-rl/scripts/export_weights.py)
└── game.skill.md     # original design spec for this project
```

## Running it

Open the project folder in Godot 4.7+ and press **Play** — `game.tscn` is configured as the main scene.
