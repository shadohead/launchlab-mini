#include "../LaunchLabMini/history_checkpoint.h"
#include "../LaunchLabMini/sensor_profile.h"
#include <cassert>
#include <iostream>
static void level(AnalogTachometer &d,unsigned value,unsigned us){for(unsigned i=0;i<us/20;++i)d.feed(value);}
static void square(AnalogTachometer &d,unsigned count,unsigned amplitude=100){
  for(unsigned i=0;i<count;++i){level(d,140+amplitude,5000);level(d,140,5000);}
}
int main(){
  using Phase=AnalogTachometer::Phase;
  assert(!HistoryCheckpoint::practiceIdle(9999,0,10000,false,false,Phase::Ready));
  assert(HistoryCheckpoint::practiceIdle(10000,0,10000,false,false,Phase::Ready));
  for(Phase phase:{Phase::Launch,Phase::Hold,Phase::Settling})assert(!HistoryCheckpoint::practiceIdle(60000,0,10000,false,false,phase));
  assert(!HistoryCheckpoint::practiceIdle(60000,0,10000,true,false,Phase::Ready));
  assert(!HistoryCheckpoint::practiceIdle(60000,0,10000,false,true,Phase::Ready));
  assert(HistoryCheckpoint::practiceIdle(8999,UINT32_MAX-1000,10000,false,false,Phase::Ready));
  AnalogTachometer d;StickS3SensorProfile::configure(d);
  assert(!HistoryCheckpoint::allowedIdle(d,0)); // Starting is not safe.
  level(d,140,1200000);assert(HistoryCheckpoint::allowedIdle(d,0));
  // First strong mark precedes any completed cycle or confirmed launch.
  level(d,240,2000);assert(d.phase==AnalogTachometer::Phase::Ready);
  assert(!HistoryCheckpoint::allowedIdle(d,0));
  level(d,140,8000);square(d,1);
  assert(d.phase==AnalogTachometer::Phase::Ready && !HistoryCheckpoint::allowedIdle(d,0));
  square(d,10);assert(d.phase==AnalogTachometer::Phase::Launch && !HistoryCheckpoint::allowedIdle(d,0));
  level(d,140,40000);assert(d.launches==1 && d.phase==AnalogTachometer::Phase::Hold);
  assert(!HistoryCheckpoint::allowedIdle(d,1));
  level(d,140,1200000);assert(d.phase==AnalogTachometer::Phase::Ready);
  assert(!HistoryCheckpoint::allowedIdle(d,0)); // Accepted after UI snapshot: reject stale counter.
  assert(HistoryCheckpoint::allowedIdle(d,1));
  // A stopped incomplete attempt clears its candidate and eventually permits a save.
  square(d,2);assert(!HistoryCheckpoint::allowedIdle(d,1));
  level(d,140,200000);assert(HistoryCheckpoint::allowedIdle(d,1));
  // Weak periodic background is not an accepted candidate and cannot starve saves.
  square(d,10,30);assert(d.phase==AnalogTachometer::Phase::Ready && HistoryCheckpoint::allowedIdle(d,1));
  d.signalFault=true;assert(!HistoryCheckpoint::allowedIdle(d,1));d.signalFault=false;
  d.setEnabled(false);assert(HistoryCheckpoint::allowedIdle(d,1));
  std::cout<<"PASS: automatic idle history guard rejects startup, first strong mark, candidate, confirmed burst, rearm, stale counter and fault; quiet recovery and weak background permit saves\n";
}
