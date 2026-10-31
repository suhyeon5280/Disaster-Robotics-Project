"""Nav2 자율주행: 저장한 지도 + 위치추정(AMCL) + 경로계획/주행. 시뮬레이션과 실물에 같이 쓴다.

/scan, /odom, TF odom→base_link를 받아 TF map→odom과 /cmd_vel을 낸다.
사용 예 (시뮬레이션): ros2 launch robot_bringup navigation.launch.py use_sim_time:=true rviz:=true
다른 지도:           ... map:=$HOME/robot_ws/src/slam/robot_bringup/maps/<이름>.yaml
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """nav2_bringup의 bringup_launch.py에 우리 지도와 설정을 넘기고, RViz(선택)를 띄운다."""
    share_dir = get_package_share_directory('robot_bringup')
    nav2_share = get_package_share_directory('nav2_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='false', description='Gazebo 시계 사용 (시뮬레이션이면 true)'
        ),
        DeclareLaunchArgument(
            'map', default_value=os.path.join(share_dir, 'maps', 'test_room.yaml'),
            description='지도 yaml 파일',
        ),
        DeclareLaunchArgument(
            'params_file', default_value=os.path.join(share_dir, 'config', 'nav2_params.yaml'),
            description='Nav2 설정 파일',
        ),
        DeclareLaunchArgument('rviz', default_value='false', description='Nav2 RViz 띄우기'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_share, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': LaunchConfiguration('map'),
                'params_file': LaunchConfiguration('params_file'),
                'use_sim_time': use_sim_time,
                'slam': 'False',
                'autostart': 'true',
            }.items(),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', os.path.join(nav2_share, 'rviz', 'nav2_default_view.rviz')],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
