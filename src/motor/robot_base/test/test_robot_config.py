import dataclasses
import math

import pytest

from robot_base.robot_config import RobotConfig, SpeedGains

FIELD_NAMES = [field.name for field in dataclasses.fields(RobotConfig)]


def test_valid_config_keeps_values(config: RobotConfig) -> None:
    assert config.wheel_base_m == 0.2
    assert config.left_ticks_per_rev == 1000


@pytest.mark.parametrize('field_name', FIELD_NAMES)
@pytest.mark.parametrize('bad_value', [0.0, -1.0, math.nan])
def test_non_positive_value_is_rejected(
    config: RobotConfig, field_name: str, bad_value: float
) -> None:
    with pytest.raises(ValueError, match=field_name):
        dataclasses.replace(config, **{field_name: bad_value})


def test_config_is_immutable(config: RobotConfig) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.wheel_base_m = 0.3  # type: ignore[misc]


def test_gains_allow_zero() -> None:
    gains = SpeedGains(kff=0.0, kp=0.0, ki=0.0)
    assert gains.kp == 0.0


@pytest.mark.parametrize('field_name', ['kff', 'kp', 'ki'])
@pytest.mark.parametrize('bad_value', [-0.1, math.nan, math.inf])
def test_gains_reject_negative_or_non_finite(field_name: str, bad_value: float) -> None:
    gains = SpeedGains(kff=0.06, kp=0.05, ki=0.3)
    with pytest.raises(ValueError, match=field_name):
        dataclasses.replace(gains, **{field_name: bad_value})
