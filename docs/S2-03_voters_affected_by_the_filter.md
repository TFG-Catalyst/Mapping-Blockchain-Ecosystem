# S2-03 — Characterize the voters affected by the filter

**Sprint:** Sprint 2
**Track:** A — Carlos
**Start date:** 2026-10-11
**Status:** Completed on 2026-10-11 (steps 1 to 4, quantification and decision on configurations)
**Script:** `scripts/analyze_voter_activity.py` (reuses `load_voters` from `explore_shared_voters.py`, with its cache)

Goal (according to the backlog): analyze in how many distinct DAOs each voter takes part using the full dataset, examine the distribution and representative cases near or above the threshold of 200 DAOs, identify the participation that the filter excludes without automatically treating very active wallets as invalid, and choose alternative configurations based on evidence.

Starting data: the full `votes.csv` (11,638,348 rows), 1,629,408 unique wallets.

> **Reproducibility note.** `votes.csv` and `deployments.csv` (in `data/raw/`), the voter cache (`data/processed/voters_cache.pkl`) and the edge files `results/S2-04/edges_<config>.csv` (about 22 MB each) are not included in the repository. The S2-00 preparation note (an earlier working note on the script) is not included either. All the results of this document are regenerated with `python scripts/analyze_voter_activity.py --cases --pattern --thresholds`, run from the repository root. **Caveat:** the printed tables of steps 3 and 3d were computed when the default threshold of the script was 200; it is now 100 (`DEFAULT_MAX_DAOS_PER_VOTER` in `scripts/explore_shared_voters.py`), so the console output of those steps differs. To reproduce them exactly, set that constant temporarily to 200.

---

## Summary and decision

**Conclusions**

1. Voter activity has a long tail: almost all wallets take part in few DAOs (the 99.9th percentile is 26 DAOs). **The threshold of 200 does not match any natural cut** in the distribution (step 2).
2. The 319 wallets with more than 100 DAOs are **all** from the same group: they vote in almost the same DAOs (mostly small ones), only on Snapshot, with one vote per DAO, within a few weeks in April–May 2022 (steps 3 and 3d). Another 150 wallets with fewer DAOs also follow the pattern, although they contribute very little weight.
3. Of the 8 wallets reviewed by hand on Etherscan (steps 3b, 3c and 3e), all were created in one of two windows (≈ 4 Apr 2021 or ≈ 1–5 Jun 2021) and two are funded directly by the most active wallet. This is consistent with a coordinated group, but it **does not prove a single operator or automation**.
4. The filter of 200 leaves out 91 wallets: 0.23% of the vote rows, but 26.9% of the graph weight and 43,843 edges (6.8%). And it **leaves in 228 wallets of the group**, which still contribute 31.8% of the weight of the current graph.
5. Between 101 and 200 DAOs there is no wallet outside the group; below ≈ 75 DAOs the filter starts excluding "other" wallets without removing more of the group (step 4).

**Decision (confirmed by Carlos on 2026-10-11): four configurations for S2-04**

| Configuration | Reason |
|---|---|
| no limit | Reference: what happens if nothing is filtered (the group contributes 50.2% of the weight) |
| 200 | Sprint 1 result, so it can be compared |
| 100 | No side effect: excludes the 319 wallets of the group with more than 100 DAOs (the group drops to 1.9% of the weight) |
| 50 | Sensitivity control: excludes 39 more wallets of the group at the cost of 76 "other" wallets |

The graphs are nested (each configuration contains the previous one), so edges can only appear or gain weight when the threshold goes up. 300, 150 and 75 are discarded (no new information), as are thresholds of 40 or less, including the p99.9 = 26 (they exclude hundreds or thousands of "other" wallets without removing more of the group).

**Limitations that must appear in the report**

- The "group" is defined by behavior (the DAO list of the most active wallet), not by on-chain evidence; it is partly circular when evaluating a filter by number of DAOs.
- The 76 "other" wallets between 51 and 100 DAOs have not been reviewed: they may be another coordinated group or very active legitimate users.
- The weight is a sum per wallet, not a count of distinct edges.
- The manual review covers 8 wallets out of a group of 469.

