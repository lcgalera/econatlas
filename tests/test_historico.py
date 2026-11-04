"""Histórico do radar (Fase 2). Empreendimentos FICTÍCIOS, montados à mão; não são dados da ANEEL."""
import sqlite3
from datetime import datetime, timezone

import pandas as pd
import pytest

from econatlas.intelligence import historico, relatorio
from econatlas.providers import aneel_siget as sg


def _emp(linhas, fontes):
    cols = ["id_aneel", "id_ons", "nome", "situacao", "operacao_ato_legal", "conclusao_ato_legal", "operacao_efetiva",
            "concessionaria", "contrato", "n_obras", "n_obras_em_andamento", "equipamentos", "ato"]
    df = pd.DataFrame(linhas, columns=cols).astype(str)
    df.attrs["fontes"] = fontes
    return df


V1 = [["1", "T-1", "SE A", "Em andamento", "30/12/2027", "30/12/2027", "", "Fictícia", "001/2001", "1", "1", "TR 230 kV", "REA-1"],
      ["2", "T-2", "SE B", "Em andamento", "31/05/2028", "31/05/2028", "", "Fictícia", "001/2001", "2", "2", "Reator 500 kV", ""],
      ["3", "T-3", "SE C", "Em andamento", "31/01/2027", "31/01/2027", "", "Fictícia", "001/2001", "1", "1", "", ""]]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    historico.ensure_schema(c)
    return c


def test_primeira_coleta_e_linha_de_base_e_repetir_nao_grava(conn):
    r = historico.registrar(conn, _emp(V1, {"eom": "aaa_eom.csv"}))
    assert r["status"] == "linha_de_base" and r["eventos"] == 0
    assert historico.registrar(conn, _emp(V1, {"eom": "aaa_eom.csv"}))["status"] == "sem_alteracao"
    assert conn.execute("SELECT COUNT(*) FROM siget_coletas").fetchone()[0] == 1
    ev = historico.eventos(conn)
    assert ev.empty and ev.attrs["anterior_em"] is None


def test_eventos_novo_mudanca_e_saida(conn):
    historico.registrar(conn, _emp(V1, {"eom": "aaa_eom.csv"}), agora=datetime(2026, 11, 4, tzinfo=timezone.utc))
    v2 = [list(x) for x in V1[:2]]
    v2[0][4] = "30/06/2028"        # data do ato legal adiada
    v2[1][3] = "Em Operação"       # entrou em operação
    v2.append(["4", "T-4", "SE D", "Em andamento", "30/12/2029", "30/12/2029", "", "Nova Fictícia", "002/2026", "1", "1", "Capacitor 138 kV", ""])
    r = historico.registrar(conn, _emp(v2, {"eom": "bbb_eom.csv"}), agora=datetime(2026, 11, 18, tzinfo=timezone.utc))
    assert r["status"] == "nova_coleta"
    ev = historico.eventos(conn)
    got = {(e.id_aneel, e.tipo, e.campo or "", e.antes or "", e.depois or "") for e in ev.itertuples()}
    assert ("1", "mudou", "operacao_ato_legal", "30/12/2027", "30/06/2028") in got
    assert ("2", "mudou", "situacao", "Em andamento", "Em Operação") in got
    assert ("4", "novo", "", "", "Em andamento") in got
    assert ("3", "saiu_da_fonte", "", "Em andamento", "") in got
    assert len(ev) == 4  # nada além do que mudou
    assert ev.attrs["anterior_em"].startswith("2026-11-04") and ev.attrs["coletado_em"].startswith("2026-11-18")


def test_historico_so_aceita_acrescimos(conn):
    historico.registrar(conn, _emp(V1, {"eom": "aaa_eom.csv"}))
    v2 = [list(x) for x in V1]
    v2[0][3] = "Concluído"
    historico.registrar(conn, _emp(v2, {"eom": "bbb_eom.csv"}))  # gatilho de linha só dispara se houver linha: precisa de evento
    assert conn.execute("SELECT COUNT(*) FROM siget_eventos").fetchone()[0] == 1
    for sql in ("UPDATE siget_versoes SET hash = 'x'", "DELETE FROM siget_versoes", "DELETE FROM siget_eventos",
                "UPDATE siget_eventos SET tipo = 'x'"):
        with pytest.raises(sqlite3.DatabaseError, match="só aceita acréscimos"):
            conn.execute(sql)


