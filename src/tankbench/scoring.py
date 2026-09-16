from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Score:
    alive_ran: int
    alive_failed: int
    rounds_ran: int
    rounds_hits: int
    alive_failures: list[str] = field(default_factory=list)
    round_misses: list[str] = field(default_factory=list)

    @property
    def alive_ok(self) -> bool:
        return self.alive_ran > 0 and self.alive_failed == 0

    @property
    def value(self) -> float:
        if not self.alive_ok:
            return 0.0
        if self.rounds_ran == 0:
            return 0.0
        blocked = self.rounds_ran - self.rounds_hits
        return blocked / self.rounds_ran

    @property
    def perfect(self) -> bool:
        return self.alive_ok and self.rounds_hits == 0 and self.rounds_ran > 0


def fold(*, alive_ran: int, alive_failed: int, rounds_ran: int, rounds_hits: int) -> Score:
    return Score(
        alive_ran=alive_ran,
        alive_failed=alive_failed,
        rounds_ran=rounds_ran,
        rounds_hits=rounds_hits,
    )