---

## Step 1 — Distribution by activity band (done)

For each wallet, `n` = number of distinct DAOs in which it has voted (the size of its set of `deployment_id`) is computed. Result (`results/S2-03/S2-03_activity_distribution.csv`):

| Band (number of DAOs) | Voters | % | Cumulative % |
|---|---|---|---|
| 1 | 1,240,517 | 76.13 | 76.13 |
| 2 | 208,460 | 12.79 | 88.93 |
| 3–5 | 127,788 | 7.84 | 96.77 |
| 6–10 | 33,812 | 2.08 | 98.84 |
| 11–50 | 18,397 | 1.13 | 99.97 |
| 51–100 | 115 | 0.007 | 99.98 |
| 101–200 | 228 | 0.014 | 99.99 |
| 201–300 | 90 | 0.006 | 100.00 |
| >300 | 1 | 0.0001 | 100.00 |

Percentiles: p50 = 1, p90 = 3, p99 = 12, p99.9 = 26 DAOs; maximum = 353 DAOs.

- % = percentage of wallets in the band over the total; cumulative % = percentage of wallets with that number of DAOs or fewer.
- The bands are a starting choice (ends at 1, 2, 100, 200, 300 to see the effect of the current threshold); they can be changed in the `BANDS` list of the script.
- Consistency with S1-04: 388,891 wallets in 2+ DAOs (23.87%) and 91 wallets above 200 (90 in 201–300 + 1 in >300).

## Step 2 — Log-log histogram (done)

Files: `results/S2-03/S2-03_activity_histogram.png` and `results/S2-03/S2-03_frequency_by_n_daos.csv` (exact data of the chart: `n_daos`, `voters`, one value for each n present).

Reading the chart:

- From 2 to about 50 DAOs, the points follow an almost straight line on a log-log scale: the number of wallets falls regularly as the number of DAOs increases (long-tail distribution).
- From ~50 DAOs on there are only between 1 and ~25 wallets for each value of n: the tail is sparse and noisy.
- **There is no natural cut at 200**: the threshold line crosses a tail that looks the same on both sides (wallets with 150–200 DAOs look like those with 201–300).
- Small groups of wallets with an almost identical number of DAOs can be seen (around 112–116, 140–155 and 229–233 DAOs). This is only a visual observation: it could indicate wallets with similar behavior, but it has not been checked. It will be reviewed when examining concrete cases.

Technical details: both axes on a logarithmic scale because the values go from 1 to 1.2 million; `matplotlib` is imported inside the function and, if it is not installed, the script warns (`pip install matplotlib`) without failing.

## Step 3 — Concrete cases: very active wallets (done)

The **319 wallets with 100 or more DAOs** are studied (228 enter the graph with the filter of 200 used at the time; 91 are left out). For them `votes.csv` is read again (≈40 s) and the following is computed per wallet: platforms, total votes, votes per DAO, percentage of DAOs where it voted only once, dates, days with activity and percentage of its votes concentrated on its best day.

Run with `python scripts/analyze_voter_activity.py --cases`. Full result: `results/S2-03/S2-03_highly_active_wallets.csv` (one row per wallet).

**Observed facts**

| Feature | 100–200 DAOs (inside the graph) | >200 DAOs (excluded) |
|---|---|---|
| Wallets | 228 | 91 |
| Median votes | 172 | 293 |
| Votes per DAO | 1.36 | 1.29 |
| DAOs with a single vote | 82% | 84% |
| Median days with votes | 2 | 5 |
| Wallets with ≥50% of their votes on one day | 156 | 83 |
| Solana / Ethereum addresses | 0 / 228 | 0 / 91 |

