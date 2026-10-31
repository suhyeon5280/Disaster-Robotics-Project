// motor_bridge.ino
// 32u4 본 펌웨어: robot_base 노드와 시리얼로 통신하며 두 바퀴 속도를 제어한다.
//   노드 → 펌웨어: V <왼쪽 목표 tick/s> <오른쪽 목표 tick/s>, G <kff> <kp> <ki>
//   펌웨어 → 노드: E <millis> <왼쪽 누적 tick> <오른쪽 누적 tick> (20Hz)
// 형식을 바꾸면 robot_base의 bridge_protocol.py도 같이 바꾼다. 이 파일은 객체 조립과 주기 관리만 한다.

#include <stdio.h>

#include "CommandParser.h"
#include "Encoder.h"
#include "Motor.h"
#include "SpeedController.h"
#include "config.h"

// "E 4294967295 -2147483648 -2147483648\n"과 끝의 '\0'이 들어가는 크기
const uint8_t REPORT_LINE_SIZE = 40;
const float US_PER_S = 1000000.0f;

Encoder leftEncoder(LEFT_ENC_A_PIN, LEFT_ENC_B_PIN, LEFT_ENC_SIGN);
Encoder rightEncoder(RIGHT_ENC_A_PIN, RIGHT_ENC_B_PIN, RIGHT_ENC_SIGN);
Motor leftMotor(LEFT_PWM_PIN, LEFT_DIR_PIN, LEFT_MOTOR_SIGN);
Motor rightMotor(RIGHT_PWM_PIN, RIGHT_DIR_PIN, RIGHT_MOTOR_SIGN);
SpeedController leftController(MOTOR_FULL_DUTY);
SpeedController rightController(MOTOR_FULL_DUTY);
CommandParser commandParser;

int32_t leftTargetTps = 0;
int32_t rightTargetTps = 0;
bool commandActive = false;
unsigned long lastCommandMs = 0;

unsigned long lastControlUs = 0;
long lastLeftTicks = 0;
long lastRightTicks = 0;

unsigned long lastReportMs = 0;

void leftEncoderIsr() {
  leftEncoder.handleInterrupt();
}

void rightEncoderIsr() {
  rightEncoder.handleInterrupt();
}

void applyCommand(const Command& command) {
  if (command.type == Command::VELOCITY) {
    leftTargetTps = command.leftTps;
    rightTargetTps = command.rightTps;
    commandActive = true;
    lastCommandMs = millis();
  } else {
    leftController.setGains(command.kff, command.kp, command.ki);
    rightController.setGains(command.kff, command.kp, command.ki);
  }
}

void readSerialCommands() {
  Command command{};
  while (Serial.available() > 0) {
    if (commandParser.feed((char)Serial.read(), command)) {
      applyCommand(command);
    }
  }
}

void stopIfCommandTimedOut(unsigned long nowMs) {
  if (commandActive && nowMs - lastCommandMs > COMMAND_TIMEOUT_MS) {
    leftTargetTps = 0;
    rightTargetTps = 0;
    commandActive = false;
  }
}

// 32비트 카운터의 변화량. unsigned 뺄셈이라 넘침이 있어도 올바르다.
long tickDelta(long current, long previous) {
  return (long)((unsigned long)current - (unsigned long)previous);
}

// 엔코더로 실제 속도를 재고 PID 출력으로 모터 듀티를 정한다.
void runSpeedControl(unsigned long nowUs) {
  const float dtS = (nowUs - lastControlUs) / US_PER_S;
  lastControlUs = nowUs;

  const long leftTicks = leftEncoder.readTicks();
  const long rightTicks = rightEncoder.readTicks();
  const float leftMeasuredTps = tickDelta(leftTicks, lastLeftTicks) / dtS;
  const float rightMeasuredTps = tickDelta(rightTicks, lastRightTicks) / dtS;
  lastLeftTicks = leftTicks;
  lastRightTicks = rightTicks;

  leftMotor.setDuty(leftController.update(leftTargetTps, leftMeasuredTps, dtS));
  rightMotor.setDuty(rightController.update(rightTargetTps, rightMeasuredTps, dtS));
}

void sendEncoderReport(unsigned long nowMs) {
  char line[REPORT_LINE_SIZE];
  const int length = snprintf(line, sizeof(line), "E %lu %ld %ld\n", nowMs,
                              leftEncoder.readTicks(), rightEncoder.readTicks());
  // 송신 버퍼에 자리가 없으면 이번 보고는 건너뛴다. 노드가 읽지 않아도 제어 루프가 멈추지 않게 한다.
  if (length > 0 && Serial.availableForWrite() >= length) {
    Serial.write(line, length);
  }
}

void setup() {
  // 모터를 가장 먼저 정지 상태로 만든다.
  Motor::beginPwmTimer();
  leftMotor.begin();
  rightMotor.begin();

  leftEncoder.begin();
  rightEncoder.begin();
  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_A_PIN), leftEncoderIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_B_PIN), leftEncoderIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_A_PIN), rightEncoderIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_B_PIN), rightEncoderIsr, CHANGE);

  // 시리얼 연결을 기다리지 않는다. 모터는 V를 받아야만 돈다.
  Serial.begin(SERIAL_BAUD);

  lastControlUs = micros();
  lastLeftTicks = leftEncoder.readTicks();
  lastRightTicks = rightEncoder.readTicks();
  lastReportMs = millis();
}

void loop() {
  readSerialCommands();

  const unsigned long nowMs = millis();
  stopIfCommandTimedOut(nowMs);

  const unsigned long nowUs = micros();
  if (nowUs - lastControlUs >= CONTROL_PERIOD_US) {
    runSpeedControl(nowUs);
  }

  if (nowMs - lastReportMs >= REPORT_PERIOD_MS) {
    lastReportMs = nowMs;
    sendEncoderReport(nowMs);
  }
}
