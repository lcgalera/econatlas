"""Indicadores antecedentes de um setor: teste fora da amostra, em tempo pseudo-real.

Pergunta: saber o valor de um indicador hoje melhora a previsão do crescimento
do setor, em relação a usar só o histórico do próprio setor?

Desenho (fixado antes de olhar os resultados):
- Alvo: variação em 12 meses (log × 100) da série do setor. Variação anual porque a série é sazonal.
- Origem t = mês em que a previsão é feita. Cada série só entra com o que estaria
  publicado em t: o alvo e as séries da CNI/IBGE chegam com ~2 meses de atraso;
  sondagens FGV/ICEI, juros e câmbio, no próprio mês. As defasagens de divulgação
  são premissas declaradas em CANDIDATOS e ALVO_DEFASAGEM.
- Horizontes h = 0 (nowcast do mês corrente), 3 e 6 meses à frente de t.
- Modelo base:      y(t+h) = a + b·y(t−2)
  Modelo ampliado:  y(t+h) = a + b·y(t−2) + c·x(t−d)
  Estimados por MQO em janela expansiva; a previsão de cada origem usa só pares
  (y, x) já observados naquela data.
- Avaliação: RMSE relativo (ampliado/base) e teste de Clark-West (modelos aninhados),
  com erro-padrão Newey-West. Correção de Holm para os múltiplos testes.
- Correlações cruzadas são só descritivas: séries persistentes inflam correlações,
  por isso a conclusão vem do teste fora da amostra.

Limitações: o modelo ampliado usa só o valor mais recente do indicador, x(t−d); uma
antecedência mais longa que o horizonte só é captada se o indicador for persistente.
Usa a versão atual dos dados (sondagens dessazonalizadas são revisadas);
associação preditiva não é causalidade.
"""
import json
from typing import Dict, List, Optional, Set

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from .. import storage

ALVO = "md_mc0397"         # alvo padrão (setor elétrico); ver SETORES
ALVO_DEFASAGEM = 2         # meses até a divulgação
HORIZONTES = [0, 3, 6]
INICIO_AVALIACAO = "2016-01-01"
MIN_ESTIMACAO = 48
PANDEMIA = ("2020-03-01", "2021-12-01")

# série, rótulo, transformação, defasagem (meses: divulgação + antecedência testada), sinal esperado, rodada
# Rodada 1: definida antes de qualquer resultado.
# Rodada 2 (canal de juros): formulada DEPOIS de ver que a Selic foi o único sinal da rodada 1;
# é uma hipótese condicionada aos dados e deve ser lida com mais cautela.
CANDIDATOS = [
    ("md_md2494", "FGV – Confiança da indústria", "nivel", 0, +1, 1),
    ("md_md2496", "FGV – Expectativas da indústria", "nivel", 0, +1, 1),
    ("md_md2497", "FGV – NUCI da indústria", "nivel", 0, +1, 1),
    ("md_md1469", "CNI – ICEI geral", "nivel", 0, +1, 1),
    ("md_md1473", "CNI – ICEI expectativas", "nivel", 0, +1, 1),
    ("md_ce1912", "FGV – Confiança da construção", "nivel", 0, +1, 1),
    ("UCI_DO_SETOR", "CNI – UCI do próprio setor (var. 12m, p.p.)", "dif12", 2, +1, 1),
    ("ibcbr_sa", "IBC-Br (var. 12m)", "log12", 2, +1, 1),
    ("selic_mensal", "Selic (var. 12m, p.p.)", "dif12", 0, -1, 1),
    ("cambio_usd", "Câmbio R$/US$ (var. 12m)", "log12", 0, 0, 1),
    ("selic_mensal", "Selic (var. 12m, p.p.), 3 meses antes", "dif12", 3, -1, 2),
    ("selic_mensal", "Selic (var. 12m, p.p.), 6 meses antes", "dif12", 6, -1, 2),
    ("juro_real_exante", "Juro real ex-ante (Selic − IPCA esperado 12m)", "nivel", 0, -1, 2),
    ("juro_real_exante", "Juro real ex-ante (var. 12m, p.p.)", "dif12", 0, -1, 2),
    ("juros_pj", "Juros médios PJ (var. 12m, p.p.)", "dif12", 1, -1, 2),
    ("concessoes_pj_real", "Concessões de crédito PJ, reais (var. 12m)", "log12", 1, +1, 2),
    ("credito_pj_saldo_real", "Saldo de crédito PJ, real (var. 12m)", "log12", 1, +1, 2),
]

