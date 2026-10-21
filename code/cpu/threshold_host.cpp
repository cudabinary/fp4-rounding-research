#include <cstdint>
#include <cstring>
#include <cstdio>
#include <vector>
#include <algorithm>
#include <chrono>
#include <cfenv>
#define __device__
#define __global__
#define __forceinline__ inline
inline unsigned int __float_as_uint(float f){unsigned int u;std::memcpy(&u,&f,4);return u;}
inline float __uint_as_float(unsigned int u){float f;std::memcpy(&f,&u,4);return f;}
inline int __clz(unsigned int a){return __builtin_clz(a);}
inline float __fadd_rn(float a,float b){volatile float c=a+b;return c;}
struct CpuDim{int x;} blockIdx{0},threadIdx{0},blockDim{0};
using u32=unsigned int;using u64=unsigned long long;
#include "exact_fp4_threshold.cuh"
#include "legacy_reference.hpp"
#include "decode_add.cu"
using U64=unsigned long long;
inline U64 naive_fp32(float x,float scale,unsigned int &code){
  unsigned int xb=__float_as_uint(x);volatile float quotient=__uint_as_float(xb&0x7fffffffu)/scale;float z=std::min(float(quotient),6.f);const float g[8]={0,.5,1,1.5,2,3,4,6};int hi=1;while(hi<7 && z>=g[hi])++hi;int lo=hi-1;volatile float p=(z-g[lo])/(g[hi]-g[lo]);code=unsigned(lo)|((xb>>28)&8u);return U64(p*4294967296.f);
}
int main(){
  std::fesetround(FE_TONEAREST);unsigned int mode,n;
  while(std::fread(&mode,4,1,stdin)==1 && std::fread(&n,4,1,stdin)==1){
    if(!n)return 2;std::vector<float>x(n),s(mode==0?n/32:n);std::vector<unsigned int>words(n);std::vector<unsigned short>r(n),out(n);std::vector<unsigned char>base(n),packed(n/2);std::vector<U64>T(n);U64 stats[16]={};
    if(mode==0){
      if(n%32)return 3;std::vector<unsigned short>yb(n);if(std::fread(yb.data(),2,n,stdin)!=n || std::fread(r.data(),2,n,stdin)!=n || std::fread(words.data(),4,n,stdin)!=n)return 4;
      for(unsigned int i=0;i<n;i++)x[i]=__uint_as_float(unsigned(yb[i])<<16);
      for(unsigned int g=0;g<n/32;g++){unsigned int mag=0;for(int j=0;j<32;j++)mag=std::max(mag,__float_as_uint(x[g*32+j])&0x7fffffffu);volatile float v=mag?__uint_as_float(mag)/6.f:__uint_as_float(85u<<23);s[g]=v;}
    }else{
      if(std::fread(x.data(),4,n,stdin)!=n || std::fread(s.data(),4,n,stdin)!=n || std::fread(words.data(),4,n,stdin)!=n)return 5;
    }
    for(unsigned int i=0;i<n;i++){
      float scale=s[mode==0?i/32:i];unsigned int xb=__float_as_uint(x[i])&0x7fffffffu,sb=__float_as_uint(scale);if(xb>=0x7f800000u || !sb || sb>=0x7f800000u)return 6;
      unsigned int a,b,c,db,carry=0;U64 tr=legacy_reference(x[i],scale,0,a);T[i]=fp4_threshold_integer_rn64(x[i],scale,b,&carry);U64 restoring=fp4_threshold_restoring_rn64(x[i],scale,db);U64 tf=naive_fp32(x[i],scale,c);base[i]=b;
      stats[0]+=(T[i]!=tr)+(restoring!=tr);stats[1]+=(a!=b)+(a!=db);stats[2]+=tf!=tr;stats[3]+=a!=c;stats[4]+=(U64(words[i])<tf)!=(U64(words[i])<tr);stats[5]+=carry;
      if(stats[6]==0 && (tf!=tr || carry)){stats[6]=1;stats[7]=__float_as_uint(x[i]);stats[8]=sb;stats[9]=tr;stats[10]=T[i];stats[11]=tf;stats[12]=carry;stats[13]=a;stats[14]=b;stats[15]=words[i];}
      if(mode==0){unsigned char code=static_cast<unsigned char>(b+unsigned(U64(words[i])<T[i]));if(!(i&1))packed[i/2]=code;else packed[i/2]|=code<<4;}
    }
    if(mode==0){blockIdx.x=0;blockDim.x=n;for(unsigned int i=0;i<n;i++){threadIdx.x=i;decode_add_bf16(packed.data(),s.data(),r.data(),out.data(),n);}}
    std::fwrite(stats,8,16,stdout);if(mode==0)std::fwrite(s.data(),4,n/32,stdout);std::fwrite(T.data(),8,n,stdout);std::fwrite(base.data(),1,n,stdout);if(mode==0){std::fwrite(packed.data(),1,n/2,stdout);std::fwrite(out.data(),2,n,stdout);}std::fflush(stdout);
  }
  return std::ferror(stdin)?7:0;
}
