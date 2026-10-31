"""Gazebo 시뮬레이션: 테스트 방 + 로봇. 실물 모터부와 LiDAR 대신 /odom, TF, /scan을 낸다.

사용 예: ros2 launch robot_gazebo sim.launch.py
         (Gazebo 창 없이: gui:=false, RViz 없이: rviz:=false)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# 로봇을 놓는 높이: base_link(바퀴 축)가 바닥에서 바퀴 반지름(0.0335m)보다 조금 위
SPAWN_Z_M = '0.04'


def generate_launch_description() -> LaunchDescription:
    """Gazebo, robot_state_publisher, 로봇 배치, RViz(선택)를 실행한다."""
    gazebo_share = get_package_share_directory('robot_gazebo')
    description_share = get_package_share_directory('robot_description')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')

    return LaunchDescription([
        DeclareLaunchArgument(
            'world', default_value=os.path.join(gazebo_share, 'worlds', 'test_room.world'),
            description='Gazebo 월드 파일',
        ),
        DeclareLaunchArgument('gui', default_value='true', description='Gazebo 창 띄우기'),
        DeclareLaunchArgument('rviz', default_value='true', description='RViz 띄우기'),
        # URDF의 package://robot_description/meshes/... 를 Gazebo가 찾을 수 있게 한다.
        AppendEnvironmentVariable('GAZEBO_MODEL_PATH', os.path.dirname(description_share)),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={
                'world': LaunchConfiguration('world'),
                'gui': LaunchConfiguration('gui'),
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(description_share, 'launch', 'description.launch.py')
            ),
            launch_arguments={
                'model': os.path.join(gazebo_share, 'urdf', 'robot_gazebo.urdf.xacro'),
                'use_sim_time': 'true',
                # 바퀴 각도는 Gazebo 플러그인이 /joint_states로 낸다.
                'use_joint_state_publisher': 'false',
                'rviz': 'false',
            }.items(),
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-topic', 'robot_description', '-entity', 'robot', '-z', SPAWN_Z_M],
            output='screen',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', os.path.join(gazebo_share, 'rviz', 'sim.rviz')],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
