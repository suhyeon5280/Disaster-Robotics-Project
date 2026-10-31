// Motor.h
// Cytron MDD10A 한 채널 (PWM + DIR). PWM은 Timer1을 20kHz로 직접 설정해 쓴다.
// analogWrite는 Timer1 설정을 덮어쓰므로 PWM 핀에 쓰지 않는다.
#pragma once

#include <Arduino.h>

// setDuty의 최대 크기. 게인(KFF 등)은 이 듀티 ±255 기준으로 정한다.
const float MOTOR_FULL_DUTY = 255.0f;

class Motor {
 public:
  // pwmPin은 Timer1 출력인 9(OC1A) 또는 10(OC1B)만 쓸 수 있다. 다른 핀이면 모터를 돌리지 않는다.
  // sign: DIR=HIGH일 때 바퀴가 전진 방향으로 돌면 +1, 후진이면 -1 (MOTOR_SIGN)
  Motor(uint8_t pwmPin, uint8_t dirPin, int8_t sign);

  // Timer1을 20kHz 위상 정확 PWM으로 설정한다. setup()에서 begin()보다 먼저 한 번 호출한다.
  static void beginPwmTimer();

  // 핀을 출력으로 설정하고 정지시킨다.
  void begin();

  // duty: -MOTOR_FULL_DUTY ~ +MOTOR_FULL_DUTY, +가 로봇 전진 방향. 범위를 넘으면 자른다.
  void setDuty(float duty);

 private:
  uint8_t pwmPin_;
  uint8_t dirPin_;
  int8_t sign_;
  volatile uint16_t* compareRegister_;  // OCR1A 또는 OCR1B. 핀이 잘못되면 nullptr
};
