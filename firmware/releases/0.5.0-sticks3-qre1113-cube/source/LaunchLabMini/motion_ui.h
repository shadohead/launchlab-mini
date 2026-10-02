#pragma once
#include "launch_motion.h"
#include "level_indicator.h"
#include "motion_replay.h"

namespace MotionUI {
inline void spatial(lgfx::LGFXBase &g,const LaunchMotion::Trace &trial,const LaunchMotion::Trace &reference,
                    int top,int height,float progress=1) {
  using namespace MotionReplay;
  // Keep geometry off the UI task stack; signatures refresh after capture or
  // reference selection. Drawing never reads the live IMU or ADC.
  static Replay current,prior;static uint32_t lastCurrent=0,lastPrior=0;
  auto signature=[](const LaunchMotion::Trace &t){
    return LaunchMotion::checksum(reinterpret_cast<const uint8_t *>(t.points),sizeof(t.points))^
      LaunchMotion::checksum(reinterpret_cast<const uint8_t *>(t.gravity),sizeof(t.gravity))^
      t.durationMs^(t.count<<16)^(unsigned(t.quality)<<24);
  };
  const auto a=signature(trial),b=signature(reference);
  if(a!=lastCurrent){current.build(trial);lastCurrent=a;}
  if(b!=lastPrior){prior.build(reference);lastPrior=b;}
  if(!current.valid)return;
  Cube cube;cube.fit(current,prior.valid?&prior:nullptr);
  Vec lo{1e9f,1e9f,0},hi{-1e9f,-1e9f,0};
  for(unsigned i=0;i<8;++i){const Vec p=camera(cube.corner(i));lo.x=std::min(lo.x,p.x);lo.y=std::min(lo.y,p.y);hi.x=std::max(hi.x,p.x);hi.y=std::max(hi.y,p.y);}
  const float scale=std::min((g.width()-12)/(hi.x-lo.x),(height-4)/(hi.y-lo.y));
  auto project=[&](Vec v){const Vec p=camera(v);return Vec{g.width()*.5f+(p.x-(lo.x+hi.x)*.5f)*scale,top+height*.5f+(p.y-(lo.y+hi.y)*.5f)*scale,0};};
  auto line=[&](Vec a,Vec b,uint16_t color){a=project(a);b=project(b);g.drawLine(lroundf(a.x),lroundf(a.y),lroundf(b.x),lroundf(b.y),color);};
  static constexpr unsigned edges[12][2]={{0,1},{1,2},{2,3},{3,0},{4,5},{5,6},{6,7},{7,4},{0,4},{1,5},{2,6},{3,7}};
  for(const auto &e:edges)line(cube.corner(e[0]),cube.corner(e[1]),TFT_DARKGREY);
  // Faint zero-height perimeter supplies a stable visual reference for dips.
  for(unsigned i=0;i<4;++i){Vec a=cube.corner(i),b=cube.corner((i+1)%4);a.z=b.z=0;line(a,b,0x2104);}
  for(const auto *r:{&prior,&current})if(r->valid)for(unsigned i=1;i<Replay::COUNT;++i)
    line(r->center[i-1],r->center[i],TFT_DARKGREY);
  const unsigned step=std::min(Replay::COUNT-1,unsigned(std::max(0.0f,std::min(1.0f,progress))*(Replay::COUNT-1)));
  for(unsigned i=1;i<=step;++i)line(current.center[i-1],current.center[i],TFT_CYAN);
  const Vec anchor=project(cube.anchor());line(cube.anchor(),{},TFT_DARKGREY);
  g.drawCircle(lroundf(anchor.x),lroundf(anchor.y),2,TFT_CYAN);
  // Wireframe end ghost stays still while the latest rectangle replays once.
  for(const auto &e:edges)line(cube.body(current,Replay::COUNT-1,e[0]),cube.body(current,Replay::COUNT-1,e[1]),TFT_DARKGREY);
  Vec body[8];for(unsigned i=0;i<8;++i)body[i]=project(cube.body(current,step,i));
  auto face=[&](unsigned a,unsigned b,unsigned c,unsigned d,uint16_t color){
    g.fillTriangle(lroundf(body[a].x),lroundf(body[a].y),lroundf(body[b].x),lroundf(body[b].y),lroundf(body[c].x),lroundf(body[c].y),color);
    g.fillTriangle(lroundf(body[a].x),lroundf(body[a].y),lroundf(body[c].x),lroundf(body[c].y),lroundf(body[d].x),lroundf(body[d].y),color);
  };
  face(0,3,7,4,0x0186);face(4,5,6,7,0x02aa);face(3,2,6,7,0x0350);
  for(const auto &e:edges)line(cube.body(current,step,e[0]),cube.body(current,step,e[1]),TFT_CYAN);
}
inline float path(lgfx::LGFXBase &g,const LaunchMotion::Trace &trial,const LaunchMotion::Trace &reference,int cx,int cy,int radius) {
  float extent=15;
  for(const auto *t:{&reference,&trial})if(t->valid())for(unsigned i=0;i<t->count;++i) {
    float x,y;t->points[i].turn(x,y);extent=std::max(extent,std::max(std::fabs(x),std::fabs(y)));
  }
  extent*=1.1f;
  g.drawRect(cx-radius,cy-radius,2*radius+1,2*radius+1,TFT_DARKGREY);
  g.drawFastHLine(cx-radius,cy,2*radius+1,TFT_DARKGREY);g.drawFastVLine(cx,cy-radius,2*radius+1,TFT_DARKGREY);
  for(const auto *t:{&reference,&trial})if(t->valid()) {
    int lastX=0,lastY=0;
    for(unsigned i=0;i<t->count;++i) {
      float x,y;t->points[i].turn(x,y);
      const int px=cx+lroundf(x/extent*radius),py=cy+lroundf(y/extent*radius);
      if(i)g.drawLine(lastX,lastY,px,py,t==&trial?TFT_CYAN:TFT_DARKGREY);lastX=px;lastY=py;
    }
    g.fillCircle(lastX,lastY,2,t==&trial?TFT_CYAN:TFT_DARKGREY);
  }
  return extent;
}
inline void feedback(lgfx::LGFXBase &g,const LaunchMotion::Trace &trial,const LaunchMotion::Trace &reference,
                     bool capturing,bool demo=false,float progress=1) {
  const int cx=g.width()/2;char text[64];
  g.setTextDatum(top_center);
  if(demo){g.setTextColor(TFT_ORANGE,TFT_BLACK);g.drawString("DEMO",cx,2,1);}
  snprintf(text,sizeof(text),"%.0f RPM",trial.rpm);g.setTextColor(TFT_CYAN,TFT_BLACK);
  g.drawString(text,cx,17,g.textWidth(text,&fonts::Font4)<=g.width()-6?4:2);
  if(trial.valid() && !capturing) {
    spatial(g,trial,reference,51,97,progress);
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("Estimated path",cx,153,1);
  } else {
    // Keep the graph area quiet when capture is pending or unavailable.
    g.drawRect(cx-39,71,79,79,TFT_DARKGREY);
  }
  for(unsigned i=0;i<2;++i) {
    const int bx=i?99:36,by=205,radius=23;
    const auto &level=i?trial.endLevel:trial.startLevel;
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString(i?"End":"Start",bx,165,2);
    g.drawCircle(bx,by,radius,TFT_DARKGREY);g.drawFastHLine(bx-radius+2,by,2*radius-3,TFT_DARKGREY);
    g.drawFastVLine(bx,by-radius+2,2*radius-3,TFT_DARKGREY);
    if(level.valid() && !capturing) {
      const auto color=level.degrees<=2?TFT_CYAN:TFT_ORANGE;
      g.fillCircle(bx+lroundf(level.right*18),by+lroundf(level.down*18),4,color);
    } else g.drawFastHLine(bx-3,by,7,TFT_DARKGREY);
  }
}
inline void draw(lgfx::LGFXBase &g,const LaunchMotion::Trace &trial,const LaunchMotion::Trace &reference,
                 bool recreate,bool capturing,bool armed,bool saveError,bool demo) {
  const int cx=g.width()/2;char text[64];
  g.setTextDatum(top_center);g.setTextColor(demo?TFT_ORANGE:TFT_WHITE,TFT_BLACK);
  g.drawString(demo?"DEMO":recreate?"Recreate":"Launch motion",cx,8,2);
  g.setTextColor(TFT_CYAN,TFT_BLACK);
  if(trial.number)snprintf(text,sizeof(text),"%.0f RPM",trial.rpm);else snprintf(text,sizeof(text),"-- RPM");
  g.drawString(text,cx,34,2);
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);
  if(reference.valid())snprintf(text,sizeof(text),"Ref #%lu: %.0f RPM",(unsigned long)reference.number,reference.rpm);
  else snprintf(text,sizeof(text),recreate || armed?"Next pull = reference":"No reference yet");
  g.drawString(text,cx,56,1);
  const auto difference=LaunchMotion::compare(reference,trial);
  if(!trial.valid() || capturing) {
    g.setTextColor(TFT_WHITE,TFT_BLACK);
    g.drawString(capturing?"Finishing capture...":trial.number?LaunchMotion::name(trial.quality):"Make a launch",cx,99,1);
    g.drawString("RPM still recorded",cx,125,1);
  } else if(!recreate) {
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("Gray ref / cyan latest",cx,77,1);
    spatial(g,trial,reference,92,109);
    g.drawString("Estimated path",cx,203,1);
  } else if(!reference.valid()) {
    g.setTextColor(TFT_WHITE,TFT_BLACK);g.drawString("Hold A to use this",cx,102,1);
    g.drawString("or make a fresh pull",cx,126,1);
  } else if(!difference.valid) {
    g.setTextColor(TFT_WHITE,TFT_BLACK);g.drawString("Too little shared time",cx,102,1);
    g.drawString("Try a similar pull",cx,126,1);
  } else {
    g.setTextColor(TFT_WHITE,TFT_BLACK);
    snprintf(text,sizeof(text),"RPM %+.0f  (%+.0f%%)",difference.rpm,difference.rpmPercent);g.drawString(text,cx,73,1);
    snprintf(text,sizeof(text),"Turn err %.1f deg",difference.turnDegrees);g.drawString(text,cx,88,1);
    const int left=25,right=129;const int first=std::min(trial.points[0].ms,reference.points[0].ms);
    const int last=std::max(trial.points[trial.count-1].ms,reference.points[reference.count-1].ms);
    for(unsigned graph=0;graph<2;++graph) {
      const bool gyro=graph!=0;const int top=graph?163:110,bottom=graph?196:143;
      float maximum=gyro?100.0f:.5f;
      for(const auto *t:{&reference,&trial})for(unsigned i=0;i<t->count;++i)maximum=std::max(maximum,t->points[i].magnitude(gyro)*1.1f);
      g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString(gyro?"Gyro deg/s":"Accel change g",cx,graph?151:99,1);
      snprintf(text,sizeof(text),gyro?"%.0f":"%.1f",maximum);
      g.setTextDatum(top_right);g.drawString(text,left-4,top,1);g.drawString("0",left-4,bottom-7,1);g.setTextDatum(top_center);
      g.drawFastVLine(left-2,top,bottom-top+1,TFT_DARKGREY);g.drawFastHLine(left-2,bottom,right-left+3,TFT_DARKGREY);
      const int zero=left+(0-first)*(right-left)/(last-first);
      g.drawFastVLine(zero,top,bottom-top+1,TFT_DARKGREY);
      for(const auto *t:{&reference,&trial}) {
        int lx=0,ly=0;
        for(unsigned i=0;i<t->count;++i) {
          const int px=left+(t->points[i].ms-first)*(right-left)/(last-first);
          const int py=bottom-lroundf(t->points[i].magnitude(gyro)/maximum*(bottom-top));
          if(i)g.drawLine(lx,ly,px,py,t==&trial?TFT_CYAN:TFT_DARKGREY);lx=px;ly=py;
        }
      }
    }
    snprintf(text,sizeof(text),"A err %.2fg %+.0fms",difference.accelG,float(difference.durationMs));g.drawString(text,cx,206,1);
  }
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("A view  B back",cx,219,1);
  g.setTextColor(saveError?TFT_ORANGE:TFT_DARKGREY,TFT_BLACK);
  g.drawString(saveError?"Reference not saved":armed?"Next pull = new ref":"Hold A: use as ref",cx,231,1);
}
inline void makeDemo(LaunchMotion::Trace &t,bool reference) {
  t={};t.quality=LaunchMotion::Quality::Valid;t.count=LaunchMotion::Trace::POINTS;t.number=reference?1:2;
  t.rpm=reference?6000:6500;t.durationMs=reference?400:450;t.gravity[2]=1;
  for(unsigned i=0;i<t.count;++i) {
    auto &p=t.points[i];p.ms=-500+int(i*1250/(t.count-1));
    const float s=std::max(0.0f,std::min(1.0f,p.ms/float(t.durationMs)));
    LaunchMotion::Quaternion q;const float rate[3]={reference?30.0f:45.0f,reference?65.0f:85.0f,reference?10.0f:30.0f};
    q.integrate(rate,s*t.durationMs*.001f);
    p.q[0]=lroundf(q.w*16384);p.q[1]=lroundf(q.x*16384);p.q[2]=lroundf(q.y*16384);p.q[3]=lroundf(q.z*16384);
    if(p.ms>0 && p.ms<int(t.durationMs))for(unsigned j=0;j<3;++j){p.g[j]=lroundf(rate[j]*10);p.a[j]=lroundf(std::sin(s*3.14159265f)*(reference?900:1300)*(j==0?1:.3f));}
  }
  LaunchMotion::recordLevels(t);
}
}
