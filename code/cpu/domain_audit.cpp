
#include <algorithm>
#include <array>
#include <cfenv>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <xmmintrin.h>
using u32=unsigned int;using u64=unsigned long long;using U128=__uint128_t;
u32 __float_as_uint(float x){u32 b;std::memcpy(&b,&x,4);return b;}
float __uint_as_float(u32 b){float x;std::memcpy(&x,&b,4);return x;}
int cpu_clz(u32 x){return __builtin_clz(x);}
// Integer-only replacement for the legacy binary64 FP4 threshold, under finite
// x / positive finite F32 scale preconditions. No floating-point arithmetic.
// RN64 names the legacy division's rounding semantics, not an FP64 instruction.
inline void fp4_unpack_positive(unsigned int bits,int &e,unsigned int &m){
  unsigned int exponent=bits>>23;
  if(exponent){e=int(exponent)-127;m=(bits&0x7fffffu)|0x800000u;}
  else {int h=31-cpu_clz(bits);e=h-149;m=bits<<(23-h);}
}
template<bool Restoring>
inline unsigned long long fp4_threshold_core_rn64(
    float x,float scale,unsigned int &code,unsigned int *carry_out=nullptr){
  using U64=unsigned long long;
  unsigned int xb=__float_as_uint(x),mag=xb&0x7fffffffu,sign=(xb>>28)&8u;
  if(carry_out)*carry_out=0;
  if(!mag){code=sign;return 0;}
  int ae,se;unsigned int am,sm;fp4_unpack_positive(mag,ae,am);fp4_unpack_positive(__float_as_uint(scale),se,sm);
  int d=ae-se;
  if(d>=4){code=6u|sign;return 1ull<<32;}
  if(d<-33){code=sign;return 0;}
  int lower=0;
  if(d>=-1){
    U64 twice=U64(am)<<(d+1),D=sm;
    if(twice>=12*D){code=6u|sign;return 1ull<<32;}
    lower=twice<D?0:twice<2*D?1:twice<3*D?2:twice<4*D?3:twice<6*D?4:twice<8*D?5:6;
  }
  code=unsigned(lower)|sign;
  int S=lower<4?33:lower<6?32:31;int k=d+S;
  U64 numerator=U64(am)<<k;
  // All power-of-two scales, including subnormals, avoid integer division.
  const unsigned int L2[7]={0,1,2,3,4,6,8};
  U64 lower_scaled=U64(L2[lower])<<(S-1),t;unsigned int rem;
  if(sm==0x800000u){t=(numerator>>23)-lower_scaled;rem=unsigned(numerator&0x7fffffu);}
  else if constexpr(Restoring){
    U64 rest=numerator-lower_scaled*sm;t=0;
    // 0<=rest/sm<2^32. Fixed32 branchless compare/subtract steps; no divide.
    #pragma unroll
    for(int bit=31;bit>=0;--bit){U64 shifted=U64(sm)<<bit;U64 take=U64(rest>=shifted);rest-=shifted&(0ull-take);t|=take<<bit;}
    rem=unsigned(rest);
  }else{U64 q=numerator/U64(sm);rem=unsigned(numerator-q*sm);t=q-lower_scaled;}
  int exponent=d-int(am<sm),J=53-exponent-S;
  // The next 2^-S grid point has an even binary64 significand. Equality
  // therefore rounds upward too. J uses the exponent below the boundary.
  if(rem && J<24 && (U64(sm-rem)<<J)<=sm){++t;if(carry_out)*carry_out=1;}
  return t;
}
inline unsigned long long fp4_threshold_integer_rn64(float x,float scale,unsigned int &code,unsigned int *carry=nullptr){return fp4_threshold_core_rn64<false>(x,scale,code,carry);}
inline unsigned long long fp4_threshold_restoring_rn64(float x,float scale,unsigned int &code,unsigned int *carry=nullptr){return fp4_threshold_core_rn64<true>(x,scale,code,carry);}