# Alvos analisados. "replicacao" = o conjunto de hipóteses (as duas rodadas) foi fixado
# antes de olhar qualquer resultado deste alvo; serve para ver se o achado do setor elétrico se repete.
SETORES = {  # séries-alvo públicas (abertas). As de uso pessoal vêm de privado/setores_pessoais.json, fora do git.
    "eletrico_pim": {"alvo": "pim_eletricos", "rotulo": "IBGE – Produção física: máquinas e materiais elétricos",
                     "fonte": "IBGE/SIDRA 8888 (PIM-PF), seção 3.27", "uci": None, "defasagem": 2, "replicacao": True},
    "maquinas_pim": {"alvo": "pim_maquinas", "rotulo": "IBGE – Produção física: máquinas e equipamentos",
                     "fonte": "IBGE/SIDRA 8888 (PIM-PF), seção 3.28", "uci": None, "defasagem": 2, "replicacao": True},
}


def _carregar_setores_pessoais():
    """Acrescenta os setores de uso pessoal (Macrodados) se o arquivo local existir. No repositório
    público e no GitHub Actions ele não existe, e só as séries abertas são analisadas."""
    from .. import config
    f = config.PRIVATE_DIR / "setores_pessoais.json"
    if not f.exists():
        return []
    cfg = json.loads(f.read_text(encoding="utf-8"))
    for s, uci in cfg.get("uci_setores_publicos", {}).items():
        if s in SETORES:
            SETORES[s]["uci"] = uci
    SETORES.update(cfg.get("setores", {}))
    ordem = [s for s in cfg.get("ordem", []) if s in SETORES]
    reordenado = {s: SETORES[s] for s in ordem + [s for s in SETORES if s not in ordem]}
    SETORES.clear()
    SETORES.update(reordenado)
    return cfg.get("setores_previsao_pessoais", [])


SETORES_PESSOAIS_PREVISAO = _carregar_setores_pessoais()


def load_candidate(conn, sid: str) -> pd.Series:
    """Série observada do catálogo ou derivada declarada aqui (deflação, juro real)."""
    from ..transforms import ipca_index
    if sid == "juro_real_exante":
        selic = storage.load_observations(conn, "selic_mensal").asfreq("MS")
        exp = storage.load_observations(conn, "ipca_expect_12m").asfreq("MS")
        return (100 * ((1 + selic / 100) / (1 + exp / 100) - 1)).dropna()
    if sid in ("concessoes_pj_real", "credito_pj_saldo_real"):
        nominal = storage.load_observations(conn, sid.replace("_real", "")).asfreq("MS")
        idx = ipca_index(storage.load_observations(conn, "ipca_mensal")).reindex(nominal.index)
        return (nominal / idx).dropna()  # preços constantes (base arbitrária; irrelevante para var. 12m)
    return storage.load_observations(conn, sid)


SERIES_BASE = {"juro_real_exante": ["selic_mensal", "ipca_expect_12m"],
               "concessoes_pj_real": ["concessoes_pj", "ipca_mensal"],
               "credito_pj_saldo_real": ["credito_pj_saldo", "ipca_mensal"]}
TRANSFORMACOES = {"nivel": "nível", "dif12": "x(t) − x(t−12)", "log12": "100·ln(x(t)/x(t−12))"}


def transform(s: pd.Series, how: str) -> pd.Series:
    s = s.asfreq("MS")
    if how == "nivel":
        return s
    if how == "dif12":
        return s - s.shift(12)
    if how == "log12":
        return 100 * np.log(s / s.shift(12))
    raise ValueError(how)


