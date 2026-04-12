# Solid-State Synthesis Recipe Database

## Files
| File | Purpose |
|------|---------|
| `synthesis_recipes.csv` | Found recipes (Material Class, Formula, Sintering Temp (C), Heating Time, Precursors, DOI, Notes) |
| `synthesis_recipes_not_found.csv` | Compositions with no recipe found (Material Class, Formula, Notes) |
| `synthesis_recipes_queue.csv` | Remaining compositions to search (Material Class, Formula) |
| `disorder_comparison.csv` | Experimental cation disorder data organized for comparison with Wang-Landau calculations (see schema below) |
| `disorder_measurement_queue.csv` | Remaining compositions to search for disorder data (Material Class, Formula) |

## CSV Schema — synthesis_recipes.csv
1. **Material Class** — Spinel / Double Perovskite / Ilmenite / Pyrochlore / Garnet
2. **Material Formula**
3. **Sintering Temp (C)** — use a range (e.g. "1400-1600") if needed
4. **Heating Time** — e.g. "2 h"; use `inaccessible` if paywalled, `missing` if absent in a fully-read paper
5. **Precursors** — comma-separated (e.g. "MgO, Al2O3")
6. **DOI** — no URL prefix
7. **Notes** — atmosphere, special method, data caveats, etc.

## Search Workflow
Work through `synthesis_recipes_queue.csv` **one composition at a time — no batching**:
1. Take the next composition from the top of the queue
2. Search for solid-state synthesis recipes
3. If found → add row(s) to `synthesis_recipes.csv` — **each paper gets its own row** (do not merge data from multiple papers into one row); if not found → add row to `synthesis_recipes_not_found.csv`
   - **If the compound does not adopt the presumed structure type** (e.g., listed as Pyrochlore but forms a triclinic or tetragonal phase instead): do NOT add to `synthesis_recipes.csv`; add a single row to `synthesis_recipes_not_found.csv` with an explanation in the Notes field — include why it cannot be treated as the target structure (e.g., different space group, different disorder mechanism), and cite any relevant DOIs within the Notes field
4. Remove the composition from the queue
5. Repeat

## Viability Assessment for Not-Found Compounds
Every entry added to `synthesis_recipes_not_found.csv` **must** be rigorously assessed for viability. Do not simply record "no papers found" — determine *why* it wasn't found. The Notes field must reflect one of the following assessments:

1. **Does the compound form the target structure type at all?**
   - Calculate the relevant stability metric (tolerance factor for perovskites, radius ratios for pyrochlores, garnet tolerance factor for garnets, etc.)
   - Compare against confirmed compounds with similar metrics
   - Check if the compound adopts a different structure instead (e.g., perovskite instead of ilmenite, defect fluorite instead of pyrochlore, simple perovskite instead of double perovskite)

2. **Has it been synthesized by any method (not just solid-state)?**
   - Search for hydrothermal, sol-gel, coprecipitation, high-pressure, melt growth, etc.
   - If a non-SS route exists, note it — the compound is real but just not SS-accessible

3. **Is it likely feasible but simply unattempted?**
   - Check if close analogues exist (same structure with neighboring elements)
   - Verify the tolerance factor / radius ratio falls within the confirmed stability window
   - Note the specific analogues that support feasibility

4. **Is it physically impossible?**
   - Cite the specific structural/chemical reason (ion too large/small, charge balance issue, redox instability, etc.)
   - Reference confirmed compounds that bracket the stability boundary
   - Include tolerance factor or radius ratio calculations where applicable

The Notes field should include enough reasoning and citations that the classification can be independently verified.

For double perovskites, search both B'-B'' orderings (e.g. Sr2AlTaO6 and Sr2TaAlO6) — record under one consistent format.

---

## Cation Disorder Measurement Search

### Goal
For every composition known to exist (by any synthesis method), find all papers that have quantitatively measured the degree of cation disorder on the swappable sites. This includes compounds in `synthesis_recipes.csv` (solid-state found) as well as those in `synthesis_recipes_not_found.csv` classified as non-SS/HP (cat 3) or disordered solid solution (cat 5).

### CSV Schema — disorder_measurements.csv
1. **Material Class** — Spinel / Double Perovskite / Ilmenite / Pyrochlore / Garnet
2. **Material Formula**
3. **Disorder Parameter** — quantitative measure of cation disorder, e.g.:
   - For double perovskites: B-site order parameter S (0 = fully disordered, 1 = fully ordered), or % antisite defects
   - For spinels: inversion parameter x (0 = normal, 1 = fully inverse)
   - For pyrochlores: fraction of antisite defects or x in (A1-xBx)2(B1-xAx)2O7
   - For garnets: site occupancy fractions from Rietveld refinement
   - Use `inaccessible` if paywalled, `missing` if absent in a fully-read paper
4. **Measurement Method** — e.g., "Rietveld refinement (XRD)", "Rietveld refinement (neutron)", "NMR", "EXAFS", "Mössbauer", "EELS", "TEM diffraction (superstructure reflections)", "DFT (calculated)"
5. **DOI** — no URL prefix
6. **Notes** — synthesis conditions that produced this disorder level, annealing history, temperature of measurement, any relevant context

