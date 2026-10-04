# Readable tilt recap 0.10.1

**Built offline; not flashed.** Installed firmware remains 0.10.0.

The automatic recap shows a larger blue-screen/violet-back body, a thick white
USB end, a quieter isometric cube, gravity reference and progress marker.
Playback follows optical Start to End over 1.8 seconds, then holds the end pose
for the rest of the existing five-second recap. Frozen Start/End tilt dots stay
visible. The gray reference pose appears only on the dedicated Motion page.
Missing/pending capture has a plain status instead of an empty box.

The body stays centered and fixed scale. Initial measured tilt and the neutral
heading at the nearest middle edge remain. This is orientation only; no height,
travel, velocity or absolute compass heading is inferred. RPM selection, sensor
acquisition, history/settings, shake wake and tournament mode are unchanged.

Build and motion/replay tests pass, including sanitizer checks. Offline previews
render actual firmware drawing primitives, with approximate host font metrics.
The displayed launch is synthetic. Device readability/physical acceptance is
pending. See [design research and evidence](evidence/design-notes.md),
[animated preview](evidence/tilt-replay.gif) and [manifest](manifest.json).

Application-only ESP32-S3 binary at 0x10000; preserve NVS, bootloader and partitions.
