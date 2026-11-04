"""Evidências por empreendimento e categoria de produto, a partir das tabelas do SIGET (regras R1–R5).

Níveis (docs/06 §2):
  confirmado          a fonte cita o equipamento numa obra em andamento (campo estruturado de módulo novo, ou texto
                      com verbo de fornecimento seguido do termo da categoria);
  inferencia_tecnica  a natureza da obra sugere o equipamento, mas a fonte não o cita (ex.: bay novo → para-raios);
  nao_verificado      o equipamento existe no módulo, mas a obra é de adequação e o texto não fala em troca.
Só obras com situação "Em andamento" geram evidência.
"""
import re
from typing import Dict, List, Optional

import pandas as pd

from ..providers import aneel_siget as sg

CONFIRMADO, INFERENCIA, NAO_VERIFICADO = "confirmado", "inferencia_tecnica", "nao_verificado"
OBRA_NOVA = {"Instalação", "Ampliação"}  # tipos de obra que criam módulo (DscTipObr)
JANELA_TEXTO = 120  # caracteres entre o verbo de fornecimento e o termo da categoria
COLUNAS = ["id_aneel", "categoria", "nivel", "origem", "regra", "detalhe", "tensao_kv"]
KV_TEXTO = re.compile(r"(\d{2,3}(?:[.,]\d+)?)\s*(?:/\s*\d+(?:[.,]\d+)?\s*)*kv", re.I)


def compilar(cats: dict) -> dict:
    """Pré-compila as expressões do catálogo (não altera o dicionário original)."""
    out = {"verbos": re.compile(f"(?:{cats['verbos_fornecimento']})", re.I), "categorias": {}}
    for c in cats["categorias"]:
        out["categorias"][c["id"]] = dict(c, _re=re.compile(c["termos_texto"], re.I))
    return out


def trecho_confirmado(texto: str, termo: "re.Pattern", verbos: "re.Pattern", janela: int = JANELA_TEXTO) -> Optional[str]:
    """Trecho em que um verbo de fornecimento é seguido pelo termo da categoria em até `janela` caracteres."""
    for v in verbos.finditer(texto or ""):
        m = termo.search(texto, v.end(), v.end() + janela)
        if m:
            return texto[max(0, v.start() - 15): min(len(texto), m.end() + 25)].strip()
    return None


def _num(v) -> float:
    x = sg.numero(pd.Series([v])).iloc[0]
    return 0.0 if pd.isna(x) else float(x)


def _txt_kv(tns, pot) -> str:
    t, p = _num(tns), _num(pot)
    return (f" {t:g} kV" if t else "") + (f" {p:g} MVA" if p else "")


