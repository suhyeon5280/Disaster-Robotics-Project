# LattePanda 2D SLAM 로봇: 실행 명령

터미널마다 블록을 그대로 붙여넣는다. 끝낼 때는 각 터미널에서 `Ctrl+C`.

---

## LattePanda (실물 로봇)

### 준비
Ubuntu 22.04 + ROS 2 Humble. ROS가 없으면 공식 문서대로 `ros-humble-desktop`까지 설치한다:
https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html

### 처음 한 번: 받기, 설치, 빌드
```bash
git clone https://github.com/suhyeon5280/Disaster-Robotics-Project.git ~/robot_ws
cd ~/robot_ws && ./setup_lattepanda.sh
```
- 스크립트가 하는 일: apt 업데이트, colcon/rosdep, ROS 의존성, arduino-cli, 시리얼 포트 권한, 빌드
- 끝에 "로그아웃했다가 다시 로그인하세요"가 나오면 그대로 한다
- 중간에 실패하면 원인을 고치고 같은 명령을 다시 실행한다 (이미 된 단계는 건너뜀)
- 비공개 저장소면 clone 때 GitHub 아이디와 토큰(비밀번호 대신)을 입력한다
- 실행 전에 무엇을 할지만 보려면: `./setup_lattepanda.sh --dry-run`

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

---

## 하드웨어 연결

### 방향 기준
- **앞 = RPLIDAR 모터 부분(헤드 옆으로 튀어나온 부분)의 반대쪽**
- 왼쪽/오른쪽은 **로봇 뒤에서 앞을 보고** 정한다. 왼쪽 바퀴의 모터가 "왼쪽 모터"다.
- 구동 바퀴 2개는 차체 가운데, 볼 캐스터 2개는 바퀴 축에서 앞뒤로 60mm

### 전체 배선도
```
 3S 리포 11.1V (XT60)
   (+) ── [퓨즈 10A] ── [메인 스위치] ── MDD10A  POWER +
   (−) ──────────────────────────────── MDD10A  POWER −

 LattePanda Alpha (32u4 핀 헤더)                Cytron MDD10A
   D9  ──────────────────────────────────────── PWM1  ┐ 왼쪽 모터 채널
   D4  ──────────────────────────────────────── DIR1  ┘ (M1A, M1B)
   D10 ──────────────────────────────────────── PWM2  ┐ 오른쪽 모터 채널
   D8  ──────────────────────────────────────── DIR2  ┘ (M2A, M2B)
   GND ──────────────────────────────────────── GND   ← 반드시 연결 (공통 접지)

 MDD10A 모터 출력                               모터
   M1A ── 왼쪽 모터 +        M2A ── 오른쪽 모터 +
   M1B ── 왼쪽 모터 −        M2B ── 오른쪽 모터 −

 LattePanda Alpha (32u4 핀 헤더)                엔코더 (모터 뒤쪽 홀 센서)
   5V  ──────┬── 왼쪽 엔코더 VCC
             └── 오른쪽 엔코더 VCC
   GND ──────┬── 왼쪽 엔코더 GND
             └── 오른쪽 엔코더 GND
   D0  ───────── 왼쪽 엔코더 A
   D1  ───────── 왼쪽 엔코더 B
   D2  ───────── 오른쪽 엔코더 A
   D3  ───────── 오른쪽 엔코더 B

 LattePanda USB-A  ── RPLIDAR A1 (전용 USB 어댑터 보드 경유) → /dev/ttyUSB0
 LattePanda USB-C  ── PD 보조배터리 (모터 배터리와 따로)
```

