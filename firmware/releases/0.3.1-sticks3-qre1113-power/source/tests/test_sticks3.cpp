#include "../LaunchLabMini/sensor_profile.h"
#include "../LaunchLabMini/sample_ring.h"
#include <cassert>
#include <cmath>
#include <iostream>
using D=AnalogTachometer;
static void level(D &d,int value,uint32_t us) {
  for(uint32_t i=0;i<us/20;++i)d.feed(value);
}
static D ready() {
  D d;StickS3SensorProfile::configure(d);level(d,140,1200000);
  assert(d.phase==D::Phase::Ready);return d;
}
static void square(D &d,uint32_t period,unsigned count,int amplitude=100) {
  for(unsigned i=0;i<count;++i){level(d,140+amplitude,period/2);level(d,140,period-period/2);}
}
static void finish(D &d){level(d,140,1600000);}
static void broadMarks(D &d,uint32_t period,unsigned count) {
  // One broad reflective mark, with a 30-count subsidiary dip on its plateau.
  // The known fundamental is the independent timing oracle, not the code's
  // detected edges. A smaller hysteresis can count the internal dip as a cycle.
  for(unsigned cycle=0;cycle<count;++cycle)for(uint32_t us=0;us<period;us+=20) {
    const float t=float(us)/period;
    float value=140;
    if(t<.1f)value=140+100*t/.1f;
    else if(t<.2f)value=240;
    else if(t<.25f)value=240-30*(t-.2f)/.05f;
    else if(t<.35f)value=210+30*(t-.25f)/.1f;
    else if(t<.5f)value=240;
    else if(t<.6f)value=240-100*(t-.5f)/.1f;
    d.feed(uint16_t(value));
  }
}
int main() {
  D defaults;assert(defaults.minMark==300 && defaults.edgeSwingFraction==.30f);
  for(uint32_t period:{4000u,8000u,10000u,16000u,40000u,59000u}) {
    D d=ready();square(d,period,12);finish(d);
    assert(d.launches==1 && std::fabs(d.resultRpm-60000000.0f/period)<3);
  }
  for(uint32_t period:{61000u,100000u,200000u}) {
    D d=ready();square(d,period,12);finish(d);assert(d.launches==0);
  }
  for(int amplitude:{15,30,60,79}) {
    D d=ready();square(d,10000,16,amplitude);finish(d);
    assert(d.launches==0 && d.weakWindows>0);
  }
  for(uint32_t period:{8000u,12000u,20000u}) {
    D d=ready();broadMarks(d,period,18);finish(d);
    assert(d.launches==1 && std::fabs(d.resultRpm-60000000.0f/period)<3);
  }
  D shortBurst=ready();square(shortBurst,10000,2);finish(shortBurst);assert(shortBurst.launches==0);
  D rewind=ready();square(rewind,10000,12);level(rewind,140,60000);
  square(rewind,15000,80);finish(rewind);assert(rewind.launches==1);
  square(rewind,8000,12);finish(rewind);assert(rewind.launches==2);
  D loss=ready();square(loss,10000,3);loss.dataLoss();square(loss,10000,12);
  finish(loss);assert(loss.launches==0);
  D paused=ready();paused.setEnabled(false);square(paused,10000,12);finish(paused);assert(paused.launches==0);
  // Persistent startup 60 Hz interference must not arm, and a legitimate
  // 60 Hz pull after quiet must still be measurable. There is no 60 Hz notch.
  D mains;StickS3SensorProfile::configure(mains);square(mains,16680,180,1000);
  assert(mains.launches==0 && mains.phase==D::Phase::Settling);
  D sixty=ready();square(sixty,16680,12);finish(sixty);
  assert(sixty.launches==1 && std::fabs(sixty.resultRpm-60000000.0f/16680)<3);
  // Ring ordering across wrap and exports after data loss. Only the newest
  // contiguous segment may be exported; the hot path needs no 64-bit modulo.
  uint16_t storage[7]={};SampleRing ring(storage,7);
  for(uint16_t i=0;i<20;++i)ring.record(i);
  assert(ring.count()==7 && ring.first()==13 && ring.total()==20);
  for(unsigned i=0;i<7;++i)assert(storage[(ring.first()+i)%7]==13+i);
  ring.discontinuity();assert(ring.count()==0);
  for(uint16_t i=20;i<23;++i)ring.record(i);
  assert(ring.count()==3 && ring.first()==20);
  for(unsigned i=0;i<3;++i)assert(storage[(ring.first()+i)%7]==20+i);
  SampleRing noStorage(nullptr,7);noStorage.record(5);assert(noStorage.count()==0);
  std::cout<<"PASS: M5 period oracle, multi-peak marks, 80-count noise floor, 1000-RPM floor, short burst, rewind, pause/data loss, 60-Hz handling and recorder wrap/discontinuity\n";
}
