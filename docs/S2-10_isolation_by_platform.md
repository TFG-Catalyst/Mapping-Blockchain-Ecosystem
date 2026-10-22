# S2-10 — Isolation and differences between platforms

**Status:** Done (2026-10-22). Analysis in `notebooks/05_isolation_by_platform.ipynb`.
**Graph:** reference graph of Sprint 2 (`max_daos = 100`): 86,495 nodes, 576,861 edges, 49,256 isolated nodes. Built from the 11.6M-vote `votes.csv`, so all figures are preliminary (see S2-01).

## Method

Each node is classified with the processed files only:

- `connected`: endpoint of at least one edge in `edges.csv`.
- `votes_no_edges`: has votes in `votes_clean.csv` but no edge.
- `no_votes`: does not appear in `votes_clean.csv`.

The number of voters of each deployment is counted from `votes_clean.csv` (distinct voters), not from the `unique_voters` metadata.

## Isolation by platform

| Platform | Nodes | Connected | Votes, no edges | No votes | Isolated among deployments with votes |
| --- | --- | --- | --- | --- | --- |
| Snapshot | 71,958 | 47.7% | 37.3% | 15.0% | 43.9% |
| Tally | 4,394 | 19.9% | 6.2% | 73.9% | 23.8% |
| Realms | 4,224 | 18.5% | 15.9% | 65.6% | 46.3% |
| DAOhaus | 3,459 | 22.2% | 4.9% | 72.9% | 18.0% |
| Aragon | 2,402 | 20.4% | 20.9% | 58.6% | 50.6% |
| DAOstack | 58 | 51.7% | 43.1% | 5.2% | 45.5% |
| Total | 86,495 | 43.1% | 33.0% | 24.0% | 43.4% |

The 49,256 isolated nodes are of two kinds: 20,743 deployments with no recorded votes and 28,513 active deployments whose voters vote in no other deployment of the graph.

## Why active deployments are isolated

- **Not the filter.** Only 32 deployments are isolated because their only shared voters vote in more than 100 deployments. The other 28,481 have only single-deployment voters (the same figure as the unfiltered graph in S2-04).
- **Size.** The median number of voters is 1 for isolated deployments and 2 for connected ones. 42,054 of the 65,752 deployments with votes (64%) have a single voter.

| Voters in votes.csv | Deployments | Isolated | Isolated (%) |
| --- | --- | --- | --- |
| 1 | 42,054 | 24,672 | 58.7% |
| 2-5 | 13,903 | 3,185 | 22.9% |
| 6-20 | 4,552 | 518 | 11.4% |
| 21-100 | 3,031 | 106 | 3.5% |
| >100 | 2,212 | 32 | 1.4% |

Controlling for size (deployments with 2 or more voters, 23,698), isolation is 10.1% in DAOhaus, 14.4% in Tally, 15.1% in Snapshot, 24.2% in DAOstack, 33.7% in Aragon and 38.9% in Realms.

## Connections between platforms

| Platform pair | Edges | Share |
| --- | --- | --- |
| Snapshot - Snapshot | 468,304 | 81.2% |
| Snapshot - Tally | 75,154 | 13.0% |
| DAOhaus - Snapshot | 12,309 | 2.1% |
| Tally - Tally | 5,624 | 1.0% |
| DAOhaus - DAOhaus | 5,242 | 0.9% |
| Realms - Realms | 3,556 | 0.6% |
| Other pairs | 6,672 | 1.2% |

93,585 edges (16.2%) join different platforms, and almost all of them involve Snapshot. Realms has no edge with any other platform.

## Interpretation

What can be attributed to observed participation:

- Most isolation among active deployments is a size effect: a deployment with one voter can only connect if that voter votes elsewhere. Once single-voter deployments are removed, Snapshot is as connected as Tally and DAOhaus.
- Snapshot is the centre of cross-platform connections, mainly with Tally.

What requires caution:

- **Inactive deployments.** In Tally, DAOhaus, Realms and Aragon, 59-74% of the nodes have no votes. Their isolation reflects missing activity in the catalogue, not an absence of relationships.
- **Voter identity.** Realms uses Solana addresses, which can never match the Ethereum addresses of the other platforms, so Realms is isolated by construction. In general a person using several addresses is counted as several voters.
- **Coverage.** `votes.csv` covers only 13.7% of the declared Snapshot votes (S2-01). The gap is mostly in large proposals, so it should affect isolation little, but 16,736 smaller proposals are also missing. Isolation figures may change with the new Zenodo version.
- **Open question.** Aragon remains isolated (33.7%) even with 2 or more voters; these data do not explain why. DAOstack has only 58 deployments.