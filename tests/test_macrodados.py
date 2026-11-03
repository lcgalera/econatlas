import pandas as pd
import pytest

from econatlas.providers import arquivo, macrodados

# mesmo formato de uma exportação CSV da Macrodados Web (nov/2026), com nomes e valores fictícios
EXPORT_ANUAL = (
    '﻿"Data","ASSOC - Faturamento da Indústria Exemplo - Total (R$ M)"\r\n'
    '"2023","1000.00"\r\n"2024","1100.50"\r\n"2025","1210.25"\r\n\r\n'
    '"Fonte : Macrodados Web"\r\n"web.macrodados.com"\r\n'
).encode("utf-8")


def test_parse_real_export_format():
    [s] = macrodados.parse_export(EXPORT_ANUAL, "macrodados_2716.CSV")
    assert s.nome == "ASSOC - Faturamento da Indústria Exemplo - Total"
    assert (s.instituicao, s.unidade, s.periodicidade) == ("ASSOC", "R$ M", "anual")
    assert s.data["date"].tolist() == [pd.Timestamp(y, 1, 1) for y in (2023, 2024, 2025)]
    assert s.data["value"].tolist() == [1000.0, 1100.5, 1210.25]  # rodapé ignorado


def test_multi_series_monthly_export():
    raw = ('"Data","ORG1 - Indicador A (%)","ORG2 - Indicador B (pontos)"\n'
           '"01/2026","78.1","95.2"\n"02/2026","78.4",""\n"03/2026","78.0","96.0"\n').encode()
    a, b = macrodados.parse_export(raw, "x.csv")
    assert a.periodicidade == "mensal" and len(a.data) == 3
    assert len(b.data) == 2  # célula vazia não vira zero


def test_slug_is_stable_and_ascii():
    assert macrodados.slug("ASSOC - Fat. da Ind. Exemplo - Informática (R$ M)") == \
        "assoc_fat_da_ind_exemplo_informatica"


@pytest.mark.parametrize("txt,expected", [
    ("2024", "2024-01-01"), ("03/2024", "2024-03-01"), ("2024-03", "2024-03-01"),
    ("mar/2024", "2024-03-01"), ("mar/24", "2024-03-01"), ("2T2024", "2024-04-01"),
    ("2º tri/2024", "2024-04-01"), ("T3/2024", "2024-07-01"), ("15/03/2024", "2024-03-15"),
])
def test_date_formats(txt, expected):
    assert arquivo._parse_date(txt) == pd.Timestamp(expected)


def test_unrecognized_date_is_not_silently_accepted():
    assert pd.isna(arquivo._parse_date("Fonte : Macrodados Web"))


def test_manifest_matches_columns_with_non_breaking_spaces(tmp_path):
    import json
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"coluna": "ASSOC - Fat. - Informática (R$ M)", "codigo_md": "xx0001"}]))
    m = macrodados.load_manifest(p)
    assert m[macrodados.norm("ASSOC - Fat. -\xa0Informática\xa0(R$ M)")]["codigo_md"] == "xx0001"


def test_real_basket_manifest_is_consistent():
    from econatlas import config
    if not config.MACRODADOS_MANIFEST.exists():
        pytest.skip("manifesto da Macrodados é local (privado/), fora do repositório público")
    m = macrodados.load_manifest(config.MACRODADOS_MANIFEST)
    codes = [i["codigo_md"] for i in m.values()]
    assert len(codes) == len(set(codes)) >= 28
    assert all(i["instituicao"] and i["unidade"] and i["tema"] for i in m.values())
