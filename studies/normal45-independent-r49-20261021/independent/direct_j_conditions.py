"""Direct, complete enumeration of the small R49 reduced conditions.

This program reads only its own pre-run protocol. It does not generate j by
an inverse or gcd algorithm and does not enumerate raw BF16 input pairs.
"""

import csv
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from time import perf_counter


OUT = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def nearest_integer(numerator, denominator):
    lower, remainder = divmod(numerator, denominator)
    correction = 2 * remainder > denominator
    if 2 * remainder == denominator:
        correction = lower % 2 == 1
    return lower + int(correction)


def ratio_exponent(numerator, denominator):
    estimate = numerator.bit_length() - denominator.bit_length()
    if estimate >= 0:
        below = numerator < denominator * (1 << estimate)
    else:
        below = numerator * (1 << -estimate) < denominator
    return estimate - int(below)


def rounded_rational(numerator, denominator, precision):
    exponent = ratio_exponent(numerator, denominator)
    shift = precision - 1 - exponent
    if shift >= 0:
        rounded = nearest_integer(numerator * (1 << shift), denominator)
        return Fraction(rounded, 1 << shift)
    rounded = nearest_integer(numerator, denominator * (1 << -shift))
    return Fraction(rounded * (1 << -shift))


def canonical(value, grid, b):
    clipped = min(value, grid[-1])
    if clipped == grid[-1]:
        return [len(grid) - 2, 1 << b]
    for interval in range(len(grid) - 1):
        low, high = grid[interval:interval + 2]
        if low <= clipped < high:
            scaled = (clipped - low) * (1 << b) / (high - low)
            return [interval, scaled.numerator // scaled.denominator]
    raise ValueError("Value outside the nonnegative canonical domain")


def physical_X_bounds(q, A, v):
    if v == 0:
        return 1, A if q == 15 else 255
    return 128, A if q == 15 + v else 255


def main():
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    protocol_path = OUT / "pre_run_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    config = protocol["contract"]
    environment = dict(python_version=platform.python_version(),
                       implementation=sys.implementation.name,
                       operating_system=platform.platform(),
                       integer_arithmetic="arbitrary precision",
                       dependencies="Python standard library only")
    binding = dict(started_utc=started,
                   source_base=protocol["verified_start_head"],
                   protocol_sha256=digest(protocol_path),
                   implementation_sha256=digest(Path(__file__)),
                   environment=environment)
    save_json("run_start.json", binding)

    grid = [Fraction(x) for x in config["grid"]]
    b = config["b"]
    precision = config["working_precision"]
    minimum_J = precision - 33
    carry_denominator = 1 << minimum_J
    failures = []
    declared_counters = [
        "A_values", "coefficient_t_branches", "epsilon_zero_coefficient_t_branches",
        "empty_carry_range_coefficient_t_branches", "congruence_checks",
        "epsilon_zero_divisibility_checks", "diagnostic_epsilon_zero_congruence_hits",
        "nonzero_epsilon_congruence_rejections", "coarse_survivors",
        "full_equation_numerator_evaluations", "reconstruction_checks",
        "canonical_comparisons", "rounding_helper_controls"]
    count = Counter({key: 0 for key in declared_counters})
    class_results = []
    survivors = []
    exact_scale_anomalies = []

    check_fields = ["q", "A", "t", "j", "m", "residue", "status"]
    branch_fields = ["q", "A", "D", "epsilon", "t", "t_max", "m",
                     "j_cap", "checks", "survivor_j", "status"]
    with (OUT / "all_congruence_checks.csv").open("w", encoding="utf-8", newline="") as checks_file, \
         (OUT / "all_coefficient_t_branches.csv").open("w", encoding="utf-8", newline="") as branches_file:
        checks_writer = csv.DictWriter(checks_file, fieldnames=check_fields)
        branches_writer = csv.DictWriter(branches_file, fieldnames=branch_fields)
        checks_writer.writeheader()
        branches_writer.writeheader()
        for specification in config["classes"]:
            q = specification["q"]
            before = count.copy()
            modulus_cases = []
            for v in specification["v"]:
                for S in config["S_values"]:
                    u = 16 + v + S - 2 * q
                    modulus_cases.append(dict(v=v, S=S, u=u, m=min(u, q)))
            safe_m = min(item["m"] for item in modulus_cases)
            M = 1 << safe_m
            observed_t_maxima = set()
            maximum_D = maximum_cap = 0
            A_epsilon_counts = Counter()
            for A in range(specification["A_min"], specification["A_max"] + 1):
                D = nearest_integer(A * (1 << q), 3)
                epsilon = 3 * D - A * (1 << q)
                cap = D // carry_denominator
                # The strict upper rational bound is represented over 65536.
                upper_numerator = (1 << (34 - 2 * q)) * carry_denominator + A * A
                t_max = (upper_numerator - 1) // carry_denominator
                observed_t_maxima.add(t_max)
                maximum_D = max(maximum_D, D)
                maximum_cap = max(maximum_cap, cap)
                A_epsilon_counts[str(epsilon)] += 1
                count["A_values"] += 1
                if epsilon not in (-1, 0, 1) or not 0 < D < 1 << 23:
                    failures.append(dict(kind="SCALE_IDENTITY_FAILURE", q=q, A=A,
                                         D=D, epsilon=epsilon))
                for t in range(1, t_max + 1):
                    count["coefficient_t_branches"] += 1
                    if epsilon == 0:
                        count["epsilon_zero_coefficient_t_branches"] += 1
                    local_survivors = []
                    for j in range(1, cap + 1):
                        residue = (3 * j * A * A - epsilon * t) % M
                        count["congruence_checks"] += 1
                        if epsilon == 0:
                            count["epsilon_zero_divisibility_checks"] += 1
                            if residue == 0:
                                count["diagnostic_epsilon_zero_congruence_hits"] += 1
                            if j % (1 << q):
                                status = "EPS0_DIVISIBILITY_REJECT"
                            else:
                                status = "EPS0_NOT_EXCLUDED"
                                anomaly = dict(q=q, A=A, D=D, t=t, j=j)
                                exact_scale_anomalies.append(anomaly)
                                failures.append(dict(kind="EXACT_SCALE_DIVISIBILITY_ANOMALY", **anomaly))
                        elif residue:
                            status = "CONGRUENCE_REJECT"
                            count["nonzero_epsilon_congruence_rejections"] += 1
                        else:
                            status = "COARSE_SURVIVOR"
                            count["coarse_survivors"] += 1
                            local_survivors.append(j)
                            survivors.append(dict(q=q, A=A, D=D, epsilon=epsilon,
                                                  t=t, j=j, m=safe_m,
                                                  v_values=specification["v"]))
                        checks_writer.writerow(dict(q=q, A=A, t=t, j=j, m=safe_m,
                                                    residue=residue, status=status))
                    if cap == 0:
                        branch_status = "EMPTY_CARRY_RANGE"
                        count["empty_carry_range_coefficient_t_branches"] += 1
                    elif epsilon == 0:
                        branch_status = "EXACT_SCALE_DIVISIBILITY_EXCLUSION"
                    elif local_survivors:
                        branch_status = "CONTAINS_COARSE_SURVIVOR"
                    else:
                        branch_status = "ALL_J_FAIL_CONGRUENCE"
                    branches_writer.writerow(dict(q=q, A=A, D=D, epsilon=epsilon,
                                                  t=t, t_max=t_max, m=safe_m, j_cap=cap,
                                                  checks=cap,
                                                  survivor_j=";".join(map(str, local_survivors)),
                                                  status=branch_status))
            class_results.append(dict(q=q, A_min=specification["A_min"],
                                      A_max=specification["A_max"],
                                      v_values=specification["v"],
                                      modulus_cases=modulus_cases, safe_m=safe_m,
                                      observed_t_maxima=sorted(observed_t_maxima),
                                      maximum_D=maximum_D, maximum_j_cap=maximum_cap,
                                      A_epsilon_counts=dict(A_epsilon_counts),
                                      counts={key: count[key] - before[key]
                                              for key in declared_counters}))

    reconstructions = []
    physical_candidates = []
    counterexamples = []
    for candidate in survivors:
        q, A = candidate["q"], candidate["A"]
        D, epsilon = candidate["D"], candidate["epsilon"]
        t, j = candidate["t"], candidate["j"]
        B = t * (A * (1 << q) + epsilon) - 3 * j * A * A
        count["full_equation_numerator_evaluations"] += 1
        for v in candidate["v_values"]:
            for S in config["S_values"]:
                L = 16 + v + S
                u = L - 2 * q
                divisor = 3 * (1 << u)
                X, remainder = divmod(B, divisor)
                count["reconstruction_checks"] += 1
                low, high = physical_X_bounds(q, A, v)
                row = dict(candidate=candidate.copy(), v=v, S=S, L=L, u=u,
                           numerator=B, divisor=divisor, X_floor=X,
                           X_remainder=remainder, physical_X_min=low,
                           physical_X_max=high)
                if B <= 0:
                    row["status"] = "NONPOSITIVE_X"
                elif remainder:
                    row["status"] = "NONINTEGER_X"
                elif not low <= X <= high:
                    row["status"] = "BF16_X_RANGE_EXCLUSION"
                else:
                    numerator = X * (1 << (16 + v))
                    ratio = Fraction(numerator, D)
                    a_units = A * (1 << (q - 15))
                    x_units = X * (1 << v)
                    row.update(X=X, a_minimum_units=a_units, x_minimum_units=x_units,
                               a_code=A + 128 * (q - 15), x_code=X + 128 * v,
                               ratio_numerator=numerator, ratio_denominator=D)
                    if x_units > a_units:
                        row["status"] = "X_EXCEEDS_A"
                    elif ratio >= 6:
                        row["status"] = "SATURATED_RATIO_EXCLUSION"
                    else:
                        actual_S = 33 if ratio < 2 else 32 if ratio < 4 else 31
                        row["actual_S"] = actual_S
                        if actual_S != S:
                            row["status"] = "INTERVAL_WIDTH_EXCLUSION"
                        else:
                            exponent = ratio_exponent(numerator, D)
                            J = precision - exponent - S
                            N_remainder = (X * (1 << L)) % D
                            actual_j = D - N_remainder
                            exact = canonical(ratio, grid, b)
                            rounded = canonical(rounded_rational(numerator, D, precision), grid, b)
                            count["canonical_comparisons"] += 1
                            carry = j * (1 << J) <= D
                            row.update(E=exponent, J=J, actual_j=actual_j,
                                       N_remainder=N_remainder, carry=carry,
                                       exact_canonical=exact, rounded_canonical=rounded)
                            if N_remainder == 0 or actual_j != j or J < minimum_J:
                                failures.append(dict(kind="RECONSTRUCTION_CONSISTENCY_FAILURE", row=row.copy()))
                            if carry != (exact != rounded):
                                failures.append(dict(kind="ROUNDING_CARRY_DISAGREEMENT", row=row.copy()))
                            physical_candidates.append(row.copy())
                            if exact != rounded:
                                row["status"] = "ACTUAL_R49_COUNTEREXAMPLE"
                                counterexamples.append(row.copy())
                            else:
                                row["status"] = "EXACT_CARRY_GUARD_EXCLUSION"
                count["reconstruction_status_" + row["status"]] += 1
                reconstructions.append(row)

    # Independent helper controls; these do not assert any enumeration outcome.
    controls = [
        dict(n=9, d=8, p=3, expected=Fraction(1)),
        dict(n=11, d=8, p=3, expected=Fraction(3, 2)),
        dict(n=15, d=8, p=3, expected=Fraction(2)),
        dict(n=3, d=16, p=3, expected=Fraction(3, 16))]
    for control in controls:
        actual = rounded_rational(control["n"], control["d"], control["p"])
        count["rounding_helper_controls"] += 1
        if actual != control["expected"]:
            failures.append(dict(kind="ROUNDING_HELPER_CONTROL_FAILURE",
                                 input={k: str(v) for k, v in control.items()}, actual=str(actual)))

    if failures:
        verdict = "INTERNAL_CHECK_FAILURE_PRESERVED"
    elif counterexamples:
        verdict = "R49_COUNTEREXAMPLE_FOUND"
    elif exact_scale_anomalies:
        verdict = "EXACT_SCALE_ANOMALY_PRESERVED"
    else:
        verdict = "NO_R49_COUNTEREXAMPLE_IN_COMPLETE_REDUCED_CONDITIONS"
    result = dict(schema="independent-r49-direct-j-result-v1", verdict=verdict,
                  source_base=binding["source_base"], binding=binding,
                  ended_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=perf_counter() - timer,
                  method="Direct j substitution for every relaxed A,t,j; no inverse/gcd candidate generator",
                  proof_kind="Analytic coverage plus complete finite reduced-condition enumeration",
                  raw_BF16_pairs_enumerated=False, counts=dict(count),
                  minimum_J=minimum_J, classes=class_results,
                  coarse_survivors=survivors, reconstructions=reconstructions,
                  physical_candidates=physical_candidates, counterexamples=counterexamples,
                  exact_scale_anomalies=exact_scale_anomalies, failures=failures,
                  limitations="Prior exposure is disclosed in the protocol. This is a new implementation and run, "
                              "not a blind audit, proof-assistant proof, normal-scale certificate, or GPU evidence.")
    result["complete_ledgers"] = {
        name: dict(bytes=(OUT / name).stat().st_size, sha256=digest(OUT / name))
        for name in ["all_coefficient_t_branches.csv", "all_congruence_checks.csv"]}
    save_json("independent_results.json", result)
    print(json.dumps(dict(verdict=verdict, counts=dict(count), classes=class_results,
                          coarse_survivors=survivors, reconstructions=reconstructions,
                          failures=failures), indent=2))


if __name__ == "__main__":
    main()
