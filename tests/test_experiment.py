import datetime

import pytest

from ui.experiment import ExperimentConfig


def test_each_experiment_gets_a_timezone_aware_timestamp():
    first = ExperimentConfig("Learn about risk")
    second = ExperimentConfig("Learn about risk")

    first_time = datetime.datetime.fromisoformat(first.created_at)
    second_time = datetime.datetime.fromisoformat(second.created_at)
    assert first_time.tzinfo is not None
    assert second_time.tzinfo is not None
    assert first.created_at != second.created_at


@pytest.mark.parametrize(
    "values",
    [
        {"goal": "", "ticker": "VTI"},
        {"goal": "Risk", "ticker": " "},
        {"goal": "Risk", "starting_amount": -1},
        {"goal": "Risk", "monthly_contribution": -1},
        {"goal": "Risk", "horizon_years": 0},
        {"goal": "Risk", "start_date": "not-a-date"},
        {"goal": "Risk", "start_date": "2024-02-01", "end_date": "2024-01-01"},
    ],
)
def test_imported_experiments_reject_invalid_values(values):
    with pytest.raises(ValueError):
        ExperimentConfig.from_dict(values)


def test_removed_weights_are_ignored_when_importing_old_config():
    experiment = ExperimentConfig.from_dict(
        {"goal": "Risk", "ticker": "VTI", "weights": {"VTI": 1.0}}
    )

    assert not hasattr(experiment, "weights")