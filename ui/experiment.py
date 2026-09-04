from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import datetime


@dataclass
class ExperimentConfig:
    goal: str
    ticker: str = "VTI"
    starting_amount: float = 10000.0
    monthly_contribution: float = 0.0
    horizon_years: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strategy: str = "Buy & Hold"
    weights: Optional[Dict[str, float]] = None
    lesson: Optional[str] = None
    created_at: str = datetime.datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        # allow partial dicts
        keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in keys}
        return cls(**filtered)

    @classmethod
    def preset_for_goal(cls, goal: str, suggestion: str = "VTI"):
        if goal == "Grow money over time":
            return cls(
                goal=goal,
                ticker=suggestion,
                starting_amount=10000,
                monthly_contribution=250,
                horizon_years=20,
                lesson="How time and contributions affect growth",
            )
        if goal == "Understand risk":
            return cls(
                goal=goal,
                ticker=suggestion,
                starting_amount=10000,
                monthly_contribution=0,
                horizon_years=10,
                lesson="What market crashes look like",
            )
        # default
        return cls(
            goal=goal,
            ticker=suggestion,
            starting_amount=10000,
            monthly_contribution=100,
            horizon_years=10,
            lesson="Explore this question",
        )
