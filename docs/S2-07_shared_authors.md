# S2-07: Shared-author network

**Script:** `src/shared_authors.py` (from the prototype in `notebooks/02_data_quality.ipynb`)
**Output:** `edges_authors.csv`, `authors_coverage_by_platform.csv`

## Definition
Two DAOs are connected if the same wallet created proposals in both. Weight = number of distinct shared authors. Authors count once per DAO.

## Validation
- **Author normalization.** Authors are lowercased. Snapshot stores 20,100 proposals with mixed-case (checksum) addresses, the other platforms lowercase. Without lowercasing there are 145,348 authors; with it 139,679 (5,669 duplicates merged). The effect on the network: 106 edges that were hidden appear and the total weight drops from 38,390 to 37,919, because the same wallet in two spellings was counted twice.
- **Linking proposals to nodes.** `dao_id` (deployment_id, or platform_deployment_id when missing, lowercased) matches the node table for 99.91% of proposals; the other 319 belong to the six Snapshot spaces of S2-02, which are added as nodes. After that no proposal is left without a node and every edge endpoint is a node.
- **Representative cases.** The 5 strongest and 5 random edges are recomputed with sets and match. Three authors have a 66-character identifier instead of a 42-character address; they are not wallets of the usual format and do not affect results.
- No author proposes in more than 70 DAOs, so no activity filter like the one for voters is needed.

## Result
139,679 authors, 66,619 DAOs with at least one authored proposal, **28,359 edges**, total weight 37,919; 87.6% of edges have weight 1. The strongest edges are families of spaces by the same operator (the 狂奔的蜗牛 spaces, 106-133 shared authors; two deployments with 140).

| Platform | Proposals with author | DAOs | DAOs in author edges |
| :-- | --: | --: | --: |
| Snapshot | 100% | 71,958 | 6,361 (8.8%) |
| DAOhaus | 100% | 3,459 | 1,007 (29.1%) |
| Aragon | 100% | 2,402 | 575 (23.9%) |
| DAOstack | 100% | 58 | 53 (91.4%) |
| Tally | 0% | 4,394 | 0 |
| Realms | 0% | 4,224 | 0 |

By platform pair: Snapshot-Snapshot 13,794, DAOhaus-DAOhaus 7,321, DAOhaus-Snapshot 3,145, Aragon-Aragon 1,655, the rest under 800 each.

## Limits
Tally and Realms proposals have no author at all, so 8,618 DAOs (10% of the nodes) cannot appear in this network. A missing author is a gap in the data, not an absence of relationship, and must not be read as one in S2-08.
