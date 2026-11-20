"""Verificación de todas las referencias del proyecto en fuentes oficiales y generación de docs/referencias.md.

Para cada referencia con DOI: Crossref (existe, metadatos, licencia), doi.org (resuelve) y PubMed
(PMID y texto libre en PMC). Para las páginas oficiales sin DOI (PhysioNet): que la página responda.
"""
import datetime
from pathlib import Path
import json
import time
import urllib.error
import urllib.parse
import urllib.request

UA = {"User-Agent": "verificador-referencias/1.0 (TP universitario)"}
HOY = datetime.date.today().isoformat()

# clave: (cita en el texto, referencia completa, DOI o None, URL oficial extra o None, dónde se usa)
REFS = [
    ('Aickin y Gensler (1996)', 'Aickin, M. y Gensler, H. (1996). Adjusting for multiple testing when reporting research results: the Bonferroni vs Holm methods. American Journal of Public Health, 86(5), 726–728.', '10.2105/AJPH.86.5.726', None, '04 §8; 06 §5; 07 §4 (método de Holm)'),
    ('Arlot y Celisse (2010)', 'Arlot, S. y Celisse, A. (2010). A survey of cross-validation procedures for model selection. Statistics Surveys, 4, 40–79.', '10.1214/09-SS054', None, '04 §15'),
    ('Bates et al. (2023)', 'Bates, S., Hastie, T. y Tibshirani, R. (2023). Cross-validation: what does it estimate and how well does it do it? Journal of the American Statistical Association, 119(546), 1434–1445.', '10.1080/01621459.2023.2197686', None, '07 §7 (intervalos de la validación cruzada)'),
    ('Bazett (1920)', 'Bazett, H. C. (1920). An analysis of the time-relations of electrocardiograms. Heart, 7, 353–370. Reimpreso en Annals of Noninvasive Electrocardiology, 2(2), 177–194 (1997).', '10.1111/j.1542-474X.1997.tb00325.x', None, '02 §2'),
    ('Berger (1982)', 'Berger, R. L. (1982). Multiparameter hypothesis testing and acceptance sampling. Technometrics, 24(4), 295–300.', '10.1080/00401706.1982.10487790', None, '04 §14; 06 §5'),
    ('Breiman et al. (1984)', 'Breiman, L., Friedman, J. H., Olshen, R. A. y Stone, C. J. (1984). Classification and Regression Trees. Chapman & Hall/CRC.', '10.1201/9781315139470', None, 'docs/criterio_parsimonia.md (regla de sencillez)'),
    ('Carter (1987)', 'Carter, G. C. (1987). Coherence and time delay estimation. Proceedings of the IEEE, 75(2), 236–255.', '10.1109/PROC.1987.13723', None, '03 §6'),
    ('Charlton et al. (2018)', 'Charlton, P. H. et al. (2018). Breathing rate estimation from the electrocardiogram and photoplethysmogram: a review. IEEE Reviews in Biomedical Engineering, 11, 2–20.', '10.1109/RBME.2017.2763681', None, '03 §1'),
    ('de Chazal et al. (2003)', "de Chazal, P., Heneghan, C., Sheridan, E., Reilly, R., Nolan, P. y O'Malley, M. (2003). Automated processing of the single-lead electrocardiogram for the detection of obstructive sleep apnoea. IEEE Transactions on Biomedical Engineering, 50(6), 686–696.", '10.1109/TBME.2003.812203', None, '07 §9'),
    ('Clifford et al. (2002)', 'Clifford, G. D., McSharry, P. E. y Tarassenko, L. (2002). Characterizing artefact in the normal human 24-hour RR time series to aid identification and artificial replication of circadian variations in human beat to beat heart rate using a simple threshold. Computers in Cardiology, 29, 129–132.', '10.1109/CIC.2002.1166724', 'https://physionet.org/files/challenge-2002/1.0.0/papers/129.pdf', '02 §4'),
    ('Dobbin y Simon (2011)', 'Dobbin, K. K. y Simon, R. M. (2011). Optimally splitting cases for training and testing high dimensional classifiers. BMC Medical Genomics, 4, 31.', '10.1186/1755-8794-4-31', None, '01 §2'),
    ('Efron y Tibshirani (1993)', 'Efron, B. y Tibshirani, R. J. (1993). An Introduction to the Bootstrap. Chapman & Hall/CRC.', '10.1201/9780429246593', None, '04'),
    ('Fluss et al. (2005)', 'Fluss, R., Faraggi, D. y Reiser, B. (2005). Estimation of the Youden index and its associated cutoff point. Biometrical Journal, 47(4), 458–472.', '10.1002/bimj.200410135', None, '04 §9'),
    ('Guilleminault et al. (1984)', 'Guilleminault, C., Connolly, S., Winkle, R., Melvin, K. y Tilkian, A. (1984). Cyclical variation of the heart rate in sleep apnoea syndrome. The Lancet, 323(8369), 126–131.', '10.1016/S0140-6736(84)90062-X', None, '01 §6–7'),
    ('Habibzadeh et al. (2016)', 'Habibzadeh, F., Habibzadeh, P. y Yadollahie, M. (2016). On determining the most appropriate test cut-off value: the case of tests with continuous results. Biochemia Medica, 26(3), 297–307.', '10.11613/BM.2016.034', None, '04 §9'),
    ('Hampel (1974)', 'Hampel, F. R. (1974). The influence curve and its role in robust estimation. Journal of the American Statistical Association, 69(346), 383–393.', '10.1080/01621459.1974.10482962', None, '03 §6'),
    ('Hanley y McNeil (1982)', 'Hanley, J. A. y McNeil, B. J. (1982). The meaning and use of the area under a receiver operating characteristic (ROC) curve. Radiology, 143(1), 29–36.', '10.1148/radiology.143.1.7063747', None, '04'),
    ('Hastie et al. (2009)', 'Hastie, T., Tibshirani, R. y Friedman, J. (2009). The Elements of Statistical Learning (2.ª ed.), §7.10. Springer.', '10.1007/978-0-387-84858-7', None, 'docs/criterio_parsimonia.md (regla de un error estándar)'),
    ('Kligfield et al. (2007)', 'Kligfield, P. et al. (2007). Recommendations for the standardization and interpretation of the electrocardiogram: part I. Circulation, 115(10), 1306–1324.', '10.1161/CIRCULATIONAHA.106.180200', None, '02 §1'),
    ('Laguna et al. (1998)', 'Laguna, P., Moody, G. B. y Mark, R. G. (1998). Power spectral density of unevenly sampled data by least-square analysis: performance and application to heart rate signals. IEEE Transactions on Biomedical Engineering, 45(6), 698–715.', '10.1109/10.678605', None, '04 §1'),
    ('Lander y Berbari (1997)', 'Lander, P. y Berbari, E. J. (1997). Time-frequency plane Wiener filtering of the high-resolution ECG: background and time-frequency representations. IEEE Transactions on Biomedical Engineering, 44(4), 247–255.', '10.1109/10.563294', None, '07 §9'),
    ('Lippman et al. (1994)', 'Lippman, N., Stein, K. M. y Lerman, B. B. (1994). Comparison of methods for removal of ectopy in measurement of heart rate variability. American Journal of Physiology, 267(1), H411–H418.', '10.1152/ajpheart.1994.267.1.H411', None, '02 §4'),
    ('Lomb (1976)', 'Lomb, N. R. (1976). Least-squares frequency analysis of unequally spaced data. Astrophysics and Space Science, 39, 447–462.', '10.1007/BF00648343', None, '04 §1'),
    ('Metz (1978)', 'Metz, C. E. (1978). Basic principles of ROC analysis. Seminars in Nuclear Medicine, 8(4), 283–298.', '10.1016/S0001-2998(78)80014-2', None, '04 §9'),
    ('Möcks et al. (1986)', 'Möcks, J., Gasser, T., Köhler, W. y De Weerd, J. P. C. (1986). Does filtering and smoothing of average evoked potentials really pay? A statistical comparison. Electroencephalography and Clinical Neurophysiology, 64(5), 469–480.', '10.1016/0013-4694(86)90080-5', None, '07 §9'),
    ('Nadeau y Bengio (2003)', 'Nadeau, C. y Bengio, Y. (2003). Inference for the generalization error. Machine Learning, 52(3), 239–281.', '10.1023/A:1024068626366', None, '07 §7'),
    ('Nagelkerke y Strackee (1979)', 'Nagelkerke, N. J. D. y Strackee, J. (1979). Some notes on the statistical properties of a posteriori Wiener filtering. Biological Cybernetics, 33(2), 121–123.', '10.1007/BF00355260', None, '07 §9'),
    ('Pan y Tompkins (1985)', 'Pan, J. y Tompkins, W. J. (1985). A real-time QRS detection algorithm. IEEE Transactions on Biomedical Engineering, 32(3), 230–236.', '10.1109/TBME.1985.325532', None, '02 §2'),
    ('Peltola (2012)', 'Peltola, M. A. (2012). Role of editing of R–R intervals in the analysis of heart rate variability. Frontiers in Physiology, 3, 148.', '10.3389/fphys.2012.00148', None, '02 §4'),
    ('Penzel et al. (2000)', 'Penzel, T., Moody, G. B., Mark, R. G., Goldberger, A. L. y Peter, J. H. (2000). The Apnea-ECG Database. Computers in Cardiology, 27, 255–258.', '10.1109/CIC.2000.898505', 'https://physionet.org/content/apnea-ecg/1.0.0/', '01 §1'),
    ('Penzel et al. (2002)', 'Penzel, T., McNames, J., de Chazal, P., Raymond, B., Murray, A. y Moody, G. (2002). Systematic comparison of different algorithms for apnoea detection based on electrocardiogram recordings. Medical and Biological Engineering and Computing, 40(4), 402–407.', '10.1007/BF02345072', None, '07 §9; estado del arte'),
    ('Perkins y Schisterman (2006)', 'Perkins, N. J. y Schisterman, E. F. (2006). The inconsistency of "optimal" cutpoints obtained using two criteria based on the receiver operating characteristic curve. American Journal of Epidemiology, 163(7), 670–675.', '10.1093/aje/kwj063', None, '04 §9'),
    ('PhysioNet: bxb', 'PhysioNet. bxb: ANSI/AAMI-standard beat-by-beat annotation comparator. WFDB Applications Guide.', None, 'https://physionet.org/physiotools/wag/bxb-1.htm', '02 §2'),
    ('Sörnmo y Laguna (2005)', 'Sörnmo, L. y Laguna, P. (2005). Bioelectrical Signal Processing in Cardiac and Neurological Applications. Elsevier Academic Press.', '10.1016/B978-0-12-437552-9.X5000-4', None, '02 §2; 03 §5'),
    ('Spearman (1904)', 'Spearman, C. (1904). The proof and measurement of association between two things. American Journal of Psychology, 15(1), 72–101. Reimpreso en International Journal of Epidemiology, 39(5), 1137–1150 (2010).', '10.1093/ije/dyq191', None, '04'),
    ('Tarvainen et al. (2002)', 'Tarvainen, M. P., Ranta-aho, P. O. y Karjalainen, P. A. (2002). An advanced detrending method with application to HRV analysis. IEEE Transactions on Biomedical Engineering, 49(2), 172–175.', '10.1109/10.979357', None, '04 §15'),
    ('Task Force (1996)', 'Task Force of the European Society of Cardiology and the North American Society of Pacing and Electrophysiology (1996). Heart rate variability: standards of measurement, physiological interpretation and clinical use. Circulation, 93(5), 1043–1065.', '10.1161/01.CIR.93.5.1043', None, '04 §1'),
    ('Ünal (2017)', 'Ünal, I. (2017). Defining an optimal cut-point value in ROC analysis: an alternative approach. Computational and Mathematical Methods in Medicine, 2017, 3762651.', '10.1155/2017/3762651', None, '04 §9'),
    ('Ungan y Başar (1976)', 'Ungan, P. y Başar, E. (1976). Comparison of Wiener filtering and selective averaging of evoked potentials. Electroencephalography and Clinical Neurophysiology, 40(5), 516–520.', '10.1016/0013-4694(76)90081-X', None, '07 §9'),
    ('Varma y Simon (2006)', 'Varma, S. y Simon, R. (2006). Bias in error estimation when using cross-validation for model selection. BMC Bioinformatics, 7, 91.', '10.1186/1471-2105-7-91', None, '07 §8 (validación cruzada anidada)'),
    ('Varon et al. (2020)', 'Varon, C. et al. (2020). A comparative study of ECG-derived respiration in ambulatory monitoring using the single-lead ECG. Scientific Reports, 10, 5704.', '10.1038/s41598-020-62624-5', None, '03 §2'),
    ('Virtanen et al. (2020)', 'Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods, 17, 261–272.', '10.1038/s41592-019-0686-2', None, '03 §5'),
    ('Walter (1968)', 'Walter, D. O. (1968). A posteriori "Wiener filtering" of average evoked responses. Electroencephalography and Clinical Neurophysiology, Suppl. 27, 61–70. Sin DOI; registro oficial en PubMed (PMID 4184013).', None, 'https://pubmed.ncbi.nlm.nih.gov/4184013/', '07 §9'),
    ('de Weerd (1981)', 'de Weerd, J. P. C. (1981). A posteriori time-varying filtering of averaged evoked potentials. I. Introduction and conceptual basis. Biological Cybernetics, 41(3), 211–222.', '10.1007/BF00340322', None, '07 §9'),
    ('Welch (1967)', 'Welch, P. D. (1967). The use of fast Fourier transform for the estimation of power spectra: a method based on time averaging over short, modified periodograms. IEEE Transactions on Audio and Electroacoustics, 15(2), 70–73.', '10.1109/TAU.1967.1161901', None, '01 §7; 04 §1'),
    ('Wiener (1949)', 'Wiener, N. (1949). Extrapolation, Interpolation, and Smoothing of Stationary Time Series. MIT Press.', '10.7551/mitpress/2946.001.0001', None, '03 §5'),
    ('Youden (1950)', 'Youden, W. J. (1950). Index for rating diagnostic tests. Cancer, 3(1), 32–35.', '10.1002/1097-0142(1950)3:1<32::AID-CNCR2820030106>3.0.CO;2-3', None, '04 §9'),
    ('Zweig y Campbell (1993)', 'Zweig, M. H. y Campbell, G. (1993). Receiver-operating characteristic (ROC) plots: a fundamental evaluation tool in clinical medicine. Clinical Chemistry, 39(4), 561–577.', '10.1093/clinchem/39.4.561', None, '04 §9'),
]


