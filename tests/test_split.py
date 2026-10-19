import numpy as np
import pandas as pd

from src.config import RESP_RECORDS
from src.data import parse_test_annotations
from src.split import category_from_labels, make_split


def _fake_table():
    recs = ([f"a{i:02d}" for i in range(1, 21)] + [f"xa{i:02d}" for i in range(20)]
            + [f"b{i:02d}" for i in range(1, 6)] + [f"xb{i:02d}" for i in range(5)]
            + [f"c{i:02d}" for i in range(1, 11) if i != 5] + [f"xc{i:02d}" for i in range(10)])
    cat = [r[1].upper() if r[0] == "x" else r[0].upper() for r in recs]
    return pd.DataFrame({"record": recs, "category": cat,
                         "has_resp": [r in RESP_RECORDS for r in recs]})


def test_split_counts_and_rules():
    s = make_split(_fake_table())
    counts = s[s.set == "test"].groupby("category").size().to_dict()
    assert counts == {"A": 12, "B": 3, "C": 6}
    assert (s.loc[s.has_resp, "set"] == "dev").all()
    assert s.record.is_unique


def test_split_is_deterministic():
    assert make_split(_fake_table()).equals(make_split(_fake_table()))


def test_category_rule():
    assert category_from_labels(np.array([1] * 100 + [0] * 300)) == "A"
    assert category_from_labels(np.array([1] * 5 + [0] * 300)) == "B"
    assert category_from_labels(np.array([1] * 4 + [0, -1])) == "C"


def test_parse_test_annotations():
    text = "x01\n 0 NNAA\n 1 AN\nx02\n 0 NNN\n"
    out = parse_test_annotations(text)
    assert out["x01"].tolist() == [0, 0, 1, 1, 1, 0]
    assert out["x02"].tolist() == [0, 0, 0]
