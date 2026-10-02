#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .arduino/m5-libraries
if [ ! -d .arduino/m5-libraries/M5Unified ]; then
  git clone --depth 1 --branch 0.2.23 https://github.com/m5stack/M5Unified.git .arduino/m5-libraries/M5Unified
fi
if [ ! -d .arduino/m5-libraries/M5GFX ]; then
  git clone --depth 1 --branch 0.2.30 https://github.com/m5stack/M5GFX.git .arduino/m5-libraries/M5GFX
fi
