#include <algorithm>
#include <cmath>
#include <stdint.h>
#include <cassert>
#include <iostream>
#include "../LaunchLabMini/sensor_profile.h"
#include "../LaunchLabMini/history_checkpoint.h"
#include "../LaunchLabMini/rpm_estimator.h"
namespace Original {
#include "../releases/0.6.2-sticks3-qre1113-rotation/source/analog_tachometer.h"
}
template<class T>static void feed(T &d,unsigned us,int v){for(unsigned n=0;n<us/20;++n)d.feed(v);}
template<class T>static void square(T &d,unsigned period,unsigned count,int amp=100) {
  for(unsigned n=0;n<count;++n){feed(d,period/2,140+amp);feed(d,period-period/2,140);}
}
static AnalogTachometer ready(){AnalogTachometer d;StickS3SensorProfile::configure(d);feed(d,1200000,140);return d;}
static Original::AnalogTachometer oldReady(){Original::AnalogTachometer d;d.minMark=80;d.edgeSwingFraction=.7f;feed(d,1200000,140);return d;}
int main() {
  auto config=ready();assert(!config.singleTurnPeak && config.trackSingleTurnPeak);
  assert(RpmEstimator::DEFAULT_MODE==RpmEstimator::Mode::ThreeTurn);
  for(unsigned tail:{1u,2u,3u}) {
    auto d=ready();auto old=oldReady();square(d,10000,12);square(old,10000,12);
    square(d,4000,tail);square(old,4000,tail);feed(d,1700000,240);feed(old,1700000,240);
    assert(d.launches==1 && d.resultValid && old.launches==1);
    assert(d.resultRpm==old.resultRpm && d.burstEndUs==old.burstEndUs);
    assert(std::fabs(d.resultRpm-(tail<3?6000:15000))<3 && std::fabs(d.singlePeakRpm-15000)<3);
    assert(RpmEstimator::select(RpmEstimator::Mode::ThreeTurn,d.sustainedPeakRpm,d.singlePeakRpm)==d.resultRpm);
    assert(RpmEstimator::select(RpmEstimator::Mode::SingleTurn,d.sustainedPeakRpm,d.singlePeakRpm)==d.singlePeakRpm);
    const auto copy=HistoryCheckpoint(d);d.dataLoss();copy.restore(d);
    assert(d.resultValid && d.sustainedPeakRpm==old.resultRpm && std::fabs(d.singlePeakRpm-15000)<3);
  }
  auto separated=ready();square(separated,10000,12);
  for(unsigned i=0;i<3;++i){square(separated,4000,1);square(separated,10000,8);}
  feed(separated,1700000,240);
  assert(separated.launches==1 && std::fabs(separated.sustainedPeakRpm-6000)<3);
  assert(std::fabs(separated.singlePeakRpm-15000)<3); // Never join three separate fast turns.
  auto ramp=ready();auto old=oldReady();square(ramp,10000,12);square(old,10000,12);
  for(unsigned p:{10000u,9600u,9200u,8800u,8400u,8000u,7600u,7200u,6800u,6400u,6000u}) {
    square(ramp,p,1);square(old,p,1);
  }
  feed(ramp,1700000,240);feed(old,1700000,240);
  const float elapsedThree=180000000.f/(6800+6400+6000);
  assert(std::fabs(ramp.resultRpm-elapsedThree)<3 && ramp.resultRpm==old.resultRpm);
  assert(std::fabs(ramp.singlePeakRpm-10000)<3);
  const float arithmeticMean=(60000000.f/6800+60000000.f/6400+60000000.f/6000)/3;
  assert(std::fabs(ramp.resultRpm-arithmeticMean)>20); // Time average, not mean of RPMs.
  for(int amplitude:{30,300}) {
    auto d=ready();auto baseline=oldReady();
    square(d,10000,12);square(baseline,10000,12);
    square(d,4000,1,amplitude);square(baseline,4000,1,amplitude);
    square(d,10000,8);square(baseline,10000,8);
    feed(d,1600000,140);feed(baseline,1600000,140);
    assert(d.launches==1 && d.sustainedPeakRpm==baseline.resultRpm && d.burstEndUs==baseline.burstEndUs);
    assert(std::fabs(d.singlePeakRpm-6000)<3); // Bad single mark rejected; retain frozen three-turn behavior.
  }
  ramp.dataLoss();assert(!ramp.resultValid && ramp.singlePeakRpm==0 && ramp.sustainedPeakRpm==0);
  std::cout<<"PASS: frozen three-adjacent-turn timing oracle, no nonadjacent peak averaging, period-vs-RPM average, simultaneous final peaks, checkpoint retention, shape/noise and data-loss rejection\n";
}
