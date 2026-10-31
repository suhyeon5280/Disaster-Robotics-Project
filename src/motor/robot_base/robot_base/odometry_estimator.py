"""엔코더 누적 tick으로 오도메트리(위치, 방향, 속도)를 추정한다."""

import math
from dataclasses import dataclass

from robot_base.diff_drive_kinematics import DiffDriveKinematics

MS_PER_S = 1000.0
UINT32_RANGE = 2**32
INT32_HALF_RANGE = 2**31


@dataclass(frozen=True)
class OdometryState:
    """odom 프레임 기준 위치·방향과 base_link 기준 속도."""

    x_m: float
    y_m: float
    theta_rad: float
    linear_mps: float
    angular_radps: float


class OdometryEstimator:
    """엔코더 누적 tick의 변화량을 적분해 로봇 상태를 추정한다."""

    def __init__(self, kinematics: DiffDriveKinematics) -> None:
        self._kinematics = kinematics
        self._state = OdometryState(0.0, 0.0, 0.0, 0.0, 0.0)
        self._last_reading: tuple[int, int, int] | None = None

    @property
    def state(self) -> OdometryState:
        """마지막으로 추정한 상태."""
        return self._state

    def update(self, time_ms: int, left_ticks: int, right_ticks: int) -> OdometryState:
        """새 엔코더 값으로 상태를 갱신한다.

        처음 호출하면 기준점만 잡고 현재 상태를 그대로 반환한다.
        시간 간격이 0이면 위치는 갱신하고 속도는 이전 값을 유지한다.
        """
        last_reading = self._last_reading
        self._last_reading = (time_ms, left_ticks, right_ticks)
        if last_reading is None:
            return self._state

        last_time_ms, last_left_ticks, last_right_ticks = last_reading
        dt_s = ((time_ms - last_time_ms) % UINT32_RANGE) / MS_PER_S
        delta_left_ticks = _int32_delta(left_ticks, last_left_ticks)
        delta_right_ticks = _int32_delta(right_ticks, last_right_ticks)

        # 변환이 선형이므로 tick 변화량을 넣으면 속도 대신 이동 거리와 회전각이 나온다.
        displacement = self._kinematics.wheels_to_body(delta_left_ticks, delta_right_ticks)
        distance_m = displacement.linear_mps
        delta_theta_rad = displacement.angular_radps

        # 중점 적분: 이번 구간의 평균 방향으로 이동했다고 본다.
        mid_theta_rad = self._state.theta_rad + delta_theta_rad / 2
        x_m = self._state.x_m + distance_m * math.cos(mid_theta_rad)
        y_m = self._state.y_m + distance_m * math.sin(mid_theta_rad)
        theta_rad = math.remainder(self._state.theta_rad + delta_theta_rad, 2 * math.pi)

        if dt_s > 0:
            linear_mps = distance_m / dt_s
            angular_radps = delta_theta_rad / dt_s
        else:
            linear_mps = self._state.linear_mps
            angular_radps = self._state.angular_radps

        self._state = OdometryState(x_m, y_m, theta_rad, linear_mps, angular_radps)
        return self._state

    def reset(self) -> None:
        """위치와 속도를 0으로 되돌리고, 다음 update를 새 기준점으로 삼는다."""
        self._state = OdometryState(0.0, 0.0, 0.0, 0.0, 0.0)
        self._last_reading = None


def _int32_delta(current: int, previous: int) -> int:
    """signed 32비트 카운터의 변화량. 넘침(overflow)이 한 번 있어도 올바른 값을 준다."""
    return (current - previous + INT32_HALF_RANGE) % UINT32_RANGE - INT32_HALF_RANGE
