"""Generate test inputs for hash uniformity analysis."""

from __future__ import annotations

import random
from typing import Literal

InputMode = Literal["sequential", "prefixed", "random"]

INPUT_MODE_LABELS: dict[InputMode, str] = {
    "sequential": "sequential integers (0, 1, 2, ...)",
    "prefixed": "prefixed strings (user:0, user:1, ...)",
    "random": "deterministic random bytes",
}


def generate_inputs(
    sample_size: int,
    *,
    input_mode: InputMode = "sequential",
    input_prefix: str = "user:",
    random_seed: int = 0,
) -> list[bytes]:
    """Build the input byte strings used for one analysis run."""
    if input_mode == "sequential":
        return [index.to_bytes(4, "big") for index in range(sample_size)]
    if input_mode == "prefixed":
        return [f"{input_prefix}{index}".encode() for index in range(sample_size)]

    rng = random.Random(random_seed)
    return [rng.randbytes(8) for _ in range(sample_size)]


def cycle_input_modes(current: InputMode) -> InputMode:
    """Return the next input mode in a simple rotate order."""
    order: list[InputMode] = ["sequential", "prefixed", "random"]
    index = order.index(current)
    return order[(index + 1) % len(order)]
