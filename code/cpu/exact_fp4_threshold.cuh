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
