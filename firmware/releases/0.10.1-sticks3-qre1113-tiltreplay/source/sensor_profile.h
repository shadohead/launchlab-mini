#pragma once
#include "analog_tachometer.h"

// M5StickS3 + QRE1113; optical thresholds retain the initial mounted profile. The confirmed
// 2026-09-30 pull has 89-130 count marks with subsidiary peaks. This remains a
// physical-validation candidate: replay cannot establish absolute shaft RPM.
namespace StickS3SensorProfile {
static constexpr float MIN_MARK=80.0f, EDGE_SWING_FRACTION=0.70f;
static inline void configure(AnalogTachometer &detector) {
  detector.minMark=MIN_MARK;
  detector.edgeSwingFraction=EDGE_SWING_FRACTION;
  detector.singleTurnPeak=false;
  detector.trackSingleTurnPeak=true;
}
}
