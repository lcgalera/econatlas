"""Leilões de transmissão (D37). A planilha abaixo é uma FIXTURE sintética no formato da oficial, com nomes inventados."""
import pandas as pd
import pytest
from openpyxl import Workbook

from rotzx import intelligence as it
from rotzx.intelligence import leiloes as lm
from rotzx.intelligence import relatorio
from rotzx.providers import aneel_leiloes as al


@pytest.fixture
def planilha(tmp_path):
    wb = Workbook()
    ws = wb.active
    linhas = [
        ["", "", "EMPREENDIMENTOS", "UF", "Extensão\nKm", "Prazo\n(meses)", "RAP - Receita Anual Permitida", "", "Deságio\n%", "CONCESSIONÁRIA"],
        ["", "", "", "", "", "", "Edital", "Proposta", "", ""],
        # formato antigo: cada linha é uma concorrência, com número e data na coluna 1; deságio em %
        ["CONCORRÊNCIA", "007/1999\n(03/12/1999)", "LT Fictícia Antiga", "SP", "505", "18", "100", "90", "10", "CONSÓRCIO ANTIGO"],
        ["", "", "", "TOTAL", "505", "*****", "100", "90", "10", ""],
        # formato intermediário, com lote não leiloado
        ["LEILÃO nº 013/2013\n(7/11/2013)", "LOTE A", "LT 500KV Fictícia - B", "MG", "85", "36", "200", "150", "25", "TRANSMISSORA FICTÍCIA"],
        ["", "LOTE B", "SE 230/138 kV Fictícia C", "RO", "*****", "*****", "*****", "*****", "*****", "NÃO LEILOADO"],
        # formato recente: deságio em fração; descrição ausente (célula repete o cabeçalho); lote misto
        ["LEILÃO nº 01/2026 - 27/03/2026", "LOTE 1", "LEILÃO nº 01/2026 - 27/03/2026\n1ª ETAPA", "SP", "43", "49", "1000", "500", "0.5", "VENCEDORA UM S.A."],
        ["", "LOTE 2", "SE 500/345 kV Fictícia D - (6+1Res) x 300 MVA", "SP", "0", "42", "1000", "600", "0.4", "VENCEDORA DOIS S.A."],
        ["", "", "", "", "43", "*", "2000", "1100", "45", ""],
        ["LEILÃO nº 04/2026 - 30/10/2026", "LOTE 1", "Continuidade prestação do serviço: -SE 230/69 kV Fictícia E - 2 x 100 MVA; Novas instalações: -LT 230 kV Fictícia F - G, com 95 km; -SE 230/69 kV Fictícia E - 3º Trafo 230/69 kV 100 MVA", "BA", "238", "", "100", "50", "0.5", "VENCEDORA TRÊS S.A."],
        ["", "LOTE 2", "SE Coletora Fictícia - 3 x Compensações Síncronas (-200/+300) Mvar", "RO", "0", "42", "100", "40", "0.6", "VENCEDORA QUATRO S.A."],
    ]
    for l in linhas:
        ws.append(l)
    f = tmp_path / "Resultado_leiloes_transmissao.xlsx"
    wb.save(f)
    return f


def test_planilha_vira_uma_linha_por_lote_nos_tres_formatos(planilha):
    df = al.ler_planilha(planilha).set_index(["leilao", "lote"])
    assert len(df) == 7  # 1 + 2 + 2 + 2 lotes; sem as linhas de TOTAL e de cabeçalho
    assert df.loc[("07/1999", "único"), "data_leilao"] == "1999-12-03"
    assert df.loc[("13/2013", "A"), "data_leilao"] == "2013-11-07"
    assert df.loc[("13/2013", "B"), "situacao"] == "não leiloado" and df.loc[("13/2013", "B"), "vencedor"] == ""
    r = df.loc[("01/2026", "1")]
    assert r.etapa == "1" and r.empreendimento == ""  # a célula só repetia o cabeçalho
    # deságio recalculado das receitas: a fonte usa % no formato antigo e fração no recente
    assert df.loc[("07/1999", "único"), "desagio_pct"] == 10.0 and df.loc[("01/2026", "2"), "desagio_pct"] == 40.0
    assert df.loc[("04/2026", "1"), "prazo_texto"] == "" and pd.isna(df.loc[("04/2026", "1"), "prazo_meses"])


