from setuptools import find_packages, setup

package_name = 'robot_base'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/robot_base.yaml']),
        ('share/' + package_name + '/launch', ['launch/base.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='suhyeon',
    maintainer_email='u260208@kist.re.kr',
    description='32u4 펌웨어와 시리얼로 통신하는 차동구동 베이스 브릿지 노드',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'diff_drive_bridge = robot_base.diff_drive_bridge_node:main',
        ],
    },
)
