"""모터부 실행: robot_base 노드. 사용 예: ros2 launch robot_base base.launch.py [port:=/dev/pts/3]"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """robot_base 노드를 yaml 파라미터와 port 인자로 실행한다. 시리얼 오류로 죽으면 2초 뒤 재시작."""
    params_file = os.path.join(
        get_package_share_directory('robot_base'), 'config', 'robot_base.yaml'
    )
    return LaunchDescription([
        DeclareLaunchArgument(
            'port', default_value='/dev/ttyACM0', description='32u4 시리얼 포트'
        ),
        Node(
            package='robot_base',
            executable='diff_drive_bridge',
            name='robot_base',
            parameters=[params_file, {'port': LaunchConfiguration('port')}],
            output='screen',
            respawn=True,
            respawn_delay=2.0,
        ),
    ])
