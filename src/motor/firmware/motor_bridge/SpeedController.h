// SpeedController.h
// 바퀴 하나의 속도 제어: 피드포워드 + PI. Arduino 의존 없음.
#pragma once

class SpeedController {
 public:
  // outputLimit: 출력(듀티) 크기의 상한
  explicit SpeedController(float outputLimit);

  // 게인을 바꾼다. 적분값은 유지한다. 처음에는 모두 0이라 G를 받기 전에는 출력이 0이다.
  void setGains(float kff, float kp, float ki);

  // 목표/측정 속도(tick/s)와 경과 시간(s)으로 듀티를 계산한다.
  // 목표가 0이면 적분을 비우고 0을 반환한다. 출력이 상한에 걸리면 그 방향으로는 적분하지 않는다.
  float update(float targetTps, float measuredTps, float dtS);

  // 적분값을 0으로 되돌린다.
  void reset();

 private:
  float outputLimit_;
  float kff_ = 0.0f;
  float kp_ = 0.0f;
  float ki_ = 0.0f;
  float integralTicks_ = 0.0f;  // 속도 오차(tick/s)를 시간으로 적분한 값
};
