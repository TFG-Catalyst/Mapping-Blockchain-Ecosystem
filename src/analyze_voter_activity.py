"""
S2-03 — Characterize the voters affected by the activity filter
================================================================
TFG - Sprint 2 (Track A)

Question this script answers: how many distinct DAOs does each voter have,
and which voters does the filter leave out (200 DAOs by default in
Sprint 1, 100 since S2-04)?

It is built in steps (each step is a function):
  STEP 1: distribution by bands of the number of distinct DAOs per voter.
  STEP 2: histogram (log-log scale) of the number of DAOs per voter.
  STEP 3: concrete cases: how very active wallets behave.
          (only with the --cases option: it re-reads votes.csv, ~1 min)
  STEP 3d: how many more wallets follow the same pattern as the group of 319
          (only with the --pattern option: it uses only the cache, takes seconds)
  STEP 4: comparison table of thresholds (what each cut-off excludes)
          (only with the --thresholds option: it uses only the cache, takes seconds)

How to use it (from the repository root, where data/raw/votes.csv lives):
    python scripts/analyze_voter_activity.py               # steps 1 and 2
    python scripts/analyze_voter_activity.py --cases       # steps 1, 2 and 3
    python scripts/analyze_voter_activity.py --pattern     # steps 1, 2 and 3d
    python scripts/analyze_voter_activity.py --thresholds  # steps 1, 2 and 4

Reuses the votes.csv reading (with its cache) from explore_shared_voters.py,
so the CSV is not read again if the cache already exists.

Writes to results/S2-03/ (created if it does not exist).
"""

import argparse
import csv
import math
import statistics
import sys
from collections import Counter
from datetime import date
from pathlib import Path

# We import our previous script as if it were a library to reuse its
# functions (load_voters, extract_address, is_excluded) and its paths
# (VOTES_CSV). It works because both scripts are in the same folder.
import explore_shared_voters as ev

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
OUTPUT_DIR = Path("results/S2-03")
OUTPUT_DISTRIBUTION = OUTPUT_DIR / "S2-03_activity_distribution.csv"
OUTPUT_FREQUENCY = OUTPUT_DIR / "S2-03_frequency_by_n_daos.csv"
OUTPUT_HISTOGRAM = OUTPUT_DIR / "S2-03_activity_histogram.png"
OUTPUT_WALLETS = OUTPUT_DIR / "S2-03_highly_active_wallets.csv"

# A number so large that no wallet reaches it. It is used as the maximum
# of the last band, which has no real upper limit.
VERY_LARGE = 1000000

# Step 3: all wallets with at least MIN_DAOS_CASES DAOs are studied;
# the "representative cases" are chosen between CASES_MIN and CASES_MAX DAOs
# (evenly spread).
MIN_DAOS_CASES = 100
CASES_MIN = 150
CASES_MAX = 250
N_CASES = 10
N_TOP = 5

# Step 3d: a wallet "follows the pattern" if at least CONTAINMENT_THRESHOLD of
# its DAOs are in the DAO list of the reference wallet (the most active one).
# Only wallets with MIN_DAOS_PATTERN DAOs or more are evaluated: with 1 or 2
# DAOs a high containment may be a coincidence.
OUTPUT_PATTERN = OUTPUT_DIR / "S2-03_wallets_with_pattern.csv"
MIN_DAOS_PATTERN = 5
CONTAINMENT_THRESHOLD = 0.8
# Bands for step 3d: (minimum, maximum, label)
PATTERN_BANDS = [
    (5, 9, "5-9"),
    (10, 19, "10-19"),
    (20, 49, "20-49"),
    (50, 99, "50-99"),
    (100, 200, "100-200"),
    (201, VERY_LARGE, ">200"),
]

# Step 4: thresholds being compared (a wallet is EXCLUDED if it has more
# DAOs than the threshold). 0 means "no limit".
OUTPUT_THRESHOLDS = OUTPUT_DIR / "S2-03_threshold_comparison.csv"
THRESHOLDS_TO_COMPARE = [0, 300, 200, 150, 100, 75, 50, 40, 30, 26, 20, 10]

