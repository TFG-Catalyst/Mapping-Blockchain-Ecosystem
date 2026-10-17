# S2-05: Normalized edge weights using Jaccard similarity

**Sprint:** 2 
**Owner:** Rodrigo 
**Script:** `src/jaccard_weights.py` 
**Output:** `data/processed/edges_jaccard.csv`

## 1. Why normalize

`shared_voters.py` counts the number of wallets that voted in both DAOs. Two large DAOs share many voters just because they are large, so the raw count mixes two things: community size and the real overlap between them. 

Jaccard similarity divides the shared voters by the size of both communities together:

```
jaccard (A,B) = [voters (A) ∩ voters (B)] / [voters (A) ∪ voters (B)]
This can also be expressed as:
jaccard (A,B) = [shared_voters] / [voters (A) + voters (B) - shared_voters]
```


## 2. Population

- Voter sets are derived from `votes_clean.csv`, the same file used by `edge_generator.py`. 
- Wallets voting in more than `max_daos = 100` DAOs are removed, as agreed by the group.
- Edges (numerator) are rebuilt inside the script with the same functions and threshold as `edge_generator.py`, so numerator and denominator always come from the same filtered votes.

**Open decision: single-DAO voters in the denominator** (`COUNT_SINGLE_DAO_VOTERS`). Wallets voting in only one DAO never create edges, so `edge_generator.py` drops them. They are still members of that DAO's community.

| Option | DAO size counts | Effect |
| :-- | :-- | :-- |
| `True` (default, proposed) | All voters with ≤ 100 DAOs | Jaccard reflects the real community size |
| `False` | Only voters with 2..100 DAOs | Measures overlap among cross-DAO voters only; inflates small overlaps |

Example: A has 10 voters and B has 6; only 4 of them vote anywhere else, and those 4 are shared. With `True`, Jaccard = 0.33. With `False`, both DAOs shrink to those 4 voters and Jaccard = 1.0, as if A and B had identical communities. The group should confirm the choice.

## 3. Validation

A single function, `validate_results`, runs three parts:

1. **Logic check on every edge:** DAO size present, `shared_voters ≤ min(voters_A, voters_B)`, `union ≥ max(voters_A, voters_B)`, `0 < jaccard ≤ 1`.
2. **Hand recalculation of representative pairs:** the edge with the most shared voters, the highest and lowest Jaccard, and 5 random edges (seed 42). For each, shared voters and union are recomputed directly with Python sets and compared with the table.
3. **Comparison with `edges.csv`:** if the file exists, edge count and total weight must match the recomputed edges; otherwise it prints a warning because the file was generated with another threshold.

Parts A and B catch different errors. A wrong shared count that is still plausible (for example 5 instead of 4 for a DAO of 6 voters) passes A and is caught by B.


## 4. Results on the full dataset (run 2026-10-13, max_daos = 100)

**Validation.** All global checks gave 0 failing edges. The 8 representative pairs (strongest by count, highest and lowest Jaccard, 5 random) match their recomputation with sets. The 576,861 recomputed edges and their total weight (4,503,001) match the `edges_max100.csv` generated independently by Carlos for S2-04, so both analyses use the same graph.

**Distribution of Jaccard** (576,861 edges): median 0.00098, mean 0.035, 90th percentile 0.02, maximum 1.0. Most relationships are very weak in proportional terms; the mean is far above the median because of a small group of very high values.

**Rank agreement.** The Spearman correlation between `shared_voters` and `jaccard` is 0.20, so the two measures order the edges very differently. This is the starting point for S2-06.

**Examples that show the size effect**

| Pair | shared_voters | Jaccard | Reading |
| :-- | --: | --: | :-- |
| arbitrum treasury and arbitrum core (Tally) | 86,230 | 0.604 | Strongest by count and still very high proportionally; same organization |
| cakevote.eth (PancakeSwap) and fistdex.eth | 1 | 0.000007 | Lowest Jaccard: one shared voter against 137,266 distinct voters |
| hinny.eth and tunny.eth (Snapshot) | 4,063 | 0.996 | Almost identical voter bases at moderate size |
| three Tally deployments (0x141ae870..., 0x157823bc..., 0xbbd718cc...) | 117 | 1.0 | Identical voter sets of 117 wallets; cause unknown |
| two deployments (0x3beb9da3..., 0xc1a90f60...) | 1 | 1.0 | Jaccard 1.0 with a single voter: not informative |

**Caution on very small DAOs.** 10,047 edges (1.7%) have Jaccard exactly 1.0 and 25.9% of edges involve a DAO with fewer than 10 voters. Jaccard is unstable when a DAO is that small, so S2-06 should apply a minimum (for example `shared_voters >= 10`, which leaves 41,759 edges, 894 of them with Jaccard >= 0.9). The threshold is a decision for the group.

**Metadata is not comparable.** For the Arbitrum pair, `unique_voters` in the metadata gives a union of 164,963 voters, while the votes used in the graph give 142,735. The 469 excluded high-activity wallets cannot explain a gap of about 22,000, so the metadata describes a different population (see S2-01). The cause has not been identified.

**Top neighbour of the S2-09 hubs by count and by Jaccard.** For most hubs both measures agree (Arbitrum, Uniswap, balsam). They differ for Strio (fabien.eth by count, 0xchenhu.eth by Jaccard), tarpon (balsam.eth vs danhuacap.eth), Stargate DAO, Lido and ENS. PancakeSwap's strongest relationship by count (Aave DAO, 6,713 voters) has a Jaccard of only 0.04, consistent with the size of its community.

Files: `data/processed/edges_jaccard.csv` (all edges) and `data/processed/edges_jaccard_hubs_S2-09.csv` (62,973 edges touching the 15 hubs selected in S2-09).

## 5. Notes for S2-06

`edges_jaccard.csv` keeps `shared_voters`, both DAO sizes, the union and `jaccard`, so S2-06 can compare rankings under both measures and separate size effects from proportional overlap without recomputing anything.
