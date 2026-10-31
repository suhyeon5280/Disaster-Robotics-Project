import pytest

from robot_base.bridge_protocol import BridgeProtocol, EncoderReading
from robot_base.robot_config import SpeedGains


@pytest.fixture
def protocol() -> BridgeProtocol:
    return BridgeProtocol()


@pytest.mark.parametrize(
    ('left_tps', 'right_tps', 'expected'),
    [
        (1200, -1200, 'V 1200 -1200'),
        (1199.6, -1199.6, 'V 1200 -1200'),
        (0.4, -0.4, 'V 0 0'),
        (0, 0, 'V 0 0'),
    ],
)
def test_format_velocity_command(
    protocol: BridgeProtocol, left_tps: float, right_tps: float, expected: str
) -> None:
    assert protocol.format_velocity_command(left_tps, right_tps) == expected


@pytest.mark.parametrize(
    ('gains', 'expected'),
    [
        (SpeedGains(0.06, 0.05, 0.3), 'G 0.060000 0.050000 0.300000'),
        (SpeedGains(0.0, 12.5, 0.0), 'G 0.000000 12.500000 0.000000'),
        (SpeedGains(0.00005, 0.0, 0.0), 'G 0.000050 0.000000 0.000000'),  # 지수 표기 없음
    ],
)
def test_format_gains_command(
    protocol: BridgeProtocol, gains: SpeedGains, expected: str
) -> None:
    assert protocol.format_gains_command(gains) == expected


def test_parse_valid_encoder_line(protocol: BridgeProtocol) -> None:
    assert protocol.parse_encoder_line('E 123456 5021 -4987') == EncoderReading(
        time_ms=123456, left_ticks=5021, right_ticks=-4987
    )


@pytest.mark.parametrize('line', ['E 1 2 3\n', 'E 1 2 3\r\n', 'E 1 2 3\r'])
def test_parse_ignores_line_ending(protocol: BridgeProtocol, line: str) -> None:
    assert protocol.parse_encoder_line(line) == EncoderReading(1, 2, 3)


def test_parse_accepts_32bit_limits(protocol: BridgeProtocol) -> None:
    assert protocol.parse_encoder_line('E 4294967295 2147483647 -2147483648') == (
        EncoderReading(4294967295, 2147483647, -2147483648)
    )


@pytest.mark.parametrize(
    'line',
    [
        '',
        'E',
        'E 1 2',
        'E 1 2 3 4',
        'V 1 2 3',
        'e 1 2 3',
        'E 1.5 2 3',
        'E 1 2 x',
        'E -1 2 3',             # millis는 음수가 될 수 없다
        'E 4294967296 0 0',     # millis가 32비트를 넘음
        'E 0 2147483648 0',     # tick이 int32를 넘음
        'E 0 0 -2147483649',
        'E 1 2 ٣',              # 유니코드 숫자
        'garbage',
    ],
)
def test_parse_rejects_invalid_line(protocol: BridgeProtocol, line: str) -> None:
    assert protocol.parse_encoder_line(line) is None
