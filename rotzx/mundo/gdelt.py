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
INTERVALO = 20.0  # o GDELT pede no máximo uma consulta a cada 5 s; de IPs compartilhados (Actions) ele limita bem antes
MAX_REGISTROS = 250  # máximo do modo artlist
_ultima = [0.0]

CATEGORIAS = {  # cada termo começa no início de uma palavra (\b); os curtos também terminam nela
    "economia": r"econom|pib\b|infla[çc]|juros\b|banco central|export|import|com[ée]rcio|tarifa|bolsas?\b|a[çc][õo]es\b|"
                r"d[óo]lar|moedas?\b|petr[óo]leo|soja\b|min[ée]rio|investiment|empresa|mercados?\b|pre[çc]os?\b|ind[úu]stria|"
                r"empregos?\b|desemprego|d[íi]vidas?\b|fiscal\b|impostos?\b|agroneg|custo de vida",
    "politica": r"elei[çc]|presidente|governo|congresso|parlamento|senado|partido|ministr|oposi[çc]|vota[çc]|lei\b|reforma|"
                r"justi[çc]a|tribunal|protesto|premi[êe]",
    "geopolitica": r"guerra|conflito|militar|ex[ée]rcito|otan\b|san[çc][õo]|diplomac|embaixad|fronteira|ataque|m[íi]sseis\b|m[íi]ssil\b|"
                   r"tratado|invas|tropas|nuclear|cessar-fogo|territ[óo]ri|chanceler|negocia[çc][õo]es de paz|acordo de paz",
    "afeta_o_mundo": r"mundial|global|mundo\b|mercados\b|onu\b|clima\b|pandemia|recess|g20\b|g7\b|brics\b|c[úu]pula|"
                     r"cadeias? de suprimento",
}
_CAT = {k: re.compile(r"\b(?:" + v + ")", re.I) for k, v in CATEGORIAS.items()}


class LimiteGDELT(OSError):
    """O GDELT respondeu com texto em vez de JSON (ex.: "Please limit requests…"): é falha, não ausência de notícias."""


def _get(params: dict, tentativas: int = 3) -> dict:
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
            if not corpo.strip().startswith("{"):
                raise LimiteGDELT(corpo.strip()[:120] or "resposta vazia")
            return json.loads(corpo)
        except OSError:
            if t == tentativas - 1:
                raise
            time.sleep(INTERVALO * 2 * (t + 1))
    raise LimiteGDELT("sem resposta")


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


def _chave(titulo: str) -> str:
    return re.sub(r"\W+", " ", (titulo or "").lower()).strip()


def lote(paises: List[dict], dias: int = 1) -> Dict[str, List[dict]]:
    """Uma consulta para vários países (o nome de cada um, em OR); cada manchete vai para os países que o TÍTULO cita.

    Junta numa só o que seriam várias consultas por país: o GDELT limita o número de consultas, não o tamanho delas.
    """
    nomes = " OR ".join(f'"{p["nome"]}"' if " " in p["nome"] else p["nome"] for p in paises)
    dados = _get({"query": f"({nomes}) sourcelang:portuguese", "mode": "artlist", "maxrecords": MAX_REGISTROS,
                  "timespan": f"{dias}d", "sort": "datedesc", "format": "json"})
    out: Dict[str, List[dict]] = {p["iso_num"]: [] for p in paises}
    vistos: Dict[str, set] = {p["iso_num"]: set() for p in paises}
    for a in dados.get("articles", []):
        m = _limpa(a)
        if not m["titulo"]:
            continue
        for p in paises:
            if menciona(m["titulo"], p["termos"]) and _chave(m["titulo"]) not in vistos[p["iso_num"]]:
                vistos[p["iso_num"]].add(_chave(m["titulo"]))
                out[p["iso_num"]].append(m)
    return out


def juntar(antigas: List[dict], novas: List[dict], desde: str, maximo: int = 30) -> List[dict]:
    """Acumula manchetes entre coletas: sem repetir título, só as de `desde` (AAAAMMDD) em diante, as mais recentes primeiro."""
    vistos, out = set(), []
    for m in sorted(novas + antigas, key=lambda x: x.get("data", ""), reverse=True):
        k = _chave(m.get("titulo"))
        if k and k not in vistos and m.get("data", "") >= desde:
            vistos.add(k)
            out.append(m)
    return out[:maximo]
