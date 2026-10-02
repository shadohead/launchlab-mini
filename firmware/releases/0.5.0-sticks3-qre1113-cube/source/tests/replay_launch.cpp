#include "../LaunchLabRpm/launch_detector.h"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <string>
#include <cstdlib>

int main(int argc,char **argv) {
  if(argc<2 || argc>3){std::cerr<<"usage: replay_launch samples.u16le [minimum_contrast]\n";return 2;}
  std::ifstream f(argv[1],std::ios::binary);if(!f)return 2;
  LaunchDetector detector;
  if(argc==3)detector.minimumContrast=std::stof(argv[2]);
  uint32_t revision=0;char bytes[2];
  while(f.read(bytes,2)) {
    detector.feed(uint8_t(bytes[0])|(uint16_t(uint8_t(bytes[1]))<<8));
    if(detector.resultRevision!=revision) {
      revision=detector.resultRevision;
      std::cout<<"{\"time_s\":"<<double(detector.nowUs)/1e6<<",\"valid\":"<<(detector.resultValid?"true":"false")
        <<",\"rpm\":"<<detector.resultRpm<<",\"cycles\":"<<detector.cycles<<",\"reason\":\""<<detector.endName()<<"\"}\n";
    }
  }
  std::cout<<"{\"summary\":true,\"launches\":"<<detector.launches<<",\"filtered\":"<<detector.filtered<<",\"state\":\""<<detector.stateName()<<"\"}\n";
}
