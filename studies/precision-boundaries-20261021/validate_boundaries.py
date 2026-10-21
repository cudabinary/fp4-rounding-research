"""Direct integer RNE evaluation; does NOT use the gap/carry inequality."""
from pathlib import Path
from fractions import Fraction
import csv, hashlib, json, struct, time

ROOT = Path(__file__).resolve().parent
HALF_GRID = (0,1,2,3,4,6,8,12)

def parts(code, fmt):
    if fmt == 'bf16':
        field, frac = code >> 7, code & 127
        return (frac,-133) if field == 0 else (128+frac,field-134)
    field, frac = code >> 23, code & 0x7fffff
    return (frac,-149) if field == 0 else (0x800000+frac,field-150)

def ratio(ac, xc):
    a = struct.unpack('<f',struct.pack('<I',ac << 16))[0]
    sb = struct.unpack('<I',struct.pack('<f',a/6.0))[0]
    xn, xe = parts(xc,'bf16')
    sn, se = parts(sb,'f32')
    shift = xe-se
    return (xn << shift,sn,sb) if shift >= 0 else (xn,sn << -shift,sb)

def rounded_pair(n,d,p):
    if not n:
        return 0,1
    # Magnitude bounds are verified directly after a bit-length initial guess.
    e=n.bit_length()-d.bit_length()
    while (n < d << e) if e >= 0 else (n << -e < d):
        e-=1
    while (n >= d << (e+1)) if e+1 >= 0 else (n << -(e+1) >= d):
        e+=1
    quantum=e+1-p
    num,den=(n,d << quantum) if quantum >= 0 else (n << -quantum,d)
    q,r=divmod(num,den)
    if r > den-r or (r == den-r and q % 2):
        q+=1
    return (q << quantum,1) if quantum >= 0 else (q,1 << -quantum)

def full_threshold(n,d,b):
    if n >= 6*d:
        return 6,1 << b
    for i in range(7):
        if 2*n < HALF_GRID[i+1]*d:
            return i,((2*n-HALF_GRID[i]*d) << b)//((HALF_GRID[i+1]-HALF_GRID[i])*d)
    raise AssertionError()

def main():
    start=time.perf_counter()
    scales={x['amax_bf16']:x['scale_f32'] for x in json.loads((ROOT/'scale_checks.json').read_text())}
    rows=[]
    failures=[]
    for b in (32,37,38):
        for kind in ('normal','subnormal'):
            ps=(44,45) if b==32 and kind=='normal' else (48,49) if b==32 else (53,)
            counts={p:0 for p in ps}
            pairs=0
            digest=hashlib.sha256()
            if kind=='normal':
                cases=((0x3f80+A-128,((127+t)<<7)|(X-128))
                       for A in range(128,256) for t in range(-(b+6),1)
                       for X in range(128,(A if t==0 else 255)+1))
            else:
                cases=((ac,xc) for ac in range(1,448) for xc in range(ac+1))
            for ac,xc in cases:
                n,d,sb=ratio(ac,xc)
                assert sb==scales[ac]
                exact=full_threshold(n,d,b)
                pairs+=1
                for p in ps:
                    rn,rd=rounded_pair(n,d,p)
                    result=full_threshold(rn,rd,b)
                    mismatch=result!=exact
                    counts[p]+=mismatch
                    digest.update(struct.pack('<iii?',ac,xc,p,mismatch))
                    if mismatch:
                        failures.append(dict(kind=kind,b=b,p=p,amax_bf16=ac,x_bf16=xc,
                                             scale_f32=sb,ratio_n=n,ratio_d=d,
                                             ideal_base=exact[0],ideal_T=exact[1],
                                             rounded_base=result[0],rounded_T=result[1]))
            for p in ps:
                rows.append(dict(b=b,kind=kind,p=p,pairs=pairs,mismatches=counts[p],
                                 enumeration_sha256=digest.hexdigest()))
            print(json.dumps(dict(b=b,kind=kind,pairs=pairs,mismatches=counts)),flush=True)
    main_result=json.loads((ROOT/'results.json').read_text())
    for row in rows:
        expected=next(s for s in main_result['summaries'] if s['b']==row['b'])
        k=expected['kinds'][row['kind']]
        assert (row['mismatches']==0)==(row['p']>k['max_crossing_p'])
        if row['b']==38:
            expected_count=0 if row['kind']=='normal' else 9
            assert row['mismatches']==expected_count
    (ROOT/'direct_validation.json').write_text(json.dumps(dict(cpu_only=True,
        algorithm='Direct correctly-rounded integer significand followed by complete E2M1 interpolation; no gap inequality',
        total_RNE_evaluations=sum(x['pairs'] for x in rows),rows=rows,
        mismatches=failures,wall_seconds=time.perf_counter()-start),indent=2),encoding='utf-8')
    print('VALIDATION_COMPLETE',sum(x['pairs'] for x in rows),len(failures),flush=True)

if __name__=='__main__':
    main()
