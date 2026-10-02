#include "../LaunchLabMini/launch_motion.h"
#include <cassert>
#include <iostream>
#include <memory>
using namespace LaunchMotion;
static bool near(float a,float b,float tolerance){return std::fabs(a-b)<tolerance;}
static Trace capture(float speed=90,float heading=0,int skip=0,bool clipped=false,bool settled=true) {
  auto ring=std::make_unique<Ring>();Quaternion world;const float yaw[3]={0,0,heading};world.integrate(yaw,1);
  for(uint64_t us=1000000;us<=2800000;us+=10000) {
    if(skip && us>=2050000 && us<2050000+uint64_t(skip))continue;
    Quaternion body;const float rate[3]={0,speed,0};body.integrate(rate,std::max(0.0f,std::min(.65f,(int64_t(us)-1750000)*1e-6f)));
    Sample s;s.us=us;s.q=multiply(world,body);const float up[3]={0,0,1};inverse(s.q).rotate(up,s.a);
    s.g[1]=us>=1750000 && us<2400000?speed:0;s.fused=true;s.settled=settled;s.stationary=us<1750000;
    s.clipped=clipped && us==2150000;ring->feed(s);
  }
  return ring->build(2000000,2400000,6000,7);
}
int main() {
  assert(!captureReady(2255000,2000000,2249000)); // raw ready, fused post-roll still short
  assert(captureReady(2260000,2000000,2250000));
  assert(!captureReady(2249999,2000000,2250000));
  assert(captureReady(3000000,2000000,0)); // bounded unavailable-sensor timeout
  const auto t=capture();assert(t.valid() && t.fused && t.count==48 && t.durationMs==400);
  assert(t.points[0].ms==-500 && t.points[47].ms==650);
  unsigned onset=0,end=0;for(const auto &p:t.points){onset+=p.ms==0;end+=p.ms==400;assert(p.magnitude(false)<.003f);}
  assert(onset==1 && end==1 && t.startLevel.valid() && t.endLevel.valid());
  assert(near(t.startLevel.degrees,22.5f,.05f) && near(t.endLevel.degrees,58.5f,.05f));
  assert(t.startLevel.right<0 && t.endLevel.right<0);
  // Arbitrary global yaw cancels in relative comparisons, while actual turn
  // differences remain. A moving start never causes a stillness rejection.
  const auto heading=capture(90,123),changed=capture(120);
  assert(compare(t,heading).valid && compare(t,heading).turnDegrees<.05f);
  assert(compare(t,changed).valid && compare(t,changed).turnDegrees>5);
  assert(capture(90,0,50000).quality==Quality::Gap);
  assert(capture(90,0,0,true).quality==Quality::Clipped);
  assert(capture(90,0,0,false,false).quality==Quality::Warming);
  auto moving=t;moving.stationaryBias=false;assert(moving.valid() && compare(t,moving).valid);
  auto legacy=t;legacy.fused=false;assert(legacy.valid() && !compare(t,legacy).valid);
  auto ring=std::make_unique<Ring>();Sample sample;sample.a[2]=1;
  for(unsigned i=0;i<2000;++i){sample.us=1000000+i*10000;ring->feed(sample);}
  assert(ring->size()==Ring::CAPACITY && ring->at(0).us==10760000);
  ring->feed(sample);assert(ring->size()==Ring::CAPACITY);
  assert(ring->build(2000000,2400000,6000,1).quality==Quality::Missing);
  assert(ring->build(18000000,21000000,6000,1).quality==Quality::TooLong);
  Image image;encode(t,42,image);Trace restored;uint32_t gen=0;
  assert(decode(image,restored,gen) && gen==42 && restored.fused && restored.rpm==6000 && restored.number==7);
  assert(restored.startLevel.valid() && restored.endLevel.valid());
  assert(compare(restored,t).valid && compare(restored,t).turnDegrees<.05f);
  const auto valid=image;image[77]^=1;assert(!decode(image,restored,gen) && restored.number==7);
  image=valid;put32(image.data()+4,99);put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  for(unsigned schema=1;schema<=3;++schema) {
    image=valid;put32(image.data()+4,schema);put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));
    assert(decode(image,restored,gen) && restored.valid() && !restored.fused && restored.endLevel.valid());
  }
  image=valid;image[36]=99;put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  image=valid;put16(image.data()+40,32767);put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  image=valid;for(unsigned j=0;j<4;++j)put16(image.data()+64+14+j*2,0);
  put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  std::cout<<"PASS: full-rate fused poses, exact onset/end, gravity separation, fixed recorded tilt, heading-independent comparisons, moving-start acceptance, gap/clipping/warmup rejection, ring wrap, v4 storage and v1/v2/v3 retention\n";
}
