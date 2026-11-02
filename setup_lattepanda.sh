#!/bin/bash
# LattePanda 처음 설정: 의존성 설치, arduino-cli, 시리얼 포트 권한, 빌드.
# 여러 번 실행해도 된다 (이미 된 단계는 건너뛴다).
#
# 사용:     cd ~/robot_ws && ./setup_lattepanda.sh
# 미리보기: ./setup_lattepanda.sh --dry-run   (실행할 명령만 출력하고 아무것도 바꾸지 않는다)
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS_SETUP=/opt/ros/humble/setup.bash
ROS_INSTALL_DOC=https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
ARDUINO_CLI_VERSION=1.5.1
ARDUINO_CLI="$HOME/.local/bin/arduino-cli"
ARDUINO_CLI_URL="https://github.com/arduino/arduino-cli/releases/download/v${ARDUINO_CLI_VERSION}/arduino-cli_${ARDUINO_CLI_VERSION}_Linux_64bit.tar.gz"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi
NEED_RELOGIN=false
CURRENT_STEP="시작"

step() {
  CURRENT_STEP="$*"
  echo
  echo "=== $* ==="
}

# 명령을 보여주고 실행한다. --dry-run이면 보여주기만 한다.
run() {
  echo "+ $*"
  if ! $DRY_RUN; then
    "$@"
  fi
}

fail() {
  echo "!!! $*" >&2
  exit 1
}

trap 'echo "!!! 실패한 단계: ${CURRENT_STEP} (위의 오류 메시지를 확인하세요)" >&2' ERR

step "1/7 환경 확인"
[[ $EUID -ne 0 ]] || fail "sudo 없이 실행하세요: ./setup_lattepanda.sh (필요한 곳에서만 sudo를 씁니다)"
[[ -z "${CONDA_PREFIX:-}" ]] || fail "conda가 켜져 있습니다. 'conda deactivate' 후 다시 실행하세요."
. /etc/os-release
[[ "${VERSION_ID}" == "22.04" ]] || fail "Ubuntu 22.04가 필요합니다 (지금: ${PRETTY_NAME})."
[[ "$(uname -m)" == "x86_64" ]] || fail "x86_64 컴퓨터용 스크립트입니다 (지금: $(uname -m))."
[[ -f "$ROS_SETUP" ]] || fail "ROS 2 Humble이 없습니다. 공식 문서대로 ros-humble-desktop을 설치한 뒤 다시 실행하세요: $ROS_INSTALL_DOC"
echo "Ubuntu ${VERSION_ID}, $(uname -m), ROS 2 Humble 확인. 워크스페이스: $WS_DIR"
$DRY_RUN && echo "(미리보기: 명령을 출력만 하고 실행하지 않습니다)"

step "2/7 apt 패키지를 최신으로 (ROS 패키지 버전을 서로 맞춘다)"
run sudo apt-get update
run sudo apt-get -y upgrade

step "3/7 빌드 도구 (colcon, rosdep)"
run sudo apt-get install -y ros-dev-tools

step "4/7 ROS 의존성 (각 package.xml에 적힌 것, 시뮬레이션 제외)"
if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  run sudo rosdep init
else
  echo "rosdep init: 이미 했음"
fi
run rosdep update
# ROS setup 스크립트는 정의되지 않은 변수를 참조하므로 잠시 -u를 끈다.
set +u
# shellcheck disable=SC1090
source "$ROS_SETUP"
set -u
cd "$WS_DIR"
run rosdep install --from-paths src/motor src/slam --ignore-src -y

step "5/7 arduino-cli ${ARDUINO_CLI_VERSION} + Leonardo 보드 지원"
if [[ -x "$ARDUINO_CLI" ]]; then
  echo "arduino-cli: 이미 있음 ($("$ARDUINO_CLI" version | head -1))"
else
  tmp_dir="$(mktemp -d)"
  run curl -fsSL -o "$tmp_dir/arduino-cli.tar.gz" "$ARDUINO_CLI_URL"
  run tar -xzf "$tmp_dir/arduino-cli.tar.gz" -C "$tmp_dir" arduino-cli
  run install -D -m 755 "$tmp_dir/arduino-cli" "$ARDUINO_CLI"
  rm -rf "$tmp_dir"
fi
run "$ARDUINO_CLI" core update-index
run "$ARDUINO_CLI" core install arduino:avr

step "6/7 시리얼 포트 권한 (dialout 그룹: 32u4 /dev/ttyACM0, LiDAR /dev/ttyUSB0)"
if id -nG "$USER" | tr ' ' '\n' | grep -x dialout > /dev/null; then
  echo "dialout: 이미 있음"
else
  run sudo usermod -aG dialout "$USER"
  NEED_RELOGIN=true
fi

step "7/7 빌드 (시뮬레이션 robot_gazebo 제외)"
cd "$WS_DIR"
run colcon build --packages-skip robot_gazebo

CURRENT_STEP="완료"
echo
echo "=== 끝 ==="
if $NEED_RELOGIN; then
  echo "* 시리얼 포트 권한을 새로 받았습니다. 로그아웃했다가 다시 로그인하세요."
fi
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  echo "* arduino-cli는 다시 로그인하면 'arduino-cli'로 쓸 수 있습니다 (그 전에는 $ARDUINO_CLI)."
fi
cat <<'EOF'
다음 할 일 (README.md의 "펌웨어 업로드"):
  1) 바퀴를 바닥에서 띄우고 motor_encoder_test로 배선, 부호, ticks_per_rev 확인
  2) 결과를 src/motor/firmware/motor_bridge/config.h, src/motor/robot_base/config/robot_base.yaml에 적기
  3) motor_bridge 업로드 → cd ~/robot_ws && source install/setup.bash
     → ros2 launch robot_bringup robot.launch.py mode:=base
EOF
