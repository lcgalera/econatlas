"""Retrato histórico da relação de cada país com o Brasil (D46): dados do globo de portfólio.

Gera `prototipos/globo/dados/historia.json|js` (window.HISTORIA), com uma entrada por país do mapa (catalog/paises_mundo.csv):
- comércio com o Brasil ano a ano desde 1997 (Comex Stat), e os 5 principais produtos de cada lado em 2000 e no último ano;
- concordância com o Brasil nas votações nominais da Assembleia Geral da ONU, ano a ano desde 1946 (Voeten et al., CC0);
- conflitos armados por ano desde 1946 (UCDP/PRIO, CC BY 4.0): no território do país, como lado principal ou com tropas;
- disputas comerciais com o Brasil na OMC;
- indicadores atuais do Banco Mundial (CC BY 4.0).

Coleta de uma vez (sem atualização recorrente, D45). Séries guardadas como listas alinhadas ao primeiro ano da fonte; ano sem dado = null
(nunca zero). Conflitos de países que não existem mais (Vietnã do Sul, Iêmen do Sul…) aparecem no país de hoje, nas fronteiras atuais.
"""
import csv
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from . import bancomundial, codigos, comex, conflitos, omc, onu, produtos_nomes

ANO_COMEX = 1997
ANO_ONU = 1946
ANO_UCDP = 1946


def _serie(valores: Dict[int, float], inicio: int, fim: int, casas: Optional[int] = None) -> List[Optional[float]]:
    return [(round(valores[a], casas) if casas is not None else valores[a]) if a in valores else None for a in range(inicio, fim + 1)]


# ---------- comércio ----------
ANOS_PRODUTOS = (2000, 2010)   # mais o último ano: recortes com a composição completa por produto (D47)
TOP_PRODUTOS = 10


def comercio(tabela: List[dict], fim: int, pasta: Optional[Path] = None, anos_produtos: Optional[List[int]] = None,
             nomes_comex: Optional[List[dict]] = None, pares_saida: Optional[dict] = None) -> dict:
    """A API devolve o nome do país (noPaispt), não o código: a ponte é a tabela de países do Comex (/tables/countries)."""
    nomes_comex = nomes_comex if nomes_comex is not None else codigos._json(codigos.COMEX_PAISES)["data"]["list"]
    cod_de = {x["text"]: x["id"] for x in nomes_comex}
    iso_de = {c: r["iso_num"] for r in tabela for c in r["comex"]}
    por_codigo = {nome: iso_de[c] for nome, c in cod_de.items() if c in iso_de}
    anos_produtos = sorted(set(anos_produtos or [*ANOS_PRODUTOS, fim]))
    out = {"inicio": ANO_COMEX, "fim": fim, "paises": {}, "brasil": {}, "sh4": {}, "anos_produtos": anos_produtos}
    totais = {}
    for fluxo, k in (("exportacao", "e"), ("importacao", "i")):
        serie = comex.serie(str(ANO_COMEX), str(fim), fluxo, pasta)   # {(nome do país, ano): US$ FOB}
        tot = {}
        for (cod, ano), v in serie.items():
            iso = por_codigo.get(cod)
            tot[ano] = tot.get(ano, 0) + v
            if iso:
                d = out["paises"].setdefault(iso, {"e": {}, "i": {}})
                d[k][ano] = d[k].get(ano, 0) + v
        totais[k] = tot
    for iso, d in out["paises"].items():
        d["e"] = _serie(d["e"], ANO_COMEX, fim)
        d["i"] = _serie(d["i"], ANO_COMEX, fim)
    out["brasil"] = {k: _serie(v, ANO_COMEX, fim) for k, v in totais.items()}
    # Composição por produto: a consulta traz TODOS os pares país × SH4 do ano, então o total bilateral (denominador das
    # participações) e o número de posições são exatos; guardam-se os 10 maiores de cada lado.
    for ano in anos_produtos:
        for fluxo, k in (("exportacao", "e"), ("importacao", "i")):
            pares = comex.produtos_todos(str(ano), fluxo, pasta)    # {nome do país: [(sh4, nome, fob)]}
            por_iso: Dict[str, Dict[str, float]] = {}
            for cod, itens in pares.items():
                iso = por_codigo.get(cod)
                for sh4, nome, fob in itens:
                    out["sh4"][sh4] = nome
                    if iso:
                        d = por_iso.setdefault(iso, {})
                        d[sh4] = d.get(sh4, 0) + fob
            if pares_saida is not None:
                pares_saida[(ano, k)] = por_iso
            for iso, soma in por_iso.items():
                top = sorted(soma.items(), key=lambda kv: -kv[1])[:TOP_PRODUTOS]
                out["paises"].setdefault(iso, {}).setdefault("p", {}).setdefault(str(ano), {})[k] = \
                    {"t": round(sum(soma.values())), "n": len(soma), "top": [[sh4, round(v)] for sh4, v in top]}
    out["curtos"] = {c: produtos_nomes.curto(c, n) for c, n in out["sh4"].items() if c in produtos_nomes.CURTOS or c in produtos_nomes.SEM_DESCRICAO}
    return out


