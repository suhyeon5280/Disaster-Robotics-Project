# LattePanda 2D SLAM 로봇: 실행 명령

터미널마다 블록을 그대로 붙여넣는다. 끝낼 때는 각 터미널에서 `Ctrl+C`.

---

## LattePanda (실물 로봇)

### 처음 한 번: 설치와 빌드
```bash
sudo apt update && sudo apt upgrade
git clone <이 저장소 주소> ~/robot_ws
cd ~/robot_ws
sudo rosdep init        # 처음 한 번만. 이미 했으면 나오는 오류는 무시
rosdep update
rosdep install --from-paths src/motor src/slam --ignore-src -y
colcon build --packages-skip robot_gazebo
sudo usermod -aG dialout $USER   # 시리얼 포트 권한. 실행 후 로그아웃했다가 다시 로그인
```

### 처음 한 번: arduino-cli 설치
```bash
mkdir -p ~/.local/bin && cd /tmp
curl -fsSLO https://github.com/arduino/arduino-cli/releases/download/v1.5.1/arduino-cli_1.5.1_Linux_64bit.tar.gz
tar -xzf arduino-cli_1.5.1_Linux_64bit.tar.gz arduino-cli
install -m 755 arduino-cli ~/.local/bin/
source ~/.profile
arduino-cli core update-index && arduino-cli core install arduino:avr
```

### 코드를 고친 뒤 (GitHub에서 받기)
```bash
cd ~/robot_ws && git pull && colcon build --packages-skip robot_gazebo
```

### 펌웨어 업로드
업로드 전에 `robot.launch.py`를 끈다 (같은 포트를 쓴다).

처음에는 배선/부호 시험 스케치. 바퀴를 바닥에서 띄우고, 모니터에서 `h` 도움말, `l`/`r` 왼쪽/오른쪽 모터 2초 회전, `z` 카운트 리셋.
부호 4개는 `src/motor/firmware/motor_bridge/config.h`에, 바퀴를 손으로 10바퀴 돌린 tick ÷ 10은 `src/motor/robot_base/config/robot_base.yaml`의 `*_ticks_per_rev`에 적는다.
```bash
cd ~/robot_ws
arduino-cli compile --fqbn arduino:avr:leonardo src/motor/firmware/motor_encoder_test
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo src/motor/firmware/motor_encoder_test
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```
본 펌웨어
```bash
cd ~/robot_ws
arduino-cli compile --fqbn arduino:avr:leonardo src/motor/firmware/motor_bridge
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo src/motor/firmware/motor_bridge
```

### 조종 (모터 + LiDAR + 로봇 모델)
**터미널 1**
```bash
cd ~/robot_ws && source install/setup.bash
ros2 launch robot_bringup robot.launch.py mode:=base
```
**터미널 2**: 방향키를 누르는 동안만 이동
```bash
cd ~/robot_ws && source install/setup.bash
ros2 run key_teleop key_teleop --ros-args -r key_vel:=cmd_vel -p forward_rate:=0.2 -p backward_rate:=0.2 -p rotation_rate:=0.5
```
**게인 튜닝** (터미널 1이 켜진 상태에서, 소수점 필수)
```bash
cd ~/robot_ws && source install/setup.bash
ros2 param set /robot_base kp 0.08
```

### 지도 만들기
**터미널 1**
```bash
cd ~/robot_ws && source install/setup.bash
ros2 launch robot_bringup robot.launch.py mode:=slam
```
**터미널 2**: 조종 (위 "조종"의 터미널 2와 같음)
```bash
cd ~/robot_ws && source install/setup.bash
ros2 run key_teleop key_teleop --ros-args -r key_vel:=cmd_vel -p forward_rate:=0.2 -p backward_rate:=0.2 -p rotation_rate:=0.5
```
**터미널 3**: 다 그렸으면 저장 (`<이름>`을 바꾼다)
```bash
cd ~/robot_ws && source install/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/robot_ws/src/slam/robot_bringup/maps/<이름>
```