# Chart colors (a single series -> a single color; the rest is neutral ink).
COLOR_SURFACE = "#fcfcfb"         # background
COLOR_TEXT_PRIMARY = "#0b0b0b"    # title and annotations
COLOR_TEXT_SECONDARY = "#52514e"  # axes and threshold line
COLOR_TEXT_MUTED = "#7a7974"      # footnote
COLOR_GRID = "#e6e5e1"            # grid and axes (almost invisible)
COLOR_ZONE = "#efeeea"            # zone excluded by the filter
COLOR_SERIES = "#2a78d6"          # the data points

# Activity bands: (minimum, maximum, label). "Activity" = number of distinct
# DAOs in which the wallet has voted. Both ends are included.
# The last band has no real maximum.
BANDS = [
    (1, 1, "1"),
    (2, 2, "2"),
    (3, 5, "3-5"),
    (6, 10, "6-10"),
    (11, 50, "11-50"),
    (51, 100, "51-100"),
    (101, 200, "101-200"),
    (201, 300, "201-300"),
    (301, VERY_LARGE, ">300"),
]

# Percentiles to compute (e.g. 99 = value below which 99 % of the voters lie).
PERCENTILES = [50, 90, 99, 99.9]


# ----------------------------------------------------------------------
# Small helper functions used in several steps
# ----------------------------------------------------------------------
def pairs_of(n):
    """Pairs of DAOs created by a wallet with n DAOs = n·(n-1)/2.
    Each pair adds exactly 1 to the weight of an edge, so this is what the
    wallet contributes to the total sum of weights of the graph."""
    return n * (n - 1) // 2


def get_n_daos(wallet_info):
    """Number of DAOs of a wallet (used to sort lists of wallets)."""
    return wallet_info["n_daos"]


def get_wallet(wallet_info):
    """Address of a wallet (used to sort lists of wallets)."""
    return wallet_info["wallet"]


