#include "../LaunchLabMini/launch_motion.h"
#include <cassert>
#include <iostream>
#include <memory>
using namespace LaunchMotion;
static bool near(float a,float b,float tolerance){return std::fabs(a-b)<tolerance;}
// Analytic 90 deg/s rotation around Y, with gravity expressed in the rotating
// body frame. Constant gyro offsets deliberately exercise resting calibration.
static Trace capture(bool acceleration=false,int skip=0,bool clipped=false,bool moving=false) {
  auto ring=std::make_unique<Ring>();
  for(uint64_t us=1000000;us<=2800000;us+=5000) {
    if(skip && us>=2050000 && us<2050000+uint64_t(skip))continue;
    const float seconds=std::max(0.0f,std::min(.65f,(int64_t(us)-1750000)*1e-6f));
    const float theta=90*seconds/DEG,c=std::cos(theta),s=std::sin(theta);
    const float ax=acceleration && us>=2000000 && us<=2400000?.3f:0;
    Sample sample;sample.us=us;sample.a[0]=c*ax-s;sample.a[2]=s*ax+c;
    sample.g[0]=1;sample.g[1]=2+(us>=1750000 && us<2400000?90:0);sample.g[2]=-1;
    if(moving && us<1500000)sample.g[0]=20;
    sample.clipped=clipped && us==2150000;ring->feed(sample);
  }
  return ring->build(2000000,2400000,6000,7);
}
int main() {
  const auto rotation=capture();assert(rotation.valid() && rotation.count==48 && rotation.durationMs==400);
  assert(rotation.points[0].ms== -500 && rotation.points[47].ms==650);
  float x,y;rotation.points[47].turn(x,y);assert(near(x,58.5f,.3f) && near(y,0,.1f));
  float roll,pitch,yaw;rotation.points[47].rotation().angles(roll,pitch,yaw);
  assert(near(roll,0,.1f) && near(pitch,58.5f,.3f) && near(yaw,0,.1f));
  // Analytic start/end pose from the recorded gyro and gravity, independent of
  // the current live sensor: 22.5 degrees at onset, 58.5 at optical end.
  assert(rotation.startLevel.valid() && rotation.endLevel.valid());
  assert(near(rotation.startLevel.degrees,22.5f,.4f) && near(rotation.endLevel.degrees,58.5f,.4f));
  assert(rotation.startLevel.right<0 && rotation.endLevel.right<0);
  StickS3Level live;live.feed(.6f,0,.8f,100);
  assert(rotation.startLevel.right<0 && live.reading(100).right>0);
  for(unsigned i=0;i<rotation.count;++i)assert(rotation.points[i].magnitude(false)<.006f);
  const auto accelerated=capture(true);bool found=false;
  for(unsigned i=0;i<accelerated.count;++i)if(accelerated.points[i].ms>30 && accelerated.points[i].ms<350) {
    assert(near(accelerated.points[i].a[0]*.001f,.3f,.006f));
    assert(std::abs(accelerated.points[i].a[2])<6);found=true;
  }
  assert(found && compare(rotation,rotation).valid && compare(rotation,rotation).turnDegrees<.05f);
  auto changed=rotation;changed.rpm=6600;changed.durationMs+=50;
  Quaternion offset;const float yawRate[3]={0,0,30};offset.integrate(yawRate,1);
  // A fixed 30-degree quaternion difference has a known geodesic error.
  for(unsigned i=0;i<changed.count;++i){auto &p=changed.points[i];p.q[0]=lroundf(offset.w*16384);p.q[1]=0;p.q[2]=0;p.q[3]=lroundf(offset.z*16384);p.a[0]=200;p.g[0]=100;}
  auto flat=changed;flat.rpm=6000;flat.durationMs=400;
  for(unsigned i=0;i<flat.count;++i){auto &p=flat.points[i];p.q[0]=16384;p.q[3]=0;p.a[0]=0;p.g[0]=0;}
  const auto difference=compare(flat,changed);assert(difference.valid && near(difference.turnDegrees,30,.01f));
  assert(near(difference.accelG,.2f,.001f) && near(difference.gyroDps,10,.01f));
  assert(difference.rpm==600 && near(difference.rpmPercent,10,.001f) && difference.durationMs==50);
  // Different sample timestamps are interpolated on elapsed time, without
  // stretching a short pull to the duration of a longer pull.
  auto ramp=flat,shifted=flat;
  for(unsigned i=0;i<ramp.count;++i){ramp.points[i].a[0]=ramp.points[i].ms;shifted.points[i].ms+=2;shifted.points[i].a[0]=shifted.points[i].ms;}
  assert(compare(ramp,shifted).valid && compare(ramp,shifted).accelG<.00001f);
  shifted.points[0].ms=2000;shifted.count=2;shifted.points[1].ms=2010;
  assert(!compare(ramp,shifted).valid);
  assert(capture(false,50000).quality==Quality::Gap);
  assert(capture(false,0,true).quality==Quality::Clipped);
  const auto moving=capture(false,0,false,true);assert(moving.valid() && !moving.stationaryBias && rotation.stationaryBias);
  moving.points[moving.count-1].rotation().angles(roll,pitch,yaw);assert(roll>1 && roll<10);
  auto ring=std::make_unique<Ring>();Sample sample;sample.a[2]=1;
  for(unsigned i=0;i<2000;++i){sample.us=1000000+i*5000;ring->feed(sample);}
  assert(ring->size()==Ring::CAPACITY && ring->at(0).us==5880000);
  ring->feed(sample);assert(ring->size()==Ring::CAPACITY);
  assert(ring->build(2000000,2400000,6000,1).quality==Quality::Missing);
  assert(ring->build(9000000,12000000,6000,1).quality==Quality::TooLong);
  Image image;encode(accelerated,42,image);Trace restored;uint32_t gen=0;
  assert(decode(image,restored,gen) && gen==42 && restored.rpm==6000 && restored.number==7);
  assert(restored.startLevel.valid() && restored.endLevel.valid());
  assert(near(restored.startLevel.degrees,accelerated.startLevel.degrees,.01f));
  assert(near(restored.endLevel.right,accelerated.endLevel.right,.0001f));
  assert(compare(restored,accelerated).turnDegrees<.05f && compare(restored,accelerated).accelG<.00001f);
  const auto valid=image;image[77]^=1;assert(!decode(image,restored,gen) && restored.number==7);
  image=valid;put32(image.data()+4,99);put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  image=valid;put32(image.data()+4,1);put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(decode(image,restored,gen) && restored.stationaryBias);
  assert(restored.startLevel.valid() && near(restored.startLevel.degrees,22.5f,.4f));
  image=valid;put32(image.data()+4,2);image[36]=image[44]=0;
  put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(decode(image,restored,gen) && restored.endLevel.valid());
  image=valid;image[36]=99;put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  image=valid;put16(image.data()+40,32767);put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  image=valid;for(unsigned j=0;j<4;++j)put16(image.data()+64+14+j*2,0);
  put32(image.data()+IMAGE_BYTES-4,checksum(image.data(),IMAGE_BYTES-4));assert(!decode(image,restored,gen));
  std::cout<<"PASS: analytic rotation/bias, recorded start/end tilt independent of live pose, acceleration change, elapsed-time comparisons, RPM delta, gap/clipping rejection, moving start, ring wrap and v1/v2/v3 reference integrity\n";
}
