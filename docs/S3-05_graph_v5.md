# S3-05 — Reference graph on the complete votes (Zenodo v5)

**Status:** Done (2026-11-02).
**Command:** `python -m src.pipeline.run_pipeline --max-daos 100` (full run about 28 minutes).
**Data:** Zenodo v5, `votes.csv` with 67,340,666 rows (see `data_dictionary.md`,
"Dataset version (S3-03)" and "Coverage of votes.csv in v5 (S3-04)").
**Configuration:** unchanged from Sprint 2 (`max_daos = 100`; Jaccard denominators
count every voter of the deployment, including single-deployment voters).
**Breakdown:** `notebooks/05_isolation_by_platform.ipynb` (method of S2-10), rerun on v5.

This graph replaces the Sprint 2 graph as the reference for S3-06 and S3-07.

## Sprint 2 baseline against the new graph

| | Sprint 2 (v4) | S3-05 (v5) | Change |
| --- | ---: | ---: | ---: |
| Votes in `votes.csv` | 11,638,348 | 67,340,666 | x5.8 |
| Distinct (voter, deployment) pairs | 2,721,671 | 9,250,601 | x3.4 |
| Deployments with votes | 65,752 | 66,086 | +334 |
| Nodes | 86,495 | 86,495 | 0 |
| Edges | 576,861 | 700,304 | +21.4% |
| Total weight (shared voters) | 4,503,001 | 10,682,356 | x2.4 |
| Average degree | 13.34 | 16.19 | +2.85 |
| Connected nodes | 37,239 | 51,218 | +13,979 |
| Isolated nodes | 49,256 | 35,277 | -13,979 |
| Connected components | 50,767 | 36,263 | -14,504 |
| Largest connected component | 31,017 | 46,722 | +15,705 |

The node set does not change: nodes come from the catalogue plus the six
deployments of S2-02, and the catalogue is the same in v4 and v5.

## Jaccard validation

The checks of `src/pipeline/jaccard_weights.py` pass on the new graph:

- Logic check on all 700,304 edges: no missing deployment size, no shared count
  above the smaller deployment, no union below the larger deployment, no Jaccard
  value outside (0, 1].
- Hand recalculation from the voter sets matches the table for every representative
  pair. Example: `crypto435.eth` and `linea-build.eth` share 170,988 voters out of a
  union of 2,906,437 (Jaccard 0.0588). `linea-build.eth` had no votes in v4.
- `edges_jaccard.csv` has the same 700,304 edges as `edges.csv`.

## Where the change comes from

### Isolation by platform

| Platform | Nodes | Connected v4 | Connected v5 | Votes, no edges v4 | Votes, no edges v5 | No votes v4 | No votes v5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Snapshot | 71,958 | 34,294 | 48,148 | 26,869 | 13,349 | 10,795 | 10,461 |
| Tally | 4,394 | 875 | 905 | 274 | 244 | 3,245 | 3,245 |
| Realms | 4,224 | 780 | 780 | 673 | 673 | 2,771 | 2,771 |
| DAOhaus | 3,459 | 769 | 787 | 169 | 151 | 2,521 | 2,521 |
| Aragon | 2,402 | 491 | 562 | 503 | 432 | 1,408 | 1,408 |
| DAOstack | 58 | 30 | 36 | 25 | 19 | 3 | 3 |
| Total | 86,495 | 37,239 | 51,218 | 28,513 | 14,868 | 20,743 | 20,409 |

- **Snapshot explains almost all the change** (+13,854 of the +13,979 newly
  connected nodes). These are mostly small spaces whose voters also vote in the
  large spaces that were missing in v4.
- **334 Snapshot spaces had no votes at all in v4** and have them in v5: all their
  proposals had more than 5,000 votes and were never collected.
- **Tally, DAOhaus, Aragon and DAOstack** have exactly the same votes in v4 and v5,
  yet 125 of their deployments become connected. Their voters were already in the
  data; what was missing was the Snapshot side of the relationship.
- **Realms does not change at all.** It uses Solana addresses, which never match the
  Ethereum addresses of the other platforms, so new Snapshot votes cannot reach it.

