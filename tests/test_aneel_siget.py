"""Visão por empreendimento do SIGET. Os dados abaixo são FIXTURES sintéticas (nomes e números inventados), não registros da ANEEL."""
import pandas as pd
import pytest

from econatlas.providers import aneel_siget as sg


def _df(rows, cols):
    return pd.DataFrame(rows, columns=cols).astype(str)


@pytest.fixture
def tabelas():
    eom_cols = ["IdeCcd", "IdeEpd", "IdeOnsEpd", "NomEpd", "DscEpd", "DscSituacaoEpd", "DatOprComEpd", "DatCaoCgmAtoLgl",
                "DatEfeOprComEpd", "IdeObr", "DscSitObr", "DscTipObr", "IdeMdl"]
    eom = _df([
        # empreendimento 1 (autorização): troca de transformador, em andamento, data futura
        ["10", "1", "T-FIC-1", "SE Fictícia A: troca do TR1", "Substituição do TR1 por 100 MVA", "Em andamento", "30/12/2027", "30/12/2027", "", "100", "Em andamento", "Adequação", "1000"],
        ["10", "1", "T-FIC-1", "SE Fictícia A: troca do TR1", "Substituição do TR1 por 100 MVA", "Em andamento", "30/12/2027", "30/12/2027", "", "101", "Em andamento", "Instalação", "1001"],
        # empreendimento 2 (contrato): LT nova, em andamento, data futura
        ["20", "2", "T-FIC-2", "LT 500 kV Fictícia B", "LT e SE novas", "Em andamento", "31/05/2028", "31/05/2028", "", "200", "Em andamento", "Instalação", "2000"],
        ["20", "2", "T-FIC-2", "LT 500 kV Fictícia B", "LT e SE novas", "Em andamento", "31/05/2028", "31/05/2028", "", "201", "Em andamento", "Instalação", "2001"],
        # empreendimento 3: já em operação (fora da amostra)
        ["20", "3", "T-FIC-3", "SE Fictícia C", "Antiga", "Em Operação", "01/01/2015", "01/01/2015", "02/01/2015", "300", "Em operação", "Instalação", "3000"],
        # empreendimento 4: em andamento, mas data do ato legal no passado (fora da amostra)
        ["10", "4", "T-FIC-4", "SE Fictícia D", "Atrasada", "Em andamento", "01/01/2025", "01/01/2025", "", "400", "Em andamento", "Instalação", "4000"],
    ], eom_cols)
    agente = _df([["10", "Transmissora Fictícia Um", "00000000000191", "001/2001"],
                  ["20", "Transmissora Fictícia Dois", "00000000000272", "002/2024"]],
                 ["IdeCcd", "DscRazaoSocial", "NumCNPJ", "NumCnaCcd"])
    equipamento = _df([["1000", "Transformador de Potência", "230,00", "100.00", "BA"],
                       ["2000", "Reator de Linha", "500,00", "", "MG"],
                       ["3000", "Transformador de Potência", "138,00", "50.00", "SP"],
                       ["4000", "Banco de Capacitores", "69,00", "", "RS"]],
                      ["IdeMdl", "DscTipEqp", "NumTnsMdl", "MdaPotAtvMdlEqp", "SigUFSubestacao"])
    manobra = _df([["1001", "1", "3", "BA"], ["2001", "", "", "BA"]],
                  ["IdeMdl", "QtdDijMdlMno", "QtdChvSccMdlMno", "SigUFSubestacao"])
    linha = _df([["2001", "201", "LT 500 kV FICTICIA B /C", "500,00", "MG", "BA"]],
                ["IdeMdl", "IdeObr", "NomLinTms", "NumTensaoBaseLinhaTransm", "SigUFSubestacaoOrigem", "SigUFSubestacaoDestino"])
    geral = _df([], ["IdeMdl", "SigUFSubestacao"])
    resolucao = _df([["1", "REA-2024-1", "2024-03-01", "http://exemplo.invalido/REA20241"],
                     ["1", "REA-2025-2", "2025-06-01", "http://exemplo.invalido/REA20252"],
                     ["4", "DSP-2023-9", "2023-01-01", "http://exemplo.invalido/DSP20239"]],
                    ["IdeEpd", "CodReg", "DatPubDoc", "DscLink"])
    return {"eom": eom, "agente": agente, "equipamento": equipamento, "manobra": manobra,
            "linha": linha, "geral": geral, "resolucao": resolucao}


def test_numero_e_data_aceitam_os_formatos_da_fonte():
    assert sg.numero(pd.Series(["500,00", "150.00", "1.234,56", ""])).tolist()[:3] == [500.0, 150.0, 1234.56]
    d = sg.data(pd.Series(["30/12/2027", "2025-06-01 00:00:00", ""]))
    assert d[0] == pd.Timestamp("2027-12-30") and d[1] == pd.Timestamp("2025-06-01") and pd.isna(d[2])


