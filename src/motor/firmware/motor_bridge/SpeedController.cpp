// SpeedController.cpp
#include "SpeedController.h"

SpeedController::SpeedController(float outputLimit) : outputLimit_(outputLimit) {}

void SpeedController::setGains(float kff, float kp, float ki) {
  kff_ = kff;
  kp_ = kp;
  ki_ = ki;
}

float SpeedController::update(float targetTps, float measuredTps, float dtS) {
  if (targetTps == 0.0f) {
    // 정지 명령에서 남은 적분값 때문에 모터가 떨리지 않게 한다.
    reset();
    return 0.0f;
  }

  const float errorTps = targetTps - measuredTps;
  float nextIntegralTicks = integralTicks_ + errorTps * dtS;
  float output = kff_ * targetTps + kp_ * errorTps + ki_ * nextIntegralTicks;

  // 출력이 상한에 걸린 상태에서 같은 방향으로 적분이 계속 쌓이지 않게 한다 (anti-windup).
  if (output > outputLimit_) {
    output = outputLimit_;
    if (errorTps > 0.0f) {
      nextIntegralTicks = integralTicks_;
    }
  } else if (output < -outputLimit_) {
    output = -outputLimit_;
    if (errorTps < 0.0f) {
      nextIntegralTicks = integralTicks_;
    }
  }
  integralTicks_ = nextIntegralTicks;
  return output;
}

void SpeedController::reset() {
  integralTicks_ = 0.0f;
}