- The two sides of the threshold are very similar: 200 does not separate two different behaviors.
- All 319 wallets are Ethereum addresses; 288 vote only on Snapshot.
- Their activity almost always starts on the same dates: 193 on 2022-04-25, 97 on 2022-04-27 and 25 on 2022-04-29. For 199 of them the last vote is from May 2022.
- The 5 most active (353, 267, 245, 244 and 233 DAOs) vote between April and June 2022, with 233–484 votes in total and only 6–8 days with activity.
- The DAO sets of the 30 most active wallets are almost identical (Jaccard similarity: median 0.97, minimum 0.51).
- Among the 319 wallets they use only 415 distinct DAOs, and 33 of them appear in at least 80% of the wallets (7 in all 319).
- Those 33 DAOs are small: median of 4 proposals and 363 unique voters (minimum 331). Since the group already contributes about 319 voters, **most of the voters of those DAOs are these same wallets**.
- Names such as `0xueli`, `huxueli`, `0xchenhu` and `兔子洞投票任务专用` (own translation, to be confirmed: "exclusive for the Rabbit Hole voting task") suggest spaces created by individuals or for voting tasks.

**Interpretation (hypothesis, unchecked)**

Everything is consistent with a **coordinated voting campaign across many small Snapshot spaces** (for example, to complete tasks in exchange for a reward), with wallets that behave almost the same. There is no proof that they are bots, nor of the intent. A manual review in a block explorer is still missing.

**Consequence for the graph (hypothesis to verify in S2-04):** a group of almost identical wallets that share the same DAOs creates heavily weighted edges between small DAOs that have no other relationship. Those edges reflect the campaign, not a real relationship between the communities.

**Technical details**

- `read_votes_of()` makes a single pass over `votes.csv` and only accumulates data of the wallets of interest; the rest are discarded as soon as it is checked that they are not in the set.
- `summarize_wallet()` checks with an `assert` that the number of DAOs matches that of the cache.
- `choose_cases()` takes 10 wallets from the 150–250 range spread at regular intervals (deterministic).
- The DAO names come from `deployments.csv`, which must be at `data/raw/deployments.csv`; if it is missing, they are shown by id.

## Step 3b — Manual review on Etherscan (done by Carlos, 2 wallets)

Carlos reviewed the two most active wallets on Etherscan (screenshots of 2026-10-11).

| | `0xbd2a18…b086d` (353 DAOs) | `0xd3d0e2…8db24` (267 DAOs) |
|---|---|---|
| Balance | 0 ETH | 0 ETH |
| Tokens | 53 tokens, value < $1 | 47 tokens, value < $1 |
| First transaction sent | 5 years and 190 days ago (≈ April 2021) | same |
| Last transaction sent | 3 years and 122 days ago (≈ June 2023) | same |
| Funded by | **Binance** | **wallet `0xbd2a18…b086d`** (the first one) |

**Facts**

- The second wallet was funded by the first, and the first by Binance, on the same day on which both made their first transaction. That coincidence of dates is not by chance: it is a consequence of one having funded the other.
- Both are empty and only keep token dust (< $1).
- Snapshot votes are not visible on Etherscan: they are off-chain signatures and cost no gas. The Etherscan dates (2021–2023) are not those of the votes (April–June 2022, according to `votes.csv`); the on-chain activity surrounds the voting activity.
- The dates are approximate because Etherscan shows relative times.

**Check with the project data:** for each of the 319 wallets, the fraction of its DAOs that are also among those of wallet #1 was measured. The median is 1.00 and all 319 exceed 80%: **wallet #1 votes in practically all the DAOs where any of the others votes**.

**Reading (well-founded hypothesis, not proof of automation)**

- There is a direct funding link between the two wallets, and the 319 vote in subsets of the same DAOs. This strongly supports that **they are controlled by the same entity**.
- It does not prove that they are bots. What it does support is that they are not 319 independent voters.
- This fits an account farm (several wallets of a single operator voting in a list of spaces), but the motive is unchecked.

**Consequence for the project:** counting these wallets as independent voters overestimates the relationship between the DAOs they share. For S2-04, the filter by number of DAOs is only an approximation to a problem of coordinated wallets. It should be stated as a limitation in the report.

## Step 3c — Manual review on Etherscan of 3 wallets that ARE inside the graph

