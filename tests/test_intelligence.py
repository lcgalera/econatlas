"""Motor de oportunidades (Fase 3). Tabelas abaixo são FIXTURES sintéticas (nomes e números inventados), não dados da ANEEL."""
import re

import pandas as pd
import pytest

from econatlas import intelligence as it
from econatlas.intelligence import evidencia as evm
from econatlas.intelligence import relatorio, scoring
from econatlas.providers import aneel_siget as sg

HOJE = pd.Timestamp("2026-11-04")


@pytest.fixture(scope="module")
def cats():
    return it.carregar_categorias()


@pytest.fixture(scope="module")
def cc(cats):
    return evm.compilar(cats)


def _df(rows, cols):
    return pd.DataFrame(rows, columns=cols).astype(str)


@pytest.fixture
def t():
    eom_cols = ["IdeCcd", "IdeEpd", "IdeOnsEpd", "NomEpd", "DscEpd", "DscSituacaoEpd", "DatOprComEpd", "DatCaoCgmAtoLgl",
                "DatEfeOprComEpd", "IdeObr", "DscObr", "DscSitObr", "DscTipObr", "IdeMdl", "DatGeracaoConjuntoDados"]
    g = "2026-11-02"
    eom = _df([
        # 1: troca de transformador descrita no texto, módulo em "Adequação" (só o texto confirma)
        ["10", "1", "T-FIC-1", "SE Fictícia A: Substituição do TR2 230/69 kV por um de 100 MVA", "Troca do TR2", "Em andamento",
         "30/12/2027", "30/12/2027", "", "100", "Substituir o TR2", "Em andamento", "Adequação", "1000", g],
        # 2: banco de capacitores novo (campo) + módulo de manobra novo sem quantidade (inferência)
        ["10", "2", "T-FIC-2", "SE Fictícia B: banco de capacitores", "Banco de capacitores 138 kV", "Em andamento",
         "31/05/2028", "31/05/2028", "", "200", "Obra B", "Em andamento", "Instalação", "2000", g],
        ["10", "2", "T-FIC-2", "SE Fictícia B: banco de capacitores", "Banco de capacitores 138 kV", "Em andamento",
         "31/05/2028", "31/05/2028", "", "201", "Obra B2", "Em andamento", "Instalação", "2001", g],
        # 3: revitalização sem troca (nada confirmado)
        ["10", "3", "T-FIC-3", "SE Fictícia C: revitalização do transformador conversor", "Revitalização", "Em andamento",
         "30/12/2028", "30/12/2028", "", "300", "Revitalizar", "Em andamento", "Adequação", "3000", g],
        # 4: reator novo, mas operação em 2 meses (fora da janela)
        ["10", "4", "T-FIC-4", "SE Fictícia D: Instalação do 1º reator de barra", "Reator", "Em andamento",
         "04/01/2027", "04/01/2027", "", "400", "Instalar reator", "Em andamento", "Instalação", "4000", g],
        # 5: só módulo de manobra novo sem quantidade (só inferência) e descrição com pendência
        ["10", "5", "T-FIC-5", "SE Fictícia E: módulo de conexão", "Aguardar solução em estudo", "Em andamento",
         "30/12/2028", "30/12/2028", "", "500", "Obra E", "Em andamento", "Instalação", "5001", g],
    ], eom_cols)
    agente = _df([["10", "Transmissora Fictícia", "191", "001/2001"]], ["IdeCcd", "DscRazaoSocial", "NumCNPJ", "NumCnaCcd"])
    eq_cols = ["IdeMdl", "DscTipEqp", "NumTnsMdl", "MdaPotAtvMdlEqp", "NomSubestacao", "SigUFSubestacao"]
    equipamento = _df([["1000", "Transformador de Potência", "230,00", "", "FIC A", "BA"],
                       ["2000", "Banco de Capacitores", "138,00", "", "FIC B", "SP"],
                       ["3000", "Transformador de Potência", "600,00", "900.00", "FIC C", "PR"],
                       ["4000", "Reator de Barra", "500,00", "", "FIC D", "MG"]], eq_cols)
    mm_cols = ["IdeMdl", "DscMdlMno", "NumTnsMdl", "QtdDijMdlMno", "QtdChvSccMdlMno", "NomSubestacao", "SigUFSubestacao"]
    manobra = _df([["2001", "Módulo de Conexão", "138,00", "", "", "FIC B", "SP"],
                   ["5001", "Módulo de Conexão", "230,00", "", "", "FIC E", "RS"]], mm_cols)
    linha = _df([], ["IdeMdl", "IdeObr", "NomLinTms", "NumTensaoBaseLinhaTransm", "SigUFSubestacaoOrigem", "SigUFSubestacaoDestino"])
    geral = _df([], ["IdeMdl", "SigUFSubestacao"])
    resolucao = _df([["1", "REA-2025-1", "2025-01-01", "http://exemplo.invalido/1"]], ["IdeEpd", "CodReg", "DatPubDoc", "DscLink"])
    return {"eom": eom, "agente": agente, "equipamento": equipamento, "manobra": manobra, "linha": linha, "geral": geral,
            "resolucao": resolucao}


