"""Genera data/split.csv una única vez.

Uso:  python scripts/make_split.py           # falla si split.csv ya existe
      python scripts/make_split.py --force   # solo con acuerdo de los tres
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import EXCLUDED, SPLIT_CSV  # noqa: E402
from src.split import make_split, record_table  # noqa: E402

if __name__ == "__main__":
    if SPLIT_CSV.exists() and "--force" not in sys.argv:
        sys.exit(f"{SPLIT_CSV} ya existe. La partición no se regenera (usar --force).")

    table = record_table()
    split = make_split(table)
    split.to_csv(SPLIT_CSV, index=False)

    print(f"Guardado {SPLIT_CSV}\n")
    print(split.groupby(["set", "category"]).size().unstack(fill_value=0), "\n")
    print("Excluidos:", "; ".join(f"{k}: {v}" for k, v in EXCLUDED.items()))
    bad = split[(split.record.str[0] != "x") & (split.category != split.rule_category)]
    if len(bad):
        print("\nAviso: categoría por nombre distinta a la regla por minutos:")
        print(bad[["record", "category", "rule_category", "apnea_minutes"]].to_string(index=False))
