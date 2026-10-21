"""Limited independent integer checks for the p53 subnormal proof review.

This is not a raw-pair sweep or a substitute for the mathematical case proof.
Only the standard library is used. The prior analytic checker is not imported.
"""

from fractions import Fraction
from hashlib import sha256
from math import gcd, isqrt
from pathlib import Path
import json
import platform
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GRID = tuple(map(Fraction, (0, "1/2", 1, "3/2", 2, 3, 4, 6)))


def pow2(exponent):
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def nearest_even_integer(value):
    lower, remainder = divmod(value.numerator, value.denominator)
    twice = 2 * remainder
    return lower + int(twice > value.denominator or
                       (twice == value.denominator and lower % 2 == 1))


def bf16_value(code):
    exponent, fraction = divmod(code, 128)
    assert 0 <= code < 0x7F80
    if exponent == 0:
        return fraction * pow2(-133)
    return (128 + fraction) * pow2(exponent - 134)


def floor_log2(value):
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    if value < pow2(exponent):
        exponent -= 1
    assert pow2(exponent) <= value < pow2(exponent + 1)
    return exponent


def rne_precision(value, precision):
    if not value:
        return value
    exponent = floor_log2(value)
    quantum = pow2(exponent - precision + 1)
    return nearest_even_integer(value / quantum) * quantum


def canonical(value):
    value = min(value, Fraction(6))
    if value == 6:
        return (6, 1 << 32)
    for index, (lower, upper) in enumerate(zip(GRID, GRID[1:])):
        if lower <= value < upper:
            scaled = (value - lower) * (1 << 32) / (upper - lower)
            return (index, scaled.numerator // scaled.denominator)
    raise AssertionError("No canonical interval")


def main():
    # Fixed ties check both directions and the next-binade endpoint.
    assert rne_precision(Fraction(9, 8), 3) == 1
    assert rne_precision(Fraction(11, 8), 3) == Fraction(3, 2)
    assert rne_precision(Fraction(15, 8), 3) == 2

    boundary_codes = [1, 2, 3, 95, 96, 97, 127, 128, 191, 192, 193,
                      242, 255, 256, 257, 383, 384, 385, 446, 447, 448]
    scale_rows = []
    sample_rows = []
    for code in boundary_codes:
        a = bf16_value(code)
        units = nearest_even_integer((a / 6) / pow2(-149))
        assert 0 < units <= 1 << 23
        if code <= 255:
            A, q = code, 15
        elif code <= 383:
            A, q = code - 128, 16
        elif code <= 447:
            A, q = code - 256, 17
        else:
            A = q = None
        if code <= 447:
            epsilon = 3 * units - A * (1 << q)
            assert epsilon in (-1, 0, 1)
            assert (epsilon == 0) == (A % 3 == 0)
            assert units < 1 << 23
            if epsilon:
                assert units % 2 == 1 and gcd(A, units) == 1
        else:
            epsilon = None
            assert units == 1 << 23
        scale_rows.append(dict(a_code=code, A=A, q=q, D=units, epsilon=epsilon))
        x_codes = {0, 1, code // 2, max(0, code - 1), code}
        x_codes.update(x for x in [127, 128, 255, 256, 383, 384] if x <= code)
        if code == 242:
            x_codes.add(221)
        for x_code in sorted(x_codes):
            ratio = bf16_value(x_code) / (units * pow2(-149))
            exact = canonical(ratio)
            rounded = canonical(rne_precision(ratio, 53))
            assert exact == rounded
            sample_rows.append(dict(a_code=code, x_code=x_code,
                                    canonical=list(exact), p53_pass=True))

    # Independently construct the ten adjacent square brackets from (j,k),
    # rather than copying the displayed roots or residuals.
    bracket_rows = []
    for j, ks in [(1, range(1, 6)), (2, range(7, 12))]:
        for k in ks:
            target = k * (1 << 15)
            lower = isqrt(target // (3 * j))
            upper = lower + 1
            residuals = (3 * j * lower * lower - target,
                         3 * j * upper * upper - target)
            assert residuals[0] < -16 and residuals[1] > 16
            bracket_rows.append(dict(j=j, k=k, lower=lower, upper=upper,
                                     residuals=list(residuals)))

    odd_q16 = [(j, t, epsilon)
               for j in range(1, 6) for t in range(1, 5)
               for epsilon in (-1, 1) if (3 * j - epsilon * t) % 8 == 0]
    assert set(odd_q16) == {(1, 3, 1), (2, 2, -1), (3, 1, 1),
                            (4, 4, 1), (4, 4, -1), (5, 1, -1)}
    even_q16 = [(j, epsilon) for j in range(1, 6) for epsilon in (-1, 1)
                if (3 * j - epsilon) % 8 == 0]
    odd_q17 = [(j, epsilon) for j in range(1, 8) for epsilon in (-1, 1)
               if j % 2 and (3 * j - epsilon) % 8 == 0]
    assert even_q16 == odd_q17 == [(3, 1), (5, -1)]

    nonsquare_rows = []
    for label, modulus, lower_m, upper_m in [
            ("q16_even_A", 8192, 8, 29),
            ("q16_odd_A", 32768, 8, 29),
            ("q17", 8192, 30, 67)]:
        for m in range(lower_m, upper_m + 1):
            numerator = m * modulus - 1
            if numerator % 15:
                continue
            candidate = numerator // 15
            lower = isqrt(candidate)
            assert lower * lower < candidate < (lower + 1) ** 2
            nonsquare_rows.append(dict(case=label, m=m, value=candidate,
                                       lower=lower, upper=lower + 1))
    assert len(nonsquare_rows) == 5

    # Nontrivial negative control: the known subnormal p48 failure.
    witness_a, witness_x = bf16_value(242), bf16_value(221)
    witness_D = nearest_even_integer((witness_a / 6) / pow2(-149))
    witness_ratio = witness_x / (witness_D * pow2(-149))
    assert canonical(witness_ratio) != canonical(rne_precision(witness_ratio, 48))
    assert canonical(witness_ratio) == canonical(rne_precision(witness_ratio, 53))

    sources = ["AGENTS.md", "studies/analytic-denominator-20261021/analytic_proof.txt"]
    result = dict(
        status="PASS_LIMITED_CHECKS",
        source_commit="2e7c2dae61ac9da85e889168694a459bfed13cd1",
        scope="21 fixed scale boundaries; selected x codes only; ten brackets; "
              "40 q16 odd-A parity combinations; 24 additional parity combinations; "
              "five nonsquares; one p48 negative control. No raw-pair sweep.",
        environment=dict(python=sys.version.split()[0], platform=platform.system(),
                         libraries="Python standard library only"),
        source_sha256={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        scale_rows=scale_rows, sampled_pair_count=len(sample_rows), samples=sample_rows,
        q15_brackets=bracket_rows, q16_odd_A_mod8=odd_q16,
        q16_even_A_mod8=even_q16, q17_mod8=odd_q17,
        nonsquares=nonsquare_rows,
        negative_control=dict(a_code=242, x_code=221, D=witness_D,
                              exact=list(canonical(witness_ratio)),
                              p48=list(canonical(rne_precision(witness_ratio, 48))),
                              p53=list(canonical(rne_precision(witness_ratio, 53)))),
        failures=[])
    output = HERE / "p53_integer_check_results.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=result["status"], scale_count=len(scale_rows),
                          sampled_pair_count=len(sample_rows),
                          bracket_count=len(bracket_rows),
                          nonsquare_count=len(nonsquare_rows), failures=[])))


if __name__ == "__main__":
    main()
