#!/usr/bin/env python3
"""
Plot literature search results as colored 2D grids organized by material class and cation site.
"""

import csv
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

# --- Category definitions ---
# 0: In queue (not yet searched)
# 1: Solid-state synthesis found
# 2: Not found but probably feasible
# 3: Non-SS or high-pressure synthesis required (merged)
# 5: Forms the phase but disordered (solid solution on swap sites)
# 7: Prefers an entirely different phase
# 6: Not physically possible

CAT_COLORS = {
    0: "#ffffff",   # white (in queue, not yet searched)
    1: "#2ca02c",   # green (SS synthesis found)
    2: "#c5e17a",   # yellow-green (not found, feasible)
    3: "#fdd835",   # yellow (non-SS / high-pressure only)
    5: "#4db6ac",   # teal (disordered solid solution)
    7: "#ff9f43",   # orange (prefers different phase) — not used in current plot
    6: "#e53935",   # red (not physically possible)
}

# --- Parse CSVs ---
def parse_found(path):
    """Return set of (class, formula) that have SS synthesis found."""
    found = set()
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            found.add((row["Material Class"].strip(), row["Material Formula"].strip()))
    return found

def parse_not_found(path):
    """Return dict of (class, formula) -> category based on notes."""
    results = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["Material Class"].strip(), row["Material Formula"].strip())
            formula = row["Material Formula"].strip()
            notes = row["Notes"].strip()
            nl = notes.lower()

            # =================================================================
            # Category 6: Not physically possible
            # Compound doesn't exist as any single phase, or ions fundamentally
            # incompatible (too large/small) with no known phase at any pressure
            # =================================================================
            if any(phrase in nl for phrase in [
                "does not exist",
                "far too large for dodecahedral",   # Ba garnets
                "far too large for b-site in ilmenite",
                "far too large for ilmenite b-site",
                "likely unstable against decomposition",
                "does not exist as stable single phase",  # Ba2Nb2O7, Ba2Ta2O7
            ]):
                results[key] = 6
                continue

            if formula in ("MgCeO3", "ZnCeO3"):
                results[key] = 6
                continue

            # Structural chemistry makes formation impossible
            if any(phrase in nl for phrase in [
                "ce4+ on the b-site",
                "chemically difficult to stabilize",
                "ca2+ is far too large for octahedral",
                "ca2+ is too large for octahedral",
                "zn2+ strongly prefers tetrahedral",
                "tolerance factor may be unfavorable",
                "ca2+ may be too large for b-site",
                "mg2+ too small for dodecahedral",
                "la3+ too large for dodecahedral",
                "si framework too small",
                "si4+ tetrahedral framework too small",
                "si4+ gives too tight a framework",
                "severe tolerance factor mismatch",
                "too large for octahedral site in mg oxide spinel",  # MgSc2O4
                "too large for octahedral site in zn oxide spinel",  # ZnSc2O4
                "still too small on octahedral site for sr",  # Sr3Ga2Ge3O12
                "al3+ far too small on octahedral site for sr",  # Sr3Al2Ge3O12
                "too small on octahedral site to expand lattice enough for la",  # La3Al2Ga3O12
                "does not form as ordered phase",  # Ga2Al3 garnets
                "too small on octahedral site to stabilize la",  # La3Ga2Al3O12
                "adopts orthorhombic silico-carnotite",  # Ca3Y2Si3O12
                "boundary for ca-silicate garnets",  # Ca3In2Si3O12
                "thermodynamically unstable above",  # La3Sc2Al3O12
                "dynamically unstable",  # MgSnO3 ilmenite
                "too small for stable octahedral coordination",  # Bi Ge compounds
                "too large for b-site when paired with",  # Bi Ca non-Ti compounds
                "does not form perovskite; ce4+",  # Bi Ce compounds
                "no bi(ca0.5x)o3 reported",  # Bi Ca compounds
                "too large for b-site with ce4+",  # Bi2CaCeO6
                "no bi(b0.5ge0.5)o3 reported",  # Bi Ge compounds
            ]):
                results[key] = 6
                continue

            # "does not form" with size reason → impossible
            if "does not form" in nl and ("far too large" in nl or "far too small" in nl):
                results[key] = 6
                continue

            # "does not form double perovskite" with B-site size problem → impossible
            if "does not form double perovskite" in nl:
                results[key] = 6
                continue

            # =================================================================
            # Category 5: Disordered solid solution
            # Makes the phase but the swap sites are not ordered
            # =================================================================

            # DP Cat 4: isovalent 4+/4+ → disordered perovskite (no ordering driving force)
            # Also catches cases where B-site size similarity prevents ordering
            if "isovalent +4/+4" in nl or "disordered solid solution" in nl or "likely forms disordered perovskite" in nl:
                results[key] = 5
                continue

            # Pyrochlore → defect fluorite (disordered version of pyrochlore)
            if "forms defect fluorite" in nl or "disordered defect-fluorite" in nl:
                results[key] = 5
                continue

            # Specific known disordered cases
            if "does not adopt ordered double perovskite" in nl and "disordered" in nl:
                results[key] = 5
                continue

            # =================================================================
            # Bi-based double perovskites → disordered simple perovskite
            # High-pressure or metastable ones → category 3; rest → category 5
            # =================================================================
            if key[0] == "Double Perovskite" and formula.startswith("Bi2"):
                if "high-pressure" in nl or "metastable" in nl or "high pressure" in nl:
                    results[key] = 3
                    continue
                if "does not adopt" in nl or "forms simple perovskite" in nl:
                    results[key] = 5
                    continue

            # =================================================================
            # Category 3: Non-SS or high-pressure synthesis required (merged)
            # =================================================================
            if any(phrase in nl for phrase in [
                "high-pressure polymorph",
                "requires high-pressure synthesis",
                "requires high pressure",
                "multi-anvil press",
                "stoichiometric pyrochlore requires high-pressure",
            ]):
                results[key] = 3
                continue

            # Ilmenites that form target structure at HP
            if any(phrase in nl for phrase in [
                "does not adopt ilmenite at ambient pressure; ilmenite only at",
                "does not adopt ilmenite at ambient pressure; requires high-pressure",
                "does not adopt ilmenite at ambient pressure; requires",
                "does not adopt ilmenite structure at ambient pressure; requires high-pressure",
                "does not adopt ilmenite structure at ambient pressure; mgsi",
            ]):
                results[key] = 3
                continue

            if formula == "MgSiO3" and "ilmenite" in key[0].lower():
                results[key] = 3
                continue

            if formula == "ZnSnO3" and key[0] == "Ilmenite" and "7 gpa" in nl:
                results[key] = 3
                continue

            # Non-SS ambient-pressure methods
            if any(phrase in nl for phrase in [
                "metastable",
                "coprecipitation",
                "cannot be made by conventional solid-state",
                "cannot be made by solid-state",
                "no solid-state route",
                "czochralski",
                "melt growth",
                "sol-gel auto-combustion only",
                "hydrothermal",
                "wet chemistry",
                "non-stoichiometric",
            ]):
                results[key] = 3
                continue

            # =================================================================
            # Category 7: Prefers entirely different phase
            # =================================================================
            if any(phrase in nl for phrase in [
                "does not adopt ilmenite structure; forms",
                "does not adopt ilmenite structure; ambient form",
                "does not adopt pyrochlore structure",
                "does not adopt ordered double perovskite",
                "does not adopt double perovskite",
                "forms disordered",
                "adopts a triclinic",
                "adopts monoclinic",
                "adopts other",
                "layered perovskite",
                "dynamically unstable",
                "thermodynamically unstable above",
            ]):
                results[key] = 7
                continue

            # Remaining ilmenites that prefer other phases
            if "does not adopt ilmenite" in nl:
                results[key] = 7
                continue

            # Remaining "does not form" → different phase
            if "does not form" in nl:
                results[key] = 7
                continue

            # =================================================================
            # Category 2: Not found but likely feasible (default)
            # =================================================================
            results[key] = 2

    return results

