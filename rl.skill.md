# Pong RL — Reinforcement Learning Skill

## Role

You are an ML/RL engineer building a reinforcement-learning system that learns to play Pong.

The existing playable Pong game is implemented separately in Godot.

This project is responsible for:

- Pong simulation for training
- RL environment
- PPO training
- self-play
- model checkpointing
- evaluation
- optional visual rendering/debugging

Keep the implementation small, understandable, and suitable as a first reinforcement-learning project.

Do not over-engineer.

---

# Technology

Language: Python 3.12+
Package manager: uv

Core libraries:

- gymnasium
- numpy
- torch
- stable-baselines3

Optional:

- pygame for visualizing the Python simulation

Do NOT use:

- Conda
- TensorFlow
- Jupyter notebooks as the primary implementation
- unnecessary web frameworks
- databases
- distributed training systems

Use `uv` for dependency and environment management.

---

# Project Setup

Initialize this as a uv project.

Expected structure:

pong-rl/
├── pyproject.toml
├── uv.lock
├── README.md
├── rl.skill.md
│
├── pong_rl/
│   ├── __init__.py
│   ├── env.py
│   ├── physics.py
│   ├── opponent.py
│   └── renderer.py
│
├── scripts/
│   ├── train.py
│   ├── evaluate.py
│   └── watch.py
│
├── models/
│
└── tests/

---

# Architecture

For V1, DO NOT launch Godot for every training episode.

Implement a lightweight Pong simulation directly in Python.

Reason:

Training may require hundreds of thousands or millions of simulation steps.

The Python environment should be able to run much faster than real-time without rendering.

Godot remains the eventual playable/visual environment.

The Python simulation and Godot game must share the same conceptual observation/action contract so the trained policy can later be integrated with Godot.

Architecture:

                    TRAINING

             Python PPO Trainer
                    |
                    | actions
                    v
            Python Pong Environment
                    |
                    | observations/rewards
                    v
                 PPO Agent

                    |
                    v

              saved model


                    PLAYING

              Godot Pong
                    |
                    v
             trained policy

Godot integration is NOT required for V1 unless explicitly requested later.

---

# Pong Environment

Implement the environment using the Gymnasium API.

Create:

PongEnv(gym.Env)

Implement at minimum:

- reset()
- step(action)
- render()
- close()

The environment represents ONE learning paddle.

The opposite paddle is controlled by an opponent strategy.

---

# Game State

The observation should initially contain exactly these six features:

1. ball_x
2. ball_y
3. ball_velocity_x
4. ball_velocity_y
5. my_paddle_y
6. opponent_paddle_y

Represent observations as:

numpy.float32

Normalize values.

Positions should generally map to:

0.0 → 1.0

Velocities should generally map to:

-1.0 → 1.0

Observation shape:

(6,)

Example:

[
    0.42,   # ball x
    0.71,   # ball y
    0.83,   # ball velocity x
   -0.31,   # ball velocity y
    0.55,   # my paddle y
    0.38    # opponent paddle y
]

Do NOT provide engineered features such as:

- predicted intercept
- distance to ball
- ideal paddle location
- future ball position

The agent should learn useful relationships itself.

---

# Actions

Discrete action space with exactly three actions:

0 = STAY
1 = UP
2 = DOWN

Use:

gymnasium.spaces.Discrete(3)

Paddle movement must be deterministic given an action.

---

# Physics

Implement simple deterministic Pong physics.

Game contains:

- ball
- learning paddle
- opponent paddle
- top wall
- bottom wall

Ball must:

- move every simulation step
- bounce from top/bottom walls
- bounce from paddles
- score when passing a paddle

Paddles:

- move vertically
- cannot leave screen bounds

Avoid perfectly vertical or horizontal ball trajectories.

Use constants for:

- game width
- game height
- paddle width
- paddle height
- ball size
- paddle speed
- ball speed

Keep these constants easy to modify.

Physics should roughly correspond to the existing Godot Pong implementation.

---

# Simulation Speed

Training must NOT depend on wall-clock time.

Do not use sleep() during training.

Each call to:

env.step(action)

should advance the simulation by a deterministic timestep.

Training should therefore run significantly faster than real-time.

Rendering must be optional.

---

# Render Modes

Support:

render_mode=None

for fast headless training.

Also support a human-readable visual mode:

render_mode="human"

Use pygame if needed.

The same environment should therefore support:

fast headless training

and

watching the agent play.

Rendering must not affect simulation physics.

---

# Rewards

Start with a simple reward system.

Recommended initial rewards:

Hit opponent-facing ball with paddle:

+1

Score a point:

+5

Lose a point:

-5

Normal simulation step:

0

Do NOT initially reward simply moving toward the ball.

Avoid excessive reward shaping.

The goal is for the agent to discover useful movement through gameplay.

Reward constants should be configurable.

---

# Episodes

An episode should consist of a Pong match or a bounded number of rallies.

Recommended:

First to 5 points

OR

terminate after a configurable maximum number of steps.

Environment must never allow infinite episodes.

reset() must restore:

- score
- ball
- paddles
- internal counters

---

# Opponents

Implement multiple opponent types.

## RandomOpponent

Randomly chooses:

UP
DOWN
STAY

Useful for initial testing.

## TrackingOpponent

Simple deterministic Pong bot.

It should move its paddle toward the ball's Y position.

Allow configurable reaction imperfection so it is not unbeatable.

This opponent is NOT machine learning.

## ModelOpponent

Loads a previously saved PPO policy and uses it as the opponent.

This enables self-play.

All opponents should expose a simple interface such as:

choose_action(observation) -> int

Keep the interface simple.

---

# PPO Agent

Use Stable-Baselines3 PPO.

