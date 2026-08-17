"""Run the full training curriculum we used by hand: random -> tracking,
each stage continuing from the previous stage's best model.

This just chains scripts/train.py and scripts/evaluate.py together with
--init-model, so each stage builds on the last instead of starting over.

Example:
    uv run python scripts/curriculum.py
    uv run python scripts/curriculum.py --model-dir models/my_curriculum
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

SCRIPTS_DIR = os.path.dirname(__file__)
PYTHON = sys.executable

# (stage name, opponent, timesteps, checkpoint frequency)
STAGES = [
    ("stage1_random", "random", 500_000, 100_000),
    ("stage2_tracking", "tracking", 500_000, 100_000),
    ("stage3_tracking", "tracking", 3_000_000, 500_000),
    ("stage4_tracking", "tracking", 10_000_000, 1_000_000),
    ("stage5_tracking", "tracking", 15_000_000, 1_000_000),
]


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}\n")
    subprocess.run(cmd, check=True)


def evaluate(model_path: str, opponent: str, episodes: int = 100) -> None:
    run(
        [
            PYTHON,
            os.path.join(SCRIPTS_DIR, "evaluate.py"),
            "--model",
            model_path,
            "--opponent",
            opponent,
            "--episodes",
            str(episodes),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the random->tracking training curriculum.")
    parser.add_argument("--model-dir", type=str, default="models/curriculum")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--eval-episodes", type=int, default=30)
    parser.add_argument(
        "--skip-eval",
        action="store_true",
        help="Skip the intermediate evaluate.py calls between stages (faster, less visibility).",
    )
    parser.add_argument(
        "--init-model",
        type=str,
        default=None,
        help="Continue the curriculum from an existing model (e.g. models/best_model.zip) "
        "instead of training stage 1 from scratch. Combine with --start-stage to resume "
        "partway through instead of redoing the random/tracking stages you already have.",
    )
    parser.add_argument(
        "--start-stage",
        type=int,
        default=0,
        help="Skip earlier stages and start at this stage index (0 = stage1_random, "
        "1 = stage2_tracking, etc.). Requires --init-model so there's something to build on.",
    )
    args = parser.parse_args()

    if args.start_stage > 0 and not args.init_model:
        parser.error("--start-stage > 0 requires --init-model")

    previous_model: str | None = args.init_model
    stages = list(enumerate(STAGES))[args.start_stage :]

    for stage_index, (stage_name, opponent, timesteps, checkpoint_freq) in stages:
        stage_dir = os.path.join(args.model_dir, stage_name)
        print(f"\n=== {stage_name}: {timesteps:,} steps vs {opponent} ===")

        train_cmd = [
            PYTHON,
            os.path.join(SCRIPTS_DIR, "train.py"),
            "--timesteps",
            str(timesteps),
            "--opponent",
            opponent,
            "--seed",
            str(args.seed),
            "--model-dir",
            stage_dir,
            "--checkpoint-frequency",
            str(checkpoint_freq),
            "--eval-episodes",
            str(args.eval_episodes),
        ]
        if previous_model:
            train_cmd += ["--init-model", previous_model]

        run(train_cmd)

        best_model = os.path.join(stage_dir, "best_model.zip")
        if not args.skip_eval:
            evaluate(best_model, "random", episodes=100)
            evaluate(best_model, "tracking", episodes=100)

        previous_model = best_model

    print(f"\nCurriculum complete. Final model: {previous_model}")


if __name__ == "__main__":
    main()
