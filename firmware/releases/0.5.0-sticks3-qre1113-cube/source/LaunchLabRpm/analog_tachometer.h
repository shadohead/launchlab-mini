#pragma once
#include <algorithm>
#include <cmath>
#include <stdint.h>

// AO only. Time is measured in ADC sample positions, not loop/USB timing.
// Analog pulse extraction and first-burst selection are deliberately separate.
class AnalogTachometer {
public:
  enum class Phase { Paused, Settling, Ready, Launch, Hold };
  enum class End { None, Slowdown, Gap, Signal, DataLoss, Cancel };
  static constexpr uint32_t SAMPLE_HZ=50000, QUIET_US=1000000;
  static constexpr uint32_t MIN_PERIOD_US=2000, MAX_PERIOD_US=750000;
  // A launch starts only on a three-revolution window of at least this speed.
  // Through the launcher opening a revolution changes AO by 10-40 counts, and
  // idle AO wanders by the same 11-30 counts over 100-700 ms. Three matching
  // periods of that wander occasionally formed idle 90-640 RPM "launches",
  // indistinguishable from slow rotation by amplitude. Every recorded launch
  // began above 1,180 RPM, so slower windows cannot start a result.
  static constexpr float MIN_LAUNCH_RPM=1000;
  // Every mark in a counted three-revolution window must swing AO by at least
  // this much. In the enclosure (2026-09-26) real revolution marks measured
  // 900-1,100 counts, handling after a pull 100-270, and every idle or
  // picked-up phantom 10-21 counts (edges riding the noise band). The earlier
  // case gave real marks of only 10-40 counts, so its recordings are replayed
  // with minMark=0; a floor cannot separate phantoms from pulls there.
  static constexpr float MIN_LAUNCH_MARK=300;
  float minMark=MIN_LAUNCH_MARK;
  // Board/optics profiles may require more reversal hysteresis for a broad
  // mark with subsidiary peaks. The Waveshare default remains unchanged.
  float edgeSwingFraction=0.30f;
  // A display transfer disturbs AO a few milliseconds later: 1,000+ recorded
  // dips all fell 3.7-10.5 ms after the first sample read once the transfer
  // began. Edge and swing tracking hold their state through this window, so a
  // dip that comes and goes inside it is invisible, while a real transition
  // is still registered (late) when the window ends.
  static constexpr uint32_t BLANK_FROM_US=2500,BLANK_TO_US=14000;
  void displayWrite() {
    if(nowUs>=blankUntil)blankFrom=nowUs+BLANK_FROM_US;
    blankUntil=nowUs+BLANK_TO_US;
  }
  Phase phase=Phase::Settling;
  End ended=End::None;
  bool enabled=true, resultValid=false, signalFault=false;
  float peakRpm=0, resultRpm=0, candidateRpm=0;
  // Diagnostics for the burst: weakest mark in the fastest window, and the
  // noise band when the burst began. Phantoms sit near the noise band.
  float peakAmplitude=0, startNoiseBand=0;
  float signalLow=0, signalHigh=0, signalContrast=0, noiseBand=3, hysteresis=3;
  uint32_t launches=0, attempts=0, resultRevision=0, cycles=0, revolutions=0;
  uint32_t opticalEdges=0, rejectedPeriods=0, rejectedShape=0, inconsistentWindows=0, slowWindows=0, weakWindows=0;
  uint32_t rearmExtensions=0;
  uint64_t nowUs=0, resultUs=0, burstStartUs=0, burstEndUs=0;
  uint32_t quietMs() const {return uint32_t((nowUs-quietSince)/1000);}
  uint32_t rearmMs() const {return nowUs-quietSince>=QUIET_US?0:uint32_t((QUIET_US-(nowUs-quietSince)+999)/1000);}
  void setEnabled(bool value) {
    enabled=value; dataLoss(); ended=End::Cancel;
    phase=value?Phase::Settling:Phase::Paused;
  }
  void dataLoss(bool =true) {
    resultValid=false;resultRpm=0;peakRpm=0;resultRevision++;ended=End::DataLoss;
    phase=enabled?Phase::Settling:Phase::Paused;quietSince=nowUs;
    clearSequence();rise=fall=0;initialized=false;sum=0;count=index=group=0;
    diffCount=diffIndex=0;clearMotion();railSince=0;signalFault=false;swingCount=0;
  }
  void feed(uint16_t raw) {
    nowUs+=20;
    if(count<25)count++;else sum-=smooth[index];
    sum+=raw;smooth[index]=raw;index=(index+1)%25;
    if(++group<5)return;group=0;if(count<25)return;
    const float value=float(sum)/25;
    if(!initialized){initialized=true;extreme=swingExtreme=swingPivot=previous=value;high=swingHigh=false;return;}
    // Median slope rejects optical transitions and isolated interference when
    // estimating the background jitter of the 0.5 ms rolling mean.
    diffs[diffIndex]=fabsf(value-previous);diffIndex=(diffIndex+1)%128;
    if(diffCount<128)diffCount++;
    previous=value;
    if(diffCount==128 && diffIndex%32==0) {
      float sorted[128];std::copy(diffs,diffs+128,sorted);
      std::nth_element(sorted,sorted+64,sorted+128);
      noiseBand=fmaxf(3.0f,20.0f*sorted[64]);
    }
    const bool blanked=nowUs>=blankFrom && nowUs<blankUntil;
    if(!blanked)trackSwing(value);
    hysteresis=fmaxf(noiseBand,edgeSwingFraction*pulseSwing());
    // Only the LOW rail is a fault. More reflected IR pulls AO down, and the
    // strongest reflection in the enclosure reads about 130, so a full second
    // near 0 means lost sensor power or wiring. The HIGH rail is an ordinary
    // state there: a shaft resting where little IR returns reads 4095 for as
    // long as it stays put (2026-09-26 recording). Treating it as a fault
    // cleared the previous result and swallowed the next pull, which began
    // inside the rearm second that followed recovery.
    if(value<5) {
      if(!railSince)railSince=nowUs;
      if(nowUs-railSince>=QUIET_US && !signalFault) {
        signalFault=true;resultValid=false;resultRpm=peakRpm=0;
        resultRevision++;ended=End::Signal;phase=enabled?Phase::Hold:Phase::Paused;
        clearSequence();clearMotion();rise=fall=0;quietSince=nowUs;
      }
    } else {
      railSince=0;
      if(signalFault){signalFault=false;quietSince=nowUs;extreme=value;rise=fall=0;high=false;}
    }
    if(!signalFault && !blanked) {
      if(high) {
        extreme=fmaxf(extreme,value);
        if(extreme-value>=hysteresis) {
          signalHigh=extreme;
          high=false;extreme=value;fall=nowUs-260;
        }
      } else {
        extreme=fminf(extreme,value);
        if(value-extreme>=hysteresis) {
          signalLow=extreme;signalContrast=fmaxf(0,signalHigh-signalLow);
          high=true;extreme=value;
          const uint64_t stamp=nowUs-260;
          if(rise && fall>rise)cycle(stamp,uint32_t(fall-rise));
          rise=stamp;
        }
      }
    }
    tick();
  }
  const char *stateName() const {
    if(signalFault)return "CHECK SENSOR";
    switch(phase){case Phase::Paused:return "PAUSED";case Phase::Settling:return "STARTING";
      case Phase::Ready:return "READY";case Phase::Launch:return "MEASURING";default:return "REARM";}
  }
  const char *endName() const {
    switch(ended){case End::Slowdown:return "slowdown";case End::Gap:return "gap";
      case End::Signal:return "signal_fault";
      case End::DataLoss:return "data_loss";case End::Cancel:return "cancelled";default:return "none";}
  }
private:
  uint16_t smooth[25]={};uint32_t sum=0;unsigned count=0,index=0,group=0;
  float diffs[128]={},previous=0,extreme=0;
  unsigned diffCount=0,diffIndex=0;
  bool initialized=false,high=false;
  // Every reversal larger than the noise band, independent of the edge
  // hysteresis. A pulse's size comes from these swings rather than an overall
  // min/max envelope: a string pull can shift the whole baseline by hundreds of
  // counts while each revolution's mark changes it by only tens.
  static constexpr unsigned SWINGS=8;
  static constexpr uint32_t SWING_WINDOW_US=1000000;
  float swingSize[SWINGS]={},swingExtreme=0,swingPivot=0;
  uint64_t swingUs[SWINGS]={};
  unsigned swingCount=0,swingNext=0;
  bool swingHigh=false;
  void trackSwing(float value) {
    const bool reversed=swingHigh?swingExtreme-value>=noiseBand:value-swingExtreme>=noiseBand;
    if(swingHigh)swingExtreme=fmaxf(swingExtreme,value);else swingExtreme=fminf(swingExtreme,value);
    if(!reversed)return;
    swingSize[swingNext]=fabsf(swingExtreme-swingPivot);swingUs[swingNext]=nowUs;
    swingNext=(swingNext+1)%SWINGS;if(swingCount<SWINGS)swingCount++;
    swingPivot=swingExtreme;swingExtreme=value;swingHigh=!swingHigh;
  }
  // Third-largest swing of the last second: a revolution repeats its swing, so
  // up to two isolated baseline steps cannot raise the edge hysteresis. Old
  // strong pulses age out, so they cannot hide a weaker next pull either.
  float pulseSwing() const {
    float top[3]={0,0,0};
    for(unsigned i=0;i<swingCount;i++) {
      if(nowUs-swingUs[i]>SWING_WINDOW_US)continue;
      float size=swingSize[i];
      for(unsigned j=0;j<3;j++)if(size>top[j])std::swap(size,top[j]);
    }
    return top[2];
  }
  uint64_t rise=0,fall=0,railSince=0,quietSince=0,lastCycle=0,slowStartUs=0;
  uint64_t blankFrom=0,blankUntil=0;
  uint32_t periods[3]={},nPeriods=0,lastPeriod=0,slowCount=0,motionPeriod=0;
  float motionDuty=0,motionAmplitude=0;
  uint64_t motionStamp=0;
  void clearMotion(){motionPeriod=0;motionStamp=0;}
  float duties[3]={},amplitudes[3]={};
  void clearSequence(){nPeriods=lastPeriod=slowCount=0;lastCycle=slowStartUs=0;}
  void finish(End reason) {
    // The burst ends at the inferred boundary, not at the later instant that
    // a gap / second slow cycle confirms it.
    burstEndUs=reason==End::Slowdown?slowStartUs:lastCycle;
    ended=reason;phase=Phase::Hold;resultUs=nowUs;
    resultValid=peakRpm>0;resultRpm=peakRpm;resultRevision++;
    if(resultValid)launches++;
    clearSequence();
  }
  void tick() {
    if(!enabled || signalFault)return;
    if(phase==Phase::Launch || (phase==Phase::Ready && nPeriods)) {
      const uint32_t limit=std::min<uint32_t>(900000,std::max<uint32_t>(30000,2*lastPeriod));
      if(lastCycle && nowUs-lastCycle>limit) {
        if(phase==Phase::Launch)finish(End::Gap);else clearSequence();
      }
    }
    if((phase==Phase::Hold || phase==Phase::Settling) && nowUs-quietSince>=QUIET_US) {
      const bool afterPull=phase==Phase::Hold && resultValid;
      phase=Phase::Ready;clearSequence();
      if(afterPull) {
        // Preserve the learned noise floor; discard the completed pull's edge
        // history. Its swings stop counting one second after they occurred.
        clearMotion();extreme=previous;
        signalLow=signalHigh=previous;signalContrast=0;
        high=false;rise=fall=0;
      }
    }
  }
  void cycle(uint64_t stamp,uint32_t highUs) {
    opticalEdges++;
    const uint64_t wide=stamp-rise;
    if(wide<MIN_PERIOD_US || wide>MAX_PERIOD_US) {rejectedPeriods++;nPeriods=0;clearMotion();return;}
    const uint32_t period=uint32_t(wide);
    // Both colors must occupy a meaningful part of the cycle. Narrow electrical
    // dips repeated by display updates are not complete shaft revolutions.
    if(highUs<300 || period-highUs<300 || highUs*20<period || (period-highUs)*20<period) {
      rejectedShape++;nPeriods=0;clearMotion();return;
    }
    const float duty=float(highUs)/period;
    candidateRpm=60000000.0f/period;
    if(!enabled || signalFault)return;
    // Rewind needs adjacent, similar full cycles. Never join a pulse to one
    // before a rejected edge/gap: that allowed stray noise to restart the timer.
    const bool adjacent=motionStamp && stamp-motionStamp==period;
    const bool matching=motionPeriod && uint64_t(period)*4<=uint64_t(motionPeriod)*5 &&
      uint64_t(motionPeriod)*4<=uint64_t(period)*5 && fabsf(duty-motionDuty)<=0.20f &&
      signalContrast>0 && motionAmplitude>0 && signalContrast<=motionAmplitude*2.5f &&
      motionAmplitude<=signalContrast*2.5f;
    if(adjacent && matching) {
      if(phase==Phase::Hold){quietSince=nowUs;rearmExtensions++;}
      else if(phase==Phase::Launch)quietSince=nowUs;
    }
    motionPeriod=period;motionDuty=duty;motionAmplitude=signalContrast;motionStamp=stamp;
    if(lastCycle && stamp-lastCycle>uint64_t(period)*3/2)clearSequence();
    lastCycle=stamp;
    if(phase==Phase::Launch && peakRpm>0) {
      const float peakPeriod=60000000.0f/peakRpm;
      if(period>peakPeriod*1.45f) {
        if(!slowCount)slowStartUs=stamp-period;
        slowCount++;
      } else {slowCount=0;slowStartUs=0;}
      if(slowCount>=2){finish(End::Slowdown);return;}
    }
    lastPeriod=period;
    periods[nPeriods%3]=period;duties[nPeriods%3]=duty;
    amplitudes[nPeriods%3]=signalContrast;nPeriods++;
    if(phase==Phase::Launch)revolutions++;
    if(nPeriods<3)return;
    const auto bounds=std::minmax_element(periods,periods+3);
    const auto dutyBounds=std::minmax_element(duties,duties+3);
    const auto ampBounds=std::minmax_element(amplitudes,amplitudes+3);
    if(uint64_t(*bounds.second)*4>uint64_t(*bounds.first)*5 ||
        *dutyBounds.second-*dutyBounds.first>0.20f ||
        *ampBounds.first<=0 || *ampBounds.second>*ampBounds.first*2.5f) {
      inconsistentWindows++;return;
    }
    quietSince=nowUs; // Three matching cycles distinguish motion from stray dips.
    if(phase!=Phase::Ready && phase!=Phase::Launch)return;
    const float rpm=180000000.0f/(periods[0]+periods[1]+periods[2]);
    const bool strong=*ampBounds.first>=minMark;
    if(phase==Phase::Ready) {
      if(rpm<MIN_LAUNCH_RPM){slowWindows++;return;}
      if(!strong){weakWindows++;return;}
      burstStartUs=stamp-uint64_t(periods[0])-periods[1]-periods[2];
      phase=Phase::Launch;attempts++;peakRpm=0;cycles=0;revolutions=3;startNoiseBand=noiseBand;
      resultValid=false;resultRpm=0;ended=End::None;
    }
    if(!strong){weakWindows++;return;} // Weak windows never set the peak.
    if(rpm>peakRpm){peakRpm=rpm;peakAmplitude=*ampBounds.first;}
    cycles=nPeriods;
  }
};