template<bool Restoring>
inline unsigned long long fp4_threshold_core_no_correction(
    float x,float scale,unsigned int &code,unsigned int *carry_out=nullptr){
  using U64=unsigned long long;
  unsigned int xb=__float_as_uint(x),mag=xb&0x7fffffffu,sign=(xb>>28)&8u;
  if(carry_out)*carry_out=0;
  if(!mag){code=sign;return 0;}
  int ae,se;unsigned int am,sm;fp4_unpack_positive(mag,ae,am);fp4_unpack_positive(__float_as_uint(scale),se,sm);
  int d=ae-se;
  if(d>=4){code=6u|sign;return 1ull<<32;}
  if(d<-33){code=sign;return 0;}
  int lower=0;
  if(d>=-1){
    U64 twice=U64(am)<<(d+1),D=sm;
    if(twice>=12*D){code=6u|sign;return 1ull<<32;}
    lower=twice<D?0:twice<2*D?1:twice<3*D?2:twice<4*D?3:twice<6*D?4:twice<8*D?5:6;
  }
  code=unsigned(lower)|sign;
  int S=lower<4?33:lower<6?32:31;int k=d+S;
  U64 numerator=U64(am)<<k;
  // All power-of-two scales, including subnormals, avoid integer division.
  const unsigned int L2[7]={0,1,2,3,4,6,8};
  U64 lower_scaled=U64(L2[lower])<<(S-1),t;unsigned int rem;
  if(sm==0x800000u){t=(numerator>>23)-lower_scaled;rem=unsigned(numerator&0x7fffffu);}
  else if constexpr(Restoring){
    U64 rest=numerator-lower_scaled*sm;t=0;
    // 0<=rest/sm<2^32. Fixed32 branchless compare/subtract steps; no divide.
    #pragma unroll
    for(int bit=31;bit>=0;--bit){U64 shifted=U64(sm)<<bit;U64 take=U64(rest>=shifted);rest-=shifted&(0ull-take);t|=take<<bit;}
    rem=unsigned(rest);
  }else{U64 q=numerator/U64(sm);rem=unsigned(numerator-q*sm);t=q-lower_scaled;}
  int exponent=d-int(am<sm),J=53-exponent-S;
  // The next 2^-S grid point has an even binary64 significand. Equality
  // therefore rounds upward too. J uses the exponent below the boundary.
  if(carry_out)*carry_out=unsigned(rem && J<24); // diagnostic eligibility only; never increments T
  return t;
}

inline u64 threshold_value(float x,float scale,int format,u32 &code) {
  u32 bits=__float_as_uint(x),mag=bits&0x7fffffffu;
  if(format==1){code=(bits>>16);return u64(mag&65535u)<<16;}
  double z=double(__uint_as_float(mag))/double(scale);if(z>6.0)z=6.0;
  // Explicit form of A's six ordered comparisons; carry the selected endpoints.
  int upper=1;double grid_lower=0.0,grid_upper=0.5;
  if(z>=0.5){upper=2;grid_lower=0.5;grid_upper=1.0;
    if(z>=1.0){upper=3;grid_lower=1.0;grid_upper=1.5;
      if(z>=1.5){upper=4;grid_lower=1.5;grid_upper=2.0;
        if(z>=2.0){upper=5;grid_lower=2.0;grid_upper=3.0;
          if(z>=3.0){upper=6;grid_lower=3.0;grid_upper=4.0;
            if(z>=4.0){upper=7;grid_lower=4.0;grid_upper=6.0;}
          }
        }
      }
    }
  }
  int lower=upper-1;double p=(z-grid_lower)/(grid_upper-grid_lower);
  code=u32(lower)|((bits>>28)&8u);return u64(p*4294967296.0);
}

