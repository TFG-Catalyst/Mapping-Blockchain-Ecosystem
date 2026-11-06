# S3-06 - Filtering and hub analyses on the complete votes (Zenodo v5)

**Status:** Rerun completed on v5. The stability criteria below were written before running any
analysis on v5, so they do not depend on the results.
**Reference graph:** S3-05 (`max_daos = 100`, Zenodo v5; see `S3-05_graph_v5.md`).
**Scope:** repeat S2-03, S2-04 and S2-09 with the same code, the same constants and the
same thresholds. No new parameter values are explored in this sprint.

## What is repeated

| Task | Question | Scripts (unchanged) | Baseline (v4) |
| --- | --- | --- | --- |
| S2-03 | Who does the activity filter affect? | `analysis/s2_03_voter_activity/analyze_voter_activity.py` | `results/S2-03/` |
| S2-04 | How sensitive is the graph to the threshold? | `analysis/common/explore_shared_voters.py` (edges of the four configurations), then `analysis/s2_04_graph_sensitivity/` | `results/S2-04/` |
| S2-09 | Which deployments are hubs and why? | `analysis/s2_09_ecosystem_hubs/` | `results/S2-09/` |

The four configurations are the same as in Sprint 2: `nolimit`, `max200`, `max100`, `max50`.
The group of wallets is recomputed with the same rule as in S2-03 (at least 5 DAOs and at
least 80% of their DAOs in the list of the most active wallet). S2-09 keeps the 15 hubs
selected in Sprint 2 and their verified identities; a deployment that enters the
candidates in v5 is reported as a new candidate with identity not verified.

## Stability criteria

v5 has 5.8 times more votes than v4, so absolute counts (wallets, edges, weight) are
expected to grow. They are reported with their ratio and marked **SCALE**, not as
instability. Conclusions are judged on shares, rankings and categories.

| Kind of result | STABLE if | Example |
| --- | --- | --- |
| Share (%) | changes by at most 2 percentage points | % of graph weight from the group at `max100` (1.9% in v4) |
| Value | changes by at most 10% (relative) | percentiles of DAOs per wallet, mean degree |
| Top-10 ranking | at least 90% of the v4 top 10 is still in the top 10 | hubs by degree and by weighted degree, per configuration |
| Category or flag | same value | category of each selected hub, `F_filter`, `F_overlap`, `F_size`, `F_org` |
| Counts that must stay zero | stay zero | excluded wallets that are not in the group at `max100` |

Anything outside these limits is **CHANGED** and is explained in the results section.
The tolerances are decisions of the team, not findings; they are constants at the top of
`compare_v4_v5.py`.

### Does `max100` remain justified?

`max100` was adopted in S2-04 for three reasons. They are checked again on v5 without
exploring new thresholds:

1. The group contributes a small share of the graph weight (1.9% in v4).
2. Every excluded wallet belongs to the group (0 others in v4).
3. Almost all wallets are kept (99.98% in v4).

S3-05 already shows that, with the complete data, more voters exceed 100 deployments
(121 deployments isolated only by the filter, against 32 in v4), so reasons 2 and 3 are
the ones to watch.

## How to rerun on v5

The scripts are the ones of the repository, unchanged, with the same commands as in
Sprint 2. They write to relative paths (`results/S2-0x`, `data/raw`), so they are run from a
separate working folder, outside the repository, with the repository on `PYTHONPATH`. That
keeps the Sprint 2 results (v4) in `results/S2-0x` untouched, and the repository without local
changes. Two scripts of this task are new and live in `analysis/s3_06_v5_comparison/`:
`select_hubs_v5.py` and `compare_v4_v5.py`.

Requirements: the packages of `requirements.txt` (pandas, networkx, matplotlib) and the v5
files of Zenodo (`votes.csv` of about 15 GB, `deployments.csv`, `proposals.csv`) in
`<working folder>/data/raw/`.

PowerShell, from the working folder (`<repo>` is the path of the repository):

