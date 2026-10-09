#pragma once
#include <Preferences.h>
#include "practice_history.h"

// Alternating, versioned snapshots. Never erase the namespace on a read error.
// save() is called only after the ADC owner acknowledges a guarded checkpoint.
class PracticeStore {
public:
  bool begin(PracticeHistory &history,const char *name="ll-practice") {
    ready_=prefs_.begin(name,false);
    if(!ready_)return false;
    bool found=false,present=false;
    auto candidate=std::unique_ptr<PracticeHistory>(new(std::nothrow) PracticeHistory);
    if(!candidate){ready_=false;return false;}
    for(unsigned slot=0;slot<2;++slot) {
      const char *key=slot?"history1":"history0";
      const size_t n=prefs_.getBytesLength(key);present|=n!=0 || prefs_.isKey(key);
      if(n!=image_.size() || prefs_.getBytes(key,image_.data(),image_.size())!=image_.size() ||
         !candidate->decode(image_.data(),image_.size()))continue;
      if(!found || int32_t(candidate->generation()-history.generation())>0) {
        history=*candidate;slot_=slot;found=true;
      }
    }
    if(present && !found){ready_=false;return false;}
    savedGeneration_=history.generation();return true;
  }
  bool save(const PracticeHistory &history) {
    if(!ready_)return false;
    if(history.generation()==savedGeneration_)return true;
    const unsigned next=slot_^1u;const char *key=next?"history1":"history0";
    history.encode(image_);
    const uint32_t expected=PracticeHistory::checksum(image_.data(),image_.size());
    if(prefs_.putBytes(key,image_.data(),image_.size())!=image_.size())return false;
    // Read back and decode before treating the new generation as saved.
    auto readback=std::unique_ptr<PracticeHistory>(new(std::nothrow) PracticeHistory);
    if(!readback)return false;
    if(prefs_.getBytes(key,image_.data(),image_.size())!=image_.size() ||
       PracticeHistory::checksum(image_.data(),image_.size())!=expected ||
       !readback->decode(image_.data(),image_.size()) || readback->generation()!=history.generation())return false;
    slot_=next;savedGeneration_=history.generation();return true;
  }
  bool ready()const{return ready_;}
  bool pending(const PracticeHistory &history)const{return history.generation()!=savedGeneration_;}
  uint32_t pendingCount(const PracticeHistory &history)const{return history.generation()-savedGeneration_;}
private:
  Preferences prefs_;
  PracticeHistory::Image image_{};
  uint32_t savedGeneration_=0;
  unsigned slot_=0;
  bool ready_=false;
};