def write_csv(path, header, rows):
    """Creates the folder if needed and writes a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


# ----------------------------------------------------------------------
# STEP 1: distribution of the number of DAOs per voter
# ----------------------------------------------------------------------
def daos_per_voter(voter_to_daos):
    """
    Returns a list with one number per wallet: in how many distinct DAOs it
    has voted. (Each value of the dictionary is a set of deployment_id, so
    its size is already "distinct DAOs".)
    """
    ns = []
    for daos in voter_to_daos.values():
        ns.append(len(daos))
    return ns


def table_by_bands(ns):
    """
    Counts how many wallets fall into each band of BANDS.
    Returns a list of rows: (label, wallets, % of total, cumulative %).
    """
    total = len(ns)

    # frequency[n] = how many wallets have exactly n DAOs. There are only a
    # few hundred distinct values of n, so summing by bands over this
    # dictionary is much faster than going through the million and a half
    # wallets once per band.
    frequency = Counter(ns)

    rows = []
    cumulative = 0
    for minimum, maximum, label in BANDS:
        wallets = 0
        for n, count in frequency.items():
            if minimum <= n <= maximum:
                wallets += count
        cumulative += wallets
        rows.append((label, wallets, wallets / total * 100, cumulative / total * 100))

    # Safety check: all voters must have fallen into some band (if not,
    # the bands have a gap).
    assert cumulative == total, "Some voters do not fall into any band"
    return rows


def percentile(sorted_ns, p):
    """
    Value below which (or equal to which) p % of the voters lie.
    "Nearest rank" method: with N sorted values, percentile p is the one in
    position ceil(p/100 * N) (counting from 1).
    """
    position = math.ceil(p / 100 * len(sorted_ns))   # position counting from 1
    if position < 1:
        position = 1
    return sorted_ns[position - 1]                   # -1: lists start at 0


def save_distribution(rows, path):
    csv_rows = []
    for label, wallets, pct, cumulative_pct in rows:
        csv_rows.append([label, wallets, f"{pct:.4f}", f"{cumulative_pct:.4f}"])
    write_csv(path, ["dao_band", "voters", "percent", "cumulative_percent"], csv_rows)
    print(f"\nDistribution saved to: {path.resolve()}")


def step1_distribution(ns):
    total = len(ns)
    print(f"Unique voters (wallets): {total:,}")

    connecting = 0
    for n in ns:
        if n >= 2:
            connecting += 1
    print(f"Voters in 2+ DAOs (the only ones that create edges): {connecting:,} "
          f"({connecting / total:.2%})")

    print("\n--- Distribution by activity band (number of distinct DAOs) ---")
    print(f"  {'band':>8} {'voters':>12} {'%':>10} {'cum. %':>10}")
    rows = table_by_bands(ns)
    for label, wallets, pct, cumulative_pct in rows:
        print(f"  {label:>8} {wallets:>12,} {pct:>9.4f}% {cumulative_pct:>9.4f}%")

    print("\n--- Percentiles (number of DAOs) ---")
    sorted_ns = sorted(ns)
    for p in PERCENTILES:
        print(f"  p{p:<5} = {percentile(sorted_ns, p)} DAOs")
    print(f"  maximum = {sorted_ns[-1]} DAOs")

    save_distribution(rows, OUTPUT_DISTRIBUTION)


# ----------------------------------------------------------------------
# STEP 2: histogram on a log-log scale
# ----------------------------------------------------------------------
def thousands_format(x):
    """1234567 -> '1,234,567' (thousands separator)."""
    return f"{x:,.0f}"


def format_tick(value, position):
    """Text shown on each axis tick of the chart (matplotlib calls this function)."""
    return thousands_format(value)


def frequency_by_n(ns):
    """
    {n: number of wallets that vote in exactly n DAOs}, sorted by n.
    It is what the histogram draws: one point for each distinct value of n.
    """
    counts = Counter(ns)
    frequency = {}
    for n in sorted(counts):
        frequency[n] = counts[n]
    return frequency


def save_frequency(frequency, path):
    """Saves the exact data of the chart (the 'table view' of the histogram)."""
    csv_rows = []
    for n, wallets in frequency.items():
        csv_rows.append([n, wallets])
    write_csv(path, ["n_daos", "voters"], csv_rows)
    print(f"Frequency by number of DAOs saved to: {path.resolve()}")


def draw_histogram(frequency, path, threshold):
    """
    Draws, with both axes on a logarithmic scale, how many wallets there are
    for each value of "number of distinct DAOs", and marks the filter
    threshold.

    Log scale: each axis tick is 10 times larger than the previous one. It
    is used because the data go from 1 wallet to 1.2 million wallets; on a
    normal scale almost all the points would be squashed against the axis.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")                 # draw to a file, without opening a window
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
    except ImportError:
        print("\nWARNING: matplotlib is missing, the histogram is not drawn. "
              "Install it with:  pip install matplotlib")
        return

    xs = list(frequency)                        # values of n (number of DAOs)
    ys = []                                     # number of wallets with that n
    for n in xs:
        ys.append(frequency[n])
    total = sum(ys)
    single_dao = frequency.get(1, 0)

    # Wallets above the threshold (the ones the filter leaves out)
    excluded = 0
    for n, count in frequency.items():
        if n > threshold:
            excluded += count

    fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.85, max(xs) * 1.25)
    ax.set_ylim(0.6, max(ys) * 4)

    # Zone the filter leaves out (more than `threshold` DAOs) and the threshold line.
    ax.axvspan(threshold, ax.get_xlim()[1], color=COLOR_ZONE, linewidth=0, zorder=0)
    ax.axvline(threshold, color=COLOR_TEXT_SECONDARY, linewidth=1, zorder=2)

    # The data: one point for each distinct value of n.
    ax.scatter(xs, ys, s=46, color=COLOR_SERIES,
               edgecolors=COLOR_SURFACE, linewidths=1.2, zorder=3)

    # Discreet axes and grid.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLOR_GRID)
    ax.spines["bottom"].set_color(COLOR_GRID)
    ax.grid(True, which="major", color=COLOR_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xticks([1, 2, 5, 10, 20, 50, 100, 200, 300])
    ax.set_yticks([1, 10, 100, 1000, 10000, 100000, 1000000])
    ax.xaxis.set_major_formatter(FuncFormatter(format_tick))
    ax.yaxis.set_major_formatter(FuncFormatter(format_tick))
    ax.minorticks_off()
    ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=10, length=0)
    ax.set_xlabel("Number of distinct DAOs the wallet votes in (logarithmic scale)",
                  color=COLOR_TEXT_SECONDARY, fontsize=10.5, labelpad=10)
    ax.set_ylabel("Number of wallets (logarithmic scale)",
                  color=COLOR_TEXT_SECONDARY, fontsize=10.5, labelpad=10)

    # Annotations: only the three that tell the story.
    ax.annotate(f"{thousands_format(single_dao)} wallets vote in only 1 DAO",
                xy=(xs[0], ys[0]), xytext=(14, 0), textcoords="offset points",
                va="center", ha="left", color=COLOR_TEXT_PRIMARY, fontsize=10)
    ax.text(threshold / 1.07, 300000,
            f"Current threshold: {threshold} DAOs\n"
            f"{excluded} wallets above it (excluded)",
            ha="right", va="center", color=COLOR_TEXT_PRIMARY, fontsize=10.5)
    arrow = dict(arrowstyle="-", color=COLOR_TEXT_MUTED, linewidth=0.8)
    ax.annotate(f"Maximum: {xs[-1]} DAOs ({ys[-1]} wallet)",
                xy=(xs[-1], ys[-1]), xytext=(-75, 70), textcoords="offset points",
                ha="right", va="bottom", color=COLOR_TEXT_PRIMARY, fontsize=10,
                arrowprops=arrow)

    # Title (with the finding), subtitle and footnote.
    fig.subplots_adjust(top=0.80, left=0.13, right=0.97, bottom=0.14)
    fig.text(0.13, 0.93,
             f"{single_dao / total * 100:.0f}% of wallets vote in a single DAO; "
             f"only {excluded} exceed {threshold}",
             color=COLOR_TEXT_PRIMARY, fontsize=15, fontweight="bold", ha="left")
    fig.text(0.13, 0.87,
             f"Number of distinct DAOs per wallet · {thousands_format(total)} wallets",
             color=COLOR_TEXT_SECONDARY, fontsize=11, ha="left")
    fig.text(0.13, 0.025,
             "Source: votes.csv. Each point is a distinct value of the number of DAOs; "
             "both axes on a logarithmic scale.",
             color=COLOR_TEXT_MUTED, fontsize=8.5, ha="left")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Histogram saved to: {path.resolve()}")


