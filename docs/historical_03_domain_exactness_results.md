# New domain result: removing the RN64-compatibility correction

**New result:** for all532,701,120 legal finite BF16 magnitude/amax pairs, D1 without B's final RN64 compatibility increment returns the same canonical base and32-bit SR threshold (stored in U64) as source A″, unchanged B and an independent integer-RNE64 oracle. No mismatch or required increment occurred. This extends old sample-level observations to the entire explicitly defined finite producer domain.

## Complete results

| Quantity | Main CPU result |
|---|---:|
| Legal magnitude pairs |532701120|
| Source A″ vs unchanged B disagreements |0|
| Source A″ vs independent U128-RNE oracle disagreements |0|
| D1 vs source A″ threshold/base disagreements |0|
| Compatibility guard eligible pairs (rem!=0 and J<24) |22535364|
| Actual RN64 compatibility increments |0|
| Per-amax rows |32639|
| Main CPU wall seconds |7.476410244|

The guard fraction over this uniformly enumerated domain is not an activation frequency or GPU branch counter. Most pairs involve widely separated exponents. The older model-input85–91% guard eligibility and this domain's4.23% eligibility have different denominators; no performance conclusion follows from comparing them.

The diagnostic CPU D1 variant reports guard eligibility through an optional output pointer even though it does not increment T. That instrumentation is not part of its numerical output contract or a performance optimization. Calling without diagnostics permits removal of now-unused arithmetic in ordinary CPU code; no new GPU codegen is measured.

## Why the uncorrected formula is exact real-rational floor

Write |x|=M_x*2^(e_x-23), s=M_s*2^(e_s-23), with24-bit normalized integers, including leading-bit normalization of subnormals. Let d=e_x-e_s. For the selected interval [L,H], let S=33,32 or31 so that2^S=2^32/(H-L). With L2=2L, define

  N=M_x*2^(d+S)
  Lscaled=L2*2^(S-1)
  T_real=floor(N/M_s)-Lscaled.

B's uncorrected quotient path computes exactly this formula. For nontrivial bins, d+S>=0 and N<2^58, so U64 arithmetic suffices; power-of-two scales use an equivalent shift. For d<-33 the ideal threshold is0; for saturation it is2^32. Integer bin comparisons use exact rational boundaries. These are existing B arithmetic identities, not newly invented division.

The generic B compatibility step adds1 when rounding the first real ratio to RN64 crosses a threshold-floor boundary. The exhaustive result establishes that **no such crossing occurs on the full BF16/derived-scale joint domain**, so that step is unnecessary there.

This is a complete finite-domain equivalence certificate. After the sweep, a complementary analytic no-carry argument was derived for normal derived F32 scales and checked by independent R within the same review. It is not a proof that the sufficient conditions are minimal. No arbitrary scale or broader CUDA API is silently included.

## Analytic mechanism, and where finite verification remains necessary

The complete derivation is preserved in `REPRO/ANALYTIC_LEMMA_DRAFT.md`, the actual document examined by R. Despite its historical draft filename, R's final review accepts the stated normal-scale argument. It is a post-sweep explanation for the frozen question, not a held-out prediction or proof-assistant certificate.

Normalize a positive BF16 group maximum as a=A*2^(ea-7), with integer A in [128,255]. When s=RN32(a/6) is normal, its 24-bit significand D obeys

  3D=A*2^q+epsilon,
  q=18 for A<192, otherwise q=17,
  epsilon in {-1,0,1}.

This restricted divisor is the relevant property. “BF16 has fewer bits” by itself does not establish the result. Normalize x=X*2^(ex-7), X in [128,255], and let N=X*2^L be the exact scaled numerator before threshold-bin subtraction. A hypothetical rounding carry requires a small positive gap j=D-(N mod D), with j*2^J<=D, 20<=J<=23 and L+J=69+h for h in {0,1}. Hence L>=46 and j<=15.

For epsilon=0, D and N are divisible by 2^q, so a positive gap this small is impossible. For epsilon=+/-1, write ceil(N/D)=K*2^q+3*epsilon*j. Substitution forces K+3jA to be a positive multiple of 2^q. For q=18 it is at most 74131, below 2^18: contradiction. For q=17 the only possible multiple is 2^17, forcing J=20 and

  3jA^2 = epsilon (mod 32768), with j<=10.

Odd-square residues leave j=3 for epsilon=+1 or j=5 for epsilon=-1. The former would require (3A-1)(3A+1) divisible by 2^15 although both positive factors are below 766; their gcd is 2, so this is impossible. The latter forces A^2=37137, strictly between 192^2 and 193^2. Both cases fail. Thus the normal-scale branch cannot require the compatibility increment. The derivation includes exponent, selected-bin, quotient and tie bounds; the full witness is preferable to using this abbreviated argument as an unrestricted theorem.

