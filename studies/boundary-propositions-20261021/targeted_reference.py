"""Small raw-code minimality certificates using bit-serial integer RNE."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parent
GRID2 = (0, 1, 2, 3, 4, 6, 8, 12)

def pow2(e):
    return Fraction(1 << e) if e >= 0 else Fraction(1, 1 << -e)

def bf16(code):
    e, f = code >> 7, code & 127
    return f * pow2(-133) if e == 0 else (128 + f) * pow2(e - 134)

def f32(bits):
    e, f = bits >> 23, bits & 0x7fffff
    return f * pow2(-149) if e == 0 else (0x800000 + f) * pow2(e - 150)

def scale_bisection(a):
    if a == 0:
        return 85 << 23
    v = bf16(a) / 6
    low, high = 0, 0x7f7fffff
    while low < high:
        mid = (low + high + 1) // 2
        if f32(mid) <= v:
            low = mid
        else:
            high = mid - 1
    dlow, dhigh = v - f32(low), f32(low + 1) - v
    return low if dlow < dhigh or (dlow == dhigh and low % 2 == 0) else low + 1

def nearest(v, p):
    """Separate exact midpoint reference; no bit-serial division."""
    if v == 0:
        return Fraction(0)
    normalized, e = v, 0
    while normalized < 1:
        normalized *= 2
        e -= 1
    while normalized >= 2:
        normalized /= 2
        e += 1
    step = pow2(e - p + 1)
    location = v / step
    lower = location.numerator // location.denominator
    mid = (2 * lower + 1) * step / 2
    return (lower + int(v > mid or (v == mid and lower % 2))) * step

def scale_midpoint(a):
    if a == 0:
        return 85 << 23
    v = bf16(a) / 6
    if v < pow2(-126):
        z = v / pow2(-149)
        q, r = divmod(z.numerator, z.denominator)
        return q + int(2*r > z.denominator or (2*r == z.denominator and q % 2))
    rounded = nearest(v, 24)
    normalized, e = rounded, 0
    while normalized < 1:
        normalized *= 2
        e -= 1
    while normalized >= 2:
        normalized /= 2
        e += 1
    sig = normalized * (1 << 23)
    assert sig.denominator == 1
    return ((e + 127) << 23) | (sig.numerator - (1 << 23))

def serial_rne(n, d, p):
    """Generate p significand bits and guard/sticky from exact long division."""
    if n == 0:
        return 0, 1
    e = n.bit_length() - d.bit_length()
    nn, dd = (n, d << e) if e >= 0 else (n << -e, d)
    if nn < dd:
        nn *= 2
        e -= 1
    assert dd <= nn < 2 * dd
    q, remainder = 1, nn - dd
    for _ in range(p - 1):
        remainder *= 2
        bit = remainder >= dd
        if bit:
            remainder -= dd
        q = 2 * q + bit
    remainder *= 2
    guard = remainder >= dd
    if guard:
        remainder -= dd
    sticky = remainder != 0
    q += int(guard and (sticky or q % 2))
    shift = e - p + 1
    return (q << shift, 1) if shift >= 0 else (q, 1 << -shift)

def threshold(n, d, b):
    if n >= 6*d:
        return 6, 1 << b
    for k in range(7):
        if 2*n < GRID2[k+1]*d:
            return k, ((2*n-GRID2[k]*d) << b) // ((GRID2[k+1]-GRID2[k])*d)
    raise AssertionError('No interval')

def evaluate(a, x, b, p, scale):
    ratio = bf16(x) / f32(scale)
    n, d = ratio.numerator, ratio.denominator
    rn, rd = serial_rne(n, d, p)
    ideal, rounded = threshold(n, d, b), threshold(rn, rd, b)
    return dict(amax_bf16=a, x_bf16=x, scale_f32=scale, b=b, p=p,
                ratio_n=n, ratio_d=d, rounded_n=rn, rounded_d=rd,
                ideal_base=ideal[0], ideal_T=ideal[1],
                rounded_base=rounded[0], rounded_T=rounded[1], mismatch=ideal != rounded)

def main():
    start = time.perf_counter()
    protocol = json.loads((ROOT/'protocol.json').read_text())
    scales, prefixes, independent_checks, failures = {}, [], 0, []
    for p in (35, 44, 48, 53, 64):
        for v in (Fraction(0), Fraction(1,3), 1+pow2(-p), 1+3*pow2(-p), Fraction(6)):
            n, d = serial_rne(v.numerator,v.denominator,p)
            assert Fraction(n,d) == nearest(v,p)
            independent_checks += 1
    for spec in protocol['raw_code_minimality_prefixes']:
        first, count, local_failures = None, 0, []
        digest = hashlib.sha256()
        for a in range(spec['amax_first'],spec['amax_last']+1):
            if a not in scales:
                s1, s2 = scale_bisection(a), scale_midpoint(a)
                assert s1 == s2, ('SCALE_REFERENCE_DISAGREEMENT',a)
                scales[a] = s1
            for x in range(a+1):
                c = evaluate(a,x,spec['b'],spec['p'],scales[a])
                count += 1
                digest.update(f"{a},{x},{c['ideal_base']},{c['ideal_T']},{c['rounded_base']},{c['rounded_T']}\n".encode())
                if c['mismatch']:
                    first = first or c
                    local_failures.append(c)
                if count % 997 == 0 or c['mismatch']:
                    expected = nearest(Fraction(c['ratio_n'],c['ratio_d']),spec['p'])
                    assert expected == Fraction(c['rounded_n'],c['rounded_d'])
                    independent_checks += 1
        assert first is not None, ('EXPECTED_BOUNDARY_NOT_REPRODUCED',spec['id'])
        prefixes.append(dict(id=spec['id'],evaluations=count,mismatches=len(local_failures),
                             first_failure=first,coverage_sha256=digest.hexdigest(),
                             all_failures=local_failures))
        failures.extend(local_failures)
        print(json.dumps(dict(id=spec['id'],evaluations=count,mismatches=len(local_failures),
                              first_amax=first['amax_bf16'],first_x=first['x_bf16'])),flush=True)
    precision_checks = []
    for prefix in prefixes:
        c = prefix['first_failure']
        lo = 35 if c['b'] == 32 else 41
        for p in range(lo,65):
            rec = evaluate(c['amax_bf16'],c['x_bf16'],c['b'],p,scales[c['amax_bf16']])
            expected = nearest(Fraction(rec['ratio_n'],rec['ratio_d']),p)
            assert expected == Fraction(rec['rounded_n'],rec['rounded_d'])
            independent_checks += 1
            precision_checks.append(rec)
    small = prefixes[2]['first_failure']
    assert (small['amax_bf16'],small['x_bf16'],small['scale_f32']) == (16,4,174763)
    assert (small['ideal_T'],small['rounded_T']) == (274876334082,274876334083)
    assert small['rounded_n'] * (1 << 39) == 824632147971 * small['rounded_d']
    coarse = evaluate(16,4,37,53,174763)
    assert not coarse['mismatch'] and coarse['ideal_T'] == 137438167041
    assert pow(2,19,174763) == 174762 and pow(2,57,174763) == 174762
    assert pow(2,56,174763) == (174763-1)//2
    zeros = [evaluate(0,0,b,53,scale_bisection(0)) for b in (32,37,38)]
    assert all(not c['mismatch'] and c['ideal_T']==0 for c in zeros)
    receipt = dict(schema='targeted-bit-serial-reference-v1',
        base_commit=protocol['base_commit'],
        protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        algorithm='Exact normalized bit-serial long division; guard/sticky/ties-even; no gap inequality',
        prefixes=prefixes,precision_checks=precision_checks,coarse_small_witness=coarse,
        zero_checks=zeros,scale_checks=len(scales),independent_midpoint_checks=independent_checks,
        total_prefix_evaluations=sum(p['evaluations'] for p in prefixes),
        source_selection='Known witness endpoints; post-selection minimality validation, not discovery',
        assertion_status='PASS',gpu_executions=0,compiler_executions=0,
        wall_seconds=time.perf_counter()-start)
    (ROOT/'targeted_results.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print('TARGETED_REFERENCE_PASS',receipt['total_prefix_evaluations'],independent_checks,flush=True)

if __name__=='__main__':
    main()