def step2_histogram(ns):
    frequency = frequency_by_n(ns)
    print("\n--- Histogram (log-log scale) ---")
    save_frequency(frequency, OUTPUT_FREQUENCY)
    draw_histogram(frequency, OUTPUT_HISTOGRAM, ev.DEFAULT_MAX_DAOS_PER_VOTER)


# ----------------------------------------------------------------------
# STEP 3: concrete cases (very active wallets)
# ----------------------------------------------------------------------
def load_dao_names(path):
    """
    {lowercase deployment_id: name} from deployments.csv.
    (Lowercased because in votes.csv some ids come with mixed case and in
    deployments.csv in lowercase.)
    If the file does not exist, it returns {} and the DAOs are shown by id.
    """
    names = {}
    if not path.exists():
        print(f"WARNING: cannot find {path}; DAOs will be shown by id only.")
        return names
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("name")
            if name is None:
                name = ""
            names[row["deployment_id"].lower()] = name.strip()
    return names


def read_votes_of(votes_csv, targets):
    """
    One pass over votes.csv that stores information ONLY for the wallets in
    `targets` (a set of already normalized addresses). For each one it accumulates:
      - how many votes there are on each platform,
      - how many votes there are in each DAO,
      - how many votes there are on each day (to see bursts),
      - first and last date.
    The rest of the wallets are ignored as soon as it is checked that they are
    not in `targets`, which is why it is a fast pass.
    """
    data = {}
    for wallet in targets:
        data[wallet] = {
            "platforms": Counter(),
            "votes_per_dao": Counter(),
            "days": Counter(),
            "first": None,
            "last": None,
        }

    row_number = 0
    with votes_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row_number += 1
            if row_number % 2000000 == 0:
                print(f"  ... {row_number:,} rows read", flush=True)

            if not row["voter"]:
                continue
            wallet = ev.extract_address(row["voter"])
            if wallet not in data:
                continue                      # not a wallet we are interested in
            info = data[wallet]

            info["platforms"][row["platform"]] += 1
            info["votes_per_dao"][row["deployment_id"]] += 1
            day = row["date"][:10]            # "2020-09-29 01:11:17" -> "2020-09-29"
            if day:
                info["days"][day] += 1
                if info["first"] is None or day < info["first"]:
                    info["first"] = day
                if info["last"] is None or day > info["last"]:
                    info["last"] = day
    return data


