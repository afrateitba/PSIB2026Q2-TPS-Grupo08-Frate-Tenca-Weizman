"""¿Usan el filtro de Wiener los trabajos de detección de apnea con ECG y de EDR?

Búsqueda reproducible en las fuentes oficiales del NCBI (API E-utilities):
1. PubMed Central, artículos de acceso abierto: se baja el texto completo y se
   cuenta cuántos mencionan "Wiener" y, para comparar, otros filtros comunes.
2. PubMed: cuántos resúmenes mencionan Wiener.
Resultado: docs/busqueda_wiener_pmc.json (lo cita notebooks/07_simplificacion.ipynb, sección 9).
Uso: python scripts/buscar_wiener_pmc.py  (necesita acceso a eutils.ncbi.nlm.nih.gov)
"""
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SALIDA = Path(__file__).resolve().parents[1] / "docs" / "busqueda_wiener_pmc.json"
APNEA = ('("sleep apnea"[Title/Abstract] OR "sleep apnoea"[Title/Abstract]) AND '
         '(ECG[Title/Abstract] OR electrocardiogram[Title/Abstract] OR electrocardiographic[Title/Abstract]) AND '
         '(detection[Title/Abstract] OR classification[Title/Abstract] OR screening[Title/Abstract])')
EDR = ('("ECG-derived respiration"[Title/Abstract] OR "ECG derived respiration"[Title/Abstract] OR '
       '"electrocardiogram-derived respiration"[Title/Abstract] OR "ECG-derived respiratory"[Title/Abstract])')
TERMINOS = {"Wiener": r"wiener", "Butterworth": r"butterworth", "pasabanda": r"band-?pass", "Pan-Tompkins": r"pan[- ]?(and )?tompkins",
            "wavelet": r"wavelet", "filtro de mediana": r"median filter", "notch": r"notch", "promedio móvil": r"moving[- ]average",
            "Kalman": r"kalman", "filtro adaptativo": r"adaptive filter",
            "promediado coherente o plantilla": r"ensemble[- ]averag|coherent averag|template",
            "base Apnea-ECG": r"apnea-ecg|apnoea-ecg|physionet apnea"}


def get(url):
    for i in range(4):
        try:
            return urllib.request.urlopen(url, timeout=60).read()
        except Exception:  # noqa: BLE001
            time.sleep(2 * (i + 1))
    raise RuntimeError(url)


def buscar(db, q, n=1000):
    r = json.loads(get(BASE + "esearch.fcgi?" + urllib.parse.urlencode({"db": db, "term": q, "retmax": n, "retmode": "json"})))
    time.sleep(0.4)
    return int(r["esearchresult"]["count"]), r["esearchresult"]["idlist"]


def textos(ids):
    out = {}
    for i in range(0, len(ids), 40):
        raiz = ET.fromstring(get(BASE + "efetch.fcgi?" + urllib.parse.urlencode({"db": "pmc", "id": ",".join(ids[i:i + 40]), "retmode": "xml"})))
        for art in raiz.findall(".//article"):
            pmcid = next((a.text for a in art.findall(".//article-id") if a.get("pub-id-type") in ("pmc", "pmcid")), None)
            titulo = art.find(".//article-title")
            body = art.find(".//body")
            if body is not None:
                out[pmcid] = {"titulo": " ".join("".join(titulo.itertext()).split()) if titulo is not None else "",
                              "cuerpo": " ".join("".join(body.itertext()).split())}
        time.sleep(0.4)
    return out


def contar(tx):
    return {t: sum(bool(re.search(p, v["cuerpo"], re.I)) for v in tx.values()) for t, p in TERMINOS.items()}


if __name__ == "__main__":
    res = {"fecha": time.strftime("%Y-%m-%d"), "fuente": "NCBI E-utilities (PubMed y PubMed Central)", "pmc": {}, "pubmed": {}}
    for nombre, q in (("deteccion de apnea con ECG", APNEA), ("EDR", EDR)):
        qq = q + ' AND "open access"[filter]'
        n, ids = buscar("pmc", qq)
        tx = textos(ids)
        menc = {k: {"titulo": v["titulo"], "contexto": [v["cuerpo"][max(0, m.start() - 160):m.end() + 160]
                                                         for m in re.finditer("wiener", v["cuerpo"], re.I)][:3]}
                for k, v in tx.items() if re.search("wiener", v["cuerpo"], re.I)}
        ae = {k: v for k, v in tx.items() if re.search(TERMINOS["base Apnea-ECG"], v["cuerpo"], re.I)}
        res["pmc"][nombre] = {"consulta": qq, "resultados": n, "con_texto_completo": len(tx), "conteos": contar(tx),
                              "con_base_apnea_ecg": {"n": len(ae), "conteos": contar(ae)}, "mencionan_wiener": menc}
        for et, qp in ((nombre, q), (nombre + " y Wiener", q + " AND Wiener[Title/Abstract]")):
            res["pubmed"][et] = {"consulta": qp, "resultados": buscar("pubmed", qp, 0)[0]}
        print(nombre, res["pmc"][nombre]["con_texto_completo"], res["pmc"][nombre]["conteos"]["Wiener"], flush=True)
    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("escrito", SALIDA)
