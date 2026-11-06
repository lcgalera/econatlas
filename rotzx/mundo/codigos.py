"""Tabela de países do globo (D46): liga os códigos de cada fonte ao país do mapa.

Uma linha por país em `catalog/paises_mundo.csv`:
- `iso_num` (ISO 3166 numérico, o id do mapa world-atlas), `iso3`, `nome` (português de uso comum);
- `comex`: códigos do Comex Stat (um país pode ter mais de um, ex.: "Saint Kitts e Nevis" e "São Cristóvão e Névis");
- `cow`: códigos Correlates of War (votos na ONU); `gw`: códigos Gleditsch & Ward (UCDP);
- `no_mapa`: 1 se o país aparece no mapa (world-atlas 1:110m), 0 se só na lista.

A tabela é gerada uma vez (`rotzx mundo-codigos`) e fica versionada; o globo e a coleta histórica só a leem.
Fontes: ISO 3166 e nomes oficiais em português do pacote pycountry (dados do iso-codes do Debian); nomes e códigos do
Comex Stat (`/tables/countries`); COW + ISO3 do arquivo de pontos ideais da ONU (Harvard Dataverse); GW conferido contra os nomes
"Government of …" da própria UCDP. O que não casa sozinho está nas exceções abaixo, escritas à mão e testadas.
"""
import csv
import gettext
import json
import re
import unicodedata
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from .. import config

ARQUIVO = config.ROOT / "catalog" / "paises_mundo.csv"
COMEX_PAISES = "https://api-comexstat.mdic.gov.br/tables/countries"
ATLAS = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json"

# Comex Stat → ISO3 que o casamento por nome não acha (ou acha errado: o "Congo" do Comex é a República do Congo, não a RDC)
COMEX_ISO3 = {
    "Congo": "COG", "Congo, República Democrática": "COD", "Azerbaijão": "AZE", "Belarus": "BLR", "Burkina Faso": "BFA",
    "Coveite (Kuweit)": "KWT", "Macedônia": "MKD", "Malavi": "MWI", "Mianmar": "MMR", "Papua Nova Guiné": "PNG", "Rússia": "RUS",
    "Saint Kitts e Nevis": "KNA", "Salomão, Ilhas": "SLB", "San Marino": "SMR", "Seicheles": "SYC", "Singapura": "SGP", "Síria": "SYR",
    "Tcheca, República": "CZE", "Trinidad e Tobago": "TTO", "Marshall, Ilhas": "MHL", "Vaticano": "VAT", "Anguilla": "AIA",
    "Bermudas": "BMU", "Cayman, Ilhas": "CYM", "Cook, Ilhas": "COK", "Falkland (Malvinas)": "FLK", "Faroe, Ilhas": "FRO",
    "Canal, Ilhas do (Guernsey)": "GGY", "Canal, Ilhas do (Jersey)": "JEY", "Marianas do Norte, Ilhas": "MNP", "Mayotte": "MYT",
    "Norfolk, Ilha": "NFK", "Sint Maarten": "SXM", "São Martinho, Ilha de (parte francesa)": "MAF", "Svalbard e Jan Mayen": "SJM",
    "Terras Austrais Francesas": "ATF", "Turcas e Caicos, Ilhas": "TCA", "Virgens, Ilhas (Americanas)": "VIR",
    "Virgens, Ilhas (Britânicas)": "VGB", "Wallis e Futuna, Ilhas": "WLF", "Bonaire, Saint Eustatius e Saba": "BES",
    "Aland, Ilhas": "ALA", "Bouvet, Ilha": "BVT", "Christmas (Navidad), Ilha": "CXR", "Cocos (Keeling), Ilhas": "CCK",
    "Geórgia do Sul e Sandwich do Sul, Ilhas": "SGS", "Heard e ilhas mcdonald, Ilha": "HMD", "Antártica": "ATA",
    # partes de um país que o Comex registra com código próprio: somadas ao país
    "Dubai": "ARE", "Inglaterra": "GBR",
}
# Códigos do Comex que não são um país de hoje (agregados, territórios extintos, países que deixaram de existir): ficam fora
COMEX_FORA = {"A Designar", "Bancos Centrais", "Internação na Zona Franca de Manaus", "Não Declarados", "Não Definido",
              "Organizações Internacionais", "Provisão de Navios e Aeronaves", "Sem informação", "Alemanha Oriental",
              "Antilhas Holandesas", "Iugoslávia", "Iêmen Democrático", "Tchecoslováquia",
              "União das Repúblicas Socialistas Soviéticas", "Alboran-Perejil, Ilhas", "Canárias, Ilhas", "Madeira, Ilha da",
              "Johnston, Ilhas", "Lebuan, Ilhas", "Midway, Ilhas", "Wake, Ilha", "Pacífico, Ilhas do (Administração dos EUA)",
              "Pacífico, Ilhas do (EUA)", "Pacífico, Ilhas do (Território Fideicomisso EUA)", "Papua, Território de",
              "Território Antártico Britânico", "Território da Alta Comissão do Pacífico Ocidental", "Zona do Canal do Panamá"}
