// motor_encoder_test.ino
// 배선 확인, MOTOR_SIGN / ENC_SIGN 판정, ticks_per_rev 측정을 위한 진단 스케치.
// 한 번 쓰고 버리는 도구라 클래스로 나누지 않는다. 사용 절차: docs/motor_encoder_test.md
//
// 시리얼 명령 (115200 baud, 한 글자):
//   l : 왼쪽 모터를 DIR=HIGH, TEST_PWM으로 RUN_TIME_MS 동안 회전
//   r : 오른쪽 모터를 같은 방식으로 회전
//   z : tick 카운트와 에러 카운트를 0으로 리셋
//   s : 즉시 정지
//   h : 도움말 출력
// 그 외 글자는 안전을 위해 모터를 정지시킨다.

// ---- 핀 배치 (motor_bridge/config.h와 같게) ----
const uint8_t LEFT_PWM_PIN = 9;
const uint8_t LEFT_DIR_PIN = 4;
const uint8_t LEFT_ENC_A_PIN = 0;
const uint8_t LEFT_ENC_B_PIN = 1;
const uint8_t RIGHT_PWM_PIN = 10;
const uint8_t RIGHT_DIR_PIN = 8;
const uint8_t RIGHT_ENC_A_PIN = 2;
const uint8_t RIGHT_ENC_B_PIN = 3;

// ---- 테스트 설정 ----
const unsigned long SERIAL_BAUD = 115200;
const uint8_t TEST_PWM = 60;                // 0~255. 바퀴가 안 돌고 웅웅거리기만 하면 올린다.
const unsigned long RUN_TIME_MS = 2000;
const unsigned long PRINT_PERIOD_MS = 200;  // 5Hz

// 인덱스 = (이전 AB 상태 << 2) | 현재 AB 상태 → tick 증감.
// A, B 두 비트가 동시에 바뀐 경우(펄스를 놓침)는 여기서 0이고, 에러로 따로 센다.
const int8_t QUAD_STEP_TABLE[16] = {
   0, -1, +1,  0,
  +1,  0,  0, -1,
  -1,  0,  0, +1,
   0, +1, -1,  0,
};
const uint8_t BOTH_BITS_CHANGED = 0b11;

volatile long left_ticks = 0;
volatile long right_ticks = 0;
volatile long left_errors = 0;
volatile long right_errors = 0;
volatile uint8_t left_prev_state = 0;
volatile uint8_t right_prev_state = 0;

enum RunningMotor : uint8_t { MOTOR_NONE, MOTOR_LEFT, MOTOR_RIGHT };
RunningMotor running_motor = MOTOR_NONE;
unsigned long run_start_ms = 0;
unsigned long last_print_ms = 0;

uint8_t read_ab_state(uint8_t pin_a, uint8_t pin_b) {
  return (digitalRead(pin_a) << 1) | digitalRead(pin_b);
}

void update_encoder(uint8_t pin_a, uint8_t pin_b, volatile uint8_t &prev_state,
                    volatile long &ticks, volatile long &errors) {
  uint8_t state = read_ab_state(pin_a, pin_b);
  if ((state ^ prev_state) == BOTH_BITS_CHANGED) {
    errors++;
  } else {
    ticks += QUAD_STEP_TABLE[(prev_state << 2) | state];
  }
  prev_state = state;
}

void left_encoder_isr() {
  update_encoder(LEFT_ENC_A_PIN, LEFT_ENC_B_PIN, left_prev_state, left_ticks, left_errors);
}

void right_encoder_isr() {
  update_encoder(RIGHT_ENC_A_PIN, RIGHT_ENC_B_PIN, right_prev_state, right_ticks, right_errors);
}

// 8비트 MCU에서 long(32비트) 읽기는 여러 명령으로 나뉘므로 인터럽트를 막고 읽는다.
long read_atomic(const volatile long &value) {
  noInterrupts();
  long copy = value;
  interrupts();
  return copy;
}

void reset_counts() {
  noInterrupts();
  left_ticks = 0;
  right_ticks = 0;
  left_errors = 0;
  right_errors = 0;
  interrupts();
  Serial.println(F("RESET"));
}

