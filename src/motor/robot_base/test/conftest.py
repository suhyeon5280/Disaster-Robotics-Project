import math

import pytest

from robot_base.robot_config import RobotConfig


@pytest.fixture
def config() -> RobotConfig:
    """계산하기 쉬운 테스트용 치수: 바퀴 둘레 1m, 1000 tick/rev → 1 tick = 1mm."""
    return RobotConfig(
        wheel_radius_m=1 / (2 * math.pi),
        wheel_base_m=0.2,
        left_ticks_per_rev=1000,
        right_ticks_per_rev=1000,
        max_wheel_speed_mps=0.5,
    )
