#pragma once
#include <algorithm>
#include "appearance.h"

namespace BestEffectUI {
// 1.1 KiB scratch mask, reused by the sole UI owner. No second framebuffer,
// heap allocation, delay, random input or acquisition interaction.
class Renderer {
  static constexpr int W=135,H=65,TOP=3;
  std::array<uint8_t,(W*H+7)/8> blocked_{};
  void block(int x,int y){if(x>=0 && x<W && y>=TOP && y<TOP+H){const unsigned b=(y-TOP)*W+x;blocked_[b/8]|=1u<<(b%8);}}
  bool allowed(int x,int y)const{
    if(x<3 || x>=W-3 || y<TOP || y>=TOP+H || (y>=13 && y<=45))return false;
    const unsigned b=(y-TOP)*W+x;return !(blocked_[b/8]&(1u<<(b%8)));
  }
  static float ease(float t){t=std::max(0.0f,std::min(1.0f,t));return 1-(1-t)*(1-t)*(1-t);}
  static uint16_t dim(uint16_t c,float f){f=std::max(0.0f,std::min(1.0f,f));return (unsigned(((c>>11)&31)*f)<<11)|(unsigned(((c>>5)&63)*f)<<5)|unsigned((c&31)*f);}
  template<class G>void pixel(G &g,int x,int y,uint16_t c){if(allowed(x,y))g.drawPixel(x,y,c);}
  template<class G>void line(G &g,int x,int y,int xx,int yy,uint16_t c){
    const int dx=std::abs(xx-x),sx=x<xx?1:-1,dy=-std::abs(yy-y),sy=y<yy?1:-1;int error=dx+dy;
    for(unsigned n=0;n<512;++n){pixel(g,x,y,c);if(x==xx && y==yy)break;const int e=2*error;if(e>=dy){error+=dy;x+=sx;}if(e<=dx){error+=dx;y+=sy;}}
  }
  template<class G>void rect(G &g,int x,int y,int w,int h,uint16_t c){
    for(int j=0;j<h;++j)for(int i=0;i<w;++i)if(!allowed(x+i,y+j))return;
    g.fillRect(x,y,w,h,c);
  }
  static void orbitPoint(float distance,int &x,int &y){
    constexpr float pi=3.14159265f,a=5*pi/2,p=2*(114+34)+4*a;
    float d=std::fmod(distance,p);if(d<0)d+=p;
    const float lengths[]={a,34,a,114,a,34,a,114};unsigned s=0;
    while(s<7 && d>lengths[s])d-=lengths[s++];
    float xx=0,yy=0;
    switch(s){
      case 0:xx=10+5*std::cos(pi/2+d/5);yy=44+5*std::sin(pi/2+d/5);break;
      case 1:xx=5;yy=44-d;break;
      case 2:xx=10+5*std::cos(pi+d/5);yy=10+5*std::sin(pi+d/5);break;
      case 3:xx=10+d;yy=5;break;
      case 4:xx=124+5*std::cos(3*pi/2+d/5);yy=10+5*std::sin(3*pi/2+d/5);break;
      case 5:xx=129;yy=10+d;break;
      case 6:xx=124+5*std::cos(d/5);yy=44+5*std::sin(d/5);break;
      default:xx=124-d;yy=49;break;
    }
    x=lroundf(xx);y=lroundf(yy);
  }
public:
  template<class G>void draw(G &g,Appearance::Effect effect,uint32_t elapsed,uint16_t color){
    if(g.width()!=W || g.height()!=240 || elapsed>=Appearance::duration(effect))return;
    blocked_.fill(0);
    // Dilate every existing clean UI pixel by 3px. The full numeric strip is
    // unconditionally locked, including blank glyph holes and font fallbacks.
    for(int y=0;y<=70;++y){if(y>=16 && y<=42)continue;for(int x=0;x<W;++x)if(g.readPixel(x,y))
      for(int dy=-3;dy<=3;++dy)for(int dx=-3;dx<=3;++dx)block(x+dx,y+dy);}
    const float t=elapsed*.001f;
    using Appearance::Effect;
    if(effect==Effect::Orbit){
      constexpr float p=2*(114+34)+10*3.14159265f;float distance=0,fade=1;
      if(t<.12f)fade=ease(t/.12f);
      else if(t<.72f)distance=p*(t-.12f)/.60f;
      else if(t<.84f)distance=p+9*ease((t-.72f)/.12f);
      else {fade=1-ease((t-.84f)/.12f);for(int x:{5,129})for(int y:{5,49}){const int sx=x==5?1:-1,sy=y==5?1:-1;line(g,x,y+sy*2,x,y,dim(color,.7f*fade));line(g,x,y,x+sx*2,y,dim(color,.7f*fade));}return;}
      int x,y;orbitPoint(distance,x,y);rect(g,x,y,2,2,dim(color,fade));
      const int lag[]={2,5,9};const float f[]={.7f,.43f,.23f};
      for(unsigned i=0;i<3;++i){orbitPoint(distance-lag[i],x,y);rect(g,x,y,1,1,dim(color,f[i]*fade));}
    } else if(effect==Effect::Flames){
      const int sites[]={28,38,98,108};
      for(unsigned i=0;i<4;++i){const float birth=(i==0 || i==3)?.075f:0;if(t<birth)continue;const float age=t-birth;
        const int h=lroundf(age<.18f?12*ease(age/.18f):age<.34f?12:age<.52f?9:9*(1-ease((age-.52f)/(.9f-birth-.52f))));if(h<1)continue;
        const int x=sites[i];const uint16_t outer=dim(color,.75f);
        for(int dy=0;dy<=h;++dy){const int half=dy<h/3?2:dy<2*h/3?1:0;for(int dx=-half;dx<=half;++dx)pixel(g,x+dx,62-dy,outer);}
        line(g,x,62,x,62-std::max(1,h/2),color);
      }
    } else if(effect==Effect::Sparkles){
      const int sites[][2]={{23,6},{111,49},{24,64},{113,6},{26,49},{111,64}};
      for(unsigned i=0;i<6;++i){const float age=t-i*.048f;if(age<0 || age>=.48f)continue;
        const int drift=int(2*age/.48f),x=sites[i][0]+(sites[i][0]<67?-drift:drift),y=sites[i][1];
        const int r=age<.08f?0:age<.20f?1:age<.33f?2:age<.40f?1:0;
        const uint16_t c=dim(color,age<.33f?1:age<.4f?.65f:.32f);
        line(g,x-r,y,x+r,y,c);if(r)line(g,x,y-r,x,y+r,c);
      }
    } else if(effect==Effect::Shockwave){
      for(unsigned i=0;i<2;++i){const float age=t-i*.11f;if(age<0 || age>=.61f)continue;
        const float p=age/.61f,scale=.65f+.50f*ease(p);const uint16_t c=dim(color,(p<.4f?1:p<.72f?.65f:.32f)*(i?.45f:1));
        int px=lroundf(66.5f+61.5f*scale),py=27;
        // 96 fixed segments, <=2 pixel thickness; clipping never touches UI.
        for(unsigned k=1;k<=96;++k){const float a=k*6.2831853f/96;const int x=lroundf(66.5f+61.5f*scale*std::cos(a)),y=lroundf(26.5f+24*scale*std::sin(a));
          line(g,px,py,x,y,c);if(!i && p<.4f)line(g,px,py+1,x,y+1,c);px=x;py=y;}
      }
    } else if(effect==Effect::Crown){
      if(t<.16f){const int half=lroundf(4*ease(t/.16f));line(g,26-half,9,26+half,9,color);}
      else {const float rise=t<.38f?ease((t-.16f)/.22f):t<.7f?1:1-ease((t-.7f)/.35f);
        const float center=t<.38f?ease((t-.25f)/.13f):rise;
        const int points[][2]={{22,9},{19,int(lroundf(9-5*rise))},{23,int(lroundf(9-3*rise))},{26,int(lroundf(9-6*center))},{29,int(lroundf(9-3*rise))},{33,int(lroundf(9-5*rise))},{30,9},{22,9}};
        for(unsigned i=1;i<8;++i)line(g,points[i-1][0],points[i-1][1],points[i][0],points[i][1],color);
        if(t>=.38f && t<.7f)rect(g,26,7,2,1,dim(color,.55f));
      }
    }
  }
};
}
