#include "../LaunchLabMini/practice_store.h"
#include <cassert>
#include <iostream>
int main() {
  PracticeHistory h;PracticeStore store;assert(store.begin(h) && !store.pending(h));
  h.accept(1,true,4000,100);assert(store.pending(h) && store.save(h) && !store.pending(h));
  h.accept(2,true,8000,30100);assert(store.save(h));
  PracticeHistory loaded;PracticeStore reboot;
  assert(reboot.begin(loaded) && loaded.size()==2 && loaded.session()->mean()==6000);
  // Latest slot damaged: load earlier complete snapshot without erasing bytes.
  Preferences::data["ll-practicehistory0"][100]^=1;
  PracticeHistory fallback;PracticeStore recovery;
  assert(recovery.begin(fallback) && fallback.size()==1 && fallback.recent()->rpm==4000);
  fallback.accept(1,true,9000,100);
  Preferences::failWrite=true;assert(!recovery.save(fallback) && recovery.pending(fallback));
  Preferences::failWrite=false;assert(recovery.save(fallback) && !recovery.pending(fallback));
  PracticeHistory durable;PracticeStore reread;assert(reread.begin(durable) && durable.size()==2 && durable.recent()->rpm==9000);
  PracticeHistory scratch;PracticeStore isolated;assert(isolated.begin(scratch,"ll-prac-qa"));
  scratch.accept(1,true,16000,100);assert(isolated.save(scratch));
  PracticeHistory real;PracticeStore realStore;assert(realStore.begin(real) && real.recent()->rpm==9000);
  durable.accept(1,true,10000,100);Preferences::shortRead=true;
  assert(!reread.save(durable) && reread.pending(durable));Preferences::shortRead=false;
  const auto before=Preferences::data;
  for(auto &entry:Preferences::data)if(entry.first.find("ll-practice")==0)entry.second[0]^=1;
  const auto damaged=Preferences::data;
  PracticeHistory empty;PracticeStore broken;assert(!broken.begin(empty));
  assert(Preferences::data==damaged && !broken.ready());
  std::cout<<"PASS: alternating snapshots, exact save/readback, reboot selection, damaged newest fallback, failed write/read retention and no destructive corruption recovery\n";
}
