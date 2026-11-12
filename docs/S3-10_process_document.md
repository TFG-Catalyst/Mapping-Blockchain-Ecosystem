# S3-10 - Process document: version 1

**Reference dataset:** Zenodo v5.

## 1. Purpose

This project maps relationships between DAO deployments through
shared participation in governance. The main network connects
deployments that share voters. A complementary network examines
shared proposal authors.

The process covers dataset inspection, data cleaning, node and
edge construction, activity filtering, edge weighting, validation
and analysis. This document describes the methodological choices
and links to the detailed evidence produced during the project.

The unit represented by a node is a deployment, which does not
necessarily correspond to a distinct organization. Relationships
represent overlap observed in the dataset and should not
automatically be interpreted as collaboration or influence.

## 2. Dataset and initial inspection
The project uses the dataset Mapping Decentralized Autonomous
Organization Governance Across Chains: An Updated, Multi-Platform
Dataset, by Farin, Hassan and Arroyo (MSR 2026). The reference
version is Zenodo v5, with a collection cut-off of October 2025.

The dataset covers six governance platforms: Aragon, DAOhaus,
DAOstack, Realms, Snapshot and Tally. It contains three CSV files:

| File | Unit represented | Rows in v5 |
|---|---|---:|
| deployments.csv | DAO deployment | 86,489 |
| proposals.csv | Governance proposal record | 351,269 |
| votes.csv | Individual vote record | 67,340,666 |

Initial inspection examined file schemas, missing values,
duplicates, identifier formats and consistency between files.
The exploration is recorded in the dataset inspection,
data-quality and vote-coverage notebooks, with findings
summarized in the data dictionary.

An important check compared observed vote rows with the counts
declared in the metadata. This revealed substantial Snapshot
undercoverage in v4, which was used during Sprints 1 and 2.
The project adopted v5 during Sprint 3 and reran the pipeline
and analyses using the updated data.

Snapshot coverage relative to deployment metadata increased
from 13.7% in v4 to 99.8% in v5. However, aggregate agreement
does not guarantee completeness: 55 Snapshot proposals with
declared votes still have no corresponding vote rows.
Tally also retains a discrepancy, with observed vote rows
equal to 110.9% of the declared deployment count.

Version tracking is therefore part of the method. Earlier
measurements retained in the data dictionary are explicitly
identified as v4 results, while the reference graph and
consolidated conclusions use v5.

## 3. Data cleaning and identity handling
Raw files are read from data/raw/, and cleaned versions are
written to data/processed/. The cleaning process preserves
the original files.

Deployment identifiers are converted to lowercase strings.
For proposals, both deployment_id and platform_deployment_id
are normalized, and dao_id uses deployment_id where available,
falling back to platform_deployment_id when it is missing.
Exact duplicate proposal rows are removed. This does not
remove every repeated proposal_id or merge deployments
belonging to the same organization.

Voter normalization handles the different representations
used in the source data:

- For values containing "-voter-", the address after that
  marker is extracted.
- For "eip155:<chain_id>:<address>" values, the address is
  extracted without the chain prefix.
- Ethereum-style addresses beginning with "0x" are converted
  to lowercase.
- Other values retain their case, preserving case-sensitive
  identifiers such as Solana addresses.

Normalization follows the format of the value itself rather
than relying on the platform label. Missing voter values
remain missing.

Removing the Ethereum chain prefix allows the same address
to match across chains. This defines identity at the address
level; it does not establish that matched addresses represent
the same person or organization, or link different addresses
controlled by one participant.

The votes file is processed in chunks of one million rows.
Identifiers and selected fields, including vote dates and
weights, are read as text to avoid inconsistent type inference
and rounding of large voting-power values.

Vote cleaning transforms columns without removing rows.
The pipeline compares the numbers of rows read and written
and raises an error if they differ. Deduplicating voter–
deployment pairs and applying the activity filter occur later,
during network construction.
## 4. Node and edge construction
The node set includes every deployment in deployments_clean.csv,
including those without recorded votes. Deployments found in
votes_clean.csv but absent from the catalogue are also added.
On v5, this produces 86,495 nodes: 86,489 catalogue entries
and six additional deployments.

