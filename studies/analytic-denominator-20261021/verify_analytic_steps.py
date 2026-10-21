"""Check explicit proof constants and a few witnesses, not a raw-input sweep."""
from pathlib import Path
from fractions import Fraction
import hashlib
import importlib.util
import json
import math

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT.parent/'boundary-propositions-20261021/targeted_reference.py'

def load_reference():
    spec = importlib.util.spec_from_file_location('sealed_bit_serial_reference',REFERENCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def units(a):
    if a <= 255:
        A,q = a,15
    elif a <= 383:
        A,q = a-128,16
    else:
        A,q = a-256,17
    n = A << q
    D, rem = divmod(n,3)
    D += rem == 2
    epsilon = 3*D-n
    assert epsilon in (-1,0,1)
    return A,q,D,epsilon

def main():
    ref = load_reference()
    scales=[]
    for a in (1,2,3,127,128,242,255,256,383,384,447,448,492):
        A,q,D,eps = units(a)
        assert ref.scale_bisection(a)==D
        assert (D < 1<<23) == (a < 448)
        scales.append(dict(amax_code=a,A=A,q=q,D=D,epsilon=eps))
    assert ref.bf16(448)/6 == Fraction(1,1<<126)

    brackets=[]
    for j, multipliers in ((1,range(1,6)),(2,range(7,12))):
        for m in multipliers:
            target=m*(1<<15)
            lower=math.isqrt(target//(3*j))
            upper=lower+1
            low_residual=3*j*lower*lower-target
            high_residual=3*j*upper*upper-target
            assert low_residual <= 0 < high_residual
            assert abs(low_residual)>16 and high_residual>16
            brackets.append(dict(j=j,m=m,lower_A=lower,upper_A=upper,
                                 low_residual=low_residual,high_residual=high_residual))
    odd_q16=[(j,t,e) for j in range(1,6) for t in range(1,5) for e in (-1,1) if (3*j-e*t)%8==0]
    assert set(odd_q16)=={(1,3,1),(2,2,-1),(3,1,1),(4,4,-1),(4,4,1),(5,1,-1)}
    odd_small=[(j,e) for j in range(1,8) for e in (-1,1) if (3*j-e)%8==0]
    assert odd_small==[(3,1),(5,-1)]
    assert [(j,e) for j in range(1,6) for e in (-1,1) if (3*j-e)%8==0]==odd_small

    square_checks=[]
    for n in (4369,12561,20753,28945,37137):
        k=math.isqrt(n)
        assert k*k<n<(k+1)*(k+1)
        square_checks.append(dict(n=n,lower=k,upper=k+1))
    assert (8192*8-1)//15==4369
    assert (8192*23-1)//15==12561
    assert (8192*38-1)//15==20753
    assert (8192*53-1)//15==28945
    assert (32768*17-1)//15==37137
    assert [m for m in range(8,30) if (2*m-1)%15==0]==[8,23]
    assert [m for m in range(30,68) if (2*m-1)%15==0]==[38,53]
    assert [m for m in range(8,30) if (8*m-1)%15==0]==[17]
    assert 766 < 1<<14 and 382 < 1<<12 and 574 < 1<<12

    witnesses=[]
    for a,x,q,A,X,L,S,E,pbad in ((492,199,17,236,199,49,33,0,44),
                                (242,221,15,242,221,47,31,2,48)):
        D=ref.scale_bisection(a)
        eps=3*D-(A<<q)
        N=X<<L
        Q=(N+D-1)//D
        j=Q*D-N
        assert j>0
        u=L-2*q
        numerator=j*A*A+(X<<u)
        t,rem=divmod(numerator,D)
        assert rem==0 and t>0
        assert Q==t*(1<<(2*q))-3*j*((A<<q)-eps)
        assert 3*X*(1<<u)==t*((A<<q)+eps)-3*j*A*A
        J=pbad-E-S
        assert j*(1<<J)<=D<j*(1<<(J+1))
        evaluations=[]
        for p in (pbad,pbad+1,53):
            out=ref.evaluate(a,x,32,p,D)
            assert out['mismatch']==(p==pbad)
            evaluations.append(out)
        witnesses.append(dict(amax=a,x=x,A=A,q=q,D=D,epsilon=eps,X=X,L=L,S=S,E=E,
                              gap=j,Q=Q,u=u,t=t,J_at_failure=J,evaluations=evaluations))
    assert witnesses[0]['gap']==2845 and witnesses[0]['t']==16
    assert witnesses[1]['gap']==47 and witnesses[1]['t']==12
    result=dict(schema='explicit-analytic-proof-constant-check-v1',
                base_commit='f7ba45359f485eaffd23794604fb9d636546bc56',
                protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                reused_reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
                scale_examples=scales,q15_integer_brackets=brackets,q16_odd_mod8_cases=odd_q16,
                small_odd_cases=odd_small,nonsquares=square_checks,witnesses=witnesses,
                status='PASS_EXPLICIT_CONSTANTS_AND_FIXED_WITNESSES',
                raw_pair_sweep=False,large_scan_rerun=False,gpu_executions=0,
                sharp_p45_p49_symbolic_sufficiency='OPEN',
                conservative_b32_p53_subnormal_proof='ELEMENTARY_PROOF_IN_COMPANION_DOCUMENT_NOT_PROOF_ASSISTANT')
    (ROOT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=result['status'],scale_examples=len(scales),
                          integer_brackets=len(brackets),nonsquares=len(square_checks),
                          fixed_witness_evaluations=6,raw_pair_sweep=False)))

if __name__=='__main__':
    main()
