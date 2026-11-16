# Pong Monorepo

## Play it now

**[https://saurabh-saha.github.io/pong-godot/](https://saurabh-saha.github.io/pong-godot/)**

1. Open the link
2. Click **Play vs Computer** (or **2 Players**), or press **2** / **1**
3. Move your paddle with **W** / **S** or **↑** / **↓** (in 2-player mode the right paddle uses **↑** / **↓**). On a phone, drag up and down
4. **P** or **Esc** pauses; first to 5 wins

The computer opponent is a neural network (small tanh MLP) trained with reinforcement learning
(PPO), originally inside a Godot-provided environment, later moved to a fast headless Python
simulation for training. See [`rl/README.md`](rl/README.md) for the full training write-up.

New to ML/RL terms like neural networks, PPO, or backpropagation? Read
**[Pip Learns to Play](docs/pip_learns_to_play.pdf)** — a short story that explains all of it
using this project's own AI opponent as the example.

## Structure

- [`game/`](game/) — the Godot Pong game ([game/README.md](game/README.md))
- [`rl/`](rl/) — pong-rl, the reinforcement-learning training project for the AI opponent ([rl/README.md](rl/README.md), added as a git subtree from [saurabh-saha/pong-rl](https://github.com/saurabh-saha/pong-rl))
- [`docs/`](docs/) — browser-playable HTML/JS port of the game (served via GitHub Pages), including the same AI opponent reimplemented in JS
