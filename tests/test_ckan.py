"""Exploração de fontes CKAN (Fase 1). Os dados abaixo são FIXTURES sintéticas, não registros da ANEEL."""
import io
import zipfile

import pandas as pd

from rotzx.providers import ckan

# Formato típico de CSV de órgão público brasileiro: cp1252, separador ";" e acentos nos nomes.
CSV_EMPREENDIMENTOS = "IdeEmpreendimento;NomEmpreendimento;SigUF;DatPrevista\n1;Subestação Fictícia A;MG;2027-01-01\n2;LT Fictícia B;BA;\n3;SE Fictícia C;MG;2026-05-01\n".encode("cp1252")
CSV_MODULOS = "IdeModulo;IdeEmpreendimento;DscModulo\n10;1;Transformador\n11;1;Entrada de linha\n12;9;Reator\n".encode("cp1252")


def test_ler_csv_detecta_codificacao_e_separador():
    df = ckan.ler_csv(CSV_EMPREENDIMENTOS)
    assert list(df.columns) == ["IdeEmpreendimento", "NomEmpreendimento", "SigUF", "DatPrevista"]
    assert df.loc[0, "NomEmpreendimento"] == "Subestação Fictícia A"
    assert df.loc[1, "DatPrevista"] == ""  # vazio continua vazio, sem virar NaN ou número


def test_perfil_conta_preenchimento_distintos_e_chave():
    p = {c["coluna"]: c for c in ckan.perfil(ckan.ler_csv(CSV_EMPREENDIMENTOS))}
    assert p["IdeEmpreendimento"]["parece_chave"] and p["IdeEmpreendimento"]["distintos"] == 3
    assert p["DatPrevista"]["preenchido_pct"] == round(200 / 3, 1) and not p["DatPrevista"]["parece_chave"]
    assert p["SigUF"]["distintos"] == 2 and p["SigUF"]["exemplos"][0] == "MG"


def test_colunas_compartilhadas_medem_sobreposicao():
    tabs = {"emp": ckan.ler_csv(CSV_EMPREENDIMENTOS), "mod": ckan.ler_csv(CSV_MODULOS)}
    comp = ckan.colunas_compartilhadas(tabs)
    assert len(comp) == 1
    r = comp[0]
    assert (r["coluna_a"], r["coluna_b"], r["em_comum"]) == ("IdeEmpreendimento", "IdeEmpreendimento", 1)
    # o módulo 12 aponta para o empreendimento 9, que não existe: a sobreposição não é total
    assert r["distintos_b"] == 2


def test_tabelas_le_csvs_de_dentro_do_zip(tmp_path):
    z = tmp_path / "siget.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("empreendimentos.csv", CSV_EMPREENDIMENTOS)
        f.writestr("leiame.txt", b"ignorado")
    t = ckan.tabelas(z)
    assert list(t) == ["empreendimentos.csv"] and len(t["empreendimentos.csv"]) == 3


def test_buscar_resume_resposta_ckan(monkeypatch):
    resposta = {"results": [{"name": "siget", "title": "SIGET", "license_title": "Licença X", "metadata_modified": "2026-10-01",
                             "organization": {"title": "ANEEL"}, "notes": " Dados da transmissão ",
                             "resources": [{"id": "r1", "name": "Empreendimentos", "format": "CSV", "url": "https://x/e.csv"}]}]}
    monkeypatch.setattr(ckan, "_api", lambda portal, acao, **kw: resposta)
    [c] = ckan.buscar("aneel", "siget")
    assert c["licenca"] == "Licença X" and c["organizacao"] == "ANEEL" and c["descricao"] == "Dados da transmissão"
    assert c["recursos"][0]["formato"] == "csv"


def test_explorar_grava_relatorio_e_brutos_sem_sobrescrever(monkeypatch, tmp_path):
    meta = {"nome": "siget", "titulo": "SIGET", "licenca": "Licença X", "organizacao": "ANEEL", "modificado": "2026-10-01",
            "descricao": "", "recursos": [
                {"id": "a", "nome": "Empreendimentos", "formato": "csv", "url": "https://x/emp.csv", "modificado": None},
                {"id": "b", "nome": "Módulos", "formato": "csv", "url": "https://x/mod.csv", "modificado": None},
                {"id": "c", "nome": "Manual", "formato": "pdf", "url": "https://x/manual.pdf", "modificado": None}]}
    corpos = {"https://x/emp.csv": CSV_EMPREENDIMENTOS, "https://x/mod.csv": CSV_MODULOS}
    monkeypatch.setattr(ckan, "conjunto", lambda portal, nome: meta)
    monkeypatch.setattr(ckan, "_get", lambda url, tries=4: corpos[url])
    rel = ckan.explorar("aneel", "siget", pasta=tmp_path)
    texto = rel.read_text()
    assert "Licença declarada no portal: Licença X" in texto
    assert "## Tabela `Empreendimentos`" in texto and "## Tabela `Módulos`" in texto
    assert "candidatas a ligação" in texto and "IdeEmpreendimento" in texto
    assert len(list((tmp_path / "brutos").iterdir())) == 2  # o PDF não é baixado
    ckan.explorar("aneel", "siget", pasta=tmp_path)  # repetir não duplica nem sobrescreve brutos
    assert len(list((tmp_path / "brutos").iterdir())) == 2