// Independent integer oracle: decode exact F32 fractions, round the ratio to
// 53 significant bits with ties-to-even, then evaluate dyadic interval threshold.
u64 oracle(u32 xb,u32 sb,u32 &base){
 xb&=0x7fffffffu;if(!xb){base=0;return 0;}
 int ex=xb>>23,es=sb>>23;
 u32 mx=ex?((xb&0x7fffff)|0x800000):(xb&0x7fffff);
 u32 ms=es?((sb&0x7fffff)|0x800000):(sb&0x7fffff);
 int delta=(ex?ex-150:-149)-(es?es-150:-149);
 int lx=31-cpu_clz(mx),ls=31-cpu_clz(ms);
 int E=delta+lx-ls;
 if((u64(mx)<<ls)<(u64(ms)<<lx))--E;
 int shift=delta-E+52;
 if(shift<0||shift>100)throw std::runtime_error("oracle shift");
 U128 n=U128(mx)<<shift;u64 M=u64(n/ms);u32 rem=u32(n%ms);
 if(u64(rem)*2>ms||(u64(rem)*2==ms&&(M&1)))++M;
 if(M==(1ull<<53)){M>>=1;++E;}
 u64 bits=(u64(E+1023)<<52)|(M-(1ull<<52));
 if(bits>0x4018000000000000ull){bits=0x4018000000000000ull;E=2;M=3ull<<51;}
 const u64 cuts[6]={0x3fe0000000000000ull,0x3ff0000000000000ull,0x3ff8000000000000ull,0x4000000000000000ull,0x4008000000000000ull,0x4010000000000000ull};
 base=0;for(auto c:cuts)base+=bits>=c;
 int S=base<4?33:base<6?32:31,J=52-E-S;
 if(J<0)throw std::runtime_error("negative threshold shift");
 const u32 L2[7]={0,1,2,3,4,6,8};
 return (J>=64?0:(M>>J))-(u64(L2[base])<<(S-1));
}
struct Acc {u64 pairs=0,guard=0,carry=0,badD1=0,badB=0,badOracle=0;};
struct Witness {u32 a,x,s,base;u64 A,B,D,O;};
std::vector<Witness>witnesses;
Acc all;
std::vector<u32>scales(32640);
std::chrono::steady_clock::time_point start;
bool inspect(u32 a,u32 x,Acc &row){
 float s=__uint_as_float(scales[a]),v=__uint_as_float(x<<16);
 u32 ca=0,cb=0,cd=0,co=0,carry=0,guard=0;
 u64 ta=threshold_value(v,s,0,ca);
 u64 tb=fp4_threshold_integer_rn64(v,s,cb,&carry);
 u64 td=fp4_threshold_core_no_correction<false>(v,s,cd,&guard);
 u64 to=oracle(x<<16,scales[a],co);
 ++row.pairs;row.guard+=guard;row.carry+=carry;
 row.badB+=(ta!=tb||ca!=cb);row.badOracle+=(ta!=to||ca!=co);row.badD1+=(ta!=td||ca!=cd);
 if((ta!=td||ca!=cd)&&witnesses.size()<32)witnesses.push_back({a,x,scales[a],ca,ta,tb,td,to});
 if(ta!=tb||ca!=cb||ta!=to||ca!=co){
  std::cerr<<"BASELINE_OR_ORACLE_FAILURE a="<<a<<" x="<<x<<" A="<<ta<<" B="<<tb<<" O="<<to<<std::endl;return false;
 }
 return true;
}
void accumulate(const Acc&r){all.pairs+=r.pairs;all.guard+=r.guard;all.carry+=r.carry;all.badD1+=r.badD1;all.badB+=r.badB;all.badOracle+=r.badOracle;}
std::string report(bool smoke,bool complete,double elapsed){
 std::ostringstream o;o<<std::setprecision(17);
 o<<"{\"mode\":\""<<(smoke?"SMOKE":"MAIN")<<"\",\"complete\":"<<(complete?"true":"false")
 <<",\"pairs\":"<<all.pairs<<",\"generic_guard_eligible\":"<<all.guard<<",\"RN64_carry\":"<<all.carry
 <<",\"D1_disagreements\":"<<all.badD1<<",\"B_disagreements\":"<<all.badB<<",\"oracle_disagreements\":"<<all.badOracle
 <<",\"CPU_wall_seconds\":"<<elapsed<<",\"MXCSR\":"<<_mm_getcsr()<<",\"FE_TONEAREST\":"<<(std::fegetround()==FE_TONEAREST?"true":"false")
 <<",\"witnesses\":[";
 for(size_t i=0;i<witnesses.size();++i){auto w=witnesses[i];if(i)o<<",";
 o<<"{\"amax_bf16\":"<<w.a<<",\"x_bf16\":"<<w.x<<",\"scale_f32\":"<<w.s<<",\"base\":"<<w.base<<",\"A_T\":"<<w.A<<",\"B_T\":"<<w.B<<",\"D1_T\":"<<w.D<<",\"oracle_T\":"<<w.O<<"}";}
 o<<"]}";return o.str();
}
int main(int argc,char**argv){
 try{
  bool smoke=argc>1&&std::string(argv[1])=="smoke";
  if(std::fegetround()!=FE_TONEAREST||(_mm_getcsr()&0x8040))throw std::runtime_error("non-RNE or FTZ/DAZ");
  std::ifstream in("SCALE_BITS.bin",std::ios::binary);in.read(reinterpret_cast<char*>(scales.data()),scales.size()*4);
  if(!in||!in.eof()&&in.peek()!=EOF)throw std::runtime_error("scale manifest file");
  // Prior arbitrary-F32 witness is intentionally outside the producer domain.
  u32 ca,cb,cd,co,carry=0;float x=__uint_as_float(1073733634u),s=__uint_as_float(1065353217u);
  auto ta=threshold_value(x,s,0,ca),tb=fp4_threshold_integer_rn64(x,s,cb,&carry);
  auto td=fp4_threshold_core_no_correction<false>(x,s,cd);
  auto to=oracle(1073733634u,1065353217u,co);
  if(ta!=4286578689ull||tb!=ta||to!=ta||td!=4286578688ull||!carry)throw std::runtime_error("old witness cross-check");
  if(smoke){
   // Fixed signed corners test sign separation only, not another input search.
   for(u32 xb:{0u,0x80000000u,0x10000u,0x80010000u,0x3f800000u,0xbf800000u,0x7f7f0000u,0xff7f0000u}){
    u32 p,n;float v=__uint_as_float(xb);u64 t=threshold_value(v,1.f,0,p),u=threshold_value(__uint_as_float(xb&0x7fffffff),1.f,0,n);
    if(t!=u||p!=(n|((xb>>28)&8)))throw std::runtime_error("signed smoke");
   }
  }
  std::ofstream csv(smoke?"SMOKE_PER_AMAX.csv":"MAIN_PER_AMAX.csv");
  csv<<"amax_bf16,scale_f32,pairs,generic_guard_eligible,RN64_carry,D1_disagreements,B_disagreements,oracle_disagreements\n";
  std::vector<u32>amax;
  if(smoke)amax={1,127,128,447,448,16256,32639};
  else for(u32 a=1;a<=32639;++a)amax.push_back(a);
  start=std::chrono::steady_clock::now();bool complete=true;
  Acc zero;if(!inspect(0,0,zero))return 3;accumulate(zero);
  for(u32 a:amax){
   // Check compiled source's precise F32 scale against independent Fraction RNE.
   volatile float av=__uint_as_float(a<<16);float scale=av/6.f;
   if(__float_as_uint(scale)!=scales[a])throw std::runtime_error("scale CPU oracle disagreement");
   Acc row;
   for(u32 v=0;v<=a;++v)if(!inspect(a,v,row)){complete=false;break;}
   accumulate(row);
   csv<<a<<','<<scales[a]<<','<<row.pairs<<','<<row.guard<<','<<row.carry<<','<<row.badD1<<','<<row.badB<<','<<row.badOracle<<'\n';
   if(!complete)break;
   double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
   if(elapsed>1700){complete=false;break;}
   if(!smoke&&a%4096==0)std::cerr<<"PROGRESS amax="<<a<<" pairs="<<all.pairs<<" seconds="<<elapsed<<std::endl;
  }
  double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  auto result=report(smoke,complete,elapsed);std::ofstream out(smoke?"SMOKE_RESULT.json":"MAIN_RESULT.json");out<<result<<'\n';std::cout<<result<<std::endl;
  return complete&&all.badB==0&&all.badOracle==0?0:4;
 }catch(const std::exception&e){std::cerr<<"ERROR_NO_RETRY "<<e.what()<<std::endl;return 2;}
}
