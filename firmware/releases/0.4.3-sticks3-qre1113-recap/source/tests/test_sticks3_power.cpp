#include "../LaunchLabMini/power_status.h"
#include <cassert>
#include <iostream>

int main() {
  InactivityTimer timer;timer.touch(1000);
  assert(timer.remaining(1000)==600000 && !timer.due(600999));
  assert(timer.due(601000) && timer.remaining(601000)==0);
  assert(!timer.due(601000,true)); // active measured burst is protected
  timer.touch(601000);assert(!timer.due(1200999));assert(timer.due(1201000));
  timer.touch(UINT32_MAX-500000);
  assert(!timer.due(uint32_t(UINT32_MAX-500000+599999u)));
  assert(timer.due(uint32_t(UINT32_MAX-500000+600000u)));

  StickS3Battery b;
  assert(!b.valid(0) && b.percent==-1);
  b.update(3700,true,true,0,100);assert(b.valid(100) && b.percent==50 && b.charging);
  assert(b.valid(15100) && !b.valid(15101));
  b.update(4200,true,true,1,200);assert(b.percent==100 && !b.charging);
  b.update(3000,true,true,1,200);assert(b.percent==0);
  for(unsigned mv:{0u,2400u,4400u,65535u}) {
    b.update(mv,true,true,0,300);assert(!b.valid(300) && b.percent==-1);
  }
  b.update(3700,false,false,0,400);assert(!b.valid(400) && !b.chargeKnown && !b.charging);
  b.update(3900,true,false,0,500);assert(b.valid(500) && b.percent==75 && !b.chargeKnown);
  b.update(3900,true,true,1,UINT32_MAX-1000);assert(b.valid(1000));
  std::cout<<"PASS: exact 10-minute timeout, activity reset, active-burst guard, millis wrap, checked battery voltage, estimate limits, stale/error handling and charging GPIO\n";
}