def cross_correlations(y: pd.Series, x: pd.Series, max_lag: int = 12) -> List[Dict]:
    """corr(y(t), x(t−k)) para k = 0..max_lag (k > 0: x antecede y)."""
    out = []
    for k in range(max_lag + 1):
        pair = pd.concat([y, x.shift(k)], axis=1).dropna()
        out.append({"defasagem": k, "corr": float(pair.corr().iloc[0, 1]), "n": int(len(pair))})
    return out


def _design(y: pd.Series, x: pd.Series, h: int, ylag: int, xlag: int) -> pd.DataFrame:
    """Linha indexada pela origem t: alvo y(t+h), regressores y(t−ylag) e x(t−xlag)."""
    idx = y.index.union(x.index)
    y, x = y.reindex(idx), x.reindex(idx)
    return pd.DataFrame({"alvo": y.shift(-h), "ylag": y.shift(ylag), "x": x.shift(xlag)}, index=idx)


def clark_west(e_base: np.ndarray, e_aug: np.ndarray, f_base: np.ndarray, f_aug: np.ndarray, hac_lags: int):
    """Teste de Clark-West (2007) para modelos aninhados. Devolve (estatística, p-valor unilateral)."""
    adj = e_base ** 2 - (e_aug ** 2 - (f_base - f_aug) ** 2)
    res = sm.OLS(adj, np.ones_like(adj)).fit(cov_type="HAC", cov_kwds={"maxlags": max(hac_lags, 1)})
    t = float(res.tvalues[0])
    return t, float(1 - stats.norm.cdf(t))


def oos_test(y: pd.Series, x: pd.Series, h: int, xlag: int, ylag: int = ALVO_DEFASAGEM) -> Dict:
    d = _design(y, x, h, ylag, xlag)
    origins = d.index[(d.index >= INICIO_AVALIACAO) & d["alvo"].notna() & d["ylag"].notna() & d["x"].notna()]
    rows = []
    for t in origins:
        # pares cujo alvo y(s+h) já estava publicado em t, isto é, s + h ≤ t − ALVO_DEFASAGEM
        train = d[(d.index <= t - pd.DateOffset(months=h + ylag))].dropna()
        if len(train) < MIN_ESTIMACAO:
            continue
        xb = sm.add_constant(train[["ylag"]]); xa = sm.add_constant(train[["ylag", "x"]])
        fb = sm.OLS(train["alvo"], xb).fit().params
        fa = sm.OLS(train["alvo"], xa).fit().params
        row = d.loc[t]
        pb = fb["const"] + fb["ylag"] * row["ylag"]
        pa = fa["const"] + fa["ylag"] * row["ylag"] + fa["x"] * row["x"]
        rows.append((t, row["alvo"], pb, pa, fa["x"]))
    r = pd.DataFrame(rows, columns=["origem", "real", "base", "ampliado", "coef_x"]).set_index("origem")
    if len(r) < 24:
        return {"n": int(len(r)), "insuficiente": True}
    eb, ea = (r["real"] - r["base"]).values, (r["real"] - r["ampliado"]).values
    cw, p = clark_west(eb, ea, r["base"].values, r["ampliado"].values, hac_lags=h + ylag)
    fora = ~((r.index >= PANDEMIA[0]) & (r.index <= PANDEMIA[1]))
    rmse = lambda e: float(np.sqrt(np.mean(e ** 2)))
    return {
        "n": int(len(r)), "inicio": f"{r.index.min():%Y-%m}", "fim": f"{r.index.max():%Y-%m}",
        "rmse_base": rmse(eb), "rmse_ampliado": rmse(ea), "razao_rmse": rmse(ea) / rmse(eb),
        "razao_rmse_sem_pandemia": rmse(ea[fora]) / rmse(eb[fora]),
        "clark_west": cw, "p_valor": p,
        "coef_x_ultimo": float(r["coef_x"].iloc[-1]),
        "coef_x_mesmo_sinal_pct": float((np.sign(r["coef_x"]) == np.sign(r["coef_x"].iloc[-1])).mean()),
    }