Do NOT implement PPO from scratch.

Use an MLP policy.

The conceptual neural network is:

6 observation features
        ↓
small MLP
        ↓
3 action probabilities

Allow Stable-Baselines3 to manage the exact policy implementation.

Start with reasonable small-network defaults.

Do not build a large model.

Pong does not require one.

---

# Training Progression

Implement training so we can progress through stages.

## Stage 1

Agent vs RandomOpponent.

Purpose:

Verify that:

- environment works
- rewards work
- PPO learns anything
- model can be saved

## Stage 2

Agent vs TrackingOpponent.

The tracking opponent should be configurable in difficulty.

Purpose:

Teach stronger Pong behaviour.

## Stage 3

Self-play.

Current agent plays against previously saved versions of itself.

Do not immediately implement complicated population-based training.

Use simple checkpoint self-play.

Example:

models/
├── checkpoint_010000.zip
├── checkpoint_050000.zip
├── checkpoint_100000.zip
└── best_model.zip

Periodically save the current policy.

ModelOpponent can randomly select from previous checkpoints.

This prevents the opponent from changing every single gradient update.

---

# Training CLI

Provide:

scripts/train.py

Example usage:

uv run python scripts/train.py

Useful arguments:

--timesteps
--opponent
--seed
--model-dir
--checkpoint-frequency

Example:

uv run python scripts/train.py \
    --timesteps 500000 \
    --opponent tracking

Training should default to HEADLESS mode.

Do not open a graphical window during normal training.

---

# Watch CLI

Provide:

scripts/watch.py

This loads a trained model and visually displays games.

Example:

uv run python scripts/watch.py \
    --model models/best_model.zip

This should run at human-viewable speed.

The purpose is to visually inspect learned behaviour.

Allow:

--opponent random
--opponent tracking
--opponent model

if practical.

---

# Evaluation

Provide:

scripts/evaluate.py

Evaluation must run without rendering.

Run a configurable number of episodes.

Report:

- games played
- wins
- losses
- win rate
- average reward
- average episode length

Example:

uv run python scripts/evaluate.py \
    --model models/best_model.zip \
    --episodes 100

Evaluation should be deterministic when given a seed where practical.

---

# Checkpointing

Save models periodically.

Do not commit large generated model files by default.

Add model artifacts to .gitignore where appropriate.

Maintain:

models/best_model.zip

when evaluation determines a new best policy.

---

# Reproducibility

Support configurable random seeds.

Seed:

- Python random
- NumPy
- Gymnasium environment
- Stable-Baselines3 where appropriate

Exact bit-for-bit reproducibility is not required, but repeated experiments should be reasonably comparable.

---

# Tests

Add lightweight tests for the environment.

At minimum verify:

1. reset() returns valid observation.
2. observation shape is (6,).
3. observation values are within declared observation space.
4. actions move paddle correctly.
5. paddle cannot leave screen.
6. ball bounces from top wall.
7. ball bounces from bottom wall.
8. ball collision with paddle changes direction.
9. scoring produces correct reward.
10. episode termination works.
11. environment passes Gymnasium environment validation.

Use:

gymnasium.utils.env_checker.check_env

where appropriate.

---

# Godot Compatibility Contract

Although Godot integration is not part of V1, design around this future interface.

Observation:

[
    ball_x,
    ball_y,
    ball_velocity_x,
    ball_velocity_y,
    my_paddle_y,
    opponent_paddle_y
]

Action:

0 = STAY
1 = UP
2 = DOWN

When we later connect the trained agent to Godot, Godot should be able to construct the same normalized observation vector and receive one of these three actions.

Do not make Python-specific assumptions in this observation/action contract.

---

# Important ML Principle

Do not train from rendered screenshots.

The initial agent receives structured game-state features.

We are learning:

state
    ↓
policy
    ↓
action

NOT:

image
    ↓
computer vision
    ↓
action

Pixel-based learning may be explored later as a separate experiment.

---

# Engineering Rules

Keep the code beginner-readable.

Prefer:

simple classes
clear functions
type hints
small modules

Avoid:

dependency injection frameworks
complex configuration systems
distributed RL
Ray
Kubernetes
databases
microservices
premature abstractions

This is an educational RL project.

---

# README

Create a concise README explaining:

1. What the project does.
2. How the agent observes Pong.
3. The three available actions.
4. How rewards work.
5. What PPO is at a high level.
6. How to install with uv.
7. How to train.
8. How to watch the trained agent.
9. How to evaluate it.
10. How self-play will work.

Include commands that can be copied directly.

---

# Validation

Before considering implementation complete:

Run dependency installation.

Run tests.

Run Gymnasium env checker.

Run a short PPO smoke training session.

Example:

1000–5000 timesteps.

Verify:

- training completes
- model saves
- saved model loads
- evaluation runs
- watch mode starts if graphical environment is available

Do not claim successful visual validation if the execution environment cannot open graphical windows.

Fix Python/import/environment errors before completion.

---

# Implementation Order

Implement in this order:

1. uv project
2. Pong physics
3. Gymnasium environment
4. tests
5. random opponent
6. tracking opponent
7. PPO training
8. checkpoint saving
9. evaluation
10. visual watch mode
11. model opponent
12. basic checkpoint self-play

Do not start with self-play.

First prove that a single PPO agent can learn Pong.

---

# Success Criteria

The project is successful when:

uv run python scripts/train.py --timesteps 100000 --opponent tracking

can train and save a model,

and:

uv run python scripts/watch.py --model models/best_model.zip

lets the developer watch that model play Pong.

The trained policy must use only:

6 input features

and

3 discrete actions.

Once this works reliably, Godot integration will be designed separately.
