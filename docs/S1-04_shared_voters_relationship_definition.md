# S1-04 — Formal Definition of a DAO-to-DAO Relationship: "Shared Voters"

**Sprint:** Sprint 1 — Dataset exploration & first DAO network pipeline
**Track:** A (exploration and network relationships) — Carlos
**Date:** 2026-09-27
**Status:** Proposal validated with real data, pending team review

---

## 1. Chosen relationship

Out of the four candidate relationships identified by the team (shared authors, same organization across platforms, parent/child DAO, shared voters), **shared voters** is chosen for this first version of the graph, for the following reasons:

- It is the signal with the most data available (`votes.csv` has far more rows than `proposals.csv`), which produces a denser and more representative graph.
- It does not depend on fragile text comparisons (names, identifier substrings), unlike the "same organization" or "parent/child DAO" relationships.
- It connects directly to the CATALYST research framework that the TFG is part of, which focuses on measuring the redundancy of connections ("wide bridges") between communities as an indicator of ecosystem cohesion and resilience.

The other three candidate relationships are proposed for Sprint 2 (see section 8).

## 2. Data source

Only `votes.csv` is used, with the columns `deployment_id`, `voter` and `platform`. `deployments.csv` and `proposals.csv` are not used for this relationship. The `weight` column is not used.

## 3. Formal definition

- **Nodes:** each unique `deployment_id` in the dataset (each DAO).
- **Edge:** an **undirected** edge exists between DAO A and DAO B if and only if at least one wallet address (see section 4 on normalization) has cast at least one vote in both.
- **Edge weight:** number of distinct wallet addresses that have voted in both DAOs (a count, not voting power).
- **Exclusion threshold:** wallets that appear voting in more than 200 distinct DAOs (`MAX_DAOS_PER_VOTER = 200`) are excluded from the computation. They are considered outliers (professional delegates, voting bots) whose inclusion would generate a disproportionate number of edges without representing a real connection between those DAOs. This threshold is adjustable and should be reviewed in Sprint 2 with more context.

**Why `weight` (voting power) is not used as the edge weight:** according to the data dictionary, `weight` is expressed in the minimum unit of each DAO's token and is not comparable across different DAOs (one token is not worth the same as another). Using it directly would mix incomparable magnitudes. The count of shared wallets is used instead as a simpler, more defensible first approximation.

## 4. Voter address extraction and normalization

The `voter` field in `votes.csv` **does not have a single format**: it varies depending on the platform each vote comes from. This is a relevant finding for the data dictionary and should be documented alongside Rodrigo's work (S1-02).

| Platform | Rows (approx.) | Format of the `voter` field | Treatment applied |
|---|---|---|---|
| snapshot | 8,883,118 | Plain Ethereum address (`0x...`) | Used as is, lowercased |
| tally | 1,597,604 | CAIP-10 prefix: `eip155:<chain_id>:<address>` | The `eip155:<chain_id>:` prefix is removed, keeping only the address; lowercased |
| realms | 1,067,333 | Solana address in base58 (not `0x`) | Left untouched, **not** lowercased (in Solana, upper/lower case is significant) |
| daohaus | 51,129 | Plain Ethereum address (`0x...`) | Used as is, lowercased |
| aragon | 26,833 | `<deployment_id>-voter-<address>` | The part after `-voter-` is extracted; lowercased |
| daostack | 12,331 | Plain Ethereum address (`0x...`) | Used as is, lowercased |

**Important note:** Ethereum addresses are normalized to lowercase because they are case-insensitive (the mixed-case "checksum" is only a visual check and does not change the address). Realms (Solana) addresses are NOT modified, because in base58 they are case-sensitive.

**Known limitation:** Realms (Solana) DAOs are effectively isolated from the rest of the graph, since their addresses are not comparable with Ethereum ones. This is not an error; it is an expected consequence of mixing two different blockchain ecosystems in the same dataset.

## 5. Known decisions and simplifications (to be validated with the team)

- **Equivalent DAOs across platforms are not deduplicated.** If the same organization has deployments on both Snapshot and Tally, they are treated here as two distinct nodes. This can artificially inflate the weight of some edges (see the finding in section 6) and is a candidate to be resolved in Sprint 2 by combining this relationship with relationship 2 ("same organization across platforms").
- The `MAX_DAOS_PER_VOTER = 200` threshold is a provisional decision and can be adjusted.