```
$env:PYTHONPATH = "<repo>"
$env:PYTHONIOENCODING = "utf-8"     # some DAO names have characters that cp1252 cannot print
New-Item -ItemType Directory -Force data\processed, results\S2-03, results\S2-04, results\S2-09
Copy-Item <repo>\results\S2-09\S2-09_verified_identity.csv results\S2-09\   # manual evidence

# S2-03
python -m analysis.s2_03_voter_activity.analyze_voter_activity --cases --pattern --thresholds

# S2-04: edges of the four configurations, then the analyses
foreach ($n in 50, 100, 200, 0) {
  $name = if ($n -eq 0) { "nolimit" } else { "max$n" }
  python -m analysis.common.explore_shared_voters --max-daos $n --format team --output results/S2-04/edges_$name.csv
}
python -m analysis.s2_04_graph_sensitivity.graph_metrics
python -m analysis.s2_04_graph_sensitivity.analyze_hubs_components
python -m analysis.s2_04_graph_sensitivity.analyze_stability
python -m analysis.s2_04_graph_sensitivity.make_s2_04_figures

# S2-09
python -m analysis.s2_09_ecosystem_hubs.prepare_hub_candidates
python -m analysis.s2_09_ecosystem_hubs.classify_hubs --top 60
python <repo>\analysis\s3_06_v5_comparison\select_hubs_v5.py
```

`select_hubs_v5.py` runs the `select_hubs.py` of the repository with its `SELECTION` list
unchanged. The original aborts if a selected hub is no longer in the indicators table. On v5
this happens for three hubs (see the results), so the new script leaves them out of that run
and writes them, with their ranks, to `results/S2-09/S2-09_selected_hubs_not_found.csv`.

The run takes about 10 minutes on a laptop once the voter cache
(`data/processed/voters_cache.pkl`) exists. Building the cache needs several GB of memory.

## How the comparison is produced

```
python <repo>\analysis\s3_06_v5_comparison\compare_v4_v5.py --v4 <repo>\results --v5 results --output-dir results
```

It writes `S3-06_v4_vs_v5.csv` (one row per metric with its verdict) and
`S3-06_v4_vs_v5.md` (same table). It only reads result files. Comparing a folder with itself
gives no CHANGED and no MISSING. The tolerances are constants at the top of the script.

## Results

Output files of the rerun are in `results/S3-06/` (`S2-03/`, `S2-04/`, `S2-09/`, without the four
edge files, which are 110 MB). Full comparison, one row per metric with its verdict:
`results/S3-06/S3-06_v4_vs_v5.csv` / `.md`
(127 rows: 45 STABLE, 43 CHANGED, 35 SCALE, 4 INFO, 0 MISSING). Sprint 2 (v4) values come
from the committed `results/S2-0x`; v5 values from this rerun.

### Summary

| Result of Sprint 2 | On v5 |
| --- | --- |
| Heavy tail of activity (a few wallets in hundreds of DAOs) | **Stable** |
| A group of about 470 wallets with the same voting pattern | **Stable** (464; 446 of the 469 are still in it) |
| The group dominates the unfiltered graph | **Changed in size**: 30% of the weight without limit (50% in v4), 17% at `max200` (32%) |
| `max100` removes the group almost completely | **Stable**: 0.9% of the weight (1.9%) |
| `max100` excludes only wallets of the group | **Almost**: 2 other wallets are excluded (0 in v4) |
| Structure of the graph (weight distribution, edges lost between thresholds) | **Stable** |
| Which deployments are the hubs | **Changed**: 6 of the v4 top 10 remain |
| Hubs that depend on the filter | **Changed**: none among the candidates (17 in v4) |
| Category of each selected hub | **Stable** for the 12 that are still candidates |
| Overlap proportions of S2-09 | **Not reliable on v5** (see limitations) |

### S2-03: who the filter affects

