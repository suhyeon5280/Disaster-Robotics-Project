"""줄 단위 텍스트 통신 채널의 인터페이스."""

from abc import ABC, abstractmethod


class TransportError(Exception):
    """채널을 열거나 읽고 쓰다가 실패했을 때 발생한다."""


class Transport(ABC):
    """줄 단위로 텍스트를 주고받는 통신 채널."""

    @abstractmethod
    def write_line(self, line: str) -> None:
        """줄 끝에 줄바꿈을 붙여 보낸다. 실패하면 TransportError."""

    @abstractmethod
    def read_lines(self) -> list[str]:
        """지금까지 받은 완전한 줄들을 줄바꿈 없이 반환한다. 기다리지 않는다. 실패하면 TransportError."""

    @abstractmethod
    def close(self) -> None:
        """채널을 닫는다."""
