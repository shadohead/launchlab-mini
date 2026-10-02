#pragma once
#include "launch_motion.h"

// Fixed-center orientation replay. Coordinates below are display units only.
// Translation, height change, distance, velocity and compass heading are absent.
namespace MotionReplay {
struct Vec {
  float x=0,y=0,z=0;
  Vec operator+(Vec b)const{return {x+b.x,y+b.y,z+b.z};}
  Vec operator-(Vec b)const{return {x-b.x,y-b.y,z-b.z};}
  Vec operator*(float f)const{return {x*f,y*f,z*f};}
  float length()const{return std::sqrt(x*x+y*y+z*z);}
};
inline Vec rotate(const LaunchMotion::Quaternion &q,Vec v) {
  const float in[3]={v.x,v.y,v.z};float out[3];q.rotate(in,out);return {out[0],out[1],out[2]};
}
struct Replay {
  static constexpr unsigned COUNT=48;
  bool valid=false;
  LaunchMotion::Quaternion pose[COUNT];int ms[COUNT]={};
  bool build(const LaunchMotion::Trace &t) {
    valid=false;if(!t.valid() || !t.fused)return false;
    LaunchMotion::Interpolated onset;if(!LaunchMotion::interpolate(t,0,onset))return false;
    // Include the recorded 500 ms before and 250 ms after the optical pull.
    // Optical onset fixes the relative orientation, not a guessed velocity.
    for(unsigned i=0;i<COUNT;++i) {
      ms[i]=t.points[0].ms+(t.points[t.count-1].ms-t.points[0].ms)*int(i)/int(COUNT-1);
      LaunchMotion::Interpolated sample;if(!LaunchMotion::interpolate(t,ms[i],sample))return false;
      pose[i]=LaunchMotion::relative(onset.q,sample.q);
    }
    valid=true;return true;
  }
};
struct Cube {
  // Fixed scale and centered body for every capture. These are not meters.
  Vec low{-1,-1,-1},high{1,1,1};
  Vec corner(unsigned i)const {
    static constexpr unsigned bits[8]={0,1,3,2,4,5,7,6};const unsigned b=bits[i];
    return {b&1?high.x:low.x,b&2?high.y:low.y,b&4?high.z:low.z};
  }
  Vec body(const Replay &r,unsigned i,unsigned vertex)const {
    static constexpr unsigned bits[8]={0,1,3,2,4,5,7,6};const unsigned b=bits[vertex];
    return rotate(r.pose[i],{(b&1?1:-1)*.65f,(b&2?1:-1)*.4f,(b&4?1:-1)*.12f});
  }
};
inline Vec camera(Vec v){return {(v.x+v.y)*.707106781f,(-v.x+v.y-2*v.z)*.40824829f,0};}
}