# Nome de exibição quando o do Comex não serve (parênteses, ordem invertida, grafia antiga)
NOMES = {"KWT": "Kuwait", "NLD": "Países Baixos", "TWN": "Taiwan", "COG": "República do Congo", "COD": "Rep. Dem. do Congo",
         "CZE": "Tchéquia", "MKD": "Macedônia do Norte", "KNA": "São Cristóvão e Névis", "FLK": "Ilhas Malvinas (Falkland)",
         "GBR": "Reino Unido", "ARE": "Emirados Árabes Unidos", "SWZ": "Essuatíni", "CIV": "Costa do Marfim",
         "PSE": "Palestina", "TLS": "Timor-Leste", "BIH": "Bósnia e Herzegovina",
         "VGB": "Ilhas Virgens Britânicas", "VIR": "Ilhas Virgens Americanas", "HMD": "Ilhas Heard e McDonald"}
# Códigos da UCDP (Gleditsch & Ward) e da ONU (COW) que o arquivo da ONU não liga a um ISO3 de hoje: país atual no mapa
GW_ISO3 = {751: "IND",   # Hyderabad (1948) → território da Índia
           817: "VNM",   # Vietnã do Sul
           678: "YEM", 679: "YEM", 680: "YEM",   # Iêmen do Norte, Iêmen unificado, Iêmen do Sul
           265: "DEU", 255: "DEU", 260: "DEU",   # Alemanhas
           345: "SRB", 347: "XKX"}               # Iugoslávia/Sérvia; Kosovo (sem ISO oficial, fica fora do mapa)


# "tipo": país (Estado soberano) ou território. Regra: quem tem código COW na base de votos da ONU é Estado; os Estados
# abaixo não aparecem nela (observadores na ONU ou sem voto registrado) e são marcados à mão. O resto é território
# (dependências, regiões administrativas especiais, áreas sem governo próprio) — a interface diz "países e territórios".
ESTADOS_SEM_COW = {"PSE", "VAT", "XKX", "SSD"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()).strip()


def _nome_comum(comex_nome: str) -> str:
    """'Salomão, Ilhas' → 'Ilhas Salomão'; tira parênteses ('Países Baixos (Holanda)' → 'Países Baixos')."""
    n = re.sub(r"\s*\(.*?\)", "", comex_nome).strip()
    m = re.match(r"^(.*), (.*)$", n)
    return f"{m.group(2)} {m.group(1)}".strip() if m else n


def _iso_pycountry():
    import pycountry
    pt = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["pt_BR"], fallback=True)
    paises = {c.alpha_3: {"iso_num": c.numeric, "iso3": c.alpha_3, "iso2": c.alpha_2, "nome_oficial": pt.gettext(c.name)}
              for c in pycountry.countries}
    indice = {}
    for c in pycountry.countries:
        for n in {c.name, getattr(c, "common_name", c.name), getattr(c, "official_name", c.name)}:
            t = pt.gettext(n)
            for v in {t, re.sub(r"^(.*), (.*)$", r"\2 \1", t), t.split(",")[0]}:
                indice.setdefault(_norm(v), c.alpha_3)
    return paises, indice


def casar_comex(lista: List[dict], indice: Dict[str, str]) -> Dict[str, Optional[str]]:
    """{nome do Comex: ISO3 ou None (fora)}. Exceções primeiro; depois o nome em português (com e sem parênteses)."""
    out = {}
    for x in lista:
        t = x["text"]
        if t in COMEX_FORA:
            out[t] = None
        elif t in COMEX_ISO3:
            out[t] = COMEX_ISO3[t]
        else:
            out[t] = indice.get(_norm(t)) or indice.get(_norm(re.sub(r"\s*\(.*?\)", "", t)))
    return out


