# Mapping Blockchain Ecosystem

DAO-to-DAO network built from the voters that DAOs share, using the MSR 2026
DAO governance dataset (Zenodo).

## Repository structure

```
src/                      Reusable code
  paths.py                Single definition of the project folders
  pipeline/               Raw CSVs -> clean CSVs -> nodes/edges -> graph
    data_loader.py          Read the raw CSVs from data/raw/
    wallet_normalization.py Turn the `voter` field into a wallet address
    data_cleaner.py         Clean deployments, proposals and votes
    node_generator.py       data/processed/nodes.csv
    edge_generator.py       data/processed/edges.csv (shared voters)
    jaccard_weights.py      data/processed/edges_jaccard.csv (S2-05)
    graph_builder.py        nodes.csv + edges.csv -> NetworkX graph
    graph_sanity.py         Basic checks of the graph
  visualization/
    network_visualization.py Interactive view of the graph (S2-11..S2-13)
analysis/                 One folder per backlog item; scripts reproduce its results
  common/                 Code shared by several tasks (explore_shared_voters.py)
  s2_03_voter_activity/
  s2_04_graph_sensitivity/
  s2_06_normalization_effect/
  s2_07_shared_authors/
  s2_09_ecosystem_hubs/
  s2_14_edge_weight_comparison/
notebooks/                Exploration and data-quality notebooks
docs/                     One document per backlog item, data dictionary, figures/
results/                  Tables produced by the analysis scripts
data/raw/, data/processed/ Dataset and generated files (not in git)
```

## How to run the code

Always run from the repository root, as a module (`python -m`, with dots
instead of slashes and without `.py`). This puts the root on Python's import
path, so every module can import any other one as `src.pipeline.<module>`
or `analysis.<folder>.<module>`.

```bash
python -m src.pipeline.node_generator
python -m src.pipeline.edge_generator
python -m src.pipeline.jaccard_weights
python -m src.pipeline.graph_sanity
```

The clean CSVs in `data/processed/` (`deployments_clean.csv`,
`proposals_clean.csv`, `votes_clean.csv`) are currently generated from
`notebooks/02_data_quality.ipynb`.

## Development Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Jupyter notebooks

When running the notebooks in VS Code, select the Python interpreter from the `.venv` virtual environment as the Jupyter kernel.

## Graph visualization and filters (S2-12 and S2-13)

Run from the project root with the virtual environment activated and
`data/processed/nodes.csv` and `data/processed/edges.csv` available:

```bash
python -m src.visualization.network_visualization
```

Click a node to view its name, ID, platform, unique voters, votes, and
number of connections in the full graph. Click an edge to view the two
connected DAOs and their shared voters. Details appear inside the plot;
node selection takes priority when clicking near an endpoint.

Available options:

| Option | Description | Default |
| --- | --- | --- |
| `--top-n` | Maximum number of DAOs selected by degree | `50` |
| `--max-edges` | Maximum number of relationships displayed | `100` |
| `--min-shared-voters` | Minimum shared voters per relationship | `1` |
| `--platform` | `all`, `snapshot`, `tally`, or `aragon` | `all` |

All numeric options must be integers greater than zero. For example:

```bash
python -m src.visualization.network_visualization --platform snapshot --top-n 30 --max-edges 50 --min-shared-voters 100
```

When a platform is selected, DAOs are ranked by their degree within that
platform. Relationships between the selected DAOs are filtered by the
minimum shared voters, then the strongest remaining relationships are
displayed up to the edge limit. Nodes without a selected relationship
are omitted, so fewer than `--top-n` nodes may appear.

If no relationships match the filters, the program prints
`No relationships match the selected filters.` and exits without opening a plot.

To list the command-line options:

```bash
python -m src.visualization.network_visualization --help
```

If loading fails because `nodes.csv` is missing the `in_catalogue` column,
regenerate it from `deployments_clean.csv` and `votes_clean.csv`:

```bash
python -m src.pipeline.node_generator
```

This overwrites `data/processed/nodes.csv` with the current node structure.