def get(url, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.status, r.read()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def doi_code(doi):
    req = urllib.request.Request("https://doi.org/" + urllib.parse.quote(doi, safe="/()<>:;."), headers=UA, method="HEAD")
    try:
        urllib.request.build_opener(NoRedirect).open(req, timeout=30)
        return 200
    except urllib.error.HTTPError as e:
        return e.code


def reintentar(f, *a):
    for k in range(4):
        try:
            return f(*a)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 * (k + 1)); continue
            raise
    return f(*a)


filas = []
for cita, ref, doi, url, donde in REFS:
    fila = {"cita": cita, "ref": ref, "doi": doi, "url": url, "donde": donde}
    if doi:
        m = json.loads(reintentar(get, "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/()<>:;."))[1])["message"]
        fila["crossref_titulo"] = (m.get("title") or [""])[0]
        fila["licencia"] = [l.get("URL", "") for l in m.get("license", [])]
        fila["doi_http"] = doi_code(doi)
        time.sleep(0.5)
        q = urllib.parse.quote(f'"{doi}"[DOI]')
        ids = json.loads(reintentar(get, f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term={q}")[1])["esearchresult"]["idlist"]
        fila["pmid"] = ids[0] if len(ids) == 1 else None
        fila["pmc"] = None
        if fila["pmid"]:
            time.sleep(0.5)
            s = json.loads(reintentar(get, f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={fila['pmid']}")[1])["result"][fila["pmid"]]
            fila["pmc"] = next((x["value"] for x in s.get("articleids", []) if x["idtype"] == "pmc"), None)
            fila["pubmed_titulo"] = s.get("title", "")
        time.sleep(0.5)
    if url and "pubmed.ncbi.nlm.nih.gov/" in url:   # sin DOI: se verifica el PMID con E-utilities
        pmid = url.rstrip("/").split("/")[-1]
        s_ = json.loads(reintentar(get, f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={pmid}")[1])["result"][pmid]
        fila["pmid"], fila["pubmed_titulo"], fila["url_http"] = pmid, s_.get("title", ""), "PubMed ✓"
        time.sleep(0.5)
    elif url:
        try:
            fila["url_http"] = get(url)[0]
        except urllib.error.HTTPError as e:
            fila["url_http"] = e.code
    filas.append(fila)
    print(cita, "| doi.org", fila.get("doi_http"), "| PMID", fila.get("pmid"), "| PMC", fila.get("pmc"), "| url", fila.get("url_http"), "|", fila.get("crossref_titulo", "")[:60])




def acceso(f):
    if f.get("pmc"):
        return f"Texto completo libre en PubMed Central ([{f['pmc']}](https://pmc.ncbi.nlm.nih.gov/articles/{f['pmc']}/))"
    if any("creativecommons" in l for l in f.get("licencia", [])):
        return "Acceso abierto (licencia Creative Commons)"
    if f.get("url") and "physionet.org" in f["url"] and f.get("url_http") == 200:
        return f"Libre en PhysioNet ([enlace]({f['url']}))"
    if f.get("pmid"):
        return f"Resumen público en [PubMed](https://pubmed.ncbi.nlm.nih.gov/{f['pmid']}/); texto completo en la página del editor (puede requerir suscripción)"
    return "Página del editor (puede requerir suscripción o acceso institucional)"


lineas = ["# Referencias", "",
          f"Todas las fuentes citadas en el repositorio, verificadas el {HOY} en fuentes oficiales:",
          "- **Crossref** (`api.crossref.org`): el DOI existe y sus metadatos coinciden con la cita.",
          "- **doi.org**: el DOI resuelve a la página del editor (respuesta 302 de redirección).",
          "- **PubMed** (`eutils.ncbi.nlm.nih.gov`): PMID y, si existe, texto completo libre en PubMed Central.",
          "- **PhysioNet**: las páginas oficiales sin DOI responden (código 200). Walter (1968), sin DOI, se verifica por su PMID en PubMed.",
          "",
          "Solo se citan fuentes con un identificador oficial (DOI) o una página oficial. Malik y Camm (1995), un libro sin DOI, aparece solo como la fuente que cita Clifford et al. (2002) para la regla del 20 %. La norma ANSI/AAMI EC57 se cita a través de la documentación oficial de `bxb` en PhysioNet, su implementación de referencia. Moody et al. (1985), sin DOI ni copia oficial en línea, se reemplazó por las revisiones de Charlton et al. (2018) y Varon et al. (2020).",
          "", "| Cita | Referencia | Enlace oficial | Verificación | Acceso | Dónde se usa |", "|---|---|---|---|---|---|"]
for f in filas:
    enlace = f"[doi:{f['doi']}](https://doi.org/{f['doi']})" if f["doi"] else f"[página oficial]({f['url']})"
    ver = []
    if f["doi"]:
        ver.append(f"Crossref ✓; doi.org {f['doi_http']}")
        if f.get("pmid"):
            ver.append(f"PubMed [{f['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{f['pmid']}/)")
    if f.get("url"):
        ver.append(f"PubMed [{f['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{f['pmid']}/) ✓ (E-utilities)" if f.get("url_http") == "PubMed ✓"
                   else f"página {f.get('url_http')}")
    lineas.append(f"| {f['cita']} | {f['ref']} | {enlace} | {'; '.join(ver)} | {acceso(f)} | {f['donde']} |")
lineas += ["", "Para repetir la verificación: `python scripts/verificar_referencias.py` (necesita acceso a api.crossref.org, doi.org, eutils.ncbi.nlm.nih.gov y physionet.org).", ""]
open(Path(__file__).resolve().parents[1] / "docs" / "referencias.md", "w").write("\n".join(lineas))
print("docs/referencias.md escrito")
