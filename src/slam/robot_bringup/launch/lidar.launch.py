"""LiDAR: RPLIDAR A1 드라이버(rplidar_ros). /scan(frame laser)을 낸다.

단독 사용 예 (노트북에 LiDAR를 꽂아 확인): ros2 launch robot_bringup lidar.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """rplidar_node를 yaml 설정과 lidar_port 인자로 실행한다. 연결이 끊겨 죽으면 2초 뒤 재시작."""
    params_file = os.path.join(
        get_package_share_directory('robot_bringup'), 'config', 'rplidar.yaml'
    )
    return LaunchDescription([
        DeclareLaunchArgument(
            'lidar_port', default_value='/dev/ttyUSB0', description='RPLIDAR 시리얼 포트'
        ),
        Node(
            package='rplidar_ros',
            executable='rplidar_node',
            name='rplidar_node',
            parameters=[params_file, {'serial_port': LaunchConfiguration('lidar_port')}],
            output='screen',
            respawn=True,
            respawn_delay=2.0,
        ),
    ])
