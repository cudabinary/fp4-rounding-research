"""Publish residue witnesses for checking coverage without modular inversion."""
from pathlib import Path
import csv
import json
import math

ROOT = Path(__file__).resolve().parent


def build():
    rows = []
    for q, lo, hi, tmax in ((18, 128, 191, 9), (17, 192, 255, 16)):
        for A in range(lo, hi+1):
            D, rem = divmod(A << q, 3)
            D += rem == 2
            eps = 3*D-(A << q)
            if not eps:
                continue
            for t in range(1, tmax+1):
                for J in range(12, 24):
                    if t*2**J >= A*A + 2**(46-2*q):
                        continue
                    for eta in (0, 1):
                        L = 61+eta-J
                        u = L-2*q
                        c, M = 3*A*A, 2**u
                        g = math.gcd(c, M)
                        row = dict(q=q, A=A, D=D, epsilon=eps, t=t, J=J,
                                   eta=eta, L=L, u=u, gcd=g, j_cap=D//2**J,
                                   modulus='', residue='', status='GCD_EXCLUSION')
                        if eps*t % g == 0:
                            modulus = M//g
                            residue = eps*t//g*pow(c//g, -1, modulus) % modulus
                            row.update(modulus=modulus, residue=residue,
                                       status='RECORDED_RESIDUE_CLASS')
                        rows.append(row)
    with (ROOT/'normal45_branch_certificate.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({'certificate_branches': len(rows),
                      'source': 'Bounded coefficient conditions; no raw-pair sweep'}))


if __name__ == '__main__':
    build()
