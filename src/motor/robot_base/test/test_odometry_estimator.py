import dataclasses
import math

import pytest

from robot_base.diff_drive_kinematics import DiffDriveKinematics
from robot_base.odometry_estimator import OdometryEstimator, OdometryState
from robot_base.robot_config import RobotConfig

INT32_MAX = 2**31 - 1
INT32_MIN = -(2**31)
UINT32_MAX = 2**32 - 1


@pytest.fixture
def estimator(config: RobotConfig) -> OdometryEstimator:
    return OdometryEstimator(DiffDriveKinematics(config))


@pytest.fixture
def spin_estimator(config: RobotConfig) -> OdometryEstimator:
    """양쪽 바퀴가 1000 tick씩 반대로 돌면 정확히 90° 도는 바퀴 간격 (4/π m)."""
    spin_config = dataclasses.replace(config, wheel_base_m=4 / math.pi)
    return OdometryEstimator(DiffDriveKinematics(spin_config))


def assert_state(
    state: OdometryState,
    x_m: float,
    y_m: float,
    theta_rad: float,
    linear_mps: float = 0.0,
    angular_radps: float = 0.0,
    abs_tol: float = 1e-9,
) -> None:
    assert state.x_m == pytest.approx(x_m, abs=abs_tol)
    assert state.y_m == pytest.approx(y_m, abs=abs_tol)
    assert state.theta_rad == pytest.approx(theta_rad, abs=abs_tol)
    assert state.linear_mps == pytest.approx(linear_mps, abs=abs_tol)
    assert state.angular_radps == pytest.approx(angular_radps, abs=abs_tol)


def test_first_update_only_sets_baseline(estimator: OdometryEstimator) -> None:
    state = estimator.update(time_ms=1000, left_ticks=5000, right_ticks=-3000)
    assert_state(state, 0.0, 0.0, 0.0)
    assert estimator.state == state


def test_straight_one_meter(estimator: OdometryEstimator) -> None:
    estimator.update(1000, 5000, -3000)
    state = estimator.update(2000, 6000, -2000)
    assert_state(state, 1.0, 0.0, 0.0, linear_mps=1.0)


def test_straight_backward(estimator: OdometryEstimator) -> None:
    estimator.update(0, 0, 0)
    state = estimator.update(500, -250, -250)
    assert_state(state, -0.25, 0.0, 0.0, linear_mps=-0.5)


def test_spin_in_place_90_degrees(spin_estimator: OdometryEstimator) -> None:
    spin_estimator.update(0, 0, 0)
    state = spin_estimator.update(1000, -1000, 1000)
    assert_state(state, 0.0, 0.0, math.pi / 2, angular_radps=math.pi / 2)


def test_spin_in_place_360_degrees_wraps_theta(spin_estimator: OdometryEstimator) -> None:
    spin_estimator.update(0, 0, 0)
    expected_thetas_rad = [math.pi / 2, math.pi, -math.pi / 2, 0.0]
    for step, expected_theta_rad in enumerate(expected_thetas_rad, start=1):
        state = spin_estimator.update(step * 1000, -step * 1000, step * 1000)
        assert abs(math.remainder(state.theta_rad - expected_theta_rad, 2 * math.pi)) < 1e-9
        assert -math.pi <= state.theta_rad <= math.pi
    assert_state(state, 0.0, 0.0, 0.0, angular_radps=math.pi / 2)


def test_quarter_circle_arc(estimator: OdometryEstimator) -> None:
    # 반지름 1m 원을 반시계로 1/4 돌면 (0, 0, 0) → (1, 1, π/2).
    radius_m = 1.0
    half_base_m = 0.1
    left_total_ticks = (math.pi / 2) * (radius_m - half_base_m) * 1000
    right_total_ticks = (math.pi / 2) * (radius_m + half_base_m) * 1000
    steps = 100

    estimator.update(0, 0, 0)
    for step in range(1, steps + 1):
        state = estimator.update(
            step * 50,
            round(left_total_ticks * step / steps),
            round(right_total_ticks * step / steps),
        )

    assert state.x_m == pytest.approx(1.0, abs=0.005)
    assert state.y_m == pytest.approx(1.0, abs=0.005)
    assert state.theta_rad == pytest.approx(math.pi / 2, abs=0.01)


def test_tick_counter_overflow(estimator: OdometryEstimator) -> None:
    estimator.update(0, INT32_MAX - 499, INT32_MAX - 499)
    state = estimator.update(1000, INT32_MIN + 500, INT32_MIN + 500)
    assert_state(state, 1.0, 0.0, 0.0, linear_mps=1.0)


def test_tick_counter_underflow(estimator: OdometryEstimator) -> None:
    estimator.update(0, INT32_MIN + 500, INT32_MIN + 500)
    state = estimator.update(1000, INT32_MAX - 499, INT32_MAX - 499)
    assert_state(state, -1.0, 0.0, 0.0, linear_mps=-1.0)


def test_millis_overflow(estimator: OdometryEstimator) -> None:
    estimator.update(UINT32_MAX - 499, 0, 0)
    state = estimator.update(500, 1000, 1000)
    assert_state(state, 1.0, 0.0, 0.0, linear_mps=1.0)


def test_zero_time_step_updates_pose_and_keeps_velocity(estimator: OdometryEstimator) -> None:
    estimator.update(0, 0, 0)
    estimator.update(1000, 1000, 1000)
    state = estimator.update(1000, 1100, 1100)
    assert_state(state, 1.1, 0.0, 0.0, linear_mps=1.0)


def test_reset_clears_state_and_baseline(estimator: OdometryEstimator) -> None:
    estimator.update(0, 0, 0)
    estimator.update(1000, 1000, 1000)

    estimator.reset()
    assert_state(estimator.state, 0.0, 0.0, 0.0)

    state = estimator.update(5000, 7000, 7000)
    assert_state(state, 0.0, 0.0, 0.0)
    state = estimator.update(6000, 7500, 7500)
    assert_state(state, 0.5, 0.0, 0.0, linear_mps=0.5)