- Rows read: 67,340,666 (expected from the v5 metadata). Wallets: 6,509,336 (1,629,408 in v4).
- **The population changes, the tail does not.** Wallets that vote in a single DAO go from
  76.1% to 85.2%, and the percentiles fall (p90 3 to 2, p99 12 to 8, p99.9 26 to 21): the
  complete votes add many occasional voters. At the top nothing moves: maximum 353 to 361 DAOs,
  wallets with more than 100 DAOs 319 to 321, with more than 200 DAOs 91 to 91.
- **Group.** The S2-03 rule gives 464 wallets (469 in v4); 446 are in both.
- **Threshold comparison.**

| Threshold | Excluded wallets (v4 / v5) | Of which not in the group (v4 / v5) | Weight from the group (v4 / v5) |
| --- | --- | --- | --- |
| no limit | 0 / 0 | 0 / 0 | 50.2% / 30.4% |
| 200 | 91 / 91 | 0 / 0 | 31.8% / 17.1% |
| 100 | 319 / 321 | 0 / **2** | 1.9% / 0.9% |
| 75 | 337 / 348 | 18 / 29 | 1.9% / 0.9% |
| 50 | 434 / 536 | 76 / 178 | 0.1% / 0.1% |

### S2-04: sensitivity of the graph

- **Same reference graph as S3-05.** At `max100` the weight is 10,682,356 in S2-03, equal to the
  total weight of the S3-05 graph. S2-04 gives 698,898 edges and weight 10,676,241; the
  difference with S3-05 (700,304 edges) is the S2-02 rule (edges whose end is not a known
  deployment), as in v4 (575,513 against 576,861).
- **Stable:** % of edges with weight at least 2 (35.7% at `max100`, 35.1-37.7% in all
  configurations), median weight (1), % of edges lost from `max200` to `max100` (4.2% to 4.5%),
  % of edges that depend on the group at `max100` (0.5%), and the size of each edge category:
  74.5% of the edges have the same weight in the four configurations (75.2% in v4).
- **Changed:** `max100` keeps 70% of the weight of `nolimit` (51% in v4), because the group is a
  smaller part of the data. The weight by activity band moves accordingly: wallets with 2-50
  DAOs contribute 67% of the weight (48%), wallets with more than 200 DAOs 16% (27%).
- **Scale only:** edges, total weight, nodes in the largest component (46,836 against 31,043),
  isolated nodes (35,157 against 49,224) and mean degree (+20% on the same 86,495 nodes).
- **Hubs by configuration.** The top 10 by degree and by weighted degree is the same in the
  four configurations (as in v4). It is not the same as in v4: 6 of 10 remain
  (Stargate DAO, Arbitrum DAO, arbitrum treasury, arbitrum core, Aave DAO, `test`). By degree,
  PancakeSwap, Uniswap (Snapshot and Tally) and Gitcoin leave and Linea, GMX, Optimism
  Collective and ENS enter; by weighted degree, PancakeSwap, Uniswap (both) and Gitcoin
  leave and Linea, GMX, Yoginth and Crypto435 enter. The new hubs are Snapshot spaces with few proposals and very many
  votes (Linea: 2 proposals, 3.1 million votes; Yoginth and Crypto435: 1 proposal each). This
  is what v5 corrects: proposals with more than 5,000 votes were incomplete.
- **Persistence of hubs.** Of the top 100 by degree, 94% are stable across thresholds (96% in v4).
  By weighted degree, 54% are stable (37% in v4): the nodes that move because of the group
  carry less of the ranking.

### S2-09: hubs

- **Candidates.** 60 nodes (78 in v4); 17 of the 29 initial candidates of v4 remain. 11 are
  new, with identity not verified (Linea, Yoginth, Crypto435, Optimism Collective,
  EtherScore, Base Name Service, SyncSwap, Mail3, Vesta, Magic Square, Cultivator DAO).