Carlos reviewed 3 wallets that the filter of 200 lets through (screenshots of 2026-10-11; approximate dates, computed from relative times).

| Wallet (DAOs) | Funded by | First tx sent | Last tx sent | Balance |
|---|---|---|---|---|
| `0x9088eb…8acd` (168) | `dappio.eth` | ≈ 4 Apr 2021 | ≈ 10 Jun 2023 | 0 ETH, 36 tokens ($0.29) |
| 153 DAOs (according to Carlos; the screenshot shows only the ENS name `erzii.eth`, without the full address) | **`0xbd2a18…b086d` (wallet #1)** | ≈ 5 Jun 2021 | ≈ 10 Jun 2023 | 0 ETH, 33 tokens ($1.1) |
| 110 DAOs (according to Carlos; the screenshot does not show the address) | `Disperse.app` | ≈ 4 Jun 2021 | ≈ 25 Jul 2022 | 0.004 ETH (≈ $10.5) |

**Facts**

- The wallet with 153 DAOs was funded directly by wallet #1. Wallet #1 has 353 DAOs and the filter excludes it; the wallet funded by it does enter the graph.
- The wallets with 168 and 153 DAOs, like the two reviewed in 3b, have their last transaction on the same date (≈ June 2023, one day apart). The one with 168 also has its first transaction on the same day as wallets #1 and #2.
- The wallet with 168 DAOs was funded by another address (`dappio.eth`), not by #1. There is no verified direct link.
- The wallet with 110 DAOs was funded by `Disperse.app`, a tool to send funds to many addresses in a single transaction. It has a different calendar (last tx in 2022) and some balance.
- According to `votes.csv`, that wallet with 110 DAOs voted **only on 2022-04-27** (144 votes in one day).

**Reading (hypothesis, not proof)**

- There is at least one wallet inside the graph with a direct funding link to #1. The filter by individual wallet **leaves part of the coordinated network inside**, because each wallet on its own is below the threshold.
- The one with 168 DAOs shares a calendar with the group, but without a direct link: circumstantial evidence.
- The one with 110 DAOs cannot be associated with the same group with these data. Being funded through `Disperse.app` indicates a distribution of funds to several addresses, but legitimate users also use it.

**Consequence:** besides the DAO threshold, S2-04 must measure what part of the graph depends on a group of wallets with the same pattern (same DAOs, same period), even if each wallet is under the threshold.

## Step 3d — How many more wallets follow the same pattern? (done)

Run with `python scripts/analyze_voter_activity.py --pattern` (it only uses the cache; ≈5 s).

**Method.** The reference wallet is the one that votes in the most DAOs (`0xbd2a18…b086d`, 353 DAOs). For each wallet with 5 or more DAOs (72,847 wallets) the *containment* is computed: the fraction of its DAOs that are in the reference's list. A wallet is considered to "follow the pattern" if the containment is ≥ 0.8. The threshold of 5 DAOs prevents a high containment from being a coincidence in wallets with 1–2 DAOs.

**Results**

Distribution of the containment: 71,125 wallets between 0.0 and 0.1; 469 between 0.8 and 1.0; between 0.3 and 0.8 there are only 179. The separation is clear: almost all wallets either have no relationship with the list, or are almost completely inside it.

| Band of DAOs | Wallets | With pattern | % | Weight they contribute | Total band weight |
|---|---|---|---|---|---|
| 5–9 | 50,896 | 108 | 0.2% | 1,566 | 868,622 |
| 10–19 | 18,267 | 0 | 0% | 0 | 1,601,410 |
| 20–49 | 3,240 | 3 | 0.1% | 2,303 | 1,135,747 |
| 50–99 | 125 | 39 | 31.2% | 81,807 | 262,276 |
| 100–200 | 228 | 228 | 100% | 1,977,604 | 1,977,604 |
| >200 (excluded) | 91 | 91 | 100% | 0 (outside the graph) | 0 |

("Weight" = sum of the weights of the edges contributed by each wallet = n·(n−1)/2 per wallet. Only wallets with ≤ 200 DAOs count, which are those that enter the graph.)

- The 319 wallets studied in step 3 all follow the pattern, and 42 more appear with fewer than 100 DAOs (39 with 50–99 and 3 with 20–49).
- **469 wallets (0.64% of those evaluated) contribute 2,063,280 of the 6,480,605 weight points of the graph at the time (31.8%).** Almost all comes from the 228 wallets with 100–200 DAOs, which the filter of 200 leaves inside.
- With the filter of 200, the 91 excluded wallets would contribute about 2.38 M of additional weight if they were included.
- The 108 wallets with 5–9 DAOs and containment ≥ 0.8 contribute a negligible weight (1,566). **They are not interpreted:** they may be a coincidence (some DAOs of the list are common) or part of the group; there is no evidence.

**Caveats**

- The weight is a sum per wallet, not a count of distinct edges. The wallets of the group share the same DAOs, so their weight is concentrated in few edges. The effect on the number of edges is measured in S2-04.
- Part of the 31.8% is due to the weight growing with the square of the number of DAOs: a wallet with 150 DAOs weighs ≈ 11,000 times what one with 2 does.
- The reference list comes from a single wallet. The 42 new wallets with fewer than 100 DAOs are associated by behavior, with no on-chain verification.
- Full list: `results/S2-03/S2-03_wallets_with_pattern.csv` (`wallet`, `n_daos`, `daos_in_reference_list`, `containment`).

**Technical details**

- `pairs_of(n)` returns n·(n−1)/2. Each pair of DAOs of a wallet adds 1 to the weight of an edge.
- The reference is chosen with `max(..., key=len)`; there are no hand-written addresses.
- `daos & reference_list` is the intersection of two sets; its size divided by the number of DAOs of the wallet is the containment.

## Step 3e — Manual review of 3 wallets with the pattern and 50–99 DAOs

Carlos reviewed on Etherscan 3 wallets that follow the pattern (step 3d) and that the filter leaves inside the graph. Approximate dates (relative times as of 2026-10-11).

| Wallet (DAOs) | Funded by | First tx | Last tx | Balance |
|---|---|---|---|---|
| `0x664401…d32e` (62) | `0x7a172c2C…c3308a800` | ≈ 4 Apr 2021 | ≈ 29 Jul 2021 | 0 ETH, 4 tokens ($0) |
| `0x965d9f…547c` (65) | `0x0A1433b3…A494D11A2` | ≈ 1 Jun 2021 | ≈ 10 Aug 2021 | 0 ETH, 2 tokens ($0) |
| `0xbd204a…6eb6` (71) | `0x52dccc92…05282D5e5` | ≈ 4 Apr 2021 | ≈ 21 Apr 2022 | 0.002 ETH (≈ $5.5), 7 tokens ($2.5) |

**Facts**

- None is funded by wallet #1; each by a different address, on the same day as its first transaction.
- **Creation dates (first transaction) of the 8 wallets reviewed so far:** all fall in one of two narrow windows: ≈ 4 Apr 2021 (#1, #2, 168 DAOs, 62 DAOs and 71 DAOs) or ≈ 1–5 Jun 2021 (153, 110 and 65 DAOs).
- The **last** transaction dates do not coincide: ≈ Jun 2023 (#1, #2, 168 and 153 DAOs), Jul 2022 (110), Jul–Aug 2021 (62 and 65) and Apr 2022 (71).
- For the wallets with 62 and 65 DAOs the last on-chain transaction is from 2021, before the voting (April–May 2022). Since Snapshot votes are not transactions, this is compatible with wallets that were inactive on-chain and only signed votes.

**Reading (circumstantial, not conclusive)**

- Coinciding in one of two creation windows is an unlikely pattern by chance among 8 wallets that also vote in almost the same DAOs. It supports that they form a group, but it does not prove a single operator.
- There is no direct funding link for these 3 wallets. It would remain to check whether the three addresses that funded them have anything in common.
- Summary of the manual review (8 wallets): 2 funded directly by #1; 8 of 8 with a creation date in one of two windows; 3 with a different source of funds; 1 of them (110 DAOs) without evidence of belonging to the group except the voting pattern.

## Step 4 — Threshold comparison table (done)

Run with `python scripts/analyze_voter_activity.py --thresholds` (it only uses the cache; ≈5 s). A wallet is **excluded** if it has **more** DAOs than the threshold. "Group" = the 469 wallets that follow the pattern (step 3d). "Others" = excluded wallets that are not in the group (side effect). "Weight" = sum of the weights of the edges (n·(n−1)/2 per wallet).

| Threshold | Excluded | From the group | Others | Group inside the graph | Graph weight | % of weight from the group |
|---|---|---|---|---|---|---|
| no limit | 0 | 0 | 0 | 469 | 8,863,095 | 50.2% |
| 300 | 1 | 1 | 0 | 468 | 8,800,967 | 49.8% |
| **200 (current at the time)** | 91 | 91 | 0 | 378 | 6,480,605 | 31.8% |
| 150 | 129 | 129 | 0 | 340 | 6,034,679 | 26.8% |
| **100** | 319 | 319 | 0 | 150 | 4,503,001 | 1.9% |
| 75 | 337 | 319 | 18 | 150 | 4,438,804 | 1.9% |
| **50** | 434 | 358 | 76 | 111 | 4,252,975 | 0.1% |
| 40 | 594 | 359 | 235 | 110 | 4,095,110 | 0.1% |
| 30 | 1,115 | 361 | 754 | 108 | 3,793,870 | 0.0% |
| 26 (p99.9) | 1,581 | 361 | 1,220 | 108 | 3,613,379 | 0.0% |
| 20 | 3,182 | 361 | 2,821 | 108 | 3,200,358 | 0.0% |
| 10 | 18,831 | 361 | 18,470 | 108 | 1,643,968 | 0.1% |

(Total: 1,629,408 wallets. Full table in `results/S2-03/S2-03_threshold_comparison.csv`.)

**Reading**

1. **There is no wallet outside the group with more than 100 DAOs:** the 319 wallets with more than 100 DAOs are all in the group. Excluding above 100 has no side effect according to the pattern.
2. With 200 (the Sprint 1 threshold), the group still contributes 31.8% of the weight; with 100 it drops to 1.9%. The 228 wallets between 101 and 200 DAOs are all in the group.
3. Below ≈ 75 DAOs the side effect appears: 18 "others" at 75, 76 at 50. The group hardly improves (from 319 to 358 excluded).
4. The statistical threshold p99.9 = 26 DAOs (step 1) excludes 1,220 "others" and only 3 more wallets of the group compared with 50. With 10, 18,470 "others".
5. The group is not exhausted: the 108 wallets with 5–9 DAOs that follow the pattern are not removed by any reasonable threshold. Their weight is negligible (step 3d) and they are not interpreted.

**Proposed configurations for S2-04** (pending confirmation at the time)

| Configuration | Reason |
|---|---|
| no limit | Reference: what happens if nothing is filtered (the group contributes 50.2% of the weight) |
| 200 | Sprint 1 result (comparability) |
| 100 | No side effect: removes the 319 wallets of the group with more than 100 DAOs |
| 50 | Conservative option: removes 39 more wallets of the group in exchange for 76 "others" |

Discarded: 300, 150 and 75 (intermediate points with no new information); 40 and lower, including the p99.9 = 26 (they exclude hundreds or thousands of "other" wallets and hardly remove more of the group).

**Caveats**

- The "group" is defined by behavior (same DAO list as the most active wallet), not by on-chain evidence. It is partly circular: a filter by number of DAOs is evaluated with a group that has many DAOs. The manual check of 8 wallets (steps 3b, 3c and 3e) supports the group, but does not prove it.
- The "others" have not been reviewed: they may be another coordinated group or very active legitimate users (for example, delegates). There is no evidence in either direction.
- The weight is a sum, not a count of distinct edges. The number of edges per configuration is measured in S2-04.

## Quantification of what the filter of 200 excludes (done)

What the Sprint 1 threshold leaves out (91 wallets with more than 200 DAOs), compared with not filtering.

| Measure | Excluded by the filter | Total without filter | % excluded |
|---|---|---|---|
| Wallets | 91 | 1,629,408 | 0.006% |
| Vote rows (`votes.csv`) | 26,899 | 11,638,348 | 0.23% |
| (wallet, DAO) pairs | 20,828 | 2,721,671 | 0.77% |
| Edge weight (pairs of DAOs) | 2,382,490 | 8,863,095 | 26.9% |
| Distinct edges that only exist because of them | 43,843 | 646,138 | 6.8% |

How it was obtained: wallets, (wallet, DAO) pairs and weight come from the cache (steps 2 and 4); the vote rows, from summing the `votes` column of `S2-03_highly_active_wallets.csv` for the 91 wallets with more than 200 DAOs; the edges, from comparing the no-limit CSV with the one for threshold 200 (646,138 versus 602,295; the second loses none, see the note `S2-00`, not included in this repository).

**Reading:** the filter leaves out a minimal part of the participation (0.23% of the vote rows) but a large part of the structure of the graph: a quarter of the weight and 7 out of every 100 distinct edges. The cause is that each wallet contributes n·(n−1)/2 pairs, so a few wallets with hundreds of DAOs generate many edges.

## Pending in S2-03

- [x] Representative cases (step 3).
- [x] Manual review of the 2 most active wallets (step 3b).
- [x] Review 3 wallets that are inside the graph (step 3c).
- [x] Measure how many more wallets follow the same pattern (step 3d; only the DAO list was used, not the dates).
- [x] Quantify what the filter of 200 excludes: wallets, vote rows, pairs and edges that only exist because of them (previous section). The edge count for each alternative threshold is left for S2-04.
- [x] Configurations confirmed by Carlos: no limit, 200, 100 and 50 (see "Summary and decision").

For S2-04 (not pending items of S2-03):

- Build a graph per configuration and measure edges, weights, hubs and connected components.
- Optional: review the 76 "other" wallets between 51 and 100 DAOs if the results between 100 and 50 differ.
- Check with Rodrigo (S2-05/06) the name of the threshold parameter and the format of the edge CSV.

## Changelog

| Date | Change | Files |
|---|---|---|
| 2026-10-11 | Step 1: distribution by band and percentiles | `scripts/analyze_voter_activity.py`, `results/S2-03/S2-03_activity_distribution.csv` |
| 2026-10-11 | Step 2: log-log histogram and frequency table | `scripts/analyze_voter_activity.py`, `results/S2-03/S2-03_activity_histogram.png`, `results/S2-03/S2-03_frequency_by_n_daos.csv` |
| 2026-10-11 | Step 3: analysis of the 319 wallets with 100+ DAOs (option `--cases`) | `scripts/analyze_voter_activity.py`, `results/S2-03/S2-03_highly_active_wallets.csv` |
| 2026-10-11 | Step 3b: manual review on Etherscan of 2 wallets and overlap check with #1 | this document |
| 2026-10-11 | Step 3c: manual review of 3 wallets inside the graph | this document |
| 2026-10-11 | Step 3d: wallets that follow the reference pattern (option `--pattern`) | `scripts/analyze_voter_activity.py`, `results/S2-03/S2-03_wallets_with_pattern.csv` |
| 2026-10-11 | Step 3e: manual review of 3 wallets with the pattern and 50–99 DAOs; correction of the translation of `兔子洞投票任务专用` | this document |
| 2026-10-11 | Step 4: threshold comparison table (option `--thresholds`); function `evaluate_containment()` extracted from step 3d | `scripts/analyze_voter_activity.py`, `results/S2-03/S2-03_threshold_comparison.csv` |
| 2026-10-11 | Quantification of what is excluded by the filter of 200 (wallets, vote rows, pairs, weight and edges) | this document |
| 2026-10-11 | Closing of S2-03: summary, decision on the 4 configurations and completed status | this document |
| 2026-10-16 | English version for the repository: file names, script names, options and CSV columns translated; numbers use English formatting | all files of S2-03 |
