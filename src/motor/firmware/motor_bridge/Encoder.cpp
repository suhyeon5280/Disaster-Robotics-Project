// Encoder.cpp
#include "Encoder.h"

namespace {

// 인덱스 = (이전 AB 상태 << 2) | 현재 AB 상태 → tick 증감.
// A, B가 동시에 바뀐 경우(펄스를 놓침)는 방향을 알 수 없어 0으로 둔다.
const int8_t QUAD_STEP_TABLE[16] = {
   0, -1, +1,  0,
  +1,  0,  0, -1,
  -1,  0,  0, +1,
   0, +1, -1,  0,
};

}  // namespace

Encoder::Encoder(uint8_t pinA, uint8_t pinB, int8_t sign)
    : pinA_(pinA), pinB_(pinB), sign_(sign) {}

void Encoder::begin() {
  pinMode(pinA_, INPUT_PULLUP);
  pinMode(pinB_, INPUT_PULLUP);
  // ISR에서 digitalRead보다 빠르게 읽도록 입력 레지스터와 비트를 미리 구해 둔다.
  inputRegisterA_ = portInputRegister(digitalPinToPort(pinA_));
  inputRegisterB_ = portInputRegister(digitalPinToPort(pinB_));
  bitMaskA_ = digitalPinToBitMask(pinA_);
  bitMaskB_ = digitalPinToBitMask(pinB_);
  prevState_ = readState();
}

void Encoder::handleInterrupt() {
  const uint8_t state = readState();
  count_ += QUAD_STEP_TABLE[(prevState_ << 2) | state] * sign_;
  prevState_ = state;
}

long Encoder::readTicks() const {
  // 8비트 MCU에서 32비트 읽기는 여러 명령으로 나뉘므로 인터럽트를 막고 읽는다.
  const uint8_t savedSreg = SREG;
  noInterrupts();
  const uint32_t count = count_;
  SREG = savedSreg;
  return (long)count;
}

uint8_t Encoder::readState() const {
  const uint8_t a = (*inputRegisterA_ & bitMaskA_) ? 1 : 0;
  const uint8_t b = (*inputRegisterB_ & bitMaskB_) ? 1 : 0;
  return (a << 1) | b;
}
