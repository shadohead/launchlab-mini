#include "../LaunchLabMini/sensor_profile.h"
#include <fstream>
#include <iostream>
#include <string>
int main(int argc,char **argv) {
  if(argc<2 || argc>3 || (argc==3 && std::string(argv[2])!="--three-turn"))return 2;
  std::ifstream input(argv[1],std::ios::binary);if(!input)return 2;
  AnalogTachometer detector;StickS3SensorProfile::configure(detector);
  if(argc==3)detector.singleTurnPeak=false;
  uint32_t revision=0;char bytes[2];
  while(input.read(bytes,2)) {
    const uint16_t sample=uint8_t(bytes[0])|(uint16_t(uint8_t(bytes[1]))<<8);
    // M5 display tags are evidence only. Its electrical blanking interval has
    // not been measured, so the Waveshare-specific interval does not apply.
    detector.feed(sample&0x0fff);
    if(detector.resultRevision!=revision) {
      revision=detector.resultRevision;
      std::cout<<"{\"time_s\":"<<detector.nowUs/1e6<<",\"valid\":"<<detector.resultValid
        <<",\"rpm\":"<<detector.resultRpm<<",\"amplitude\":"<<detector.peakAmplitude
        <<",\"three_turn_rpm\":"<<detector.sustainedPeakRpm
        <<",\"reason\":\""<<detector.endName()<<"\"}\n";
    }
  }
  if(!input.eof() || input.gcount()!=0)return 2;
  std::cout<<"{\"summary\":true,\"launches\":"<<detector.launches
    <<",\"edges\":"<<detector.opticalEdges<<",\"weak_rejected\":"<<detector.weakWindows
    <<",\"single_updates\":"<<detector.singlePeakUpdates<<",\"single_rejected\":"<<detector.singlePeakRejected
    <<",\"state\":\""<<detector.stateName()<<"\"}\n";
}
