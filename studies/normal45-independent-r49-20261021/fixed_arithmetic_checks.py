"""Small exact scale, failure-witness and eta checks; no input sweep."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json

ROOT=Path(__file__).resolve().parent
GRID=tuple(map(Fraction,(0,Fraction(1,2),1,Fraction(3,2),2,3,4,6)))


def rne(value,p):
    n,d=value.numerator,value.denominator
    e=n.bit_length()-d.bit_length()
    if (n < d*2**e) if e>=0 else (n*2**(-e)<d):
        e-=1
    scale=Fraction(2)**(p-1-e)
    exact=value*scale
    lower=exact.numerator//exact.denominator
    residual=exact-lower
    rounded=lower+int(residual>Fraction(1,2) or
                      (residual==Fraction(1,2) and lower%2))
    return Fraction(rounded)/scale


def canonical(v):
    if v>=6:return 6,2**32
    for k in range(7):
        if GRID[k]<=v<GRID[k+1]:
            a=(v-GRID[k])/(GRID[k+1]-GRID[k])*2**32
            return k,a.numerator//a.denominator
    raise AssertionError()


def run():
    scale_checks=[]
    for A in (128,142,191,192,236,239,255):
        actual=rne(Fraction(A,768),24)
        q=18 if A<192 else 17
        e=-3 if q==18 else -2
        D=actual*2**(23-e)
        assert D.denominator==1
        D=int(D)
        eps=3*D-(A<<q)
        assert eps in (-1,0,1)
        scale_checks.append(dict(A=A,q=q,D=D,epsilon=eps))
    D,j=10310997,2845
    assert (199<<49)+j==10864811689*D
    assert j*2**11==5826560<=D<11653120==j*2**12
    r=Fraction(13041664,D)
    ideal=canonical(r)
    rounded44=canonical(rne(r,44))
    rounded45=canonical(rne(r,45))
    assert ideal==(2,2274877096) and rounded44==(2,2274877097)
    assert rounded45==ideal
    eta_rows=[]
    for q,A,D,t,j,X,u in ((18,142,12408149,4,2277,227,14),
                         (17,239,10442069,5,649,231,16)):
        assert 3*D==(A<<q)-1
        assert 3*X*2**u==t*((A<<q)-1)-3*j*A*A
        assert 128<=X<=255 and X*65536>D
        eta_rows.append(dict(q=q,A=A,X=X,D=D,assumed_eta=1,actual_eta=0,
                             X_times_65536=X*65536))
    result=dict(status='PASS_FIXED_ARITHMETIC',scale_checks=scale_checks,
                witness=dict(a_code=492,x_code=199,identity_verified=True,
                             ideal=ideal,p44=rounded44,p45=rounded45,
                             negative_control='p44 differs by one threshold unit'),
                eta_exceptions=eta_rows,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                raw_pair_sweep=False,gpu_runs=0)
    (ROOT/'fixed_arithmetic_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=result['status'],scale_examples=len(scale_checks),
                          direct_witness_precisions=2,eta_exceptions=len(eta_rows))))


if __name__=='__main__':run()
