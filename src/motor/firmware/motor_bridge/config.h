// config.h
// motor_bridge 펌웨어 설정값: 핀 배치, 부호, 시리얼 주기와 타임아웃, 제어 주기.
// 속도 제어 게인은 여기 두지 않는다: 노드가 robot_base.yaml 값을 G 메시지로 보낸다.
#pragma once

#include <stdint.h>

// ---- 핀 배치 ----
const uint8_t LEFT_PWM_PIN = 9;    // Timer1 OC1A
const uint8_t LEFT_DIR_PIN = 4;
const uint8_t LEFT_ENC_A_PIN = 0;
const uint8_t LEFT_ENC_B_PIN = 1;
const uint8_t RIGHT_PWM_PIN = 10;  // Timer1 OC1B
const uint8_t RIGHT_DIR_PIN = 8;
const uint8_t RIGHT_ENC_A_PIN = 2;
const uint8_t RIGHT_ENC_B_PIN = 3;

// ---- 부호: motor_encoder_test 결과로 수정한다 (TBD) ----
// MOTOR_SIGN: DIR=HIGH일 때 바퀴가 로봇 전진 방향으로 돌면 +1, 후진 방향이면 -1
// ENC_SIGN: 바퀴를 전진 방향으로 돌릴 때 카운트가 늘면 +1, 줄면 -1
const int8_t LEFT_MOTOR_SIGN = 1;
const int8_t RIGHT_MOTOR_SIGN = 1;
const int8_t LEFT_ENC_SIGN = 1;
const int8_t RIGHT_ENC_SIGN = 1;

// ---- 시리얼 프로토콜 ----
const unsigned long SERIAL_BAUD = 115200;
const unsigned long COMMAND_TIMEOUT_MS = 500;  // 이 시간 동안 올바른 V가 없으면 정지
const unsigned long REPORT_PERIOD_MS = 50;     // E 전송 주기 (20Hz)

// ---- 속도 제어 ----
const unsigned long CONTROL_PERIOD_US = 20000;  // 50Hz
