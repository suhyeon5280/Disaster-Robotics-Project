"""32u4 펌웨어와 주고받는 시리얼 메시지의 생성과 파싱.

노드 → 펌웨어: "V <왼쪽 tick/s> <오른쪽 tick/s>", "G <kff> <kp> <ki>"
펌웨어 → 노드: "E <millis> <왼쪽 누적 tick> <오른쪽 누적 tick>"
형식을 바꾸면 펌웨어(motor_bridge/CommandParser)도 같이 바꾼다. 줄바꿈 처리는 Transport가 맡는다.
"""

import re
from dataclasses import dataclass

from robot_base.robot_config import SpeedGains

UINT32_MAX = 2**32 - 1
INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1

# re.ASCII: 유니코드 숫자(예: '٣')를 정수로 받아들이지 않게 한다.
ENCODER_LINE_PATTERN = re.compile(r'E (\d+) (-?\d+) (-?\d+)', re.ASCII)


@dataclass(frozen=True)
class EncoderReading:
    """E 메시지 한 줄의 내용."""

    time_ms: int
    left_ticks: int
    right_ticks: int


class BridgeProtocol:
    """V, G 메시지 생성과 E 메시지 파싱."""

    def format_velocity_command(self, left_tps: float, right_tps: float) -> str:
        """바퀴 목표 속도(tick/s)로 V 메시지를 만든다. 값은 정수로 반올림한다."""
        return f'V {round(left_tps)} {round(right_tps)}'

    def format_gains_command(self, gains: SpeedGains) -> str:
        """속도 제어 게인으로 G 메시지를 만든다. 지수 표기 없이 소수점 아래 6자리로 보낸다."""
        return f'G {gains.kff:.6f} {gains.kp:.6f} {gains.ki:.6f}'

    def parse_encoder_line(self, line: str) -> EncoderReading | None:
        """E 메시지 한 줄을 파싱한다. 형식이나 범위가 맞지 않으면 None을 반환한다."""
        match = ENCODER_LINE_PATTERN.fullmatch(line.strip())
        if match is None:
            return None
        time_ms, left_ticks, right_ticks = (int(group) for group in match.groups())
        if time_ms > UINT32_MAX:
            return None
        if not (INT32_MIN <= left_ticks <= INT32_MAX and INT32_MIN <= right_ticks <= INT32_MAX):
            return None
        return EncoderReading(time_ms, left_ticks, right_ticks)
