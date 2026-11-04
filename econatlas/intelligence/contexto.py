"""Contexto de mercado do radar (Fase 5): pipeline da transmissão (SIGET) + indicadores econômicos públicos (BCB/IBGE).

O contexto apoia a leitura das oportunidades; não prova demanda específica nem mede causalidade (docs/07).
As frases são descritivas e geradas a partir dos números; o "por que importa" e o "limite" de cada indicador
vêm de catalog/contexto_radar.json, escritos antes de olhar os valores.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .. import config, storage, transforms
from ..providers import aneel_siget as sg

CONTEXTO_FILE = config.ROOT / "catalog" / "contexto_radar.json"
REGISTRO_SETORIAL = config.ROOT / "registro" / "previsoes_setoriais.csv"


def carregar_config(caminho: Path = CONTEXTO_FILE) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def series_usadas(cfg: Optional[dict] = None) -> List[str]:
    """Séries que o contexto precisa (inclui ipca_mensal, o deflator das métricas reais)."""
    cfg = cfg or carregar_config()
    ids = [i["id"] for g in cfg["grupos"] for i in g["indicadores"]]
    return list(dict.fromkeys(ids + ["ipca_mensal"]))


def _mensal(s: pd.Series) -> pd.Series:
    s = s.sort_index()
    return s.resample("MS").last().dropna() if len(s) and (s.index.to_series().diff().dt.days.median() or 30) < 20 else s


def _ha_12_meses(s: pd.Series) -> Optional[float]:
    """Valor de 12 meses antes da última observação (a última observação até essa data)."""
    alvo = s.index[-1] - pd.DateOffset(months=12)
    antes = s[s.index <= alvo]
    return float(antes.iloc[-1]) if len(antes) else None


def medir(s: pd.Series, metrica: str, ipca_mensal: Optional[pd.Series] = None) -> Optional[Dict]:
    """Métrica de um indicador: último valor, comparação com 12 meses antes e a data de referência.

    nivel_diff12     nível e diferença em p.p. contra 12 meses antes (taxas)
    nivel_var12      nível e variação % contra 12 meses antes (preços, câmbio)
    real_var12       deflacionado pelo IPCA; variação % real em 12 meses
    real_soma12_var  deflacionado; soma de 12 meses contra os 12 anteriores (%)
    media12_var      média de 12 meses contra os 12 anteriores (%), para séries ruidosas (produção)
    """
    s = s.dropna().sort_index()
    if s.empty:
        return None
    if metrica in ("nivel_diff12", "nivel_var12"):
        s = _mensal(s)
        ult, ant = float(s.iloc[-1]), _ha_12_meses(s)
        if ant is None:
            return None
        comp = ult - ant if metrica == "nivel_diff12" else (ult / ant - 1) * 100
        return {"data": s.index[-1], "valor": ult, "comparacao": comp, "unidade_comp": "p.p." if metrica == "nivel_diff12" else "%"}
    if metrica in ("real_var12", "real_soma12_var"):
        if ipca_mensal is None or ipca_mensal.empty:
            return None
        idx = transforms.ipca_index(ipca_mensal)
        comum = s.index.intersection(idx.index)
        if not len(comum):
            return None
        r = (s.loc[comum] * idx.loc[comum].iloc[-1] / idx.loc[comum]).dropna()
        if metrica == "real_soma12_var":
            r = r.rolling(12, min_periods=12).sum().dropna()
        if len(r) < 13:
            return None
        return {"data": r.index[-1], "valor": float(r.iloc[-1]), "comparacao": (float(r.iloc[-1]) / float(r.iloc[-13]) - 1) * 100,
                "unidade_comp": "% real", "base_deflator": f"{comum[-1]:%Y-%m}"}
    if metrica == "media12_var":
        m = s.rolling(12, min_periods=12).mean().dropna()
        if len(m) < 13:
            return None
        return {"data": m.index[-1], "valor": float(s.iloc[-1]), "comparacao": (float(m.iloc[-1]) / float(m.iloc[-13]) - 1) * 100,
                "unidade_comp": "% (média de 12 meses)"}
    raise ValueError(f"métrica desconhecida: {metrica}")


def indicadores(conn, catalog: Dict, cfg: Optional[dict] = None) -> List[Dict]:
    """Indicadores configurados, só séries públicas do catálogo. Série sem dados volta com 'erro' (não some em silêncio)."""
    cfg = cfg or carregar_config()
    ipca = storage.load_observations(conn, "ipca_mensal")
    out = []
    for g in cfg["grupos"]:
        for ind in g["indicadores"]:
            meta = catalog.get(ind["id"])
            item = dict(ind, grupo=g["nome"])
            if meta is None or meta.uso != "publico":
                item["erro"] = "série fora do catálogo público"
                out.append(item)
                continue
            s = storage.load_observations(conn, ind["id"])
            m = medir(s, ind["metrica"], ipca) if len(s) else None
            v = storage.latest_vintage(conn, ind["id"])
            item.update(unidade=meta.unidade, instituicao=meta.instituicao, codigo=meta.codigo, provedor=meta.provedor,
                        coletado_em=v["fetched_at"] if v else None)
            if m is None:
                item["erro"] = "sem dados suficientes; rode `econatlas atualizar`"
            else:
                item.update(m)
            out.append(item)
    return out


def pipeline(t: Dict[str, pd.DataFrame], emp: pd.DataFrame, hoje: pd.Timestamp) -> Dict[str, pd.Series]:
    """Contagens do próprio SIGET: o tamanho e o ritmo da expansão que o radar acompanha (contagens, não valores)."""
    and_ = emp[emp.situacao == sg.EM_ANDAMENTO]
    op_ano = sg.data(and_.operacao_ato_legal).dt.year.dropna().astype(int)
    res = t["resolucao"].drop_duplicates("IdeDoc") if "IdeDoc" in t["resolucao"] else t["resolucao"]
    atos = sg.data(res.DatPubDoc).dt.year.dropna().astype(int)
    ag = t["agente"]
    contratos = sg.data(ag.DatAsnCcd).dt.year.dropna().astype(int) if "DatAsnCcd" in ag else pd.Series(dtype=int)
    ano0 = hoje.year - 5
    anos = range(ano0, hoje.year + 1)  # ano sem registro aparece como 0, não some
    contar = lambda x: x[x >= ano0].value_counts().reindex(anos, fill_value=0)
    return {
        "em_andamento_por_ano_operacao": op_ano.value_counts().sort_index(),
        "atos_autorizativos_por_ano": contar(atos),
        "contratos_assinados_por_ano": contar(contratos),
        "ano_corrente": hoje.year,
        "data_referencia": hoje,
    }


def previsao_setorial(caminho: Path = REGISTRO_SETORIAL, setor: str = "eletrico_pim") -> Optional[Dict]:
    """Última previsão REGISTRADA (registro público) da produção CNAE 27, modelos com e sem juros, 3 e 6 meses."""
    if not Path(caminho).exists():
        return None
    r = pd.read_csv(caminho, dtype=str)
    r = r[(r.setor == setor) & r.horizonte.isin(["3", "6"])]
    if r.empty:
        return None
    ult = r[r.origem == r.origem.max()]
    out = {"origem": ult.origem.iloc[0], "registrado_em": ult.registrado_em.iloc[0], "linhas": []}
    for x in ult.sort_values(["horizonte", "modelo"]).itertuples():
        out["linhas"].append({"modelo": x.modelo, "horizonte": int(x.horizonte), "alvo": x.alvo, "valor": float(x.valor),
                              "lo80": float(x.lo80), "hi80": float(x.hi80)})
    return out


def _br(v: float, casas: int, sinal: bool = False) -> str:
    txt = f"{v:+.{casas}f}" if sinal else f"{v:.{casas}f}"
    return txt.replace("-", "−").replace(".", ",")


def frase(ind: Dict) -> str:
    """Frase descritiva, sem juízo causal: valor, data e comparação com 12 meses antes (com sinal)."""
    if "erro" in ind:
        return f"{ind['rotulo']}: {ind['erro']}."
    quando = f"{ind['data']:%m/%Y}"
    if ind["metrica"] == "nivel_diff12":
        return f"{ind['rotulo']}: {_br(ind['valor'], 2)} {ind.get('unidade', '')} em {quando} ({_br(ind['comparacao'], 2, True)} p.p. em 12 meses)."
    if ind["metrica"] == "nivel_var12":
        return f"{ind['rotulo']}: {_br(ind['valor'], 2)} {ind.get('unidade', '')} em {quando} ({_br(ind['comparacao'], 1, True)}% em 12 meses)."
    base = {"real_soma12_var": "soma de 12 meses, real, contra os 12 meses anteriores",
            "media12_var": "média de 12 meses contra os 12 meses anteriores",
            "real_var12": "real, contra 12 meses antes"}[ind["metrica"]]
    return f"{ind['rotulo']}: {_br(ind['comparacao'], 1, True)}% ({base}; dados até {quando})."
