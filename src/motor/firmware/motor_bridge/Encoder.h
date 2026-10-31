// Encoder.h
// 홀 엔코더 A/B 4체배 디코딩. A, B 두 핀을 모두 외부 인터럽트(CHANGE)에 연결해 handleInterrupt를 부른다.
#pragma once

#include <Arduino.h>

class Encoder {
 public:
  // sign: 바퀴를 전진 방향으로 돌릴 때 카운트가 늘면 +1, 줄면 -1 (ENC_SIGN)
  Encoder(uint8_t pinA, uint8_t pinB, int8_t sign);

  // 핀을 풀업 입력으로 설정하고 현재 A/B 상태를 읽는다. attachInterrupt 전에 호출한다.
  void begin();

  // ISR에서 호출한다. A 또는 B가 바뀔 때마다 ±1 tick.
  void handleInterrupt();

  // 부호 보정된 누적 tick. 32비트로 넘치면 순환한다.
  long readTicks() const;

 private:
  uint8_t readState() const;

  uint8_t pinA_;
  uint8_t pinB_;
  int8_t sign_;
  volatile uint8_t* inputRegisterA_ = nullptr;
  volatile uint8_t* inputRegisterB_ = nullptr;
  uint8_t bitMaskA_ = 0;
  uint8_t bitMaskB_ = 0;
  // 부호 없는 정수로 쌓아야 넘칠 때 동작이 정의된다 (순환).
  volatile uint32_t count_ = 0;
  volatile uint8_t prevState_ = 0;
};
