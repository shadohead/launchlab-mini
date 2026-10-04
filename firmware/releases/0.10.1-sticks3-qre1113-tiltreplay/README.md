# Readable tilt recap 0.10.1

**Full first install and exact readback verified on a fresh M5StickS3.** Runtime verification awaits a physical power cycle. The native USB installation used the same four files served by the web updater; browser USB transfer remains pending because the chooser cancelled before any writes.

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

For an existing compatible LaunchLab installation, update the application at 0x10000. For a fresh factory M5StickS3, choose First install in the web updater: bootloader at 0x0, partitions at 0x8000, boot_app0 at 0xe000 and application at 0x10000. Back up factory firmware first if it must be restorable.