Each node is identified by deployment_id. Catalogue nodes retain
their platform, name, proposals_count, unique_voters and
votes_count attributes. The in_catalogue flag distinguishes
catalogue entries from the additional deployments, whose
unavailable metadata remain missing.

The retained voter and vote counts are catalogue metadata,
not values recomputed from votes.csv. They must therefore
be distinguished from the vote-based community sizes used
for Jaccard and the corrected hub analysis.

Edge construction begins by extracting distinct
(voter, deployment_id) pairs from votes_clean.csv.
Repeated votes by the same wallet within one deployment
do not increase its contribution to an edge.

Wallets participating in between two and 100 deployments
are retained for edge generation. For each retained wallet,
every unordered pair of its deployments receives one unit
of shared-voter weight. Contributions from different wallets
are then summed for each pair.

For example, a wallet participating in deployments A, B and C
contributes one unit to A–B, A–C and B–C, regardless of how many
proposals it voted on in each deployment. Consequently, total
edge weight counts shared-wallet contributions across pairs,
rather than distinct wallets or individual votes.

The resulting network is undirected, with no self-loops.
An edge exists when at least one retained wallet participates
in both deployments. Its shared_voters weight is the number
of distinct retained wallets they share.

The node and edge tables are saved as nodes.csv and edges.csv.
NetworkX builds the graph from these tables, preserving
isolated nodes. Edges with endpoints absent from the node
table are skipped with a warning. The v5 reference graph
contains 700,304 edges.
## 5. Activity filtering and edge weighting
The activity filter limits the contribution of wallets that
participate in unusually many deployments. A wallet appearing
in k deployments can contribute to k(k−1)/2 deployment pairs,
so a small number of highly active wallets can account for
a substantial share of total edge weight.

Sensitivity analyses compared thresholds of 50, 100 and
200 deployments with an unfiltered configuration. The reference
threshold remains max_daos = 100. On v5, it excludes 321 wallets
and reduces the identified group's share of total edge weight
from 30.4% without filtering to 0.9%.

Of the excluded wallets, 319 belong to the identified group
and two do not. This threshold is a methodological compromise,
not a classification of wallets as bots or proof of an optimal
cut-off. Its effects on connectivity are considered in the
analysis.

Each relationship retains its shared_voters count and receives
a complementary Jaccard similarity:

Jaccard(A, B) = shared_voters /
               (voters_A + voters_B - shared_voters)

Community sizes are computed from distinct voter–deployment
pairs in votes_clean.csv, rather than catalogue metadata.
Wallets participating in more than 100 deployments are excluded
from both the shared-voter counts and the community sizes.

Wallets participating in only one deployment are included in
its community size, although they cannot create an edge.
This preserves the distinction between the whole retained
community and the subset that overlaps with other deployments.

Shared-voter counts measure absolute overlap, while Jaccard
measures overlap relative to the union of the two communities.
Both are retained in edges_jaccard.csv because they describe
different aspects of a relationship.

The normalization analysis in S3-07 additionally restricts its
comparisons to edges with at least 10 shared voters and defines
high values using a top-5% cut. These are analysis settings;
they do not remove edges from the reference graph.

## 6. Validation and reproducibility
The reference pipeline runs from the repository root, with
the dependencies in requirements.txt installed and the three
Zenodo v5 CSV files available in data/raw/:

```bash
python -m src.pipeline.run_pipeline --max-daos 100
```

It performs cleaning, node generation, edge generation,
Jaccard calculation and graph diagnostics in that order.
The same max_daos value is passed to edge generation and
Jaccard calculation to keep their populations consistent.

The --skip-cleaning option reuses existing cleaned files.
It should only be used when those files correspond to the
intended dataset version and cleaning procedure. Running
the pipeline regenerates the processed output files.

Validation combines several checks:

- Vote cleaning checks that the numbers of rows read and
  written are equal.
- Jaccard validation checks every edge for missing community
  sizes, impossible shared-voter counts, inconsistent union
  bounds and values outside the interval (0, 1].
- Selected edges are recalculated using explicit voter-set
  intersections and unions. The selection includes extreme
  cases and a random sample with a fixed seed.
- Graph diagnostics report node and edge counts, isolated
  nodes, connected components, degree statistics, self-loops
  and the size of the largest component.

A separate check of the saved Jaccard table verifies its
arithmetic and agreement with the pairs and shared-voter
counts in edges.csv:

```bash
python -m analysis.s3_07_v5_comparison.check_jaccard_consistency
```

The v5 reference results are 86,495 nodes, 700,304 edges,
total shared-voter weight 10,682,356, 35,277 isolated nodes,
36,263 connected components and 46,722 nodes in the largest
component. S3-07 reports that a full pipeline run on a second
computer reproduced these values.

These checks establish internal consistency and support
reproducibility. They do not establish completeness of the
source data or validate the real-world meaning of every
relationship. Graph diagnostics report measurements rather
than automatically asserting agreement with the reference
values.

## 7. Analysis and visualization
Analysis examines voter activity, sensitivity to the filtering
threshold, hub rankings, differences between shared-voter counts
and Jaccard similarity, and isolation by platform. S3-06 and
S3-07 repeat the earlier analyses on v5, while S3-08 gathers
descriptive tables and figures.

Hub interpretation distinguishes community size, proportional
overlap, filter dependence and known organizational relationships.
The corrected v5 hub indicators use community sizes calculated
from votes.csv. Rankings must be compared using the same graph,
edge selection and weighting measure.

A complementary network connects deployments that share proposal
authors. Its construction uses distinct author–deployment pairs
from cleaned proposals, lowercases author identifiers and counts
each author once per deployment pair. Unlike the voter network,
the current author analysis applies no maximum-deployment activity
filter. Tally and Realms lack author information, which limits
comparability. Direct comparison of the two networks remains
pending in S3-11.

The interactive voter-network view can be opened from the
repository root:

```bash
python -m src.visualization.network_visualization
```

By default, the visualization selects the 50 deployments with
the highest degree, retains up to 100 of the strongest edges
between them, and displays the largest connected component
of that selection. Nodes without retained edges and smaller
components are omitted.

Command-line options control the platform, number of candidate
nodes, maximum number of edges and minimum shared-voter count.
When a platform is selected, candidate nodes are ranked by
degree within that platform.

Node colour indicates platform. Node size represents degree
in the full graph, and edge width represents shared-voter
count, both scaled within the displayed view. Clicking a node
shows its identifiers, catalogue metadata and full-graph degree;
clicking an edge shows its endpoints and shared-voter count.

The layout uses a fixed random seed. Positions support visual
exploration and should not be interpreted as a quantitative
distance between communities. The displayed subgraph is a
selection of prominent relationships, not the entire network.

Static figures and descriptive tables are produced by the
S3-08 output scripts. The view supports highlighting a selected node's displayed
neighbours, showing Jaccard alongside shared-voter counts
on edges, and resetting the selection by clicking empty space.
The S3-08 figure export was also checked successfully.

## 8. Main findings and limitations
The v5 reference graph contains 86,495 deployment nodes and
700,304 shared-voter edges. Of its 35,277 isolated nodes,
20,409 have no recorded votes and 14,868 have votes but no
connections under the selected filter. These situations
require different interpretations.

The dataset update changes which deployments appear most
prominent. It also supports retaining max_daos = 100 as the
reference configuration: this threshold substantially reduces
the identified wallet group's contribution while retaining
approximately 99.995% of observed wallets.

Shared-voter counts and Jaccard similarity provide complementary
views. Among relationships with at least 10 shared voters,
the top 100 edges under the two measures have no edges in common.
Consequently, neither measure alone provides a sufficient basis
for interpreting the importance of a deployment.

Several limitations remain:

- Source coverage is imperfect. Some Snapshot proposals lack
  vote rows, and Tally vote counts disagree with metadata.
- Catalogue voter counts differ from the populations used
  to construct edges. Vote-based sizes are required for
  consistent overlap calculations.
- Address matching does not identify people or resolve all
  cross-chain identities. Multiple deployments may also
  represent the same organization.
- Filtering changes connectivity, and analysis thresholds
  are methodological choices.
- Missing author information for Tally and Realms limits
  comparisons between author and voter networks.
- New hub identities and the revised selection of representative
  hubs require team review.
- The visualization shows a selected subgraph and cannot
  establish patterns for the entire network on its own.

The resulting networks describe observed participation overlap.
They do not by themselves demonstrate collaboration, influence,
common ownership or coordinated behaviour.

The consolidated interpretation is documented in
[S3-09](S3-09_consolidated_results.md).