## 6. Empirical validation (run on the full dataset, 11,638,348 rows)

- Unique voters (addresses): 1,629,408
- **Voters participating in 2+ DAOs: 388,891 (23.87%)** → confirms there is real and sufficient overlap for the relationship to be useful.
- Edges generated (weight ≥ 1): 602,295
- Edges with weight ≥ 2: 226,663
- DAOs connected to at least one other DAO: 37,252
- Mean edge weight: 10.76 shared voters; maximum weight: 86,230
- 91 wallets excluded for exceeding the 200-DAO threshold (possible bots/delegates; the most active one appears in 353 DAOs)

**Resolved finding (see section 9):** the pair of DAOs with the most shared voters (86,230) corresponds to two deployments on Arbitrum (`0x789fC9...` and `0xf07DeD...`). Confirmed with `deployments.csv`: they are `arbitrum treasury` and `arbitrum core`, two distinct governance bodies of the same organization (Arbitrum DAO) on Tally. It is not a data error.

## 7. Deliverables of this task

- Exploration and edge-building script: `explorar_votantes_compartidos.py` (full version) and `shared_voters_simple.py` (simplified version with English names and comments)
- Resulting edge table: `edges_votantes_compartidos.csv` (602,295 rows: `deployment_id_a`, `deployment_id_b`, `peso_votantes_compartidos`)
- This document

## 8. Proposed next steps (Sprint 2)

1. Review and decide whether to deduplicate equivalent DAOs across platforms before recomputing the graph (candidate relationship "same organization across platforms").
2. Add the "shared authors" relationship (`proposals.csv`) as a second connection layer, sparser but with higher commitment (proposing takes more effort than voting).
3. Review the `MAX_DAOS_PER_VOTER` threshold with more context about who those highly active wallets are.
4. Evaluate the "parent/child DAO" relationship (Snapshot) as a complementary, non-substitutive hierarchical relationship.

## 9. Complementary finding (post-delivery): initial exploration of `deployments.csv`

After closing the empirical validation, an additional exploration (not blocking for considering S1-04 complete) was carried out on `deployments.csv`, motivated by the finding in section 6, to inform the deduplication decision pending for Sprint 2.

**1. Confirmation of the specific 86,230 shared-voters case:**

| deployment_id | platform | name | proposals_count | unique_voters |
|---|---|---|---|---|
| `eip155:42161:0xf07ded9dc292157749b6fd268e37df6ea38395b9` | tally | arbitrum core | 22 | 112,713 |
| `eip155:42161:0x789fc99093b09ad01c34dc7251d0c89ce743e5a4` | tally | arbitrum treasury | 54 | 138,480 |

Both deployments belong to the same organization (Arbitrum DAO), as two separate governance bodies (one for "core" protocol decisions, the other for treasury management). The very high number of shared voters makes sense: it is the same community voting in two places within the same DAO. **It is neither a bug nor an accidental duplication of data.**

**2. General exploration of "same organization across platforms" (Rodrigo's candidate relationship 2):**

Grouping `deployments.csv` by the `name` field:

- 4,897 distinct names appear in 2+ deployments; 887 of them across 2+ different platforms.
- However, reviewing the top matches, the vast majority is **noise**: generic names of test DAOs (`test`, `testdao`, `testing`, `asdasd`, `mydao`, `hello`) or isolated personal names (`alex`, `mark`, `jack`), consistent with users trying out DAO creation on Snapshot or Realms (trivial and free) with no real activity afterwards. Only a couple of names in the top 25 look like real recurring organizations (`zksync`, `gitcoin`).

**Conclusion for Sprint 2:** the `name` field in `deployments.csv`, used on its own, **is not a reliable signal** for deduplicating organizations across platforms — it would produce many false positives with toy DAOs. Any deduplication proposal should combine the name with another signal (e.g. `website`, or a minimum `proposals_count`/`unique_voters` threshold to discard deployments with no real activity), or go through manual review of a short list of candidates.
