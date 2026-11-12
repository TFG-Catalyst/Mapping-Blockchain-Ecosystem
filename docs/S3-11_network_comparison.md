# S3-11 - Comparison of shared-author and shared-voter networks

Reference dataset: Zenodo v5.

## 1. Scope and comparison method

The comparison uses edges.csv and edges_authors.csv generated
from the v5 data. Relationships are matched by unordered pairs
of deployment identifiers, so endpoint order does not affect
whether two edges are considered equal.

The voter network contains 700,304 edges and applies
max_daos = 100. The author network contains 28,359 edges
and applies no equivalent activity filter. The comparison
therefore describes networks built under different rules.

## 2. Overlap between relationships

| Relationship category | Edges |
|---|---:|
| Present in both networks | 10,506 |
| Present only in the voter network | 689,798 |
| Present only in the author network | 17,853 |

Overall, 37.05% of author edges also appear in the voter
network, while 1.50% of voter edges appear in the author
network.

Tally and Realms lack proposal-author information. Restricting
both networks to Snapshot, Aragon, DAOhaus and DAOstack leaves
611,886 voter edges and all 28,359 author edges. The intersection
remains 10,506 edges, representing 1.72% of voter edges within
these platforms.

The networks therefore capture partially overlapping
relationships. An author-only edge indicates shared authors
without a shared-voter edge under the selected voter filter.
A voter-only edge indicates no observed shared-author edge,
rather than proof that no authors are shared.

## 3. Comparison within platforms with author data

The remaining comparisons use Snapshot, Aragon, DAOhaus and
DAOstack, the four platforms with proposal-author information.
Both endpoints of each retained edge must belong to these
platforms. This leaves 611,886 voter edges and 28,359 author
edges.

Restricting voter edges further to deployments with at least
one recorded author produces the same edge set in these data.
However, this does not remove differences in activity filtering
or establish that author coverage is complete.

The table reports overlap by platform pair. The final column
uses author edges as its denominator.

| Platform pair | Voter edges | Author edges | Common edges | Author edges also in voter network (%) |
|---|---:|---:|---:|---:|
| Snapshot - Snapshot | 587,662 | 13,794 | 4,308 | 31.23 |
| DAOhaus - DAOhaus | 5,242 | 7,321 | 3,377 | 46.13 |
| DAOhaus - Snapshot | 13,147 | 3,145 | 1,780 | 56.60 |
| Aragon - Aragon | 472 | 1,655 | 312 | 18.85 |
| Aragon - DAOhaus | 534 | 736 | 235 | 31.93 |
| Aragon - Snapshot | 3,748 | 572 | 226 | 39.51 |
| DAOstack - DAOstack | 78 | 613 | 64 | 10.44 |
| DAOhaus - DAOstack | 133 | 273 | 90 | 32.97 |
| DAOstack - Snapshot | 806 | 158 | 81 | 51.27 |
| Aragon - DAOstack | 64 | 92 | 33 | 35.87 |
| Total | 611,886 | 28,359 | 10,506 | 37.05 |

Snapshot–Snapshot accounts for the largest number of common
edges, followed by DAOhaus–DAOhaus. However, the proportion
of author edges also found in the voter network is highest
for DAOhaus–Snapshot, at 56.60%.

Within Aragon, DAOhaus and DAOstack, author edges outnumber
voter edges. The author network therefore adds relationships
that cannot be inferred from the filtered voter network,
despite being much smaller overall.

These differences describe the observed networks. They do
not establish why platforms differ or whether shared authors
coordinate their activities.

## 4. Deployments participating in relationships

Within the four-platform comparison, a deployment is counted
as connected when it has at least one retained edge.

| Measure | Deployments |
|---|---:|
| Connected in the voter network | 49,266 |
| Connected in the author network | 7,996 |
| Connected in both networks | 6,417 |
| Connected only in the voter network | 42,849 |
| Connected only in the author network | 1,579 |

The author network connects 1,579 deployments that have no
voter edge within this comparison. This demonstrates the
additional coverage provided by the authorship relationship.

Connected in both networks does not necessarily mean having
the same neighbours. A deployment may share voters with one
set of deployments and authors with another.

“Connected only” refers to the restricted networks used here.
It does not imply that a deployment has no other relationships
outside these platforms or outside the dataset.

## 5. Comparison of prominent deployments

Degree is the number of distinct neighbours in the restricted
network. Strength is the sum of edge weights: shared voters
in one network and shared authors in the other.

Rankings include every retained edge with positive weight.
They do not apply the minimum of 10 shared voters used in
the S3-07 normalization analysis. Ties are resolved by
deployment identifier in ascending order.

### 5.1 Highest-degree deployments

| Rank | Voter network deployment | Degree | Author network deployment | Degree |
|---|---|---:|---|---:|
| 1 | Stargate DAO | 31,018 | dead foundationsdao | 1,202 |
| 2 | Linea | 17,577 | raid guild | 297 |
| 3 | Arbitrum DAO | 12,602 | raid guild war chest | 290 |
| 4 | Aave DAO | 7,406 | metacartel xdai | 276 |
| 5 | GMX | 7,377 | poolhaus | 229 |
| 6 | Optimism Collective | 6,611 | daohaus second story cco | 226 |
| 7 | ENS | 6,362 | hausdao warcamp | 218 |
| 8 | Yoginth | 5,423 | hausdao | 214 |
| 9 | PancakeSwap | 5,356 | stakehaus | 194 |
| 10 | Mail3 | 5,356 | haus magesmith | 185 |

