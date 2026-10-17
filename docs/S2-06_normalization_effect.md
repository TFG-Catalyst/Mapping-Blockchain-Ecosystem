# S2-06: How normalization changes prominent relationships

**Script:** `src/normalization_comparison.py` 
**Figures:** `docs/figures/S2-06_*.png` 
**Input:** `edges_jaccard.csv` (S2-05, max_daos = 100)

## Method
Same reference graph, two weights: `shared_voters` (count, grows with community size) and `jaccard` (proportional overlap). Edges with fewer than 10 shared voters are excluded (`MIN_SHARED_VOTERS`, pending group decision): below that Jaccard is unstable and thousands of edges reach exactly 1.0. That leaves 41,759 edges. "High" means top 5% of those edges.

## Results
- **Prominent edges do not coincide.** None of the top 10, 50 or 100 edges by count is in the top 10, 50 or 100 by Jaccard; 7% at K = 500 and 10% at K = 1000 (`S2-06_top_k_overlap.png`).
- **Four types of edge** (`S2-06_scatter_count_vs_jaccard.png`): size effect 1,975 (high count, low Jaccard), proportional overlap 1,983 (high Jaccard, low count), both 115, neither 37,686.
- **Size effect examples:** arbitrum treasury - arbitrum core (86,230 voters, Jaccard 0.60, same organization) and PancakeSwap - Aave DAO (6,713 voters, Jaccard 0.04).
- **Proportional overlap examples:** Cube stone - Work Club 1 (190 voters, 0.86), and Tally deployments sharing the same 117 voters (Jaccard 1.0). Edges high on both are the balsam, tarpon, danhuacap, mists cluster (about 4,500 voters, Jaccard 0.98-0.99).
- **Prominent deployments change completely.** Strength = sum of edge weights. Top 10 and top 50 by count and by Jaccard share no deployment (`S2-06_rank_change_deployments.png`). By count the leaders are large organizations (Arbitrum, Aave, Uniswap, PancakeSwap); by Jaccard they are spaces such as VDP, miraidao or monsoul, each linked to 40-46 near-identical Snapshot spaces. The large organizations fall to ranks 350-800 by Jaccard.
- **S2-09 hubs:** Lido is 20th by count and 351st by Jaccard, ENS 34th and 392nd; balsam and tarpon are 19th and 21st by count and 145th and 144th by Jaccard.

## Interpretation
Neither measure alone identifies important deployments. Count rewards scale; summed Jaccard rewards membership in groups of near-identical communities, which may be one operator or a shared audience (cause unknown). Use both: count for how many voters connect two DAOs, Jaccard for how much of each community they represent, and flag clusters before reading either ranking as influence.

## Limits
`MIN_SHARED_VOTERS = 10` and the 5% cut are our choices. Large Snapshot DAOs are undercovered in votes.csv (S2-01), so their counts are lower bounds and their Jaccard is biased. The strength of a deployment is the sum of weights over its edges with at least 10 shared voters, not over all edges.
