#include "../LaunchLabMini/motion_replay.h"
#include <cassert>
#include <iostream>
using namespace MotionReplay;
static bool near(float a,float b,float tolerance=.0001f){return std::fabs(a-b)<tolerance;}
static LaunchMotion::Trace trace(float ax=0,float ay=0,float az=0) {
  LaunchMotion::Trace t;t.quality=LaunchMotion::Quality::Valid;t.rpm=6000;t.durationMs=400;
  t.count=48;t.gravity[2]=1;
  for(unsigned i=0;i<t.count;++i){auto &p=t.points[i];p.ms=-500+int(i*1150/47);p.a[0]=std::lround(ax*1000);p.a[1]=std::lround(ay*1000);p.a[2]=std::lround(az*1000);}
  return t;
}
int main() {
  Replay still;assert(still.build(trace()));for(const auto &p:still.center)assert(near(p.length(),0));
  Replay rise,dip,forward;assert(rise.build(trace(0,0,.5f)) && dip.build(trace(0,0,-.5f)) && forward.build(trace(0,.5f,0)));
  const float expected=.5f*9.80665f*.4f*.4f*.5f;
  assert(near(rise.center[47].z,expected) && near(dip.center[47].z,-expected));
  assert(near(forward.center[47].x,expected) && near(forward.center[47].y,0));
  auto tilted=trace(.5f,0,0);tilted.gravity[2]=0;tilted.gravity[0]=1;
  Replay upright;assert(upright.build(tilted) && near(upright.center[47].z,expected));
  // Rotation without acceleration must turn the glyph without manufacturing
  // travel. Pose is relative to optical onset, including a nonzero onset pose.
  auto turning=trace();
  for(auto &p:turning.points){LaunchMotion::Quaternion q;const float rate[3]={0,0,90};q.integrate(rate,(p.ms+500)*.001f);p.q[0]=std::lround(q.w*16384);p.q[3]=std::lround(q.z*16384);}
  Replay rotation;assert(rotation.build(turning));
  for(const auto &p:rotation.center)assert(near(p.length(),0));
  assert(LaunchMotion::Quaternion::difference(rotation.pose[0],{})<.05f);
  assert(near(LaunchMotion::Quaternion::difference(rotation.pose[47],{}),36,.02f));
  for(const auto *r:{&still,&rise,&dip,&forward,&rotation}) {
    Cube cube;cube.fit(*r,&dip);
    assert(near(cube.high.x-cube.low.x,cube.high.y-cube.low.y));
    assert(near(cube.high.x-cube.low.x,cube.high.z-cube.low.z));
    assert(near(cube.high.z,-cube.low.z) && near(cube.anchor().z,0) && near(cube.anchor().y,cube.high.y));
    for(const auto *capture:{r,static_cast<const Replay *>(&dip)})for(unsigned i=0;i<Replay::COUNT;++i)for(unsigned j=0;j<8;++j) {
      const auto v=cube.body(*capture,i,j);
      assert(v.x>=cube.low.x && v.x<=cube.high.x && v.y>=cube.low.y && v.y<=cube.high.y && v.z>=cube.low.z && v.z<=cube.high.z);
    }
  }
  auto missing=trace();missing.quality=LaunchMotion::Quality::Gap;assert(!rise.build(missing) && !rise.valid);
  missing=trace();missing.gravity[2]=0;assert(!rise.build(missing));
  missing=trace();missing.points[0].ms=10;assert(!rise.build(missing));
  std::cout<<"PASS: analytic displacement, gravity-aligned rises/dips, relative gyro pose, no invented rotation travel, equal cube sides, full glyph containment, midpoint start, and invalid trace rejection\n";
}