# ---------- produtos (D47): séries anuais por SH4 e distribuição por parceiro nos anos com recorte completo ----------
MIN_PRODUTO = 50e6   # posições que passaram de US$ 50 milhões num ano em algum dos fluxos (o resto fica de fora do explorador)
TOP_PARCEIROS = 12


def produtos(fim: int, pares: dict, nomes: Dict[str, str], pasta: Optional[Path] = None) -> dict:
    """Arquivo do explorador por produto. Séries do Brasil por SH4 (todos os parceiros) desde 1997 e, nos anos de `pares`,
    os maiores parceiros de cada produto com o total do produto no ano (denominador das participações)."""
    serie = {k: comex.produtos_serie(str(ANO_COMEX), str(fim), fluxo, pasta) for fluxo, k in (("exportacao", "e"), ("importacao", "i"))}
    por_sh4: Dict[str, Dict[str, Dict[int, float]]] = {}
    for k, d in serie.items():
        for (sh4, ano), v in d.items():
            por_sh4.setdefault(sh4, {"e": {}, "i": {}})[k][ano] = v
    manter = {c for c, d in por_sh4.items() if max(list(d["e"].values()) + list(d["i"].values()) or [0]) >= MIN_PRODUTO}
    itens = {}
    for c in sorted(manter):
        itens[c] = {"nome": produtos_nomes.curto(c, nomes.get(c, "")), "oficial": nomes.get(c, ""),
                    "e": _serie(por_sh4[c]["e"], ANO_COMEX, fim), "i": _serie(por_sh4[c]["i"], ANO_COMEX, fim), "p": {}}
    for gid, g in produtos_nomes.GRUPOS.items():
        soma = {k: {} for k in ("e", "i")}
        for c in g["sh4"]:
            for k in ("e", "i"):
                for ano, v in por_sh4.get(c, {}).get(k, {}).items():
                    soma[k][ano] = soma[k].get(ano, 0) + v
        itens[gid] = {"nome": g["nome"], "oficial": "Grupo: " + g["regra"], "grupo": g["sh4"],
                      "e": _serie(soma["e"], ANO_COMEX, fim), "i": _serie(soma["i"], ANO_COMEX, fim), "p": {}}
    for (ano, k), por_iso in pares.items():
        por_produto: Dict[str, Dict[str, float]] = {}
        for iso, d in por_iso.items():
            for c, v in d.items():
                alvos = [c] if c in itens else []
                alvos += [gid for gid, g in produtos_nomes.GRUPOS.items() if c in g["sh4"]]
                for a in alvos:
                    por_produto.setdefault(a, {})[iso] = por_produto.setdefault(a, {}).get(iso, 0) + v
        for a, d in por_produto.items():
            top = sorted(d.items(), key=lambda kv: -kv[1])[:TOP_PARCEIROS]
            itens[a]["p"].setdefault(str(ano), {})[k] = {"t": round(sum(d.values())), "n": len(d), "top": [[iso, round(v)] for iso, v in top]}
    return {"inicio": ANO_COMEX, "fim": fim, "anos_parceiros": sorted({a for a, _ in pares}), "min_produto": MIN_PRODUTO, "itens": itens}


# ---------- ONU ----------
def votos(tabela: List[dict], caminho_concordancia: Path) -> dict:
    cow_iso = {str(c): r["iso_num"] for r in tabela for c in r["cow"]}
    conc = onu.concordancias(caminho_concordancia, cow_iso)       # {iso_num: {ano: valor}}
    fim = max(a for v in conc.values() for a in v)
    mediana = {a: statistics.median([v[a] for v in conc.values() if a in v]) for a in range(ANO_ONU, fim + 1)
               if any(a in v for v in conc.values())}
    return {"inicio": ANO_ONU, "fim": fim, "mediana": _serie(mediana, ANO_ONU, fim, 3),
            "paises": {iso: _serie(v, ANO_ONU, fim, 3) for iso, v in conc.items()}}


