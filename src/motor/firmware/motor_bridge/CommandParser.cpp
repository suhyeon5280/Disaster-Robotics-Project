// CommandParser.cpp
#include "CommandParser.h"

#include <errno.h>
#include <math.h>
#include <stdlib.h>

namespace {

// int32 범위의 정수 하나를 읽는다. 숫자가 없거나 범위를 넘으면 false.
bool parseInt32(const char*& cursor, int32_t& value) {
  char* end;
  errno = 0;
  const long parsed = strtol(cursor, &end, 10);
  if (end == cursor || errno == ERANGE || parsed < INT32_MIN || parsed > INT32_MAX) {
    return false;
  }
  value = (int32_t)parsed;
  cursor = end;
  return true;
}

// 0 이상의 유한한 실수(게인) 하나를 읽는다.
bool parseGain(const char*& cursor, float& value) {
  char* end;
  const double parsed = strtod(cursor, &end);
  if (end == cursor || !isfinite(parsed) || parsed < 0.0) {
    return false;
  }
  value = (float)parsed;
  cursor = end;
  return true;
}

// 다음 글자가 공백이면 넘기고 true.
bool skipSeparator(const char*& cursor) {
  if (*cursor != ' ') {
    return false;
  }
  ++cursor;
  return true;
}

}  // namespace

bool CommandParser::feed(char c, Command& command) {
  if (c == '\r') {
    return false;
  }
  if (c != '\n') {
    if (length_ < BUFFER_SIZE - 1) {
      buffer_[length_++] = c;
    } else {
      overflowed_ = true;
    }
    return false;
  }

  buffer_[length_] = '\0';
  const bool valid = !overflowed_ && parseLine(command);
  length_ = 0;
  overflowed_ = false;
  return valid;
}

bool CommandParser::parseLine(Command& command) const {
  const char type = buffer_[0];
  if (type == '\0' || buffer_[1] != ' ') {
    return false;
  }
  const char* cursor = buffer_ + 2;

  if (type == 'V') {
    int32_t left;
    int32_t right;
    if (!parseInt32(cursor, left) || !skipSeparator(cursor) || !parseInt32(cursor, right) ||
        *cursor != '\0') {
      return false;
    }
    command.type = Command::VELOCITY;
    command.leftTps = left;
    command.rightTps = right;
    return true;
  }

  if (type == 'G') {
    float kff;
    float kp;
    float ki;
    if (!parseGain(cursor, kff) || !skipSeparator(cursor) || !parseGain(cursor, kp) ||
        !skipSeparator(cursor) || !parseGain(cursor, ki) || *cursor != '\0') {
      return false;
    }
    command.type = Command::GAINS;
    command.kff = kff;
    command.kp = kp;
    command.ki = ki;
    return true;
  }

  return false;
}
