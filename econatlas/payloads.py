"""Montagem dos dados que a interface consome.

Usado por dois caminhos, para que mostrem exatamente os mesmos números:
- a API local (api.py), com o catálogo completo;
- o build público estático (public_build.py), com o catálogo filtrado a uso "publico".

Toda função recebe a conexão e o catálogo explicitamente: quem chama decide o que entra.
"""
import json
import math
from typing import Dict, Iterable, List, Optional

import pandas as pd

from . import config, quality, storage, transforms


def points(s: pd.Series) -> List:
    return [[f"{d:%Y-%m-%d}", None if (v is None or math.isnan(v)) else round(float(v), 6)] for d, v in s.items()]


def vintage_info(v) -> Optional[Dict]:
    if v is None:
        return None
    return {k: v[k] for k in ("id", "fetched_at", "source_url", "raw_path", "raw_sha256", "n_obs",
                              "first_date", "last_date", "n_new", "n_revised")}


def _meta_dict(meta) -> Dict:
    item = meta.to_dict()
    if meta.provedor == "arquivo":
        item["codigo"] = None  # não expor caminho local
    return item


def catalogo(conn, catalog: Dict) -> List[Dict]:
    out = []
    for meta in catalog.values():
        s = storage.load_observations(conn, meta.id)
        item = _meta_dict(meta)
        item["transformacoes"] = transforms.available(meta)
        item["versao"] = vintage_info(storage.latest_vintage(conn, meta.id))
        if len(s):
            item["ultimo"] = {"data": f"{s.index[-1]:%Y-%m-%d}", "valor": float(s.iloc[-1])}
            item["anterior"] = {"data": f"{s.index[-2]:%Y-%m-%d}", "valor": float(s.iloc[-2])} if len(s) > 1 else None
            spark = s.resample("MS").last() if meta.periodicidade == "diaria" else s
            years = 15 if meta.periodicidade == "anual" else 3  # séries anuais precisam de janela maior
            item["spark"] = points(spark[spark.index >= spark.index[-1] - pd.DateOffset(years=years)])
        out.append(item)
    return out


def series(conn, catalog: Dict, series_id: str, transform: str = "nivel",
           inicio: Optional[str] = None, fim: Optional[str] = None) -> Dict:
    """KeyError = série fora do catálogo; LookupError = sem dados; ValueError = transformação inválida."""
    meta = catalog[series_id]
    s = storage.load_observations(conn, series_id)
    if s.empty:
        raise LookupError(f"série {series_id} ainda não foi baixada; rode `python -m econatlas atualizar`")
    deflator = None
    if transform == "deflacionado_ipca":
        if "ipca_mensal" not in catalog:
            raise ValueError("deflacionar exige a série ipca_mensal no catálogo")
        deflator = storage.load_observations(conn, "ipca_mensal")
    out = transforms.apply(s, meta, transform, deflator=deflator)
    if inicio:
        out = out[out.index >= inicio]
    if fim:
        out = out[out.index <= fim]
    t = transforms.TRANSFORMS[transform]
    return {
        "serie": _meta_dict(meta),
        "transformacao": {"id": t.id, "rotulo": t.rotulo, "formula": t.formula,
                          "unidade": t.unidade(meta.unidade), "base": out.attrs.get("base"),
                          "series_auxiliares": ["ipca_mensal"] if deflator is not None else []},
        "versao": vintage_info(storage.latest_vintage(conn, series_id)),
        "dados": points(out),
    }


def versoes(conn, series_id: str) -> List[Dict]:
    return storage.list_vintages(conn, series_id)


def qualidade(conn, catalog: Dict) -> List[Dict]:
    return quality.run_all(conn, catalog)


def previsoes_ipca(conn) -> Dict:
    from .forecast import models, registry
    rows = registry.evaluated(conn)
    backtest = json.loads(config.BACKTEST_FILE.read_text(encoding="utf-8")) if config.BACKTEST_FILE.exists() else None
    ultima_origem = rows[0]["origem"] if rows else None
    return {
        "modelos": {k: {"rotulo": m["rotulo"], "spec": m["spec"]} for k, m in models.MODELOS.items()}
                   | {"focus_mediana": {"rotulo": "Focus (mediana)", "spec": "expectativa de mercado registrada no mesmo dia"}},
        "ultima_origem": ultima_origem,
        "atuais": [r for r in rows if r["origem"] == ultima_origem],
        "registro": rows,
        "placar": registry.scoreboard(rows),
        "backtest": backtest,
    }


def analises_setores(setores: Iterable[str]) -> List[Dict]:
    """Análises de antecedentes já salvas em data/analyses (geradas por `analisar-setor`)."""
    out = []
    for setor in setores:
        f = config.ANALYSES_DIR / f"{setor}_antecedentes.json"
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def previsoes_setoriais(conn, setores: Iterable[str]) -> Dict:
    from .analysis import leading
    from .forecast import setorial
    setores = list(setores)
    rows = [r for r in setorial.evaluated(conn) if r["setor"] in setores]
    cal_file = config.ANALYSES_DIR / "previsao_setorial_calibracao.json"
    cal = json.loads(cal_file.read_text(encoding="utf-8")) if cal_file.exists() else None
    if cal:
        cal = {**cal, "setores": {s: v for s, v in cal["setores"].items() if s in setores}}

    def historico(s):  # últimos 4 anos da variação em 12 meses, para o gráfico
        y = leading.transform(storage.load_observations(conn, leading.SETORES[s]["alvo"]), "log12").dropna()
        return points(y[y.index >= y.index[-1] - pd.DateOffset(years=4)])

    return {
        "setores": {s: {"rotulo": leading.SETORES[s]["rotulo"], "fonte": leading.SETORES[s]["fonte"],
                        "historico": historico(s)} for s in setores},
        "modelos": setorial.ESPEC,
        "especificacao": {"id": setorial.SPEC_ID, **setorial.SPEC},
        "registro": rows,
        "placar": setorial.scoreboard(rows),
        "calibracao": cal,
    }