def parse_queue(path):
    """Return set of (class, formula) still in queue."""
    queue = set()
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            queue.add((row["Material Class"].strip(), row["Material Formula"].strip()))
    return queue


def get_status(mat_class, formula, found_set, not_found_dict, queue_set):
    """Get category for a compound."""
    key = (mat_class, formula)
    if key in found_set:
        return 1
    elif key in not_found_dict:
        return not_found_dict[key]
    elif key in queue_set:
        return 0
    else:
        return -1  # unknown / not in any list


def draw_grid(ax, row_labels, col_labels, data, title, row_axis_label="", col_axis_label=""):
    """Draw a colored grid on the given axes."""
    nrows = len(row_labels)
    ncols = len(col_labels)

    for i in range(nrows):
        for j in range(ncols):
            val = data[i][j]
            if val == -2:
                continue  # skip N/A cells entirely (upper/lower triangle)
            elif val == -3:
                color = "#d9d9d9"  # solid light gray (B=C diagonal)
                hatch = None
            elif val == -1:
                color = "white"
                hatch = "///"
            else:
                color = CAT_COLORS.get(val, "white")
                hatch = None

            rect = mpatches.FancyBboxPatch(
                (j, nrows - 1 - i), 1, 1,
                boxstyle="square,pad=0",
                facecolor=color,
                edgecolor="black",
                linewidth=1.0,
            )
            if hatch:
                rect.set_hatch(hatch)
            ax.add_patch(rect)

    ax.set_xlim(0, ncols)
    ax.set_ylim(0, nrows)
    ax.set_xticks([x + 0.5 for x in range(ncols)])
    ax.set_xticklabels(col_labels, fontsize=18, fontweight='bold')
    ax.set_yticks([y + 0.5 for y in range(nrows)])
    ax.set_yticklabels(row_labels[::-1], fontsize=18, fontweight='bold')
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=19, fontweight='bold', pad=8)

    if col_axis_label:
        ax.set_xlabel(col_axis_label, fontsize=16, style='italic')
    if row_axis_label:
        ax.set_ylabel(row_axis_label, fontsize=16, style='italic')

    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def main():
    base = "/Users/cbu/literature-search/"
    found_set = parse_found(base + "synthesis_recipes.csv")
    not_found_dict = parse_not_found(base + "synthesis_recipes_not_found.csv")
    queue_set = parse_queue(base + "synthesis_recipes_queue.csv")

    # =========================================================================
    # Define all material classes and their grids
    # =========================================================================
    spinel_A = ["Mg", "Zn"]
    spinel_B = ["Al", "Ga", "In"]

    dp1_A = ["Ca", "Sr", "Ba", "Pb"]
    dp1_Bp = ["Al", "Ga", "Sc", "In", "Y", "Lu"]
    dp1_Bpp = ["Nb", "Ta", "Sb", "Bi"]

    dp2_A = ["Ca", "Sr", "Ba", "Pb"]
    dp2_Bp = ["Mg", "Ca", "Zn"]
    dp2_Bpp = ["W", "Mo", "Te"]

    dp3_A = ["La", "Bi", "Y", "Lu"]
    dp3_Bp = ["Mg", "Ca", "Zn"]
    dp3_Bpp = ["Ti", "Sn", "Zr", "Hf", "Ge"]

    dp4_A = ["Ca", "Sr", "Ba", "Pb"]
    dp4_B = ["Ti", "Zr", "Hf", "Sn"]

    ilm_A = ["Mg", "Zn"]
    ilm_B = ["Ti", "Si", "Ge", "Sn"]

    pyro1_A = ["La", "Y", "Lu", "Bi"]
    pyro1_B = ["Ti", "Zr", "Hf", "Sn"]

    pyro2_A = ["Pb"]
    pyro2_B = ["Nb", "Ta", "Sb"]

    gar1_A = ["Ca", "Sr"]
    gar1_B = ["Al", "Ga", "Sc", "In", "Y"]
    gar1_C = ["Si", "Ge"]

    gar2_A = ["Y", "La", "Lu"]
    gar2_B = ["Al", "Sc", "In"]          # octahedral — removed Ga (can't be forced to oct)
    gar2_C = ["Ga", "Al"]               # tetrahedral — swapped order; Al-Al will be invisible

    # =========================================================================
    # Formula builders
    # =========================================================================
    def make_formula_spinel(a, b):
        return f"{a}{b}2O4"

    def make_formula_dp(a, bp, bpp):
        return f"{a}2{bp}{bpp}O6"

    def make_formula_ilmenite(a, b):
        return f"{a}{b}O3"

    def make_formula_pyrochlore(a, b):
        return f"{a}2{b}2O7"

    def make_formula_garnet(a, b, c):
        return f"{a}3{b}2{c}3O12"

    def status(mc, formula):
        return get_status(mc, formula, found_set, not_found_dict, queue_set)

    # =========================================================================
    # Tight layout with GridSpec — reduced whitespace
    # =========================================================================
    from matplotlib.gridspec import GridSpec

    fig = plt.figure(figsize=(26, 28))
    fig.suptitle("Literature Search Results: Solid-State Synthesis of Oxide Ceramics",
                 fontsize=32, fontweight='bold', y=0.99)

    # Height ratios tuned to grid row counts
    gs = GridSpec(7, 16, figure=fig,
                  height_ratios=[0.8, 4, 6, 3, 3, 5, 5],
                  hspace=0.6, wspace=0.35,
                  top=0.97, bottom=0.02, left=0.05, right=0.98)

    # --- Row 0: Legend at top ---
    legend_patches = [
        mpatches.Patch(facecolor=CAT_COLORS[1], edgecolor='black', linewidth=1.2,
                       label='SS synthesis found'),
        mpatches.Patch(facecolor=CAT_COLORS[2], edgecolor='black', linewidth=1.2,
                       label='Not found (likely feasible)'),
        mpatches.Patch(facecolor=CAT_COLORS[3], edgecolor='black', linewidth=1.2,
                       label='Non-SS / high-pressure only'),
        mpatches.Patch(facecolor=CAT_COLORS[5], edgecolor='black', linewidth=1.2,
                       label='Disordered solid solution'),
        mpatches.Patch(facecolor=CAT_COLORS[6], edgecolor='black', linewidth=1.2,
                       label='Not physically possible'),
        mpatches.Patch(facecolor=CAT_COLORS[0], edgecolor='black', linewidth=1.2,
                       label='In queue'),
    ]
    fig.legend(handles=legend_patches, loc='upper center', ncol=4,
              fontsize=20, frameon=True, fancybox=True, shadow=True,
              bbox_to_anchor=(0.5, 0.975))

    # --- Row 1: Spinel + Ilmenite + Pyrochlores ---
    ax = fig.add_subplot(gs[1, 0:3])
    data = [[status("Spinel", make_formula_spinel(a, b)) for b in spinel_B] for a in spinel_A]
    draw_grid(ax, spinel_A, spinel_B, data, "Spinel  AB$_2$O$_4$", "A site", "B site")

    ax = fig.add_subplot(gs[1, 4:8])
    data = [[status("Ilmenite", make_formula_ilmenite(a, b)) for b in ilm_B] for a in ilm_A]
    draw_grid(ax, ilm_A, ilm_B, data, "Ilmenite  ABO$_3$", "A site", "B site")

    ax = fig.add_subplot(gs[1, 9:13])
    data = [[status("Pyrochlore", make_formula_pyrochlore(a, b)) for b in pyro1_B] for a in pyro1_A]
    draw_grid(ax, pyro1_A, pyro1_B, data,
              "Pyrochlore  A$_2$B$_2$O$_7$\n(A$^{3+}$, B$^{4+}$)", "A site", "B site")

    ax = fig.add_subplot(gs[1, 14:16])
    data = [[status("Pyrochlore", make_formula_pyrochlore(a, b)) for b in pyro2_B] for a in pyro2_A]
    draw_grid(ax, pyro2_A, pyro2_B, data,
              "Pyrochlore  A$_2$B$_2$O$_7$\n(A$^{2+}$, B$^{5+}$)", "A site", "B site")

    # --- Row 2: Double Perovskite Cat 1 (3+/5+): 6x4, 4 panels ---
    for idx, a in enumerate(dp1_A):
        ax = fig.add_subplot(gs[2, idx*4:(idx*4)+4])
        data = [[status("Double Perovskite", make_formula_dp(a, bp, bpp))
                 for bpp in dp1_Bpp] for bp in dp1_Bp]
        draw_grid(ax, dp1_Bp, dp1_Bpp, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{3+}}$ / B''$^{{5+}}$)",
                  "B' site", "B'' site")

    # --- Row 4: Double Perovskite Cat 2 (2+/6+): 3x3, 4 panels ---
    for idx, a in enumerate(dp2_A):
        ax = fig.add_subplot(gs[3, idx*4:(idx*4)+3])
        data = [[status("Double Perovskite", make_formula_dp(a, bp, bpp))
                 for bpp in dp2_Bpp] for bp in dp2_Bp]
        draw_grid(ax, dp2_Bp, dp2_Bpp, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{2+}}$ / B''$^{{6+}}$)",
                  "B' site", "B'' site")

    # --- Row 5: Double Perovskite Cat 3 (2+/4+): 3x6 ---
    for idx, a in enumerate(dp3_A):
        ax = fig.add_subplot(gs[4, idx*4:(idx*4)+4])
        data = [[status("Double Perovskite", make_formula_dp(a, bp, bpp))
                 for bpp in dp3_Bpp] for bp in dp3_Bp]
        draw_grid(ax, dp3_Bp, dp3_Bpp, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{2+}}$ / B''$^{{4+}}$)",
                  "B' site", "B'' site")

    # --- Row 6: Double Perovskite Cat 4 (4+/4+): lower triangle, trimmed ---
    # Rows = all except first (Ti), Cols = all except last (Sn)
    # Lower triangle: b1_idx > b2_idx in original list
    dp4_rows = dp4_B[1:]    # Zr, Hf, Ce, Sn
    dp4_cols = dp4_B[:-1]   # Ti, Zr, Hf, Ce
    for idx, a in enumerate(dp4_A):
        ax = fig.add_subplot(gs[5, idx*4:(idx*4)+4])
        data = []
        for b1_idx, b1 in enumerate(dp4_rows):
            row = []
            for b2_idx, b2 in enumerate(dp4_cols):
                # b1 is at original index b1_idx+1, b2 at original index b2_idx
                if b2_idx >= (b1_idx + 1):
                    row.append(-2)  # upper triangle — skip
                elif b1 == b2:
                    row.append(-2)
                else:
                    # Try both orderings since B'/B'' are interchangeable
                    s = status("Double Perovskite", make_formula_dp(a, b1, b2))
                    if s == -1:
                        s = status("Double Perovskite", make_formula_dp(a, b2, b1))
                    row.append(s)
            data.append(row)
        draw_grid(ax, dp4_rows, dp4_cols, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{4+}}$ / B''$^{{4+}}$)",
                  "B' site", "B'' site")

    # --- Row 7: All Garnets on one row ---
    col = 0
    # Cat 1: rectangular grids (no B=C possible since B is 3+ and C is 4+)
    for idx, a in enumerate(gar1_A):
        ncols_g = len(gar1_C)
        ax = fig.add_subplot(gs[6, col:col+ncols_g])
        data = [[status("Garnet", make_formula_garnet(a, b, c))
                 for c in gar1_C] for b in gar1_B]
        draw_grid(ax, gar1_B, gar1_C, data,
                  f"Garnet  {a}$_3$B$_2$C$_3$O$_{{12}}$\n(A$^{{2+}}$, B$^{{3+}}$, C$^{{4+}}$)",
                  "B site", "C site")
        col += ncols_g + 1

    # Cat 2: rectangular grid, B (oct) x C (tet), gray out B=C
    # Not symmetric: octahedral and tetrahedral are different sites
    # C-site restricted to Al, Ga (Sc/In too large for tetrahedral)
    for idx, a in enumerate(gar2_A):
        ncols_g = len(gar2_C)
        ax = fig.add_subplot(gs[6, col:col+ncols_g])
        data = []
        for b in gar2_B:
            row = []
            for c in gar2_C:
                if b == c:
                    row.append(-2)  # invisible B=C cell (like DP Cat 4)
                else:
                    row.append(status("Garnet", make_formula_garnet(a, b, c)))
            data.append(row)
        draw_grid(ax, gar2_B, gar2_C, data,
                  f"Garnet  {a}$_3$B$_2$C$_3$O$_{{12}}$\n(A$^{{3+}}$, B$^{{3+}}$, C$^{{3+}}$)",
                  "B (oct.)", "C (tet.)")
        col += ncols_g + 1

    plt.savefig(base + "literature_search_results.png", dpi=200, bbox_inches='tight')
    plt.savefig(base + "literature_search_results.pdf", bbox_inches='tight')
    print("Saved literature_search_results.png and .pdf")


if __name__ == "__main__":
    main()
