"""Genera data/split.csv una única vez.

Uso:  python scripts/make_split.py           # falla si split.csv ya existe
      python scripts/make_split.py --force   # solo con acuerdo de los tres
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import EXCLUDED, SEED, SPLIT_CSV  # noqa: E402
from src.split import candidate_splits, make_split, record_table  # noqa: E402

if __name__ == "__main__":
    if SPLIT_CSV.exists() and "--force" not in sys.argv:
        sys.exit(f"{SPLIT_CSV} ya existe. La partición no se regenera (usar --force).")

    table = record_table()
    split = make_split(table)
    if (split.groupby("subject")["set"].nunique() > 1).any():
        sys.exit("Error: hay sujetos en dev y en test.")
    split.to_csv(SPLIT_CSV, index=False)

    _, masks = candidate_splits(table)
    by_set = split.groupby("set")
    print(f"Guardado {SPLIT_CSV}")
    print(f"Particiones válidas: {len(masks)}; se eligió una con semilla {SEED}.\n")
    print(split.groupby(["set", "category"]).size().unstack(fill_value=0), "\n")
    print("Sujetos:", by_set["subject"].nunique().to_dict())
    frac = by_set["apnea_minutes"].sum() / by_set["n_minutes"].sum()
    print("Fracción de minutos de apnea:", frac.round(3).to_dict(), "\n")
    print("Excluidos:", "; ".join(f"{k}: {v}" for k, v in EXCLUDED.items()))
    bad = split[(split.record.str[0] != "x") & (split.category != split.rule_category)]
    if len(bad):
        print("\nAviso: categoría por nombre distinta a la regla por minutos:")
        print(bad[["record", "category", "rule_category", "apnea_minutes"]].to_string(index=False))
