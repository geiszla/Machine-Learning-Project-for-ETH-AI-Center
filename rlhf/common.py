"""Utility function for the RLHF Blender project."""

import os
from os import path
from pathlib import Path
from typing import Literal, Union

import torch

from .types import FeedbackType

# Set these two before each experiment
EXPERIMENT_NUBMER = 9
FEEDBACK_TYPE: FeedbackType = "corrective"

# Additional configuration options
ALGORITHM: Union[Literal["sac"], Literal["ppo"]] = "sac"
ENVIRONMENT_NAME = "HalfCheetah-v3"
USE_SDE = False
USE_REWARD_DIFFERENCE = False

STEPS_PER_CHECKPOINT = 10000

# Paths and other variables used by multiple scripts
FEEDBACK_ID = "_".join([ALGORITHM, ENVIRONMENT_NAME, *(["sde"] if USE_SDE else [])])
MODEL_ID = f"#{EXPERIMENT_NUBMER}_{FEEDBACK_ID}"

script_path = Path(__file__).parent.resolve()
checkpoints_path = path.join(script_path, "..", "rl_checkpoints")

cpu_count = os.cpu_count()
cpu_count = cpu_count if cpu_count is not None else 8

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# Common functions
def get_reward_model_name(postfix: int | str, is_without_feedback: bool = False):
    """Return the name of the trained reward model by the number postfix."""
    return "_".join(
        [
            MODEL_ID,
            *([FEEDBACK_TYPE] if not is_without_feedback else []),
            *(["diff"] if USE_REWARD_DIFFERENCE and not is_without_feedback else []),
            str(postfix),
        ]
    )
