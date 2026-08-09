"""Watch a trained PPO Pong agent play, visually, at human speed.

Example:
    uv run python scripts/watch.py --model models/best_model.zip --opponent tracking
"""

from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from stable_baselines3 import PPO

from pong_rl.env import PongEnv
from pong_rl.opponent import ModelOpponent, Opponent, RandomOpponent, TrackingOpponent


def build_opponent(name: str, model_path: str | None, seed: int) -> Opponent:
    rng = random.Random(seed)
    if name == "random":
        return RandomOpponent(rng=rng)
    if name == "tracking":
        return TrackingOpponent(imperfection=0.1, rng=rng)
    if name == "model":
        if not model_path:
            raise ValueError("--opponent model requires --opponent-model <path>")
        return ModelOpponent(model_path)
    raise ValueError(f"Unknown opponent: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch a trained PPO Pong agent play.")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument(
        "--opponent", type=str, default="tracking", choices=["random", "tracking", "model"]
    )
    parser.add_argument("--opponent-model", type=str, default=None)
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    opponent = build_opponent(args.opponent, args.opponent_model, args.seed)
    env = PongEnv(opponent=opponent, render_mode="human")
    model = PPO.load(args.model)

    for episode in range(args.episodes):
        observation, _ = env.reset(seed=args.seed + episode)
        terminated = False
        truncated = False

        while not (terminated or truncated):
            action, _ = model.predict(observation, deterministic=True)
            observation, _, terminated, truncated, info = env.step(int(action))

        print(f"Episode {episode + 1}: {info['left_score']} - {info['right_score']}")

    env.close()


if __name__ == "__main__":
    main()
