# Pong Monorepo

## Play it now

**[https://saurabh-saha.github.io/pong-godot/](https://saurabh-saha.github.io/pong-godot/)**

1. Open the link
2. Press **2** for Player vs Computer (or **1** for Player vs Player)
3. Move your paddle with **W** / **S** (right paddle uses **↑** / **↓** if not AI-controlled)

The computer opponent is a neural network — trained with reinforcement learning (PPO, ReLU/tanh MLP)
originally inside a Godot-provided environment, later moved to a fast headless Python simulation for
training. See [`rl/README.md`](rl/README.md) for the full training write-up.

## Structure

- [`game/`](game/) — the Godot Pong game ([game/README.md](game/README.md))
- [`rl/`](rl/) — pong-rl, the reinforcement-learning training project for the AI opponent ([rl/README.md](rl/README.md), added as a git subtree from [saurabh-saha/pong-rl](https://github.com/saurabh-saha/pong-rl))
- [`docs/`](docs/) — browser-playable HTML/JS port of the game (served via GitHub Pages), including the same AI opponent reimplemented in JS
