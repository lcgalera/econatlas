"""Motor de oportunidades do rotzx (Fase 3): evidências por categoria de produto, score explicável e relatório.

Tudo é determinístico e documentado em docs/06-motor-de-oportunidades.md. Nenhuma regra afirma compra:
"confirmado" quer dizer que a fonte oficial descreve o equipamento na obra; "inferência técnica" quer
dizer que a natureza da obra sugere o equipamento sem que a fonte o cite.
"""
import json
from pathlib import Path

from .. import config

CATEGORIAS_FILE = config.ROOT / "catalog" / "product_categories.json"
PERFIL_DEMO_FILE = config.ROOT / "catalog" / "perfil_demo.json"


def carregar_categorias(caminho: Path = CATEGORIAS_FILE) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def carregar_perfil(caminho: Path = PERFIL_DEMO_FILE) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))
