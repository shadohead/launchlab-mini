#include "../LaunchLabMini/motion_replay.h"
#include <cassert>
#include <iostream>
using namespace MotionReplay;
static bool near(float a,float b,float tolerance=.0001f){return std::fabs(a-b)<tolerance;}
static LaunchMotion::Trace trace(float acceleration=0,float heading=0) {
  LaunchMotion::Trace t;t.quality=LaunchMotion::Quality::Valid;t.fused=true;t.rpm=6000;t.durationMs=400;t.count=48;t.gravity[2]=1;
  const float yaw[3]={0,0,heading},turn[3]={0,90,0};LaunchMotion::Quaternion world;world.integrate(yaw,1);
  for(unsigned i=0;i<t.count;++i) {
    auto &p=t.points[i];p.ms=-500+int(i*1150/47);p.a[0]=std::lround(acceleration*1000);
    LaunchMotion::Quaternion body;body.integrate(turn,(p.ms+500)*.001f);
    const auto q=LaunchMotion::multiply(world,body);
    p.q[0]=std::lround(q.w*16384);p.q[1]=std::lround(q.x*16384);p.q[2]=std::lround(q.y*16384);p.q[3]=std::lround(q.z*16384);
  }
  return t;
}
int main() {
  assert(camera({0,1,0}).x>0 && camera({0,1,0}).y<0);
  assert(camera({1,0,0}).x>0 && camera({1,0,0}).y>0);
  assert(camera({0,0,1}).y<0);
  Replay rotation,translated,heading;assert(rotation.build(trace()) && translated.build(trace(2)) && heading.build(trace(0,123)));
  assert(rotation.ms[0]==-500 && rotation.ms[47]==650);
  for(unsigned i=0;i<Replay::COUNT;++i) {
    assert(LaunchMotion::Quaternion::difference(rotation.pose[i],translated.pose[i])<.05f);
    assert(LaunchMotion::Quaternion::difference(rotation.pose[i],heading.pose[i])<.05f);
    Cube cube;Vec center;
    for(unsigned j=0;j<8;++j) {
      const auto v=cube.body(rotation,i,j);center=center+v;
      assert(v.x>=cube.low.x && v.x<=cube.high.x && v.y>=cube.low.y && v.y<=cube.high.y && v.z>=cube.low.z && v.z<=cube.high.z);
    }
    assert(near(center.length(),0));
    assert(near(cube.high.x-cube.low.x,cube.high.y-cube.low.y) && near(cube.high.x-cube.low.x,cube.high.z-cube.low.z));
  }
  // Initial tilt is retained, not silently flattened at optical onset.
  const LaunchMotion::Quaternion neutralHeading{std::cos(.785398163f*.5f),0,0,std::sin(.785398163f*.5f)};
  assert(near(LaunchMotion::Quaternion::difference(rotation.pose[0],neutralHeading),0,.03f));
  assert(near(LaunchMotion::Quaternion::difference(rotation.pose[47],neutralHeading),103.5f,.03f));
  const float up[3]={0,0,1};float actual[3],shown[3];
  for(unsigned i=0;i<Replay::COUNT;++i) {
    LaunchMotion::Interpolated original;assert(LaunchMotion::interpolate(trace(),rotation.ms[i],original));
    LaunchMotion::inverse(original.q).rotate(up,actual);LaunchMotion::inverse(rotation.pose[i]).rotate(up,shown);
    for(unsigned j=0;j<3;++j)assert(near(actual[j],shown[j],.0002f));
  }
  // An upright neutral screen faces midway between the front walls. Its
  // width is horizontal on screen and its top stays gravity-up. This is a
  // display-heading choice only; no position or measured inclination changes.
  auto upright=trace();LaunchMotion::Quaternion uprightQ;const float tip[3]={90,0,0};uprightQ.integrate(tip,1);
  for(unsigned i=0;i<upright.count;++i) {
    auto &p=upright.points[i];p.q[0]=std::lround(uprightQ.w*16384);p.q[1]=std::lround(uprightQ.x*16384);p.q[2]=0;p.q[3]=0;
  }
  Replay facing;assert(facing.build(upright));
  const Vec width=rotate(facing.pose[0],{1,0,0}),top=rotate(facing.pose[0],{0,1,0}),front=rotate(facing.pose[0],{0,0,1});
  assert(near(camera(width).y,0) && near(camera(width).x,1));
  assert(near(top.x,0) && near(top.y,0) && near(top.z,1));
  assert(front.x>0 && front.y<0 && near(front.x,-front.y));
  const auto nearestEdge=camera({1,-1,0});assert(near(nearestEdge.x,0));
  auto missing=trace();missing.quality=LaunchMotion::Quality::Gap;assert(!rotation.build(missing) && !rotation.valid);
  missing=trace();missing.fused=false;assert(!rotation.build(missing));
  missing=trace();missing.points[0].ms=10;assert(!rotation.build(missing));
  std::cout<<"PASS: fixed-center rotation only, neutral screen faces nearest middle edge, measured tilt preserved, acceleration cannot create travel, arbitrary heading canceled, constant cube scale, full rotated-body containment, pre/post capture, and legacy/invalid rejection\n";
}
