# Readable orientation recap: 0.10.1

Research and offline UI revision, 2026-10-04. Not installed.

Garmin's attitude display distinguishes a reference horizon, aircraft symbol and
roll marker. The useful principle here is a stable reference for tilt, not copying
its cockpit numerical scales onto a 135×240 screen.
https://www8.garmin.com/manuals/webhelp/GUID-1FA95EDE-BA0A-4000-B109-7E73945389F7/EN-US/GUID-3C15377B-32FE-4604-A1BB-2B59E4205102.html

Xsens MT Manager section 5.7.3.1 uses a 3D sensor box to represent measured
orientation, and provides a playback toolbar separately from orientation data.
Its box illustration gives recognizable faces and axis cues. For this launcher,
a screen inset and USB cap identify the physical object without X/Y/Z labels.
https://www.xsens.com/hubfs/Downloads/Manuals/MT%20Manager%20User%20Manual.pdf

These are interface analogues, not evidence of user-tested readability on this
hardware. This revision applies their principles while keeping the user's cube,
neutral heading at the nearest middle edge and frozen Start/End tilt dots.

Changes:
- Larger fixed-scale body, tighter cube: ±0.84 display units contains the body's
  0.773-unit bounding sphere at every orientation. Same camera, no autoscaling.
- Quiet rear cage, brighter near edges, stationary middle-height reference lines
  and an up arrow. The display stays centered; no height/travel is inferred.
- Blue screen face, violet back, dark sides, screen inset and thick white USB cap.
  The USB cue is deliberately drawn last to remain visible in edge/back poses.
- Automatic recap draws one body. Gray reference endpoint appears only on the
  dedicated Motion page, where its meaning is labeled.
- Playback uses fused pose at optical onset (0 ms) through optical end
  (durationMs), with quaternion interpolation, rather than the full -500 ms to
  end+250 ms capture. Initial physical tilt is preserved. The retained full
  capture still supports comparison and storage; no sensor data are discarded.
- 1.8-second replay, followed by frozen end pose for the rest of the existing
  five-second recap. Progress marker makes the animated/frozen stages visible.
- Start/End dots retain recorded onset/end tilt throughout. Label spacing fixed;
  unavailable/pending capture now has a plain explanation rather than an empty box.

The scene's middle-height line is a gravity/attitude reference. It is not a
measured travel path, height, velocity or absolute compass heading. The IMU
estimator, acquisition, RPM modes, histories, power settings and tournament
views are unchanged. No angles/degrees clutter added to automatic recap.

Validation: actual MotionUI drawing primitives rendered offline for 37 playback
frames, five phase snapshots, 18 extreme-axis poses and unavailable/capturing
states. SVG/PNG/GIF use approximate host font metrics; exact device fonts and
physical acceptance remain pending. Preview is an illustrative synthetic launch,
not a recorded physical pull. Native replay tests cover smooth/clamped sampling,
exact onset/end orientation, initial tilt, yaw invariance, no acceleration-based
travel, fixed cube and body containment. Launch-motion regressions also pass.
A firmware build is retained in build.log. No USB commands or flash performed.

Reproduce host previews from repository root:
  c++ -std=c++17 firmware/tools/render_m5_motion_ui.cpp -o /tmp/render-m5-motion
  /tmp/render-m5-motion firmware/evidence/sticks3-0.10.1-tiltreplay