def _conf(cc, cid, texto):
    return evm.trecho_confirmado(texto, cc["categorias"][cid]["_re"], cc["verbos"])


def test_texto_confirma_so_com_verbo_de_fornecimento_seguido_do_equipamento(cc):
    assert _conf(cc, "transformador_potencia", "Reforço na SE X: Substituição do TR2 230/69 kV - 33 MVA por dois TRs de 100 MVA")
    assert _conf(cc, "transformador_potencia", "Instalação do 3º ATF 230/138 kV")
    assert _conf(cc, "reator", "Instalação do 1º Banco de Reatores de Barra")
    assert _conf(cc, "banco_capacitores", "Substituição do BC1 500 kV, 390MVAr, por outro de 543MVAr")
    # sem verbo de fornecimento, não confirma
    assert _conf(cc, "compensador", "Reforma do Compensador Síncrono para reestabelecer a vida útil") is None
    assert _conf(cc, "transformador_potencia", "Melhoria na SE Y: revitalização do transformador conversor 7197219") is None
    # nome de arranjo não é compra de disjuntor
    assert _conf(cc, "disjuntor", "Instalar, na SE Z, um módulo geral MG1, em 525 kV, arranjo Disjuntor e Meio.") is None
    assert _conf(cc, "disjuntor", "Instalar, na SE Z, um módulo de conexão com disjuntor, em 500kV")
    # transformador de corrente é transformador de instrumento, não de potência
    assert _conf(cc, "transformador_potencia", "Substituição dos transformadores de corrente da SE W") is None
    assert _conf(cc, "transformador_instrumento", "Substituição dos transformadores de corrente da SE W")


def test_evidencias_separam_confirmado_inferencia_e_nao_verificado(t, cats):
    ev = evm.evidencias(t, cats)
    get = lambda i, c: set(ev[(ev.id_aneel == i) & (ev.categoria == c)].nivel)
    assert get("1", "transformador_potencia") == {"confirmado", "nao_verificado"}  # texto confirma; módulo em adequação não
    assert set(ev[(ev.id_aneel == "1") & (ev.nivel == "confirmado")].origem) == {"texto"}
    assert "confirmado" in get("2", "banco_capacitores")
    assert get("2", "disjuntor") == {"inferencia_tecnica"} and get("2", "para_raios") == {"inferencia_tecnica"}
    assert "confirmado" not in set(ev[ev.id_aneel == "3"].nivel)  # revitalização sem troca
    kv = ev[(ev.id_aneel == "1") & (ev.origem == "texto")].tensao_kv.dropna()
    assert (kv == 230).all() and len(kv)


def test_score_explicavel_janela_teto_de_inferencia_e_pendencia(t, cats):
    perfil = it.carregar_perfil()
    emp, ev = sg.empreendimentos(t), evm.evidencias(t, cats)
    op = scoring.oportunidades(emp, ev, cats, perfil, hoje=HOJE, data_fonte=pd.Timestamp("2026-11-02")).set_index("id_aneel")
    assert "3" not in op.index        # nada do perfil confirmado nem inferido para revitalização
    assert "4" not in op.index        # operação em 2 meses: fora da janela de 6
    assert op.loc["5", "nivel_evidencia"] == "inferência técnica" and op.loc["5", "score"] <= scoring.TETO_INFERENCIA
    assert op.loc["5", "c_estagio"] <= scoring.ESTAGIO_PENDENCIA and "pendência" in op.loc["5", "explicacao_score"]
    assert op.loc["2", "nivel_evidencia"] == "confirmado" and 0 <= op.loc["2", "score"] <= 100
    assert op.loc["1", "c_evidencia"] == pytest.approx(0.8)  # só texto
    for col in ("c_compatibilidade", "c_estagio", "c_evidencia", "c_geografia"):
        assert col in op.columns
    # reproduzível
    pd.testing.assert_frame_equal(op.reset_index(), scoring.oportunidades(emp, ev, cats, perfil, hoje=HOJE,
                                                                          data_fonte=pd.Timestamp("2026-11-02")))


