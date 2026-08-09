"""Train a PPO agent to play Pong.

Examples:
    uv run python scripts/train.py --timesteps 100000 --opponent tracking
    uv run python scripts/train.py --timesteps 500000 --opponent self_play
"""

from __future__ import annotations

import argparse
import glob
import os
import random
import sys

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pong_rl.env import PongEnv
from pong_rl.opponent import ModelOpponent, Opponent, RandomOpponent, TrackingOpponent


class SelfPlayOpponent:
    """Randomly picks one of the saved checkpoints to act as the opponent.

    Falls back to a TrackingOpponent until at least one checkpoint exists,
    so training can start in self-play mode from scratch.
    """

    def __init__(self, model_dir: str, fallback: Opponent, rng: random.Random) -> None:
        self._model_dir = model_dir
        self._fallback = fallback
        self._rng = rng
        self._current: Opponent = fallback

    def choose_action(self, observation: np.ndarray) -> int:
        return self._current.choose_action(observation)

    def reset(self, seed: int | None = None) -> None:
        checkpoints = sorted(glob.glob(os.path.join(self._model_dir, "checkpoint_*.zip")))
        if checkpoints:
            chosen = self._rng.choice(checkpoints)
            self._current = ModelOpponent(chosen)
        else:
            self._current = self._fallback
        self._current.reset(seed)


class SelfPlayResetCallback(BaseCallback):
    """Forces the vec env to reset periodically so SelfPlayOpponent re-samples a checkpoint."""

    def __init__(self, reset_every: int) -> None:
        super().__init__()
        self.reset_every = reset_every

    def _on_step(self) -> bool:
        if self.n_calls % self.reset_every == 0:
            self.training_env.reset()
        return True


def build_opponent(name: str, model_dir: str, seed: int) -> Opponent:
    rng = random.Random(seed)
    if name == "random":
        return RandomOpponent(rng=rng)
    if name == "tracking":
        return TrackingOpponent(imperfection=0.1, rng=rng)
    if name == "self_play":
        return SelfPlayOpponent(model_dir, TrackingOpponent(imperfection=0.2, rng=rng), rng)
    raise ValueError(f"Unknown opponent: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a PPO Pong agent.")
    parser.add_argument("--timesteps", type=int, default=100_000)
    parser.add_argument(
        "--opponent",
        type=str,
        default="tracking",
        choices=["random", "tracking", "self_play"],
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model-dir", type=str, default="models")
    parser.add_argument("--checkpoint-frequency", type=int, default=25_000)
    parser.add_argument(
        "--ent-coef",
        type=float,
        default=0.01,
        help="Entropy bonus coefficient; higher values discourage the policy "
        "from collapsing to a single action before it learns to track the ball.",
    )
    parser.add_argument(
        "--init-model",
        type=str,
        default=None,
        help="Path to an existing model to continue training from, instead of "
        "starting a fresh policy. Useful for curriculum training (e.g. random -> tracking).",
    )
    parser.add_argument(
        "--eval-frequency",
        type=int,
        default=None,
        help="Evaluate deterministically every N steps and keep the best-performing "
        "checkpoint as best_model.zip, since training reward can regress over long "
        "runs. Defaults to --checkpoint-frequency.",
    )
    parser.add_argument("--eval-episodes", type=int, default=20)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    os.makedirs(args.model_dir, exist_ok=True)

    opponent = build_opponent(args.opponent, args.model_dir, args.seed)
    env = PongEnv(opponent=opponent, render_mode=None)

    if args.init_model:
        print(f"Continuing training from {args.init_model}")
        model = PPO.load(args.init_model, env=env)
        model.ent_coef = args.ent_coef
    else:
        model = PPO(
            "MlpPolicy",
            env,
            seed=args.seed,
            policy_kwargs={"net_arch": [64, 64]},
            n_steps=2048,
            batch_size=256,
            ent_coef=args.ent_coef,
            verbose=1,
        )

    checkpoint_callback = CheckpointCallback(
        save_freq=args.checkpoint_frequency,
        save_path=args.model_dir,
        name_prefix="checkpoint",
    )

    eval_opponent = build_opponent(args.opponent, args.model_dir, args.seed + 1000)
    eval_env = Monitor(PongEnv(opponent=eval_opponent, render_mode=None))
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=args.model_dir,
        log_path=args.model_dir,
        eval_freq=args.eval_frequency or args.checkpoint_frequency,
        n_eval_episodes=args.eval_episodes,
        deterministic=True,
    )

    callbacks = [checkpoint_callback, eval_callback]
    if args.opponent == "self_play":
        callbacks.append(SelfPlayResetCallback(reset_every=args.checkpoint_frequency))

    model.learn(total_timesteps=args.timesteps, callback=callbacks)

    final_model_path = os.path.join(args.model_dir, "final_model.zip")
    model.save(final_model_path)
    print(f"Saved final-step model to {final_model_path}")
    print(
        f"Best evaluated model (highest mean eval reward) saved to "
        f"{os.path.join(args.model_dir, 'best_model.zip')}"
    )


if __name__ == "__main__":
    main()
