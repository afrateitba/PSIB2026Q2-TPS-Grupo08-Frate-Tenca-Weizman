import numpy as np
import pandas as pd
import pytest

from src.config import RAW_DIR, RESP_RECORDS
from src.data import load_record_info, parse_record_info, parse_test_annotations
from src.split import assign_subjects, category_from_labels, make_split


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