### 핀 표 (LattePanda Alpha의 32u4 핀 헤더, 보드에 인쇄된 핀 이름 기준)
| 32u4 핀 | 연결 | 용도 |
|---|---|---|
| D9 | MDD10A PWM1 | 왼쪽 모터 속도 (20kHz PWM) |
| D4 | MDD10A DIR1 | 왼쪽 모터 방향 |
| D10 | MDD10A PWM2 | 오른쪽 모터 속도 (20kHz PWM) |
| D8 | MDD10A DIR2 | 오른쪽 모터 방향 |
| GND | MDD10A GND (신호 단자) | 공통 접지. 없으면 모터가 제멋대로 돈다 |
| D0 | 왼쪽 엔코더 A | 외부 인터럽트 |
| D1 | 왼쪽 엔코더 B | 외부 인터럽트 |
| D2 | 오른쪽 엔코더 A | 외부 인터럽트 |
| D3 | 오른쪽 엔코더 B | 외부 인터럽트 |
| 5V | 양쪽 엔코더 VCC | 엔코더 전원 (3.3~5V용. 12V 금지) |
| GND | 양쪽 엔코더 GND | |

- D0/D1은 32u4의 하드웨어 시리얼(Serial1), D2/D3은 I2C(SDA/SCL)와 같은 핀이라 그 기능은 쓸 수 없다. PC와의 통신은 USB라서 영향 없다.
- PWM은 D9/D10만 된다 (펌웨어가 Timer1을 20kHz로 직접 쓴다). 다른 핀으로 옮기지 않는다.

### 모터 선 (JGA25-370 엔코더 모터, 6가닥)
흔히 쓰는 색 배치. **판매처 그림이나 라벨이 다르면 그쪽을 따른다.**

| 흔한 색 | 기능 | 왼쪽 모터 | 오른쪽 모터 |
|---|---|---|---|
| 빨강 | 모터 + | MDD10A M1A | MDD10A M2A |
| 흰색 | 모터 − | MDD10A M1B | MDD10A M2B |
| 파랑 | 엔코더 VCC | LattePanda 5V | LattePanda 5V |
| 검정 | 엔코더 GND | LattePanda GND | LattePanda GND |
| 노랑 | 엔코더 A (C1) | D0 | D2 |
| 초록 | 엔코더 B (C2) | D1 | D3 |

- **모터 선(빨강/흰색)과 엔코더 전원선을 바꿔 꽂으면 엔코더에 모터 전압이 걸려 망가진다.** 꽂기 전에 한 번 더 확인한다.
- 모터 +/−나 엔코더 A/B를 반대로 꽂는 것은 괜찮다. `motor_encoder_test`로 확인한 뒤 `src/motor/firmware/motor_bridge/config.h`의 `*_MOTOR_SIGN`, `*_ENC_SIGN`(+1 또는 −1)으로 맞춘다.
- 왼쪽/오른쪽이 바뀐 것(왼쪽 모터가 M2에 연결 등)은 부호로 못 맞춘다. 선을 다시 꽂는다.

### 전원
- MDD10A는 **역극성 보호가 없다.** 배터리 +/−를 반대로 꽂으면 바로 망가진다. 연결 전에 멀티미터로 극성을 확인한다.
- 배터리 + 선에 10A 내외 퓨즈와 메인 스위치를 단다.
- 3S 리포 밸런스 단자에 전압 알람을 꽂아 과방전을 막는다.
- LattePanda는 USB-C PD 보조배터리로 따로 켠다. 모터 쪽과는 GND 한 가닥(LattePanda GND ↔ MDD10A GND)으로만 이어진다.
- **켜는 순서**: LattePanda 먼저 → 모터 메인 스위치. **끄는 순서**: 모터 메인 스위치 먼저.

### LiDAR (RPLIDAR A1)
- 로봇 중심 바로 위에, 모터 부분이 **뒤쪽**을 향하게 단다.
- 함께 온 USB 어댑터 보드에 연결한 뒤 LattePanda USB-A 포트에 꽂는다 (`/dev/ttyUSB0`). 전원도 USB로 받는다.

### 처음 전원을 넣기 전 확인
- [ ] 배터리 +/− 극성 (멀티미터)
- [ ] 퓨즈, 메인 스위치가 배터리 + 선에 있음
- [ ] LattePanda GND ↔ MDD10A GND 연결
- [ ] 엔코더 VCC가 LattePanda 5V에 연결 (모터 선과 바뀌지 않음)
- [ ] 바퀴가 바닥에서 떠 있음 (첫 시험은 항상 띄워서)
- [ ] (선택) MDD10A 보드의 테스트 버튼으로 마이컴 없이 모터만 먼저 돌려 보기
