__device__ __forceinline__ u64 legacy_reference(float x,float scale,int format,u32 &code) {
  u32 bits=__float_as_uint(x),mag=bits&0x7fffffffu;
  if(format==1){code=(bits>>16);return u64(mag&65535u)<<16;}
  double z=double(__uint_as_float(mag))/double(scale);if(z>6.0)z=6.0;
  const double grid[8]={0,.5,1,1.5,2,3,4,6};int upper=1;
  while(upper<7 && z>=grid[upper])upper++;
  int lower=upper-1;double p=(z-grid[lower])/(grid[upper]-grid[lower]);
  code=u32(lower)|((bits>>28)&8u);return u64(p*4294967296.0);
}