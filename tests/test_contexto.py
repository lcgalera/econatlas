"""Contexto de mercado do radar (Fase 5). Séries e tabelas abaixo são FIXTURES sintéticas, não dados do BCB, IBGE ou ANEEL."""
import numpy as np
import pandas as pd
import pytest

from rotzx import storage
from rotzx.catalog import SeriesMeta
from rotzx.intelligence import contexto, relatorio
from rotzx.providers import FetchResult

IDX = pd.date_range("2020-01-01", "2026-09-01", freq="MS")


def _s(vals, idx=IDX):
    return pd.Series(vals, index=idx, dtype=float)


def test_metricas_com_sinal_e_data():
    taxa = _s(np.r_[np.full(len(IDX) - 12, 15.0), np.full(12, 13.75)])
    m = contexto.medir(taxa, "nivel_diff12")
    assert m["valor"] == 13.75 and m["comparacao"] == pytest.approx(-1.25) and m["data"] == IDX[-1]
    cambio = _s(np.linspace(4.0, 5.0, len(IDX)))
    m = contexto.medir(cambio, "nivel_var12")
    assert m["comparacao"] > 0 and m["unidade_comp"] == "%"
    prod = _s(100 * 1.01 ** (np.arange(len(IDX)) / 12))  # cresce ~1% ao ano
    assert contexto.medir(prod, "media12_var")["comparacao"] == pytest.approx(1.0, abs=0.05)
    # real: série nominal que só acompanha a inflação tem variação real ~0
    ipca = _s(np.full(len(IDX), 0.4))
    nominal = _s(1000 * (1.004) ** np.arange(len(IDX)))
    assert contexto.medir(nominal, "real_var12", ipca)["comparacao"] == pytest.approx(0, abs=1e-6)
    assert contexto.medir(nominal, "real_soma12_var", ipca)["comparacao"] == pytest.approx(0, abs=1e-6)
    assert contexto.medir(_s([1.0, 2.0], IDX[:2]), "nivel_diff12") is None  # menos de 12 meses: não inventa
    with pytest.raises(ValueError):
        contexto.medir(taxa, "inventada")


def test_serie_diaria_vira_mensal_antes_de_comparar():
    d = pd.date_range("2025-01-01", "2026-11-03", freq="D")
    s = pd.Series(np.where(d < "2026-06-01", 15.0, 13.75), index=d)
    m = contexto.medir(s, "nivel_diff12")
    assert m["data"] == pd.Timestamp("2026-11-01") and m["comparacao"] == pytest.approx(-1.25)


def test_frase_descreve_sem_juizo_causal():
    f = contexto.frase({"rotulo": "Meta Selic", "metrica": "nivel_diff12", "valor": 13.75, "comparacao": -1.25,
                        "unidade_comp": "p.p.", "unidade": "% a.a.", "data": pd.Timestamp("2026-11-01")})
    assert f == "Meta Selic: 13,75 % a.a. em 11/2026 (−1,25 p.p. em 12 meses)."
    for proibida in ("portanto", "causa", "vai", "deve", "provoca"):
        assert proibida not in f.lower()
    assert "sem dados" in contexto.frase({"rotulo": "X", "erro": "sem dados suficientes"})


def _meta(sid, uso="publico", unidade="% a.a."):
    return SeriesMeta(id=sid, nome=sid, modulo="radar_brasil", tema="juros", instituicao="X", provedor="bcb_sgs", codigo="1",
                      unidade=unidade, periodicidade="mensal", geografia="Brasil", licenca="L", uso=uso, extra={})


