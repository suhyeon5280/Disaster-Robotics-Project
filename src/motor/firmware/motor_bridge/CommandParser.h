// CommandParser.h
// 시리얼로 받은 글자를 줄 단위로 모아 V, G 명령으로 해석한다. Arduino 의존 없음.
// 형식: "V <left tps> <right tps>", "G <kff> <kp> <ki>". 바꾸면 robot_base의 bridge_protocol.py도 같이 바꾼다.
// 버퍼를 넘는 줄과 형식이 틀린 줄은 버린다.
#pragma once

#include <stdint.h>

struct Command {
  enum Type : uint8_t { VELOCITY, GAINS };

  Type type;
  int32_t leftTps;   // VELOCITY
  int32_t rightTps;  // VELOCITY
  float kff;         // GAINS
  float kp;          // GAINS
  float ki;          // GAINS
};

class CommandParser {
 public:
  // 한 글자를 넣는다. 줄이 끝났고('\n') 올바른 명령이면 command를 채우고 true를 반환한다.
  bool feed(char c, Command& command);

 private:
  // 가장 긴 줄(G와 게인 3개)보다 넉넉하게 잡는다.
  static const uint8_t BUFFER_SIZE = 48;

  bool parseLine(Command& command) const;

  char buffer_[BUFFER_SIZE];
  uint8_t length_ = 0;
  bool overflowed_ = false;
};
