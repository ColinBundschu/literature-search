# Solid-State Synthesis Recipe Database

## Files
| File | Purpose |
|------|---------|
| `synthesis_recipes.csv` | Found recipes (Material Class, Formula, Sintering Temp (C), Heating Time, Precursors, DOI, Notes) |
| `synthesis_recipes_not_found.csv` | Compositions with no recipe found (Material Class, Formula, Notes) |
| `synthesis_recipes_queue.csv` | Remaining compositions to search (Material Class, Formula) |

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
3. If found → add row(s) to `synthesis_recipes.csv`; if not found → add row to `synthesis_recipes_not_found.csv`
4. Remove the composition from the queue
5. Repeat

For double perovskites, search both B'-B'' orderings (e.g. Sr2AlTaO6 and Sr2TaAlO6) — record under one consistent format.

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

Category 1 (Silicate-type) — A: (Ca, Mg, Sr, Ba) / B: (Al, Ga, Sc) / C: (Si, Ge)
Category 2 (Rare Earth) — A: (Y, La, Lu) / B/C: pick two from (Al, Ga, Sc)
