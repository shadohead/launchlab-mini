#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../firmware"
CLI="${ARDUINO_CLI:-arduino-cli}"
CACHE="$PWD/.arduino"
mkdir -p "$CACHE/libraries"
cat > "$CACHE/config.yaml" <<YAML
board_manager:
  additional_urls:
    - https://espressif.github.io/arduino-esp32/package_esp32_index.json
directories:
  data: $CACHE/data
  downloads: $CACHE/downloads
  user: $CACHE/user
YAML
"$CLI" core update-index --config-file "$CACHE/config.yaml"
"$CLI" core install esp32:esp32@3.3.0 --config-file "$CACHE/config.yaml"
"$CLI" lib install 'M5Unified@0.2.23' 'M5GFX@0.2.30' --config-file "$CACHE/config.yaml"
mkdir -p build-source/LaunchLabMini
cp LaunchLabMini/*.ino LaunchLabMini/*.h LaunchLabRpm/analog_tachometer.h build-source/LaunchLabMini/
cp -R LaunchLabMini/src build-source/LaunchLabMini/
"$CLI" compile --config-file "$CACHE/config.yaml" \
  --fqbn 'esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashSize=8M,PartitionScheme=default_8MB,PSRAM=opi' \
  --build-property 'compiler.cpp.extra_flags=-DVQF_SINGLE_PRECISION' \
  --build-path "$PWD/build" build-source/LaunchLabMini
