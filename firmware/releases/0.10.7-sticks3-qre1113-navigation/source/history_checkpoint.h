#pragma once
#include "analog_tachometer.h"

// A flash write must not defer DMA interrupts through a measured burst.
// Preserve the completed result, then require fresh quiet after the gap.
struct HistoryCheckpoint {
  bool valid=false;
  float rpm=0,peak=0,amplitude=0,noise=0,three=0,single=0,threeAmplitude=0,singleAmplitude=0;
  uint32_t revision=0;
  AnalogTachometer::End end=AnalogTachometer::End::None;
  AnalogTachometer::Phase phase=AnalogTachometer::Phase::Paused;
  static bool allowed(const AnalogTachometer &d) {
    return d.phase==AnalogTachometer::Phase::Hold || d.phase==AnalogTachometer::Phase::Paused;
  }
  explicit HistoryCheckpoint(const AnalogTachometer &d):valid(d.resultValid),rpm(d.resultRpm),
    peak(d.peakRpm),amplitude(d.peakAmplitude),noise(d.startNoiseBand),revision(d.resultRevision),end(d.ended),phase(d.phase) {
    three=d.sustainedPeakRpm;single=d.singlePeakRpm;
    threeAmplitude=d.sustainedPeakAmplitude;singleAmplitude=d.singlePeakAmplitude;
  }
  HistoryCheckpoint()=default;
  void restore(AnalogTachometer &d)const {
    d.dataLoss();
    d.resultValid=valid;d.resultRpm=rpm;d.peakRpm=peak;d.peakAmplitude=amplitude;
    d.sustainedPeakRpm=three;d.singlePeakRpm=single;
    d.sustainedPeakAmplitude=threeAmplitude;d.singlePeakAmplitude=singleAmplitude;
    d.startNoiseBand=noise;d.resultRevision=revision;d.ended=end;
    d.phase=d.enabled && phase==AnalogTachometer::Phase::Hold?phase:
      (d.enabled?AnalogTachometer::Phase::Settling:AnalogTachometer::Phase::Paused);
  }
};
