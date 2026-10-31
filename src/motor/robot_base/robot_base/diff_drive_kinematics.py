"""차동구동 기구학: 차체 속도 (v, ω) ↔ 바퀴 속도 (tick/s)."""

import math
from dataclasses import dataclass

from robot_base.robot_config import RobotConfig


@dataclass(frozen=True)
class WheelSpeeds:
    """양쪽 바퀴 속도. +는 로봇 전진 방향."""

    left_tps: float
    right_tps: float


@dataclass(frozen=True)
class BodyVelocity:
    """base_link 기준 차체 속도. 각속도는 반시계 방향이 +."""

    linear_mps: float
    angular_radps: float


class DiffDriveKinematics:
    """차체 속도와 바퀴 속도 사이의 변환."""

    def __init__(self, config: RobotConfig) -> None:
        self._config = config
        wheel_circumference_m = 2 * math.pi * config.wheel_radius_m
        self._left_m_per_tick = wheel_circumference_m / config.left_ticks_per_rev
        self._right_m_per_tick = wheel_circumference_m / config.right_ticks_per_rev

    def body_to_wheels(self, linear_mps: float, angular_radps: float) -> WheelSpeeds:
        """차체 속도를 바퀴 목표 속도로 바꾼다.

        한 바퀴라도 max_wheel_speed_mps를 넘으면 두 바퀴를 같은 비율로 줄여 회전 반경을 유지한다.
        """
        half_base_m = self._config.wheel_base_m / 2
        left_mps = linear_mps - angular_radps * half_base_m
        right_mps = linear_mps + angular_radps * half_base_m

        fastest_mps = max(abs(left_mps), abs(right_mps))
        if fastest_mps > self._config.max_wheel_speed_mps:
            scale = self._config.max_wheel_speed_mps / fastest_mps
            left_mps *= scale
            right_mps *= scale

        return WheelSpeeds(
            left_tps=left_mps / self._left_m_per_tick,
            right_tps=right_mps / self._right_m_per_tick,
        )

    def wheels_to_body(self, left_tps: float, right_tps: float) -> BodyVelocity:
        """바퀴 속도를 차체 속도로 바꾼다."""
        left_mps = left_tps * self._left_m_per_tick
        right_mps = right_tps * self._right_m_per_tick
        return BodyVelocity(
            linear_mps=(left_mps + right_mps) / 2,
            angular_radps=(right_mps - left_mps) / self._config.wheel_base_m,
        )
