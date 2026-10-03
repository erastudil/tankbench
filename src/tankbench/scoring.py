from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Score:
    alive_ran: int
    alive_failed: int
    rounds_ran: int
    rounds_hits: int
    measures_ran: int = 0
    measures_passed: int = 0
    alive_failures: list[str] = field(default_factory=list)
    round_misses: list[str] = field(default_factory=list)
    measure_failures: list[str] = field(default_factory=list)

    @property
    def alive_ok(self) -> bool:
        return self.alive_ran > 0 and self.alive_failed == 0

    @property
    def rounds_blocked(self) -> int:
        return self.rounds_ran - self.rounds_hits

    @property
    def blocked_ratio(self) -> float:
        if self.rounds_ran == 0:
            return 0.0
        return self.rounds_blocked / self.rounds_ran

    @property
    def measures_ratio(self) -> float:
        if self.measures_ran == 0:
            return 0.0
        return self.measures_passed / self.measures_ran

    @property
    def value(self) -> float:
        if not self.alive_ok:
            return 0.0
        if self.rounds_ran == 0 and self.measures_ran == 0:
            return 0.0
        if self.measures_ran == 0:
            return self.blocked_ratio
        # Composite rubric: 50% offensive backdoor resistance + 50% preventative armory tooling
        return (0.5 * self.blocked_ratio) + (0.5 * self.measures_ratio)

    @property
    def perfect(self) -> bool:
        return (
            self.alive_ok
            and self.rounds_hits == 0
            and self.rounds_ran > 0
            and (self.measures_ran == 0 or self.measures_passed == self.measures_ran)
        )


def fold(
    *,
    alive_ran: int,
    alive_failed: int,
    rounds_ran: int,
    rounds_hits: int,
    measures_ran: int = 0,
    measures_passed: int = 0,
) -> Score:
    return Score(
        alive_ran=alive_ran,
        alive_failed=alive_failed,
        rounds_ran=rounds_ran,
        rounds_hits=rounds_hits,
        measures_ran=measures_ran,
        measures_passed=measures_passed,
    )
