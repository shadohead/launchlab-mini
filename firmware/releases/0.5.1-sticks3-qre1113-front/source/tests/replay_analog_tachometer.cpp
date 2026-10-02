#include "../LaunchLabRpm/analog_tachometer.h"
#include <fstream>
#include <iostream>
#include <string>
int main(int argc,char**argv) {
  if(argc<2 || argc>3)return 2;std::ifstream f(argv[1],std::ios::binary);if(!f)return 2;
  AnalogTachometer d;uint32_t revision=0;char b[2];
  // Optional mark floor override: recordings from the earlier case carried
  // only 10-40 count marks and are replayed with 0 to exercise the rest.
  if(argc==3)d.minMark=std::stof(argv[2]);
  while(f.read(b,2)) {
    // Since 0.5.3 bit 15 marks the first sample read after a display transfer
    // began, exactly as the firmware reports it to the detector.
    const uint16_t raw=uint8_t(b[0])|(uint16_t(uint8_t(b[1]))<<8);
    if(raw&0x8000)d.displayWrite();
    d.feed(raw&0x0fff);
    if(d.resultRevision!=revision) {
      revision=d.resultRevision;
      std::cout<<"{\"time_s\":"<<d.nowUs/1e6<<",\"valid\":"<<d.resultValid<<",\"rpm\":"<<d.resultRpm
        <<",\"cycles\":"<<d.cycles<<",\"revs\":"<<d.revolutions<<",\"amplitude\":"<<d.peakAmplitude<<",\"start_noise\":"<<d.startNoiseBand<<",\"reason\":\""<<d.endName()<<"\"}\n";
    }
  }
  std::cout<<"{\"summary\":true,\"launches\":"<<d.launches<<",\"edges\":"<<d.opticalEdges<<",\"shape_rejected\":"<<d.rejectedShape
    <<",\"inconsistent\":"<<d.inconsistentWindows<<",\"slow_rejected\":"<<d.slowWindows<<",\"weak_rejected\":"<<d.weakWindows<<",\"noise\":"<<d.noiseBand<<",\"state\":\""<<d.stateName()<<"\"}\n";
}