- **Flags.** `F_filter`: 17 nodes in v4, **0** in v5. `F_overlap` (15), `F_size` (24 to 22)
  and `F_org` (8) are unchanged, and no node present in both tables changes any flag.
- **Selected hubs.** 12 of the 15 are still candidates, and in all 12 the category is still
  backed by its flag. Not found: Metrox and Strio (`filter-dependent`) and OpenDAO
  (`dominated by community size`). They are listed with their ranks in
  `results/S3-06/S2-09/S2-09_selected_hubs_not_found.csv`.

| Hub | Category | Rank by weighted degree, v4 | v5 |
| --- | --- | --- | --- |
| Metrox | filter-dependent | 38 to 173 | 68 to 191 (90% of its weight from the group) |
| Strio | filter-dependent | 45 to 255 | 72 to 294 (97% from the group) |
| OpenDAO | size | 209 to 62 | 146 to 86 |
| arbitrum treasury / arbitrum core | same organization | 1 / 2 | 4 / 5 (same in the four configurations) |
| Uniswap / uniswap | same organization | 5 / 7 | 16 / 21 |
| Stargate DAO | size | 9 | 2 |
| Aave DAO | size | 3 | 6 |
| PancakeSwap | size | 6 | 19 |
| balsam / tarpon | proportional overlap | 24 / 25 | 38 / 41 |
| Lido / ENS | stable | 19 / 21 | 44 / 22 |

  Ranks are for `nolimit`; for Metrox, Strio and OpenDAO, `nolimit` to `max100`.

  Metrox and Strio keep depending on the group (more than 30% of their weight); they leave the
  candidates because other nodes gain real weight, not because they stop depending on the
  filter. What is not true on v5 is that any candidate is filter-dependent. All ranks move
  down together because Linea, Yoginth and Crypto435 enter at the top, but the order inside
  the four configurations is kept, which is what the categories describe.
- **Main neighbour.** Only 1 of the 12 selected hubs keeps its main neighbour. This is mostly
  the arrival of the new hubs (Linea, Stargate DAO and Arbitrum DAO are now the neighbours of
  Aave DAO, Stargate DAO and the Arbitrum governors), not a change in the relation they had.

### Does `max100` remain justified?

Yes, with one qualification.

1. The group contributes 0.9% of the weight (1.9%): holds.
2. The wallets excluded are almost all from the group: 319 of 321. The 2 others are new in
   v5 and show up only because the complete votes make some wallet exceed 100 DAOs without
   following the pattern. At `max75` and `max50` the others are 29 and 178 (18 and 76 in v4),
   so lower thresholds are less justified than before.
3. Almost all wallets are kept: 99.995% (6,509,015 of 6,509,336).

The threshold is not changed in this sprint, as agreed.

### Limitations and open points

- **Overlap proportions.** `unique_voters` of `deployments.csv` does not seem to include the
  votes added in v5: it is the same as in v4 for the old hubs and 0 for Linea, Yoginth and
  Crypto435. The proportion with the main neighbour of S2-09 (shared voters over unique voters
  of the smaller one) is therefore above 1 in several cases (Arbitrum DAO 4.9, Aave DAO 1.33)
  and `F_overlap` is not reliable. To be confirmed in the data dictionary; the exact
  proportion has to be recomputed with the method of S2-05/06 on the v5 graph. For example,
  balsam and tarpon share 6,070 voters (their unique voters are 4,570 and 4,541), so their
  overlap remains very high.
- **New hubs without identity.** The 11 new candidates have not been checked on Snapshot or on
  the block explorers. Their weight comes from few and very large proposals.
- **Selection of hubs.** The 15 hubs of Sprint 2 were chosen by hand. The 3 missing hubs and
  the new candidates should be reviewed by the team before S3-09 fixes a new selection.
- **Method.** The criteria were fixed before looking at the results. Labels in the
  comparison are mechanical: for example, mean degree is marked CHANGED by the script, but it
  is a scale effect (more edges between the same nodes) and is reported as such above.