def holm(pvalues: List[float]) -> List[float]:
    order = np.argsort(pvalues)
    m = len(pvalues)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adj[i] = running
    return adj.tolist()


def run(conn, setor: str = "eletrico", permitidas: Optional[Set[str]] = None) -> Dict:
    """`permitidas`: se dado, só entram candidatos cujas séries de origem estejam no conjunto
    (versão pública: só séries de uso público). A correção de Holm é refeita sobre essa família menor,
    para que nenhum número publicado dependa de testes com dados excluídos."""
    cfg = SETORES[setor]
    alvo, ylag = cfg["alvo"], cfg["defasagem"]
    if permitidas is not None and alvo not in permitidas:
        raise ValueError(f"série-alvo {alvo} fora das séries permitidas")
    y = transform(storage.load_observations(conn, alvo), "log12").dropna()
    vintages = {alvo: storage.latest_vintage(conn, alvo)["id"]}
    results = []
    excluidos = 0
    for sid, rotulo, how, lag, sinal, rodada in CANDIDATOS:
        if sid == "UCI_DO_SETOR":
            sid = cfg.get("uci")
            if not sid:  # versão pública: a UCI da CNI é de uso pessoal
                excluidos += 1
                continue
        if permitidas is not None and not set(SERIES_BASE.get(sid, [sid])) <= permitidas:
            excluidos += 1
            continue
        raw = load_candidate(conn, sid)
        if raw.empty:
            results.append({"id": sid, "rotulo": rotulo, "rodada": rodada, "erro": "série sem dados"})
            continue
        if raw.index.to_series().diff().dt.days.median() < 20:  # diária -> média mensal
            raw = raw.resample("MS").mean()
        for base in SERIES_BASE.get(sid, [sid]):
            vintages[base] = storage.latest_vintage(conn, base)["id"]
        x = transform(raw, how).dropna()
        results.append({
            "id": sid, "rotulo": rotulo, "rodada": rodada, "transformacao": TRANSFORMACOES[how],
            "defasagem_divulgacao": lag, "sinal_esperado": sinal, "inicio_dados": f"{x.index.min():%Y-%m}",
            "series_base": SERIES_BASE.get(sid, [sid]),
            "correlacoes": cross_correlations(y, x),
            "fora_da_amostra": {str(h): oos_test(y, x, h, lag, ylag) for h in HORIZONTES},
        })
    # Holm dentro de cada rodada (família de hipóteses declarada junta) e sobre todos os testes
    keys = [(i, h) for i, r in enumerate(results) for h, o in r.get("fora_da_amostra", {}).items() if "p_valor" in o]
    pv = lambda k: results[k[0]]["fora_da_amostra"][k[1]]["p_valor"]
    for (i, h), a in zip(keys, holm([pv(k) for k in keys])):
        results[i]["fora_da_amostra"][h]["p_holm_total"] = a
    for rodada in sorted({r["rodada"] for r in results}):
        ks = [k for k in keys if results[k[0]]["rodada"] == rodada]
        for (i, h), a in zip(ks, holm([pv(k) for k in ks])):
            results[i]["fora_da_amostra"][h]["p_holm"] = a
    return {
        "setor": setor, "replicacao": cfg["replicacao"],
        "alvo": {"id": alvo, "rotulo": cfg["rotulo"], "fonte": cfg["fonte"],
                 "transformacao": "100·ln(x(t)/x(t−12))", "defasagem_divulgacao": ylag,
                 "serie": [[f"{d:%Y-%m-%d}", round(float(v), 3)] for d, v in y.items()]},
        "horizontes": HORIZONTES, "inicio_avaliacao": INICIO_AVALIACAO, "n_testes": len(keys),
        "versoes": vintages, "metodo": __doc__.strip(), "candidatos": results,
        "candidatos_excluidos": excluidos, "somente_permitidas": permitidas is not None,
    }
