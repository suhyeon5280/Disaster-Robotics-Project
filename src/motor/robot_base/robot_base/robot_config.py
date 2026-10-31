"""로봇 치수, 속도 상한, 속도 제어 게인 설정값."""

import math
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class RobotConfig:
    """차동구동 로봇의 치수와 속도 상한.

    값은 params yaml에서 읽어 Node가 생성한다. 모든 값은 0보다 커야 한다.
    """

    wheel_radius_m: float
    wheel_base_m: float
    left_ticks_per_rev: float
    right_ticks_per_rev: float
    max_wheel_speed_mps: float

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            # `not value > 0`은 NaN도 걸러낸다.
            if not value > 0:
                raise ValueError(f'{field.name} must be positive, got {value}')


@dataclass(frozen=True)
class SpeedGains:
    """펌웨어 바퀴 속도 제어 게인 (피드포워드 + PI, 듀티 ±255 기준).

    값은 params yaml에서 읽고, 실행 중 `ros2 param set`으로 바꿀 수 있다. 모든 값은 0 이상이어야 한다.
    """

    kff: float
    kp: float
    ki: float

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if not (math.isfinite(value) and value >= 0):
                raise ValueError(f'{field.name} must be finite and non-negative, got {value}')
