#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-m5-source/LaunchLabMini
cp LaunchLabMini/LaunchLabMini.ino build-m5-source/LaunchLabMini/
cp LaunchLabMini/*.h build-m5-source/LaunchLabMini/
cp LaunchLabRpm/analog_tachometer.h build-m5-source/LaunchLabMini/
exec tools/arduino-cli compile --config-file arduino-cli.yaml \
  --fqbn 'esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashSize=8M,PartitionScheme=default_8MB,PSRAM=opi' \
  --libraries "$PWD/.arduino/m5-libraries" --build-path "$PWD/build-m5" \
  build-m5-source/LaunchLabMini "$@"