def test_pendentes_usa_o_mapa_conferido_e_marca_ambiguidade(planilha):
    df = al.ler_planilha(planilha)
    mapa = pd.DataFrame([
        {"leilao": "01/2026", "data_leilao": "2026-03-27", "lote": "2", "contrato": "016/2026", "status": "conferido", "evidencia": "nome bate"},
        {"leilao": "01/2026", "data_leilao": "2026-03-27", "lote": "1", "contrato": None, "status": "ambiguo", "evidencia": "dois candidatos"},
    ])
    p = lm.pendentes(df, mapa, pd.Timestamp("2026-11-04")).set_index(["leilao", "lote"])
    assert ("01/2026", "2") not in p.index                         # já tem contrato
    assert p.loc[("01/2026", "1"), "status_contrato"] == "contrato não identificado com segurança"
    assert p.loc[("04/2026", "2"), "status_contrato"] == "sem contrato identificado"
    assert ("13/2013", "A") not in p.index and ("07/1999", "único") not in p.index  # fora da janela de 24 meses
    assert p.loc[("04/2026", "2"), "operacao_estimada"] == "04/2030" and p.loc[("04/2026", "1"), "operacao_estimada"] == ""


def test_prazos_sao_medidos_nas_ligacoes():
    mapa = pd.DataFrame([{"leilao": "04/2025", "data_leilao": "2025-10-31", "lote": "1", "contrato": "001/2026", "status": "conferido", "evidencia": ""},
                         {"leilao": "04/2025", "data_leilao": "2025-10-31", "lote": "2", "contrato": None, "status": "ambiguo", "evidencia": ""}])
    agente = pd.DataFrame({"NumCnaCcd": ["001/2026"], "DatAsnCcd": ["23/02/2026"]})
    p = lm.prazos_observados(mapa, agente)
    assert p["n"] == 1 and p["min"] == p["max"] == 115


def test_evidencias_do_lote_separam_instalacao_nova_de_continuidade():
    cats = it.carregar_categorias()
    novo = lm.evidencias_lote("SE 500/345 kV Fictícia D - (6+1Res) x 300 MVA", cats)
    assert {(e["categoria"], e["nivel"]) for e in novo} >= {("transformador_potencia", "confirmado"), ("para_raios", "inferencia_tecnica")}
    comp = lm.evidencias_lote("SE Coletora Fictícia - 3 x Compensações Síncronas (-200/+300) Mvar", cats)
    assert ("compensador", "confirmado") in {(e["categoria"], e["nivel"]) for e in comp}
    misto = lm.evidencias_lote("Continuidade prestação do serviço: -SE 230/69 kV E - 2 x 100 MVA; Novas instalações: -SE 230/69 kV E - 3º Trafo 230/69 kV 100 MVA", cats)
    niveis = {e["nivel"] for e in misto if e["categoria"] == "transformador_potencia"}
    assert niveis == {"confirmado", "nao_verificado"}  # o novo confirma; o existente fica como não verificado
    so_existente = lm.evidencias_lote("Continuidade prestação do serviço: -SE 230/69 kV E - 2 x 100 MVA", cats)
    assert {e["nivel"] for e in so_existente} == {"nao_verificado"}
    assert lm.evidencias_lote("", cats) == []


def test_relatorio_lista_lotes_sem_contrato_com_ressalvas(planilha, tmp_path):
    df = al.ler_planilha(planilha)
    p = lm.pendentes(df, pd.DataFrame(columns=["leilao", "data_leilao", "lote", "contrato", "status", "evidencia"]), pd.Timestamp("2026-11-04"))
    cats, perfil = it.carregar_categorias(), it.carregar_perfil()
    h = relatorio._secao_leiloes({"pendentes": p, "prazos": {"n": 3, "min": 68, "max": 115, "mediana": 91}}, cats, perfil, tmp_path)
    assert "não pedidos de compra" in h and "estimativa" in h and "de 68 a 115 dias" in h
    assert "descrição ausente na planilha" in h and "não informado" in h
    assert (tmp_path / "leiloes_sem_contrato.csv").exists()
    assert "rotzx leiloes-importar" in relatorio._secao_leiloes(None, cats, perfil)


def test_mapa_conferido_e_valido():
    m = lm.carregar_mapa()
    assert set(m.status) <= {"conferido", "provavel", "ambiguo"}
    assert m[m.status != "ambiguo"].contrato.notna().all() and m.evidencia.str.len().min() > 10
    assert not m.duplicated(["leilao", "data_leilao", "lote"]).any()
