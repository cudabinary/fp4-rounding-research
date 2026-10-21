"""Explore complete reduced normal p45 conditions; never enumerate raw pairs."""
from collections import Counter
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent


def run():
    counts = Counter()
    candidates = []
    for q, lo, hi, tcap in ((18, 128, 191, 9), (17, 192, 255, 16)):
        for A in range(lo, hi + 1):
            D, rem = divmod(A << q, 3)
            D += rem == 2
            eps = 3 * D - (A << q)
            assert eps in (-1, 0, 1) and 2**23 <= D < 2**24
            for t in range(1, tcap + 1):
                counts['A_t_branches'] += 1
                if eps == 0:
                    counts['exact_scale_branch_exclusions'] += 1
                    continue
                for J in range(12, 24):
                    counts['A_t_J_branches'] += 1
                    # t < (A^2 + 2^(46-2q)) / 2^J is strict.
                    if t * 2**J >= A*A + 2**(46-2*q):
                        counts['refined_t_bound_exclusions'] += 1
                        continue
                    for eta in (0, 1):
                        counts['bounded_eta_branches'] += 1
                        L = 61 + eta - J
                        u = L - 2*q
                        assert 0 <= u <= q
                        M = 2**u
                        c = 3*A*A
                        g = math.gcd(c, M)
                        if eps*t % g:
                            counts['gcd_exclusions'] += 1
                            continue
                        modulus = M // g
                        j0 = ((eps*t//g) * pow(c//g, -1, modulus)) % modulus
                        cap = D // 2**J
                        start = j0 if j0 else modulus
                        for j in range(start, cap + 1, modulus):
                            counts['coarse_j_candidates'] += 1
                            B = t*((A << q)+eps)-3*j*A*A
                            divisor = 3 << u
                            assert B % divisor == 0
                            X = B // divisor
                            row = dict(q=q, A=A, D=D, epsilon=eps, t=t, J=J,
                                       eta=eta, L=L, u=u, j=j, X=X)
                            if not 128 <= X <= 255:
                                row['status'] = 'NORMALIZED_X_RANGE_EXCLUSION'
                                counts['X_range_exclusions'] += 1
                            elif int((X << 16) < D) != eta:
                                row['status'] = 'ETA_CONSISTENCY_EXCLUSION'
                                counts['eta_exclusions'] += 1
                            else:
                                row['status'] = 'REQUIRES_PHYSICAL_INTERVAL_CHECK'
                                counts['survivors_before_physical_check'] += 1
                                tests = []
                                for S in (31, 32, 33):
                                    d = L-q-1-S
                                    n = X << max(d+q+1, 0)
                                    den = D << max(-(d+q+1), 0)
                                    r = Fraction(n, den)
                                    expected = 33 if r < 2 else 32 if r < 4 else 31 if r < 6 else None
                                    legal = d <= 0 and (d < 0 or X <= A)
                                    tests.append(dict(S=S, exponent_difference=d,
                                                      expected_S=expected, legal_x_le_a=legal,
                                                      physical=legal and expected == S))
                                row['physical_checks'] = tests
                                row['physical'] = any(z['physical'] for z in tests)
                                if row['physical']:
                                    counts['physical_counterexample_candidates'] += 1
                            candidates.append(row)
    result = dict(base_commit='07ac3e0c932e54fcd96b310e0990ab8513e0e84a',
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
                  counts=dict(counts), candidates=candidates,
                  coverage='All bounded A,t,J,eta residue solutions; not raw BF16 pairs',
                  raw_pair_sweep=False, gpu_runs=0)
    (ROOT/'normal45_reduction_results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'counts': counts, 'survivors': [r for r in candidates
                      if r['status'] == 'REQUIRES_PHYSICAL_INTERVAL_CHECK']}, indent=2))


if __name__ == '__main__':
    run()
