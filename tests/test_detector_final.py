import json
import shutil

import numpy as np
import pytest

import src.qrs.pan_tompkins as pt
from src import detector_final as df
from src.config import RAW_DIR


def test_parametros_congelados():
    """docs/parametros_final.json es el archivo congelado: si cambia, hay que volver a registrarlo."""
    assert df.sha256() == df.SHA256_PARAMS
    p = df.cargar_params()
    assert {"mu1", "s1", "mu2", "s2", "w", "umbral", "etapas", "etapas_qrs"} <= set(p)


def test_un_archivo_cambiado_no_se_carga(tmp_path):
    copia = tmp_path / "p.json"
    shutil.copy(df.PARAMS_PATH, copia)
    p = json.loads(copia.read_text()); p["umbral"] += 0.01
    copia.write_text(json.dumps(p))
    with pytest.raises(ValueError):
        df.cargar_params(copia)


def test_opciones_del_detector_final():
    p = df.cargar_params()
    o = df.opciones_edr(p)
    assert o == {"edr_method": "area", "wiener": False, "exclude_ectopic": True, "hampel": True, "aberrant": False,
                 "relative": True, "interp": "cubic", "refine": True}
    assert p["etapas"]["tendencia_welch"] == "linear" and p["etapas"]["max_rr_corregidos_por_minuto"] == 0.2


def test_qrs_coincide_con_el_congelado(monkeypatch):
    p = df.cargar_params()
    df.verificar_qrs(p)                                    # src/config.py tiene las seis etapas activas
    monkeypatch.setattr(pt, "QRS_RELEARN", False)
    with pytest.raises(ValueError):
        df.verificar_qrs(p)


@pytest.mark.skipif(not (RAW_DIR / "a03.dat").exists(), reason="faltan los datos")
def test_tabla_final_a03():
    p = df.cargar_params()
    tab, s = df.tabla_final("a03", params=p)
    assert np.allclose(tab.C, tab.termino_rr + tab.termino_edr)
    assert ((tab.C > p["umbral"]).astype(int) == tab.decision).all()
    assert tab.termino_edr.nunique() == 1
    assert (tab.evaluado == ((tab.label >= 0) & (tab.q <= 0.2))).all()
    assert "confianza" not in tab