### 자율주행
조종 프로그램(`key_teleop`)은 끈다.
```bash
cd ~/robot_ws && source install/setup.bash
ros2 launch robot_bringup robot.launch.py mode:=nav map:=$HOME/robot_ws/src/slam/robot_bringup/maps/<이름>.yaml
```

### 포트가 다를 때
위 `robot.launch.py` 명령 끝에 붙인다.
```bash
port:=/dev/ttyACM1 lidar_port:=/dev/ttyUSB1
```

### 화면 보기
LattePanda에 모니터가 있으면 `robot.launch.py` 명령 끝에 `rviz:=true`를 붙인다.

노트북에서 보려면 (로봇 완성 후 확인 필요): 두 컴퓨터를 같은 Wi-Fi에 두고, **양쪽 모든 터미널**에서 같은 번호를 먼저 설정한다.
```bash
export ROS_DOMAIN_ID=30
```
노트북 터미널
```bash
export ROS_DOMAIN_ID=30
rviz2 -d /opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz
```
RViz에서 **Nav2 Goal**을 클릭하고, 지도 위를 클릭한 채 끌어 목표 위치와 방향을 정한다.

---

## 노트북 (시뮬레이션)

### 빌드
```bash
conda deactivate 2>/dev/null; source /opt/ros/humble/setup.bash
cd ~/robot_ws && colcon build
```

### 시뮬레이션 지도 만들기
**터미널 1**: Gazebo
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 launch robot_gazebo sim.launch.py rviz:=false
```
**터미널 2**: SLAM + 지도 화면
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 launch robot_bringup slam.launch.py use_sim_time:=true rviz:=true
```
**터미널 3**: 조종
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 run key_teleop key_teleop --ros-args -r key_vel:=cmd_vel -p forward_rate:=0.2 -p backward_rate:=0.2 -p rotation_rate:=0.5
```
**터미널 4**: 저장 (`test_room`은 기본 지도라 다른 이름을 쓴다)
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 run nav2_map_server map_saver_cli -f ~/robot_ws/src/slam/robot_bringup/maps/<이름>
```

### 시뮬레이션 자율주행
**터미널 1**: Gazebo
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 launch robot_gazebo sim.launch.py rviz:=false
```
**터미널 2**: Nav2 + RViz (Gazebo에 로봇이 보인 뒤). RViz에서 **Nav2 Goal**로 목표 지정
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 launch robot_bringup navigation.launch.py use_sim_time:=true rviz:=true
```

### LiDAR를 노트북에 꽂아 확인
**터미널 1**
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 launch robot_bringup lidar.launch.py
```
**터미널 2**
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws && source install/setup.bash
ros2 launch robot_description description.launch.py rviz:=true
```

### 시험
```bash
conda deactivate 2>/dev/null; cd ~/robot_ws
(cd src/motor/robot_base && /usr/bin/python3 -m pytest test)
~/.local/bin/arduino-cli compile --fqbn arduino:avr:leonardo --warnings all src/motor/firmware/motor_bridge
```

---

## 안 될 때
| 증상 | 해결 |
|---|---|
| `Package '...' not found` | 그 터미널에서 `source install/setup.bash`를 안 했다 |
| 빌드 중 `No module named 'catkin_pkg'` | (노트북) `conda deactivate` 후 `rm -rf build install` 하고 다시 빌드 |
| Gazebo에 로봇이 안 나옴, 바로 꺼짐 | `killall -9 gzserver gzclient` 후 다시 실행 |
| 로봇이 Nav2 목표대로 안 움직임 | `key_teleop`이 켜져 있으면 끈다 |
| `rplidar_node`가 `buffer overflow detected`로 반복 종료 | LiDAR USB 연결 확인, `ls /dev/ttyUSB*` |
| 라이브러리 `... cannot open shared object file` | `sudo apt update && sudo apt upgrade` |
