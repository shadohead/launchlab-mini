#pragma once
#include "launch_motion.h"
#include "level_indicator.h"

namespace MotionUI {
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
                     bool capturing,const StickS3Level::Reading &level) {
  const int cx=g.width()/2;char text[64];
  g.setTextDatum(top_center);g.setTextColor(TFT_WHITE,TFT_BLACK);
  snprintf(text,sizeof(text),"Launch #%lu",(unsigned long)trial.number);g.drawString(text,cx,5,2);
  snprintf(text,sizeof(text),"%.0f RPM",trial.rpm);g.setTextColor(TFT_CYAN,TFT_BLACK);g.drawString(text,cx,27,4);
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString(reference.valid()?"Gray ref / cyan latest":"Relative turn path",cx,59,1);
  if(trial.valid() && !capturing) {
    const float extent=path(g,trial,reference,cx,110,39);
    snprintf(text,sizeof(text),"+/-%.0f deg",extent);g.drawString(text,cx,152,1);
    float roll,pitch,yaw;trial.points[trial.count-1].rotation().angles(roll,pitch,yaw);
    g.drawString("End R / P / Y (deg)",cx,166,1);g.setTextColor(TFT_WHITE,TFT_BLACK);
    snprintf(text,sizeof(text),"%+.0f / %+.0f / %+.0f",roll,pitch,yaw);g.drawString(text,cx,177,1);
  } else {
    g.setTextColor(TFT_WHITE,TFT_BLACK);g.drawString(capturing?"Finishing capture...":LaunchMotion::name(trial.quality),cx,104,1);
    g.drawString("RPM still recorded",cx,132,1);
  }
  const int bx=36,by=208,radius=16;
  g.drawCircle(bx,by,radius,TFT_DARKGREY);g.drawFastHLine(bx-radius+2,by,2*radius-3,TFT_DARKGREY);
  g.drawFastVLine(bx,by-radius+2,2*radius-3,TFT_DARKGREY);
  if(level.valid()) {
    const auto color=level.degrees<=2?TFT_CYAN:TFT_ORANGE;
    g.fillCircle(bx+lroundf(level.right*12),by+lroundf(level.down*12),3,color);
    snprintf(text,sizeof(text),"%.1f deg",level.degrees);g.setTextColor(color,TFT_BLACK);g.drawString(text,89,204,1);
  } else {g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("--",89,204,1);}
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("A live  B history",cx,231,1);
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
    const float extent=path(g,trial,reference,cx,144,49);
    snprintf(text,sizeof(text),"Turn angles +/-%.0f deg",extent);g.drawString(text,cx,203,1);
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
}
}
