#include "../LaunchLabRpm/optical_calibration.h"
#include <fstream>
#include <iostream>
#include <vector>

int main(int argc,char **argv) {
  if(argc!=2){std::cerr<<"usage: replay_calibration samples.u16le\n";return 2;}
  std::ifstream f(argv[1],std::ios::binary);if(!f)return 2;
  std::vector<uint16_t> storage(OpticalCalibration::TOTAL_SAMPLES);
  OpticalCalibration cal;cal.begin(storage.data());
  char b[2];while(f.read(b,2))cal.record(uint8_t(b[0])|(uint16_t(uint8_t(b[1]))<<8));
  while(cal.analyzing())cal.process(5000);
  std::cout<<"{\"stage\":"<<unsigned(cal.stage)<<",\"recorded\":"<<cal.recorded
    <<",\"noise_span\":"<<cal.noiseSpan<<",\"passing\":"<<cal.passing
    <<",\"selected_contrast\":"<<cal.selectedContrast<<",\"matches\":"<<cal.bestMatches<<"}\n";
  for(unsigned i=0;i<cal.tested;i++) {
    const auto &r=cal.reports[i];
    std::cout<<"{\"index\":"<<i<<",\"contrast\":"<<r.contrast<<",\"above_noise\":"<<r.aboveNoise
      <<",\"idle_events\":"<<r.idleEvents<<",\"hits\":["<<r.hits[0]<<","<<r.hits[1]<<","<<r.hits[2]
      <<"],\"rpm\":["<<r.rpm[0]<<","<<r.rpm[1]<<","<<r.rpm[2]<<"],\"passed\":"<<r.passed<<"}\n";
  }
}