def summarize_wallet(wallet, info, n_daos, names):
    """Turns what has been accumulated for one wallet into a row of features."""
    votes = sum(info["votes_per_dao"].values())
    # Safety check: the cache and this pass must agree.
    assert len(info["votes_per_dao"]) == n_daos, f"{wallet}: distinct DAOs do not match"

    # In how many DAOs it has voted exactly once
    daos_single_vote = 0
    for count in info["votes_per_dao"].values():
        if count == 1:
            daos_single_vote += 1

    best_day = max(info["days"].values())
    first_day = date.fromisoformat(info["first"])
    last_day = date.fromisoformat(info["last"])
    total_days = (last_day - first_day).days + 1

    # The 3 DAOs where it has voted the most, with their name if we know it.
    top3 = []
    for dao, count in info["votes_per_dao"].most_common(3):
        label = names.get(dao.lower())
        if not label:
            label = dao[:14]
        top3.append(f"{label} ({count})")

    # Votes per platform, e.g. "snapshot 120 | tally 3"
    platform_texts = []
    for platform, count in info["platforms"].most_common():
        platform_texts.append(f"{platform} {count}")

    if wallet.startswith("0x"):
        address_type = "ethereum"
    else:
        address_type = "solana"

    return {
        "wallet": wallet,
        "address_type": address_type,
        "n_daos": n_daos,
        "votes": votes,
        "votes_per_dao": round(votes / n_daos, 2),
        "pct_daos_with_single_vote": round(daos_single_vote / n_daos * 100, 1),
        "platforms": " | ".join(platform_texts),
        "first_date": info["first"],
        "last_date": info["last"],
        "total_days": total_days,
        "days_with_votes": len(info["days"]),
        "votes_on_best_day": best_day,
        "pct_votes_on_best_day": round(best_day / votes * 100, 1),
        "top3_daos": "; ".join(top3),
    }


def choose_cases(rows, minimum, maximum, how_many):
    """
    Chooses `how_many` wallets with between `minimum` and `maximum` DAOs,
    evenly spread among those sorted by number of DAOs (so there are cases
    from the whole range and not just from one end). It is deterministic: the
    same ones always come out.
    """
    candidates = []
    for wallet_info in rows:
        if minimum <= wallet_info["n_daos"] <= maximum:
            candidates.append(wallet_info)
    candidates.sort(key=get_n_daos)

    if len(candidates) <= how_many:
        return candidates

    step = (len(candidates) - 1) / (how_many - 1)
    chosen = []
    for i in range(how_many):
        chosen.append(candidates[round(i * step)])
    return chosen


def short(wallet):
    """0x1234567890abcdef... -> 0x1234…cdef (so that it fits on screen)."""
    if len(wallet) <= 14:
        return wallet
    return f"{wallet[:6]}…{wallet[-4:]}"


def show_wallets(title, rows):
    print(f"\n--- {title} ---")
    print(f"  {'wallet':<14} {'DAOs':>5} {'votes':>6} {'v/DAO':>6} {'%1vote':>6} "
          f"{'days':>5} {'%best day':>10}  {'from':<10} {'to':<10}  platforms")
    for f in rows:
        print(f"  {short(f['wallet']):<14} {f['n_daos']:>5} {f['votes']:>6} "
              f"{f['votes_per_dao']:>6} {f['pct_daos_with_single_vote']:>5}% "
              f"{f['days_with_votes']:>5} {f['pct_votes_on_best_day']:>9}%  "
              f"{f['first_date']:<10} {f['last_date']:<10}  {f['platforms']}")


def median_of(rows, field):
    """Median of one column (field) over a list of wallet rows."""
    values = []
    for wallet_info in rows:
        values.append(wallet_info[field])
    return statistics.median(values)


