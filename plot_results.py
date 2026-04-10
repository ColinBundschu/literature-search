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
    # Fixed cell size layout — all squares same physical size
    # =========================================================================
    CELL = 0.65       # inches per grid cell
    HGAP = 1.8        # default horizontal gap between panels (inches)
    VGAP = 1.3        # vertical gap between rows (inches)
    LMARGIN = 1.2     # left margin (inches)
    TMARGIN = 2.8     # top margin for title + legend (inches)
    BMARGIN = 0.3     # bottom margin (inches)
    TITLE_PAD = 0.9   # space above each grid for title (inches)
    # Per-row horizontal gaps (some rows need more space)
    HGAP_DP2 = 2.8    # DP Cat 2 (2+/6+)
    HGAP_DP4 = 2.8    # DP Cat 4 (4+/4+)
    HGAP_GAR = 2.2    # Garnets

    def make_ax(fig, x, y, nrows, ncols, fig_w, fig_h):
        """Create axes at (x, y) inches from bottom-left, sized for nrows x ncols cells."""
        return fig.add_axes([x/fig_w, y/fig_h, ncols*CELL/fig_w, nrows*CELL/fig_h])

    # --- Pre-compute layout positions ---
    # Each row is a list of (nrows, ncols) for each panel
    # Row heights are determined by the tallest panel in that row

    # Row 0: Spinel(2,3) Ilmenite(2,4) Pyro1(4,4) Pyro2(1,3)
    r0_panels = [(2,3), (2,4), (4,4), (1,3)]
    r0_h = max(nr for nr, nc in r0_panels) * CELL + TITLE_PAD

    # Row 1: DP Cat1 x4, each (6,4)
    r1_panels = [(6,4)] * 4
    r1_h = 6 * CELL + TITLE_PAD

    # Row 2: DP Cat2 x4, each (3,3)
    r2_panels = [(3,3)] * 4
    r2_h = 3 * CELL + TITLE_PAD

    # Row 3: DP Cat3 x4, each (3,5)
    r3_panels = [(3,5)] * 4
    r3_h = 3 * CELL + TITLE_PAD

    # Row 4: DP Cat4 x4, each (3,3) lower triangle
    dp4_rows = dp4_B[1:]
    dp4_cols = dp4_B[:-1]
    r4_panels = [(len(dp4_rows), len(dp4_cols))] * 4
    r4_h = len(dp4_rows) * CELL + TITLE_PAD

    # Row 5: Garnets — Cat1(5,2) x2 + Cat2(3,2) x3
    r5_panels = [(5,2)] * 2 + [(3,2)] * 3
    r5_h = 5 * CELL + TITLE_PAD

    total_h = TMARGIN + r0_h + VGAP + r1_h + VGAP + r2_h + VGAP + r3_h + VGAP + r4_h + VGAP + r5_h + BMARGIN

    # Width: widest row is Row 3 (DP Cat3): 4 panels of 5 cols
    # Compute width needed for each row and take the max
    widths = [
        3*CELL + HGAP + 4*CELL + HGAP + 4*CELL + HGAP + 3*CELL,  # row 0
        4 * 4 * CELL + 3 * HGAP,       # row 1 (DP Cat 1)
        4 * 3 * CELL + 3 * HGAP_DP2,   # row 2 (DP Cat 2)
        4 * 5 * CELL + 3 * HGAP,       # row 3 (DP Cat 3)
        4 * 3 * CELL + 3 * HGAP_DP4,   # row 4 (DP Cat 4)
        2*2*CELL + 3*2*CELL + 4*HGAP_GAR,  # row 5 (garnets)
    ]
    widest = max(widths) + 2 * LMARGIN
    fig_w = max(widest, 22)
    fig_h = total_h

    fig = plt.figure(figsize=(fig_w, fig_h))
    fig.text(0.5, 1 - 0.5/fig_h, "Literature Search Results: Solid-State Synthesis of Oxide Ceramics",
             fontsize=32, fontweight='bold', ha='center', va='top')

    # Legend at top
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
    fig.legend(handles=legend_patches, loc='upper center', ncol=3,
              fontsize=18, frameon=True, fancybox=True, shadow=True,
              bbox_to_anchor=(0.5, 1 - 1.0/fig_h))

    def row_y(row_tops, row_idx):
        """Get the bottom y position for panels in this row (panels are top-aligned)."""
        return row_tops[row_idx]

    # Compute row top positions (y of the top of each row's cell area, from bottom)
    row_tops = []
    y = BMARGIN + r5_h  # bottom of row 5 + its height = top of row 5 cells
    row_tops.append(BMARGIN)  # row 5 (garnets) bottom
    y += VGAP
    row_tops.append(y)  # row 4 bottom
    y += r4_h + VGAP
    row_tops.append(y)  # row 3 bottom
    y += r3_h + VGAP
    row_tops.append(y)  # row 2 bottom
    y += r2_h + VGAP
    row_tops.append(y)  # row 1 bottom
    y += r1_h + VGAP
    row_tops.append(y)  # row 0 bottom
    row_tops.reverse()  # now index 0 = topmost row

    def place_panels(row_idx, panels_data, row_max_h):
        """Place panels left to right, top-aligned within the row."""
        x = LMARGIN
        axes = []
        for nr, nc in [(len(d[0]), len(d[0][0]) if d[0] else 0) for d in panels_data]:
            # Align to top of row
            y_bottom = row_tops[row_idx] + (row_max_h - TITLE_PAD - nr * CELL)
            ax = make_ax(fig, x, y_bottom, nr, nc, fig_w, fig_h)
            axes.append(ax)
            x += nc * CELL + HGAP
        return axes

    # --- Row 0: Spinel + Ilmenite + Pyrochlore ---
    x = LMARGIN
    grids_r0 = [
        (spinel_A, spinel_B, [[status("Spinel", make_formula_spinel(a, b)) for b in spinel_B] for a in spinel_A],
         "Spinel  AB$_2$O$_4$", "A site", "B site"),
        (ilm_A, ilm_B, [[status("Ilmenite", make_formula_ilmenite(a, b)) for b in ilm_B] for a in ilm_A],
         "Ilmenite  ABO$_3$", "A site", "B site"),
        (pyro1_A, pyro1_B, [[status("Pyrochlore", make_formula_pyrochlore(a, b)) for b in pyro1_B] for a in pyro1_A],
         "Pyrochlore  A$_2$B$_2$O$_7$\n(A$^{3+}$, B$^{4+}$)", "A site", "B site"),
        (pyro2_A, pyro2_B, [[status("Pyrochlore", make_formula_pyrochlore(a, b)) for b in pyro2_B] for a in pyro2_A],
         "Pyrochlore  A$_2$B$_2$O$_7$\n(A$^{2+}$, B$^{5+}$)", "A site", "B site"),
    ]
    for rl, cl, data, title, ylab, xlab in grids_r0:
        nr, nc = len(rl), len(cl)
        y_bottom = row_tops[0] + (r0_h - TITLE_PAD - nr * CELL)
        ax = make_ax(fig, x, y_bottom, nr, nc, fig_w, fig_h)
        draw_grid(ax, rl, cl, data, title, ylab, xlab)
        x += nc * CELL + HGAP

    # --- Row 1: DP Cat 1 (3+/5+) ---
    x = LMARGIN
    for a in dp1_A:
        data = [[status("Double Perovskite", make_formula_dp(a, bp, bpp))
                 for bpp in dp1_Bpp] for bp in dp1_Bp]
        nr, nc = len(dp1_Bp), len(dp1_Bpp)
        ax = make_ax(fig, x, row_tops[1], nr, nc, fig_w, fig_h)
        draw_grid(ax, dp1_Bp, dp1_Bpp, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{3+}}$ / B''$^{{5+}}$)",
                  "B' site", "B'' site")
        x += nc * CELL + HGAP

    # --- Row 2: DP Cat 2 (2+/6+) ---
    x = LMARGIN
    for a in dp2_A:
        data = [[status("Double Perovskite", make_formula_dp(a, bp, bpp))
                 for bpp in dp2_Bpp] for bp in dp2_Bp]
        nr, nc = len(dp2_Bp), len(dp2_Bpp)
        ax = make_ax(fig, x, row_tops[2], nr, nc, fig_w, fig_h)
        draw_grid(ax, dp2_Bp, dp2_Bpp, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{2+}}$ / B''$^{{6+}}$)",
                  "B' site", "B'' site")
        x += nc * CELL + HGAP_DP2

    # --- Row 3: DP Cat 3 (2+/4+) ---
    x = LMARGIN
    for a in dp3_A:
        data = [[status("Double Perovskite", make_formula_dp(a, bp, bpp))
                 for bpp in dp3_Bpp] for bp in dp3_Bp]
        nr, nc = len(dp3_Bp), len(dp3_Bpp)
        ax = make_ax(fig, x, row_tops[3], nr, nc, fig_w, fig_h)
        draw_grid(ax, dp3_Bp, dp3_Bpp, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{2+}}$ / B''$^{{4+}}$)",
                  "B' site", "B'' site")
        x += nc * CELL + HGAP

    # --- Row 4: DP Cat 4 (4+/4+) lower triangle ---
    x = LMARGIN
    for a in dp4_A:
        data = []
        for b1_idx, b1 in enumerate(dp4_rows):
            row = []
            for b2_idx, b2 in enumerate(dp4_cols):
                if b2_idx >= (b1_idx + 1):
                    row.append(-2)
                elif b1 == b2:
                    row.append(-2)
                else:
                    s = status("Double Perovskite", make_formula_dp(a, b1, b2))
                    if s == -1:
                        s = status("Double Perovskite", make_formula_dp(a, b2, b1))
                    row.append(s)
            data.append(row)
        nr, nc = len(dp4_rows), len(dp4_cols)
        ax = make_ax(fig, x, row_tops[4], nr, nc, fig_w, fig_h)
        draw_grid(ax, dp4_rows, dp4_cols, data,
                  f"Dbl. Perovskite  {a}$_2$B'B''O$_6$\n(B'$^{{4+}}$ / B''$^{{4+}}$)",
                  "B' site", "B'' site")
        x += nc * CELL + HGAP_DP4

    # --- Row 5: All Garnets ---
    x = LMARGIN
    # Cat 1
    for a in gar1_A:
        data = [[status("Garnet", make_formula_garnet(a, b, c))
                 for c in gar1_C] for b in gar1_B]
        nr, nc = len(gar1_B), len(gar1_C)
        ax = make_ax(fig, x, row_tops[5], nr, nc, fig_w, fig_h)
        draw_grid(ax, gar1_B, gar1_C, data,
                  f"Garnet  {a}$_3$B$_2$C$_3$O$_{{12}}$\n(A$^{{2+}}$, B$^{{3+}}$, C$^{{4+}}$)",
                  "B site", "C site")
        x += nc * CELL + HGAP_GAR

    # Cat 2
    for a in gar2_A:
        data = []
        for b in gar2_B:
            row = []
            for c in gar2_C:
                if b == c:
                    row.append(-2)
                else:
                    row.append(status("Garnet", make_formula_garnet(a, b, c)))
            data.append(row)
        nr, nc = len(gar2_B), len(gar2_C)
        ax = make_ax(fig, x, row_tops[5], nr, nc, fig_w, fig_h)
        draw_grid(ax, gar2_B, gar2_C, data,
                  f"Garnet  {a}$_3$B$_2$C$_3$O$_{{12}}$\n(A$^{{3+}}$, B$^{{3+}}$, C$^{{3+}}$)",
                  "B (oct.)", "C (tet.)")
        x += nc * CELL + HGAP_GAR

    plt.savefig(base + "literature_search_results.png", dpi=200, bbox_inches='tight')
    plt.savefig(base + "literature_search_results.pdf", bbox_inches='tight')
    print("Saved literature_search_results.png and .pdf")


if __name__ == "__main__":
    main()
