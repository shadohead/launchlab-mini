#pragma once
#include <algorithm>
#include <cstdint>

class InactivityTimer {
public:
  static constexpr uint32_t TIMEOUT_MS=10*60*1000;
  void touch(uint32_t now){lastActivity_=now;}
  uint32_t elapsed(uint32_t now)const{return now-lastActivity_;}
  uint32_t remaining(uint32_t now)const {
    const uint32_t idle=elapsed(now);return idle>=TIMEOUT_MS?0:TIMEOUT_MS-idle;
  }
  bool due(uint32_t now,bool measuring=false)const{return !measuring && elapsed(now)>=TIMEOUT_MS;}
private:
  uint32_t lastActivity_=0;
};

struct StickS3Battery {
  static constexpr uint32_t STALE_MS=15000;
  uint16_t millivolts=0;
  int percent=-1;
  bool voltageOk=false,chargeKnown=false,charging=false;
  uint32_t sampledAt=0;
  void update(uint16_t mv,bool voltageRead,bool chargeRead,uint8_t gpioBits,uint32_t now) {
    sampledAt=now;millivolts=mv;
    voltageOk=voltageRead && mv>=2500 && mv<=4350;
    // Match M5Unified 0.2.23's voltage-based estimate, using the one checked
    // PM1 read. This is approximate charge, not a measured runtime remaining.
    percent=voltageOk?std::max(0,std::min(100,(int(mv)-3300)*100/800)):-1;
    chargeKnown=chargeRead;charging=chargeRead && !(gpioBits&1); // PM1 G0 active low.
  }
  bool valid(uint32_t now)const{return voltageOk && now-sampledAt<=STALE_MS;}
  const char *chargeName()const{return !chargeKnown?"unknown":charging?"charging":"not_charging";}
};