Share of isolated deployments among deployments with votes:

| Platform | v4 | v5 |
| --- | ---: | ---: |
| Snapshot | 43.9% | 21.7% |
| Tally | 23.8% | 21.2% |
| Realms | 46.3% | 46.3% |
| DAOhaus | 18.0% | 16.1% |
| Aragon | 50.6% | 43.5% |
| DAOstack | 45.5% | 34.5% |
| Total | 43.4% | 22.5% |

### Why active deployments are still isolated

- 14,747 of the 14,868 active isolated deployments have only single-deployment
  voters (28,481 in v4).
- 121 are isolated only because of the filter: their shared voters vote in more than
  100 deployments (32 in v4). With the complete data, more voters cross the
  `max_daos` threshold; this is still a small effect, but it should be taken into
  account when the filter is revisited in S3-06.
- Size remains the main factor, but it weighs much less than in v4:

| Voters in votes.csv | Deployments | Isolated v4 | Isolated v5 |
| --- | ---: | ---: | ---: |
| 1 | 42,220 | 58.7% | 29.7% |
| 2-5 | 13,980 | 22.9% | 13.8% |
| 6-20 | 4,598 | 11.4% | 6.8% |
| 21-100 | 3,056 | 3.5% | 2.5% |
| >100 | 2,232 | 1.4% | 1.2% |

  About half of the single-voter deployments that were isolated in v4 are now connected:
  their only voter turns out to vote in one of the large Snapshot spaces.
- Controlling for size (deployments with 2 or more voters, 23,866), isolation is
  8.2% in Snapshot, 8.3% in DAOhaus, 13.7% in Tally, 21.2% in DAOstack, 28.8% in
  Aragon and 38.9% in Realms (15.1%, 10.1%, 14.4%, 24.2%, 33.7% and 38.9% in v4).
  Aragon remains the least connected Ethereum platform; the data still do not
  explain why.

### Connections between platforms

| Platform pair | Edges v4 | Edges v5 | Share v5 |
| --- | ---: | ---: | ---: |
| Snapshot - Snapshot | 468,304 | 587,662 | 83.9% |
| Snapshot - Tally | 75,154 | 77,860 | 11.1% |
| DAOhaus - Snapshot | 12,309 | 13,147 | 1.9% |
| Tally - Tally | 5,624 | 5,619 | 0.8% |
| DAOhaus - DAOhaus | 5,242 | 5,242 | 0.7% |
| Realms - Realms | 3,556 | 3,556 | 0.5% |
| Other pairs | 6,672 | 7,218 | 1.0% |

- 119,358 of the 123,443 new edges (97%) join two Snapshot spaces. Cross-platform
  edges grow from 93,585 to 97,675, so their share falls from 16.2% to 13.9%: the
  complete data make the network more Snapshot-centred, not less.
- Tally - Tally loses 5 edges although Tally votes did not change. Probably some Tally voters
  now exceed 100 deployments once their Snapshot votes are counted, so
  the filter removes them.
- Realms still has no edge with any other platform.

## Conclusions

Stable with respect to Sprint 2:

- Snapshot is the centre of the network and of the cross-platform connections,
  mainly with Tally and DAOhaus.
- Realms is isolated from the other platforms by construction (address format).
- Aragon is the least connected Ethereum platform, even for deployments with 2 or
  more voters.
- Inactive deployments (no votes in the catalogue) are about a quarter of the nodes
  and are isolated regardless of the data version.

Changed with the complete data:

- The network is much more connected: 59.2% of the nodes are connected (43.1% in
  v4), and the largest component grows from 31,017 to 46,722 nodes.
- Isolation among active deployments halves (43.4% to 22.5%), and the gap between
  Snapshot and the other platforms disappears once size is controlled.
- Edges are stronger (total weight x2.4) and more concentrated in Snapshot - Snapshot
  pairs.

All Sprint 2 results built on the v4 graph (S2-03 to S2-10) are therefore
preliminary and are regenerated on this graph in S3-06 and S3-07.
