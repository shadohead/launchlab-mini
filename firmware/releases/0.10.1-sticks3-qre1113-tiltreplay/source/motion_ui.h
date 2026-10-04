#pragma once
#include "launch_motion.h"
#include "level_indicator.h"
#include "motion_replay.h"

namespace MotionUI {
static constexpr uint32_t REPLAY_MS=1800;
inline void spatial(lgfx::LGFXBase &g,const LaunchMotion::Trace &trial,const LaunchMotion::Trace &reference,
                    int top,int height,float progress=1,bool showReference=false) {
  using namespace MotionReplay;
  // Fixed camera/scale and fused orientation only. Cached geometry lives off
  // the UI task stack; no live IMU, acquisition, travel or height inference.
  static Replay current,prior;static uint32_t lastCurrent=0,lastPrior=0;
  auto signature=[](const LaunchMotion::Trace &t){
    return LaunchMotion::checksum(reinterpret_cast<const uint8_t *>(t.points),sizeof(t.points))^
      LaunchMotion::checksum(reinterpret_cast<const uint8_t *>(t.gravity),sizeof(t.gravity))^
      t.durationMs^(t.count<<16)^(unsigned(t.quality)<<24)^(unsigned(t.fused)<<30);
  };
  const auto a=signature(trial),b=signature(reference);
  if(a!=lastCurrent){current.build(trial);lastCurrent=a;}
  if(b!=lastPrior){prior.build(reference);lastPrior=b;}
  if(!current.valid)return;
  Cube cube;Vec lo{1e9f,1e9f,0},hi{-1e9f,-1e9f,0};
  for(unsigned i=0;i<8;++i){const Vec p=camera(cube.corner(i));lo.x=std::min(lo.x,p.x);lo.y=std::min(lo.y,p.y);hi.x=std::max(hi.x,p.x);hi.y=std::max(hi.y,p.y);}
  const float scale=std::min((g.width()-12)/(hi.x-lo.x),(height-4)/(hi.y-lo.y));
  auto project=[&](Vec v){const Vec p=camera(v);return Vec{g.width()*.5f+(p.x-(lo.x+hi.x)*.5f)*scale,top+height*.5f+(p.y-(lo.y+hi.y)*.5f)*scale,0};};
  auto line=[&](Vec a,Vec b,uint16_t color){a=project(a);b=project(b);g.drawLine(lroundf(a.x),lroundf(a.y),lroundf(b.x),lroundf(b.y),color);};
  static constexpr unsigned edges[12][2]={{0,1},{1,2},{2,3},{3,0},{4,5},{5,6},{6,7},{7,4},{0,4},{1,5},{2,6},{3,7}};
  // Quiet rear edges, brighter near edges, a stationary mid-height plane and
  // a tiny up arrow give a gravity reference without obscuring the body.
  for(const auto &e:edges)line(cube.corner(e[0]),cube.corner(e[1]),0x18c3);
  for(const unsigned i:{0u,1u,5u,4u})line(cube.corner(i),cube.corner((i+1)%4+(i>=4?4:0)),0x39e7);
  line({-.84f,-.84f,0},{.84f,-.84f,0},0x2965);
  line({.84f,-.84f,0},{.84f,.84f,0},0x2965);
  g.drawLine(9,top+20,9,top+5,0x7bef);g.drawLine(9,top+5,6,top+9,0x7bef);g.drawLine(9,top+5,12,top+9,0x7bef);
  progress=std::max(0.0f,std::min(1.0f,progress));
  // Replay the optical pull, not the long quiet pre-roll. Start/End circles
  // below use the same onset/end timestamps, so the endpoint is unambiguous.
  const auto pose=current.at(lroundf(progress*trial.durationMs));
  auto body=[&](const LaunchMotion::Quaternion &q,unsigned vertex){
    static constexpr unsigned bits[8]={0,1,3,2,4,5,7,6};const unsigned v=bits[vertex];
    return rotate(q,{(v&1?1:-1)*.4f,(v&2?1:-1)*.65f,(v&4?1:-1)*.12f});
  };
  // Reference is confined to the dedicated motion page. Automatic recap shows
  // one solid body, avoiding a second pose that looks like another movement.
  if(showReference && prior.valid)for(const auto &e:edges)line(body(prior.at(int(reference.durationMs)),e[0]),body(prior.at(int(reference.durationMs)),e[1]),TFT_DARKGREY);
  Vec corners[8];for(unsigned i=0;i<8;++i)corners[i]=project(body(pose,i));
  auto face=[&](unsigned a,unsigned b,unsigned c,unsigned d,uint16_t color){
    g.fillTriangle(lroundf(corners[a].x),lroundf(corners[a].y),lroundf(corners[b].x),lroundf(corners[b].y),lroundf(corners[c].x),lroundf(corners[c].y),color);
    g.fillTriangle(lroundf(corners[a].x),lroundf(corners[a].y),lroundf(corners[c].x),lroundf(corners[c].y),lroundf(corners[d].x),lroundf(corners[d].y),color);
  };
  static constexpr unsigned faces[6][4]={{0,3,7,4},{1,2,6,5},{0,1,5,4},{3,2,6,7},{0,1,2,3},{4,5,6,7}};
  static constexpr Vec normal[6]={{-1,0,0},{1,0,0},{0,-1,0},{0,1,0},{0,0,-1},{0,0,1}};
  // Blue screen, violet back and dark sides provide front/back identity.
  static constexpr uint16_t colors[6]={0x1947,0x2169,0x298a,0x298a,0x50ea,0x0396};
  for(unsigned f=0;f<6;++f){const auto n=rotate(pose,normal[f]);if(n.x-n.y+n.z>0)face(faces[f][0],faces[f][1],faces[f][2],faces[f][3],colors[f]);}
  for(const auto &e:edges)line(body(pose,e[0]),body(pose,e[1]),0x5dff);
  // Thick white USB cap remains identifiable even when the screen faces away.
  const Vec usbA=project(rotate(pose,{-.4f,-.65f,0})),usbB=project(rotate(pose,{.4f,-.65f,0}));
  for(int offset=-1;offset<=1;++offset)g.drawLine(lroundf(usbA.x),lroundf(usbA.y)+offset,lroundf(usbB.x),lroundf(usbB.y)+offset,TFT_WHITE);
  // An inset rectangle identifies the screen; omit it when looking at the back.
  const auto front=rotate(pose,{0,0,1});
  if(front.x-front.y+front.z>0) {
    const Vec screen[4]={{-.28f,-.38f,.125f},{.28f,-.38f,.125f},{.28f,.43f,.125f},{-.28f,.43f,.125f}};
    for(unsigned i=0;i<4;++i)line(rotate(pose,screen[i]),rotate(pose,screen[(i+1)%4]),0x7e9f);
  }
}

inline void feedback(lgfx::LGFXBase &g,const LaunchMotion::Trace &trial,const LaunchMotion::Trace &reference,
                     bool capturing,bool demo=false,float progress=1) {
  const int cx=g.width()/2;char text[64];
  g.setTextDatum(top_center);
  if(demo){g.setTextColor(TFT_ORANGE,TFT_BLACK);g.drawString("DEMO",cx,2,1);}
  snprintf(text,sizeof(text),"%.0f RPM",trial.rpm);g.setTextColor(TFT_CYAN,TFT_BLACK);
  g.drawString(text,cx,17,g.textWidth(text,&fonts::Font4)<=g.width()-6?4:2);
  if(trial.valid() && trial.fused && !capturing) {
    spatial(g,trial,reference,49,112,progress);
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("Tilt replay",cx,164,1);
    g.drawFastHLine(26,178,83,0x39e7);
    g.fillCircle(26+lroundf(std::max(0.0f,std::min(1.0f,progress))*82),178,2,TFT_CYAN);
  } else {
    // Keep the graph area quiet when capture is pending or unavailable.
    g.drawRect(cx-39,71,79,79,TFT_DARKGREY);
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString(capturing?"Capturing":"No tilt data",cx,104,1);
  }
  for(unsigned i=0;i<2;++i) {
    const int bx=i?99:36,by=216,radius=19;
    const auto &level=i?trial.endLevel:trial.startLevel;
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString(i?"End":"Start",bx,180,2);
    g.drawCircle(bx,by,radius,TFT_DARKGREY);g.drawFastHLine(bx-radius+2,by,2*radius-3,TFT_DARKGREY);
    g.drawFastVLine(bx,by-radius+2,2*radius-3,TFT_DARKGREY);
    if(level.valid() && trial.fused && !capturing) {
      const auto color=level.degrees<=2?TFT_CYAN:TFT_ORANGE;
      g.fillCircle(bx+lroundf(level.right*15),by+lroundf(level.down*15),4,color);
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
  if(reference.valid() && reference.fused)snprintf(text,sizeof(text),"Ref #%lu: %.0f RPM",(unsigned long)reference.number,reference.rpm);
  else snprintf(text,sizeof(text),recreate || armed?"Next pull = reference":"No reference yet");
  g.drawString(text,cx,56,1);
  const auto difference=LaunchMotion::compare(reference,trial);
  if(!trial.valid() || !trial.fused || capturing) {
    g.setTextColor(TFT_WHITE,TFT_BLACK);
    g.drawString(capturing?"Finishing capture...":trial.valid() && !trial.fused?"Make a fresh launch":trial.number?LaunchMotion::name(trial.quality):"Make a launch",cx,99,1);
    g.drawString("RPM still recorded",cx,125,1);
  } else if(!recreate) {
    g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("Gray ref / cyan latest",cx,77,1);
    spatial(g,trial,reference,92,109,1,true);
    g.drawString("Rotation only",cx,203,1);
  } else if(!reference.valid() || !reference.fused) {
    g.setTextColor(TFT_WHITE,TFT_BLACK);g.drawString("Hold A to use this",cx,102,1);
    g.drawString("or make a fresh pull",cx,126,1);
  } else if(!difference.valid) {
    g.setTextColor(TFT_WHITE,TFT_BLACK);g.drawString("Too little shared time",cx,102,1);
    g.drawString("Try a similar pull",cx,126,1);
  } else {
    g.setTextColor(TFT_WHITE,TFT_BLACK);
    snprintf(text,sizeof(text),"RPM %+.0f  (%+.0f%%)",difference.rpm,difference.rpmPercent);g.drawString(text,cx,73,1);
    snprintf(text,sizeof(text),"Turn diff %.1f deg",difference.turnDegrees);g.drawString(text,cx,88,1);
    const int left=25,right=129;const int first=std::min(trial.points[0].ms,reference.points[0].ms);
    const int last=std::max(trial.points[trial.count-1].ms,reference.points[reference.count-1].ms);
    LaunchMotion::Interpolated onsetRef,onsetTrial;
    LaunchMotion::interpolate(reference,0,onsetRef);LaunchMotion::interpolate(trial,0,onsetTrial);
    auto turnError=[&](int ms) {
      LaunchMotion::Interpolated a,b;
      if(!LaunchMotion::interpolate(reference,ms,a) || !LaunchMotion::interpolate(trial,ms,b))return -1.0f;
      return LaunchMotion::Quaternion::difference(LaunchMotion::relative(onsetRef.q,a.q),LaunchMotion::relative(onsetTrial.q,b.q));
    };
    for(unsigned graph=0;graph<2;++graph) {
      const bool gyro=graph!=0;const int top=graph?163:110,bottom=graph?196:143;
      float maximum=gyro?100.0f:5.0f;
      for(const auto *t:{&reference,&trial})for(unsigned i=0;i<t->count;++i)
        maximum=std::max(maximum,(gyro?t->points[i].magnitude(true):turnError(t->points[i].ms))*1.1f);
      g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString(gyro?"Rotation speed deg/s":"Turn difference deg",cx,graph?151:99,1);
      snprintf(text,sizeof(text),"%.0f",maximum);
      g.setTextDatum(top_right);g.drawString(text,left-4,top,1);g.drawString("0",left-4,bottom-7,1);g.setTextDatum(top_center);
      g.drawFastVLine(left-2,top,bottom-top+1,TFT_DARKGREY);g.drawFastHLine(left-2,bottom,right-left+3,TFT_DARKGREY);
      const int zero=left+(0-first)*(right-left)/(last-first);
      g.drawFastVLine(zero,top,bottom-top+1,TFT_DARKGREY);
      for(const auto *t:{&reference,&trial}) {
        if(!gyro && t==&reference)continue;
        int lx=0,ly=0;bool connected=false;
        for(unsigned i=0;i<t->count;++i) {
          const int px=left+(t->points[i].ms-first)*(right-left)/(last-first);
          const float value=gyro?t->points[i].magnitude(true):turnError(t->points[i].ms);
          if(value<0){connected=false;continue;}
          const int py=bottom-lroundf(value/maximum*(bottom-top));
          if(connected)g.drawLine(lx,ly,px,py,t==&trial?TFT_CYAN:TFT_DARKGREY);lx=px;ly=py;connected=true;
        }
      }
    }
    snprintf(text,sizeof(text),"Pull time %+.0f ms",float(difference.durationMs));g.drawString(text,cx,206,1);
  }
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("A view  B back",cx,219,1);
  g.setTextColor(saveError?TFT_ORANGE:TFT_DARKGREY,TFT_BLACK);
  g.drawString(saveError?"Reference not saved":armed?"Next pull = new ref":"Hold A: use as ref",cx,231,1);
}
inline void makeDemo(LaunchMotion::Trace &t,bool reference) {
  t={};t.fused=t.stationaryBias=true;t.quality=LaunchMotion::Quality::Valid;t.count=LaunchMotion::Trace::POINTS;t.number=reference?1:2;
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
