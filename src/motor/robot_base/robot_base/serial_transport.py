"""pyserial로 구현한 Transport."""

import serial

from robot_base.transport import Transport, TransportError

LINE_END = b'\n'
# 줄바꿈 없이 쌓이는 데이터(노이즈 등)가 이 크기를 넘으면 버린다.
MAX_PENDING_BYTES = 1024
# 32u4가 응답하지 않아 쓰기가 막혔을 때 기다리는 최대 시간.
WRITE_TIMEOUT_S = 0.1


class SerialTransport(Transport):
    """시리얼 포트로 줄 단위 텍스트를 주고받는다."""

    def __init__(self, port: str, baud_rate: int) -> None:
        """포트를 연다. 열지 못하면 TransportError."""
        self._port = port
        try:
            self._serial = serial.Serial(
                port, baud_rate, timeout=0, write_timeout=WRITE_TIMEOUT_S
            )
        except (serial.SerialException, OSError) as error:
            raise self._error(error) from error
        self._pending = bytearray()

    def write_line(self, line: str) -> None:
        """줄 끝에 줄바꿈을 붙여 보낸다. 실패하면 TransportError."""
        try:
            self._serial.write(line.encode('ascii') + LINE_END)
        except (serial.SerialException, OSError) as error:
            raise self._error(error) from error

    def read_lines(self) -> list[str]:
        """지금까지 받은 완전한 줄들을 줄바꿈 없이 반환한다. 기다리지 않는다. 실패하면 TransportError."""
        try:
            waiting_bytes = self._serial.in_waiting
            if waiting_bytes:
                self._pending += self._serial.read(waiting_bytes)
        except (serial.SerialException, OSError) as error:
            raise self._error(error) from error

        *complete_lines, rest = self._pending.split(LINE_END)
        self._pending = bytearray(rest)
        if len(self._pending) > MAX_PENDING_BYTES:
            self._pending.clear()
        return [line.decode('ascii', errors='replace').rstrip('\r') for line in complete_lines]

    def close(self) -> None:
        """포트를 닫는다."""
        self._serial.close()

    def _error(self, error: Exception) -> TransportError:
        # pyserial 메시지에 이미 open/read/write 중 무엇이 실패했는지 들어 있다.
        return TransportError(f'serial port {self._port}: {error}')