# ---------- conflitos ----------
def conflitos_por_ano(tabela: List[dict], linhas: List[dict]) -> dict:
    gw_iso = {g: r["iso_num"] for r in tabela for g in r["gw"]}
    cods = lambda txt: [gw_iso[int(c)] for c in re.findall(r"\d+", txt or "") if int(c) in gw_iso]
    fim = max(int(r["year"]) for r in linhas)
    paises: Dict[str, Dict[int, dict]] = {}
    por_ano: Dict[int, list] = {}
    for r in linhas:
        ano = int(r["year"])
        inten = int(r["intensity_level"])
        local, lados, apoio = set(cods(r["gwno_loc"])), set(cods(r["gwno_a"]) + cods(r["gwno_b"])), \
            set(cods(r["gwno_a_2nd"]) + cods(r["gwno_b_2nd"]))
        for iso in local | lados | apoio:
            d = paises.setdefault(iso, {}).setdefault(ano, {"t": 0, "l": 0, "a": 0})
            if iso in local:
                d["t"] = max(d["t"], inten)          # intensidade máxima no território (1: 25–999 mortes; 2: 1.000+)
            if iso in lados:
                d["l"] += 1                          # conflitos como lado principal
            elif iso in apoio:
                d["a"] += 1                          # conflitos com tropas de apoio (inclui missões multinacionais)
        por_ano.setdefault(ano, []).append({
            "id": r["conflict_id"], "local": r["location"], "a": r["side_a"], "b": r["side_b"],
            "tipo": conflitos.TIPO.get(r["type_of_conflict"], ""), "disputa": conflitos.DISPUTA.get(r["incompatibility"], ""),
            "territorio": r["territory_name"], "guerra": inten == 2, "paises": sorted(local)})
    for lista in por_ano.values():
        lista.sort(key=lambda c: (not c["guerra"], c["local"]))
    return {"inicio": ANO_UCDP, "fim": fim,
            "paises": {iso: {str(a): v for a, v in sorted(anos.items())} for iso, anos in paises.items()},
            "por_ano": {str(a): v for a, v in sorted(por_ano.items())}}


# ---------- OMC ----------
def disputas(tabela: List[dict], js: Optional[str] = None) -> dict:
    casos = omc.ler_casos(js if js is not None else omc._get(omc.URL_CASOS))
    iso3 = [r["iso3"] for r in tabela if r["iso3"] != "BRA"]
    r = omc.por_pais(casos, iso3)
    por3 = {t["iso3"]: t["iso_num"] for t in tabela}
    out = {}
    for k, v in r.items():
        if v["com_brasil"]:
            out[por3[k]] = {"via_ue": v["via_ue"], "casos": [{"ds": c["ds"], "ano": int(c["inicio"][:4]), "titulo": c["titulo"],
                                                              "brasil_abriu": "BRA" in c["reclamantes"], "situacao": c["situacao"],
                                                              "url": c["url"]} for c in v["com_brasil"]]}
    return out


# ---------- Banco Mundial ----------
def economia(tabela: List[dict]) -> dict:
    por3 = {t["iso3"]: t["iso_num"] for t in tabela}
    wb = bancomundial.indicadores_todos()
    return {por3[k]: [{"id": i, **bancomundial.INDICADORES[i], **x} for i, x in v.items()] for k, v in wb.items() if k in por3}


def montar(saida: Path, brutos: Path, ano_fim_comex: Optional[str] = None, log=print) -> dict:
    tabela = codigos.carregar()
    fim = int(ano_fim_comex or datetime.now().year - 1)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"gerado_em": agora, "falhas": {}, "paises": {r["iso_num"]: {"nome": r["nome"], "iso3": r["iso3"], "iso2": r.get("iso2", ""),
                                                                    "tipo": r.get("tipo", ""), "no_mapa": r["no_mapa"]} for r in tabela}}
    pares: dict = {}
    etapas = [
        ("comercio", lambda: comercio(tabela, fim, brutos / "comex", pares_saida=pares)),
        ("onu", lambda: votos(tabela, sorted((brutos / "onu").glob("*_AgreementScores.csv"))[-1])),
        ("conflitos", lambda: conflitos_por_ano(tabela, conflitos.ler(sorted((brutos / "ucdp").glob("*.zip"))[-1].read_bytes()))),
        ("omc", lambda: disputas(tabela)),
        ("economia", lambda: economia(tabela)),
    ]
    for nome, f in etapas:
        log(f"{nome}: coletando")
        try:
            out[nome] = f()
        except (OSError, ValueError, KeyError, IndexError) as e:
            out["falhas"][nome] = f"{type(e).__name__}: {e}"[:200]
            log(f"  falhou: {out['falhas'][nome]}")
    _gravar(saida, "historia", "HISTORIA", out, log)
    if pares and "comercio" in out:
        log("produtos: coletando")
        try:
            pr = produtos(fim, pares, out["comercio"]["sh4"], brutos / "comex")
            pr["gerado_em"] = agora
            _gravar(saida, "produtos", "PRODUTOS", pr, log)
        except (OSError, ValueError, KeyError) as e:
            out["falhas"]["produtos"] = f"{type(e).__name__}: {e}"[:200]
            log(f"  falhou: {out['falhas']['produtos']}")
            _gravar(saida, "historia", "HISTORIA", out, log)
    return out


def _gravar(saida: Path, nome: str, var: str, dados: dict, log=print) -> None:
    txt = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    saida.mkdir(parents=True, exist_ok=True)
    (saida / f"{nome}.json").write_text(txt, encoding="utf-8")
    (saida / f"{nome}.js").write_text(f"window.{var} = {txt};\n", encoding="utf-8")
    log(f"{nome}.json: {len(txt) / 1e6:.2f} MB")
