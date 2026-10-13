# Data Dictionary

Dataset: *Mapping Decentralized Autonomous Organization Governance Across Chains: An Updated, Multi-Platform Dataset* (Farin, Hassan & Arroyo), MSR 2026.
Source: https://doi.org/10.5281/zenodo.18430339. Collection cut-off October 2025.
Collection code: https://github.com/mashiat0808/DAOGovernance/

Three CSV files. Platforms covered: Aragon, DAOHaus, DAOstack, Realms, Snapshot, Tally.

| File | Rows | Columns | Grain |
| :---- | ----: | ----: | :---- |
| `deployments.csv` | 86,489 | 9 | one row per DAO deployment |
| `proposals.csv` | 370,133 | 8 | one row per governance proposal |
| `votes.csv` | 11,638,348 | 8 | one row per individual vote |

Row counts for `deployments` and `proposals` were verified directly. The `votes.csv`
count was obtained by chunked reading (see `notebooks/01_dataset_inspection.ipynb`). The roughly 66 million votes
mentioned on Zenodo are the sum of the `votes_count` metadata, not rows of
`votes.csv`; see "Coverage of votes.csv" below.

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
| `deployment_id` | Unique identifier of the DAO. No duplicates. | 0 | **Yes**: this is the node itself |
| `platform` | Governance platform hosting the DAO | 0 | Supporting: needed to tell apart the same organisation on different platforms |
| `name` | Display name of the DAO | 3,138 | **Yes**, with care: names repeat and some are generic |
| `proposals_count` | Number of proposals in the DAO | 0 | No: node attribute / filtering |
| `unique_voters` | Number of distinct voters | 0 | No: node attribute / filtering |
| `votes_count` | Total votes cast | 0 | No: node attribute / filtering |
| `estimated_vp` | Estimated total voting power. Meaning not documented. | 71,952 | No |
| `website` | DAO website or explorer link | 12,135 | No |
| `additional` | Extra metadata (social links, version…). Contents differ by platform. | 69,797 | No |

**Quality notes**

- `estimated_vp` is missing for **exactly all 71,952 Snapshot rows and for no row of any
  other platform**. The field is platform-dependent, not randomly missing.
- Among the non-missing values, `estimated_vp` contains 13 infinite values and 9,254
  zeros, so it is not usable as a magnitude without cleaning.
- `unique_voters` is typed as float64 despite having no missing values.
- `name` is not reliable as a label: a Tally deployment on chain 10 with 78,724 unique
  voters is named `test`.
- The distribution has a very long tail: the median DAO has 1 proposal and 1 voter,
  19,826 DAOs have no voters at all, and only 7,886 have 10 or more voters
  (2,271 have 100 or more). Any meaningful network will need an activity threshold.

---

## proposals.csv

One row per proposal. Links each proposal to its DAO and to its author.

| Column | Meaning | Nulls | Useful for DAO-to-DAO relationships? |
| :---- | :---- | ----: | :---- |
| `proposal_id` | Identifier of the proposal. **Not unique**, see notes. | 0 | Not directly |
| `deployment_id` | DAO the proposal belongs to | 20,112 | **Yes**: links proposal to DAO |
| `platform` | Platform of the proposal | 0 | Supporting |
| `date` | Proposal creation timestamp | 79 | No (useful for time-sliced networks later) |
| `votes_count` | Number of votes received | 0 | No |
| `total_vp` | Total voting power used on the proposal | 20,112 | No |
| `author` | Address that created the proposal | 58,992 | **Yes**: the same address can propose in several DAOs |
| `platform_deployment_id` | Alternative DAO identifier, platform-specific | 350,021 | **Yes**: fallback when `deployment_id` is missing |

**Quality notes**

- The 20,112 rows with a missing `deployment_id` are **all Snapshot**, and they are
  exactly the rows where `platform_deployment_id` is filled. Snapshot proposals identify
  their DAO through `platform_deployment_id`. The same 20,112 rows account for all
  missing `total_vp` values. Using `platform_deployment_id` as a fallback leaves zero
  proposals without a DAO identifier.
- **Tally identifiers differ in letter case between files.** In `deployments.csv` Tally
  `deployment_id` values are stored in lowercase, while `proposals.csv` and `votes.csv`
  use the mixed-case checksum form of the same address
  (`eip155:5:0x16449fc3...` vs `eip155:5:0x16449fC3...`). A direct join fails for all
  37,635 Tally proposals; lowercasing both sides recovers every one of them. Any join
  between files must normalise `deployment_id` to lowercase first.
- After that normalisation, only **319 proposals** (all Snapshot, e.g. `mimo.eth`) point
  to a DAO that is genuinely absent from `deployments.csv`. Whether to keep or drop them
  is an open decision.
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
| `proposal_id` | Proposal being voted on | Supporting: links vote to proposal |
| `deployment_id` | DAO in which the vote was cast | **Yes**: tells which DAO the vote belongs to |
| `platform` | Platform of the vote | Supporting |
| `date` | Vote timestamp | No (useful for time-sliced networks later) |
| `voter` | Voter identity, see notes | **Yes**: the key to finding voters active in several DAOs |
| `choice` | Option voted for (e.g. TRUE / FALSE on Aragon) | No |
| `weight` | Voting power used by the voter | Not for creating edges; potentially for weighting them |

