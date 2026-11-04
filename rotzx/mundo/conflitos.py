"""Conflitos armados: UCDP/PRIO Armed Conflict Dataset (Uppsala Conflict Data Program, licença CC BY 4.0) (D43).

A base registra, ano a ano, cada conflito armado em que pelo menos um dos lados é um governo e que deixou 25 ou mais mortes
em combate no ano. Para cada um: onde, quem luta contra quem, quem apoia com tropas, o que está em disputa (território,
governo ou os dois) e a intensidade (25 a 999 mortes em combate no ano, ou 1.000 ou mais, o que a base chama de guerra).

Isto é o que a base mede. Ela não cobre protestos, crises diplomáticas nem conflitos com menos de 25 mortes no ano,
e os nomes dos lados vêm como na base (em inglês).
"""
import csv
import io
import re
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from .. import config

PAGINA = "https://ucdp.uu.se/downloads/"
LINK = "https://ucdp.uu.se/conflict/{id}"
# Códigos Gleditsch & Ward (os da UCDP) dos países do protótipo, conferidos contra os nomes "Government of …" da própria base
GW = {"BRA": 140, "CHN": 710, "USA": 2, "ARG": 160, "NLD": 210, "ESP": 230, "DEU": 260, "MEX": 70, "CHL": 155, "JPN": 740,
      "IND": 750, "ITA": 325, "KOR": 732, "CAN": 20, "FRA": 220, "PRY": 150, "RUS": 365, "SAU": 670, "GBR": 200, "COL": 100,
      "URY": 165}
DISPUTA = {"1": "território", "2": "governo", "3": "território e governo"}
TIPO = {"1": "extrassistêmico", "2": "entre Estados", "3": "interno", "4": "interno, com tropas estrangeiras"}
INTENSIDADE = {"1": "25 a 999 mortes em combate no ano", "2": "1.000 ou mais mortes em combate no ano"}


def _abrir(url: str, timeout: int = 120):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT}), timeout=timeout)


def link_mais_recente(html: str) -> str:
    """O arquivo CSV da versão mais recente da base, a partir da página de downloads (ex.: ucdp-prio-acd-261-csv.zip)."""
    achados = re.findall(r'href="(https://ucdp\.uu\.se/downloads/ucdpprio/ucdp-prio-acd-(\d+)-csv\.zip)"', html)
    if not achados:
        raise ValueError("a página de downloads da UCDP mudou: não achei ucdp-prio-acd-*-csv.zip")
    return max(achados, key=lambda a: int(a[1]))[0]


def ler(conteudo_zip: bytes) -> List[dict]:
    z = zipfile.ZipFile(io.BytesIO(conteudo_zip))
    nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    return list(csv.DictReader(io.TextIOWrapper(z.open(nome), encoding="utf-8")))


def _codigos(txt: str) -> List[int]:
    return [int(c) for c in re.findall(r"\d+", txt or "")]


def _lados(txt: str) -> List[str]:
    return [s.strip() for s in (txt or "").split(",") if s.strip()]


def resumir(linhas: List[dict], iso3: List[str], anos: int = 5) -> dict:
    """Conflitos de cada país nos últimos `anos` anos da base e o panorama do último ano."""
    ultimo = max(int(r["year"]) for r in linhas)
    desde = ultimo - anos + 1
    janela = [r for r in linhas if int(r["year"]) >= desde]
    por_conflito: Dict[str, List[dict]] = {}
    for r in janela:
        por_conflito.setdefault(r["conflict_id"], []).append(r)

    def conflito(rs: List[dict]) -> dict:
        rs = sorted(rs, key=lambda r: int(r["year"]))
        u = rs[-1]
        return {"id": u["conflict_id"], "local": u["location"], "lado_a": _lados(u["side_a"]), "lado_b": _lados(u["side_b"]),
                "apoio_a": _lados(u["side_a_2nd"]), "apoio_b": _lados(u["side_b_2nd"]),
                "disputa": DISPUTA.get(u["incompatibility"], u["incompatibility"]), "territorio": u["territory_name"],
                "tipo": TIPO.get(u["type_of_conflict"], u["type_of_conflict"]),
                "anos": [int(r["year"]) for r in rs], "ultimo_ano": int(u["year"]),
                "guerra_no_ultimo_ano": u["intensity_level"] == "2", "intensidade": INTENSIDADE.get(u["intensity_level"], ""),
                "inicio": u["start_date"], "url": LINK.format(id=u["conflict_id"])}

    def envolvido(r: dict, g: int) -> Optional[str]:
        if g in _codigos(r["gwno_a"]) + _codigos(r["gwno_b"]):
            return "lado principal"
        for lado in ("a", "b"):
            if g in _codigos(r[f"gwno_{lado}_2nd"]):
                return f"apoio_{lado}"
        return "no território" if g in _codigos(r["gwno_loc"]) else None

    paises = {}
    for k in iso3:
        g = GW[k]
        lista = []
        for rs in por_conflito.values():
            meus = [(int(r["year"]), envolvido(r, g), r) for r in rs]
            meus = sorted((m for m in meus if m[1]), key=lambda m: m[0])
            if not meus:
                continue
            c = conflito(rs)
            ano_k, papel, r = meus[-1]           # o envolvimento mais recente do país neste conflito
            c["anos_pais"] = [m[0] for m in meus]
            if papel.startswith("apoio_"):
                lado = papel[-1]
                # Muitos países do mesmo lado costumam ser tropas de missões multinacionais (ex.: as de paz da ONU);
                # a base não separa, então o painel mostra quantos são.
                c["papel"] = "apoio com tropas"
                c["apoia"] = _lados(r[f"side_{lado}"])
                c["apoiadores_no_lado"] = len(_codigos(r[f"gwno_{lado}_2nd"]))
            else:
                c["papel"] = papel
            lista.append(c)
        lista.sort(key=lambda c: (-c["anos_pais"][-1], c["papel"] != "lado principal", not c["guerra_no_ultimo_ano"], c["local"]))
        paises[k] = {"conflitos": lista}

    ativos = [conflito(rs) for rs in por_conflito.values() if any(int(r["year"]) == ultimo for r in rs)]
    ativos.sort(key=lambda c: (not c["guerra_no_ultimo_ano"], c["local"]))
    return {"ultimo_ano": ultimo, "desde": desde, "paises": paises,
            "mundo": {"ativos": ativos, "total": len(ativos), "guerras": sum(c["guerra_no_ultimo_ano"] for c in ativos)}}


def coletar(iso3: List[str], pasta: Optional[Path] = None) -> dict:
    with _abrir(PAGINA, 60) as r:
        url = link_mais_recente(r.read().decode("utf-8", errors="replace"))
    with _abrir(url) as r:
        dados = r.read()
    if pasta:
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / url.rsplit("/", 1)[-1]).write_bytes(dados)
    out = resumir(ler(dados), iso3)
    out["versao"] = re.search(r"acd-(\d+)-csv", url).group(1)
    return out