def test_relatorio_mostra_mudancas_so_a_partir_da_segunda_coleta(conn, tmp_path):
    op = pd.DataFrame({"id_aneel": ["1"], "nome": ["SE A"]})
    assert "O histórico ainda não foi iniciado" in relatorio._secao_mudancas(None, op)
    historico.registrar(conn, _emp(V1, {"eom": "aaa_eom.csv"}))
    assert "linha de base" in relatorio._secao_mudancas(historico.eventos(conn), op)
    v2 = [list(x) for x in V1]
    v2[0][4] = "30/06/2028"
    historico.registrar(conn, _emp(v2, {"eom": "bbb_eom.csv"}))
    h = relatorio._secao_mudancas(historico.eventos(conn), op)
    assert "data de operação (ato legal)" in h and "30/12/2027" in h and "30/06/2028" in h


def test_baixar_pula_arquivo_que_o_portal_nao_atualizou(monkeypatch, tmp_path):
    from econatlas.providers import ckan
    recursos = [{"nome": n, "url": f"https://x/{n}", "modificado": "2026-11-02T05:00:00", "formato": "csv"} for n in sg.ARQUIVOS.values()]
    monkeypatch.setattr(ckan, "conjunto", lambda portal, nome: {"recursos": recursos})
    baixados = []
    monkeypatch.setattr(ckan, "_get", lambda url, tries=4: baixados.append(url) or b"a;b\n1;2\n")
    assert {v["status"] for v in sg.baixar(tmp_path).values()} == {"baixado"}
    n = len(baixados)
    assert {v["status"] for v in sg.baixar(tmp_path).values()} == {"sem_atualizacao"} and len(baixados) == n
    recursos[0]["modificado"] = "2026-11-05T05:00:00"  # o portal atualizou um arquivo
    r = sg.baixar(tmp_path)
    assert r["eom"]["status"] == "mesmo_conteudo" and len(baixados) == n + 1


def test_csv_ida_e_volta_preserva_o_historico_e_so_acrescenta(conn, tmp_path):
    historico.registrar(conn, _emp(V1, {"eom": "aaa_eom.csv"}))
    historico.exportar(conn, tmp_path)
    # banco novo (como no GitHub Actions): importa e compara a próxima coleta com o estado salvo
    novo = sqlite3.connect(":memory:")
    assert historico.importar(novo, tmp_path)["status"] == "importado"
    assert historico.registrar(novo, _emp(V1, {"eom": "aaa_eom.csv"}))["status"] == "sem_alteracao"
    v2 = [list(x) for x in V1]
    v2[2][3] = "Concluído"
    r = historico.registrar(novo, _emp(v2, {"eom": "ccc_eom.csv"}))
    assert r["status"] == "nova_coleta" and r["eventos"] == 1
    antes = (tmp_path / "siget_coletas.csv").read_bytes()
    out = historico.exportar(novo, tmp_path)
    assert out["coletas"] == 1 and out["eventos"] == 1
    assert (tmp_path / "siget_coletas.csv").read_bytes().startswith(antes)  # linhas antigas byte a byte
    est = pd.read_csv(tmp_path / "siget_estado.csv", dtype=str)
    assert set(est.coleta_id) == {"2"} and est.set_index("id_aneel").loc["3", "situacao"] == "Concluído"
    # alguém editou uma linha antiga do CSV: a exportação recusa
    ev = (tmp_path / "siget_eventos.csv").read_text().replace("Concluído", "Cancelado")
    (tmp_path / "siget_eventos.csv").write_text(ev)
    with pytest.raises(historico.HistoricoAlterado):
        historico.exportar(novo, tmp_path)


def test_importar_nao_mexe_em_banco_que_ja_tem_historico(conn, tmp_path):
    historico.registrar(conn, _emp(V1, {"eom": "aaa_eom.csv"}))
    historico.exportar(conn, tmp_path)
    assert historico.importar(conn, tmp_path)["status"] == "banco_ja_tem_historico"
    assert historico.importar(sqlite3.connect(":memory:"), tmp_path / "vazio")["status"] == "sem_historico"