def test_indicadores_so_publicos_e_falta_de_dado_aparece(tmp_path):
    conn = storage.connect(tmp_path / "t.sqlite")
    catalog = {"selic_meta": _meta("selic_meta"), "juros_pj": _meta("juros_pj", uso="pessoal"), "ipca_mensal": _meta("ipca_mensal", unidade="% a.m.")}
    for sid, v in (("selic_meta", np.full(len(IDX), 10.0)), ("juros_pj", np.full(len(IDX), 20.0)), ("ipca_mensal", np.full(len(IDX), 0.4))):
        storage.save_fetch(conn, catalog[sid], FetchResult(b"x", "csv", "u", pd.DataFrame({"date": IDX, "value": v})), raw_dir=tmp_path / "raw")
    cfg = {"grupos": [{"id": "g", "nome": "G", "indicadores": [
        {"id": "selic_meta", "metrica": "nivel_diff12", "rotulo": "Selic", "por_que": "p", "limite": "l"},
        {"id": "juros_pj", "metrica": "nivel_diff12", "rotulo": "Juros PJ", "por_que": "p", "limite": "l"},
        {"id": "cambio_usd", "metrica": "nivel_var12", "rotulo": "Dólar", "por_que": "p", "limite": "l"}]}]}
    r = {i["id"]: i for i in contexto.indicadores(conn, catalog, cfg)}
    assert r["selic_meta"]["valor"] == 10.0 and r["selic_meta"]["coletado_em"]
    assert r["juros_pj"]["erro"] == "série fora do catálogo público"  # série pessoal nunca entra
    assert "erro" in r["cambio_usd"]


def test_configuracao_real_usa_series_publicas_do_catalogo():
    from rotzx import catalog as cat
    c = cat.load_catalog()
    for g in contexto.carregar_config()["grupos"]:
        for i in g["indicadores"]:
            assert i["id"] in c and c[i["id"]].uso == "publico", i["id"]
            assert i["por_que"] and i["limite"]


def test_pipeline_mostra_anos_sem_registro_como_zero():
    emp = pd.DataFrame({"situacao": ["Em andamento", "Em andamento", "Em Operação"],
                        "operacao_ato_legal": ["30/12/2027", "30/06/2028", "01/01/2015"]})
    t = {"resolucao": pd.DataFrame({"IdeDoc": ["1", "2", "2"], "DatPubDoc": ["2024-03-01", "2026-05-01", "2026-05-01"]}),
         "agente": pd.DataFrame({"DatAsnCcd": ["10/02/2024", "23/02/2026"]})}
    p = contexto.pipeline(t, emp, pd.Timestamp("2026-11-04"))
    assert p["em_andamento_por_ano_operacao"].to_dict() == {2027: 1, 2028: 1}
    assert p["contratos_assinados_por_ano"].to_dict() == {2021: 0, 2022: 0, 2023: 0, 2024: 1, 2025: 0, 2026: 1}
    assert p["atos_autorizativos_por_ano"][2026] == 1  # o mesmo ato não conta duas vezes


def test_previsao_setorial_le_o_registro_publico(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("registrado_em,setor,origem,alvo,horizonte,modelo,valor,lo80,hi80\n"
                 "2026-10-03,eletrico_pim,2026-09-01,2026-12-01,3,juros,1.0,-10,10\n"
                 "2026-11-03,eletrico_pim,2026-10-01,2027-01-01,3,juros,2.6,-11.2,11.6\n"
                 "2026-11-03,eletrico_pim,2026-10-01,2027-04-01,6,juros,0.7,-15,9.2\n")
    p = contexto.previsao_setorial(f)
    assert p["origem"] == "2026-10-01" and [l["horizonte"] for l in p["linhas"]] == [3, 6]
    assert contexto.previsao_setorial(tmp_path / "nao_existe.csv") is None


def test_relatorio_avisa_que_contexto_nao_entra_no_score():
    h = relatorio._secao_contexto({"indicadores": [{"id": "selic_meta", "grupo": "Capital", "rotulo": "Selic", "metrica": "nivel_diff12",
                                                    "valor": 13.75, "comparacao": -1.25, "unidade_comp": "p.p.", "unidade": "% a.a.",
                                                    "data": pd.Timestamp("2026-11-01"), "por_que": "custo de capital", "limite": "não indica obras"}]})
    assert "Nada desta seção muda a lista de oportunidades nem o score" in h and "Nenhuma relação aqui foi medida como causal" in h
    assert "O que não dá para concluir" in h and "não indica obras" in h
    assert "indisponível" in relatorio._secao_contexto(None)


def test_series_usadas_inclui_o_deflator():
    ids = contexto.series_usadas()
    assert "ipca_mensal" in ids and "selic_meta" in ids and len(ids) == len(set(ids))
