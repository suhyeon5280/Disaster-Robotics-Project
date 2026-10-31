import dataclasses

import pytest

from robot_base.diff_drive_kinematics import DiffDriveKinematics
from robot_base.robot_config import RobotConfig


@pytest.fixture
def kinematics(config: RobotConfig) -> DiffDriveKinematics:
    return DiffDriveKinematics(config)


def test_straight_gives_equal_wheel_speeds(kinematics: DiffDriveKinematics) -> None:
    wheels = kinematics.body_to_wheels(linear_mps=0.3, angular_radps=0.0)
    assert wheels.left_tps == pytest.approx(300)
    assert wheels.right_tps == pytest.approx(300)


def test_spin_in_place_gives_opposite_wheel_speeds(kinematics: DiffDriveKinematics) -> None:
    # ω=1 rad/s, 바퀴 간격 0.2m → 각 바퀴 0.1 m/s. 반시계(+)면 오른쪽이 전진.
    wheels = kinematics.body_to_wheels(linear_mps=0.0, angular_radps=1.0)
    assert wheels.left_tps == pytest.approx(-100)
    assert wheels.right_tps == pytest.approx(100)


def test_straight_over_limit_is_clamped(kinematics: DiffDriveKinematics) -> None:
    wheels = kinematics.body_to_wheels(linear_mps=1.0, angular_radps=0.0)
    assert wheels.left_tps == pytest.approx(500)
    assert wheels.right_tps == pytest.approx(500)


def test_turn_over_limit_keeps_wheel_ratio(kinematics: DiffDriveKinematics) -> None:
    # 제한 전: 왼쪽 0.2 m/s, 오른쪽 0.6 m/s (비율 1:3)
    wheels = kinematics.body_to_wheels(linear_mps=0.4, angular_radps=2.0)
    assert wheels.right_tps == pytest.approx(500)
    assert wheels.left_tps / wheels.right_tps == pytest.approx(1 / 3)


def test_wheels_to_body(kinematics: DiffDriveKinematics) -> None:
    body = kinematics.wheels_to_body(left_tps=-100, right_tps=100)
    assert body.linear_mps == pytest.approx(0.0)
    assert body.angular_radps == pytest.approx(1.0)


def test_round_trip_returns_original(kinematics: DiffDriveKinematics) -> None:
    wheels = kinematics.body_to_wheels(linear_mps=0.2, angular_radps=0.5)
    body = kinematics.wheels_to_body(wheels.left_tps, wheels.right_tps)
    assert body.linear_mps == pytest.approx(0.2)
    assert body.angular_radps == pytest.approx(0.5)


def test_different_ticks_per_rev_per_side(config: RobotConfig) -> None:
    kinematics = DiffDriveKinematics(dataclasses.replace(config, right_ticks_per_rev=2000))

    wheels = kinematics.body_to_wheels(linear_mps=0.3, angular_radps=0.0)
    assert wheels.left_tps == pytest.approx(300)
    assert wheels.right_tps == pytest.approx(600)

    body = kinematics.wheels_to_body(left_tps=300, right_tps=600)
    assert body.linear_mps == pytest.approx(0.3)
    assert body.angular_radps == pytest.approx(0.0)