**Quality notes**

- `choice` is present in the file but does not appear in the Zenodo field description.
- The format of `voter` **depends on the platform** and must be normalised before it can
  be used as an identity. Verified over the full file in S1-04:

  | Platform | Votes | `voter` format | Normalisation |
  | :---- | ----: | :---- | :---- |
  | snapshot | 8,883,118 | plain Ethereum address `0x…` | lowercase |
  | tally | 1,597,604 | CAIP-10 `eip155:<chain_id>:0x…` | strip prefix, lowercase |
  | realms | 1,067,333 | Solana address, base58 | none (case-sensitive) |
  | daohaus | 51,129 | plain Ethereum address `0x…` | lowercase |
  | aragon | 26,833 | `<deployment_id>-voter-0x…` | keep part after `-voter-`, lowercase |
  | daostack | 12,331 | plain Ethereum address `0x…` | lowercase |

  Realms addresses belong to a different blockchain and never match Ethereum ones, so
  Realms DAOs can only connect among themselves.
- `deployment_id` for Tally votes uses the mixed-case checksum form, as in
  `proposals.csv`; see the case note above.
- **Unverified:** `weight` appears to be expressed in the token's smallest unit
  (1e+18 = 1 token). Since each DAO uses its own token, raw weights are not comparable
  across DAOs and would need normalisation (for example, as a share of the total voting
  power of that DAO).

---
## Coverage of votes.csv (S2-01)

Analysis in `notebooks/03_votes_coverage.ipynb`.

| Platform | Declared (`deployments.votes_count`) | Rows in `votes.csv` | Coverage |
| :---- | ----: | ----: | ----: |
| aragon | 26,833 | 26,833 | 100% |
| daohaus | 51,129 | 51,129 | 100% |
| daostack | 12,331 | 12,331 | 100% |
| realms | 1,067,333 | 1,067,333 | 100% |
| tally | 1,440,390 | 1,597,604 | 110.9% |
| snapshot | 64,697,595 | 8,883,118 | 13.7% |
| **total** | 67,295,611 | 11,638,348 | 17.3% |

**Snapshot.** Compared proposal by proposal with `proposals.csv`, which declares
65,716,576 Snapshot votes (the two metadata tables do not agree). About 56.8 million
votes are missing:

- 54,749,561 (96.3%) belong to 1,040 proposals with more than 6,000 declared votes
  and no rows in `votes.csv`. Another 13 such proposals are truncated at exactly 6,000
  rows. No Snapshot proposal with more than 6,000 votes is complete.
- 2,050,741 (3.6%) belong to 16,736 smaller proposals that also have no rows. No cause
  was identified; this remains an open uncertainty.
- Missing votes are concentrated in 2023 (81%) and in six spaces (92%):
  `magicappstore.eth`, `stgdao.eth`, `arbitrumfoundation.eth`, `linea-build.eth`,
  `aavedao.eth` and `opcollective.eth`.
- 12 proposal ids have votes in `votes.csv` but are absent from `proposals.csv`.

**Tally.** `votes.csv` holds 157,214 more votes than declared. They are not duplicates
(every `vote_id` is unique; only 559 repeated `(proposal_id, voter)` pairs) and do not
come from deployments missing from the catalogue. Counts disagree in both directions
for 1,035 of 4,394 deployments: 190,512 votes above declared in 101 deployments and
33,298 below in 934. The largest difference (+110,795) is the chain-10 deployment named
`test`. Metadata and votes were probably collected at different times; this could not
be verified.

**Population represented.** For Aragon, DAOhaus, DAOstack and Realms, `votes.csv` is
the full population. For Snapshot, it covers proposals with up to about 6,000 votes,
minus an unexplained set of smaller proposals; mass-participation proposals are
excluded. For Tally, it is close to complete but does not match the metadata
deployment by deployment.

**Implications.**

- Large Snapshot spaces enter the graph with a small fraction of their voters
  (e.g. `arbitrumfoundation.eth` 6.7%, `aavedao.eth` 20.6%; `linea-build.eth` 0%), so
  their shared-voter edges are underestimated.
- Metadata counters (`votes_count`, `unique_voters`) describe a different population
  from the graph edges and must not be combined with measures computed from
  `votes.csv`.
- Snapshot is only 13.7% covered, so comparisons between platforms must take this into
  account.

---

## Is there a members table?

No. There is no table of DAO members.

The closest available object is the list of **voters** per DAO, which can be derived from
`votes.csv` by taking each distinct pair of `deployment_id` and `voter` (with the real
address already extracted). `deployments.unique_voters` gives only the count, not the
identities.

This is a list of voters, not of members: anyone who belongs to a DAO but has never voted
does not appear.
