#pragma once
#include "launch_motion.h"

// Short-window relative displacement estimate. The initial velocity is unknown
// and assumed zero at optical onset. This is never an absolute travel measure.
namespace MotionReplay {
struct Vec {
  float x=0,y=0,z=0;
  Vec operator+(Vec b)const{return {x+b.x,y+b.y,z+b.z};}
  Vec operator-(Vec b)const{return {x-b.x,y-b.y,z-b.z};}
  Vec operator*(float f)const{return {x*f,y*f,z*f};}
  float dot(Vec b)const{return x*b.x+y*b.y+z*b.z;}
  float length()const{return std::sqrt(dot(*this));}
  Vec unit()const{const float n=length();return n>.00001f?*this*(1/n):Vec{};}
  Vec cross(Vec b)const{return {y*b.z-z*b.y,z*b.x-x*b.z,x*b.y-y*b.x};}
};
inline Vec rotate(const LaunchMotion::Quaternion &q,Vec v) {
  const float in[3]={v.x,v.y,v.z};float out[3];q.rotate(in,out);return {out[0],out[1],out[2]};
}
inline LaunchMotion::Quaternion multiply(const LaunchMotion::Quaternion &a,const LaunchMotion::Quaternion &b) {
  return {a.w*b.w-a.x*b.x-a.y*b.y-a.z*b.z,a.w*b.x+a.x*b.w+a.y*b.z-a.z*b.y,
    a.w*b.y-a.x*b.z+a.y*b.w+a.z*b.x,a.w*b.z+a.x*b.y-a.y*b.x+a.z*b.w};
}
struct Replay {
  static constexpr unsigned COUNT=48;
  bool valid=false;
  Vec center[COUNT];LaunchMotion::Quaternion pose[COUNT];
  Vec forward,right,up;
  Vec world(Vec v)const{return {v.dot(forward),v.dot(right),v.dot(up)};}
  Vec baseline(Vec v)const{return forward*v.x+right*v.y+up*v.z;}
  Vec offset(unsigned i,Vec v)const{return world(rotate(pose[i],baseline(v)));}
  bool build(const LaunchMotion::Trace &t) {
    valid=false;if(!t.valid())return false;
    LaunchMotion::Interpolated onset;if(!LaunchMotion::interpolate(t,0,onset))return false;
    up=Vec{t.gravity[0],t.gravity[1],t.gravity[2]}.unit();
    if(up.length()<.9f)return false;
    forward=rotate(onset.q,{0,1,0});forward=(forward-up*forward.dot(up)).unit();
    if(forward.length()<.9f){forward=rotate(onset.q,{0,0,1});forward=(forward-up*forward.dot(up)).unit();}
    if(forward.length()<.9f)return false;
    right=up.cross(forward).unit();
    const LaunchMotion::Quaternion inverse{onset.q.w,-onset.q.x,-onset.q.y,-onset.q.z};
    Vec position,velocity,previous=world({onset.a[0],onset.a[1],onset.a[2]})*9.80665f;
    int lastMs=0;
    for(unsigned i=0;i<COUNT;++i) {
      const int ms=int(t.durationMs*i/(COUNT-1));LaunchMotion::Interpolated sample;
      if(!LaunchMotion::interpolate(t,ms,sample))return false;
      const Vec acceleration=world({sample.a[0],sample.a[1],sample.a[2]})*9.80665f;
      const float dt=(ms-lastMs)*.001f;const Vec change=acceleration-previous;
      // Exact integral of linearly interpolated acceleration over each step.
      position=position+velocity*dt+previous*(dt*dt*.5f)+change*(dt*dt/6);
      velocity=velocity+(previous+acceleration)*(dt*.5f);
      center[i]=position;pose[i]=multiply(sample.q,inverse);
      if(!std::isfinite(position.length()))return false;
      previous=acceleration;lastMs=ms;
    }
    valid=true;return true;
  }
};
struct Cube {
  Vec low,high;float glyph=0;
  Vec corner(unsigned i)const {
    static constexpr unsigned bits[8]={0,1,3,2,4,5,7,6};const unsigned b=bits[i];
    return {b&1?high.x:low.x,b&2?high.y:low.y,b&4?high.z:low.z};
  }
  Vec body(const Replay &r,unsigned i,unsigned vertex)const {
    static constexpr unsigned bits[8]={0,1,3,2,4,5,7,6};
    const unsigned b=bits[vertex];return r.center[i]+r.offset(i,{(b&1?1:-1)*glyph,(b&2?1:-1)*glyph*.22f,(b&4?1:-1)*glyph*.55f});
  }
  void fit(const Replay &trial,const Replay *reference=nullptr) {
    float span=.025f;
    for(const auto *r:{&trial,reference})if(r && r->valid)for(const auto &v:r->center)span=std::max(span,v.length());
    glyph=span*.22f;Vec lo{0,0,0},hi{0,0,0};
    for(const auto *r:{&trial,reference})if(r && r->valid)for(unsigned i=0;i<Replay::COUNT;++i)for(unsigned j=0;j<8;++j) {
      const Vec v=body(*r,i,j);lo={std::min(lo.x,v.x),std::min(lo.y,v.y),std::min(lo.z,v.z)};
      hi={std::max(hi.x,v.x),std::max(hi.y,v.y),std::max(hi.z,v.z)};
    }
    const float pad=span*.06f;
    const float side=std::max({hi.x-lo.x,hi.y-lo.y,2*std::max(std::fabs(lo.z),std::fabs(hi.z))})+2*pad;
    // True equal-sided cube; zero height stays centered. The right-face ring
    // marks onset, joined to the actual zero-origin pose just inside the face.
    const Vec mid{(lo.x+hi.x)*.5f,hi.y+pad-side*.5f,0};
    low=mid-Vec{side,side,side}*.5f;high=mid+Vec{side,side,side}*.5f;
  }
  Vec anchor()const{return {0,high.y,0};}
};
inline Vec camera(Vec v){return {(v.x+v.y)*.707106781f,(-v.x+v.y-2*v.z)*.40824829f,0};}
}