def test_perfil_filtra_por_uf_e_tensao(t, cats):
    emp, ev = sg.empreendimentos(t), evm.evidencias(t, cats)
    base = it.carregar_perfil()
    so_sp = scoring.oportunidades(emp, ev, cats, dict(base, ufs=["SP"]), hoje=HOJE).set_index("id_aneel")
    assert so_sp.loc["2", "c_geografia"] == 1.0 and so_sp.loc["1", "c_geografia"] == 0.0
    alta = scoring.oportunidades(emp, ev, cats, dict(base, tensao_min_kv=200), hoje=HOJE)
    assert "2" not in set(alta.id_aneel)  # 138 kV fica abaixo do mínimo do perfil
    assert "1" in set(alta.id_aneel)


def test_atualidade_reduz_evidencia_de_fonte_velha(t, cats):
    emp, ev, perfil = sg.empreendimentos(t), evm.evidencias(t, cats), it.carregar_perfil()
    velho = scoring.oportunidades(emp, ev, cats, perfil, hoje=HOJE, data_fonte=HOJE - pd.Timedelta(days=90)).set_index("id_aneel")
    novo = scoring.oportunidades(emp, ev, cats, perfil, hoje=HOJE, data_fonte=HOJE).set_index("id_aneel")
    assert velho.loc["2", "c_evidencia"] == novo.loc["2", "c_evidencia"] / 2


def test_relatorio_separa_fato_de_inferencia_e_atribui_a_fonte(t, cats, tmp_path):
    perfil = it.carregar_perfil()
    emp, ev = sg.empreendimentos(t), evm.evidencias(t, cats)
    op = scoring.oportunidades(emp, ev, cats, perfil, hoje=HOJE)
    out = relatorio.gerar(op, ev, cats, perfil, tmp_path, hoje=HOJE)
    h = out["html"].read_text()
    for frase in ("não é pedido de compra", "O que a fonte afirma", "Inferência técnica", "licença ODbL", "não é probabilidade de venda"):
        assert frase in h
    assert "Confira a situação antes de abordar" in h  # alerta de pendência do caso 5
    assert out["csv"].read_bytes().startswith(b"\xef\xbb\xbf")  # BOM para o Excel
    assert "<script" not in h  # relatório estático


def test_cnpj_completa_zeros_perdidos_pela_fonte():
    assert sg.formatar_cnpj("2998611000104") == "02.998.611/0001-04"
    assert sg.formatar_cnpj("") == ""


def test_regras_concordam_com_avaliacoes_humanas_registradas(cats):
    """Regressão contra avaliacoes/siget_relevancia.csv. Só roda onde os arquivos brutos do SIGET existem (fora do git)."""
    try:
        tt = sg.carregar()
    except FileNotFoundError:
        pytest.skip("arquivos brutos do SIGET não baixados (rode fonte-explorar)")
    lab = pd.read_csv(it.config.ROOT / "avaliacoes" / "siget_relevancia.csv", dtype=str).fillna("")
    ev = evm.evidencias(tt, cats)
    c1 = {"transformador_potencia", "reator", "banco_capacitores", "compensador", "disjuntor", "chave_seccionadora"}
    conf = set(ev[(ev.nivel == "confirmado") & ev.categoria.isin(c1)].id_aneel)
    lab = lab[lab.id_aneel.isin(set(tt["eom"].IdeEpd))]
    concordancia = (lab.id_aneel.isin(conf).map({True: "s", False: "n"}) == lab.c1_equipamento).mean()
    assert concordancia >= 0.95, concordancia
