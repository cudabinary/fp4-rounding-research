# Actual input and generated-scale domain

## Source/API facts

The sealed A/A″/B sources define INPUT_BF16=true. input_value takes a pointer declared float*, but reads it as unsigned short* and expands the16-bit word by shifting left16. The executed packed_lazy1_fp4 FP4 path therefore consumes **BF16 storage**, not an arbitrary F32 activation buffer. cuda_driver.py uploads producer_bf16 directly; the independent reference decodes those U16 bits as BF16.

Do not infer wider input precision from the pointer's spelling. The standalone threshold helper accepts F32 x/scale, so its generic arithmetic domain is wider than the actual packed producer's loading contract.

All96 preserved input archives were read without model execution: producer_bf16/residual_bf16 are U16, producer values are finite BF16, total34,560,000 values. They contain3,490 distinct magnitude codes and1,391 distinct group-amax codes. These counts are input inventory, not a new family of native measurements. The full finite domain below is much larger than those observed codes.

## Legal magnitude pairs

Let a be a positive finite BF16 magnitude code in1..0x7f7f (32,639 codes), and b an element magnitude in0..a inclusive. Positive finite encodings are numerically ordered. Every pair is realizable in a group32, e.g. [amax,x,0,...,0]. Conversely every finite BF16 group supplies such a pair for each element. This avoids testing arbitrary independent F32 scales as if they came from the producer.

Define s=RN32(value(a)/6). If all group magnitudes are0, use the source fallback2^-42. All scales are positive finite under gradual underflow; the minimum is F32 bits0x00002aab. Early amax values include F32-subnormal scales and were not excluded.

The finite magnitude-pair count is

  1 + sum(a+1, a=1..32639) = 532,701,120.

The extra1 is the all-zero group case. Both signs are recovered by source sign/magnitude separation; -0 retains the sign bit. This is a proof of symmetry plus fixed signed smoke checks, not an additional exhaustive enumeration of negative rows.

## Scale construction

The source uses __fdiv_rn(BF16-magnitude-expanded-to-F32,6.f), with unchanged zero fallback. An independent Fraction/ties-to-even binary32 packer generated every scale bit in SCALE_BITS.bin. The CPU sweep checked compiled F32 scale division against those bits once per amax. No scale mismatch occurred.

## Exclusions

NaN/infinity, nonpositive/invalid scale, arbitrary-F32 producer input, a scale unrelated to the group's amax, FTZ/DAZ changes, other scale policies, altered RNG/prefix/packing and arbitrary n/tail implementation semantics are not certified by this finite pair result. Element-tail zero padding does not create a new scalar magnitude, but no new CUDA synchronization/packing correctness is proved.

The certificate uses a sufficient joint domain; it does **not** establish that every listed condition is necessary or identify the maximal domain. In particular, no claim is made that BF16 precision alone is insufficient for every possible scale; that broader domain was not exhaustively tested here.
