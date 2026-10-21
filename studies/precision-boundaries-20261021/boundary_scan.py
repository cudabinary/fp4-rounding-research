"""Exact arithmetic boundary scan. Standard library only; no GPU or compiler."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import csv, hashlib, json, math, struct, time

ROOT = Path(__file__).resolve().parent
PROTOCOL = json.loads((ROOT / 'protocol.json').read_text(encoding='utf-8'))
BITS = PROTOCOL['probability_bits']
GRID = tuple(map(Fraction, ('0', '0.5', '1', '1.5', '2', '3', '4', '6')))

def power2(e):
    return Fraction(1 << e, 1) if e >= 0 else Fraction(1, 1 << -e)

def log2_ratio(n, d):
    e = n.bit_length() - d.bit_length()
    if (n < d << e) if e >= 0 else (n << -e < d):
        e -= 1
    return e

def nearest_integer(n, d):
    q, rem = divmod(n, d)
    return q + int(2 * rem > d or (2 * rem == d and q & 1))

def rne_integer(n, d, p):
    """Integer-significand oracle, exact and independent of host FP modes."""
    if n == 0:
        return Fraction(0)
    e = log2_ratio(n, d)
    shift = p - 1 - e
    q = nearest_integer(n << shift, d) if shift >= 0 else nearest_integer(n, d << -shift)
    return Fraction(q) * power2(-shift)

def rne_fraction(v, p):
    """Separate nearest-neighbor/midpoint Fraction oracle; float is only a seed."""
    if not v:
        return Fraction(0)
    e = math.frexp(float(v))[1] - 1
    while v < power2(e):
        e -= 1
    while v >= power2(e + 1):
        e += 1
    step = power2(e - p + 1)
    loc = v / step
    lower = loc.numerator // loc.denominator
    lo, hi = lower * step, (lower + 1) * step
    dl, dh = v - lo, hi - v
    return lo if dl < dh or (dl == dh and lower % 2 == 0) else hi

def bf16(code):
    ef, mant = code >> 7, code & 127
    return mant * power2(-133) if ef == 0 else (128 + mant) * power2(ef - 134)

def f32(bits):
    ef, mant = bits >> 23, bits & ((1 << 23) - 1)
    return mant * power2(-149) if ef == 0 else ((1 << 23) + mant) * power2(ef - 150)

def scale_integer(v):
    e = log2_ratio(v.numerator, v.denominator)
    if e < -126:
        return nearest_integer(v.numerator << 149, v.denominator)
    z = rne_integer(v.numerator, v.denominator, 24)
    e = log2_ratio(z.numerator, z.denominator)
    sig = z / power2(e - 23)
    assert sig.denominator == 1
    return ((e + 127) << 23) | (sig.numerator - (1 << 23))

def scale_binary_search(v):
    """F32 encoding bisection and exact midpoint; no significand-round helper."""
    lo, hi = 0, 0x7f7fffff
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if f32(mid) <= v:
            lo = mid
        else:
            hi = mid - 1
    if f32(lo) == v:
        return lo
    dl, dh = v - f32(lo), f32(lo + 1) - v
    return lo if dl < dh or (dl == dh and lo % 2 == 0) else lo + 1

def grid_threshold(v, b):
    if v >= 6:
        return 6, 1 << b
    for base in range(7):
        if v < GRID[base + 1]:
            z = (v - GRID[base]) / (GRID[base + 1] - GRID[base]) * (1 << b)
            return base, z.numerator // z.denominator
    raise AssertionError(v)

def lattice(n, d, b):
    if not n or n >= 6 * d:
        return None
    S = b + 1 if n < 2 * d else b if n < 4 * d else b - 1
    e = log2_ratio(n, d)
    rem = (n << S) % d
    if not rem:
        return None
    gap = d - rem
    max_bad_p = e + S + log2_ratio(d, gap)
    return max_bad_p, e, S, gap

def case(kind, ac, xc, sb, n, d, info, b):
    pb, e, S, gap = info
    return dict(kind=kind, amax_bf16=ac, x_bf16=xc, scale_f32=sb,
                ratio_n=n, ratio_d=d, b=b, max_crossing_p=pb,
                E=e, S=S, gap=gap)

def check(c, p, out):
    b, n, d = c['b'], c['ratio_n'], c['ratio_d']
    v = Fraction(n, d)
    rounded = rne_integer(n, d, p)
    other = rne_fraction(v, p)
    assert rounded == other, ('RNE_ORACLE_DISAGREEMENT', c, p)
    S = c['S']
    z1, z2 = v * (1 << S), rounded * (1 << S)
    f1, f2 = z1.numerator // z1.denominator, z2.numerator // z2.denominator
    predicted = p <= c['max_crossing_p']
    actual = f1 != f2
    assert p >= b + 3
    assert predicted == actual, ('GAP_PREDICTION_DISAGREEMENT', c, p, f1, f2)
    assert f2 >= f1, ('DOWNWARD_LOSS', c, p)
    real, rp = grid_threshold(v, b), grid_threshold(rounded, b)
    assert (real != rp) == actual, ('CANONICAL_GRID_DISAGREEMENT', c, p, real, rp)
    witness_u = None
    if actual:
        for u in sorted({0, (1 << b) - 1, real[1], rp[1]}):
            if 0 <= u < 1 << b:
                if real[0] + (u < real[1]) != rp[0] + (u < rp[1]):
                    witness_u = u
                    break
        assert witness_u is not None, ('NO_OUTPUT_WITNESS', c, p)
    rec = dict(c, p=p, rounded_n=rounded.numerator, rounded_d=rounded.denominator,
               ideal_base=real[0], ideal_T=real[1], rounded_base=rp[0], rounded_T=rp[1],
               crossing=actual, abstract_word_witness=witness_u)
    out.write(json.dumps(rec, separators=(',', ':')) + '\n')
    return rec

def main():
    start = time.perf_counter()
    unit_count = 0
    for p in (19, 35, 53, 64):
        for v in (Fraction(1, 3), Fraction(7, 5), 1 + power2(-p), 1 + 3 * power2(-p), Fraction(6)):
            assert rne_integer(v.numerator, v.denominator, p) == rne_fraction(v, p)
            unit_count += 1
        assert rne_integer((1 + power2(-p)).numerator, (1 + power2(-p)).denominator, p) == 1
        assert rne_integer((1 + 3 * power2(-p)).numerator, (1 + 3 * power2(-p)).denominator, p) == 1 + power2(2-p)

    scales, scale_receipts = {}, []
    for ac in list(range(1, 448)) + list(range(0x3f80, 0x4000)):
        target = bf16(ac) / 6
        s1, s2 = scale_integer(target), scale_binary_search(target)
        assert s1 == s2, ('SCALE_ORACLE_DISAGREEMENT', ac, s1, s2)
        host = struct.unpack('<I', struct.pack('<f', float(bf16(ac)) / 6.0))[0]
        assert host == s1, ('HOST_SCALE_DISAGREEMENT', ac, host, s1)
        scales[ac] = s1
        scale_receipts.append(dict(amax_bf16=ac, scale_f32=s1, scale_n=f32(s1).numerator, scale_d=f32(s1).denominator))
    (ROOT / 'scale_checks.json').write_text(json.dumps(scale_receipts, indent=2), encoding='utf-8')

    summaries, all_extremal, independent_total = [], [], 0
    counts = ROOT / 'coverage.csv'
    with counts.open('w', newline='', encoding='utf-8') as cf, \
         (ROOT / 'p53_counterexamples.jsonl').open('w', encoding='utf-8') as failures, \
         (ROOT / 'independent_checks.jsonl').open('w', encoding='utf-8') as checks:
        writer = csv.DictWriter(cf, fieldnames=('b','kind','amax_key','pairs','nontrivial_nonlattice','p53_crossings','max_crossing_p'))
        writer.writeheader()
        for b in BITS:
            histogram, digest = Counter(), hashlib.sha256()
            extrema = {'normal': (-9999, []), 'subnormal': (-9999, [])}
            total = p53_count = zero_or_saturated_or_lattice = independent_this = 0

            def consume(kind, key, ac, xc, sb, n, d, stats):
                nonlocal total, p53_count, zero_or_saturated_or_lattice, independent_this
                total += 1
                stats['pairs'] += 1
                info = lattice(n, d, b)
                pb = info[0] if info else -9999
                digest.update(struct.pack('<iii', ac, xc, pb))
                if info is None:
                    zero_or_saturated_or_lattice += 1
                    return
                stats['nontrivial_nonlattice'] += 1
                stats['max_crossing_p'] = max(stats['max_crossing_p'], pb)
                histogram[pb] += 1
                c = None
                if pb >= extrema[kind][0]:
                    c = case(kind, ac, xc, sb, n, d, info, b)
                    if pb > extrema[kind][0]:
                        extrema[kind] = (pb, [c])
                    else:
                        extrema[kind][1].append(c)
                if pb >= 53:
                    c = c or case(kind, ac, xc, sb, n, d, info, b)
                    p53_count += 1
                    stats['p53_crossings'] += 1
                    failures.write(json.dumps(c, separators=(',', ':')) + '\n')
                    check(c, 53, checks)
                    independent_this += 1
                # Deterministic stratification independent of whether the case fails.
                if ((ac * 65537 + xc * 17) % 1021) == 0:
                    c = c or case(kind, ac, xc, sb, n, d, info, b)
                    for p in sorted({b + 3, 53, 64}):
                        check(c, p, checks)
                        independent_this += 1

            for A in range(128, 256):
                ac = 0x3f80 + A - 128
                sb = scales[ac]
                es = (sb >> 23) - 127
                D = (1 << 23) | (sb & ((1 << 23) - 1))
                stats = dict(b=b,kind='normal',amax_key=A,pairs=0,nontrivial_nonlattice=0,p53_crossings=0,max_crossing_p=-9999)
                for t in range(-(b + 6), 1):
                    for X in range(128, (A if t == 0 else 255) + 1):
                        shift = t + 16 - es
                        n, d = (X << shift, D) if shift >= 0 else (X, D << -shift)
                        xc = ((127 + t) << 7) | (X - 128)
                        consume('normal', A, ac, xc, sb, n, d, stats)
                writer.writerow(stats)
            for ac in range(1, 448):
                sb = scales[ac]
                assert 0 < sb < 1 << 23
                stats = dict(b=b,kind='subnormal',amax_key=ac,pairs=0,nontrivial_nonlattice=0,p53_crossings=0,max_crossing_p=-9999)
                for xc in range(ac + 1):
                    ef, m = xc >> 7, xc & 127
                    units = m << 16 if ef == 0 else (128 + m) << (ef + 15)
                    consume('subnormal', ac, ac, xc, sb, units, sb, stats)
                writer.writerow(stats)

            per_kind = {}
            for kind, (worst, cases) in extrema.items():
                ordered = sorted(cases, key=lambda c: (c['amax_bf16'], c['x_bf16']))
                all_extremal.extend(ordered)
                for c in ordered:
                    for p in sorted({53, max(b + 3, worst), max(b + 3, worst + 1)}):
                        if p <= 64:
                            check(c, p, checks)
                            independent_this += 1
                per_kind[kind] = dict(max_crossing_p=worst,
                                      first_safe_p_in_tested_region=max(b+3, worst+1),
                                      extremal_cases=len(ordered), representative=ordered[0])
            worst = max(v[0] for v in extrema.values())
            summary = dict(b=b, pairs=total, zero_saturated_or_lattice=zero_or_saturated_or_lattice,
                           p53_crossings=p53_count, max_crossing_p=worst,
                           first_safe_p_in_tested_region=max(b+3,worst+1),
                           p53_safe=(p53_count==0), kinds=per_kind,
                           max_p_histogram=dict(sorted(histogram.items())),
                           enumeration_sha256=digest.hexdigest(), independent_checks=independent_this)
            summaries.append(summary)
            independent_total += independent_this
            cf.flush(); failures.flush(); checks.flush()
            (ROOT / 'partial_results.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
            print(json.dumps({k: summary[k] for k in ('b','pairs','p53_crossings','max_crossing_p','first_safe_p_in_tested_region','independent_checks')}), flush=True)
    results = dict(protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
                   cpu_only=True, working_exponent_range='binary64; no encountered ratio under/overflow',
                   normal_t_tail_bound='For t<-(b+6), r<12*2^t<3*2^(-b-4). With p>=b+3>=19, RN_p(r)<2^(-b-1), so both thresholds are zero.',
                   zero_case='a=x=0 uses fixed 2^-42; threshold zero at all tested b/p, independently checked',
                   scale_checks=len(scale_receipts), oracle_unit_checks=unit_count,
                   independent_checks=independent_total, summaries=summaries,
                   wall_seconds=time.perf_counter()-start)
    for b in BITS:
        assert grid_threshold(Fraction(0),b)==(0,0)
    (ROOT / 'extremal_cases.json').write_text(json.dumps(all_extremal,indent=2),encoding='utf-8')
    (ROOT / 'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('COMPLETE', json.dumps(dict(wall_seconds=results['wall_seconds'], independent_checks=independent_total)),flush=True)

if __name__ == '__main__':
    main()
