# Mapping Blockchain Ecosystem

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
python src/network_visualization.py
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
python src/network_visualization.py --platform snapshot --top-n 30 --max-edges 50 --min-shared-voters 100
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
python src/network_visualization.py --help
```

If loading fails because `nodes.csv` is missing the `in_catalogue` column,
regenerate it from `deployments_clean.csv` and `votes_clean.csv`:

```bash
python src/node_generator.py
```

This overwrites `data/processed/nodes.csv` with the current node structure.
