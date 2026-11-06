# Empty-mask audit

Source: research commit `592566b4c5f39e261c676eb034139a974e9cdfd5`; original files preserved. This audit read existing case-level records and did not rerun SAM inference.

## Finding

No empty initial or shifted predictions were observed across the 1,316 unique study images (213 development, 851 internal testing, 252 external testing).

| Cohort | Initial predictions | Initial empties (direct flag) | Shifted predictions | Shifted empties (logical determination) |
|---|---:|---:|---:|---:|
| Development | 213 | 0 | 852 | 0 |
| Internal testing | 851 | 0 | 3,404 | 0 |
| External testing | 252 | 0 | 1,008 | 0 |
| Total | 1,316 | 0 | 5,264 | 0 |

## Evidence and inference boundaries

`initial_mask_empty` is stored for every scored image and equals zero for all images. The records do not store a per-shift empty flag or the foreground pixel count. However, every one of the 5,264 initial-to-shifted Dice values is strictly greater than zero. Given a nonempty initial mask, a positive Dice requires the corresponding shifted mask to be nonempty. Thus the absence of shifted empty predictions can be determined from the stored values, without assuming that a reference Dice of zero means an empty prediction. The minimum observed consistency values are retained in the JSON audit.

The development image `bus_0905-l` has reference Dice 0 but `initial_mask_empty=0`: this is a nonempty prediction with no reference overlap, not an empty prediction.

The archived original-image rerun has the same 1,316 image identities, initial-empty flags and shifted consistency values, exactly. That archived rerun is prior evidence, not an image rerun performed by this audit.

## Consequence for Method B

The code defines Dice(empty, empty)=1. If the initial and all four shifted masks were empty, Method B would assign risk zero although the nonempty-reference Dice would be zero. This is a possible failure mode of the rule, but it did not occur in these records. No sensitivity analysis for observed empty-empty pairs is necessary, because there are no affected cases. A future implementation may explicitly flag empty initial predictions for review; that would be a prospective rule change and must not be presented as the locked analysis used here.

## Suggested manuscript wording

For mask consistency, Dice was set to 1 when both predictions were empty. No initial prediction was empty in the 1,316 study images. All 5,264 initial-to-perturbed Dice values were strictly positive, which also establishes that no perturbed prediction was empty; consequently, the empty-empty convention did not affect the reported scores or review decisions.