### Search Workflow
Work through `disorder_measurement_queue.csv` **one composition at a time — no batching**:
1. Take the next composition from the top of the queue
2. Search for papers that quantitatively measure cation disorder (order parameter, site occupancies, antisite defect concentrations)
3. If found → add row(s) to `disorder_measurements.csv` — **each paper gets its own row**; if not found → simply remove from queue (no "not found" CSV needed for this search)
4. Remove the composition from the queue
5. Repeat

### CSV Schema — disorder_comparison.csv (WL comparison format)
1. **Material Formula**
2. **Structure Type** — Spinel / Double Perovskite / Ilmenite / Pyrochlore / Garnet
3. **Antisite Fraction** — normalized disorder metric (0 = fully ordered, 0.5 = fully random):
   - Spinels: inversion parameter x directly (x=0 normal, x=1 fully inverse → capped at 0.5 for comparison)
   - Double perovskites: x = (1-S)/2 where S is the order parameter
   - Pyrochlores: antisite fraction on cation sites
   - Garnets: fraction of "wrong" cation on each site
4. **Equilibrium T (°C)** — temperature at which the disorder was established (annealing/quench T for quenched samples, measurement T for in-situ); use `inaccessible` if not reported
5. **Measurement T (°C)** — temperature at which diffraction/NMR was performed (usually 25 for quenched samples)
6. **In Situ** — TRUE if measured at the equilibrium temperature; FALSE if quenched then measured at RT
7. **Method** — experimental technique
8. **DOI**
9. **Notes**

The key distinction for WL comparison: **Equilibrium T** is what your WL calculation predicts x(T) at. A quenched sample measured at RT reflects x(T_quench), not x(RT).

### What counts as a disorder measurement
- **Yes**: Rietveld refinement reporting site occupancies or order parameter S; NMR measuring local cation environments; superstructure reflection intensities quantifying long-range order; EXAFS/PDF analysis of local cation distribution; ion irradiation studies with quantified disorder thresholds
- **No**: DFT-calculated or computationally predicted disorder parameters (this database is experimental only); papers that merely state "ordered" or "disordered" without quantification; papers that only report the crystal structure without disorder analysis; papers that study doped compositions where the dopant itself is the disordering agent

---

## Material Classes

### Spinel AB2O4
https://next-gen.materialsproject.org/materials/mp-3536
Replace Mg with A and Al with B
A: (Mg, Zn)
B: (Al, Ga, In, Sc)

### Double Perovskite A2B'B''O6
https://next-gen.materialsproject.org/materials/mp-1205594
Replace Sr with A, Al with B', and Ta with B''
Exclude B' = B''

Category 1 — A: (Ca, Sr, Ba) / B': (Al, Ga, Sc, In, Y, Lu) / B'': (Nb, Ta, Sb)
Category 2 — A: (Ca, Sr, Ba) / B': (Mg, Ca, Zn) / B'': (W, Mo)
Category 3 — A: (La, Bi, Y, Lu) / B': (Mg, Ca, Zn) / B'': (Ti, Sn, Zr, Hf, Ce, Ge)
Category 4 — A: (Ca, Sr, Ba, Pb) / B'/B'': pick two from (Ti, Zr, Hf, Ce, Sn)

### Ilmenite ABO3
https://next-gen.materialsproject.org/materials/mp-3771
Replace Mg with A and Ti with B
A: (Mg, Zn, Ca, Sr, Ba, Pb)
B: (Ti, Si, Ge, Sn, Zr, Hf, Ce)

### Pyrochlore A2B2O7
https://next-gen.materialsproject.org/materials/mp-5373
Replace Y with A and Ti with B

Category 1 — A: (La, Y, Lu, Bi) / B: (Ti, Zr, Hf, Sn, Ge, Ce)
Category 2 — A: (Ca, Sr, Ba, Pb) / B: (Nb, Ta)

### Garnet A3B2C3O12
https://next-gen.materialsproject.org/materials/mp-6008
Replace Ca with A, Al with B, and Si with C
Exclude B = C

Category 1 (A²⁺, B³⁺, C⁴⁺) — A: (Ca, Sr) / B: (Al, Ga, Sc, In, Y) / C: (Si, Ge)
Category 2 (A³⁺, B³⁺, C³⁺) — A: (Y, La, Lu) / B (octahedral): (Al, Ga, Sc, In) / C (tetrahedral): (Al, Ga)
Note: Sc³⁺ and In³⁺ are too large for the tetrahedral C-site; they can only occupy the octahedral B-site. The B and C sites are NOT interchangeable — A₃B₂C₃O₁₂ with B on octahedral and C on tetrahedral is a different compound from the reversed assignment.

Note: Mg and Ba A-site garnets were investigated and found to be non-viable (Mg²⁺ too small, Ba²⁺ too large for dodecahedral site). They remain in the CSVs for completeness but are omitted from the plot.
