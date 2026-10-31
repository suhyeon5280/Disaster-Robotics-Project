// Motor.cpp
#include "Motor.h"

namespace {

// 32u4에서 Timer1 출력이 나오는 핀 (Leonardo 핀 번호)
const uint8_t TIMER1_A_PIN = 9;
const uint8_t TIMER1_B_PIN = 10;

// 16MHz / (2 × 프리스케일러 1 × TOP 400) = 20kHz (MDD10A 최대 20kHz). 듀티 해상도 400단계.
const uint16_t PWM_TOP = 400;

volatile uint16_t* compareRegisterFor(uint8_t pwmPin) {
  if (pwmPin == TIMER1_A_PIN) return &OCR1A;
  if (pwmPin == TIMER1_B_PIN) return &OCR1B;
  return nullptr;
}

}  // namespace

Motor::Motor(uint8_t pwmPin, uint8_t dirPin, int8_t sign)
    : pwmPin_(pwmPin), dirPin_(dirPin), sign_(sign),
      compareRegister_(compareRegisterFor(pwmPin)) {}

void Motor::beginPwmTimer() {
  // 모드 10: 위상 정확 PWM, TOP = ICR1. OC1A/OC1B 비반전 출력. 프리스케일러 1.
  TCCR1A = _BV(COM1A1) | _BV(COM1B1) | _BV(WGM11);
  TCCR1B = _BV(WGM13) | _BV(CS10);
  ICR1 = PWM_TOP;
  OCR1A = 0;
  OCR1B = 0;
}

void Motor::begin() {
  pinMode(dirPin_, OUTPUT);
  setDuty(0.0f);
  pinMode(pwmPin_, OUTPUT);
}

void Motor::setDuty(float duty) {
  if (compareRegister_ == nullptr) {
    return;
  }
  const float signedDuty = constrain(duty, -MOTOR_FULL_DUTY, MOTOR_FULL_DUTY) * sign_;
  digitalWrite(dirPin_, signedDuty >= 0.0f ? HIGH : LOW);
  *compareRegister_ = (uint16_t)(fabs(signedDuty) / MOTOR_FULL_DUTY * PWM_TOP + 0.5f);
}
