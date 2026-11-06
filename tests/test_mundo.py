"""O mundo visto do Brasil (D38). Respostas das APIs abaixo são FIXTURES sintéticas no formato real, com valores inventados."""
import json

import pytest

from rotzx.mundo import bancomundial, build, comex, conflitos, gdelt, omc, onu
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
    # manchetes reais de 04/11/2026: "ações" dentro de outra palavra não é economia
    assert gdelt.categorias("Milei compartilha publicações sobre 'interferência estrangeira' após visita de Janones à Argentina") == []
    c = gdelt.categorias("Rússia lança ataque com centenas de drones e mísseis contra rede elétrica da Ucrânia às vésperas de negociações de paz")
    assert c == ["geopolitica"]
    assert gdelt.categorias("Bolsa sobe e ações da Petrobras disparam") == ["economia"]
    assert gdelt.categorias("Eleições nos EUA: Mississippi tem disputa acirrada pelo Senado com menos de 100 votos de diferença") == ["politica"]
    assert gdelt.categorias("Prefeitos voluntários administram milhares de cidades") == []          # "administram" não é "ministro"
    assert "economia" in gdelt.categorias("Custo de vida e guerra no Irã: as 9 preocupações dos eleitores")
    assert "geopolitica" in gdelt.categorias("Irã lança míssil contra base")


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


def test_noticias_mantem_as_anteriores_quando_as_fontes_falham(monkeypatch, tmp_path):
    from rotzx.mundo import rss
    (tmp_path / "noticias.json").write_text(json.dumps({"paises": {"156": [{"titulo": "China cresce", "data": "29991231"}]},
                                                       "mundo": [{"titulo": "Cúpula global", "data": "29991231"}]}))
    def falha(*a, **k): raise gdelt.LimiteGDELT("Please limit requests")
    monkeypatch.setattr(rss, "coletar", lambda: ([], {"Feed X": "OSError: recusado"}))
    monkeypatch.setattr(gdelt, "lote", falha)
    n = build.noticias(tmp_path, log=lambda *a: None)
    so = lambda l: [(m["titulo"], m["data"]) for m in l]
    assert so(n["paises"]["156"]) == [("China cresce", "29991231")]
    assert so(n["mundo"]) == [("Cúpula global", "29991231")] and n["mundo"][0]["categorias"] == ["afeta_o_mundo"]  # recalculadas
    assert "rss:Feed X" in n["falhas"] and "gdelt_lote_1" in n["falhas"]

