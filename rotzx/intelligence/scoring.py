"""Score de oportunidade (0–100) e elegibilidade, separados do nível de evidência (docs/06 §3).

O score ordena o que olhar primeiro. NÃO é probabilidade de compra nem de venda.
"""
import re
from typing import Optional

import pandas as pd

from ..providers import aneel_siget as sg
from .evidencia import CONFIRMADO, INFERENCIA

TETO_INFERENCIA = 60      # só inferência nunca passa disto
RAMPA_MESES = 6           # estágio sobe de 0,5 (na janela) a 1,0 (janela + 6 meses): perto da janela, a compra pode já ter acontecido
MESES_FAIXA_PLENA = 30    # até janela + 30 meses: estágio pleno; depois, acompanhamento
ESTAGIO_DISTANTE = 0.7
COMPAT_SEM_TENSAO = 0.85  # categoria confirmada, mas a classe de tensão não está declarada
ESTAGIO_PENDENCIA = 0.5   # descrição com pendência ("aguardar", "em estudo"…): estágio no máximo 0,5
ALERTA_TEXTO = re.compile(r"aguardar|em estudo|suspens|cancelad|paralisad|sub judice|revog", re.I)  # mostrado, não pontuado
ATUALIDADE_DIAS = 30      # arquivo da fonte com mais de 30 dias: evidência vale metade


def _uf_ok(ufs: str, perfil_ufs) -> float:
    if not perfil_ufs:
        return 1.0
    if not ufs:
        return 0.5
    return 1.0 if set(ufs.split(",")) & set(perfil_ufs) else 0.0


def oportunidades(emp: pd.DataFrame, ev: pd.DataFrame, cats: dict, perfil: dict,
                  hoje: Optional[pd.Timestamp] = None, data_fonte: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """Empreendimentos que viram oportunidade para o perfil, com score, componentes e explicação."""
    hoje = hoje or pd.Timestamp.today().normalize()
    data_fonte = data_fonte or hoje
    janela = {c["id"]: c["janela_meses"] for c in cats["categorias"]}
    nome_cat = {c["id"]: c["nome"] for c in cats["categorias"]}
    w = perfil["pesos"]
    atual = 1.0 if (hoje - data_fonte).days <= ATUALIDADE_DIAS else 0.5
    ev = ev[ev.categoria.isin(perfil["categorias"]) & ev.nivel.isin([CONFIRMADO, INFERENCIA])]
    base = emp[(emp.situacao == sg.EM_ANDAMENTO) & (emp.concessionaria.astype(str).str.strip() != "")].copy()
    base["meses_ate_operacao"] = ((sg.data(base.operacao_ato_legal) - hoje).dt.days / 30.44).round(1)
    out = []
    for e in base.itertuples(index=False):
        evs = ev[ev.id_aneel == e.id_aneel]
        if evs.empty or pd.isna(e.meses_ate_operacao):
            continue
        m = e.meses_ate_operacao
        elegiveis = [c for c in evs.categoria.unique() if m >= janela[c]]
        if not elegiveis:
            continue
        evs = evs[evs.categoria.isin(elegiveis)]
        tmin = perfil.get("tensao_min_kv")
        if tmin:  # perfil com classe de tensão mínima: evidência com tensão declarada abaixo dela não conta
            evs = evs[evs.tensao_kv.isna() | (evs.tensao_kv >= tmin)]
            if evs.empty:
                continue
        conf_ev = evs[evs.nivel == CONFIRMADO]
        conf = sorted(conf_ev.categoria.unique())
        inf = sorted(set(evs[evs.nivel == INFERENCIA].categoria) - set(conf))
        tensoes = sorted({float(x) for x in conf_ev.tensao_kv.dropna()}, reverse=True)
        compat = (1.0 if tensoes else COMPAT_SEM_TENSAO) if conf else 0.5
        J = min(janela[c] for c in elegiveis)
        estagio = (0.5 + 0.5 * min(1.0, (m - J) / RAMPA_MESES)) if m <= J + MESES_FAIXA_PLENA else ESTAGIO_DISTANTE
        alerta = "; ".join(sorted({x.group(0).lower() for x in ALERTA_TEXTO.finditer(f"{e.nome} {e.descricao}")}))
        if alerta:  # pendência descrita na fonte: o estágio fica incerto
            estagio = min(estagio, ESTAGIO_PENDENCIA)
        origens = set(evs[evs.nivel == CONFIRMADO].origem)
        qual = (1.0 if {"campo", "texto"} <= origens else 0.8 if origens else 0.4) * atual
        geo = _uf_ok(e.ufs, perfil.get("ufs"))
        score = round(100 * (w["compatibilidade"] * compat + w["estagio"] * estagio + w["evidencia"] * qual + w["geografia"] * geo))
        if not conf:
            score = min(score, TETO_INFERENCIA)
        orig_txt = "campo e texto da fonte" if {"campo", "texto"} <= origens else ("só " + next(iter(origens))) if origens else "só inferência"
        tens_txt = (", " + "/".join(f"{x:g}" for x in tensoes[:3]) + " kV") if tensoes else (", tensão não declarada" if conf else "")
        explic = (f"Compatibilidade {compat:.0%} ({'categoria do perfil confirmada na fonte' if conf else 'só por inferência técnica'}{tens_txt}); "
                  f"estágio {estagio:.0%} (operação pelo ato legal em {m:g} meses; janela mínima {J} meses"
                  f"{'; reduzido porque a descrição indica pendência' if alerta else ''}); "
                  f"evidência {qual:.0%} ({orig_txt}); geografia {geo:.0%}.")
        out.append({**e._asdict(), "score": score, "nivel_evidencia": "confirmado" if conf else "inferência técnica",
                    "categorias_confirmadas": "; ".join(nome_cat[c] for c in conf),
                    "categorias_inferidas": "; ".join(nome_cat[c] for c in inf),
                    "tensoes_kv": "/".join(f"{x:g}" for x in tensoes),
                    "c_compatibilidade": compat, "c_estagio": estagio, "c_evidencia": qual, "c_geografia": geo,
                    "explicacao_score": explic,
                    "alerta_texto": alerta})
    if not out:
        return pd.DataFrame()
    df = pd.DataFrame(out)
    df["_id"] = pd.to_numeric(df.id_aneel, errors="coerce")
    return df.sort_values(["score", "meses_ate_operacao", "_id"], ascending=[False, True, True]).drop(columns="_id").reset_index(drop=True)