def gerar(comex_lista: List[dict], cow_iso3: Dict[int, str], gw_codigos: List[int], ids_mapa: List[str]) -> List[dict]:
    paises, indice = _iso_pycountry()
    comex = casar_comex(comex_lista, indice)
    faltam = [t for t, a in comex.items() if a is None and t not in COMEX_FORA]
    if faltam:
        raise ValueError(f"países do Comex sem ISO3 (acrescente em COMEX_ISO3 ou COMEX_FORA): {faltam}")
    por_iso = {a: {**p, "nome": "", "comex": [], "cow": [], "gw": []} for a, p in paises.items()}
    for x in comex_lista:
        a = comex[x["text"]]
        if a:
            por_iso[a]["comex"].append(x["id"])
            if not por_iso[a]["nome"] or x["text"] == _nome_comum(x["text"]):
                por_iso[a]["nome"] = _nome_comum(x["text"])
    for c, a in cow_iso3.items():
        a = GW_ISO3.get(c, a)
        if a in por_iso:
            por_iso[a]["cow"].append(c)
    for g in gw_codigos:
        a = GW_ISO3.get(g) or cow_iso3.get(g)
        if a in por_iso:
            por_iso[a]["gw"].append(g)
    no_mapa = set(ids_mapa)
    linhas = []
    for a, p in sorted(por_iso.items(), key=lambda kv: kv[1]["iso_num"]):
        nome = NOMES.get(a) or p["nome"] or p["nome_oficial"]
        linhas.append({"iso_num": p["iso_num"], "iso3": a, "iso2": p["iso2"], "nome": nome, "tipo": "pais" if p["cow"] or a in ESTADOS_SEM_COW else "territorio",
                       "comex": "|".join(sorted(p["comex"])),
                       "cow": "|".join(map(str, sorted(set(p["cow"])))), "gw": "|".join(map(str, sorted(set(p["gw"])))),
                       "no_mapa": int(p["iso_num"] in no_mapa)})
    repetidos = {n for n in [r["nome"] for r in linhas] if [r["nome"] for r in linhas].count(n) > 1}
    if repetidos:
        raise ValueError(f"nomes repetidos na tabela de países (acrescente em NOMES): {sorted(repetidos)}")
    return linhas


def gravar(linhas: List[dict], arquivo: Path = ARQUIVO) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["iso_num", "iso3", "iso2", "nome", "tipo", "comex", "cow", "gw", "no_mapa"])
        w.writeheader()
        w.writerows(linhas)


def carregar(arquivo: Path = ARQUIVO) -> List[dict]:
    with open(arquivo, newline="", encoding="utf-8") as f:
        return [{**r, "comex": [c for c in r["comex"].split("|") if c], "cow": [int(c) for c in r["cow"].split("|") if c],
                 "gw": [int(c) for c in r["gw"].split("|") if c], "no_mapa": r["no_mapa"] == "1"} for r in csv.DictReader(f)]


def _json(url: str):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT}), timeout=60) as r:
        return json.loads(r.read())


def montar(pasta_onu: Path, pasta_ucdp: Path, atlas_arquivo: Optional[Path] = None, log=print) -> List[dict]:
    """Baixa o que falta (Comex, mapa), lê os arquivos já baixados da ONU e da UCDP e grava a tabela.
    `atlas_arquivo`: cópia local do countries-110m.json, se o CDN não estiver ao alcance."""
    from . import conflitos
    comex_lista = _json(COMEX_PAISES)["data"]["list"]
    atlas = json.loads(atlas_arquivo.read_text()) if atlas_arquivo else _json(ATLAS)
    ids_mapa = [g["id"] for g in atlas["objects"]["countries"]["geometries"] if g.get("id")]
    ideal = sorted(pasta_onu.glob("*Idealpoint*.csv"))[-1]
    with open(ideal, newline="", encoding="utf-8") as f:
        cow_iso3 = {int(r["ccode"]): r["iso3c"] for r in csv.DictReader(f) if r["iso3c"] not in ("", "NA")}
    linhas_ucdp = conflitos.ler(sorted(pasta_ucdp.glob("*.zip"))[-1].read_bytes())
    gw = sorted({int(c) for r in linhas_ucdp for k in ("gwno_a", "gwno_b", "gwno_a_2nd", "gwno_b_2nd", "gwno_loc")
                 for c in re.findall(r"\d+", r[k] or "")})
    linhas = gerar(comex_lista, cow_iso3, gw, ids_mapa)
    gravar(linhas)
    log(f"{len(linhas)} países; {sum(r['no_mapa'] for r in linhas)} no mapa; "
        f"{sum(bool(r['comex']) for r in linhas)} com código do Comex")
    return linhas