def group_summary(name, rows):
    """Medians of the features of a group of wallets."""
    if len(rows) == 0:
        return

    solana = 0
    one_burst = 0
    for wallet_info in rows:
        if wallet_info["address_type"] == "solana":
            solana += 1
        if wallet_info["pct_votes_on_best_day"] >= 50:
            one_burst += 1

    print(f"\n  {name}: {len(rows)} wallets")
    print(f"    median votes: {median_of(rows, 'votes'):.0f} "
          f"| votes per DAO: {median_of(rows, 'votes_per_dao'):.2f} "
          f"| % of DAOs with a single vote: {median_of(rows, 'pct_daos_with_single_vote'):.0f}%")
    print(f"    median days with votes: {median_of(rows, 'days_with_votes'):.0f} "
          f"| wallets with >=50% of their votes on a single day: {one_burst}")
    print(f"    Solana addresses: {solana} | Ethereum: {len(rows) - solana}")


def step3_cases(voter_to_daos):
    # Wallets with MIN_DAOS_CASES DAOs or more
    targets = set()
    for wallet, daos in voter_to_daos.items():
        if len(daos) >= MIN_DAOS_CASES:
            targets.add(wallet)

    print(f"\n--- Concrete cases: wallets with {MIN_DAOS_CASES}+ DAOs ({len(targets)}) ---")
    print("Reading votes.csv (only data of those wallets is stored)...", flush=True)
    names = load_dao_names(ev.DEPLOYMENTS_CSV)
    data = read_votes_of(ev.VOTES_CSV, targets)

    rows = []
    for wallet in targets:
        n_daos = len(voter_to_daos[wallet])
        rows.append(summarize_wallet(wallet, data[wallet], n_daos, names))
    rows.sort(key=get_n_daos, reverse=True)

    OUTPUT_WALLETS.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_WALLETS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Full table saved to: {OUTPUT_WALLETS.resolve()}")

    # Split the wallets into those that enter the graph and those that do not
    threshold = ev.DEFAULT_MAX_DAOS_PER_VOTER
    inside_graph = []
    excluded_by_filter = []
    for wallet_info in rows:
        if wallet_info["n_daos"] <= threshold:
            inside_graph.append(wallet_info)
        else:
            excluded_by_filter.append(wallet_info)

    print("\n--- Group comparison (medians) ---")
    group_summary(f"{MIN_DAOS_CASES}-{threshold} DAOs (enter the graph)", inside_graph)
    group_summary(f">{threshold} DAOs (excluded by the filter)", excluded_by_filter)

    show_wallets(f"The {N_TOP} most active wallets", rows[:N_TOP])
    show_wallets(f"{N_CASES} cases between {CASES_MIN} and {CASES_MAX} DAOs "
                 f"(evenly spread)",
                 choose_cases(rows, CASES_MIN, CASES_MAX, N_CASES))


# ----------------------------------------------------------------------
# STEP 3d: how many more wallets follow the same pattern?
# ----------------------------------------------------------------------
def evaluate_containment(voter_to_daos):
    """
    Returns (reference_wallet, list_of_evaluated).

    The reference is the wallet with the most DAOs (it is not written by
    hand). For each wallet with MIN_DAOS_PATTERN DAOs or more the containment
    is computed:
        |its DAOs ∩ DAOs of the reference| / |its DAOs|
    Each element of the list is a dictionary with the keys:
    wallet, n_daos, inside (DAOs that are in the reference list), containment.
    """
    # Reference wallet = the one with the most DAOs
    reference = None
    most_daos = 0
    for wallet, daos in voter_to_daos.items():
        if len(daos) > most_daos:
            reference = wallet
            most_daos = len(daos)
    reference_list = voter_to_daos[reference]

    evaluated = []
    for wallet, daos in voter_to_daos.items():
        n = len(daos)
        if n < MIN_DAOS_PATTERN:
            continue
        inside = len(daos & reference_list)         # DAOs that both sets share
        evaluated.append({
            "wallet": wallet,
            "n_daos": n,
            "inside": inside,
            "containment": inside / n,
        })
    return reference, evaluated


