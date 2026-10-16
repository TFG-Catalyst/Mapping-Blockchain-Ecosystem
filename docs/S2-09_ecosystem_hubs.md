# S2-09 — Ecosystem hubs

**Sprint:** Sprint 2
**Track:** A — Carlos
**Start date:** 2026-10-12
**Status:** In progress (selection of 15 hubs classified and with verified identity; pending review with Rodrigo's normalized results)
**Depends on:** S2-04 (done) and S2-05/06 (Rodrigo, pending)

Goal (according to the backlog): select prominent DAOs from the filtering and normalization results, examine the relationships that explain their position, verify their identity, check whether their prominence persists under other graph-construction decisions, distinguish stable hubs from those dominated by size, the filter or relationships between DAOs of the same organization, and interpret with concrete examples.

> **Reproducibility note.** The edge files `results/S2-04/edges_<config>.csv`, `results/S2-04/S2-04_nodes_by_config.csv` (an intermediate file) and `data/raw/` are not included in the repository (see the notes of S2-03 and S2-04 to regenerate them). Order of execution after S2-04: `python scripts/prepare_hub_candidates.py`, then `python scripts/classify_hubs.py --top 60`, then `python scripts/select_hubs.py`. `results/S2-09/S2-09_verified_identity.csv` is manual evidence (explorer and Snapshot consultations) and is an input, not an output, of the scripts. The candidates file `S2-09_hub_candidates.csv` was regenerated on 2026-10-16 with the complete identity file: 9 candidates that appeared as `pending` in the earlier version now show their verified identity (no other value changed).

## What can be done without Rodrigo's results and what cannot

| Task | Does it depend on S2-05/06? |
|---|---|
| Candidates, sheet, main neighbors, identity, persistence across configurations | No |
| Classification of each hub and examples | Partially: the comparison between raw weight and normalized measure (Jaccard) comes from S2-05/06 |
| Final selection of the 10-15 hubs | Partially: it must be reviewed with the normalized measure |

**Decision:** we work with the raw weight of the working configuration (`max100`, S2-04). Jaccard is not computed here: S2-05 asks to take care that the denominators come from the same votes of the graph and not from the counters of `deployments.csv`, and duplicating it risks results that do not match Rodrigo's. The column `normalized_measure_S2_05_06` of the table stays empty until then.

## Step 1 — Candidates table (done)

**Script:** `scripts/prepare_hub_candidates.py` (it only reads; it writes to `results/S2-09/`).

**Candidate criterion:** union of the first 25 nodes by degree and the first 25 by weighted degree in `max100` → **29 candidates**.

**Files:**

- `S2-09_hub_candidates.csv`: one row per candidate with name, platform, `proposals_count`, `unique_voters`, `votes_count`, `website`, degree and weighted degree in the 4 configurations, rank in each one (persistence), 5 main neighbors with weight and verified identity.
- `S2-09_main_neighbors.csv`: the 5 main neighbors of each candidate in long format.
- `S2-09_verified_identity.csv`: verified identities with source and date.

**Persistence (weighted degree):** the first 10 hold the same rank in the 4 configurations. From there on there is movement: `Metis` ranges between 44 and 73 depending on the configuration, `ApeCoin DAO` between 43 and 56, `OpenDAO` between 62 and 209.

## Step 2 — Identity verification (done for the 15 selected hubs)

On Snapshot, `deployments.csv` brings the website (`snapshot.org/#/<id>`), which identifies the space. On Tally the id is `eip155:<chain>:<contract>` and there is no website, so the contract is checked in the chain's explorer.

| Node | Name in the data | Verified identity | Source |
|---|---|---|---|
| `eip155:10:0xcdf27f…b10` | `test` | **Optimism: Governance Agora** (proxy) | [Optimistic Etherscan](https://optimistic.etherscan.io/address/0xcdf27f107725988f2261ce2256bdfcde8b382b10), 2026-10-12 |
| `eip155:1:0x408ed6…4c3` | `uniswap` | **Uniswap: Governor Bravo** | [Etherscan](https://etherscan.io/address/0x408ed6354d4973f66138c91495f2f2fcbd8724c3), 2026-10-12 |
| `eip155:42161:0x789fc9…5a4` | `arbitrum treasury` | **Arbitrum Foundation: Treasury Governor** (proxy) | Arbiscan, screenshot by Carlos, 2026-10-12 |
| `eip155:42161:0xf07ded…5b9` | `arbitrum core` | **Arbitrum Foundation: Core Governor** (proxy) | Arbiscan, screenshot by Carlos, 2026-10-12 |
| `eip155:1:0xec568f…52c` | `aave` | **Aave: Governance V2** | Etherscan, screenshot by Carlos, 2026-10-12 |
| `eip155:324:0x767053…34f` | `zkprotocolgovernor` | **ZkProtocolGovernor** (verified contract) | ZKsync Era explorer, screenshot by Carlos, 2026-10-12 |
| `eip155:324:0x10560f…e89` | `zktokengovernor` | **ZkTokenGovernor** (verified contract) | ZKsync Era explorer, screenshot by Carlos, 2026-10-12 |

**What the screenshots contribute about same-organization clusters:**

- The two Arbitrum governors are proxies with the **same implementation** (`0x46AF4EDF…3d05b5aE0`) and the same creator (an account labeled "Arbitrum Foundation: D…"). It is the same-organization cluster confirmed by the explorer.
- The two zkSync ones have the **same creator** (`0x478A…1B92`). On ZKsync Era the explorer only gives the contract name, not an organization label, so membership in zkSync rests on the contract names (`ZkProtocolGovernor`, `ZkTokenGovernor`) and on the common creator, not on an official label.

**Selected Snapshot hubs (11).** The public Snapshot API (`hub.snapshot.org/graphql`) was queried by the id of each space. It returns the name, the description and the `verified` flag, which is the mark Snapshot gives to the spaces it considers authentic. It is a source independent of the `deployments.csv` data, but it does not prove who controls the space.

| Space | Name on Snapshot | `verified` | Description on Snapshot |
|---|---|---|---|
| `aavedao.eth` | Aave DAO | yes | (empty) |
| `uniswapgovernance.eth` | Uniswap | yes | "Only delegated UNI may be used to vote on proposals…" |
| `cakevote.eth` | PancakeSwap | yes | (empty) |
| `stgdao.eth` | Stargate DAO | yes | (empty) |
| `lido-snapshot.eth` | Lido | yes | "Off-chain voting is a part of the Lido DAO decision-making process…" |
| `ens.eth` | ENS | yes | (empty) |
| `theopendao.eth` | OpenDAO | yes | "OpenDAO" |
| `balsam.eth` | balsam | **no** | (empty) |
| `tarpon.eth` | tarpon | **no** | (empty) |
| `metrox.eth` | Metrox | **no** | "Metrox test space" |
| `test6.shot.eth` | Strio | **no** | (empty) |

The 11 spaces exist and the name matches that of the data. The 7 large hubs are verified by Snapshot. The 4 in the "filter-dependent" and "overlap cluster" categories are not, and `Metrox` describes itself as a test space. The full results are in `results/S2-09/S2-09_verified_identity.csv`.

**Warning:** the node `test` is a real Optimism governance contract, with 78,724 unique voters and 240,303 votes. The name comes from the label Tally gave it. It must not be discarded as a test DAO.

## Step 3 — Objective indicators and classification (done; selection pending approval)

**Script:** `scripts/classify_hubs.py` (it only reads; it writes `results/S2-09/S2-09_hub_indicators.csv`). It was applied to the 29 candidates plus the nodes that are in the top 60 by weighted degree of any configuration (`--top 60`): **78 nodes**. It was widened because the hubs that depend on the group of 469 are not among the `max100` candidates, which is where they disappear.

**Indicators** (reference `max100`): rank by weighted degree in the 4 configurations and its difference; % of the no-limit weighted degree that comes from the group; unique voters and their rank; proportion between the weight of the main neighbor and the unique voters of the smaller of the two; whether among the 5 main neighbors there is a node of its same organization.

**Flags and thresholds** (they are decisions, not findings; they are in constants of the script):

| Flag | Criterion | Nodes |
|---|---|---:|
| `F_filter` | ≥ 30% of its no-limit weight comes from the group | 17 |
| `F_overlap` | weight of the main neighbor ≥ 0.8 × unique voters of the smaller one and rank by degree ≥ 100 places worse than by weighted degree | 15 |
| `F_size` | among the 30 nodes with the most unique voters | 24 |
| `F_org` | a main neighbor belongs to its same organization | 8 |

The organization assignment is manual and only covers Arbitrum, Uniswap, Aave and zkSync (where there is a verified identity or a clear name match). It does not cover, for example, Optimism (`test` and `Optimism Collective`), because the link has not been checked.

### What the indicators say

1. **Filter-dependent (17 nodes, 93-100% of their weight from the group).** They enter the top 40-60 in `nolimit` (ranks 38-60) and `max200` (61-80) and disappear in `max100` (ranks 173-368) and `max50` (236-2,972). Rank by weighted degree in `nolimit` → `max100` → `max50`: `Metrox` 38 → 173 → 236, `Strio` 45 → 255 → 605, `0xchenhu` 49 → 359 → 2,954.
2. **Proportional-overlap cluster (15 Snapshot spaces).** `balsam`, `tarpon`, `danhuacap`, `mists`, `godsgirl`, `goodchina`, `wangzian`, `gaggle`, `caiman`, `hotstock`, `hinny`, `electricite`, `tunny`, `angelmother` and `lootdex`. They occupy ranks 24 to 39 by weighted degree, with 3,739-4,570 unique voters each (ranks 85-116 by size). **They do not depend on the filter** (0% of the weight comes from the group) and their rank hardly changes between configurations (maximum difference of 3 places). The proportion 1.00 indicates that the voters of the smaller one are almost all contained in the neighbor, but `unique_voters` may have a different coverage than the votes of the graph, so it is indicative until S2-05/06. It is a pattern that none of the categories of the plan covers.
3. **Same organization (8 nodes):** `arbitrum treasury`, `arbitrum core`, `Arbitrum DAO`, `Uniswap` (Snapshot), `uniswap` (Tally), `zkprotocolgovernor`, `zktokengovernor` and `aave` (Tally). `Aave DAO` (Snapshot) is not flagged because its main neighbor is not the Tally `aave`.
4. **Size is the baseline explanation, not a category that distinguishes.** 24 of the 78 nodes are among the 30 with the most unique voters. Of them, 17 have no other flag (`Aave DAO`, `test`, `PancakeSwap`, `Stargate DAO`, `Gitcoin`, `OpenDAO`, `Metis`, `ApeCoin DAO`…). The ones not explained by size stand out: 21 nodes with no flag at all (`Lido`, `ENS`, `Balancer`, `Sismo`, `Optimism Collective`…), with a high rank by weighted degree despite being lower by unique voters (e.g. `Lido`: rank 18 by weighted degree and 53 by unique voters).

### Correction of an earlier assumption

`OpenDAO`, `Metis` and `ApeCoin DAO` seemed "configuration-dependent" because their rank changes (`OpenDAO` from 62 to 209). **They are not**: their weighted degree is identical in `nolimit`, `max200` and `max100` (`OpenDAO` 33,559, `Metis` 50,606, `ApeCoin DAO` 52,963) and falls 3-5% in `max50`. They only drop in rank in `nolimit` because the group inflates 147 nodes that overtake them (there are 61 nodes with more weight than `OpenDAO` in `max100` and 208 in `nolimit`). It is a change of relative ranking, not a dependence on the filter. Other nodes change the same way (`dYdX`, `compound`, `Decentraland`).

## Step 4 — Selection, classification and examples (done; provisional until S2-05/06)

**Script:** `scripts/select_hubs.py`. It writes `results/S2-09/S2-09_selected_hubs.csv`. The figures come from the indicators CSV; only the category and the interpretation of each hub are written by hand in the script (dictionary `SELECTION`).

**Selection:** 15 hubs chosen to cover each category with the clearest cases from the step 3 indicators. Carlos approved the selection on 2026-10-12. It is not a list of "the 15 largest hubs": ranks 1-15 by weighted degree include nodes that were not chosen because they repeat a category.

| Category | Hub | Weighted rank (no limit / 200 / 100 / 50) | % group weight | Unique voters (rank) | Main neighbor (weight; proportion) |
|---|---|---|---|---|---|
| filter-dependent | `Metrox` (snapshot) | 38 / 61 / 173 / 236 | 93.1% | 1,301 (275) | `Fabien` (384; 0.30) |
| filter-dependent | `Strio` (snapshot) | 45 / 65 / 255 / 605 | 98.0% | 536 (566) | `Fabien` (188; 0.35) |
| proportional-overlap cluster | `balsam` (snapshot) | 24 / 24 / 24 / 21 | 0.0% | 4,570 (85) | `tarpon` (4,528; 1.00) |
| proportional-overlap cluster | `tarpon` (snapshot) | 25 / 25 / 25 / 22 | 0.0% | 4,541 (87) | `balsam` (4,528; 1.00) |
| same-organization cluster | `arbitrum treasury` (tally) | 1 / 1 / 1 / 1 | 0.0% | 138,480 (1) | `arbitrum core` (86,230; 0.77) |
| same-organization cluster | `arbitrum core` (tally) | 2 / 2 / 2 / 2 | 0.0% | 112,713 (4) | `arbitrum treasury` (86,230; 0.77) |
| same-organization cluster | `Uniswap` (snapshot) | 5 / 5 / 5 / 5 | 2.5% | 22,446 (8) | `uniswap` (13,390; 0.62) |
| same-organization cluster | `uniswap` (tally) | 7 / 7 / 7 / 7 | 0.0% | 21,747 (9) | `Uniswap` (13,390; 0.62) |
| dominated by community size | `PancakeSwap` (snapshot) | 6 / 6 / 6 / 6 | 0.2% | 129,322 (3) | `Aave DAO` (6,713; 0.14) |
| dominated by community size | `Aave DAO` (snapshot) | 3 / 3 / 3 / 3 | 0.1% | 47,019 (6) | `Uniswap` (9,753; 0.43) |
| dominated by community size | `Stargate DAO` (snapshot) | 9 / 9 / 9 / 9 | 0.0% | 30,475 (7) | `arbitrum treasury` (7,851; 0.26) |
| stable | `Lido` (snapshot) | 19 / 19 / 18 / 19 | 0.0% | 6,657 (53) | `Aave DAO` (3,528; 0.53) |
| stable | `ENS` (snapshot) | 21 / 21 / 20 / 20 | 0.0% | 9,010 (37) | `Aave DAO` (3,028; 0.34) |
| dominated by community size | `test` (tally) | 4 / 4 / 4 / 4 | 2.0% | 78,724 (5) | `arbitrum core` (24,078; 0.31) |
| dominated by community size | `OpenDAO` (snapshot) | 209 / 63 / 62 / 62 | 0.0% | 10,636 (30) | `PeopleDAO` (550; 0.21) |

**How to read the categories.** "Dominated by community size" means that the node is among those with the most unique voters and that this is consistent with its weight, not that the cause has been demonstrated. `OpenDAO` is the borderline case (rank 30 by unique voters). "Stable" is the absence of the four flags and a rank that does not change between configurations; it does not prove that it is a real connector.

**Limits that come from S2-01 (sprint report).** (1) `votes.csv` only covers 13.7% of the declared Snapshot votes, and `aavedao.eth` and `stgdao.eth` are among the six spaces with the most missing votes: the weights of `Aave DAO` and `Stargate DAO` are lower bounds. (2) S2-01 indicates that the Jaccard denominators must come from `votes.csv`; the overlap proportion of this document uses `unique_voters` from `deployments.csv` (metadata, not recomputed), so it is indicative until S2-05.

### Interpreted examples

**1. `Metrox`: a hub that depends on the filter.** With no limit it has 790 neighbors and a weighted degree of 56,319 (rank 38); with `max100` it goes to 490 neighbors and 6,516 (rank 173), that is, it loses 88% of its weight. 93.1% of its no-limit weight comes from the group of 469 wallets. Its own community is small (1,301 unique voters, rank 275) and Snapshot describes it as "Metrox test space". Reading: it appears as a hub because the wallets of the group vote in it, not because of its community. `Strio` follows the same pattern (53,844 → 3,676). *Limit:* the data show that the weight comes from the group, not why those wallets vote there.

**2. `balsam` and `tarpon`: a proportional-overlap cluster.** Each has only 126 and 115 neighbors, but a weighted degree of 61,671 and 61,467, almost the same as `Lido` (66,693) and `ENS` (65,626) with more than 3,000 neighbors. They share 4,528 voters between them, and each has 4,570 and 4,541 unique voters, so almost all the voters of one are in the other. They do not depend on the filter (0% from the group) and in `max50` their weighted degree hardly falls (61,592 and 61,388), so that weight comes from wallets with 50 DAOs or fewer. Reading: there is a cluster of 15 spaces with an almost common voter base (of them, it has only been checked that `balsam` and `tarpon` are not verified on Snapshot). This is a lot of weight concentrated in few neighbors and it does not fit size, filter or organization. *Limits:* the cause is unknown; `unique_voters` may have a different coverage than the votes of the graph; the exact proportion will be given by S2-05/06.

**3. `arbitrum treasury` and `arbitrum core`: the same organization.** They are ranks 1 and 2 in the four configurations (338,588 and 331,442 of weighted degree, more than 9,600 neighbors each) and their main link is between them: 86,230 shared voters, proportion 0.77. They are proxies with the same implementation, verified on Arbiscan. Reading: a large part of their weight reflects that the same community votes in two governors of one organization, not that two different DAOs discover each other. The same happens with `Uniswap` and `uniswap` (13,390 shared voters, proportion 0.62). *Limit:* deciding whether these nodes should be merged in the graph is a team decision, outside S2-09.

**4. `Lido` and `ENS`: no flag.** They are ranks 18 and 20 by weighted degree in `max100` and 53 and 37 by unique voters, with equal ranks in the four configurations (±1). They do not depend on the group (0%), they are not of the same organization as their main neighbor and they are not in the top 30 by size. They contrast with `PancakeSwap` (rank 3 by unique voters, 6 by weighted degree), whose weight is consistent with the size of its community. Reading: they are the best candidates for real connectors between communities. *Limit:* that none of our four checks explains them does not prove that they are; the normalized result of S2-05/06 is missing.

## Preliminary findings (prior to the classification; see steps 3 and 4)

1. **Cluster of Snapshot spaces with an almost identical voter base** (step 3 widens it from 2 to 15 spaces). `balsam.eth` and `tarpon.eth` are at ranks 24 and 25 by weighted degree in `max100`, but very low by degree (1,784 and 1,938): they have few neighbors (126 and 115) with enormous weights. Their main neighbors are `tarpon`, `danhuacap`, `mists`, `goodchina`, `godsgirl` and `wangzian`, with 4,185-4,528 voters shared with `balsam`/`tarpon`, which have about 4,500 unique voters each according to `deployments.csv`. That is, a group of spaces that share almost all their voters. This is not community size or the known same organization: it is very high proportional overlap. The exact proportion must be computed by S2-05/06 with the correct denominators; here it is only used as an order of magnitude. It is not known why it happens.
2. **Same-organization cluster.** `arbitrum treasury` and `arbitrum core` are ranks 1 and 2 and share 86,230 voters (the strongest edge of the graph): they are two Arbitrum governors (same implementation, verified). In addition `Arbitrum DAO` (Snapshot) is rank 8. Something similar happens with Uniswap (Snapshot and Tally), Aave (Snapshot and Tally) and zkSync (`zkprotocolgovernor` and `zktokengovernor`).
3. **Very stable hubs by degree.** The first 10 by degree and by weighted degree do not change between configurations (S2-04).

## Normalized measure to be used in the review (Rodrigo's definition, 2026-10-16)

For S2-05 Rodrigo computes the **Jaccard** of each edge: `common / (voters A + voters B − common)`.

- The voters of each DAO are counted from `votes_clean.csv` with the same filter of 100: wallets with more than 100 DAOs are left out of both sides of the fraction.
- Voters who vote in only one DAO **are** counted in the denominator: they are never common voters, but they are part of that DAO's community. Without them, two DAOs of very different sizes could come out with Jaccard 1.
- It does not use `unique_voters`, in line with what S2-01 indicates.
- He will run his script on our `edges_max100.csv` (it must give the same 576,861 edges) and deliver `edges_jaccard.csv` with lowercase ids.

**The proportion in this document is not Jaccard.** `neighbor_1_proportion` is `common / unique voters of the smaller of the two` with `unique_voters` from `deployments.csv`: an overlap coefficient with metadata. It coincides with Jaccard when the two DAOs have a similar size (`balsam` and `tarpon`) and moves away when the sizes are very different, because the overlap stays high and the Jaccard drops. The category "proportional-overlap cluster" and the proportion in the sheets will be reviewed with his `edges_jaccard.csv`.

## Pending in S2-09

- [x] Candidates and sheet (step 1).
- [x] Verify the identity of the 7 Tally candidates.
- [x] Check the identity of the 11 selected Snapshot hubs (Snapshot API).
- [x] Compute the indicators and the classification (step 3).
- [x] Select 15 hubs from step 3 (approved by Carlos; provisional until S2-05/06 is available).
- [x] Classify each hub: stable, dominated by community size, filter-dependent, same-organization cluster or proportional-overlap cluster (a category that arises from finding 1).
- [x] Write 3-4 examples with their interpretation (4 written).
- [ ] Review the selection and the classification with Rodrigo's normalized results (fill in `normalized_measure_S2_05_06`).

## Changelog

| Date | Change | Files |
|---|---|---|
| 2026-10-12 | Candidates table, main neighbors and first verified identities | `scripts/prepare_hub_candidates.py`, `results/S2-09/` |
| 2026-10-12 | Verified identity of the 7 Tally candidates (screenshots by Carlos) | `results/S2-09/S2-09_verified_identity.csv`, this document |
| 2026-10-12 | Indicators and classification of 78 nodes; corrected the assumption about OpenDAO, Metis and ApeCoin | `scripts/classify_hubs.py`, `results/S2-09/S2-09_hub_indicators.csv`, this document |
| 2026-10-12 | Verified identity of the 11 selected Snapshot hubs; selection and classification of 15 hubs; 4 interpreted examples | `scripts/select_hubs.py`, `results/S2-09/S2-09_selected_hubs.csv`, `results/S2-09/S2-09_verified_identity.csv`, this document |
| 2026-10-16 | Added the limits that come from S2-01 (Snapshot coverage and denominators) | this document |
| 2026-10-16 | Recorded Rodrigo's Jaccard definition and clarified that `neighbor_1_proportion` is not Jaccard | this document |
| 2026-10-16 | English version for the repository: file names, script names, CSV columns, flags (`F_filtro` → `F_filter`, `F_solap` → `F_overlap`, `F_tamano` → `F_size`) and categories translated; candidates file regenerated with the complete identity file | all files of S2-09 |
