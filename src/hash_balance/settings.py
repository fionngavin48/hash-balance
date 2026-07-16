"""Configurable parameters for the hash balance analysis."""

from dataclasses import dataclass, field

from hash_balance.constants import auto_threshold
from hash_balance.hash_registry import DEFAULT_HASH_TARGETS, HashTarget
from hash_balance.inputs import INPUT_MODE_LABELS, InputMode
from hash_balance.modes import AnalysisMode


@dataclass
class AnalysisSettings:
    """Runtime settings for chi-squared hash uniformity analysis."""

    mode: AnalysisMode = "hash_balance"
    sample_size: int = 10_000
    bucket_count: int = 256
    threshold: float = field(default_factory=lambda: auto_threshold(256))
    auto_threshold: bool = True
    input_mode: InputMode = "sequential"
    input_prefix: str = "user:"
    random_seed: int = 0
    preview_count: int = 10
    hashes: list[HashTarget] = field(default_factory=lambda: [
        HashTarget(target.name, target.path, target.enabled)
        for target in DEFAULT_HASH_TARGETS
    ])

    def sync_threshold(self) -> None:
        """Refresh the auto threshold after bucket-count changes."""
        if self.auto_threshold:
            self.threshold = auto_threshold(self.bucket_count)

    def summary_lines(self) -> list[str]:
        """Return human-readable lines describing the current settings."""
        threshold_label = (
            f"{self.threshold:.1f} (auto)"
            if self.auto_threshold
            else f"{self.threshold:g} (manual)"
        )

        return [
            f"Sample size:      {self.sample_size:,}",
            f"Bucket count:     {self.bucket_count}",
            f"Input mode:       {INPUT_MODE_LABELS[self.input_mode]}",
            f"Input prefix:     {self.input_prefix!r}",
            f"Random seed:      {self.random_seed}",
            f"Chi² threshold:   {threshold_label}",
            f"Preview outputs:  {self.preview_count}",
        ]

    def hash_target_lines(self) -> list[str]:
        """Return configured hash targets with enabled/disabled state."""
        lines = ["Detected hash files:", ""]

        if not self.hashes:
            lines.append("  > (none configured)")
            return lines

        lines.extend(
            f"  > [{'enabled' if target.enabled else 'disabled'}] "
            f"{target.name}: {target.path}"
            for target in self.hashes
        )
        return lines


DEFAULT_SETTINGS = AnalysisSettings()
