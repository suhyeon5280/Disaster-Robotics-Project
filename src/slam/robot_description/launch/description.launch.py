"""로봇 모델 발행: robot_state_publisher (+ 실물용 joint_state_publisher, 선택으로 RViz).

사용 예: ros2 launch robot_description description.launch.py rviz:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    """robot_state_publisher, joint_state_publisher(선택), RViz(선택)를 실행한다."""
    share_dir = get_package_share_directory('robot_description')
    xacro_file = os.path.join(share_dir, 'urdf', 'robot.urdf.xacro')
    rviz_file = os.path.join(share_dir, 'rviz', 'description.rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]), value_type=str
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'model', default_value=xacro_file,
            description='xacro 파일 (시뮬레이션은 Gazebo 설정을 더한 xacro를 넘긴다)',
        ),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false', description='Gazebo 시계 사용'
        ),
        DeclareLaunchArgument(
            'use_joint_state_publisher', default_value='true',
            description='바퀴 각도를 0으로 발행 (실물용. Gazebo에서는 플러그인이 발행하므로 false)',
        ),
        DeclareLaunchArgument('rviz', default_value='false', description='RViz로 모델 보기'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': use_sim_time}],
        ),
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(LaunchConfiguration('use_joint_state_publisher')),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
