"""리눅스 가상 터미널(pty)을 시리얼 포트 대신 써서 하드웨어 없이 검사한다."""

import os
import time
from typing import Iterator

import pytest

from robot_base.serial_transport import SerialTransport
from robot_base.transport import TransportError

BAUD_RATE = 115200
READ_TIMEOUT_S = 1.0


@pytest.fixture
def pty_transport() -> Iterator[tuple[int, SerialTransport]]:
    """(펌웨어 쪽 fd, 노드 쪽 SerialTransport) 쌍."""
    firmware_fd, node_fd = os.openpty()
    transport = SerialTransport(os.ttyname(node_fd), BAUD_RATE)
    yield firmware_fd, transport
    transport.close()
    os.close(node_fd)
    os.close(firmware_fd)


def read_until(transport: SerialTransport, expected_count: int) -> list[str]:
    """줄이 expected_count개 모일 때까지 (최대 READ_TIMEOUT_S) 읽는다."""
    lines: list[str] = []
    deadline = time.monotonic() + READ_TIMEOUT_S
    while len(lines) < expected_count and time.monotonic() < deadline:
        lines += transport.read_lines()
        time.sleep(0.01)
    return lines


def test_write_line_appends_newline(pty_transport: tuple[int, SerialTransport]) -> None:
    firmware_fd, transport = pty_transport
    transport.write_line('V 1200 -1200')
    assert os.read(firmware_fd, 100) == b'V 1200 -1200\n'


def test_read_single_line(pty_transport: tuple[int, SerialTransport]) -> None:
    firmware_fd, transport = pty_transport
    os.write(firmware_fd, b'E 1 2 3\n')
    assert read_until(transport, 1) == ['E 1 2 3']


def test_read_several_lines_at_once(pty_transport: tuple[int, SerialTransport]) -> None:
    firmware_fd, transport = pty_transport
    os.write(firmware_fd, b'E 1 2 3\nE 4 5 6\n')
    assert read_until(transport, 2) == ['E 1 2 3', 'E 4 5 6']


def test_partial_line_waits_for_newline(pty_transport: tuple[int, SerialTransport]) -> None:
    firmware_fd, transport = pty_transport
    os.write(firmware_fd, b'E 1 2')
    time.sleep(0.05)
    assert transport.read_lines() == []

    os.write(firmware_fd, b' 3\n')
    assert read_until(transport, 1) == ['E 1 2 3']


def test_carriage_return_is_removed(pty_transport: tuple[int, SerialTransport]) -> None:
    firmware_fd, transport = pty_transport
    os.write(firmware_fd, b'E 1 2 3\r\n')
    assert read_until(transport, 1) == ['E 1 2 3']


def test_non_ascii_bytes_do_not_raise(pty_transport: tuple[int, SerialTransport]) -> None:
    firmware_fd, transport = pty_transport
    os.write(firmware_fd, b'\xff\xfe\nE 1 2 3\n')
    lines = read_until(transport, 2)
    assert len(lines) == 2
    assert lines[1] == 'E 1 2 3'


def test_open_missing_port_raises_transport_error() -> None:
    with pytest.raises(TransportError):
        SerialTransport('/dev/does_not_exist', BAUD_RATE)
