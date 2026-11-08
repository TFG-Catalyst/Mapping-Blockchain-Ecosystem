"""
S3-08 - The two figures that were never saved: isolation by platform (S2-10) and the graph view (S2-11).

  docs/figures/S3-08_fig1_isolation_by_platform.png   from table 4 of make_tables.py
  docs/figures/S3-08_fig2_graph_view_all.png          the view of network_visualization.py, saved instead of shown

network_visualization.py is not changed: its plt.show() is replaced here by a function that saves the figure.
Building the graph takes about 3 minutes (it is step 5 of the pipeline: graph_builder.py reads the edges one by one).

Run from the project root:  python -m analysis.s3_08_outputs.make_figures
"""

import matplotlib
matplotlib.use("Agg")                          # no window, the figures are only saved
import matplotlib.pyplot as plt
import pandas as pd

from src.paths import FIGURES_DIR, RESULTS_DIR
from src.pipeline.graph_builder import build_graph
from src.visualization.network_visualization import visualize_top_daos


def isolation_figure():
    table = pd.read_csv(RESULTS_DIR / "S3-08" / "S3-08_table4_isolation_by_platform.csv", index_col="platform")
    shares = 100 * table[["connected", "votes_no_edges", "no_votes"]].div(table["nodes"], axis=0)
    ax = shares.plot.barh(stacked=True, figsize=(9, 4.6), width=0.62, color=["#287ce4", "#e95c24", "#b5b4ae"])
    ax.invert_yaxis()                                              # first platform on top
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of the deployments of the platform")
    ax.set_ylabel("")
    ax.set_title("Connected, isolated and inactive deployments by platform (graph v5, max_daos = 100)", loc="left", fontsize=11)
    ax.legend(["connected", "votes but no edges (isolated)", "no votes in votes.csv"], frameon=False,
              loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)
    ax.figure.tight_layout()
    ax.figure.savefig(FIGURES_DIR / "S3-08_fig1_isolation_by_platform.png", dpi=160)


def graph_view_figure():
    plt.show = lambda: plt.gcf().savefig(FIGURES_DIR / "S3-08_fig2_graph_view_all.png", dpi=160, bbox_inches="tight")
    visualize_top_daos(build_graph())              # default view: 100 strongest relationships among the top 50 DAOs


if __name__ == "__main__":
    isolation_figure()
    graph_view_figure()
