"""Producer scale selection only. Packed FP4 format and consumer are unchanged."""
import os
os.environ['OPENBLAS_NUM_THREADS']='4';os.environ['OMP_NUM_THREADS']='4';os.environ['CUDA_VISIBLE_DEVICES']=''
import math
import numpy as np
from cpu_model import bf16
from independent_reference import GRID
ALPHAS=[.5,.625,.75,.875,1.,1.125,1.25]
RATIOS=np.arange(4,21,dtype=np.float32)/16
POLICIES=['original']+['amax_'+str(int(a*10000)) for a in ALPHAS]+['expected_unit_float17','expected_head_float17','expected_postadd_unit_float17','expected_postadd_head_float17','expected_unit_pow2_5','expected_head_pow2_5']
def original_scale(y):
    A=np.max(np.abs(y.reshape(-1,32)),axis=1)
    return np.fromiter((math.exp2(math.ceil(math.log2((float(a) if a>0 else 2.**-40)/6))) for a in A),np.float32,count=len(A))
def select_scale(name,y,r,original,channel_weights):
    """No target labels or RNG values enter any selector. Ties retain first candidate."""
    if name=='original':return original.copy()
    g=y.reshape(-1,32);A=np.max(np.abs(g),axis=1);base=np.where(A>0,A/np.float32(6),original).astype(np.float32)
    if name.startswith('amax_'):return (base*np.float32(int(name[5:])/10000)).astype(np.float32)
    assert name in POLICIES
    ratios=np.array([.125,.25,.5,1,2],np.float32) if 'pow2' in name else RATIOS
    start=original if 'pow2' in name else base
    weights=np.tile(channel_weights.reshape(18,32),(y.size//576,1)) if '_head_' in name else np.float64(1)
    postadd='_postadd_' in name;rg=r.reshape(-1,32);target=bf16(rg+g) if postadd else g
    minimum=np.full(len(A),np.inf,np.float64);chosen=start.copy();a=np.abs(g).astype(np.float64);sign=np.signbit(g)
    for ratio in ratios:
        s=(start*ratio).astype(np.float32);z=np.minimum(a/s[:,None].astype(np.float64),6);hi=np.minimum(np.searchsorted(GRID,z,side='right'),7);lo=hi-1
        p=np.floor((z-GRID[lo])/(GRID[hi]-GRID[lo])*float(1<<32))/float(1<<32)
        lower=np.where(sign,-GRID[lo],GRID[lo]).astype(np.float32);upper=np.where(sign,-GRID[hi],GRID[hi]).astype(np.float32)
        lower=bf16(lower*s[:,None]);upper=bf16(upper*s[:,None])
        if postadd:lower=bf16(rg+lower);upper=bf16(rg+upper)
        el=lower.astype(np.float64)-target;eu=upper.astype(np.float64)-target
        cost=np.sum(weights*((1-p)*el*el+p*eu*eu),axis=1)
        take=cost<minimum;minimum[take]=cost[take];chosen[take]=s[take]
    assert np.isfinite(chosen).all() and (chosen>0).all()
    return chosen
def encode_bytes(y,scales,words):
    x=np.ascontiguousarray(y).reshape(-1);z=np.minimum(np.abs(x).astype(np.float64)/np.repeat(scales,32).astype(np.float64),6);hi=np.minimum(np.searchsorted(GRID,z,side='right'),7);lo=hi-1
    thresholds=(((z-GRID[lo])/(GRID[hi]-GRID[lo]))*float(1<<32)).astype(np.uint64)
    codes=lo.astype(np.uint8)|((x.view(np.uint32)>>28)&8).astype(np.uint8);codes+=(words.astype(np.uint64)<thresholds).astype(np.uint8)
    return codes[::2]|(codes[1::2]<<4)
def decode_consumer(packed,scales,residual):
    # Direct CPU transcription of the unchanged decode_add.cu body, read packed bytes.
    n=residual.size;i=np.arange(n);c=(packed[i>>1]>>((i&1)*4))&15
    grid=GRID.astype(np.float32);v=grid[c&7]*scales[i>>5];v=np.where((c&8)!=0,-v,v)
    return bf16(residual+bf16(v).reshape(residual.shape))
def format_metrics(y,s):
    x=np.abs(y.reshape(-1,32)).astype(np.float64);cap=6*s[:,None].astype(np.float64);bits=s.view(np.uint32);power=((bits&np.uint32(0x807fffff))==0)&((bits>>23)>0)&((bits>>23)<255)
    return dict(groups=len(s),power2_groups=int(power.sum()),literal_clipped_coordinates=int((x>cap).sum()),material_clipped_coordinates=int((x>cap*(1+2.**-20)).sum()))
