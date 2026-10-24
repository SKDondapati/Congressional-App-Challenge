import datetime
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


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
    lesson: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    def __post_init__(self):
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("An experiment goal is required.")
        if not isinstance(self.ticker, str) or not self.ticker.strip():
            raise ValueError("A ticker symbol is required.")
        try:
            self.starting_amount = float(self.starting_amount)
            self.monthly_contribution = float(self.monthly_contribution)
        except (TypeError, ValueError) as error:
            raise ValueError("Amounts must be numbers.") from error
        if not math.isfinite(self.starting_amount) or self.starting_amount < 0:
            raise ValueError("Starting amount must be a non-negative number.")
        if not math.isfinite(self.monthly_contribution) or self.monthly_contribution < 0:
            raise ValueError("Monthly contribution must be a non-negative number.")
        if self.horizon_years is not None:
            try:
                horizon = int(self.horizon_years)
            except (TypeError, ValueError) as error:
                raise ValueError("Time horizon must be a whole number of years.") from error
            if horizon != self.horizon_years or horizon < 1:
                raise ValueError("Time horizon must be a positive whole number of years.")
            self.horizon_years = horizon

        start = self._parse_date(self.start_date)
        end = self._parse_date(self.end_date)
        if start is not None and end is not None and start > end:
            raise ValueError("Start date must be on or before end date.")

    @staticmethod
    def _parse_date(value):
        if value is None:
            return None
        try:
            text = str(value)
            if len(text) == 10:
                return datetime.date.fromisoformat(text)
            return datetime.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError as error:
            raise ValueError("Experiment dates must use YYYY-MM-DD format.") from error

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        if not isinstance(d, dict):
            raise ValueError("Experiment configuration must be a dictionary.")
        keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in keys}
        try:
            return cls(**filtered)
        except TypeError as error:
            raise ValueError("Experiment configuration is missing required fields.") from error

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
        if goal == "Compare investments":
            return cls(
                goal=goal,
                ticker=suggestion,
                starting_amount=10000,
                monthly_contribution=100,
                horizon_years=10,
                strategy="Compare All",
                lesson="How different strategies stack up over the same period",
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
