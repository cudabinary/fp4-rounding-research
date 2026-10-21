# Post-sweep analytic derivation for the same frozen D1/D2 question

Status: argument for independent R scrutiny, not another experiment, candidate or prospective prediction. It was derived after observing the exhaustive result. It must not be accepted if the algebra has a gap.

## Claim

For a finite BF16 input x and a **normal F32 scale** s=RN32(a/6) generated from a positive finite BF16 a, the generic B RN64-compatibility increment cannot fire on the nonsaturated nonzero path. This suffices for the actual |x|<=a producer; the argument need not claim the sufficient domain is maximal.

Write normalized a=A*2^(ea-7), A∈[128,255]. A is an integer even when its significant precision is below8bits. A normal derived scale has24-bit significand D satisfying

  3D=A*2^q+epsilon,
  q=18 for128<=A<192, q=17 for192<=A<=255,
  epsilon∈{-1,0,1}.

Reason: s=a/6 rounded to24bits; its exponent is ea-3 or ea-2 respectively, and rounding A*2^q/3 produces an integer with error0 or±1/3. The BF16 spacing is much larger than a rounding-interval rollover, so this exponent split has no hidden near192 case; A=192 is exact.

Normalize the BF16 x as X*2^(ex-7), X∈[128,255]. BF16 subnormal x can also be normalized to such an8-bit integer (with trailing zeros), so this representation does not exclude it.

Let d=ex-es and E=d-h be the exact exponent of x/s, where h∈{0,1} indicates whether X*2^16<D. For the FP4 interval define S=33,32,31 as before; N=X*2^L with L=16+d+S. B uses J=53-E-S. Thus

  L+J=69+h.

## Assume a carry for contradiction

If a carry fires, rem>0 and j=D-rem is a positive integer satisfying

  j*2^J<=D.

For a nonsaturated FP4 interval, J>=20. Also J<24 is necessary for this inequality because D<2^24. Therefore20<=J<=23, L>=46 and1<=j<=15.

Set Q=ceil(N/D), so N+j=QD. From the selected interval and S,0<Q<=2^34 (S33 uses ratio<2; S32 ratio<4; S31 ratio<6). These are bounds on the absolute scaled quotient before subtracting the bin offset.

### epsilon=0

D and N are both divisible by2^q (L>=46>q), so j=QD-N is divisible by2^q. This contradicts0<j<=15.

### epsilon=±1

Multiply N+j=QD by3 and reduce modulo2^q:

  Q=K*2^q+3*epsilon*j

for an integer K. Substitution and division by2^q give

  3X*2^(L-q)=KA*2^q+epsilon*(K+3jA).

Since L>=46>=2q, K+3jA is a positive multiple of2^q. Positivity is justified because a carry-eligible interval has E>=-3 and scaled quotient Q>=2^30, whereas3j<=45; hence K>0.

If q=18, K<=65536 and A<=191, so

  0<K+3jA<=65536+3*15*191=74131<2^18,

a contradiction.

If q=17, A<=255 implies D<255*2^17/3+1 and therefore j<=10.
Also K<=131072, so

  0<K+3jA<=131072+3*10*255=138722<2*2^17.

Its only possible multiple is2^17:

  K+3jA=2^17.

Consequently

  Q=2^34-3jA*2^17+3*epsilon*j > 2^33.

For S33 this forces E=0; for S32 and S31 the interval has E=1 and E=2 respectively. Thus in all cases J=20, L=49+h∈{49,50}. Put r=L-34∈{15,16}. The substituted equation becomes

  3X*2^r=A*2^17+epsilon-3jA^2.

Reducing modulo2^15:

  3jA^2 ≡ epsilon (mod32768).

A must be odd. Since an odd square is1mod8, j=3 if epsilon=+1 or j=5 if epsilon=-1 (j<=10).

- j=3 requires (3A)^2≡1 mod2^15. Equivalently, (3A-1)(3A+1) is divisible by2^15. For odd3A these factors are consecutive even numbers with gcd2, so one has exactly one factor2 and the other must be divisible by2^14. Both are positive and below766, so neither can be. This is the ordinary roots-of-unity fact in an elementary form.
- j=5 requires15A^2+1=t*32768. For192<=A<=255,17<=t<=29. Modulo15,8t≡1, so t≡2mod15 and the sole option is17. It would require A^2=37137, strictly between192^2=36864 and193^2=37249. Impossible.

Every case contradicts a carry. The normal-scale branch is therefore correction-free under the stated assumptions and existing B derivation of the carry condition.

## What this argument does not prove

- It relies on the already-derived generic B RN64 carry condition being correct; the independent ratio oracle/full source comparisons separately support that numerical connection.
- Derived subnormal scales have normalized rounding error epsilon times a power of two, so the ±1 invariant cannot be copied to them. Their actual legal subdomain (amax codes1..447 plus all-zero) remains covered by the existing complete enumeration:1+447*450/2=100576 pairs, with no new run.
- It does not prove a maximal domain, generic arbitrary-F32 compatibility, CUDA compiler correctness, or a GPU performance gain.
- Integer congruence, round-to-nearest analysis and finite validation are established techniques. Novelty, if any, is this specific scale-generation invariant and resulting removal condition, not invention of those mathematical tools.

## Connection to the generic RN64 carry condition

For a nonsaturated exact ratio r=|x|/s with exponent E and selected interval width2^(32-S), FP4 threshold boundaries occur at multiples of2^-S. Subtraction of the endpoint and division by the power-of-two gap are exact for already-rounded z, as in the preceding audit.

Let N/D=r*2^S and assume rem=N modD is nonzero. The next lattice boundary is Q*2^-S with Q=ceil(N/D), at distance

  (Q-N/D)*2^-S = j/(D*2^S).

All such lattice boundaries are binary64-representable; with E+S<=33 they have many zero low significand bits, including an even tie bit. RN64 crosses that boundary precisely when the distance is at most half the binary64 spacing below it,2^(E-53). Thus

  j/(D*2^S)<=2^(E-53) iff j*2^(53-E-S)<=D.

Equality rounds to the lattice endpoint by ties-to-even. If rem=0, the ratio is already on that boundary and no compatibility increment is needed. With D<2^24 and j>=1, J>=24 cannot satisfy this inequality. This derives the existing B criterion rather than treating it as a newly invented rule.

FP4 bin-cut boundaries themselves cannot change the canonical base under the first rounding for the F32 operands in this finite domain: an unequal ratio near a nonzero dyadic cut has an integer-ratio separation far larger than a binary64 half-ULP. Exact-cut equality is preserved. The complete independent ratio-oracle comparison separately checks canonical base on all legal pairs; no general formal proof for every arbitrary-F32 API call is substituted for that evidence.
