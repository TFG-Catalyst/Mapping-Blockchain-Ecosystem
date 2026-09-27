# Data Dictionary

Dataset: *Mapping Decentralized Autonomous Organization Governance Across Chains: An Updated, Multi-Platform Dataset* (Farin, Hassan & Arroyo), MSR 2026.
Source: https://doi.org/10.5281/zenodo.18430339 - collection cut-off October 2025.
Collection code: https://github.com/mashiat0808/DAOGovernance/

Three CSV files. Platforms covered: Aragon, DAOHaus, DAOstack, Realms, Snapshot, Tally.

| File | Rows | Columns | Grain |
| :---- | ----: | ----: | :---- |
| `deployments.csv` | 86,489 | 9 | one row per DAO deployment |
| `proposals.csv` | 370,133 | 8 | one row per governance proposal |
| `votes.csv` | 11,638,348 | 8 | one row per individual vote |

Row counts for `deployments` and `proposals` were verified directly. The `votes.csv`
count was obtained by chunked reading (see S1-01); note that the dataset description on
Zenodo mentions roughly 66 million votes, so this discrepancy is still open.

Rows per platform:

| Platform | Deployments | Proposals |
| :---- | ----: | ----: |
| snapshot | 71,952 | 244,886 |
| tally | 4,394 | 37,839 |
| realms | 4,224 | 21,153 |
| daohaus | 3,459 | 46,936 |
| aragon | 2,402 | 15,746 |
| daostack | 58 | 3,573 |

---

## deployments.csv

One row per DAO. This is the node table.

| Column | Meaning | Nulls | Useful for DAO-to-DAO relationships? |
| :---- | :---- | ----: | :---- |
| `deployment_id` | Unique identifier of the DAO. No duplicates. | 0 | **Yes** - this is the node itself |
| `platform` | Governance platform hosting the DAO | 0 | Supporting - needed to tell apart the same organisation on different platforms |
| `name` | Display name of the DAO | 3,138 | **Yes**, with care - names repeat and some are generic |
| `proposals_count` | Number of proposals in the DAO | 0 | No - node attribute / filtering |
| `unique_voters` | Number of distinct voters | 0 | No - node attribute / filtering |
| `votes_count` | Total votes cast | 0 | No - node attribute / filtering |
| `estimated_vp` | Estimated total voting power. Meaning not documented. | 71,952 | No |
| `website` | DAO website or explorer link | 12,135 | No |
| `additional` | Extra metadata (social links, version…). Contents differ by platform. | 69,797 | No |

**Quality notes**

- `estimated_vp` is missing for **exactly all 71,952 Snapshot rows and for no row of any
  other platform**. The field is platform-dependent, not randomly missing.
- Among the non-missing values, `estimated_vp` contains 13 infinite values and 9,254
  zeros, so it is not usable as a magnitude without cleaning.
- `unique_voters` is typed as float64 despite having no missing values.
- The distribution has a very long tail: the median DAO has 1 proposal and 1 voter,
  19,826 DAOs have no voters at all, and only 7,886 have 10 or more voters
  (2,271 have 100 or more). Any meaningful network will need an activity threshold.

---

## proposals.csv

One row per proposal. Links each proposal to its DAO and to its author.

| Column | Meaning | Nulls | Useful for DAO-to-DAO relationships? |
| :---- | :---- | ----: | :---- |
| `proposal_id` | Identifier of the proposal. **Not unique** - see notes. | 0 | Not directly |
| `deployment_id` | DAO the proposal belongs to | 20,112 | **Yes** - links proposal to DAO |
| `platform` | Platform of the proposal | 0 | Supporting |
| `date` | Proposal creation timestamp | 79 | No (useful for time-sliced networks later) |
| `votes_count` | Number of votes received | 0 | No |
| `total_vp` | Total voting power used on the proposal | 20,112 | No |
| `author` | Address that created the proposal | 58,992 | **Yes** - the same address can propose in several DAOs |
| `platform_deployment_id` | Alternative DAO identifier, platform-specific | 350,021 | **Yes** - fallback when `deployment_id` is missing |

**Quality notes**

- The 20,112 rows with a missing `deployment_id` are **all Snapshot**, and they are
  exactly the rows where `platform_deployment_id` is filled. Snapshot proposals identify
  their DAO through `platform_deployment_id`. The same 20,112 rows account for all
  missing `total_vp` values. Using `platform_deployment_id` as a fallback leaves zero
  proposals without a DAO identifier.
- Separately, **37,954 proposals carry a `deployment_id` that does not exist in
  `deployments.csv`** (37,635 Tally, 319 Snapshot). These proposals can still act as
  nodes, but without node metadata. Whether to keep or drop them is an open decision.
- `author` is missing for **all 37,839 Tally proposals and all 21,153 Realms
  proposals**, and for no row of any other platform. Any relationship built on shared
  authorship is therefore restricted to Snapshot, DAOHaus, Aragon and DAOstack.
- `proposal_id` is duplicated across 30,996 rows, **all of them Tally**; 5,823 rows are
  exact duplicates across every column. Deduplication is needed before counting.
- Date range: 2018-10-27 to 2025-11-21. Distinct authors: 145,348.

---

## votes.csv

One row per vote. Not loaded in full; columns reviewed on a partial read, so the notes
below are marked as unverified where they have not been checked against the whole file.

| Column | Meaning | Useful for DAO-to-DAO relationships? |
| :---- | :---- | :---- |
| `vote_id` | Unique identifier of the vote | No |
| `proposal_id` | Proposal being voted on | Supporting - links vote to proposal |
| `deployment_id` | DAO in which the vote was cast | **Yes** - tells which DAO the vote belongs to |
| `platform` | Platform of the vote | Supporting |
| `date` | Vote timestamp | No (useful for time-sliced networks later) |
| `voter` | Voter identity - see notes | **Yes** - the key to finding voters active in several DAOs |
| `choice` | Option voted for (e.g. TRUE / FALSE on Aragon) | No |
| `weight` | Voting power used by the voter | Not for creating edges; potentially for weighting them |

**Quality notes**

- `choice` is present in the file but does not appear in the Zenodo field description.
- **Unverified:** `voter` does not hold the voter address alone. Observed format is the
  proposal address, then the literal `-voter-`, then the actual address. It needs to be
  split before it can be used as an identity. Observed on Aragon rows only; the format on
  other platforms has not been checked.
- **Unverified:** `weight` appears to be expressed in the token's smallest unit
  (1e+18 = 1 token). Since each DAO uses its own token, raw weights are not comparable
  across DAOs and would need normalisation (for example, as a share of the total voting
  power of that DAO).

---

## Is there a members table?

No. There is no table of DAO members.

The closest available object is the list of **voters** per DAO, which can be derived from
`votes.csv` by taking each distinct pair of `deployment_id` and `voter` (with the real
address already extracted). `deployments.unique_voters` gives only the count, not the
identities.

This is a list of voters, not of members: anyone who belongs to a DAO but has never voted
does not appear.
