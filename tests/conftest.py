import pytest


@pytest.fixture(autouse=True)
def _isolar_arquivos_reais(tmp_path, monkeypatch):
    """Nenhum teste escreve nos arquivos reais em data/ (ex.: cache de erros do SARIMA)."""
    from rotzx.forecast import empirico
    monkeypatch.setattr(empirico, "CACHE_FILE", tmp_path / "ipca_sarima_erros.json")
