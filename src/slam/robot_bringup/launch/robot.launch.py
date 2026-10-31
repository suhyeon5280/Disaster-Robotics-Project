"""실물 로봇 통합 실행 (LattePanda). 모터부 + LiDAR + 로봇 모델에, 모드에 따라 SLAM 또는 Nav2를 더한다.

  mode:=base  모터부 + LiDAR + 로봇 모델 (조종, 보정, 센서 확인)
  mode:=slam  + slam_toolbox (지도 만들기)
  mode:=nav   + Nav2 (저장한 지도로 자율주행, map:=<지도.yaml> 필수)

사용 예: ros2 launch robot_bringup robot.launch.py mode:=slam
         ros2 launch robot_bringup robot.launch.py mode:=nav \
             map:=$HOME/robot_ws/src/slam/robot_bringup/maps/<이름>.yaml
시뮬레이션에서는 이 파일 대신 robot_gazebo의 sim.launch.py가 모터부와 LiDAR 역할을 한다.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

MODES = ('base', 'slam', 'nav')


def _include(
    package: str, launch_file: str, arguments: dict[str, str]
) -> IncludeLaunchDescription:
    path = os.path.join(get_package_share_directory(package), 'launch', launch_file)
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(path), launch_arguments=arguments.items()
    )


def _launch_setup(context: LaunchContext) -> list[IncludeLaunchDescription]:
    mode = LaunchConfiguration('mode').perform(context)
    map_file = LaunchConfiguration('map').perform(context)
    rviz = LaunchConfiguration('rviz').perform(context)
    if mode not in MODES:
        raise RuntimeError(f"mode:={mode} 는 지원하지 않습니다. {', '.join(MODES)} 중 하나를 쓰세요.")
    if mode == 'nav' and not map_file:
        raise RuntimeError('mode:=nav 에는 map:=<지도.yaml> 이 필요합니다 (실물에서 만든 지도).')

    port = LaunchConfiguration('port').perform(context)
    lidar_port = LaunchConfiguration('lidar_port').perform(context)
    actions = [
        _include('robot_base', 'base.launch.py', {'port': port}),
        _include('robot_bringup', 'lidar.launch.py', {'lidar_port': lidar_port}),
        _include('robot_description', 'description.launch.py', {
            'use_sim_time': 'false',
            'use_joint_state_publisher': 'true',
            # base 모드의 RViz는 로봇 모델과 스캔을 base_link 기준으로 보여준다.
            'rviz': rviz if mode == 'base' else 'false',
        }),
    ]
    if mode == 'slam':
        actions.append(_include('robot_bringup', 'slam.launch.py',
                                {'use_sim_time': 'false', 'rviz': rviz}))
    elif mode == 'nav':
        actions.append(_include('robot_bringup', 'navigation.launch.py',
                                {'use_sim_time': 'false', 'map': map_file, 'rviz': rviz}))
    return actions


def generate_launch_description() -> LaunchDescription:
    """모드 인자를 확인하고, 모드에 맞는 launch 파일들을 불러온다."""
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='base', description='base, slam, nav 중 하나'),
        DeclareLaunchArgument('map', default_value='', description='mode:=nav 에서 쓸 지도 yaml'),
        DeclareLaunchArgument('port', default_value='/dev/ttyACM0', description='32u4 시리얼 포트'),
        DeclareLaunchArgument(
            'lidar_port', default_value='/dev/ttyUSB0', description='RPLIDAR 시리얼 포트'
        ),
        DeclareLaunchArgument(
            'rviz', default_value='false',
            description='RViz 띄우기 (보통 LattePanda가 아니라 노트북에서 본다)',
        ),
        OpaqueFunction(function=_launch_setup),
    ])