All ten voter-network deployments are on Snapshot, while
all ten author-network deployments are on DAOhaus. Names
are catalogue labels, not independently verified identities.

### 5.2 Overlap between rankings

The following table counts deployment identifiers appearing
in both networks' top-K lists under the same measure.

| K | Common deployments by degree | Common deployments by strength |
|---|---:|---:|
| 10 | 0 | 0 |
| 50 | 2 | 1 |
| 100 | 4 | 17 |

The leading deployments therefore depend strongly on the
relationship being measured. No deployment appears in both
top-ten lists, either by degree or by strength.

The larger overlap among the top 100 by strength does not
make the weights interchangeable. Strength counts shared
participants across deployment pairs, and the two networks
use different participant roles and filtering rules.

These rankings describe structural prominence in the
constructed networks. They do not establish influence,
organizational importance or coordination.

## 6. Examples of common and distinctive relationships

Examples were selected by descending edge weight within
each category, rather than by presumed organizational
importance.

### 6.1 Relationships observed in both networks

The pair 狂奔的蜗牛.eth – 狂奔的蜗牛5.eth shares 133 authors
and 136 retained voters. It is the common edge with the
highest shared-author count.

Another common pair, 狂奔的蜗牛3.eth – 狂奔的蜗牛4.eth,
shares 122 authors and 176 retained voters.

These figures show that both forms of overlap occur for
the same deployment pairs. They do not show whether the
shared authors are also the shared voters; that would
require comparing the participant sets directly.

### 6.2 A relationship observed only through authors

The pair
0x1b975a9daf25e7b01e0a6c72d657ff74925327a8 –
0x7961b6c69ec7d7203cbecc4f3bf30755713a3822
shares 140 authors, the highest author-edge weight.

It has no edge in the filtered voter network. This is
an absence under the current voter-network construction,
not proof that no voters were ever shared. Establishing
the reason would require inspecting the underlying votes
and the effect of the activity filter for this pair.

### 6.3 Relationships observed only through voters

Crypto435 (crypto435.eth) and Linea (linea-build.eth)
share 170,988 retained voters but have no observed
shared-author edge.

Linea and Stargate DAO (stgdao.eth) share 163,326 retained
voters, also without an observed shared-author edge.

Large voting overlap therefore does not necessarily
correspond to shared proposal authorship.

## 7. Method and reproducibility

The calculations use these local v5 outputs:

- data/processed/edges.csv
- data/processed/edges_authors.csv
- data/processed/nodes.csv
- data/processed/proposals_clean.csv

Each edge is represented by a sorted pair of deployment
identifiers. Let E_v be the set of voter edges and E_a
the set of author edges:

- Common edges: E_v intersect E_a.
- Voter-only edges: E_v minus E_a.
- Author-only edges: E_a minus E_v.
- Author-edge coverage: common edges divided by author edges.
- Voter-edge coverage: common edges divided by voter edges.

For the restricted comparison, edges are retained only
when both endpoints belong to Snapshot, Aragon, DAOhaus
or DAOstack, using the platform field in nodes.csv.

Platform pairs are also treated as unordered. Degree
counts incident edges, while strength sums their weights.
Top-K overlap counts shared deployment identifiers,
with ties resolved by identifier in ascending order.

Basic consistency checks are:

- 10,506 + 689,798 = 700,304 global voter edges.
- 10,506 + 17,853 = 28,359 author edges.
- 10,506 + 601,380 = 611,886 restricted voter edges.
- Common edges summed across platform pairs equal 10,506.
- 6,417 + 42,849 = 49,266 connected voter nodes.
- 6,417 + 1,579 = 7,996 connected author nodes.

The comparison is implemented in
analysis/s3_11_network_comparison/compare_networks.py.

Run from the repository root:

```bash
python -m analysis.s3_11_network_comparison.compare_networks
```

The script checks input totals against the v5 reference and
exports six CSV tables to results/S3-11/: edge overlap,
overlap by platform, node rankings, ranking overlap,
connected nodes and relationship examples.

## 8. Limitations

- Tally and Realms have no proposal-author information.
  Their missing author edges are not evidence of absent
  authorship relationships.
- The voter network excludes wallets participating in more
  than 100 deployments; the author network applies no
  equivalent activity filter.
- Address-based identities do not establish unique people
  or organizations.
- Deployment identifiers may represent different spaces
  belonging to the same organization. Repeated proposals
  across names can also affect shared-author relationships,
  as documented for Mimo and Parallel Protocol.
- The networks measure whether participants occur in both
  deployments, not whether participation was simultaneous.
- Catalogue names used in the ranking table have not been
  independently verified in this comparison.
- Overlap between edges does not establish overlap between
  the individuals acting as authors and voters.
- Rankings are conditional on the selected platforms,
  activity rules and treatment of ties.

## 9. Conclusion

The shared-author network complements the shared-voter
network rather than reproducing it. Of its 28,359 edges,
10,506 also occur in the voter network, while 17,853 add
relationships absent from the filtered voter graph.

The distinction remains when comparisons are restricted
to platforms with author information. The networks also
highlight different deployments: their top-ten rankings
have no nodes in common by either degree or strength.

Together, the networks provide two perspectives on
governance participation: overlap in voting and overlap
in proposal authorship. Their differences should be
interpreted alongside coverage and construction rules,
without treating either network as a complete account
of relationships between organizations.