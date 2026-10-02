#include "../LaunchLabRpm/launch_history.h"
#include <cassert>
#include <iostream>
int main() {
  LaunchHistory history;
  assert(!history.recent() && history.size()==0);
  for(unsigned i=1;i<=27;i++){LaunchRecord r;r.number=i;r.rpm=100*i;history.add(r);}
  assert(history.size()==20 && history.recent()->number==27 && history.recent(19)->number==8 && !history.recent(20));
  assert(history.recent(5)->rpm==2200);
  LaunchRecord copy=*history.recent(19),next;next.number=28;history.add(next);
  assert(copy.number==8 && history.recent()->number==28 && history.recent(19)->number==9);
  std::cout<<"PASS: bounded newest-first history, ring wrap and independent record copy\n";
}