def test_empreendimentos_uma_linha_por_empreendimento_com_o_que_a_fonte_afirma(tabelas):
    emp = sg.empreendimentos(tabelas).set_index("id_aneel")
    assert list(emp.index) == ["1", "2", "3", "4"]
    a = emp.loc["1"]
    assert a.concessionaria == "Transmissora Fictícia Um" and a.cnpj == "00.000.000/0001-91"  # formatado (formatar_cnpj)
    assert a.origem == "autorização (resolução/despacho)"
    assert a.ato == "REA-2025-2" and a.ato_link.endswith("REA20252")  # o ato mais recente
    assert a.equipamentos == "Transformador de Potência 230 kV 100 MVA [Adequação]" and a.n_equipamentos == 1
    assert a.n_modulos_manobra == 1 and a.disjuntores_declarados == 1 and a.seccionadoras_declaradas == 3
    b = emp.loc["2"]
    assert b.origem == "contrato de concessão" and b.ato == ""
    assert b.ufs == "BA,MG" and b.linhas == "LT 500 kV FICTICIA B /C (500 kV)"
    assert b.equipamentos == "Reator de Linha 500 kV [Instalação]"  # sem potência declarada: não inventa
    # equipamento de obra já em operação não entra como equipamento de obra em andamento
    assert emp.loc["3"].n_equipamentos == 0


def test_amostra_segue_a_regra_documentada(tabelas):
    emp = sg.empreendimentos(tabelas)
    am = sg.amostra(emp, n=20, hoje=pd.Timestamp("2026-11-04"))
    # só em andamento, com data futura e equipamento ligado a obra em andamento
    assert sorted(am.id_aneel) == ["1", "2"]
    assert set(am.origem) == {"autorização (resolução/despacho)", "contrato de concessão"}
    assert (am.avaliacao_relevante == "").all()  # a avaliação é humana
    # reproduzível
    pd.testing.assert_frame_equal(am, sg.amostra(emp, n=20, hoje=pd.Timestamp("2026-11-04")))


def test_carregar_exige_os_arquivos_brutos(tmp_path):
    with pytest.raises(FileNotFoundError):
        sg.carregar(tmp_path)


def test_amostra_aleatoria_reproduzivel_exclui_avaliados_e_calcula_c2_c3(tabelas):
    emp = sg.empreendimentos(tabelas)
    hoje = pd.Timestamp("2026-11-04")
    a = sg.amostra_aleatoria(emp, n=5, semente=1, hoje=hoje)
    assert sorted(a.id_aneel) == ["1", "2"]  # só os elegíveis (o universo da fixture tem 2)
    pd.testing.assert_frame_equal(a, sg.amostra_aleatoria(emp, n=5, semente=1, hoje=hoje))
    assert set(sg.amostra_aleatoria(emp, n=5, semente=1, hoje=hoje, excluir={"1"}).id_aneel) == {"2"}
    r = a.set_index("id_aneel")
    assert r.loc["1", "c2_janela"] == "s" and r.loc["1", "c3_comprador"] == "s"  # 30/12/2027: > 6 meses
    assert (a.c1_equipamento == "").all()  # a condição 1 é humana
    # perto da data: falha na janela
    perto = sg.amostra_aleatoria(emp, n=5, semente=1, hoje=pd.Timestamp("2027-08-01")).set_index("id_aneel")
    assert perto.loc["1", "c2_janela"] == "n"


def test_planilha_tem_formula_de_resultado_e_resumo(tabelas, tmp_path):
    from openpyxl import load_workbook
    a = sg.amostra_aleatoria(sg.empreendimentos(tabelas), n=5, semente=1, hoje=pd.Timestamp("2026-11-04"))
    wb = load_workbook(sg.planilha_avaliacao(a, tmp_path / "av.xlsx"))
    ws = wb["Amostra"]
    assert ws["A1"].value.startswith("C1") and ws["A2"].value in (None, "")
    assert ws["B2"].value.startswith('=IF(A2=""') and 'C2="n"' in ws["B2"].value and 'D2="n"' in ws["B2"].value
    assert wb["Resumo"]["B6"].value.startswith("=IF(B3+B4=0")
    assert "ODbL" in str(wb["Como avaliar"]["A9"].value)
    # "?" é curinga no COUNTIF: a contagem dos "?" precisa do escape "~?"
    assert wb["Resumo"]["B5"].value == '=COUNTIF(Amostra!B2:B3,"~?")'  # 2 linhas na fixture
