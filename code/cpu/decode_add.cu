typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;
__device__ __forceinline__ float load_bf16(u16 x){return __uint_as_float(u32(x)<<16);}
__device__ __forceinline__ u16 rn_bf16(float x){
  u32 v=__float_as_uint(x);
  if((v&0x7fffffffu)>0x7f800000u)return u16((v>>16)|0x40u);
  return u16((v+0x7fffu+((v>>16)&1u))>>16);
}
extern "C" __global__ void decode_add_bf16(const u8* codes,const float* scales,const u16* residual,u16* out,int n){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;
 u32 c=(codes[i>>1]>>((i&1)*4))&15u;
 const float grid[8]={0.f,.5f,1.f,1.5f,2.f,3.f,4.f,6.f};
 float decoded=grid[c&7u]*scales[i>>5];
 if(c&8u)decoded=-decoded;
 float rounded=load_bf16(rn_bf16(decoded));
 out[i]=rn_bf16(__fadd_rn(load_bf16(residual[i]),rounded));
}
