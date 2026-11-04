"""Leilões arrematados ainda sem contrato no SIGET: o sinal mais cedo do radar (D37).

Um lote arrematado vira contrato de concessão alguns meses depois e só então aparece no SIGET. Enquanto isso, a descrição
do lote na planilha oficial já diz o que será construído (linhas, subestações, transformação, compensação).
  - pendentes(): lotes recentes sem contrato identificado no mapa conferido (catalog/leiloes_contratos.json)
  - evidencias_lote(): categorias de produto citadas na descrição do lote (regra R6) e inferências de bay/linha
  - prazos_observados(): dias entre o leilão e a assinatura, medidos nas ligações conferidas
Nada aqui afirma compra: o lote descreve instalações a construir, não pedidos de equipamento.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .. import config
from ..providers import aneel_siget as sg
from .evidencia import CONFIRMADO, INFERENCIA, NAO_VERIFICADO, compilar

MAPA_FILE = config.ROOT / "catalog" / "leiloes_contratos.json"
JANELA_MESES = 24  # lotes de leilões dos últimos 24 meses entram na verificação de contrato
LIGADO = {"conferido", "provavel"}
TRANSFORMACAO = re.compile(r"\d{2,3}\s*/\s*\d{2,3}(?:\s*/\s*\d{2,3})?\s*kV[^;]{0,90}?\d+(?:[.,]\d+)?\s*MVA", re.I)
SUBESTACAO = re.compile(r"\bSEs?\b|subesta[çc]", re.I)
LINHA = re.compile(r"\bLTs?\b|linha de transmiss", re.I)
CONTINUIDADE = re.compile(r"continuidade|presta[çc][ãa]o do servi[çc]o", re.I)
NOVAS = re.compile(r"novas\s+instala[çc][õo]es\s*:?", re.I)


def carregar_mapa(caminho: Path = MAPA_FILE) -> pd.DataFrame:
    d = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return pd.DataFrame(d["ligacoes"], columns=["leilao", "data_leilao", "lote", "contrato", "status", "evidencia"])


def _chave(df: pd.DataFrame) -> pd.Series:
    return df.leilao.astype(str) + "|" + df.data_leilao.astype(str) + "|" + df.lote.astype(str).str.upper()


def pendentes(leiloes: pd.DataFrame, mapa: pd.DataFrame, hoje: pd.Timestamp, meses: int = JANELA_MESES) -> pd.DataFrame:
    """Lotes arrematados nos últimos `meses` sem contrato identificado (ou com ligação ambígua)."""
    if leiloes.empty:
        return leiloes.assign(status_contrato="", evidencia_contrato="")
    l = leiloes[(leiloes.situacao == "arrematado") & leiloes.data_leilao.notna()].copy()
    l = l[pd.to_datetime(l.data_leilao) >= hoje - pd.DateOffset(months=meses)]
    m = mapa.assign(_k=_chave(mapa)).set_index("_k")
    l["_k"] = _chave(l)
    l["status_contrato"] = l._k.map(m.status).fillna("sem contrato identificado")
    l["evidencia_contrato"] = l._k.map(m.evidencia).fillna("")
    l = l[~l.status_contrato.isin(LIGADO)]
    l["status_contrato"] = l.status_contrato.replace({"ambiguo": "contrato não identificado com segurança"})
    l["dias_desde_leilao"] = (hoje - pd.to_datetime(l.data_leilao)).dt.days
    prazo = pd.to_numeric(l.prazo_meses, errors="coerce")
    base = pd.to_datetime(l.data_leilao)
    l["operacao_estimada"] = [(b + pd.DateOffset(months=int(p))).strftime("%m/%Y") if pd.notna(p) else "" for b, p in zip(base, prazo)]
    return l.drop(columns="_k").sort_values(["data_leilao", "lote"], ascending=[False, True]).reset_index(drop=True)


def prazos_observados(mapa: pd.DataFrame, agente: pd.DataFrame) -> Dict:
    """Dias entre o leilão e a assinatura do contrato, nas ligações conferidas ou prováveis (medido, não suposto)."""
    ok = mapa[mapa.status.isin(LIGADO) & mapa.contrato.notna()]
    ass = agente.assign(ass=sg.data(agente.DatAsnCcd)).set_index("NumCnaCcd").ass
    dias = (ok.contrato.map(ass) - pd.to_datetime(ok.data_leilao)).dt.days.dropna()
    por_leilao = (ok.assign(dias=ok.contrato.map(ass).sub(pd.to_datetime(ok.data_leilao)).dt.days)
                  .groupby(["leilao", "data_leilao"]).dias.median().dropna().astype(int).to_dict())
    return {"n": int(len(dias)), "min": int(dias.min()) if len(dias) else None, "max": int(dias.max()) if len(dias) else None,
            "mediana": int(dias.median()) if len(dias) else None, "por_leilao": por_leilao}


def evidencias_lote(texto: str, cats: dict) -> List[Dict]:
    """R6: categorias citadas na descrição de um lote licitado (instalações novas), com o trecho que as sustenta.

    Lote de continuidade da prestação do serviço (instalações existentes) não confirma nada: fica como não verificado.
    Lote misto ("…continuidade…; Novas instalações: …"): só o trecho depois de "Novas instalações" confirma.
    """
    cc = compilar(cats)
    texto = texto or ""
    if not texto.strip():
        return []
    if CONTINUIDADE.search(texto):
        partes = NOVAS.split(texto, maxsplit=1)
        if len(partes) == 2:  # lote misto: só o trecho depois de "Novas instalações" é instalação nova
            return evidencias_lote(partes[1], cats) + [
                dict(e, nivel=NAO_VERIFICADO, regra="R6 descrição do lote licitado (continuidade de instalações existentes)")
                for e in _r6(partes[0], cc, cats) if e["nivel"] == CONFIRMADO]
        return [dict(e, nivel=NAO_VERIFICADO, regra="R6 descrição do lote licitado (continuidade de instalações existentes)")
                for e in _r6(texto, cc, cats) if e["nivel"] == CONFIRMADO]
    return _r6(texto, cc, cats)


def _r6(texto: str, cc: dict, cats: dict) -> List[Dict]:
    """Termos das categorias no texto de instalações novas (confirmado) e inferências de bay e de linha."""
    nivel, regra = CONFIRMADO, "R6 descrição do lote licitado"
    out = []

    def trecho(m):
        return f"“{texto[max(0, m.start() - 25): m.end() + 25].strip()}”"

    for cid, c in cc["categorias"].items():
        if c.get("inferida_de_bay_novo") or c.get("inferida_de_linha_nova"):
            continue
        m = c["_re"].search(texto)
        if cid == "transformador_potencia" and not m:
            m = TRANSFORMACAO.search(texto)
        if m:
            out.append({"categoria": cid, "nivel": nivel, "regra": regra, "detalhe": trecho(m)})
    if SUBESTACAO.search(texto):
        for cid, c in cc["categorias"].items():
            if c.get("inferida_de_bay_novo"):
                out.append({"categoria": cid, "nivel": INFERENCIA, "regra": "R4 subestação no lote; a descrição não lista este equipamento", "detalhe": ""})
    if LINHA.search(texto):
        for cid, c in cc["categorias"].items():
            if c.get("inferida_de_linha_nova"):
                out.append({"categoria": cid, "nivel": INFERENCIA, "regra": "R5 linha nova no lote; a descrição não detalha os materiais", "detalhe": ""})
    return out


def resumo_categorias(evs: List[Dict], nome_cat: dict, perfil_cats: Optional[list] = None) -> Dict[str, str]:
    sel = [e for e in evs if not perfil_cats or e["categoria"] in perfil_cats]
    conf = sorted({nome_cat[e["categoria"]] for e in sel if e["nivel"] == CONFIRMADO})
    inf = sorted({nome_cat[e["categoria"]] for e in sel if e["nivel"] == INFERENCIA} - set(conf))
    nv = sorted({nome_cat[e["categoria"]] for e in sel if e["nivel"] == NAO_VERIFICADO})
    return {"confirmadas": "; ".join(conf), "inferidas": "; ".join(inf), "nao_verificadas": "; ".join(nv)}
