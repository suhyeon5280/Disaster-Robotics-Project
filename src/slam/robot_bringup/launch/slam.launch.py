"""SLAM: slam_toolbox 실시간 지도 작성. 시뮬레이션과 실물에 같이 쓴다.

/scan과 TF odom→base_link를 받아 /map과 TF map→odom을 낸다.
사용 예 (시뮬레이션): ros2 launch robot_bringup slam.launch.py use_sim_time:=true rviz:=true
지도 저장: ros2 run nav2_map_server map_saver_cli -f <경로/이름>
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """slam_toolbox(online async)와 RViz(선택)를 실행한다."""
    share_dir = get_package_share_directory('robot_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='false', description='Gazebo 시계 사용 (시뮬레이션이면 true)'
        ),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=os.path.join(share_dir, 'config', 'slam_toolbox.yaml'),
            description='slam_toolbox 설정 파일',
        ),
        DeclareLaunchArgument('rviz', default_value='false', description='지도 보기용 RViz 띄우기'),
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[LaunchConfiguration('slam_params_file'), {'use_sim_time': use_sim_time}],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', os.path.join(share_dir, 'rviz', 'slam.rviz')],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
