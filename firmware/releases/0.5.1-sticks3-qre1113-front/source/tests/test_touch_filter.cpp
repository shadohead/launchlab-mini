#include "../LaunchLabRpm/touch_filter.h"
#include <cassert>
#include <iostream>
static constexpr int64_t POLL_US=30000;
int main() {
  // Idle busy window: no errors, no phantom press.
  {
    TouchFilter f;int64_t t=0;
    assert(!f.read(false,0,0).pressed);
    for(int i=0;i<5;i++)assert(!f.failed(t+=POLL_US).pressed);
    assert(!f.read(false,0,0).pressed);
    assert(f.errors==0&&f.busyWindows==1&&f.presses==0);
  }
  // Busy window during a held press: the press continues at its last point
  // instead of a release and a second press.
  {
    TouchFilter f;int64_t t=0;
    auto p=f.read(true,120,200);assert(p.pressed&&p.x==120&&p.y==200);
    for(int i=0;i<4;i++){p=f.failed(t+=POLL_US);assert(p.pressed&&p.x==120&&p.y==200);}
    p=f.read(true,125,210);assert(p.pressed&&p.x==125&&p.y==210);
    assert(f.presses==1&&f.errors==0&&f.busyWindows==1);
    p=f.read(false,0,0);assert(!p.pressed);
    f.read(true,10,10);assert(f.presses==2);
  }
  // A silent controller releases the press once the grace expires and counts
  // one error per outage, however long it lasts.
  {
    TouchFilter f;int64_t t=0;
    f.read(true,50,60);
    const int64_t first=t+=POLL_US;
    assert(f.failed(first).pressed);
    assert(f.failed(first+TouchFilter::GRACE_US-1).pressed);
    assert(!f.failed(first+TouchFilter::GRACE_US).pressed);
    for(int i=0;i<100;i++)assert(!f.failed(first+TouchFilter::GRACE_US+i*POLL_US).pressed);
    assert(f.errors==1&&f.busyWindows==0);
    f.read(false,0,0);
    assert(f.errors==1&&f.busyWindows==0);
    // A later outage is a new one.
    f.failed(10000000);f.failed(10000000+TouchFilter::GRACE_US);
    assert(f.errors==2);
    f.read(false,0,0);
    // And a later short window is a busy window again.
    f.failed(20000000);f.read(false,0,0);
    assert(f.errors==2&&f.busyWindows==1);
  }
  std::cout<<"touch filter tests passed\n";
}
