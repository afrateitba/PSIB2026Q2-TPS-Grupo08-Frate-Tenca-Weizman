from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from src.config import LEARNING_RECORDS, RAW_DIR
from src.data import load_record_info, parse_record_info, parse_test_annotations
from src.split import (assign_subjects, candidate_splits, category_from_labels,
                       make_split, record_table)


def _fake_table():
    """12 sujetos chicos, con sujetos mixtos (S04, S07) y uno con respiración (S01).

    Cuotas con TEST_FRAC = 0,30: A 7 -> 2, B 4 -> 1, C 6 -> 2.
    """
    rows = [  # record, subject, category, has_resp, apnea_minutes
        ("a01", "S01", "A", True, 400), ("x01", "S01", "A", False, 380),
        ("a02", "S02", "A", False, 300), ("x02", "S02", "A", False, 250),
        ("a03", "S03", "A", False, 200),
        ("a04", "S04", "A", False, 150), ("x04", "S04", "B", False, 60),
        ("x05", "S05", "A", False, 120),
        ("b01", "S06", "B", False, 30),
        ("b02", "S07", "B", False, 20), ("c01", "S07", "C", False, 2),
        ("b03", "S08", "B", False, 10),
        ("c02", "S09", "C", False, 0), ("x09", "S09", "C", False, 1),
        ("c03", "S10", "C", False, 0),
        ("x11", "S11", "C", False, 3),
        ("c04", "S12", "C", False, 0),
    ]
    t = pd.DataFrame(rows, columns=["record", "subject", "category", "has_resp",
                                    "apnea_minutes"])
    t["n_minutes"] = 450
    return t


def _brute_force(table, test_frac, max_diff):
    """Particiones válidas recorriendo todas las combinaciones, una por una."""
    quota = {c: round(test_frac * n) for c, n in table.category.value_counts().items()}
    pool = sorted(set(table.subject) - set(table.loc[table.has_resp, "subject"]))
    valid = set()
    for k in range(len(pool) + 1):
        for combo in combinations(pool, k):
            test = table.subject.isin(combo)
            if any((table[test].category == c).sum() != q for c, q in quota.items()):
                continue
            ft = table[test].apnea_minutes.sum() / table[test].n_minutes.sum()
            fd = table[~test].apnea_minutes.sum() / table[~test].n_minutes.sum()
            if abs(ft - fd) <= max_diff:
                valid.add(frozenset(combo))
    return valid


@pytest.mark.parametrize("max_diff", [1.0, 0.05, 0.02])
def test_candidate_splits_match_brute_force(max_diff):
    t = _fake_table()
    pool, masks = candidate_splits(t, 0.30, max_diff)
    found = {frozenset(s for i, s in enumerate(pool) if m >> i & 1) for m in masks}
    assert found == _brute_force(t, 0.30, max_diff)
    assert len(found) > 0


def test_balance_reduces_candidates():
    t = _fake_table()
    n = [len(candidate_splits(t, 0.30, d)[1]) for d in (1.0, 0.05)]
    assert n[0] > n[1] > 0


def test_split_rules():
    t = _fake_table()
    s = make_split(t, 0.30, seed=1, max_diff=0.05)
    assert (s.groupby("subject").set.nunique() == 1).all()          # sujetos enteros
    assert (s.loc[s.subject == "S01", "set"] == "dev").all()         # respiración en dev
    assert s[s.set == "test"].category.value_counts().to_dict() == {"A": 2, "B": 1, "C": 2}
    g = s.groupby("set")
    frac = g.apnea_minutes.sum() / g.n_minutes.sum()
    assert abs(frac["test"] - frac["dev"]) <= 0.05
    assert s.record.is_unique and len(s) == len(t)


def test_split_is_deterministic():
    t = _fake_table()
    assert make_split(t, seed=7, max_diff=0.05).equals(make_split(t, seed=7, max_diff=0.05))


