# S3-09 - Consolidated analysis of round-1 results

**Data:** Zenodo v5.
**Sources:** S3-06, S3-07 and S3-08.

## 1. Purpose and scope

This document brings together the filtering, hub, normalization and
descriptive results obtained with Zenodo v5. It examines which conclusions
from Sprint 2 remain supported, which change with the updated data, and
which limitations must be considered when interpreting the network.

The reference shared-voter graph uses max_daos = 100 and contains
86,495 deployment nodes and 700,304 edges. Nodes represent deployments,
so they should not automatically be interpreted as distinct organizations.

## 2. Effect of the dataset update

Zenodo v5 contains 67,340,666 vote rows, approximately 5.8 times the
number in v4. Snapshot coverage reaches 99.8% of the votes declared
in the deployment metadata. This addresses the previous Snapshot
undercoverage limitation, although agreement with metadata does not
by itself establish that the dataset is complete.

The update changes which deployments appear most connected. Only
six of the previous top ten remain in the rankings by degree and
weighted degree reported in S3-06. Newly prominent deployments include
Linea, Yoginth and Crypto435, whose large voting communities were
underrepresented in v4.

These differences should be interpreted as an effect of the dataset
update, rather than evidence that the ecosystem changed over time.
The comparison concerns two dataset versions, not two separate
observation periods.

Other findings persist: a small group of wallets participates in
hundreds of deployments, and rankings based on shared-voter counts
differ substantially from those based on Jaccard similarity.
The following sections examine these findings separately.

## 3. Interpretation of the activity filter

The results support retaining max_daos = 100 as the reference
configuration. On v5, the identified group of wallets contributes
30.4% of the total edge weight without filtering, compared with
0.9% under this threshold. The filter excludes 321 of the
6,509,336 distinct wallets, retaining approximately 99.995%.

Of the excluded wallets, 319 belong to the identified group and
two do not. Therefore, the earlier conclusion that the filter
excludes only members of that group no longer holds exactly.

Lowering the threshold to 75 leaves the group's contribution at
0.9%, at the reported precision, while increasing the number of
excluded wallets outside the group from 2 to 29. A threshold of
50 reduces the group's contribution to 0.1%, but excludes 178
wallets outside it. Among these configurations, max_daos = 100
offers a reasonable balance between reducing the group's weight
and retaining other voters.

This is a methodological choice, not proof that the excluded
wallets are bots or that 100 is an optimal threshold. The filter
also affects connectivity: S3-05 reports 121 deployments that
become isolated solely because of it. Results must therefore
be interpreted as relationships observed under the selected
filter, rather than all relationships present in the vote data

## 4. Interpretation of hubs and edge weights

Shared-voter counts and Jaccard similarity describe different
aspects of a relationship. Counts measure the number of voters
shared by two deployments, whereas Jaccard measures that overlap
relative to the union of their voting communities.

The distinction remains important on v5. Among edges with at least
10 shared voters, the top 100 edges ranked by count and by Jaccard
have no edges in common. Crypto435 and Linea share 170,988 voters
but have a Jaccard value of 0.0588. In contrast, balsam and tarpon
share 6,070 voters and have a Jaccard value of approximately 0.998,
indicating almost identical voter sets.

Node rankings also depend on the measure. In S3-07, the top ten
deployments by summed shared-voter counts and by summed Jaccard
have no deployments in common. Counts tend to highlight large
communities, while summed Jaccard can highlight deployments
connected to many communities with nearly identical voter sets.
Neither ranking alone establishes organizational importance
or influence.

Community sizes must be computed from the same vote population
used to construct the graph. In S3-06, replacing deployment
metadata counts with counts derived from votes.csv changes the
community-size flag for 18 of the 60 hub candidates. ENS changes
from the stable category to the community-size category, while
Lido remains stable under the classification rules.

The consolidated interpretation therefore uses the corrected
vote-based indicators. The identities of the 11 new hub candidates
remain unverified, and a revised selection of representative hubs
requires team review. Similar voter sets alone do not establish
common ownership, coordination or a shared operator.

## 5. Interpretation of isolated deployments

The reference graph contains 35,277 isolated nodes. Of these,
20,409 have no votes recorded in the dataset, while 14,868 have
votes but no shared-voter edges under the selected filter.
These situations should be distinguished: absence of recorded
votes does not establish that a deployment is inactive outside
the dataset.

Among deployments with recorded votes, 22.5% are isolated.
This proportion varies across platforms: 16.1% for DAOhaus,
21.2% for Tally, 21.7% for Snapshot, 34.5% for DAOstack,
43.5% for Aragon and 46.3% for Realms.

These differences describe connectivity through shared voters
in the observed data. They do not demonstrate that one platform
is more collaborative than another. An isolated deployment may
still have relationships through shared authors, organizational
links or other mechanisms not captured by this graph.

## 6. What the shared-author network contributes

The shared-author analysis on v5 reports 139,679 distinct authors
and 28,359 edges, with a total edge weight of 37,919. These
aggregate results are unchanged from the previous analysis.
They describe overlap in proposal authorship, providing another
perspective on relationships between deployments.

Coverage limits the interpretation. Tally and Realms proposals
contain no author information, leaving 8,618 deployments without
observable author relationships. Their absence from author edges
must not be interpreted as evidence that they share no authors.

The smaller number of author edges does not by itself establish
that authorship is less interconnected than voting: the two
networks have different data coverage and construction rules.
A direct comparison of their common edges, distinctive
relationships and node rankings remains the purpose of S3-11.

## 7. Limitations and unresolved decisions

Several limitations remain relevant to the consolidated results:

- Tally vote rows represent 110.9% of the declared vote count.
  The cause of this discrepancy remains unverified.
- The hub classification script still uses deployment metadata
  for community sizes. The corrected vote-based results in S3-06
  should be used when interpreting the v5 hub candidates.
- The identities of 11 new hub candidates and the revised
  selection of representative hubs require team review.
- The minimum of 10 shared voters and the top-5% cut used in the
  normalization analysis are methodological choices. Conclusions
  from that analysis are conditional on these settings.
- Deployment nodes do not necessarily represent distinct
  organizations. The Mimo–Parallel Protocol case illustrates how
  duplicated proposals across names can create apparent overlap.
- The graph visualization displays a selected subset of strong
  relationships. It should not be treated as a representative
  view of the entire network.


## 8. Overall conclusion

The v5 results support retaining max_daos = 100 as the reference
filter and using shared-voter counts alongside Jaccard similarity.
The dataset update changes which deployments appear most
prominent, while preserving the finding that absolute overlap
and proportional similarity identify different relationships.

The network maps observed participation overlap between
deployments. Its interpretation requires distinguishing
community size, similar voter sets, organizational relationships
and missing data. Neither connectivity nor a high ranking alone
demonstrates influence, coordination or common ownership.

This synthesis provides a basis for the process document in
S3-10. The direct comparison between author and voter networks
remains pending in S3-11, together with team review of the
unresolved decisions listed above