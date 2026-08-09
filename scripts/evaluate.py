"""Evaluate a trained PPO Pong agent without rendering.

Example:
    uv run python scripts/evaluate.py --model models/best_model.zip --episodes 100
"""

from __future__ import annotations

import argparse
import os
import random
import sys

import numpy as np
from stable_baselines3 import PPO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pong_rl.env import PongEnv
from pong_rl.opponent import Opponent, RandomOpponent, TrackingOpponent


def build_opponent(name: str, seed: int) -> Opponent:
    rng = random.Random(seed)
    if name == "random":
        return RandomOpponent(rng=rng)
    if name == "tracking":
        return TrackingOpponent(imperfection=0.1, rng=rng)
    raise ValueError(f"Unknown opponent: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained PPO Pong agent.")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--opponent", type=str, default="tracking", choices=["random", "tracking"])
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    opponent = build_opponent(args.opponent, args.seed)
    env = PongEnv(opponent=opponent, render_mode=None)
    model = PPO.load(args.model)

    wins = 0
    losses = 0
    total_reward = 0.0
    total_length = 0

    for episode in range(args.episodes):
        observation, _ = env.reset(seed=args.seed + episode)
        terminated = False
        truncated = False
        episode_reward = 0.0
        episode_length = 0

        while not (terminated or truncated):
            action, _ = model.predict(observation, deterministic=True)
            observation, reward, terminated, truncated, info = env.step(int(action))
            episode_reward += reward
            episode_length += 1

        total_reward += episode_reward
        total_length += episode_length
        if info["left_score"] > info["right_score"]:
            wins += 1
        elif info["right_score"] > info["left_score"]:
            losses += 1

    env.close()

    games_played = args.episodes
    win_rate = wins / games_played if games_played else 0.0
    avg_reward = total_reward / games_played if games_played else 0.0
    avg_length = total_length / games_played if games_played else 0.0

    print(f"Games played:   {games_played}")
    print(f"Wins:           {wins}")
    print(f"Losses:         {losses}")
    print(f"Win rate:       {win_rate:.2%}")
    print(f"Average reward: {avg_reward:.2f}")
    print(f"Average length: {avg_length:.1f} steps")


if __name__ == "__main__":
    main()
