#include "../LaunchLabRpm/launch_detector.h"
#include <cassert>
#include <cmath>
#include <iostream>

static void level(LaunchDetector &d,uint16_t value,uint32_t us){for(uint32_t n=0;n<us/20;n++)d.feed(value);}
static void cycles(LaunchDetector &d,const uint32_t *periods,unsigned n){
  for(unsigned i=0;i<n;i++){level(d,1250,periods[i]/2);level(d,250,periods[i]-periods[i]/2);}
}
static void pull(LaunchDetector &d){
  const uint32_t p[]={24000,16000,12000,10000,9000,8000,8000,8000,8000,11000,14000};
  cycles(d,p,sizeof(p)/sizeof(*p));level(d,250,100000);
}
static uint32_t noiseState=1234567;
static void noisyLevel(LaunchDetector &d,int value,uint32_t us){
  for(uint32_t i=0;i<us/20;i++){
    noiseState=noiseState*1664525u+1013904223u;
    d.feed(uint16_t(value+int((noiseState>>16)%21)-10));
  }
}
static void weakPull(LaunchDetector &d,int base){
  const uint32_t p[]={24000,16000,12000,10000,9000,8000,8000,8000,8000,8000,11000,14000};
  for(uint32_t period:p){noisyLevel(d,base+12,period/2);noisyLevel(d,base,period-period/2);}
  noisyLevel(d,base,100000);
}
int main(){
  LaunchDetector d;level(d,250,1500000);assert(d.phase==LaunchDetector::Phase::Ready);
  pull(d);assert(d.launches==1 && d.resultValid && std::fabs(d.resultRpm-7500)<2);
  float first=d.resultRpm;
  // A faster spring-return train during the lock must never replace the launch.
  uint32_t fast[25];for(auto &p:fast)p=6000;cycles(d,fast,25);level(d,250,100000);
  assert(d.launches==1 && d.resultRpm==first);
  level(d,250,2500000);assert(d.phase==LaunchDetector::Phase::Ready && d.resultRpm==first);
  pull(d);assert(d.launches==2);
  d.setEnabled(false);level(d,250,3000000);pull(d);assert(d.launches==2);
  d.setEnabled(true);level(d,250,1500000);
  // A short electrical glitch is ignored; deliberate 300 RPM turns now count.
  level(d,1250,100);level(d,250,100000);
  uint32_t slow[30];for(auto &p:slow)p=200000;cycles(d,slow,30);
  level(d,1250,2000000);level(d,250,2000000);assert(d.launches==3 && std::fabs(d.resultRpm-300)<2);
  // One extra revolution-like pulse cannot inflate a previously supported peak.
  LaunchDetector spike;level(spike,250,1500000);
  uint32_t p[]={16000,12000,10000,8000,8000,8000,8000,4000,8000,8000};
  cycles(spike,p,10);level(spike,250,100000);
  assert(spike.launches==1 && spike.resultRpm<=7501);
  // Missing ADC samples invalidate an in-progress launch instead of bridging it.
  LaunchDetector loss;level(loss,250,1500000);
  uint32_t steady[8];for(auto &v:steady)v=8000;cycles(loss,steady,8);
  assert(loss.phase==LaunchDetector::Phase::Launch);loss.dataLoss();
  assert(!loss.resultValid && loss.phase==LaunchDetector::Phase::Hold);
  level(loss,250,2500000);pull(loss);assert(loss.launches==1 && loss.resultValid);
  LaunchDetector zero;level(zero,0,3000000);assert(zero.signalFault && zero.launches==0);
  level(zero,250,1600000);assert(!zero.signalFault && zero.phase==LaunchDetector::Phase::Ready);
  // Actual missed-pull scale: ~12 ADC counts of contrast amid ~6-count noise.
  // Repeated pulls at a different baseline must need no manual threshold edit.
  LaunchDetector weak;noisyLevel(weak,200,3000000);assert(weak.launches==0);
  weakPull(weak,200);assert(weak.launches==1 && weak.resultValid && weak.resultRpm>7000 && weak.resultRpm<8000);
  noisyLevel(weak,235,3000000);weakPull(weak,235);
  assert(weak.launches==2 && weak.resultValid && weak.resultRpm>7000 && weak.resultRpm<8000);
  noisyLevel(weak,235,10000000);assert(weak.launches==2);
  // The lock follows ongoing rewind, even when it continues beyond one second.
  // Then it expires one second after the last credible rotation, not after
  // incidental slow / isolated optical transitions.
  LaunchDetector rearm;level(rearm,250,1500000);pull(rearm);
  uint32_t longReturn[200];for(auto &v:longReturn)v=8000;
  cycles(rearm,longReturn,200);level(rearm,250,100000);
  assert(rearm.launches==1 && rearm.phase==LaunchDetector::Phase::Hold && rearm.rearmMs()>800);
  level(rearm,250,(rearm.rearmMs()-1)*1000);
  assert(rearm.phase==LaunchDetector::Phase::Hold);
  level(rearm,250,2000);assert(rearm.phase==LaunchDetector::Phase::Ready);
  pull(rearm);assert(rearm.launches==2);
  // Slow transitions outside the rotation envelope used to extend the lock.
  uint32_t drift[3];for(auto &v:drift)v=600000;
  const uint32_t edgesBefore=rearm.opticalEdges;
  cycles(rearm,drift,3);
  assert(rearm.opticalEdges>edgesBefore && rearm.phase==LaunchDetector::Phase::Ready);
  pull(rearm);assert(rearm.launches==3);
  // Consecutive launches need only the requested second of stillness.
  for(unsigned i=0;i<3;i++) {level(rearm,250,1050000);pull(rearm);}
  assert(rearm.launches==6);
  // Before a profile passes calibration, retain the previous speed gate so
  // periodic low-frequency background changes cannot become slow-pull results.
  LaunchDetector uncalibrated;uncalibrated.minimumRpm=3000;
  level(uncalibrated,250,1500000);cycles(uncalibrated,slow,30);
  level(uncalibrated,250,1100000);assert(uncalibrated.launches==0);
  pull(uncalibrated);assert(uncalibrated.launches==1);
  std::cout<<"PASS: peak, rewind exclusion, one-second motion-based rearm, pause, deliberate slow pulls, static/glitch rejection, discontinuity, sensor recovery, weak contrast, shifted baseline, idle noise, repeated pulls\n";
}
