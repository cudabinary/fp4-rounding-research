// Integer-only replacement for the legacy binary64 FP4 threshold, under finite
// x / positive finite F32 scale preconditions. No floating-point arithmetic.
// RN64 names the legacy division's rounding semantics, not an FP64 instruction.
__device__ __forceinline__ void fp4_unpack_positive(unsigned int bits,int &e,unsigned int &m){
  unsigned int exponent=bits>>23;
  if(exponent){e=int(exponent)-127;m=(bits&0x7fffffu)|0x800000u;}
  else {int h=31-__clz(bits);e=h-149;m=bits<<(23-h);}
}
template<bool Restoring>
__device__ __forceinline__ unsigned long long fp4_threshold_core_rn64(
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
__device__ __forceinline__ unsigned long long fp4_threshold_integer_rn64(float x,float scale,unsigned int &code,unsigned int *carry=nullptr){return fp4_threshold_core_rn64<false>(x,scale,code,carry);}
__device__ __forceinline__ unsigned long long fp4_threshold_restoring_rn64(float x,float scale,unsigned int &code,unsigned int *carry=nullptr){return fp4_threshold_core_rn64<true>(x,scale,code,carry);}

__device__ __forceinline__ float amax6_scale_from_mag(unsigned int mag){
  return mag?__fdiv_rn(__uint_as_float(mag),6.f):__uint_as_float(85u<<23);
}
#define INPUT_BF16 true
// EO026: executable EO025 contract. No cuRAND or external device headers.
typedef unsigned int u32;
typedef unsigned long long u64;
typedef unsigned char u8;
__device__ __forceinline__ uint4 philox(uint4 c, uint2 k) {
  #pragma unroll
  for(int r=0;r<10;r++) {
    u64 a=u64(0xD2511F53u)*c.x,b=u64(0xCD9E8D57u)*c.z;
    c=make_uint4(u32(b>>32)^c.y^k.x,u32(b),u32(a>>32)^c.w^k.y,u32(a));
    if(r!=9){k.x+=0x9E3779B9u;k.y+=0xBB67AE85u;}
  }
  return c;
}
__device__ __forceinline__ uint4 packet(u32 group,int plane,u64 seed,u32 epoch) {
  return philox(make_uint4(5,epoch,(5u<<24)|(5u<<21)|group,u32(plane)),make_uint2(u32(seed),u32(seed>>32)));
}
__device__ __forceinline__ u32 comp(uint4 p,int lane){return lane==0?p.x:lane==1?p.y:lane==2?p.z:p.w;}
__device__ __forceinline__ u32 nibble(u32 x,int lane){return __brev((x>>(4*(lane&7)))&15u)>>28;}
__device__ __forceinline__ int precision(u64 t){return t==0 || t==(1ull<<32)?0:33-__ffs(u32(t));}
__device__ __forceinline__ bool finish(u64 prefix,int bits,u64 t,bool &answer){
  u64 lo=prefix<<(32-bits),hi=(prefix+1)<<(32-bits);
  if(hi<=t){answer=true;return true;}if(lo>=t){answer=false;return true;}return false;
}



// Ordinary software fusion. The input is the actual GEMM output tensor.
// BF16 expansion preserves the exact float value; no intermediate tensor.
__device__ __forceinline__ float input_value(const float* p,int i){
  if constexpr(INPUT_BF16)return __uint_as_float(u32(((const unsigned short*)p)[i])<<16);
  else return p[i];
}

__device__ __forceinline__ float cohort_scale(float x){
  u32 mag=__float_as_uint(x)&0x7fffffffu;
  return amax6_scale_from_mag(__reduce_max_sync(0xffffffffu,mag));
}

__device__ __forceinline__ u64 threshold_value(float x,float scale,int format,u32 &code) {
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
template<int Format> __device__ __forceinline__ void write_value(int i,int n,u32 base,bool answer,void* result) {
  u32 code=i<n?base+u32(answer):0;
  if constexpr(Format==1){if(i<n)((unsigned short*)result)[i]=(unsigned short)code;}
  else {u32 next=__shfl_down_sync(0xffffffffu,code,1);if(i<n && !(i&1))((u8*)result)[i>>1]=u8(code|(next<<4));}
}

// Four consumer cohorts per warp; one Philox execution per canonical packet.
// Prefix-scan of 32 cohort requests packs producers across a 1024-event CTA.
// All 256 CTA threads participate in every barrier, including tail events.
template<int Window,bool Adaptive,bool Diagnostic,int Format>
__device__ void packed(const u64* thresholds,const u32* groups,u8* mask,u32* raw,
                      u32* counts,int n,u64 seed,u32 epoch,u64 scalar_t,int kind,const float* values,float* scales,void* result) {
  __shared__ u32 requests[32],offsets[33],scratch[32*Window*4];
  int tid=threadIdx.x,lane=tid&31,warp=tid>>5;
  u64 t[4],prefix[4]={0,0,0,0};bool done[4],answer[4];u32 code[4]={0,0,0,0};int cap[4],generated[4]={0,0,0,0};
  #pragma unroll
  for(int j=0;j<4;j++) {
    int i=blockIdx.x*1024+(warp*4+j)*32+lane;
    float v=i<n?input_value(values,i):0.0f;
    float local_scale=Format==1?1.0f:cohort_scale(v);
    if constexpr(Format==0){if(lane==0 && i<n)scales[i>>5]=local_scale;}
    t[j]=i<n?threshold_value(v,local_scale,Format,code[j]):0;
    answer[j]=t[j]==(1ull<<32);done[j]=kind?i>=n:(t[j]==0 || answer[j]);
    int b=kind?(i<n?(kind==1?23:32):0):precision(t[j]);
    cap[j]=(__reduce_max_sync(0xffffffffu,b)+3)/4;
  }
  for(int base=0;base<8;base+=Window) {
    #pragma unroll
    for(int j=0;j<4;j++) {
      int remain=cap[j]-base;
      int nr=remain>0?(remain<Window?remain:Window):0;
      if(Adaptive && !__any_sync(0xffffffffu,!done[j]))nr=0;
      if(lane==0)requests[warp*4+j]=nr;
    }
    __syncthreads();
    if(warp==0) {
      u32 x=requests[lane];
      #pragma unroll
      for(int d=1;d<32;d*=2){u32 v=__shfl_up_sync(0xffffffffu,x,d);if(lane>=d)x+=v;}
      offsets[lane+1]=x;if(lane==0)offsets[0]=0;
    }
    __syncthreads();
    u32 total=offsets[32];if(total==0)break;
    if(tid<int(total)) {
      int low=0,high=32;
      while(low+1<high){int mid=(low+high)/2;if(offsets[mid]<=u32(tid))low=mid;else high=mid;}
      int group_local=low,j=tid-offsets[low];
      int global_group=blockIdx.x*32+group_local;
      u32 gid=groups?groups[global_group]:u32(global_group);
      uint4 p=packet(gid,base+j,seed,epoch);
      u32* s=scratch+(group_local*Window+j)*4;s[0]=p.x;s[1]=p.y;s[2]=p.z;s[3]=p.w;
    }
    __syncthreads();
    #pragma unroll
    for(int j=0;j<4;j++) {
      int local_group=warp*4+j,nr=requests[local_group];generated[j]+=nr;
      if(!done[j]) {
        for(int q=0;q<nr;q++)prefix[j]=(prefix[j]<<4)|nibble(scratch[(local_group*Window+q)*4+(lane>>3)],lane);
        if(!kind && nr)done[j]=finish(prefix[j],(base+nr)*4,t[j],answer[j]);
      }
    }
    __syncthreads(); // all readers finish before counts/scratch are overwritten
  }
  #pragma unroll
  for(int j=0;j<4;j++) {
    int global_group=blockIdx.x*32+warp*4+j,i=global_group*32+lane;
    write_value<Format>(i,n,code[j],answer[j],result);if(i<n && mask)mask[i]=u8(answer[j]);
    if(Diagnostic && lane==0 && global_group*32<n)counts[global_group]=generated[j];
  }
}

// Warp-only alternative, no CTA barrier. A producer lane computes each packet;
// four shuffle transfers distribute all components to its 32 consumers.
template<int Window,bool Adaptive,bool Diagnostic,int Format>
__device__ void warp_impl(const u64* thresholds,const u32* groups,u8* mask,u32* raw,
                         u32* counts,int n,u64 seed,u32 epoch,u64 scalar_t,int kind,const float* values,float* scales,void* result) {
  int i=blockIdx.x*blockDim.x+threadIdx.x,lane=threadIdx.x&31;
  if((i&~31)>=n)return;
  float v=i<n?input_value(values,i):0.0f;
  float local_scale=Format==1?1.0f:cohort_scale(v);
  if constexpr(Format==0){if(lane==0 && i<n)scales[i>>5]=local_scale;}
  u32 code=0;u64 t=i<n?threshold_value(v,local_scale,Format,code):0,prefix=0;
  bool answer=t==(1ull<<32),done=kind?i>=n:(t==0 || answer);
  int b=kind?(i<n?(kind==1?23:32):0):precision(t);
  int cap=(__reduce_max_sync(0xffffffffu,b)+3)/4,generated=0;
  int gi=i>>5;u32 gid=groups?groups[gi]:u32(gi);
  for(int base=0;base<cap;base+=Window) {
    if(Adaptive && !__any_sync(0xffffffffu,!done))break;
    int nr=cap-base<Window?cap-base:Window;
    uint4 p=make_uint4(0,0,0,0);if(lane<nr)p=packet(gid,base+lane,seed,epoch);
    for(int j=0;j<nr;j++) {
      uint4 q=make_uint4(__shfl_sync(0xffffffffu,p.x,j),__shfl_sync(0xffffffffu,p.y,j),
                        __shfl_sync(0xffffffffu,p.z,j),__shfl_sync(0xffffffffu,p.w,j));
      if(!done)prefix=(prefix<<4)|nibble(comp(q,lane>>3),lane);
    }
    generated+=nr;
    if(!kind && !done)done=finish(prefix,(base+nr)*4,t,answer);
  }
  write_value<Format>(i,n,code,answer,result);if(i<n && mask)mask[i]=u8(answer);
  if(Diagnostic && lane==0)counts[gi]=generated;
}

#define CONVERT(NAME,IMPL,W,A,F) extern "C" __global__ void NAME(const float* x,float* scale,void* out,u8* mask,const u32* groups,int n,u64 seed,u32 epoch){IMPL<W,A,false,F>(nullptr,groups,mask,nullptr,nullptr,n,seed,epoch,0,0,x,scale,out);}
extern "C" __global__ void block_scale(const float* x,float* scale,int n){
  int i=blockIdx.x*blockDim.x+threadIdx.x;u32 mag=i<n?(__float_as_uint(x[i])&0x7fffffffu):0;
  mag=__reduce_max_sync(0xffffffffu,mag);if(!(threadIdx.x&31) && i<n){
    scale[i>>5]=amax6_scale_from_mag(mag);
  }
}
extern "C" __global__ void direct_bf16(const float* x,unsigned short* out,int n,u64 seed,u32 epoch){
  int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;u32 b=__float_as_uint(x[i]);
  uint4 p=philox(make_uint4(5,epoch,(6u<<24)|u32(i),0),make_uint2(u32(seed),u32(seed>>32)));
  out[i]=(unsigned short)((b>>16)+u32(p.x<((b&65535u)<<16)));
}
extern "C" __global__ void direct_fp4(const float* x,const float* scale,u8* out,int n,u64 seed,u32 epoch){
  int i=blockIdx.x*blockDim.x+threadIdx.x;if((i&~31)>=n)return;u32 code=0;u64 t=i<n?threshold_value(x[i],scale[i>>5],0,code):0;
  uint4 p=make_uint4(0,0,0,0);if(i<n && t>0 && t<(1ull<<32))p=philox(make_uint4(5,epoch,(6u<<24)|u32(i),0),make_uint2(u32(seed),u32(seed>>32)));
  write_value<0>(i,n,code,t==(1ull<<32) || (t>0 && u64(p.x)<t),out);
}
CONVERT(warp_eager_fp4,warp_impl,8,false,0)
CONVERT(warp_lazy1_fp4,warp_impl,1,true,0)
CONVERT(warp_look2_fp4,warp_impl,2,true,0)
CONVERT(warp_look4_fp4,warp_impl,4,true,0)
CONVERT(packed_eager_fp4,packed,8,false,0)
CONVERT(packed_lazy1_fp4,packed,1,true,0)
CONVERT(packed_look2_fp4,packed,2,true,0)
CONVERT(packed_look4_fp4,packed,4,true,0)
CONVERT(warp_eager_bf16,warp_impl,8,false,1)
CONVERT(warp_lazy1_bf16,warp_impl,1,true,1)
CONVERT(warp_look2_bf16,warp_impl,2,true,1)
CONVERT(warp_look4_bf16,warp_impl,4,true,1)
CONVERT(packed_eager_bf16,packed,8,false,1)
CONVERT(packed_lazy1_bf16,packed,1,true,1)
CONVERT(packed_look2_bf16,packed,2,true,1)
CONVERT(packed_look4_bf16,packed,4,true,1)

