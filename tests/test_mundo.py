"""O mundo visto do Brasil (D38). Respostas das APIs abaixo são FIXTURES sintéticas no formato real, com valores inventados."""
import json

import pytest

from rotzx.mundo import bancomundial, build, comex, gdelt
from rotzx.mundo.paises import PAISES, POR_ISO_NUM


def test_tabela_de_paises_completa_e_sem_repeticao():
    assert len(PAISES) == 21 and POR_ISO_NUM["076"]["nome"] == "Brasil"
    for chave in ("iso_num", "iso3", "comex", "nome"):
        assert len({p[chave] for p in PAISES}) == 21, chave
    assert all(p["termos"] and p["artigo"] in ("o", "a", "os") for p in PAISES)


def test_manchete_precisa_citar_o_pais_com_acento_e_palavra_inteira():
    termos = POR_ISO_NUM["250"]["termos"]  # França
    assert gdelt.menciona("Macron visita o Brasil", termos)
    assert gdelt.menciona("França anuncia nova tarifa", termos)
    assert not gdelt.menciona("Prefeitura de Franca (SP) inaugura escola", termos)  # sem acento é a cidade de SP
    assert not gdelt.menciona("Chinesas e franceses", POR_ISO_NUM["156"]["termos"][:1])  # "china" não casa dentro de outra palavra
    assert gdelt.menciona("Rússia e EUA discutem cessar-fogo", POR_ISO_NUM["840"]["termos"])


def test_categorias_por_palavras_chave():
    assert gdelt.categorias("Inflação na Argentina desacelera") == ["economia"]
    assert set(gdelt.categorias("Guerra eleva preço do petróleo nos mercados")) >= {"economia", "geopolitica", "afeta_o_mundo"}
    assert gdelt.categorias("Presidente vence eleição") == ["politica"]
    assert gdelt.categorias("Time vence o clássico") == []


def test_manchetes_filtram_repeticao_e_pais(monkeypatch):
    artigos = {"articles": [
        {"title": "China compra mais soja do Brasil", "url": "https://x/1", "domain": "x.com", "seendate": "20261104T100000Z", "sourcecountry": "Brazil"},
        {"title": "China compra mais soja do Brasil", "url": "https://y/1", "domain": "y.com", "seendate": "20261104T090000Z"},
        {"title": "Futebol: resultado da rodada", "url": "https://z/1", "domain": "z.com", "seendate": "20261104T080000Z"},
    ]}
    monkeypatch.setattr(gdelt, "_get", lambda params, tentativas=4: artigos)
    m = gdelt.manchetes(POR_ISO_NUM["156"]["termos"])
    assert [x["url"] for x in m] == ["https://x/1"]
    assert m[0]["data"] == "20261104" and m[0]["categorias"] == ["economia"] and m[0]["veiculo"] == "x.com"


def test_filtro_do_comex_no_formato_aceito_pela_api():
    f = comex._filtro("2025", "importacao", "noSh4pt", "160")
    assert f["typeForm"] == 2 and f["yearStart"] == f["yearEnd"] == "2025"
    assert f["filterArray"] == [{"item": ["160"], "idInput": "noPaispt"}] and f["detailDatabase"][0]["id"] == "noSh4pt"
    assert comex._filtro("2025", "exportacao", "noPaispt")["filterList"] == []


def test_produtos_do_comex_com_participacao(monkeypatch):
    lista = [{"coSh4": "1201", "noSh4pt": "Soja", "vlFob": "60"}, {"coSh4": "2601", "noSh4pt": "Minério", "vlFob": "30"},
             {"coSh4": "0202", "noSh4pt": "Carne", "vlFob": "10"}]
    monkeypatch.setattr(comex, "_get", lambda filtro, pasta=None, tentativas=5: lista)
    p = comex.produtos("2025", "exportacao", "160", top=2)
    assert [x["sh4"] for x in p] == ["1201", "2601"] and p[0]["participacao"] == pytest.approx(0.6)


def test_banco_mundial_pega_o_valor_mais_recente_nao_nulo(monkeypatch):
    resp = [{"lastupdated": "2026-10-08"}, [
        {"countryiso3code": "CHN", "date": "2025", "value": None},
        {"countryiso3code": "CHN", "date": "2024", "value": 5.0},
        {"countryiso3code": "CHN", "date": "2023", "value": 5.2}]]
    monkeypatch.setattr(bancomundial, "_get", lambda url, tentativas=4: resp)
    r = bancomundial.indicadores(["CHN"])
    assert r["CHN"]["NY.GDP.MKTP.KD.ZG"] == {"valor": 5.0, "ano": "2024", "atualizado": "2026-10-08"}


