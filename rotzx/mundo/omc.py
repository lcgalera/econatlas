"""Disputas comerciais na OMC: com o Brasil e de cada país com o resto do mundo (D42).

Fonte: a lista oficial de disputas do site da OMC (www.wto.org, "Disputes by country"), que o próprio site carrega de dois
arquivos de dados em JavaScript. Eles são lidos aqui como texto (expressões regulares), nunca executados.
Cada disputa tem número (DS…), título oficial em inglês, quem abriu (reclamante), contra quem (demandado), data e situação.

Na OMC, quem responde e reclama pelos países da União Europeia é a própria UE (código "EEC"): para Alemanha, França etc.,
as disputas que aparecem são as da UE, e o painel avisa.
"""
import html
import re
import urllib.request
from datetime import date
from typing import Dict, List, Optional

from .. import config

URL_CASOS = "https://www.wto.org/library/disputes/dispute_case_arrays_e.js"
URL_TABELAS = "https://www.wto.org/library/disputes/dispute_arrays_e.js"
LINK = "https://www.wto.org/english/tratop_e/dispu_e/cases_e/{ds}_e.htm"
UE = {"AUT", "BEL", "BGR", "CYP", "CZE", "DEU", "DNK", "ESP", "EST", "FIN", "FRA", "GRC", "HRV", "HUN", "IRL", "ITA", "LTU",
      "LUX", "LVA", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "SWE"}  # membros da UE (27, desde 2020)

# Situação oficial da OMC → frase curta em português. "encerrada" = o caso não tem mais etapa pendente.
SITUACAO = {
    "ST1": ("em consultas", False), "ST32": ("pedido de painel", False), "ST2": ("painel em andamento", False),
    "ST3": ("painel em andamento", False), "ST13": ("encerrada (painel caducou)", True),
    "ST15": ("relatório do painel divulgado", False), "ST4": ("em apelação", False),
    "ST16": ("relatório da apelação divulgado", False), "ST5": ("encerrada (relatório adotado)", True),
    "ST6": ("relatório adotado; medida deve ser ajustada", False), "ST17": ("prazo para ajustar a medida", False),
    "ST18": ("arbitragem do prazo", False), "ST19": ("prazo definido por arbitragem", False),
    "ST0": ("ajuste notificado pelo demandado", True), "ST7": ("encerrada (acordo sobre o ajuste)", True),
    "ST20": ("cumprimento em discussão", False), "ST21": ("cumprimento em discussão", False),
    "ST22": ("cumprimento em discussão", False), "ST33": ("encerrada (painel de cumprimento caducou)", True),
    "ST23": ("cumprimento em discussão", False), "ST24": ("cumprimento em discussão", False),
    "ST25": ("cumprimento em discussão", False), "ST8": ("cumprimento em discussão", False),
    "ST9": ("encerrada (cumprimento confirmado)", True), "ST10": ("descumprimento confirmado", False),
    "ST11": ("retaliação pedida", False), "ST26": ("retaliação em arbitragem", False),
    "ST34": ("encerrada (pedido de retaliação retirado)", True), "ST27": ("retaliação em arbitragem", False),
    "ST28": ("retaliação decidida por arbitragem", False), "ST12": ("retaliação autorizada", False),
    "ST29": ("arbitragem", False), "ST30": ("arbitragem decidida", False),
    "ST14": ("encerrada (retirada ou acordo)", True), "ST31": ("encerrada (acordo)", True),
}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def ler_casos(js: str) -> List[dict]:
    """Os objetos `ds_array[n] = {campo: "valor", ...};` do arquivo da OMC, com os campos já limpos."""
    out = []
    for bloco in re.findall(r"ds_array\[\d+\]\s*=\s*\{(.*?)\};", js, re.S):
        c = {k: html.unescape(v) for k, v in re.findall(r'(\w+):\s*"([^"]*)"', bloco)}
        if not re.fullmatch(r"DS\d+", c.get("code", "")):
            continue
        # situação: "ST5#1997_03_20" ou várias separadas por "|" (a última é a atual)
        st = (c.get("status") or "").split("|")[-1].split("#")
        sit, fim = SITUACAO.get(st[0], (st[0] or "sem informação", False))
        out.append({"ds": c["code"], "titulo": c.get("title", "").strip(),
                    "reclamantes": [x for x in c.get("origin", "").split("#") if x],
                    "demandados": [x for x in c.get("destination", "").split("#") if x],
                    "inicio": c.get("start_date", "").replace("/", "-"),
                    "situacao": sit, "encerrada": fim, "situacao_data": st[1].replace("_", "-") if len(st) > 1 else "",
                    "url": LINK.format(ds=c["code"].lower())})
    return out


def codigo_omc(iso3: str) -> str:
    return "EEC" if iso3 in UE else iso3


def _ver(c: dict, eu: str) -> dict:
    lado = "reclamante" if eu in c["reclamantes"] else "demandado"
    outros = c["demandados"] if lado == "reclamante" else c["reclamantes"]
    return {**c, "lado": lado, "contra": outros}


def por_pais(casos: List[dict], iso3: List[str], desde_ano: Optional[int] = None) -> Dict[str, dict]:
    """Para cada país: disputas com o Brasil (todas, desde 1995) e disputas com o resto do mundo (dos últimos anos)."""
    desde_ano = desde_ano or date.today().year - 5
    out = {}
    for iso in iso3:
        eu = codigo_omc(iso)
        meus = [c for c in casos if eu in c["reclamantes"] or eu in c["demandados"]]
        if iso == "BRA":
            com_brasil = []
        else:
            com_brasil = [c for c in meus if (eu in c["reclamantes"] and "BRA" in c["demandados"])
                          or (eu in c["demandados"] and "BRA" in c["reclamantes"])]
        # as disputas contra/do Brasil já estão em com_brasil; aqui ficam as com o resto do mundo
        # (inclusive aquelas em que o Brasil está do mesmo lado, como co-reclamante)
        recentes = [c for c in meus if c["inicio"][:4].isdigit() and int(c["inicio"][:4]) >= desde_ano
                    and c not in com_brasil]
        contra: Dict[str, int] = {}
        for c in recentes:
            for o in _ver(c, eu)["contra"]:
                if o == eu:
                    continue
                contra[o] = contra.get(o, 0) + 1
        ordem = lambda l: sorted(l, key=lambda c: c["inicio"], reverse=True)
        out[iso] = {
            "via_ue": eu == "EEC",
            "total": len(meus),
            "com_brasil": [_ver(c, eu) for c in ordem(com_brasil)],
            "recentes_desde": desde_ano,
            "recentes": [_ver(c, eu) for c in ordem(recentes)][:8],
            "recentes_total": len(recentes),
            "contrapartes": dict(sorted(contra.items(), key=lambda kv: -kv[1])),
        }
    return out


def disputas(iso3: List[str], js: Optional[str] = None) -> Dict[str, dict]:
    return por_pais(ler_casos(js if js is not None else _get(URL_CASOS)), iso3)