RSS = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Feed</title>
<item><title>China anuncia compra recorde de soja</title><link>https://exemplo.invalido/1</link><pubDate>Wed, 04 Nov 2026 10:00:00 -0300</pubDate></item>
<item><title>  Guerra   eleva tensão na fronteira </title><link>https://exemplo.invalido/2</link><pubDate>data ruim</pubDate></item>
<item><title>Sem link</title></item>
</channel></rss>""".encode("utf-8")
ATOM = """<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>A</title>
<entry><title>Argentina reduz juros</title><link href="https://exemplo.invalido/3"/><updated>2026-11-03T08:00:00Z</updated></entry></feed>""".encode("utf-8")


def test_rss_e_atom_viram_manchetes_com_data_e_categoria():
    from rotzx.mundo import rss
    r = rss.ler(RSS, "Veículo X")
    assert [m["url"] for m in r] == ["https://exemplo.invalido/1", "https://exemplo.invalido/2"]  # item sem link fica de fora
    assert r[0]["data"] == "20261104" and r[0]["categorias"] == ["economia"] and r[0]["veiculo"] == "Veículo X"
    assert r[1]["titulo"] == "Guerra eleva tensão na fronteira" and r[1]["data"] == "" and "geopolitica" in r[1]["categorias"]
    a = rss.ler(ATOM, "Y")
    assert a[0]["url"] == "https://exemplo.invalido/3" and a[0]["data"] == "20261103"


def test_feed_que_falha_nao_derruba_os_outros(monkeypatch):
    from rotzx.mundo import rss

    class R:
        def __init__(self, c): self.c = c
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return self.c

    def abrir(req, timeout=30):
        if "quebrado" in req.full_url:
            raise OSError("conexão recusada")
        return R(RSS)
    monkeypatch.setattr(rss.urllib.request, "urlopen", abrir)
    itens, falhas = rss.coletar([("Bom", "https://bom.invalido/rss"), ("Ruim", "https://quebrado.invalido/rss")], pausa=0)
    assert len(itens) == 2 and list(falhas) == ["Ruim"]


def test_noticias_combinam_rss_e_mantem_historico(monkeypatch, tmp_path):
    from rotzx.mundo import rss
    monkeypatch.setattr(rss, "coletar", lambda: (rss.ler(RSS, "X"), {"Ruim": "OSError"}))
    n = build.noticias(tmp_path, log=lambda *a: None, usar_gdelt=False)
    assert [m["titulo"] for m in n["paises"]["156"]] == ["China anuncia compra recorde de soja"]
    assert n["falhas"] == {"rss:Ruim": "OSError"} and n["diagnostico"]["rss_itens"] == 2
    assert (tmp_path / "noticias.js").exists()


# ---- D42: votos na ONU e disputas na OMC (fixtures sintéticas no formato real) ----

def test_onu_escolhe_arquivos_da_versao_mais_recente():
    meta = {"data": {"latestVersion": {"versionNumber": 39, "releaseTime": "2026-07-30T15:57:56Z", "files": [
        {"dataFile": {"id": 10, "filename": "IdealpointestimatesAll_Jun2024.csv"}},
        {"dataFile": {"id": 20, "filename": "IdealpointestimatesFP_2026FP.csv"}},
        {"dataFile": {"id": 15, "filename": "AgreementScores.csv"}},
        {"dataFile": {"id": 11, "filename": "AgreementScoresAll_Jun2024.csv"}}]}}}
    a = onu.arquivos(meta)
    assert a["concordancia"]["id"] == 15 and a["ideal"]["id"] == 20 and a["publicado"] == "2026-07-30"
    with pytest.raises(ValueError):
        onu.arquivos({"data": {"latestVersion": {"files": []}}})


def test_onu_concordancia_com_o_brasil_media_e_posicao(tmp_path):
    ideal = tmp_path / "ideal.csv"
    ideal.write_text('"","ccode","iso3c","year"\n"1",140,"BRA",2024\n"2",2,"USA",2024\n"3",160,"ARG",2024\n"4",710,"CHN",2024\n"5",999,"NA",2024\n')
    agree = tmp_path / "agree.csv"
    linhas = ['"","session.x","ccode1","ccode2","agree","year"']
    for i, (a, b, v, ano) in enumerate([(140, 2, 0.4, 2023), (140, 2, 0.3, 2024), (2, 140, 0.3, 2024), (140, 160, 0.9, 2024),
                                        (140, 160, 0.7, 2023), (140, 710, 0.8, 2024), (140, 999, 0.99, 2024), (140, 710, "NA", 2023)]):
        linhas.append(f'"{i}",1,{a},{b},{v},{ano}')
    agree.write_text("\n".join(linhas) + "\n")
    conc = onu.concordancias(agree, onu.cow_para_iso3(ideal))
    assert conc["USA"] == {2023: 0.4, 2024: 0.3} and 2023 not in conc["CHN"] and "NA" not in conc
    r = onu.resumir(conc, ["USA", "ARG", "CHN", "PRY"])
    assert r["ano"] == 2024 and "PRY" not in r["paises"]
    assert r["paises"]["ARG"] == {"concordancia": 0.9, "media": 0.8, "anos_media": "2020–2024", "posicao": 1, "de": 3}
    assert r["paises"]["USA"]["posicao"] == 3 and r["paises"]["USA"]["media"] == 0.35


OMC_JS = '''var ds_array = new Array();
ds_array[1] = {
    code: "DS1", title: "Measures Affecting &ldquo;Things&rdquo;", origin: "BRA", destination: "USA",
    start_date: "2001/01/02", subject: "G1", status: "ST1#2001_01_02|ST31#2003_05_06", third_party: ""
};
ds_array[2] = {
    code: "DS2", title: "Tariffs on Brazil", origin: "USA", destination: "BRA",
    start_date: "2025/08/05", status: "ST1#2025_08_05"
};
ds_array[3] = {
    code: "DS3", title: "Steel", origin: "CHN#BRA", destination: "EEC",
    start_date: "2023/03/01", status: "ST3#2024_01_01"
};
ds_array[4] = {
    code: "DS4", title: "Solar", origin: "CHN", destination: "USA",
    start_date: "2024/04/01", status: "ST99#2024_04_01"
};
ds_array[5] = { code: "XX", title: "ignorar" };
'''


def test_omc_le_casos_sem_executar_javascript():
    c = omc.ler_casos(OMC_JS)
    assert [x["ds"] for x in c] == ["DS1", "DS2", "DS3", "DS4"]
    assert c[0]["titulo"] == "Measures Affecting “Things”"            # entidades HTML decodificadas
    assert c[0]["situacao"] == "encerrada (acordo)" and c[0]["encerrada"]      # vale a última situação
    assert c[0]["situacao_data"] == "2003-05-06" and c[0]["url"].endswith("/ds1_e.htm")
    assert c[2]["reclamantes"] == ["CHN", "BRA"] and c[3]["situacao"] == "ST99"  # código desconhecido aparece cru


def test_omc_disputas_com_o_brasil_ue_e_visao_externa():
    r = omc.por_pais(omc.ler_casos(OMC_JS), ["USA", "DEU", "CHN", "BRA"], desde_ano=2021)
    eua = r["USA"]
    assert [x["ds"] for x in eua["com_brasil"]] == ["DS2", "DS1"]              # mais recente primeiro
    assert eua["com_brasil"][0]["lado"] == "reclamante" and eua["com_brasil"][1]["lado"] == "demandado"
    assert eua["recentes_total"] == 1 and eua["contrapartes"] == {"CHN": 1}    # as com o Brasil não se repetem aqui
    assert r["DEU"]["via_ue"] and [x["ds"] for x in r["DEU"]["com_brasil"]] == ["DS3"]
    assert r["CHN"]["com_brasil"] == [] and r["CHN"]["contrapartes"] == {"EEC": 1, "USA": 1}  # co-reclamante não é disputa
    assert r["BRA"]["recentes_total"] == 2 and r["BRA"]["contrapartes"] == {"USA": 1, "EEC": 1}


def test_relacoes_falha_de_uma_fonte_nao_derruba_a_outra(monkeypatch):
    m = {"paises": {"840": {"nome": "Estados Unidos"}}, "fontes": {}}
    monkeypatch.setattr(onu, "alinhamento", lambda *a, **k: (_ for _ in ()).throw(OSError("bloqueado")))
    monkeypatch.setattr(omc, "disputas", lambda iso3: {"USA": {"total": 1}, "XXX": {"total": 9}})
    monkeypatch.setattr(conflitos, "coletar", lambda iso3, pasta=None: {
        "ultimo_ano": 2025, "desde": 2021, "versao": "261", "mundo": {"ativos": [], "total": 0, "guerras": 0},
        "paises": {"USA": {"conflitos": [{"id": "9"}]}}})
    build._relacoes(m, log=lambda *_: None)
    assert m["falhas"]["onu"].startswith("OSError") and "omc" not in m["falhas"] and "conflitos" not in m["falhas"]
    assert m["paises"]["840"]["relacoes"] == {"omc": {"total": 1}, "conflitos": [{"id": "9"}]}
    assert m["conflitos"]["versao"] == "261" and {"onu", "ucdp"} <= set(m["fontes"])


# ---- D43: conflitos armados (UCDP/PRIO), fixture sintética no formato real ----

UCDP_CAB = ("conflict_id,location,side_a,side_a_id,side_a_2nd,side_b,side_b_id,side_b_2nd,incompatibility,territory_name,year,"
            "intensity_level,cumulative_intensity,type_of_conflict,start_date,start_prec,start_date2,start_prec2,ep_end,ep_end_date,"
            "ep_end_prec,gwno_a,gwno_a_2nd,gwno_b,gwno_b_2nd,gwno_loc,region,version")


def _ucdp(*linhas):
    import io as _io, zipfile as _zf
    buf = _io.BytesIO()
    with _zf.ZipFile(buf, "w") as z:
        z.writestr("UcdpPrioConflict_v26_1.csv", "\n".join((UCDP_CAB,) + linhas) + "\n")
    return buf.getvalue()


def test_ucdp_escolhe_a_versao_mais_recente_da_pagina():
    html = ('<a href="https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-251-csv.zip">'
            '<a href="https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-csv.zip">'
            '<a href="https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-xlsx.zip">')
    assert conflitos.link_mais_recente(html).endswith("acd-261-csv.zip")
    with pytest.raises(ValueError):
        conflitos.link_mais_recente("<html></html>")


def test_ucdp_conflitos_por_pais_papel_e_panorama():
    linhas = conflitos.ler(_ucdp(
        '1,"Russia (Soviet Union), Ukraine",Government of Russia (Soviet Union),57,"",Government of Ukraine,169,"",3,Crimea,2025,2,1,2,2022-02-24,1,,,0,,,365,"",369,"","365, 369",1,26.1',
        '2,Colombia,Government of Colombia,1,"",ELN,2,"",2,"",2024,1,1,3,1964-01-01,1,,,0,,,100,"","","",100,5,26.1',
        # missão multinacional: 7 países apoiando o governo; o Brasil está entre eles em 2023, não em 2025
        '3,Central African Republic,Government of Central African Republic,3,"Government of Brazil, Government of China, Government of A, Government of B, Government of C, Government of D, Government of E",CPC,4,"",2,"",2023,1,1,4,2020-12-01,1,,,0,,,482,"140, 710, 1, 3, 4, 5, 6","","",482,4,26.1',
        '3,Central African Republic,Government of Central African Republic,3,"Government of China",CPC,4,"",2,"",2025,1,1,4,2020-12-01,1,,,0,,,482,"710","","",482,4,26.1',
        '4,Peru,Government of Peru,5,"",Sendero Luminoso,6,"",2,"",2019,1,1,3,1980-01-01,1,,,0,,,135,"","","",135,5,26.1',  # fora da janela
    ))
    r = conflitos.resumir(linhas, ["RUS", "BRA", "CHN", "COL", "CHL"])
    assert r["ultimo_ano"] == 2025 and r["desde"] == 2021
    rus = r["paises"]["RUS"]["conflitos"][0]
    assert rus["papel"] == "lado principal" and rus["tipo"] == "entre Estados" and rus["disputa"] == "território e governo"
    assert rus["guerra_no_ultimo_ano"] and rus["url"].endswith("/conflict/1")
    bra = r["paises"]["BRA"]["conflitos"]
    assert len(bra) == 1 and bra[0]["papel"] == "apoio com tropas" and bra[0]["anos_pais"] == [2023]   # vale o ano em que participou
    assert bra[0]["apoiadores_no_lado"] == 7 and bra[0]["apoia"] == ["Government of Central African Republic"]
    assert r["paises"]["CHN"]["conflitos"][0]["anos_pais"] == [2023, 2025]
    assert r["paises"]["COL"]["conflitos"][0]["ultimo_ano"] == 2024 and r["paises"]["CHL"]["conflitos"] == []
    assert r["mundo"]["total"] == 2 and r["mundo"]["guerras"] == 1 and r["mundo"]["ativos"][0]["id"] == "1"   # guerra primeiro


# ---- D44: hora de Brasília e países citados em cada manchete ----

def test_rss_hora_em_brasilia_e_sem_fuso_fica_sem_hora():
    from rotzx.mundo import rss
    assert rss._quando("Wed, 04 Nov 2026 01:30:00 GMT") == ("20261103", "22:30")   # vira o dia em Brasília
    assert rss._quando("2026-11-04T10:00:00-03:00") == ("20261104", "10:00")
    assert rss._quando("2026-11-04T10:00:00") == ("20261104", "")                 # sem fuso: não inventa a hora
    assert rss._quando("") == ("", "")
    xml = ('<rss><channel><item><title>Irã e Israel</title><link>https://x.com/a</link>'
           '<pubDate>Wed, 04 Nov 2026 15:00:00 +0000</pubDate></item></channel></rss>').encode("utf-8")
    assert rss.ler(xml, "Teste")[0]["hora"] == "12:00"


def test_paises_citados_no_titulo_com_extras_e_sem_falsos_positivos():
    from rotzx.mundo.paises import MENCOES, PAISES, citados
    assert len({p["iso_num"] for p in PAISES + MENCOES}) == len(PAISES) + len(MENCOES)   # sem código repetido
    assert citados("Israel ataca Gaza e o Líbano; EUA pedem trégua") == ["840", "376", "275", "422"]
    assert citados("Hospital Sírio-Libanês inaugura ala") == []
    assert citados("Preço do peru dispara no Natal") == []
    assert citados("Trump diz que guerra contra o Irã contribuiu") == ["364"]


def test_recategorizar_marca_paises_e_publica_os_nomes():
    n = {"paises": {"076": [{"titulo": "Brasil e China fecham acordo", "data": "20261104"}]},
         "mundo": [{"titulo": "Ucrânia e Rússia negociam cessar-fogo", "data": "20261104"}]}
    build._recategorizar(n)
    assert n["paises"]["076"][0]["paises"] == ["076", "156"]
    assert n["mundo"][0]["paises"] == ["643", "804"] and "geopolitica" in n["mundo"][0]["categorias"]
    assert n["nomes"]["804"] == "Ucrânia" and n["nomes"]["076"] == "Brasil"


def test_juntar_ordena_por_data_e_hora():
    a = [{"titulo": "A", "data": "20261104", "hora": "08:00"}, {"titulo": "B", "data": "20261104", "hora": "21:00"},
         {"titulo": "C", "data": "20261103", "hora": "23:59"}]
    assert [m["titulo"] for m in gdelt.juntar(a, [], "20261101")] == ["B", "A", "C"]


# ---- D46: tabela de países do globo ----

def test_tabela_de_paises_versionada_coerente():
    from rotzx.mundo import codigos
    t = codigos.carregar()
    assert len({r["iso_num"] for r in t}) == len(t) and len({r["iso3"] for r in t}) == len(t)
    por = {r["iso3"]: r for r in t}
    assert por["BRA"]["iso_num"] == "076" and por["BRA"]["comex"] == ["105"] and por["BRA"]["cow"] == [140]
    assert por["COG"]["comex"] != por["COD"]["comex"] and por["COD"]["nome"] == "Rep. Dem. do Congo"   # o "Congo" do Comex é a COG
    assert set(por["DEU"]["gw"]) == {260} and set(por["YEM"]["gw"]) >= {678, 680}
    assert sum(r["no_mapa"] for r in t) >= 170
    assert len({r["nome"] for r in t}) == len(t)                                   # sem nomes repetidos
    assert por["BRA"]["iso2"] == "BR" and por["VGB"]["nome"] != por["VIR"]["nome"]
    assert por["BRA"]["tipo"] == "pais" and por["BMU"]["tipo"] == "territorio" and por["HKG"]["tipo"] == "territorio"
    # os 21 países com painel completo batem com a tabela
    for p in PAISES:
        assert por[p["iso3"]]["iso_num"] == p["iso_num"] and p["comex"] in por[p["iso3"]]["comex"], p["nome"]
    from rotzx.mundo.conflitos import GW
    for iso3, g in GW.items():
        assert g in por[iso3]["gw"] or not por[iso3]["gw"], iso3


def test_casamento_comex_excecoes_e_erro_para_nome_desconhecido():
    from rotzx.mundo import codigos
    _, indice = codigos._iso_pycountry()
    c = codigos.casar_comex([{"id": "1", "text": "Congo"}, {"id": "2", "text": "Países Baixos (Holanda)"},
                             {"id": "3", "text": "A Designar"}, {"id": "4", "text": "Coreia do Sul"}], indice)
    assert c == {"Congo": "COG", "Países Baixos (Holanda)": "NLD", "A Designar": None, "Coreia do Sul": "KOR"}
    assert codigos._nome_comum("Salomão, Ilhas") == "Ilhas Salomão"
    with pytest.raises(ValueError):
        codigos.gerar([{"id": "9", "text": "Terra do Nunca"}], {}, [], [])


# ---- D46: retrato histórico (fixtures sintéticas no formato real) ----

TAB = [{"iso_num": "076", "iso3": "BRA", "nome": "Brasil", "comex": ["105"], "cow": [140], "gw": [140], "no_mapa": True},
       {"iso_num": "840", "iso3": "USA", "nome": "Estados Unidos", "comex": ["249"], "cow": [2], "gw": [2], "no_mapa": True},
       {"iso_num": "784", "iso3": "ARE", "nome": "Emirados Árabes Unidos", "comex": ["244", "237"], "cow": [696], "gw": [696], "no_mapa": True},
       {"iso_num": "804", "iso3": "UKR", "nome": "Ucrânia", "comex": ["831"], "cow": [369], "gw": [369], "no_mapa": True},
       {"iso_num": "643", "iso3": "RUS", "nome": "Rússia", "comex": ["676"], "cow": [365], "gw": [365], "no_mapa": True}]


def test_historia_comercio_soma_codigos_e_ano_sem_dado_fica_null(monkeypatch):
    from rotzx.mundo import historia
    serie = {"exportacao": {("Estados Unidos", 1997): 10.0, ("Emirados Árabes Unidos", 1998): 3.0, ("Dubai", 1998): 2.0,
                            ("A Designar", 1997): 1.0},
             "importacao": {("Estados Unidos", 1998): 4.0}}
    monkeypatch.setattr(historia.comex, "serie", lambda a, b, fluxo, pasta=None: serie[fluxo])
    monkeypatch.setattr(historia.comex, "produtos_todos", lambda ano, fluxo, pasta=None: {
        "Estados Unidos": [("1201", "Soja", 6.0), ("2601", "Minério", 4.0)]} if fluxo == "exportacao" else {})
    nomes = [{"id": "249", "text": "Estados Unidos"}, {"id": "244", "text": "Emirados Árabes Unidos"}, {"id": "237", "text": "Dubai"},
             {"id": "994", "text": "A Designar"}]
    pares = {}
    c = historia.comercio(TAB, 1998, nomes_comex=nomes, anos_produtos=[1998], pares_saida=pares)
    assert c["paises"]["840"]["e"] == [10.0, None] and c["paises"]["840"]["i"] == [None, 4.0]
    assert c["paises"]["784"]["e"] == [None, 5.0]                    # Dubai soma nos Emirados
    assert c["brasil"]["e"] == [11.0, 5.0]                           # o total do Brasil inclui o que não é país
    # composição: total bilateral (denominador) e número de posições exatos, mais os maiores
    assert c["paises"]["840"]["p"]["1998"]["e"] == {"t": 10, "n": 2, "top": [["1201", 6], ["2601", 4]]}
    assert c["sh4"]["1201"] == "Soja" and c["curtos"]["1201"] == "Soja em grão (mesmo triturada)"
    assert pares[(1998, "e")] == {"840": {"1201": 6.0, "2601": 4.0}}


def test_produtos_series_parceiros_e_grupos_somados_sobre_a_distribuicao_completa(monkeypatch):
    from rotzx.mundo import historia
    serie = {"exportacao": {("1201", 1997): 60e6, ("3102", 1998): 1e6, ("3104", 1998): 2e6},
             "importacao": {("3104", 1997): 70e6, ("3102", 1998): 5e6}}
    monkeypatch.setattr(historia.comex, "produtos_serie", lambda a, b, fluxo, pasta=None: serie[fluxo])
    pares = {(1998, "i"): {"643": {"3104": 30.0, "3102": 5.0}, "124": {"3104": 20.0}}}
    pr = historia.produtos(1998, pares, {"1201": "Soja", "3104": "Adubos potássicos", "3102": "Adubos azotados"})
    it = pr["itens"]
    assert set(it) >= {"1201", "3104", "g-fertilizantes"} and "3102" not in it        # 3102 abaixo de US$ 50 mi: fora
    assert it["1201"]["e"] == [60e6, None] and it["1201"]["nome"] == "Soja em grão (mesmo triturada)"
    assert it["3104"]["p"]["1998"]["i"] == {"t": 50, "n": 2, "top": [["643", 30], ["124", 20]]}
    g = it["g-fertilizantes"]
    assert g["e"] == [None, 3e6] and g["i"] == [70e6, 5e6]                             # séries somadas por ano
    assert g["p"]["1998"]["i"] == {"t": 55, "n": 2, "top": [["643", 35], ["124", 20]]}  # inclui o 3102 (fora da lista)


def test_historia_votos_mediana_por_ano(tmp_path):
    from rotzx.mundo import historia
    agree = tmp_path / "agree.csv"
    agree.write_text('"","session.x","ccode1","ccode2","agree","year"\n"1",1,140,2,0.9,1946\n"2",1,140,369,0.5,1946\n'
                     '"3",1,140,2,0.4,1948\n"4",1,140,365,NA,1948\n')
    v = historia.votos(TAB, agree)
    assert v["inicio"] == 1946 and v["fim"] == 1948 and v["paises"]["840"] == [0.9, None, 0.4]
    assert v["mediana"] == [0.7, None, 0.4]


def test_historia_conflitos_por_ano_territorio_lado_apoio():
    from rotzx.mundo import historia
    linhas = conflitos.ler(_ucdp(
        '1,"Russia (Soviet Union), Ukraine",Government of Russia (Soviet Union),57,"Government of United States of America",Government of Ukraine,169,"",3,Crimea,2022,2,1,2,2022-02-24,1,,,0,,,365,"2",369,"","365, 369",1,26.1',
        '2,Ukraine,Government of Ukraine,169,"",DPR,3,"",1,Donetsk,2014,1,1,3,2014-04-01,1,,,0,,,369,"","","",369,1,26.1'))
    k = historia.conflitos_por_ano(TAB, linhas)
    assert k["paises"]["804"]["2022"] == {"t": 2, "l": 1, "a": 0} and k["paises"]["804"]["2014"] == {"t": 1, "l": 1, "a": 0}
    assert k["paises"]["840"]["2022"] == {"t": 0, "l": 0, "a": 1}            # apoio com tropas, fora do território
    assert k["por_ano"]["2022"][0]["guerra"] and k["por_ano"]["2022"][0]["paises"] == ["643", "804"]


def test_historia_disputas_com_o_brasil():
    from rotzx.mundo import historia
    d = historia.disputas(TAB, OMC_JS)
    assert [c["ds"] for c in d["840"]["casos"]] == ["DS2", "DS1"] and d["840"]["casos"][1]["brasil_abriu"]
    assert "784" not in d
