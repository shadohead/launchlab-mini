#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
TEST_BUILD=$(mktemp -d)
trap 'rm -rf "$TEST_BUILD"' EXIT
for suite in sticks3 sticks3_level sticks3_power launch_feedback launch_motion motion_replay motion_store practice_history practice_store orientation_estimator analog_tachometer; do
  "${CXX:-c++}" -std=c++17 -O1 -g -DVQF_SINGLE_PRECISION -fsanitize=address,undefined -fno-omit-frame-pointer -Ifirmware/tests/fakes -Ifirmware/LaunchLabRpm "firmware/tests/test_${suite}.cpp" firmware/LaunchLabMini/src/vqf/vqf.cpp -o "$TEST_BUILD/$suite"
  "$TEST_BUILD/$suite"
done
