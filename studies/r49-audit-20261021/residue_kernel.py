"""Complete small coefficient/t residue kernel; no raw BF16 pair sweep."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import csv
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parent
CLASSES=((15,1,255,16,15,42),(16,128,255,4,15,85),(17,128,191,1,13,127))
GRID=(Fraction(0),Fraction(1,2),Fraction(1),Fraction(3,2),Fraction(2),Fraction(3),Fraction(4),Fraction(6))

def floor_log(n,d):
    e=n.bit_length()-d.bit_length()
    if (n<d<<e) if e>=0 else (n<<-e<d):e-=1
    return e

def rounded_ratio(n,d,p):
    e=floor_log(n,d)
    h=p-1-e
    nn,dd=(n<<h,d) if h>=0 else (n,d<<-h)
    q,r=divmod(nn,dd)
    if r>dd-r or (r==dd-r and q%2):q+=1
    return Fraction(q,1<<h) if h>=0 else Fraction(q<<-h)

def canonical(v):
    if v>=6:return 6,1<<32
    for k in range(7):
        if v<GRID[k+1]:
            y=(v-GRID[k])/(GRID[k+1]-GRID[k])*(1<<32)
            return k,y.numerator//y.denominator
    raise AssertionError()

def input_range(q,A,v):
    if v==0:return 1,A if q==15 else 255
    if v==1:return 128,A if q==16 else 255
    return 128,A

def main():
    counts=Counter();survivors=[];reconstructions=[];physical=[];counterexamples=[]
    ledger=[];per_class=[]
    for q,amin,amax,tmax,m,global_cap in CLASSES:
        before=counts.copy()
        for A in range(amin,amax+1):
            D,rem=divmod(A<<q,3);D+=rem==2
            eps=3*D-(A<<q)
            assert eps in (-1,0,1) and 0<D<(1<<23)
            cap=D//(1<<16)
            assert cap<=global_cap
            for t in range(1,tmax+1):
                counts['coefficient_t_branches']+=1
                entry=dict(q=q,A=A,D=D,epsilon=eps,t=t,m=m,j_cap=cap,gcd=None,modulus=None,j_residue=None,status=None)
                if eps==0:
                    entry['status']='EXACT_SCALE_DIVISIBILITY_EXCLUSION';counts['epsilon_zero']+=1
                    ledger.append(entry);continue
                assert math.gcd(A,D)==1 and D%2==1
                M=1<<m;c=3*A*A;g=math.gcd(c,M)
                entry['gcd']=g
                if (eps*t)%g:
                    entry['status']='GCD_EXCLUSION';counts['gcd_exclusion']+=1
                    ledger.append(entry);continue
                modulus=M//g
                assert modulus>global_cap
                inv=pow(c//g,-1,modulus)
                assert (c//g)*inv%modulus==1
                j=(eps*t//g*inv)%modulus
                entry.update(modulus=modulus,j_residue=j)
                if not 1<=j<=cap:
                    entry['status']='UNIQUE_RESIDUE_OUTSIDE_CARRY_RANGE';counts['range_exclusion']+=1
                    ledger.append(entry);continue
                assert (3*A*A*j-eps*t)%M==0
                entry['status']='COARSE_CONGRUENCE_SURVIVOR'
                counts['coarse_survivors']+=1
                ledger.append(entry)
                a_code=A+(0 if q==15 else 128 if q==16 else 256)
                survivor=dict(q=q,A=A,D=D,epsilon=eps,t=t,j=j,m=m,amax_code=a_code)
                survivors.append(survivor)
                B=t*((A<<q)+eps)-3*j*A*A
                for v in range(q-14):
                    for S in (31,32,33):
                        counts['v_S_branches']+=1
                        L=16+v+S;u=L-2*q
                        assert min(u,q)>=m and u>=0
                        row=dict(survivor,v=v,S=S,L=L,u=u,numerator=B,X=None,status=None)
                        divisor=3<<u
                        if B<=0:
                            row['status']='NONPOSITIVE_RECONSTRUCTED_INPUT';counts['nonpositive_X']+=1
                        elif B%divisor:
                            row['status']='NONINTEGRAL_RECONSTRUCTED_INPUT';counts['nonintegral_X']+=1
                        else:
                            X=B//divisor;row['X']=X
                            lo,hi=input_range(q,A,v)
                            if not lo<=X<=hi:
                                row['status']='BF16_OR_MAXIMUM_LEGALITY_EXCLUSION';counts['input_range_exclusion']+=1
                            else:
                                x_code=X+(0 if v==0 else 128 if v==1 else 256)
                                assert 1<=x_code<=a_code
                                n=X<<(16+v);d=D
                                N=X<<L;actual_gap=D-N%D
                                assert N%D and actual_gap==j
                                expectedS=33 if n<2*d else 32 if n<4*d else 31 if n<6*d else None
                                row.update(x_code=x_code,ratio_n=n,ratio_d=d,actual_gap=actual_gap,expected_S=expectedS)
                                if expectedS!=S:
                                    row['status']='SELECTED_INTERVAL_EXCLUSION';counts['interval_exclusion']+=1
                                else:
                                    E=floor_log(n,d);J=49-E-S
                                    assert J>=16
                                    carry=j*(1<<J)<=D
                                    exact=canonical(Fraction(n,d));rounded=canonical(rounded_ratio(n,d,49))
                                    assert (exact!=rounded)==carry
                                    row.update(E=E,J=J,carry=carry,ideal_base=exact[0],ideal_T=exact[1],rounded_base=rounded[0],rounded_T=rounded[1])
                                    physical.append(row.copy())
                                    if carry:
                                        row['status']='ACTUAL_R49_COUNTEREXAMPLE';counts['actual_counterexamples']+=1
                                        counterexamples.append(row.copy())
                                    else:
                                        row['status']='EXACT_BINade_GUARD_EXCLUSION';counts['exact_guard_exclusion']+=1
                        reconstructions.append(row)
        per_class.append(dict(q=q,counts=dict(counts-before)))
    assert counts['coefficient_t_branches']==4656
    fields=('q','A','D','epsilon','t','m','j_cap','gcd','modulus','j_residue','status')
    with (ROOT/'coefficient_ledger.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(ledger)
    result=dict(schema='r49-residue-kernel-v1',base_commit='2e7c2dae61ac9da85e889168694a459bfed13cd1',
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
                counts=dict(counts),per_class=per_class,coarse_survivors=survivors,
                reconstructions=reconstructions,physical_candidates=physical,counterexamples=counterexamples,
                verdict='COUNTEREXAMPLE_FOUND' if counterexamples else 'NO_COUNTEREXAMPLE_IN_COMPLETE_REDUCED_KERNEL',
                proof_kind='Analytic reduction plus complete finite residue certificate; not a pure symbolic exclusion',
                raw_input_pairs_enumerated=False,gpu_executions=0)
    (ROOT/'kernel_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(counts=counts,verdict=result['verdict'],survivors=survivors,physical=physical),indent=2))

if __name__=='__main__':main()