def evidencias(t: Dict[str, pd.DataFrame], cats: dict) -> pd.DataFrame:
    """Todas as evidências (uma linha por empreendimento × categoria × regra × detalhe)."""
    cc = compilar(cats)
    tipo_para_cat = {tp: cid for cid, c in cc["categorias"].items() for tp in c.get("tipos_equipamento_siget", [])}
    eom = t["eom"]
    ob = eom[eom.DscSitObr == sg.EM_ANDAMENTO]
    linhas: List[list] = []
    add = lambda *r: linhas.append(list(r))

    # R1 — módulo de equipamento ligado a obra em andamento
    me = ob[["IdeEpd", "IdeMdl", "DscTipObr"]].drop_duplicates().merge(t["equipamento"], on="IdeMdl")
    for r in me.itertuples(index=False):
        cid = tipo_para_cat.get(r.DscTipEqp)
        if not cid:
            continue
        det = f"{r.DscTipEqp}{_txt_kv(r.NumTnsMdl, r.MdaPotAtvMdlEqp)} na SE {r.NomSubestacao}/{r.SigUFSubestacao} (obra: {r.DscTipObr})"
        if r.DscTipObr in OBRA_NOVA:
            add(r.IdeEpd, cid, CONFIRMADO, "campo", "R1 módulo de equipamento novo", det, _num(r.NumTnsMdl) or None)
        else:
            add(r.IdeEpd, cid, NAO_VERIFICADO, "campo", "R1 módulo existente em obra que não cria módulo", det, _num(r.NumTnsMdl) or None)

    # R3 — módulo de manobra novo: quantidades declaradas confirmam; sem quantidade, é inferência
    mm = ob[["IdeEpd", "IdeMdl", "DscTipObr"]].drop_duplicates().merge(t["manobra"], on="IdeMdl")
    mm = mm[mm.DscTipObr.isin(OBRA_NOVA)]
    for r in mm.itertuples(index=False):
        local = f"{r.DscMdlMno} {_num(r.NumTnsMdl):g} kV na SE {r.NomSubestacao}/{r.SigUFSubestacao}"
        for cid, col, nome in (("disjuntor", "QtdDijMdlMno", "disjuntor(es)"), ("chave_seccionadora", "QtdChvSccMdlMno", "seccionadora(s)")):
            q = getattr(r, col)
            kv = _num(r.NumTnsMdl) or None
            if str(q).strip() == "":
                add(r.IdeEpd, cid, INFERENCIA, "regra", "R3 módulo de manobra novo sem quantidade declarada", local, kv)
            elif _num(q) > 0:
                add(r.IdeEpd, cid, CONFIRMADO, "campo", "R3 quantidade declarada no módulo de manobra novo", f"{_num(q):g} {nome}: {local}", kv)

    # R4 — bay novo (equipamento ou manobra) → para-raios e transformadores de instrumento, por inferência
    bays = pd.concat([me[me.DscTipObr.isin(OBRA_NOVA)][["IdeEpd", "NomSubestacao", "SigUFSubestacao", "NumTnsMdl"]],
                      mm[["IdeEpd", "NomSubestacao", "SigUFSubestacao", "NumTnsMdl"]]]).drop_duplicates()
    for r in bays.itertuples(index=False):
        kv = _num(r.NumTnsMdl) or None
        for cid, c in cc["categorias"].items():
            if c.get("inferida_de_bay_novo"):
                add(r.IdeEpd, cid, INFERENCIA, "regra", "R4 bay novo costuma incluir este equipamento; a fonte não o lista",
                    f"SE {r.NomSubestacao}/{r.SigUFSubestacao}" + (f", {kv:g} kV" if kv else ""), kv)

    # R5 — linha nova → materiais de linha, por inferência
    lt = ob[["IdeEpd", "IdeObr", "DscTipObr"]].drop_duplicates().merge(t["linha"], on="IdeObr")
    for r in lt[lt.DscTipObr.isin(OBRA_NOVA)].itertuples(index=False):
        for cid, c in cc["categorias"].items():
            if c.get("inferida_de_linha_nova"):
                add(r.IdeEpd, cid, INFERENCIA, "regra", "R5 linha nova; a fonte não detalha os materiais", r.NomLinTms,
                    _num(r.NumTensaoBaseLinhaTransm) or None)

    # R2 — texto: verbo de fornecimento seguido do termo da categoria (nome, descrição e obras em andamento)
    textos = pd.concat([
        eom.drop_duplicates("IdeEpd")[["IdeEpd", "NomEpd"]].rename(columns={"NomEpd": "txt"}).assign(campo="nome"),
        eom.drop_duplicates("IdeEpd")[["IdeEpd", "DscEpd"]].rename(columns={"DscEpd": "txt"}).assign(campo="descrição"),
        ob.drop_duplicates("IdeObr")[["IdeEpd", "DscObr"]].rename(columns={"DscObr": "txt"}).assign(campo="obra"),
    ])
    textos = textos[textos.IdeEpd.isin(ob.IdeEpd)]  # só empreendimentos com obra em andamento
    for r in textos.itertuples(index=False):
        for cid, c in cc["categorias"].items():
            tr = trecho_confirmado(r.txt, c["_re"], cc["verbos"])
            if tr:
                kv = KV_TEXTO.search(tr)
                add(r.IdeEpd, cid, CONFIRMADO, "texto", f"R2 texto ({r.campo})", f"“{tr}”",
                    float(kv.group(1).replace(",", ".")) if kv else None)

    ev = pd.DataFrame(linhas, columns=COLUNAS).drop_duplicates()
    return ev.sort_values(["id_aneel", "categoria", "nivel", "regra"]).reset_index(drop=True)
