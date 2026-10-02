#pragma once
#include <string>
#include <map>
#include <vector>
#include <cstring>
class Preferences {
public:
  static inline std::map<std::string,std::vector<unsigned char>> data;
  static inline bool failWrite=false,shortRead=false;
  std::string space;
  bool begin(const char *s,bool){space=s;return true;}
  size_t getBytesLength(const char *key){auto i=data.find(space+key);return i==data.end()?0:i->second.size();}
  size_t getBytes(const char *key,void *out,size_t size) {
    auto i=data.find(space+key);if(i==data.end())return 0;
    const size_t n=std::min(size,i->second.size());std::memcpy(out,i->second.data(),n);return shortRead?n-1:n;
  }
  size_t putBytes(const char *key,const void *bytes,size_t n) {
    if(failWrite)return 0;
    const auto *p=static_cast<const unsigned char *>(bytes);data[space+key]={p,p+n};return n;
  }
};
