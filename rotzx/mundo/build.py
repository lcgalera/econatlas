"""Monta os dados do globo (prototipos/globo/dados/): mundo.json (comércio + economia) e noticias.json (manchetes).

Tudo o que aparece no globo sai daqui, com fonte e data de coleta. Os resumos "o que os dados mostram" são frases geradas
a partir dos números do Comex Stat: descrevem, não interpretam (a interpretação, quando existir, vem marcada à parte).
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .. import config
from . import bancomundial, comex, conflitos, gdelt, omc, onu
from .paises import MENCOES, PAISES, citados

SAIDA = config.ROOT / "prototipos" / "globo" / "dados"
BRUTOS = config.DATA_DIR / "fontes" / "mundo"
FONTES = {
    "comex": {"nome": "Comex Stat (MDIC)", "url": "https://comexstat.mdic.gov.br", "nota": "valores FOB em US$, ano completo"},
    "bancomundial": {"nome": "Banco Mundial (World Development Indicators)", "url": "https://data.worldbank.org", "licenca": "CC BY 4.0"},
    "gdelt": {"nome": "The GDELT Project", "url": "https://www.gdeltproject.org",
              "nota": "manchetes em português; título, veículo e link para a matéria original; categorias por palavras-chave"},
    "onu": {"nome": "Votos na Assembleia Geral da ONU (Voeten, Strezhnev e Bailey, Harvard Dataverse)",
            "url": "https://doi.org/10.7910/DVN/LEJUQZ", "licenca": "CC0",
            "nota": "índice de concordância de Lijphart: 1 = votos iguais, 0,5 = um se absteve, 0 = lados opostos"},
    "omc": {"nome": "Disputas na OMC (lista oficial do site da OMC)",
            "url": "https://www.wto.org/english/tratop_e/dispu_e/dispu_by_country_e.htm",
            "nota": "número, título oficial (em inglês), partes, data e situação de cada disputa"},
    "ucdp": {"nome": "UCDP/PRIO Armed Conflict Dataset (Uppsala Conflict Data Program)", "url": "https://ucdp.uu.se/downloads/",
             "licenca": "CC BY 4.0",
             "nota": "conflitos armados com um governo de um dos lados e 25 ou mais mortes em combate no ano"},
    "noticias": {"nome": "Feeds RSS de veículos em português (g1, Folha, BBC News Brasil, DW, Agência Brasil, RFI) e GDELT",
                 "url": "https://www.gdeltproject.org",
                 "nota": "só título, veículo, data e link para a matéria original; categorias por palavras-chave no título"},
}
CONSULTA_MUNDO = ('(guerra OR tarifa OR "mercados" OR petróleo OR cúpula OR eleição OR sanções OR "comércio mundial") '
                  'sourcelang:portuguese')


def _gravar(saida: Path, nome: str, dados: dict) -> None:
    """nome.json (para quem quiser os dados) e nome.js (window.MUNDO / window.NOTICIAS), que o globo carrega por <script>:
    assim a página funciona também aberta como arquivo local, onde o navegador bloqueia fetch()."""
    txt = json.dumps(dados, ensure_ascii=False, indent=1)
    (saida / f"{nome}.json").write_text(txt, encoding="utf-8")
    (saida / f"{nome}.js").write_text(f"window.{nome.upper()} = {txt};\n", encoding="utf-8")


def _bi(v: float) -> str:
    return f"US$ {v / 1e9:,.1f} bi".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%".replace(".", ",")


def _curto(produto: str, limite: int = 70) -> str:
    """Nome oficial do grupo SH4, cortado numa palavra inteira (o nome completo fica na tabela).

    Não se usa só o começo do nome: "Barcos-faróis, …, plataformas…" (SH4 8905) viraria "barcos-faróis" e enganaria.
    """
    p = produto.strip().rstrip(".")
    if len(p) <= limite:
        return p
    return p[:limite].rsplit(" ", 1)[0].rstrip(",;") + "…"


_DE = {"o": "do", "a": "da", "os": "dos", "as": "das"}
_COM = {"o": "com o", "a": "com a", "os": "com os", "as": "com as"}


def resumo(nome: str, c: dict, ano: str, artigo: str = "") -> str:
    """Frases só com fatos do Comex Stat: posição, valores, principais produtos e saldo."""
    o = (artigo + " " if artigo else "")
    de = (_DE.get(artigo, "de") + " ") if artigo else "de "
    com = (_COM.get(artigo, "com") + " ") if artigo else "com "
    # Os produtos ficam fora da frase: os nomes oficiais dos grupos SH4 são longos demais, e abreviá-los pode enganar
    # (ex.: "Barcos-faróis, …, plataformas…"). Eles aparecem na tabela do painel, com o nome completo.
    partes = []
    if c.get("exportacao"):
        e = c["exportacao"]
        partes.append(f"Em {ano}, {o}{nome} {'foram' if artigo in ('os', 'as') else 'foi'} o {e['posicao']}º destino das "
                      f"exportações brasileiras: {_bi(e['fob'])}, {_pct(e['participacao'])} do total.")
    if c.get("importacao"):
        i = c["importacao"]
        partes.append(f"O Brasil importou {_bi(i['fob'])} {de}{nome} ({i['posicao']}º fornecedor, {_pct(i['participacao'])} do total).")
    if c.get("saldo") is not None:
        s = c["saldo"]
        partes.append(f"{'Superávit' if s >= 0 else 'Déficit'} brasileiro de {_bi(abs(s))} no comércio {com}{nome}.")
    return " ".join(partes)


def _posicoes(valores: Dict[str, float]) -> Dict[str, int]:
    return {k: i + 1 for i, (k, _) in enumerate(sorted(valores.items(), key=lambda kv: -kv[1]))}


def montar(ano: Optional[str] = None, saida: Path = SAIDA, com_noticias: bool = True, log=print) -> Dict:
    ano = ano or str(datetime.now().year - 1)  # último ano completo
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    saida.mkdir(parents=True, exist_ok=True)

    log(f"Comex Stat {ano}: totais por país")
    exp = comex.por_pais(ano, "exportacao", BRUTOS / "comex")
    imp = comex.por_pais(ano, "importacao", BRUTOS / "comex")
    tot_e, tot_i = sum(exp.values()), sum(imp.values())
    pos_e, pos_i = _posicoes(exp), _posicoes(imp)
    # nomes do Comex Stat para os países do protótipo (ex.: "Países Baixos (Holanda)")
    por_nome = {"Países Baixos": "Países Baixos (Holanda)"}

    paises_out = {}
    for p in PAISES:
        if p["iso3"] == "BRA":
            continue
        n = por_nome.get(p["nome"], p["nome"])
        c = {}
        if n in exp:
            c["exportacao"] = {"fob": exp[n], "participacao": exp[n] / tot_e, "posicao": pos_e[n]}
        if n in imp:
            c["importacao"] = {"fob": imp[n], "participacao": imp[n] / tot_i, "posicao": pos_i[n]}
        if c:
            c["saldo"] = c.get("exportacao", {}).get("fob", 0) - c.get("importacao", {}).get("fob", 0)
        log(f"  produtos: {p['nome']}")
        c["produtos_exportados"] = comex.produtos(ano, "exportacao", p["comex"], 5, BRUTOS / "comex")
        c["produtos_importados"] = comex.produtos(ano, "importacao", p["comex"], 5, BRUTOS / "comex")
        paises_out[p["iso_num"]] = {"nome": p["nome"], "artigo": p.get("artigo", ""), "iso3": p["iso3"], "comercio": c,
                                    "resumo": resumo(p["nome"], c, ano, p.get("artigo", ""))}

    log("Banco Mundial: indicadores")
    wb = bancomundial.indicadores([p["iso3"] for p in PAISES])
    for p in PAISES:
        alvo = paises_out.setdefault(p["iso_num"], {"nome": p["nome"], "iso3": p["iso3"]})
        alvo["economia"] = [{"id": k, **bancomundial.INDICADORES[k], **v} for k, v in wb.get(p["iso3"], {}).items()]

    ranking = sorted(({"pais": n, "exportacao": exp.get(n, 0), "importacao": imp.get(n, 0)} for n in set(exp) | set(imp)),
                     key=lambda r: -(r["exportacao"] + r["importacao"]))[:15]
    paises_out["076"].update({"comercio_total": {"exportacao": tot_e, "importacao": tot_i, "saldo": tot_e - tot_i},
                              "maiores_parceiros": ranking})
    mundo = {"gerado_em": agora, "ano_comercio": ano, "fontes": FONTES, "paises": paises_out}
    _relacoes(mundo, log)
    _gravar(saida, "mundo", mundo)

    if com_noticias:
        noticias(saida, log)
    return mundo


def _relacoes(m: dict, log=print) -> None:
    """Votos na ONU, disputas na OMC (D42) e conflitos armados (D43) por país. Falha de uma fonte fica em m["falhas"]
    e não derruba as outras."""
    iso3 = [p["iso3"] for p in PAISES]
    por_iso3 = {p["iso3"]: p["iso_num"] for p in PAISES}
    falhas = m.setdefault("falhas", {})
    for chave, coletar in (("onu", lambda: onu.alinhamento(iso3, BRUTOS / "onu")), ("omc", lambda: omc.disputas(iso3)),
                           ("conflitos", lambda: conflitos.coletar(iso3, BRUTOS / "ucdp"))):
        log(f"{chave.upper()}: coletando")
        try:
            r = coletar()
        except (OSError, ValueError, KeyError) as e:
            falhas[chave] = f"{type(e).__name__}: {e}"[:200]
            log(f"  falhou: {falhas[chave]}")
            continue
        falhas.pop(chave, None)
        dados = r if chave == "omc" else r["paises"]
        for k, v in dados.items():
            if k in por_iso3:
                m["paises"].setdefault(por_iso3[k], {}).setdefault("relacoes", {})[chave] = v["conflitos"] if chave == "conflitos" else v
        if chave == "onu":
            m["onu"] = {k: r[k] for k in ("ano", "mediana", "versao_dados", "publicado")}
        if chave == "conflitos":
            m["conflitos"] = {k: r[k] for k in ("ultimo_ano", "desde", "versao", "mundo")}
    m["fontes"] = {**m.get("fontes", {}), "onu": FONTES["onu"], "omc": FONTES["omc"], "ucdp": FONTES["ucdp"]}
    m["relacoes_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")


def relacoes(saida: Path = SAIDA, log=print) -> dict:
    """Atualiza só votos na ONU e disputas na OMC no mundo.json já coletado (sem refazer o Comex Stat)."""
    f = saida / "mundo.json"
    m = json.loads(f.read_text(encoding="utf-8"))
    _relacoes(m, log)
    _gravar(saida, "mundo", m)
    return m


def refazer_resumos(saida: Path = SAIDA) -> None:
    """Regera as frases a partir do mundo.json já coletado (sem chamar o Comex Stat de novo)."""
    f = saida / "mundo.json"
    m = json.loads(f.read_text(encoding="utf-8"))
    artigos = {p["iso_num"]: p.get("artigo", "") for p in PAISES}
    for iso, d in m["paises"].items():
        if "comercio" in d:
            d["artigo"] = artigos.get(iso, "")
            d["resumo"] = resumo(d["nome"], d["comercio"], m["ano_comercio"], d["artigo"])
    _gravar(saida, "mundo", m)


def noticias(saida: Path = SAIDA, log=print, dias: int = 7, por_lote: int = 7, usar_gdelt: bool = True) -> Dict:
    """Manchetes por país e do mundo, acumulando com a coleta anterior (últimos `dias`).

    Fonte principal: feeds RSS de veículos em português (rss.py). Complemento: GDELT em lotes de países.
    Falha de uma fonte fica em "falhas" e nunca vira "sem notícias": as manchetes anteriores são mantidas.
    """
    from datetime import timedelta
    from . import rss
    agora = datetime.now(timezone.utc)
    desde = (agora - timedelta(days=dias)).strftime("%Y%m%d")
    f = saida / "noticias.json"
    antes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    out = {"gerado_em": agora.isoformat(timespec="seconds"), "fonte": FONTES["noticias"], "dias": dias,
           "paises": {}, "falhas": {}, "diagnostico": {}}

    itens, falhas_rss = rss.coletar()
    out["falhas"].update({f"rss:{k}": v for k, v in falhas_rss.items()})
    out["diagnostico"]["rss_itens"] = len(itens)
    log(f"  RSS: {len(itens)} itens de {len(rss.FEEDS) - len(falhas_rss)} feeds ({len(falhas_rss)} falharam)")
    novas = {p["iso_num"]: [m for m in itens if gdelt.menciona(m["titulo"], p["termos"])] for p in PAISES}

    if usar_gdelt:
        for i in range(0, len(PAISES), por_lote):
            grupo = PAISES[i:i + por_lote]
            try:
                r = gdelt.lote(grupo, dias=dias)
                out["diagnostico"][f"gdelt_lote_{i // por_lote + 1}"] = sum(map(len, r.values()))
                for iso, l in r.items():
                    novas[iso] += l
            except OSError as e:
                out["falhas"][f"gdelt_lote_{i // por_lote + 1}"] = f"{type(e).__name__}: {e}"[:200]

    for p in PAISES:
        out["paises"][p["iso_num"]] = gdelt.juntar(antes.get("paises", {}).get(p["iso_num"], []), novas[p["iso_num"]], desde)
        log(f"  {p['nome']}: {len(out['paises'][p['iso_num']])}")
    globais = [m for m in itens if m["categorias"] and ("afeta_o_mundo" in m["categorias"] or "geopolitica" in m["categorias"])]
    out["mundo"] = gdelt.juntar(antes.get("mundo", []), globais, (agora - timedelta(days=2)).strftime("%Y%m%d"), maximo=100)
    _recategorizar(out)
    _gravar(saida, "noticias", out)
    return out


def _recategorizar(n: dict) -> None:
    """A regra de categorias (e a de países citados, D44) pode mudar: aplica a atual a todas as manchetes guardadas."""
    for lista in list(n.get("paises", {}).values()) + [n.get("mundo", [])]:
        for m in lista:
            m["categorias"] = gdelt.categorias(m.get("titulo", ""))
            m["paises"] = citados(m.get("titulo", ""))
    n["nomes"] = {p["iso_num"]: p["nome"] for p in PAISES + MENCOES}  # para o mapa nomear quem a manchete cita
    n["mundo"] = [m for m in n.get("mundo", []) if {"afeta_o_mundo", "geopolitica"} & set(m["categorias"])]


def recategorizar(saida: Path = SAIDA) -> None:
    f = saida / "noticias.json"
    n = json.loads(f.read_text(encoding="utf-8"))
    _recategorizar(n)
    _gravar(saida, "noticias", n)
