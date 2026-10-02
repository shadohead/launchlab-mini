#include "../LaunchLabRpm/optical_calibration.h"
#include <vector>
#include <cassert>
#include <iostream>

static std::vector<uint16_t> recording(unsigned pulls=3,int contrast=6,bool slow=false) {
  std::vector<uint16_t> data(OpticalCalibration::TOTAL_SAMPLES);
  uint32_t seed=3217;
  for(auto &value:data){seed=seed*1664525u+1013904223u;value=250+int((seed>>16)%21)-10;}
  for(unsigned attempt=0;attempt<pulls;attempt++) {
    uint32_t cursor=OpticalCalibration::NOISE_SAMPLES+attempt*OpticalCalibration::SLOT_SAMPLES+50000;
    const uint32_t fast[]={24000,16000,12000,10000,9000,8000,8000,8000,8000,8000,11000,14000};
    for(unsigned i=0;i<12;i++) {
      uint32_t period=slow?250000:fast[i];
      for(uint32_t j=0;j<period/40;j++)data[cursor+j]+=contrast;
      cursor+=period/20;
    }
  }
  return data;
}
static OpticalCalibration run(std::vector<uint16_t> input) {
  // Separate storage, as on the device: recording owns its destination.
  std::vector<uint16_t> storage(input.size());OpticalCalibration cal;cal.begin(storage.data());
  for(uint16_t value:input)cal.record(value);
  while(cal.analyzing())cal.process(5000);
  return cal;
}
int main() {
  auto weak=recording();
  LaunchDetector before;for(auto value:weak)before.feed(value);
  auto calibrated=run(weak);
  std::cout<<"before="<<before.launches<<" stage="<<int(calibrated.stage)<<" selected="<<calibrated.selectedContrast<<" passing="<<calibrated.passing<<"\n";
  assert(before.launches<3 && calibrated.stage==OpticalCalibration::Stage::Passed && calibrated.selectedContrast<8);
  assert(calibrated.tested==OpticalCalibration::PROFILE_COUNT);
  unsigned reportedPasses=0;
  for(const auto &report:calibrated.reports)if(report.passed){
    reportedPasses++;assert(report.aboveNoise && report.idleEvents==0);
    for(unsigned i=0;i<3;i++)assert(report.hits[i]==1 && report.rpm[i]>0);
  }
  assert(reportedPasses==calibrated.passing);
  LaunchDetector after;after.minimumContrast=calibrated.selectedContrast;
  for(auto value:weak)after.feed(value);assert(after.launches==3);
  assert(run(recording(2)).stage==OpticalCalibration::Stage::Failed);
  assert(run(recording(0)).stage==OpticalCalibration::Stage::Failed);
  assert(run(recording(3,16,true)).stage==OpticalCalibration::Stage::Passed);
  auto broken=recording();std::fill(broken.begin()+120000,broken.begin()+125000,0);
  assert(run(broken).stage==OpticalCalibration::Stage::Failed);
  OpticalCalibration cancelled;std::vector<uint16_t> buffer(OpticalCalibration::TOTAL_SAMPLES);
  cancelled.begin(buffer.data());cancelled.record(250);cancelled.fail("cancelled");
  cancelled.record(1250);cancelled.process();assert(cancelled.recorded==1);
  // Retry the same instance, including after a completed profile search and
  // an allocation failure. Old reports/results must not leak into a retry.
  calibrated.begin(nullptr);
  assert(calibrated.stage==OpticalCalibration::Stage::Failed);
  assert(calibrated.recorded==0 && calibrated.tested==0 && calibrated.passing==0);
  for(const auto &report:calibrated.reports) {
    assert(!report.passed && report.contrast==0 && report.idleEvents==0);
    for(unsigned i=0;i<3;i++)assert(report.hits[i]==0 && report.rpm[i]==0 && report.support[i]==0);
  }
  calibrated.begin(buffer.data());
  for(auto value:weak)calibrated.record(value);
  while(calibrated.analyzing())calibrated.process();
  assert(calibrated.stage==OpticalCalibration::Stage::Passed);
  cancelled.begin(buffer.data());cancelled.record(321);
  assert(cancelled.recording() && cancelled.recorded==1 && buffer[0]==321);
  std::cout<<"PASS: weak-signal improvement, exact three pulls, idle rejection, missing pull rejection, slow pulls, signal loss, cancellation, in-place retry reset\n";
}