For BF16 amax codes 1..447, the derived scale is subnormal and the +/-1 significand invariant cannot be copied unchanged. These cases plus the all-zero pair are covered by **100,576 complete finite checks**, already included in the one main sweep. Normal-scale pairs account for the remaining **532,600,544** checks. No subnormal case was discarded by exponent symmetry, and no second numerical experiment was added.

The strongest supported description is therefore: **normal-scale analytic no-carry lemma plus complete finite verification of the subnormal/zero branch, corroborated by complete independent-reference checking of the entire legal pair domain**. It is not an all-input analytic theorem or a new generic double-rounding framework.

## Reference independence

The A″ threshold function was extracted from the actual full source and CPU-adapted only by replacing device qualifiers/bitcast/clz intrinsics. Original B arithmetic was likewise copied. D1 removes its final compatibility increment; it is a CPU-only candidate, not a new CUDA kernel.

The oracle separately decodes exact F32 fractions, uses U128 integer division to round the ratio to53 significant bits with ties-to-even, then evaluates its dyadic FP4 threshold. It does not use host FP division or B's correction criterion to obtain RN64. Scale bits come from an independent Python Fraction/RNE32 packer. A/B/D1/oracle are nevertheless implementations of a common written specification; common specification errors and compiler faults are not excluded by agreement alone.

The explicit per-amax CSV and CPU source show the full x0..amax traversal. COVERAGE_RECEIPT.json checks all32639 amax rows once and their counts, with the all-zero case added separately. There is no symmetry reduction over exponents or unchecked extrapolation. Full negative signs are justified by identical magnitude computation and unchanged sign bit, with signed smoke checks; they are not counted as newly executed pair rows.

## Counterexample outside the certificate

The preserved arbitrary-F32 witness has x_bits1073733634 and scale_bits1065353217. A/B/oracle return4286578689; D1 returns4286578688. Its x is not an exact BF16 expansion. Thus D1 is not a replacement for the standalone helper's entire generic F32 contract.

This one witness proves nonuniversality of correction removal, but does not prove that the maximal valid domain requires exactly the joint BF16/amax conditions. Necessity/minimality of those assumptions is unresolved.

## Composition and a limited corollary

On this domain, equal canonical base/T, sign and generated scale preserve every U<T decision for every logical32-bit word U. Unchanged packet addresses/prefix policy then preserve the scalar decisions, requests, packed codes and deterministic consumer inputs under the source semantics. This is a compositional argument, not a new GPU output test or a CUDA warp/barrier proof.

Because T equals the ideal-rational floor at32 random bits, for an unsaturated normalized magnitude y=|x|/s within the chosen FP4 interval:

  - (H-L)/2^32 < E[q]-y <= 0,

where q is the selected exact FP4 magnitude and U is uniform over all U32 words. The familiar limited-random-bit downward bias bound applies; this task did not invent it. Saturation, final BF16 multiplication/conversion, residual addition, model PPL and statistical independence/correlation of an actual counter stream need separate analysis. “Exactly unbiased real SR” is not claimed.

## What cost is actually removable

For this domain, the caller-side compatibility-only work can be omitted: remainder reconstruction if otherwise unused, normalized quotient exponent/J calculation, shifted gap comparison and conditional increment/carry dependency. The exact U64 quotient and its compiler helper are **not** eliminated. No percentage of total B cost or H100 latency is assigned to the removed work. Diagnostic instrumentation retains some work for counting; no CPU D1 speed benchmark was performed.

No CUDA D1 cubin exists, no D1 CUDA-output correctness gate ran, and D1 latency/registers/spills remain UNKNOWN. In particular there is no evidence yet that D1 beats strong FP64 A″. Existing26.24% remains a separate earlier implementation effect.

## Identity receipt correction

The initial generation receipt mistakenly labeled the LF in-memory source hash as source_sha256; Windows stored CRLF. The at-run receipt is preserved, and CPU_SOURCE_BUILD_MANIFEST.json now distinguishes normalized-LF digest from the actual compiled-file digest15a9ecbc2bff426a01a2814d4497400fc23fcedea2e92f529c3af1e239cbad02. Source, executable and experiments were not modified or repeated. This is an administrative hash-label correction, not a repaired numerical test. Raw-file and executable digests added after execution establish current identity; they are not retroactive at-run cryptographic attestations.