void stop_motors() {
  analogWrite(LEFT_PWM_PIN, 0);
  analogWrite(RIGHT_PWM_PIN, 0);
  if (running_motor != MOTOR_NONE) {
    Serial.println(F("STOP"));
  }
  running_motor = MOTOR_NONE;
}

void start_motor(RunningMotor motor) {
  stop_motors();
  bool is_left = (motor == MOTOR_LEFT);
  digitalWrite(is_left ? LEFT_DIR_PIN : RIGHT_DIR_PIN, HIGH);
  analogWrite(is_left ? LEFT_PWM_PIN : RIGHT_PWM_PIN, TEST_PWM);
  running_motor = motor;
  run_start_ms = millis();
  Serial.print(is_left ? F("RUN LEFT") : F("RUN RIGHT"));
  Serial.print(F(" DIR=HIGH PWM="));
  Serial.println(TEST_PWM);
}

void print_help() {
  Serial.println(F("motor_encoder_test"));
  Serial.println(F("  l: left motor  DIR=HIGH for RUN_TIME_MS"));
  Serial.println(F("  r: right motor DIR=HIGH for RUN_TIME_MS"));
  Serial.println(F("  z: reset counts"));
  Serial.println(F("  s: stop"));
  Serial.println(F("  h: help"));
}

void print_counts() {
  Serial.print(F("L="));
  Serial.print(read_atomic(left_ticks));
  Serial.print(F(" R="));
  Serial.print(read_atomic(right_ticks));
  Serial.print(F(" errL="));
  Serial.print(read_atomic(left_errors));
  Serial.print(F(" errR="));
  Serial.println(read_atomic(right_errors));
}

void handle_serial_commands() {
  while (Serial.available() > 0) {
    char command = Serial.read();
    switch (command) {
      case 'l': start_motor(MOTOR_LEFT); break;
      case 'r': start_motor(MOTOR_RIGHT); break;
      case 'z': reset_counts(); break;
      case 's': stop_motors(); break;
      case 'h': print_help(); break;
      case '\r':
      case '\n':
      case ' ':
        break;
      default:
        stop_motors();
        Serial.println(F("unknown command (h: help)"));
        break;
    }
  }
}

void setup() {
  // 모터 핀을 가장 먼저 안전한 상태(정지)로 만든다.
  pinMode(LEFT_PWM_PIN, OUTPUT);
  pinMode(RIGHT_PWM_PIN, OUTPUT);
  pinMode(LEFT_DIR_PIN, OUTPUT);
  pinMode(RIGHT_DIR_PIN, OUTPUT);
  analogWrite(LEFT_PWM_PIN, 0);
  analogWrite(RIGHT_PWM_PIN, 0);
  digitalWrite(LEFT_DIR_PIN, LOW);
  digitalWrite(RIGHT_DIR_PIN, LOW);

  pinMode(LEFT_ENC_A_PIN, INPUT_PULLUP);
  pinMode(LEFT_ENC_B_PIN, INPUT_PULLUP);
  pinMode(RIGHT_ENC_A_PIN, INPUT_PULLUP);
  pinMode(RIGHT_ENC_B_PIN, INPUT_PULLUP);
  left_prev_state = read_ab_state(LEFT_ENC_A_PIN, LEFT_ENC_B_PIN);
  right_prev_state = read_ab_state(RIGHT_ENC_A_PIN, RIGHT_ENC_B_PIN);
  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_A_PIN), left_encoder_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_B_PIN), left_encoder_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_A_PIN), right_encoder_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_B_PIN), right_encoder_isr, CHANGE);

  Serial.begin(SERIAL_BAUD);
  while (!Serial) {
    // 시리얼 모니터가 열릴 때까지 대기 (Leonardo USB 시리얼)
  }
  print_help();
}

void loop() {
  handle_serial_commands();

  unsigned long now_ms = millis();
  if (running_motor != MOTOR_NONE && now_ms - run_start_ms >= RUN_TIME_MS) {
    stop_motors();
  }
  if (now_ms - last_print_ms >= PRINT_PERIOD_MS) {
    last_print_ms = now_ms;
    print_counts();
  }
}
