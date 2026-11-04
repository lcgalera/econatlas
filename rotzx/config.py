"""Caminhos do projeto. Tudo relativo à raiz do repositório."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_FILE = ROOT / "catalog" / "series.json"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LOCAL_CATALOG_FILE = DATA_DIR / "catalogo_local.json"  # séries importadas de arquivos (uso pessoal)
DB_FILE = DATA_DIR / "rotzx.sqlite"
DB_FILE_ANTIGO = DATA_DIR / "econatlas.sqlite"  # nome até a v0.12 (D35): renomeado no primeiro uso
WEB_DIR = ROOT / "web"
BACKTEST_FILE = DATA_DIR / "backtests" / "ipca_mensal.json"

USER_AGENT = "rotzx/0.1 (pesquisa pessoal)"
MACRODADOS_MANIFEST = ROOT / "privado" / "macrodados_cesta.json"  # local, fora do git
ANALYSES_DIR = DATA_DIR / "analyses"  # <setor>_antecedentes.json
PUBLIC_SITE_DIR = ROOT / "site"  # saída do build público (rotzx publicar)
PRIVATE_DIR = ROOT / "privado"  # configuração e scripts de uso pessoal (Macrodados); fora do git
