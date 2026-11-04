"""Votos na Assembleia Geral da ONU: o quanto cada país vota igual ao Brasil (D42).

Fonte: Voeten, Strezhnev e Bailey, "United Nations General Assembly Voting Data" (Harvard Dataverse, doi:10.7910/DVN/LEJUQZ,
licença CC0). O índice de concordância é o de Lijphart (1963): 1 quando os dois votam igual, 0,5 quando um se abstém e o outro não,
0 quando votam em lados opostos; a média é sobre as votações nominais do ano em que os dois votaram.

Isto é uma medida de alinhamento diplomático, não um juízo de "relação boa ou ruim". Os próprios autores avisam que o índice
muda com a pauta do ano (ex.: muitas votações sobre o Oriente Médio), por isso o painel mostra também a média de 5 anos.
"""
import csv
import json
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from .. import config

DATASET = "doi:10.7910/DVN/LEJUQZ"
API = "https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=" + DATASET
ARQUIVO = "https://dataverse.harvard.edu/api/access/datafile/{id}"
BRASIL_COW = "140"  # código Correlates of War do Brasil


def _abrir(url: str, timeout: int = 600):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT}), timeout=timeout)


def arquivos(meta: dict) -> Dict[str, dict]:
    """Escolhe, na versão mais recente do conjunto, a tabela de concordância e uma de pontos ideais (que traz COW → ISO3)."""
    v = meta["data"]["latestVersion"]
    fs = [f["dataFile"] for f in v["files"]]
    concord = [f for f in fs if f.get("filename") == "AgreementScores.csv"]
    ideal = sorted((f for f in fs if re.match(r"Idealpointestimates.*\.csv$", f.get("filename", ""), re.I)), key=lambda f: -f["id"])
    if not concord or not ideal:
        raise ValueError("o conjunto mudou de formato: não achei AgreementScores.csv e Idealpointestimates*.csv")
    return {"concordancia": concord[0], "ideal": ideal[0], "versao": v.get("versionNumber"), "publicado": v.get("releaseTime", "")[:10]}


def _baixar(f: dict, pasta: Path) -> Path:
    destino = pasta / f"{f['id']}_{f['filename']}"
    if not destino.exists():  # cada id do Dataverse é um arquivo imutável: dá para guardar
        pasta.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix(".parcial")
        with _abrir(ARQUIVO.format(id=f["id"])) as r, open(tmp, "wb") as out:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                out.write(b)
        tmp.rename(destino)
    return destino


def cow_para_iso3(caminho: Path) -> Dict[str, str]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return {r["ccode"]: r["iso3c"] for r in csv.DictReader(f) if r.get("iso3c") and r["iso3c"] != "NA"}


def concordancias(caminho: Path, cow_iso3: Dict[str, str]) -> Dict[str, Dict[int, float]]:
    """{iso3: {ano: concordância com o Brasil}} (a tabela tem os dois sentidos de cada par; basta o lado do Brasil)."""
    out: Dict[str, Dict[int, float]] = {}
    with open(caminho, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["ccode1"] != BRASIL_COW or r["agree"] in ("", "NA"):
                continue
            iso = cow_iso3.get(r["ccode2"])
            if iso:
                out.setdefault(iso, {})[int(r["year"])] = float(r["agree"])
    return out


def resumir(conc: Dict[str, Dict[int, float]], iso3: List[str], anos_media: int = 5) -> dict:
    """Para cada país: concordância no último ano, média dos últimos anos e posição entre todos os países naquele ano."""
    ano = max(a for v in conc.values() for a in v)
    no_ano = sorted(((v[ano], k) for k, v in conc.items() if ano in v), reverse=True)
    posicao = {k: i + 1 for i, (_, k) in enumerate(no_ano)}
    paises = {}
    for k in iso3:
        v = conc.get(k, {})
        if ano not in v:
            continue
        janela = [v[a] for a in range(ano - anos_media + 1, ano + 1) if a in v]
        paises[k] = {"concordancia": round(v[ano], 4), "media": round(sum(janela) / len(janela), 4),
                     "anos_media": f"{ano - anos_media + 1}–{ano}", "posicao": posicao[k], "de": len(no_ano)}
    return {"ano": ano, "paises": paises, "mediana": round(no_ano[len(no_ano) // 2][0], 4)}


def alinhamento(iso3: List[str], pasta: Path, meta: Optional[dict] = None) -> dict:
    if meta is None:
        with _abrir(API, 60) as r:
            meta = json.load(r)
    a = arquivos(meta)
    conc = concordancias(_baixar(a["concordancia"], pasta), cow_para_iso3(_baixar(a["ideal"], pasta)))
    return {**resumir(conc, iso3), "versao_dados": a["versao"], "publicado": a["publicado"]}