def step3d_pattern(voter_to_daos):
    threshold = ev.DEFAULT_MAX_DAOS_PER_VOTER

    # 1) Reference wallet and containment of each wallet (see evaluate_containment).
    reference, evaluated = evaluate_containment(voter_to_daos)
    print("\n--- Pattern of the reference wallet ---")
    print(f"Reference: {reference} ({len(voter_to_daos[reference])} DAOs)")
    print(f"Looking for wallets (with {MIN_DAOS_PATTERN}+ DAOs) that have >= "
          f"{CONTAINMENT_THRESHOLD:.0%} of their DAOs inside that list.")
    print(f"Wallets evaluated: {len(evaluated):,}")

    # 2) Distribution of the containment in 10 intervals (0.0-0.1 ... 0.9-1.0).
    #    If there are two groups, two "piles" should be visible: one near 0 and one near 1.
    wallets_per_interval = [0] * 10
    for wallet_info in evaluated:
        interval = int(wallet_info["containment"] * 10)
        if interval > 9:
            interval = 9                 # containment 1.0 goes in the last interval
        wallets_per_interval[interval] += 1
    print("\nDistribution of the containment (number of wallets):")
    for i in range(10):
        print(f"  {i / 10:.1f} - {(i + 1) / 10:.1f}  {wallets_per_interval[i]:>9,}")

    # 3) Wallets that follow the pattern
    pattern = []
    for wallet_info in evaluated:
        if wallet_info["containment"] >= CONTAINMENT_THRESHOLD:
            pattern.append(wallet_info)
    print(f"\nWallets that follow the pattern: {len(pattern):,} of {len(evaluated):,}")

    # 4) The same, by band of number of DAOs.
    print(f"\n  {'band':<8} {'wallets':>9} {'w/ pattern':>11} {'%':>6} "
          f"{'weight they add':>17} {'total band weight':>18}")
    for low, high, label in PATTERN_BANDS:
        in_band = 0
        with_pattern = 0
        pattern_weight = 0
        band_weight = 0
        for wallet_info in evaluated:
            n = wallet_info["n_daos"]
            if n < low or n > high:
                continue
            in_band += 1
            follows_pattern = wallet_info["containment"] >= CONTAINMENT_THRESHOLD
            if follows_pattern:
                with_pattern += 1
            # Only wallets with n <= threshold count for the graph (the rest are excluded).
            if n <= threshold:
                band_weight += pairs_of(n)
                if follows_pattern:
                    pattern_weight += pairs_of(n)
        if in_band > 0:
            pct = with_pattern / in_band * 100
        else:
            pct = 0
        print(f"  {label:<8} {in_band:>9,} {with_pattern:>11,} {pct:>5.1f}% "
              f"{pattern_weight:>17,} {band_weight:>18,}")

    # 5) How much the pattern weighs in the current graph (threshold filter).
    total_weight = 0
    for daos in voter_to_daos.values():
        if len(daos) <= threshold:
            total_weight += pairs_of(len(daos))
    total_pattern_weight = 0
    for wallet_info in pattern:
        if wallet_info["n_daos"] <= threshold:
            total_pattern_weight += pairs_of(wallet_info["n_daos"])
    print(f"\nTotal edge weight of the graph (filter {threshold}): {total_weight:,}")
    print(f"Weight contributed by wallets with the pattern: {total_pattern_weight:,} "
          f"({total_pattern_weight / total_weight:.1%})")

    # 6) Save the list of wallets with the pattern: most DAOs first and, for
    #    the same number of DAOs, ordered by address. The second sort keeps
    #    the order of the first one for wallets with the same number of DAOs.
    pattern.sort(key=get_wallet)
    pattern.sort(key=get_n_daos, reverse=True)
    csv_rows = []
    for wallet_info in pattern:
        csv_rows.append([wallet_info["wallet"], wallet_info["n_daos"],
                         wallet_info["inside"], round(wallet_info["containment"], 3)])
    write_csv(OUTPUT_PATTERN,
              ["wallet", "n_daos", "daos_in_reference_list", "containment"], csv_rows)
    print(f"List saved to: {OUTPUT_PATTERN.resolve()}")


# ----------------------------------------------------------------------
# STEP 4: threshold comparison table
# ----------------------------------------------------------------------
def threshold_label(t):
    if t == 0:
        return "no limit"
    return str(t)


