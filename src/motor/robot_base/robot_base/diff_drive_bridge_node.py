"""ROS 토픽과 32u4 시리얼 메시지를 이어주는 차동구동 베이스 노드."""

import dataclasses
import math
import sys
from typing import Any, Callable

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.duration import Duration
from rclpy.logging import get_logger
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.time import Time
from tf2_ros import TransformBroadcaster

from robot_base.bridge_protocol import BridgeProtocol
from robot_base.diff_drive_kinematics import DiffDriveKinematics
from robot_base.odometry_estimator import OdometryEstimator, OdometryState
from robot_base.robot_config import RobotConfig, SpeedGains
from robot_base.serial_transport import SerialTransport
from robot_base.transport import Transport, TransportError

QUEUE_DEPTH = 10
GAIN_PARAMETER_NAMES = ('kff', 'kp', 'ki')


class DiffDriveBridgeNode(Node):
    """/cmd_vel을 V 메시지로, E 메시지를 /odom과 TF odom→base_link로 바꾼다.

    파라미터는 모두 yaml에서 받는다 (config/robot_base.yaml). 실행 중에는 게인(kff, kp, ki)만
    바꿀 수 있고, 바뀌면 G 메시지로 펌웨어에 보낸다. 시리얼 오류가 나면 TransportError가
    spin 밖으로 전달되어 노드가 종료되고, launch의 respawn이 다시 실행한다.
    """

    def __init__(
        self, transport_factory: Callable[[str, int], Transport] = SerialTransport
    ) -> None:
        super().__init__('robot_base')
        port = self._declare('port', Parameter.Type.STRING)
        baud_rate = self._declare('baud_rate', Parameter.Type.INTEGER)
        config = RobotConfig(
            wheel_radius_m=self._declare('wheel_radius_m', Parameter.Type.DOUBLE),
            wheel_base_m=self._declare('wheel_base_m', Parameter.Type.DOUBLE),
            left_ticks_per_rev=self._declare('left_ticks_per_rev', Parameter.Type.DOUBLE),
            right_ticks_per_rev=self._declare('right_ticks_per_rev', Parameter.Type.DOUBLE),
            max_wheel_speed_mps=self._declare('max_wheel_speed_mps', Parameter.Type.DOUBLE),
        )
        command_rate_hz = self._declare('command_rate_hz', Parameter.Type.DOUBLE)
        cmd_vel_timeout_s = self._declare('cmd_vel_timeout_s', Parameter.Type.DOUBLE)
        serial_poll_rate_hz = self._declare('serial_poll_rate_hz', Parameter.Type.DOUBLE)
        self._odom_frame_id = self._declare('odom_frame_id', Parameter.Type.STRING)
        self._base_frame_id = self._declare('base_frame_id', Parameter.Type.STRING)
        self._gains = SpeedGains(
            **{
                name: self._declare(name, Parameter.Type.DOUBLE, read_only=False)
                for name in GAIN_PARAMETER_NAMES
            }
        )

        self._protocol = BridgeProtocol()
        self._kinematics = DiffDriveKinematics(config)
        self._odometry = OdometryEstimator(self._kinematics)
        self._transport = transport_factory(port, baud_rate)
        self.get_logger().info(f'opened {port} at {baud_rate} baud')
        # 펌웨어는 G를 받기 전에는 게인이 0이라 움직이지 않으므로 첫 V보다 먼저 보낸다.
        self._transport.write_line(self._protocol.format_gains_command(self._gains))
        self.get_logger().info(f'sent {self._gains}')
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self._cmd_vel_timeout = Duration(seconds=cmd_vel_timeout_s)
        self._latest_cmd_vel = Twist()
        self._latest_cmd_vel_time: Time | None = None

        self._odom_publisher = self.create_publisher(Odometry, 'odom', QUEUE_DEPTH)
        self._tf_broadcaster = TransformBroadcaster(self)
        self.create_subscription(Twist, 'cmd_vel', self._on_cmd_vel, QUEUE_DEPTH)
        self.create_timer(1.0 / command_rate_hz, self._on_command_timer)
        self.create_timer(1.0 / serial_poll_rate_hz, self._on_serial_timer)

    def close(self) -> None:
        """모터 정지 명령을 보내고 포트를 닫는다."""
        try:
            self._transport.write_line(self._protocol.format_velocity_command(0, 0))
        except TransportError:
            pass  # 포트가 이미 끊겼다면 펌웨어가 500ms 뒤 스스로 멈춘다.
        self._transport.close()

    def _declare(self, name: str, parameter_type: Parameter.Type, read_only: bool = True) -> Any:
        # 기본값 없이 선언하므로 yaml에 값이 없으면 ParameterUninitializedException.
        # read_only면 실행 중 `ros2 param set`이 거부된다 (시작할 때만 읽는 값이므로).
        self.declare_parameter(
            name, parameter_type, ParameterDescriptor(read_only=read_only)
        )
        return self.get_parameter(name).value

    def _on_set_parameters(self, parameters: list[Parameter]) -> SetParametersResult:
        changed = {p.name: p.value for p in parameters if p.name in GAIN_PARAMETER_NAMES}
        if not changed:
            return SetParametersResult(successful=True)
        try:
            gains = dataclasses.replace(self._gains, **changed)
            self._transport.write_line(self._protocol.format_gains_command(gains))
        except (TypeError, ValueError, TransportError) as error:
            return SetParametersResult(successful=False, reason=str(error))
        self._gains = gains
        self.get_logger().info(f'sent {gains}')
        return SetParametersResult(successful=True)

    def _on_cmd_vel(self, msg: Twist) -> None:
        if not (math.isfinite(msg.linear.x) and math.isfinite(msg.angular.z)):
            self.get_logger().warn('ignored non-finite /cmd_vel', throttle_duration_sec=1.0)
            return
        self._latest_cmd_vel = msg
        self._latest_cmd_vel_time = self.get_clock().now()

    def _on_command_timer(self) -> None:
        linear_mps = 0.0
        angular_radps = 0.0
        if (
            self._latest_cmd_vel_time is not None
            and self.get_clock().now() - self._latest_cmd_vel_time < self._cmd_vel_timeout
        ):
            linear_mps = self._latest_cmd_vel.linear.x
            angular_radps = self._latest_cmd_vel.angular.z
        wheels = self._kinematics.body_to_wheels(linear_mps, angular_radps)
        self._transport.write_line(
            self._protocol.format_velocity_command(wheels.left_tps, wheels.right_tps)
        )

    def _on_serial_timer(self) -> None:
        for line in self._transport.read_lines():
            reading = self._protocol.parse_encoder_line(line)
            if reading is None:
                self.get_logger().debug(f'ignored line: {line!r}')
                continue
            state = self._odometry.update(
                reading.time_ms, reading.left_ticks, reading.right_ticks
            )
            self._publish(state)

    def _publish(self, state: OdometryState) -> None:
        stamp = self.get_clock().now().to_msg()
        half_theta_rad = state.theta_rad / 2

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self._odom_frame_id
        odom.child_frame_id = self._base_frame_id
        odom.pose.pose.position.x = state.x_m
        odom.pose.pose.position.y = state.y_m
        odom.pose.pose.orientation.z = math.sin(half_theta_rad)
        odom.pose.pose.orientation.w = math.cos(half_theta_rad)
        odom.twist.twist.linear.x = state.linear_mps
        odom.twist.twist.angular.z = state.angular_radps
        self._odom_publisher.publish(odom)

        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = self._odom_frame_id
        transform.child_frame_id = self._base_frame_id
        transform.transform.translation.x = state.x_m
        transform.transform.translation.y = state.y_m
        transform.transform.rotation.z = math.sin(half_theta_rad)
        transform.transform.rotation.w = math.cos(half_theta_rad)
        self._tf_broadcaster.sendTransform(transform)


def main(args: list[str] | None = None) -> None:
    """노드를 실행한다. 시리얼 오류로 끝나면 종료 코드 1을 반환한다."""
    rclpy.init(args=args)
    node: DiffDriveBridgeNode | None = None
    exit_code = 0
    try:
        node = DiffDriveBridgeNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except TransportError as error:
        get_logger('robot_base').error(str(error))
        exit_code = 1
    finally:
        if node is not None:
            node.close()
            node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(exit_code)