def test_resumo_so_com_fatos_e_concordancia():
    c = {"exportacao": {"fob": 99.9e9, "participacao": 0.287, "posicao": 1},
         "importacao": {"fob": 70.9e9, "participacao": 0.253, "posicao": 1}, "saldo": 29.0e9}
    r = build.resumo("China", c, "2025", "a")
    assert r == ("Em 2025, a China foi o 1º destino das exportações brasileiras: US$ 99,9 bi, 28,7% do total. "
                 "O Brasil importou US$ 70,9 bi da China (1º fornecedor, 25,3% do total). "
                 "Superávit brasileiro de US$ 29,0 bi no comércio com a China.")
    r = build.resumo("Estados Unidos", dict(c, saldo=-7.5e9), "2025", "os")
    assert "os Estados Unidos foram" in r and "dos Estados Unidos" in r and "Déficit brasileiro de US$ 7,5 bi" in r
    for palavra in ("deve", "vai", "porque", "portanto"):
        assert palavra not in r.lower().split()


def test_nome_de_produto_cortado_em_palavra_inteira():
    nome = "Barcos-faróis, barcos-bombas, dragas, guindastes flutuantes e outras embarcações e plataformas flutuantes"
    curto = build._curto(nome)
    assert curto.endswith("…") and len(curto) <= 71 and not curto[:-1].endswith(" ")
    assert build._curto("Soja, mesmo triturada") == "Soja, mesmo triturada"


def test_dados_gravados_tambem_como_script(tmp_path):
    build._gravar(tmp_path, "mundo", {"a": "ç"})
    assert json.loads((tmp_path / "mundo.json").read_text(encoding="utf-8")) == {"a": "ç"}
    js = (tmp_path / "mundo.js").read_text(encoding="utf-8")
    assert js.startswith("window.MUNDO = ") and json.loads(js[len("window.MUNDO = "):].rstrip().rstrip(";")) == {"a": "ç"}


def test_resposta_que_nao_e_json_e_falha_e_nao_lista_vazia(monkeypatch):
    class R:
        def __init__(self, corpo): self.corpo = corpo
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return self.corpo
    monkeypatch.setattr(gdelt, "INTERVALO", 0)
    monkeypatch.setattr(gdelt.time, "sleep", lambda s: None)
    monkeypatch.setattr(gdelt.urllib.request, "urlopen", lambda req, timeout=60: R(b"Please limit requests to one every 5 seconds"))
    with pytest.raises(gdelt.LimiteGDELT):
        gdelt.manchetes(["china"])


def test_lote_distribui_manchetes_pelo_pais_citado_no_titulo(monkeypatch):
    artigos = {"articles": [
        {"title": "China e Argentina fecham acordo de comércio", "url": "u1", "domain": "a.com", "seendate": "20261104T1"},
        {"title": "Argentina anuncia inflação de outubro", "url": "u2", "domain": "b.com", "seendate": "20261104T2"},
        {"title": "Notícia que só cita a China no corpo", "url": "u3", "domain": "c.com", "seendate": "20261104T3"},
    ]}
    monkeypatch.setattr(gdelt, "_get", lambda params, tentativas=3: artigos)
    r = gdelt.lote([POR_ISO_NUM["156"], POR_ISO_NUM["032"]])
    assert [m["url"] for m in r["156"]] == ["u1", "u3"] and [m["url"] for m in r["032"]] == ["u1", "u2"]


def test_juntar_acumula_sem_repetir_e_descarta_antigas():
    antigas = [{"titulo": "A", "data": "20261101"}, {"titulo": "B", "data": "20261020"}]
    novas = [{"titulo": "a", "data": "20261104"}, {"titulo": "C", "data": "20261103"}]
    j = gdelt.juntar(antigas, novas, desde="20261028")
    assert [m["titulo"] for m in j] == ["a", "C"]  # "A" repetida (mesmo título) e "B" antiga demais


def test_noticias_mantem_as_anteriores_quando_a_consulta_falha(monkeypatch, tmp_path):
    (tmp_path / "noticias.json").write_text(json.dumps({"paises": {"156": [{"titulo": "China cresce", "data": "29991231"}]}, "mundo": []}))
    def falha(*a, **k): raise gdelt.LimiteGDELT("Please limit requests")
    monkeypatch.setattr(gdelt, "lote", falha)
    monkeypatch.setattr(gdelt, "manchetes", falha)
    n = build.noticias(tmp_path, log=lambda *a: None)
    assert n["paises"]["156"] == [{"titulo": "China cresce", "data": "29991231"}]
    assert "156" in n["falhas"] and "mundo" in n["falhas"]