def test_split_impossible_raises():
    with pytest.raises(ValueError):
        make_split(_fake_table(), max_diff=-1.0)


def test_too_many_subjects_raises():
    t = pd.DataFrame({"record": [f"r{i}" for i in range(30)],
                      "subject": [f"S{i}" for i in range(30)], "category": "A",
                      "has_resp": False, "apnea_minutes": 100, "n_minutes": 450})
    with pytest.raises(ValueError):
        candidate_splits(t)


def test_category_rule():
    assert category_from_labels(np.array([1] * 100 + [0] * 300)) == "A"
    assert category_from_labels(np.array([1] * 5 + [0] * 300)) == "B"
    assert category_from_labels(np.array([1] * 4 + [0, -1])) == "C"


def test_parse_test_annotations():
    text = "x01\n 0 NNAA\n 1 AN\nx02\n 0 NNN\n"
    out = parse_test_annotations(text)
    assert out["x01"].tolist() == [0, 0, 1, 1, 1, 0]
    assert out["x02"].tolist() == [0, 0, 0]


def test_parse_record_info():
    text = ("Record\tLength\tnon-apn\tapnea\thours\tAI\tHI\tAHI\tAge\tSex\theight\tweight\n"
            "\tminutes\tnon-apn\tminutes\tw/apnea\t\t\t\t\t\t(cm)\t(kg)\n\n"
            "a01\t490\t20\t470\t9\t12.5\t57.1\t69.6\t51\tM\t175\t102\t\t\n"
            "\t\n"
            "x33\t474\t471\t3\t0\t0.13\t0\t0.13\t28\tF\t169\t57\t\t\n")
    df = parse_record_info(text)
    assert df.record.tolist() == ["a01", "x33"]
    assert df.loc[0, ["apnea_min", "age", "sex", "height_cm", "weight_kg"]].tolist() \
        == [470, 51, "M", 175, 102]
    assert df.loc[1, "AHI"] == pytest.approx(0.13)


def test_assign_subjects():
    info = pd.DataFrame({
        "record":    ["a01", "a02", "c05", "c06", "x01", "x33"],
        "age":       [51, 38, 28, 28, 51, 28],
        "sex":       ["M", "M", "F", "F", "M", "F"],
        "height_cm": [175, 180, 169, 171, 175, 169],
        "weight_kg": [102, 120, 57, 65, 102, 57],
    })
    s = assign_subjects(info, aliases={"c06": "c05"})
    assert s["a01"] == s["x01"] == "S01"     # mismo perfil
    assert s["a02"] == "S02"                 # perfil único
    assert s["c05"] == s["c06"] == s["x33"] == "S03"  # alias + perfil
    assert assign_subjects(info, aliases={})["c06"] != s["c05"]


@pytest.mark.skipif(not (RAW_DIR / "additional-information.txt").exists(),
                    reason="falta additional-information.txt (scripts/download_data.py)")
def test_subjects_real_data():
    info = load_record_info()
    assert len(info) == 70
    s = assign_subjects(info)
    assert s.drop("c05").nunique() == 31     # c05 está excluido del análisis
    assert s["c06"] == s["x33"]
    assert s["a07"] == s["a16"] == s["x01"] == s["x30"]


_ALL_LABELS = (RAW_DIR / "test-dataset-annos.txt").exists() and all(
    (RAW_DIR / f"{r}.apn").exists() for r in LEARNING_RECORDS)


@pytest.mark.skipif(not _ALL_LABELS, reason="faltan anotaciones (scripts/download_data.py)")
def test_split_real_data():
    s = make_split(record_table())
    assert (s.groupby("subject").set.nunique() == 1).all()
    assert s[s.set == "test"].category.value_counts().to_dict() == {"A": 12, "B": 3, "C": 6}
    g = s.groupby("set")
    frac = g.apnea_minutes.sum() / g.n_minutes.sum()
    assert abs(frac["test"] - frac["dev"]) <= 0.02