def step4_thresholds(voter_to_daos):
    """
    For each threshold T in THRESHOLDS_TO_COMPARE (a wallet is excluded if it
    has more than T DAOs) it computes:
      - how many wallets are excluded and how many of them belong to the
        group (pattern),
      - how many "other" wallets are excluded (side effect),
      - how many wallets of the group remain inside the graph,
      - the total weight of the graph and what percentage comes from the group.
    Everything is computed from two small tables "n DAOs -> number of wallets"
    (one with all wallets and another only with those of the group), without
    going through the 1.2 M voters again for each threshold.
    """
    _, evaluated = evaluate_containment(voter_to_daos)

    # Wallets of the group (the ones that follow the pattern)
    group = []
    for wallet_info in evaluated:
        if wallet_info["containment"] >= CONTAINMENT_THRESHOLD:
            group.append(wallet_info["wallet"])

    # Two small tables: how many wallets have exactly n DAOs
    all_by_n = Counter()
    for daos in voter_to_daos.values():
        all_by_n[len(daos)] += 1
    group_by_n = Counter()
    for wallet in group:
        group_by_n[len(voter_to_daos[wallet])] += 1
    group_total = len(group)

    print("\n--- Threshold comparison ---")
    print(f"Total wallets: {len(voter_to_daos):,} | in the group (pattern): {group_total}")
    print("A wallet is EXCLUDED if it has MORE DAOs than the threshold.\n")
    print(f"  {'threshold':>10} {'excluded':>10} {'from group':>10} {'others':>7} "
          f"{'group inside':>13} {'graph weight':>15} {'% group weight':>15}")

    rows = []
    for t in THRESHOLDS_TO_COMPARE:
        # All wallets: how many are excluded and how much weight stays
        excluded = 0
        weight = 0
        for n, count in all_by_n.items():
            if ev.is_excluded(n, t):
                excluded += count
            else:
                weight += count * pairs_of(n)

        # Only the wallets of the group
        excluded_group = 0
        group_weight = 0
        for n, count in group_by_n.items():
            if ev.is_excluded(n, t):
                excluded_group += count
            else:
                group_weight += count * pairs_of(n)

        others = excluded - excluded_group
        group_inside = group_total - excluded_group
        if weight > 0:
            pct = group_weight / weight * 100
        else:
            pct = 0
        rows.append([threshold_label(t), excluded, excluded_group, others,
                     group_inside, weight, group_weight, round(pct, 1)])
        print(f"  {threshold_label(t):>10} {excluded:>10,} {excluded_group:>10,} {others:>7,} "
              f"{group_inside:>13,} {weight:>15,} {pct:>14.1f}%")

    header = ["threshold", "excluded_wallets", "excluded_from_group",
              "excluded_others", "group_inside_graph",
              "graph_total_weight", "group_weight", "pct_group_weight"]
    write_csv(OUTPUT_THRESHOLDS, header, rows)
    print(f"\nTable saved to: {OUTPUT_THRESHOLDS.resolve()}")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="S2-03: analysis of the voters affected by the activity filter."
    )
    parser.add_argument(
        "--thresholds", action="store_true",
        help="Also runs STEP 4 (threshold table; uses only the cache).",
    )
    parser.add_argument(
        "--pattern", action="store_true",
        help="Also runs STEP 3d (uses only the cache; takes seconds).",
    )
    parser.add_argument(
        "--cases", action="store_true",
        help="Also runs STEP 3 (re-reads votes.csv; takes ~1 minute).",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    if not ev.VOTES_CSV.exists():
        sys.exit(f"ERROR: cannot find {ev.VOTES_CSV}. Run the script from the "
                 f"repository root, where data/raw/votes.csv is.")

    print("Loading voters (cache or votes.csv)...", flush=True)
    voter_to_daos = ev.load_voters(ev.VOTES_CSV)

    ns = daos_per_voter(voter_to_daos)   # number of DAOs of each wallet (computed once)
    step1_distribution(ns)
    step2_histogram(ns)

    if args.cases:
        step3_cases(voter_to_daos)

    if args.pattern:
        step3d_pattern(voter_to_daos)

    if args.thresholds:
        step4_thresholds(voter_to_daos)


if __name__ == "__main__":
    main()
