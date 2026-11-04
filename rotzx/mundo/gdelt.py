"""GDELT (DOC 2.0): manchetes recentes em português. Só título, veículo, data e link: o texto fica no site de cada veículo.

A busca do GDELT procura o termo no texto inteiro da matéria; para ficar só com o que FALA do país, a manchete precisa citar
um dos termos do país (rotzx/mundo/paises.py). As categorias são atribuídas por palavras-chave no título (regra documentada,
automática e imperfeita): economia, política, geopolítica e "afeta o mundo". Uma manchete pode ter mais de uma categoria.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from .. import config

URL = "https://api.gdeltproject.org/api/v2/doc/doc?"
INTERVALO = 8.0  # o GDELT pede no máximo uma consulta a cada 5 segundos; com folga, ele derruba menos conexões
_ultima = [0.0]

CATEGORIAS = {
    "economia": r"econom|pib|infla[çc]|juros|banco central|export|import|com[ée]rcio|tarifa|bolsa|a[çc][õo]es|d[óo]lar|moeda|"
                r"petr[óo]leo|soja|min[ée]rio|investiment|empresa|mercado|pre[çc]o|ind[úu]stria|emprego|d[íi]vida|fiscal|imposto|agroneg",
    "politica": r"elei[çc]|presidente|governo|congresso|parlamento|senado|partido|ministr|oposi[çc]|vota[çc]|\blei\b|reforma|"
                r"justi[çc]a|tribunal|protesto|premi[êe]",
    "geopolitica": r"guerra|conflito|militar|ex[ée]rcito|otan|san[çc]|diplomac|embaixad|fronteira|ataque|m[íi]ssil|tratado|"
                   r"invas|tropas|nuclear|cessar-fogo|territ[óo]ri|chanceler",
    "afeta_o_mundo": r"mundial|global|\bmundo\b|mercados|\bonu\b|clima|pandemia|recess|\bg20\b|\bg7\b|brics|c[úu]pula|cadeias? de suprimento",
}
_CAT = {k: re.compile(v, re.I) for k, v in CATEGORIAS.items()}


def _get(params: dict, tentativas: int = 2) -> dict:
    url = URL + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    for t in range(tentativas):
        falta = INTERVALO - (time.time() - _ultima[0])
        if falta > 0:
            time.sleep(falta)
        _ultima[0] = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                corpo = r.read().decode("utf-8", "replace")
            return json.loads(corpo) if corpo.strip().startswith("{") else {"articles": []}
        except OSError:
            if t == tentativas - 1:
                raise
            time.sleep(INTERVALO * 2 * (t + 1))
    return {"articles": []}


def categorias(titulo: str) -> List[str]:
    return [k for k, rx in _CAT.items() if rx.search(titulo or "")]


def menciona(titulo: str, termos: List[str]) -> bool:
    """O título cita o país? Comparação em minúsculas, COM acento e por palavra inteira."""
    t = (titulo or "").lower()
    return any(re.search(r"(?<![\wà-ú])" + re.escape(x) + r"(?![\wà-ú])", t) for x in termos)


def _limpa(a: dict) -> dict:
    return {"titulo": re.sub(r"\s+", " ", a.get("title", "")).strip(), "url": a.get("url"), "veiculo": a.get("domain"),
            "data": (a.get("seendate") or "")[:8], "pais_do_veiculo": a.get("sourcecountry"), "categorias": categorias(a.get("title", ""))}


def manchetes(termos: List[str], dias: int = 7, maximo: int = 75, exigir_no_titulo: bool = True,
              consulta: Optional[str] = None) -> List[dict]:
    """Manchetes em português dos últimos `dias`, sem repetir título, as mais recentes primeiro."""
    q = consulta or "(" + " OR ".join(f'"{t}"' if " " in t else t for t in termos[:4]) + ") sourcelang:portuguese"
    dados = _get({"query": q, "mode": "artlist", "maxrecords": maximo, "timespan": f"{dias}d", "sort": "datedesc", "format": "json"})
    vistos, out = set(), []
    for a in dados.get("articles", []):
        m = _limpa(a)
        chave = re.sub(r"\W+", " ", m["titulo"].lower()).strip()
        if not m["titulo"] or chave in vistos or (exigir_no_titulo and not menciona(m["titulo"], termos)):
            continue
        vistos.add(chave)
        out.append(m)
    return out
