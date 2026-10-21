"""Check one supplied coefficient survivor, not the complete residue kernel."""
from fractions import Fraction
from hashlib import sha256
from math import gcd
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


def main():
    bounds = []
    for q, maximum_A, expected_j_cap, expected_t_max, safe_modulus_exp in [
            (15, 255, 42, 16, 15),
            (16, 255, 85, 4, 15),
            (17, 191, 127, 1, 13)]:
        # Exact nearest-integer rounding of maximum_A*2^q/3.
        lower, remainder = divmod(maximum_A * (1 << q), 3)
        maximum_D = lower + (remainder == 2)
        assert maximum_D // (1 << 16) == expected_j_cap
        upper_t = Fraction(1 << 34, 1 << (2 * q)) + Fraction(maximum_A ** 2, 1 << 16)
        assert expected_t_max < upper_t < expected_t_max + 1
        minimum_u = 47 - 2 * q
        assert min(minimum_u, q) == safe_modulus_exp
        bounds.append(dict(q=q, maximum_D=maximum_D, j_cap=expected_j_cap,
                           t_upper_bound=str(upper_t), t_max=expected_t_max,
                           minimum_u=minimum_u, safe_modulus_exp=safe_modulus_exp))

    q, A, epsilon, t, j = 16, 230, 1, 4, 51
    D = 5024427
    assert 3 * D == A * (1 << q) + epsilon
    assert gcd(A, D) == 1 and D % 2 == 1
    assert 1 <= j <= D // (1 << 16)
    assert (3 * j * A * A - epsilon * t) % (1 << 15) == 0
    reconstructed = t * (A * (1 << q) + epsilon) - 3 * j * A * A
    assert reconstructed == 52199424 == 3 * 531 * (1 << 15)
    assert 531 % 2 == 1
    rows = []
    for v in (0, 1):
        for S in (31, 32, 33):
            u = 16 + v + S - 2 * q
            X = Fraction(reconstructed, 3 * (1 << u))
            assert (u == 15 and X == 531) or (u > 15 and X.denominator > 1)
            rows.append(dict(v=v, S=S, u=u, reconstructed_X=str(X),
                             exclusion="X_EXCEEDS_255" if u == 15 else "X_NOT_INTEGER"))
    result = dict(status="PASS_SINGLE_SURVIVOR_AND_BOUND_CHECKS",
                  scope="Three class-bound constants and the supplied single survivor only; "
                        "the full residue kernel was not executed or independently enumerated.",
                  source_commit="2e7c2dae61ac9da85e889168694a459bfed13cd1",
                  reviewed_kernel_sha256=sha256((HERE.parent / "residue_kernel.py").read_bytes()).hexdigest(),
                  checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  bounds=bounds,
                  survivor=dict(q=q, A=A, D=D, epsilon=epsilon, t=t, j=j,
                                reconstructed_numerator=reconstructed,
                                factorization="3 * 531 * 2^15"),
                  reconstructions=rows, failures=[])
    (HERE / "r49_survivor_check_results.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=result["status"], reconstruction_count=len(rows), failures=[])))


if __name__ == "__main__":
    main()
